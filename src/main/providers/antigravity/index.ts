// Antigravity provider (DECISIONS 26.09.19 11:42): one account that reuses the user's own
// `agy` sign-in. Usage comes only from the official CLI's `/usage` slash command in print
// mode. The adapter never reads the Windows credential store, never calls Google endpoints
// and never talks to the IDE's local language server.

import { mkdir, rm } from 'node:fs/promises';
import path from 'node:path';
import { maskSecrets } from '../../../shared/mask';
import type { Account, ErrorCode, LoginEvent, UsageSnapshot } from '../../../shared/types';
import { createEmptySnapshot } from '../../../shared/usage';
import { defaultResolveDeps, resolveCommand, type ResolveDeps } from '../../cli/resolve';
import { BASE_ENV_ALLOW, SpawnError, run, type EnvPolicy, type ResolvedCommand } from '../../cli/spawn';
import { stripAnsi } from '../../cli/text';
import { isPathInside } from '../../paths';
import { ProviderError, type CliInfo, type ProviderAdapter, type ProviderDeps, type ProviderIdentity } from '../types';
import { parseAgyUsage } from './usage';

export interface AntigravityTimeouts {
  versionMs: number;
  /** Hard kill limit of one `/usage` run; agy's own `--print-timeout` is set below it. */
  usageMs: number;
  printTimeoutSec: number;
}

export const DEFAULT_ANTIGRAVITY_TIMEOUTS: AntigravityTimeouts = {
  versionMs: 20_000,
  usageMs: 45_000,
  printTimeoutSec: 30,
};

export type AgyCliResolution = { ok: true; command: ResolvedCommand; source: string } | { ok: false; code: ErrorCode };

export interface AntigravityAdapterOptions {
  /** Test hook: replaces CLI discovery. */
  resolveCli?: () => AgyCliResolution;
  resolveDeps?: ResolveDeps;
  timeouts?: Partial<AntigravityTimeouts>;
  /** How long a result from getIdentity may be reused by the next fetchUsage (and vice versa). */
  primeTtlMs?: number;
}

/** Credential and endpoint overrides that must never reach the child (defence in depth over the whitelist). */
export const AGY_ENV_REMOVE: readonly string[] = [
  'GEMINI_API_KEY',
  'GOOGLE_API_KEY',
  'GOOGLE_APPLICATION_CREDENTIALS',
  'GOOGLE_CLOUD_PROJECT',
  'AGY_ADC_AUTH',
  'ANTIGRAVITY_EXECUTABLE_DATA_DIR',
  'ANTIGRAVITY_CSRF_TOKEN',
];

/** The updater is off so a background refresh can never raise a UAC elevation prompt. */
export const AGY_ENV_POLICY: EnvPolicy = {
  allow: BASE_ENV_ALLOW,
  remove: AGY_ENV_REMOVE,
  set: { AGY_CLI_DISABLE_AUTO_UPDATE: '1', NO_COLOR: '1' },
};

/** PATH first, then the managed install `%LOCALAPPDATA%\agy\bin\agy.exe`. */
export function resolveAgyCli(env: NodeJS.ProcessEnv, resolveDeps: ResolveDeps): AgyCliResolution {
  const onPath = resolveCommand('agy', resolveDeps);
  if (onPath.ok) return { ok: true, command: onPath.command, source: onPath.source };
  const localAppData = env.LOCALAPPDATA;
  if (resolveDeps.platform === 'win32' && typeof localAppData === 'string' && localAppData !== '') {
    const managed = resolveCommand(path.win32.join(localAppData, 'agy', 'bin', 'agy.exe'), resolveDeps);
    if (managed.ok) return { ok: true, command: managed.command, source: managed.source };
  }
  if (onPath.code === 'node-not-found') return { ok: false, code: 'node-not-found' };
  return { ok: false, code: onPath.code === 'unsupported-shim' ? 'cli-unsupported-install' : 'cli-not-found' };
}

/** `1.2.6` or `agy 1.2.6` -> `1.2.6`. */
export function parseAgyVersion(output: string): string | undefined {
  return /\b(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)\b/.exec(stripAnsi(output))?.[1];
}

/** Sign-in wording of a CLI that has no account; anything else stays "unknown", never "logged out". */
const SIGNED_OUT_PATTERN = /\b(not (?:logged|signed) in|sign in required|login required|please (?:log|sign) in|unauthenticated)\b/i;

/** Connectivity wording; shown as a network error and retried with the normal back-off. */
const NETWORK_PATTERN = /\b(network|dns|econn\w*|enotfound|etimedout|timed? ?out|connection (?:refused|reset|closed)|unreachable|tls|socket hang up|offline)\b/i;

type ProbeResult =
  | { kind: 'ok'; windows: UsageSnapshot['windows'] }
  | { kind: 'failed'; state: 'error' | 'unavailable' | 'logged-out'; code: ErrorCode };

interface Primed {
  at: number;
  result: ProbeResult;
}

export function createAntigravityAdapter(deps: ProviderDeps, options: AntigravityAdapterOptions = {}): ProviderAdapter {
  const { logger } = deps;
  const timeouts: AntigravityTimeouts = { ...DEFAULT_ANTIGRAVITY_TIMEOUTS, ...options.timeouts };
  const primeTtlMs = options.primeTtlMs ?? 15_000;
  const profilesRoot = path.join(deps.profilesRoot, 'antigravity');
  const primedForUsage = new Map<string, Primed>();
  const primedForIdentity = new Map<string, Primed>();
  const inFlight = new Map<string, Promise<ProbeResult>>();
  /**
   * Set when `/usage` came back as something other than a zero-turn command result, i.e. the
   * CLI treated it as an AI prompt. Further runs would spend the user's quota on every
   * refresh, so the adapter stops calling agy until the app restarts.
   */
  let slashCommandUnsupported = false;

  const resolveCli = (): AgyCliResolution =>
    options.resolveCli?.() ?? resolveAgyCli(deps.env, options.resolveDeps ?? { ...defaultResolveDeps(), env: deps.env });

  const profileDirOf = (account: Account): string => {
    if (account.provider !== 'antigravity' || !isPathInside(profilesRoot, account.profileDir)) {
      throw new ProviderError('internal', 'antigravity profile dir is outside the profiles root');
    }
    return path.resolve(account.profileDir);
  };

  const fail = (state: 'error' | 'unavailable' | 'logged-out', code: ErrorCode): ProbeResult => ({ kind: 'failed', state, code });

  const probeOnce = async (account: Account, signal: AbortSignal): Promise<ProbeResult> => {
    if (slashCommandUnsupported) return fail('unavailable', 'cli-unsupported-version');
    let dir: string;
    try {
      dir = profileDirOf(account);
      await mkdir(dir, { recursive: true });
    } catch (error) {
      logger.error('antigravity working dir unusable', { accountId: account.id, error });
      return fail('error', 'internal');
    }
    const cli = resolveCli();
    if (!cli.ok) return fail('error', cli.code);

    let result;
    try {
      result = await run(
        cli.command,
        ['-p', '/usage', '--output-format', 'json', '--print-timeout', `${timeouts.printTimeoutSec}s`],
        // An empty widget-owned cwd: agy must not pick up a project from wherever the app started.
        { env: AGY_ENV_POLICY, parentEnv: deps.env, cwd: dir, timeoutMs: timeouts.usageMs, signal },
      );
    } catch (error) {
      if (signal.aborted) return fail('error', 'cancelled');
      return fail('error', error instanceof SpawnError && error.code === 'cli-not-found' ? 'cli-not-found' : 'spawn-failed');
    }
    if (result.aborted) return fail('error', 'cancelled');
    if (result.timedOut) return fail('error', 'timeout');

    const parsed = parseAgyUsage(result.stdout);
    if (parsed.kind === 'ok') {
      if (parsed.windows.length === 0) return fail('unavailable', 'quota-unavailable');
      return { kind: 'ok', windows: parsed.windows };
    }
    if (parsed.kind === 'not-usage-command') {
      slashCommandUnsupported = true;
      logger.warn('agy did not expand /usage as a command; antigravity polling is off until restart', { accountId: account.id });
      return fail('unavailable', 'cli-unsupported-version');
    }
    const text = stripAnsi(`${result.stdout}\n${result.stderr}`);
    if (SIGNED_OUT_PATTERN.test(text)) return fail('logged-out', 'not-logged-in');
    // Output may name the account, so only the status, a masked short reason and the first stderr
    // line are kept. The one failure seen so far (26.09.20 08:12) could not be explained because
    // nothing but "failed" had been recorded.
    const stderrLine = stripAnsi(result.stderr).split(/\r?\n/).find((line) => line.trim() !== '');
    logger.info('agy usage run failed', {
      accountId: account.id,
      exitCode: result.exitCode,
      parse: parsed.kind,
      status: parsed.kind === 'failed' ? parsed.status : undefined,
      reason: parsed.kind === 'failed' && parsed.reason !== undefined ? maskSecrets(parsed.reason) : undefined,
      stderr: stderrLine === undefined ? undefined : maskSecrets(stderrLine.trim().slice(0, 160)),
      durationMs: result.durationMs,
    });
    if (NETWORK_PATTERN.test(text)) return fail('error', 'network');
    return fail('error', parsed.kind === 'failed' ? 'provider-error' : 'parse-error');
  };

  /** One agy process per account at a time; concurrent callers share the run. */
  const probe = (account: Account, signal: AbortSignal): Promise<ProbeResult> => {
    const running = inFlight.get(account.id);
    if (running !== undefined) return running;
    const promise = probeOnce(account, signal).finally(() => {
      if (inFlight.get(account.id) === promise) inFlight.delete(account.id);
    });
    inFlight.set(account.id, promise);
    return promise;
  };

  const prime = (map: Map<string, Primed>, accountId: string, result: ProbeResult): void => {
    if (result.kind === 'failed' && result.code === 'cancelled') return;
    map.set(accountId, { at: deps.now(), result });
  };

  const takePrimed = (map: Map<string, Primed>, accountId: string): ProbeResult | undefined => {
    const entry = map.get(accountId);
    map.delete(accountId);
    if (entry === undefined || deps.now() - entry.at > primeTtlMs) return undefined;
    return entry.result;
  };

  const toSnapshot = (account: Account, result: ProbeResult): UsageSnapshot => {
    const base = { accountId: account.id, provider: 'antigravity' as const, source: 'antigravity-cli-usage' as const };
    if (result.kind === 'failed') return createEmptySnapshot({ ...base, state: result.state, errorCode: result.code });
    const now = deps.now();
    return { ...base, state: 'ok', windows: result.windows.map((w) => ({ ...w })), measuredAt: now, lastSuccessAt: now };
  };

  return {
    id: 'antigravity',
    // Sign-in happens in the user's own terminal; the widget never opens a login URL for it.
    loginUrlHosts: [],

    async detectCli(signal) {
      const cli = resolveCli();
      if (!cli.ok) return { found: false, errorCode: cli.code };
      try {
        const result = await run(cli.command, ['--version'], {
          env: AGY_ENV_POLICY,
          parentEnv: deps.env,
          timeoutMs: timeouts.versionMs,
          signal,
        });
        const info: CliInfo = { found: true, path: cli.source };
        const version = parseAgyVersion(`${result.stdout}\n${result.stderr}`);
        if (version !== undefined) info.version = version;
        if (result.timedOut) info.errorCode = 'timeout';
        else if (result.aborted) info.errorCode = 'cancelled';
        return info;
      } catch (error) {
        const code: ErrorCode = error instanceof SpawnError && error.code === 'cli-not-found' ? 'cli-not-found' : 'spawn-failed';
        return { found: false, errorCode: code };
      }
    },

    async ensureProfileDir(account) {
      await mkdir(profileDirOf(account), { recursive: true });
    },

    /** No widget-driven login exists (PROVIDER_TRAITS.antigravity.widgetLogin is false); answer instead of hanging. */
    startLogin(_account, emit: (event: LoginEvent) => void) {
      try {
        emit({ type: 'error', code: 'not-implemented' });
      } catch (error) {
        logger.warn('login event listener threw', error);
      }
      return Promise.resolve();
    },

    async getIdentity(account, signal): Promise<ProviderIdentity> {
      const result = takePrimed(primedForIdentity, account.id) ?? (await probe(account, signal));
      prime(primedForUsage, account.id, result);
      // `/usage` only answers for a signed-in CLI; it reports neither e-mail nor plan.
      if (result.kind === 'ok') return { loggedIn: true };
      if (result.state === 'logged-out') return { loggedIn: false };
      throw new ProviderError(result.code, 'antigravity login state could not be determined');
    },

    async fetchUsage(account, signal) {
      const result = takePrimed(primedForUsage, account.id) ?? (await probe(account, signal));
      prime(primedForIdentity, account.id, result);
      return toSnapshot(account, result);
    },

    async removeProfile(account) {
      const dir = profileDirOf(account);
      primedForUsage.delete(account.id);
      primedForIdentity.delete(account.id);
      await inFlight.get(account.id)?.catch(() => undefined);
      // Only the widget-owned working dir; the user's agy sign-in is untouched.
      await rm(dir, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
    },
  };
}
