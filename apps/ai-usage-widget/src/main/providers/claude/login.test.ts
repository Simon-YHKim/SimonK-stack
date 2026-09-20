import { describe, expect, it } from 'vitest';
import type { LoginEvent } from '../../../shared/types';
import { SpawnError, type ExitInfo, type LongLivedOptions, type LongLivedProcess } from '../../cli/spawn';
import { nullLogger } from '../../log';
import { ProviderError, type ProviderIdentity } from '../types';
import { claudeEnvPolicy } from './env';
import {
  CLAUDE_LOGIN_TIMEOUT_MS,
  createLoginManager,
  createLoginOutputParser,
  isAllowedClaudeLoginUrl,
  normalizePasteCode,
  type SpawnLongLivedFn,
} from './login';

const AUTH_URL =
  'https://claude.com/cai/oauth/authorize?code=true&client_id=abc&response_type=code&redirect_uri=https%3A%2F%2Fplatform.claude.com%2Foauth%2Fcode%2Fcallback&state=xyz';
const ESC = '\u001b';
const BEL = '\u0007';

describe('isAllowedClaudeLoginUrl', () => {
  it('accepts the subscription authorize endpoints', () => {
    expect(isAllowedClaudeLoginUrl(AUTH_URL)).toBe(true);
    expect(isAllowedClaudeLoginUrl('https://claude.ai/oauth/authorize?state=1')).toBe(true);
  });

  it.each([
    'http://claude.com/cai/oauth/authorize',
    'https://claude.com.evil.test/cai/oauth/authorize',
    'https://evil.test/?u=https://claude.com/cai/oauth/authorize',
    'https://user:pw@claude.com/cai/oauth/authorize',
    'https://claude.com:8443/cai/oauth/authorize',
    'https://claude.com/cai/oauth/authorize/../../logout',
    'https://platform.claude.com/oauth/authorize',
    'https://claude.com/login',
    `https://claude.com/cai/oauth/authorize?${'a'.repeat(2100)}`,
    'not a url',
  ])('rejects %s', (url) => {
    expect(isAllowedClaudeLoginUrl(url)).toBe(false);
  });
});

describe('normalizePasteCode', () => {
  it('accepts code#state and trims whitespace', () => {
    expect(normalizePasteCode('  Ab3_-x.y~z#st4te-9 ')).toBe('Ab3_-x.y~z#st4te-9');
  });

  it.each(['', 'nohash', '#state', 'code#', 'a#b#c', 'co de#state', 'code#sta\nte', `${'a'.repeat(4096)}#b`])(
    'rejects %j',
    (text) => {
      expect(normalizePasteCode(text)).toBeNull();
    },
  );
});

describe('login output parser', () => {
  it('emits url and needs-paste from the pipe-mode output, including OSC 8 links', () => {
    const parser = createLoginOutputParser();
    expect(parser.stdout('Opening browser to sign in…')).toEqual([{ type: 'progress', stage: 'waiting-browser' }]);
    const osc = `${ESC}]8;;${AUTH_URL}${BEL}${AUTH_URL}${ESC}]8;;${BEL}`;
    expect(parser.stdout(`If the browser didn't open, visit: ${osc}`)).toEqual([
      { type: 'url', url: AUTH_URL },
      { type: 'needs-paste' },
      { type: 'progress', stage: 'waiting-paste' },
    ]);
    expect(parser.urlSeen).toBe(true);
    expect(parser.stderr('Invalid code. Please make sure the full code was copied.')).toEqual([
      { type: 'needs-paste' },
      { type: 'progress', stage: 'waiting-paste' },
    ]);
    expect(parser.stdout('Paste code here if prompted > Login successful.')).toEqual([]);
    expect(parser.succeeded).toBe(true);
    expect(parser.failure).toBeNull();
  });

  it('flags a URL outside the allowlist without emitting it', () => {
    const parser = createLoginOutputParser();
    expect(parser.stdout("If the browser didn't open, visit: https://phish.test/cai/oauth/authorize")).toEqual([]);
    expect(parser.failure).toBe('protocol-error');
    expect(parser.urlSeen).toBe(false);
  });

  it('maps CLI failure messages to login-failed', () => {
    const parser = createLoginOutputParser();
    parser.stderr('Login failed: request rejected');
    expect(parser.failure).toBe('login-failed');
  });
});

function fakeProcess(): {
  proc: LongLivedProcess;
  written: string[];
  stdout(line: string): void;
  stderr(line: string): void;
  finish(info: Partial<ExitInfo>): void;
  killed(): boolean;
} {
  const out = new Set<(line: string, truncated: boolean) => void>();
  const err = new Set<(line: string, truncated: boolean) => void>();
  const written: string[] = [];
  let open = true;
  let wasKilled = false;
  let resolveExit: (info: ExitInfo) => void = () => undefined;
  const exited = new Promise<ExitInfo>((resolve) => {
    resolveExit = resolve;
  });
  const finish = (info: Partial<ExitInfo>): void => {
    open = false;
    resolveExit({ exitCode: null, signal: null, timedOut: false, aborted: false, ...info });
  };
  const proc: LongLivedProcess = {
    pid: 4242,
    writeLine: (line) => {
      if (!open) return false;
      written.push(line);
      return true;
    },
    writeJson: (value) => proc.writeLine(JSON.stringify(value)),
    onStdoutLine: (listener) => {
      out.add(listener);
      return () => out.delete(listener);
    },
    onStderrLine: (listener) => {
      err.add(listener);
      return () => err.delete(listener);
    },
    closeStdin: () => {
      open = false;
    },
    exited,
    kill: () => {
      wasKilled = true;
      finish({ aborted: true });
      return exited;
    },
  };
  return {
    proc,
    written,
    stdout: (line) => out.forEach((listener) => listener(line, false)),
    stderr: (line) => err.forEach((listener) => listener(line, false)),
    finish,
    killed: () => wasKilled,
  };
}

const tick = (): Promise<void> => new Promise((resolve) => setTimeout(resolve, 0));

function setup(identity: ProviderIdentity | Error = { loggedIn: true, emailMasked: 'u***@e***.com', plan: 'pro' }) {
  const fake = fakeProcess();
  const calls: Array<{ args: readonly string[]; options: LongLivedOptions }> = [];
  const spawn: SpawnLongLivedFn = (_command, args, options) => {
    calls.push({ args, options });
    return Promise.resolve(fake.proc);
  };
  const events: LoginEvent[] = [];
  const manager = createLoginManager({ logger: nullLogger, spawn });
  const controller = new AbortController();
  const done = manager.start({
    accountId: 'acc1',
    command: { file: 'C:\\cli\\claude.exe', prefixArgs: [] },
    env: claudeEnvPolicy('C:\\profiles\\claude\\acc1'),
    parentEnv: {},
    cwd: 'C:\\profiles\\claude\\acc1',
    emit: (event) => events.push(event),
    signal: controller.signal,
    verify: () => (identity instanceof Error ? Promise.reject(identity) : Promise.resolve(identity)),
  });
  return { fake, calls, events, manager, controller, done };
}

describe('login manager', () => {
  it('runs the full paste flow and reports the verified identity', async () => {
    const { fake, calls, events, manager, done } = setup();
    await tick();
    expect(calls[0]?.args).toEqual(['auth', 'login', '--claudeai']);
    expect(calls[0]?.options.timeoutMs).toBe(CLAUDE_LOGIN_TIMEOUT_MS);
    expect(calls[0]?.options.env.set).toEqual({ CLAUDE_CONFIG_DIR: 'C:\\profiles\\claude\\acc1' });
    expect(calls[0]?.options.env.remove).toContain('ANTHROPIC_API_KEY');

    fake.stdout('Opening browser to sign in…');
    fake.stdout(`If the browser didn't open, visit: ${AUTH_URL}`);
    await manager.submitPaste('acc1', ' code123#state456 ');
    expect(fake.written).toEqual(['code123#state456']);
    fake.stdout('Paste code here if prompted > Login successful.');
    fake.finish({ exitCode: 0 });
    await done;

    expect(events).toEqual([
      { type: 'progress', stage: 'starting' },
      { type: 'progress', stage: 'waiting-browser' },
      { type: 'url', url: AUTH_URL },
      { type: 'needs-paste' },
      { type: 'progress', stage: 'waiting-paste' },
      { type: 'progress', stage: 'verifying' },
      { type: 'progress', stage: 'verifying' },
      { type: 'success', emailMasked: 'u***@e***.com', plan: 'pro' },
    ]);
    expect(manager.isActive('acc1')).toBe(false);
  });

  it('rejects malformed pastes and pastes before the URL without writing', async () => {
    const { fake, manager, done } = setup();
    await tick();
    await expect(manager.submitPaste('acc1', 'code#state')).rejects.toBeInstanceOf(ProviderError);
    fake.stdout(`If the browser didn't open, visit: ${AUTH_URL}`);
    await expect(manager.submitPaste('acc1', 'no-hash-here')).rejects.toMatchObject({ code: 'parse-error' });
    await expect(manager.submitPaste('other', 'code#state')).rejects.toMatchObject({ code: 'login-failed' });
    expect(fake.written).toEqual([]);
    fake.finish({ exitCode: 1 });
    await done;
  });

  it('kills the process when the URL is not allowlisted', async () => {
    const { fake, events, done } = setup();
    await tick();
    fake.stdout("If the browser didn't open, visit: https://claude.com.evil.test/cai/oauth/authorize");
    await done;
    expect(fake.killed()).toBe(true);
    expect(events.at(-1)).toEqual({ type: 'error', code: 'protocol-error' });
    expect(events.some((event) => event.type === 'url')).toBe(false);
  });

  it('reports timeout, cancellation and CLI failure', async () => {
    const timeout = setup();
    await tick();
    timeout.fake.finish({ timedOut: true });
    await timeout.done;
    expect(timeout.events.at(-1)).toEqual({ type: 'error', code: 'timeout' });

    const cancelled = setup();
    await tick();
    cancelled.controller.abort();
    cancelled.fake.finish({ aborted: true });
    await cancelled.done;
    expect(cancelled.events.at(-1)).toEqual({ type: 'error', code: 'cancelled' });

    const failed = setup();
    await tick();
    failed.fake.stderr('Login failed: denied');
    failed.fake.finish({ exitCode: 1 });
    await failed.done;
    expect(failed.events.at(-1)).toEqual({ type: 'error', code: 'login-failed' });
  });

  it('still reports success when the identity check fails after a successful login', async () => {
    const { fake, events, done } = setup(new ProviderError('timeout'));
    await tick();
    fake.stdout(`visit: ${AUTH_URL}`);
    fake.stdout('Login successful.');
    fake.finish({ exitCode: 0 });
    await done;
    expect(events.at(-1)).toEqual({ type: 'success' });
  });

  it('maps spawn failures', async () => {
    const events: LoginEvent[] = [];
    const manager = createLoginManager({
      logger: nullLogger,
      spawn: () => Promise.reject(new SpawnError('cli-not-found', 'missing')),
    });
    await manager.start({
      accountId: 'acc1',
      command: { file: 'C:\\cli\\claude.exe', prefixArgs: [] },
      env: claudeEnvPolicy('C:\\p'),
      parentEnv: {},
      cwd: 'C:\\p',
      emit: (event) => events.push(event),
      signal: new AbortController().signal,
      verify: () => Promise.resolve({ loggedIn: true }),
    });
    expect(events).toEqual([
      { type: 'progress', stage: 'starting' },
      { type: 'error', code: 'cli-not-found' },
    ]);
  });
});
