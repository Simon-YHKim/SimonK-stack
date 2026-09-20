// Grok provider (DECISIONS 26.09.15 02:23): per-account GROK_HOME, login via
// `grok login --device-auth`, usage only through the official binary's ACP billing
// extension. The adapter never reads auth.json and never calls xAI HTTP APIs.

import { mkdir, rm } from 'node:fs/promises';
import path from 'node:path';
import type { Account, ErrorCode, LoginEvent, UsageSnapshot } from '../../../shared/types';
import { createEmptySnapshot } from '../../../shared/usage';
import { defaultResolveDeps, resolveCommand, type ResolveDeps } from '../../cli/resolve';
import {
  BASE_ENV_ALLOW,
  SpawnError,
  run,
  spawnLongLived,
  type EnvPolicy,
  type LongLivedProcess,
  type ResolvedCommand,
} from '../../cli/spawn';
import { stripAnsi } from '../../cli/text';
import { isPathInside } from '../../paths';
import { ProviderError, type CliInfo, type ProviderAdapter, type ProviderDeps, type ProviderIdentity } from '../types';
import { acpFailure, queryAcpBilling, type AcpFailure } from './acp';
import { parseBillingResponse, type GrokBilling } from './billing';
import { classifyLoginFailure, createDeviceAuthParser } from './device-auth';

export interface GrokTimeouts {
  versionMs: number;
  acpLifetimeMs: number;
  acpInitializeMs: number;
  acpRequestMs: number;
  loginMs: number;
}

export const DEFAULT_GROK_TIMEOUTS: GrokTimeouts = {
  versionMs: 20_000,
  acpLifetimeMs: 60_000,
  acpInitializeMs: 30_000,
  acpRequestMs: 20_000,
  loginMs: 10 * 60_000,
};

export type GrokCliResolution = { ok: true; command: ResolvedCommand; source: string } | { ok: false; code: ErrorCode };

export interface GrokAdapterOptions {
  /** Test hook: replaces CLI discovery. */
  resolveCli?: () => GrokCliResolution;
  resolveDeps?: ResolveDeps;
  timeouts?: Partial<GrokTimeouts>;
  /** How long a billing result from getIdentity/login may be reused by the next fetchUsage (and vice versa). */
  primeTtlMs?: number;
}

/** Credential and endpoint overrides that must never reach the child (defence in depth over the whitelist). */
export const GROK_ENV_REMOVE: readonly string[] = [
  'XAI_API_KEY',
  'XAI_MANAGEMENT_KEY',
  'GROK_HOME',
  'GROK_CONFIG',
  'GROK_CONFIG_PATH',
  'GROK_AUTH_PROVIDER_COMMAND',
  'GROK_AUTH_PROVIDER_LABEL',
  'GROK_AUTH_TOKEN_TTL',
  'GROK_AUTH_EXPIRED',
  'GROK_AUTH_EARLY_INVALIDATION_SECS',
  'GROK_OIDC_ISSUER',
  'GROK_OIDC_CLIENT_ID',
  'GROK_CLI_CHAT_PROXY_BASE_URL',
  'GROK_AGENT_SECRET',
  'GROK_LOG_FILE',
];

export function grokEnvPolicy(grokHome: string): EnvPolicy {
  return { allow: BASE_ENV_ALLOW, remove: GROK_ENV_REMOVE, set: { GROK_HOME: grokHome, NO_COLOR: '1' } };
}

/** PATH first, then the managed install `<home>\.grok\bin\grok.exe`. */
export function resolveGrokCli(homeDir: string, resolveDeps: ResolveDeps): GrokCliResolution {
  const isWin = resolveDeps.platform === 'win32';
  const onPath = resolveCommand('grok', resolveDeps);
  if (onPath.ok) return { ok: true, command: onPath.command, source: onPath.source };
  const p = isWin ? path.win32 : path.posix;
  const managed = resolveCommand(p.join(homeDir, '.grok', 'bin', isWin ? 'grok.exe' : 'grok'), resolveDeps);
  if (managed.ok) return { ok: true, command: managed.command, source: managed.source };
  if (onPath.code === 'node-not-found') return { ok: false, code: 'node-not-found' };
  return { ok: false, code: onPath.code === 'unsupported-shim' ? 'cli-unsupported-install' : 'cli-not-found' };
}

/** `grok 1.0.30 (04b7ffed98c6) [stable]` -> `1.0.30`. */
export function parseGrokVersion(output: string): string | undefined {
  const text = stripAnsi(output);
  const match = /\bgrok\s+v?(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)/i.exec(text) ?? /\b(\d+\.\d+\.\d+)\b/.exec(text);
  return match?.[1];
}

type ProbeResult = { kind: 'ok'; billing: GrokBilling } | { kind: 'failed'; failure: AcpFailure };

interface Primed {
  at: number;
  result: ProbeResult;
}

const LOGIN_TAIL_LINES = 40;

export function createGrokAdapter(deps: ProviderDeps, options: GrokAdapterOptions = {}): ProviderAdapter {
  const { logger } = deps;
  const timeouts: GrokTimeouts = { ...DEFAULT_GROK_TIMEOUTS, ...options.timeouts };
  const primeTtlMs = options.primeTtlMs ?? 15_000;
  const grokProfilesRoot = path.join(deps.profilesRoot, 'grok');
  const primedForUsage = new Map<string, Primed>();
  const primedForIdentity = new Map<string, Primed>();
  // grok processes run with cwd and GROK_HOME in the profile dir; removeProfile waits for them.
  const active = new Map<string, Set<{ controller: AbortController; done: Promise<unknown> }>>();

  const track = <T>(accountId: string, signal: AbortSignal, body: (signal: AbortSignal) => Promise<T>): Promise<T> => {
    const controller = new AbortController();
    const promise = body(AbortSignal.any([signal, controller.signal]));
    const entry = { controller, done: promise.catch(() => undefined) };
    let set = active.get(accountId);
    if (set === undefined) {
      set = new Set();
      active.set(accountId, set);
    }
    set.add(entry);
    const owner = set;
    void entry.done.then(() => {
      owner.delete(entry);
      if (owner.size === 0 && active.get(accountId) === owner) active.delete(accountId);
    });
    return promise;
  };

  const resolveCli = (): GrokCliResolution =>
    options.resolveCli?.() ?? resolveGrokCli(deps.homeDir, options.resolveDeps ?? { ...defaultResolveDeps(), env: deps.env });

  const profileDirOf = (account: Account): string => {
    if (account.provider !== 'grok' || !isPathInside(grokProfilesRoot, account.profileDir)) {
      throw new ProviderError('internal', 'grok profile dir is outside the profiles root');
    }
    return path.resolve(account.profileDir);
  };

  const fail = (state: AcpFailure['state'], code: ErrorCode): ProbeResult => ({ kind: 'failed', failure: acpFailure(state, code) });

  const probe = (account: Account, signal: AbortSignal): Promise<ProbeResult> =>
    track(account.id, signal, (opSignal) => probeOnce(account, opSignal));

  const probeOnce = async (account: Account, signal: AbortSignal): Promise<ProbeResult> => {
    let dir: string;
    try {
      dir = profileDirOf(account);
      await mkdir(dir, { recursive: true });
    } catch (error) {
      logger.error('grok profile dir unusable', { accountId: account.id, error });
      return fail('error', 'internal');
    }
    const cli = resolveCli();
    if (!cli.ok) return fail('error', cli.code);
    const outcome = await queryAcpBilling({
      command: cli.command,
      env: grokEnvPolicy(dir),
      parentEnv: deps.env,
      cwd: dir,
      appVersion: deps.appVersion,
      logger,
      signal,
      lifetimeMs: timeouts.acpLifetimeMs,
      initializeMs: timeouts.acpInitializeMs,
      requestMs: timeouts.acpRequestMs,
    });
    if (outcome.kind === 'failed') {
      logger.info('grok billing unavailable', { accountId: account.id, code: outcome.failure.code });
      return outcome;
    }
    const billing = parseBillingResponse(outcome.result);
    if (billing === null) {
      logger.warn('grok billing result is not an object', { accountId: account.id });
      return fail('error', 'parse-error');
    }
    return { kind: 'ok', billing };
  };

  const prime = (map: Map<string, Primed>, accountId: string, result: ProbeResult): void => {
    if (result.kind === 'failed' && result.failure.code === 'cancelled') return;
    map.set(accountId, { at: deps.now(), result });
  };

  const takePrimed = (map: Map<string, Primed>, accountId: string): ProbeResult | undefined => {
    const entry = map.get(accountId);
    map.delete(accountId);
    if (entry === undefined || deps.now() - entry.at > primeTtlMs) return undefined;
    return entry.result;
  };

  const toSnapshot = (account: Account, result: ProbeResult): UsageSnapshot => {
    const base = { accountId: account.id, provider: 'grok' as const, source: 'grok-acp' as const };
    if (result.kind === 'failed') {
      return createEmptySnapshot({ ...base, state: result.failure.state, errorCode: result.failure.code });
    }
    const { billing } = result;
    if (billing.windows.length === 0) {
      const empty = createEmptySnapshot({ ...base, state: 'unavailable', errorCode: 'quota-unavailable' });
      if (billing.plan !== undefined) empty.plan = billing.plan;
      return empty;
    }
    const now = deps.now();
    const snapshot: UsageSnapshot = {
      ...base,
      state: 'ok',
      windows: billing.windows.map((window) => ({ ...window })),
      measuredAt: now,
      lastSuccessAt: now,
    };
    if (billing.plan !== undefined) snapshot.plan = billing.plan;
    return snapshot;
  };

  const identityFrom = (result: ProbeResult): ProviderIdentity => {
    if (result.kind === 'ok') {
      const identity: ProviderIdentity = { loggedIn: true };
      if (result.billing.plan !== undefined) identity.plan = result.billing.plan;
      return identity;
    }
    if (result.failure.state === 'logged-out') return { loggedIn: false };
    // No ACP auth-status method is advertised; without billing the login state is unknown.
    throw new ProviderError(result.failure.code, 'grok login state could not be determined');
  };

  const adapter: ProviderAdapter = {
    id: 'grok',
    // Same xAI-owned hosts that device-auth.ts accepts for verification pages.
    loginUrlHosts: ['x.ai', 'grok.com'],

    async detectCli(signal) {
      const cli = resolveCli();
      if (!cli.ok) return { found: false, errorCode: cli.code };
      try {
        const result = await run(cli.command, ['--version'], {
          // A widget-owned GROK_HOME keeps even `--version` away from the user's ~/.grok.
          env: grokEnvPolicy(path.join(deps.localDataRoot, 'cli-probe', 'grok')),
          parentEnv: deps.env,
          timeoutMs: timeouts.versionMs,
          signal,
        });
        const info: CliInfo = { found: true, path: cli.source };
        const version = parseGrokVersion(`${result.stdout}\n${result.stderr}`);
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

    startLogin(account, emit, signal) {
      return track(account.id, signal, (opSignal) => runLogin(account, emit, opSignal));
    },

    async getIdentity(account, signal) {
      const result = takePrimed(primedForIdentity, account.id) ?? (await probe(account, signal));
      prime(primedForUsage, account.id, result);
      return identityFrom(result);
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
      const running = [...(active.get(account.id) ?? [])];
      for (const operation of running) operation.controller.abort();
      await Promise.all(running.map((operation) => operation.done));
      await rm(dir, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
    },
  };

  async function runLogin(account: Account, emit: (event: LoginEvent) => void, signal: AbortSignal): Promise<void> {
    const send = (event: LoginEvent): void => {
      try {
        emit(event);
      } catch (error) {
        logger.warn('login event listener threw', error);
      }
    };
    let proc: LongLivedProcess | undefined;
    try {
      const dir = profileDirOf(account);
      await mkdir(dir, { recursive: true });
      send({ type: 'progress', stage: 'starting' });
      const cli = resolveCli();
      if (!cli.ok) {
        send({ type: 'error', code: cli.code });
        return;
      }
      if (signal.aborted) {
        send({ type: 'error', code: 'cancelled' });
        return;
      }
      try {
        proc = await spawnLongLived(cli.command, ['login', '--device-auth'], {
          env: grokEnvPolicy(dir),
          parentEnv: deps.env,
          cwd: dir,
          timeoutMs: timeouts.loginMs,
          signal,
        });
      } catch (error) {
        const code: ErrorCode = signal.aborted
          ? 'cancelled'
          : error instanceof SpawnError && error.code === 'cli-not-found'
            ? 'cli-not-found'
            : 'spawn-failed';
        send({ type: 'error', code });
        return;
      }

      const parser = createDeviceAuthParser(deps.now);
      // Kept in memory only to classify a failure; never logged (may contain URLs or codes).
      const tail: string[] = [];
      const onLine = (raw: string): void => {
        const line = stripAnsi(raw);
        tail.push(line);
        if (tail.length > LOGIN_TAIL_LINES) tail.shift();
        const prompt = parser.push(line);
        if (prompt === null) return;
        logger.info('grok device code received', { accountId: account.id });
        const event: LoginEvent = { type: 'device-code', userCode: prompt.userCode, verificationUrl: prompt.verificationUrl };
        if (prompt.expiresAt !== undefined) event.expiresAt = prompt.expiresAt;
        send(event);
        send({ type: 'progress', stage: 'waiting-device-code' });
      };
      const offStdout = proc.onStdoutLine(onLine);
      const offStderr = proc.onStderrLine(onLine);
      const exit = await proc.exited;
      offStdout();
      offStderr();

      if (exit.aborted || signal.aborted) {
        send({ type: 'error', code: 'cancelled' });
        return;
      }
      if (exit.timedOut) {
        send({ type: 'error', code: 'timeout' });
        return;
      }
      if (exit.exitCode !== 0) {
        const code = classifyLoginFailure(tail.join('\n'));
        logger.info('grok login exited with failure', { accountId: account.id, exitCode: exit.exitCode, code });
        send({ type: 'error', code });
        return;
      }

      send({ type: 'progress', stage: 'verifying' });
      const result = await probe(account, signal);
      prime(primedForUsage, account.id, result);
      if (result.kind === 'ok') {
        const success: LoginEvent = { type: 'success' };
        if (result.billing.plan !== undefined) success.plan = result.billing.plan;
        send(success);
      } else if (result.failure.code === 'cancelled') {
        send({ type: 'error', code: 'cancelled' });
      } else if (result.failure.state === 'logged-out') {
        send({ type: 'error', code: 'login-failed' });
      } else {
        // The CLI reported success; a billing problem must not turn that into a login failure.
        send({ type: 'success' });
      }
    } catch (error) {
      logger.error('grok login failed unexpectedly', { accountId: account.id, error });
      if (proc !== undefined) await proc.kill();
      send({ type: 'error', code: 'internal' });
    }
  }

  return adapter;
}
