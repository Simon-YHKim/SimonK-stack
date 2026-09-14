// `claude auth login --claudeai` over pipes (not a TUI). Output sequence in claude.exe 2.1.270:
//   stdout "Opening browser to sign in…"
//   stdout "If the browser didn't open, visit: <url>"   (URL may carry OSC 8 escapes)
//   stdout "Paste code here if prompted > "              (no newline, written right after the URL line)
//   stdin  "<code>#<state>"                               (missing '#': stderr "Invalid code..." and keeps waiting)
//   stdout "Login successful." + exit 0                   (lands on the prompt line)

import type { ErrorCode, LoginEvent } from '../../../shared/types';
import type { Logger } from '../../log';
import { SpawnError, type EnvPolicy, type LongLivedProcess, type ResolvedCommand, type spawnLongLived } from '../../cli/spawn';
import { stripAnsi } from '../../cli/text';
import { ProviderError, type ProviderIdentity } from '../types';

export const CLAUDE_LOGIN_TIMEOUT_MS = 10 * 60_000;
export const CLAUDE_LOGIN_ARGS: readonly string[] = ['auth', 'login', '--claudeai'];
export const PASTE_PROMPT = 'Paste code here if prompted';
const URL_MAX_LENGTH = 2048;

/** Authorize endpoints for subscription login (claude.exe: CLAUDE_AI_AUTHORIZE_URL; claude.ai kept for older CLIs). */
const ALLOWED_LOGIN_URLS: ReadonlyArray<{ host: string; path: string }> = [
  { host: 'claude.com', path: '/cai/oauth/authorize' },
  { host: 'claude.ai', path: '/oauth/authorize' },
];

/** Hosts the shell may open for Claude login (the exact paths are enforced above). */
export const CLAUDE_LOGIN_URL_HOSTS: readonly string[] = ALLOWED_LOGIN_URLS.map((allowed) => allowed.host);

export function isAllowedClaudeLoginUrl(value: string): boolean {
  if (value.length === 0 || value.length > URL_MAX_LENGTH) return false;
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    return false;
  }
  return (
    url.protocol === 'https:' &&
    url.username === '' &&
    url.password === '' &&
    url.port === '' &&
    ALLOWED_LOGIN_URLS.some((allowed) => url.hostname === allowed.host && url.pathname === allowed.path)
  );
}

const CODE_PART = '[A-Za-z0-9._~+/=-]{1,2048}';
const PASTE_RE = new RegExp(`^${CODE_PART}#${CODE_PART}$`);

/** `code#state` as shown by the browser; exactly one '#', no whitespace. Returns null when invalid. */
export function normalizePasteCode(text: string): string | null {
  const trimmed = text.trim();
  if (trimmed.length < 3 || trimmed.length > 4096) return null;
  return PASTE_RE.test(trimmed) ? trimmed : null;
}

const URL_IN_LINE_RE = /https:\/\/[^\s"'<>]+/;

export interface LoginOutputParser {
  stdout(line: string): LoginEvent[];
  stderr(line: string): LoginEvent[];
  readonly urlSeen: boolean;
  readonly succeeded: boolean;
  readonly failure: ErrorCode | null;
}

export function createLoginOutputParser(): LoginOutputParser {
  let urlSeen = false;
  let succeeded = false;
  let browserAnnounced = false;
  let failure: ErrorCode | null = null;

  return {
    stdout(raw) {
      const line = stripAnsi(raw);
      const events: LoginEvent[] = [];
      if (line.includes('Login successful.')) {
        succeeded = true;
        return events;
      }
      if (!browserAnnounced && line.includes('Opening browser')) {
        browserAnnounced = true;
        events.push({ type: 'progress', stage: 'waiting-browser' });
      }
      const match = urlSeen ? null : URL_IN_LINE_RE.exec(line);
      if (match !== null) {
        if (!isAllowedClaudeLoginUrl(match[0])) {
          failure = 'protocol-error';
          return events;
        }
        urlSeen = true;
        // The paste prompt has no trailing newline, so it cannot arrive as a line;
        // claude writes it synchronously right after this URL line.
        events.push({ type: 'url', url: match[0] }, { type: 'needs-paste' }, { type: 'progress', stage: 'waiting-paste' });
      }
      return events;
    },
    stderr(raw) {
      const line = stripAnsi(raw);
      if (line.includes('Invalid code')) {
        return urlSeen ? [{ type: 'needs-paste' }, { type: 'progress', stage: 'waiting-paste' }] : [];
      }
      if (/Login failed|cannot be used together|Managed settings|^Error:/i.test(line)) failure ??= 'login-failed';
      return [];
    },
    get urlSeen() {
      return urlSeen;
    },
    get succeeded() {
      return succeeded;
    },
    get failure() {
      return failure;
    },
  };
}

export type SpawnLongLivedFn = typeof spawnLongLived;

export interface StartLoginInput {
  accountId: string;
  command: ResolvedCommand;
  env: EnvPolicy;
  parentEnv: NodeJS.ProcessEnv;
  cwd: string;
  emit: (event: LoginEvent) => void;
  signal: AbortSignal;
  /** Reads the identity after a successful login (auth status). */
  verify: (signal: AbortSignal) => Promise<ProviderIdentity>;
}

interface ActiveLogin {
  proc: LongLivedProcess;
  parser: LoginOutputParser;
  emit: (event: LoginEvent) => void;
}

export interface LoginManager {
  start(input: StartLoginInput): Promise<void>;
  submitPaste(accountId: string, text: string): Promise<void>;
  cancel(accountId: string): Promise<void>;
  isActive(accountId: string): boolean;
}

export function createLoginManager(options: { logger: Logger; spawn: SpawnLongLivedFn; timeoutMs?: number }): LoginManager {
  const active = new Map<string, ActiveLogin>();
  const timeoutMs = options.timeoutMs ?? CLAUDE_LOGIN_TIMEOUT_MS;

  const cancel = async (accountId: string): Promise<void> => {
    const session = active.get(accountId);
    if (session !== undefined) await session.proc.kill();
  };

  return {
    isActive: (accountId) => active.has(accountId),
    cancel,

    async start(input) {
      const { emit, signal } = input;
      await cancel(input.accountId);
      emit({ type: 'progress', stage: 'starting' });

      let proc: LongLivedProcess;
      try {
        proc = await options.spawn(input.command, CLAUDE_LOGIN_ARGS, {
          env: input.env,
          parentEnv: input.parentEnv,
          cwd: input.cwd,
          timeoutMs,
          signal,
        });
      } catch (error) {
        const code: ErrorCode = signal.aborted
          ? 'cancelled'
          : error instanceof SpawnError && error.code === 'cli-not-found'
            ? 'cli-not-found'
            : 'spawn-failed';
        options.logger.warn('login spawn failed', { code });
        emit({ type: 'error', code });
        return;
      }

      const parser = createLoginOutputParser();
      const session: ActiveLogin = { proc, parser, emit };
      active.set(input.accountId, session);
      const forward = (events: LoginEvent[]): void => {
        for (const event of events) emit(event);
        if (parser.failure === 'protocol-error') void proc.kill();
      };
      const offOut = proc.onStdoutLine((line) => forward(parser.stdout(line)));
      const offErr = proc.onStderrLine((line) => forward(parser.stderr(line)));

      const exit = await proc.exited;
      offOut();
      offErr();
      if (active.get(input.accountId) === session) active.delete(input.accountId);

      if (parser.failure === 'protocol-error') {
        options.logger.warn('login URL outside the allowlist; process killed');
        emit({ type: 'error', code: 'protocol-error' });
        return;
      }
      if (exit.aborted || signal.aborted) {
        emit({ type: 'error', code: 'cancelled' });
        return;
      }
      if (exit.timedOut) {
        emit({ type: 'error', code: 'timeout' });
        return;
      }
      if (!parser.succeeded || exit.exitCode !== 0) {
        options.logger.info('login ended without success', { exitCode: exit.exitCode });
        emit({ type: 'error', code: parser.failure ?? 'login-failed' });
        return;
      }

      emit({ type: 'progress', stage: 'verifying' });
      let identity: ProviderIdentity | null = null;
      try {
        identity = await input.verify(signal);
      } catch (error) {
        options.logger.warn('identity check after login failed', {
          code: error instanceof ProviderError ? error.code : 'internal',
        });
      }
      if (identity !== null && !identity.loggedIn) {
        emit({ type: 'error', code: 'login-failed' });
        return;
      }
      const success: LoginEvent = { type: 'success' };
      if (identity?.emailMasked !== undefined) success.emailMasked = identity.emailMasked;
      if (identity?.plan !== undefined) success.plan = identity.plan;
      emit(success);
    },

    submitPaste(accountId, text) {
      const session = active.get(accountId);
      if (session === undefined || !session.parser.urlSeen) {
        return Promise.reject(new ProviderError('login-failed', 'no login is waiting for a code'));
      }
      const code = normalizePasteCode(text);
      if (code === null) return Promise.reject(new ProviderError('parse-error', 'pasted text is not code#state'));
      if (!session.proc.writeLine(code)) {
        return Promise.reject(new ProviderError('login-failed', 'login process is no longer running'));
      }
      session.emit({ type: 'progress', stage: 'verifying' });
      return Promise.resolve();
    },
  };
}
