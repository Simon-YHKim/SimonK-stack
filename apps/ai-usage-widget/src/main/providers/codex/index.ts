// Codex provider (DECISIONS 26.09.15 02:23, DESIGN 7-2): per-account CODEX_HOME,
// official `codex app-server` over stdio, device-code login, account/rateLimits/read.

import { existsSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import { mkdir, rm } from 'node:fs/promises';
import path from 'node:path';
import type { Account, ErrorCode, LoginEvent, UsageSnapshot } from '../../../shared/types';
import { createEmptySnapshot } from '../../../shared/usage';
import { JsonRpcClosedError } from '../../cli/jsonrpc';
import { defaultResolveDeps, resolveCommand, type ResolveResult } from '../../cli/resolve';
import { run } from '../../cli/spawn';
import { isPathInside, profileDirFor } from '../../paths';
import { ProviderError, type CliInfo, type ProviderAdapter, type ProviderDeps, type ProviderIdentity } from '../types';
import { classifyFailure, classifyLoginError, resolveFailureCode, stateForCode, type CodexFailure } from './errors';
import {
  METHOD,
  parseAccountRead,
  parseLoginCompleted,
  parseLoginStartResult,
  parseRateLimits,
  parseResetOffer,
  parseConsumeResetOutcome,
  samePath,
  type CodexAccountInfo,
  type DeviceCodeStart,
  type LoginCompleted,
} from './protocol';
import { codexEnvPolicy, DEFAULT_TIMEOUTS, openCodexSession, type CodexSession, type CodexTimeouts } from './session';

export interface CodexAdapterOptions {
  /** Test seam: how the `codex` command is located. Default: PATH lookup via `resolveCommand`. */
  resolveCli?: (env: NodeJS.ProcessEnv) => ResolveResult;
  timeouts?: Partial<CodexTimeouts>;
}

const SOURCE = 'codex-app-server';
const VERSION_RE = /codex-cli\s+v?(\d+\.\d+\.\d+[0-9A-Za-z.+-]*)/i;
const LOOSE_VERSION_RE = /\b(\d+\.\d+\.\d+[0-9A-Za-z.+-]*)\b/;

type LoginOutcome =
  | { kind: 'completed'; completed: LoginCompleted }
  | { kind: 'aborted' }
  | { kind: 'timeout' }
  | { kind: 'closed' };

interface ActiveOperation {
  controller: AbortController;
  done: Promise<unknown>;
}

export function createCodexAdapter(deps: ProviderDeps, options: CodexAdapterOptions = {}): ProviderAdapter {
  const timeouts: CodexTimeouts = { ...DEFAULT_TIMEOUTS, ...options.timeouts };
  const logger = deps.logger;
  const resolveCli =
    options.resolveCli ?? ((env: NodeJS.ProcessEnv) => resolveCommand('codex', { ...defaultResolveDeps(), env }));
  const active = new Map<string, Set<ActiveOperation>>();
  /** Prevent periodic reads from opening a second app-server while a native redemption dialog is open. */
  const redeeming = new Set<string>();

  /** The only CODEX_HOME an account may use: `<profilesRoot>\codex\<id>`, never ~/.codex. */
  const profileDirOf = (account: Account): string => {
    if (account.provider !== 'codex') throw new ProviderError('internal', 'not a codex account');
    let expected: string;
    try {
      expected = profileDirFor(deps.profilesRoot, 'codex', account.id);
    } catch (error) {
      throw new ProviderError('internal', 'invalid codex account id', { cause: error });
    }
    if (!samePath(expected, account.profileDir)) {
      throw new ProviderError('internal', 'codex profile dir is outside the widget profiles root');
    }
    return expected;
  };

  const trackOperation = <T>(account: Account, signal: AbortSignal, body: (signal: AbortSignal) => Promise<T>): Promise<T> => {
    const controller = new AbortController();
    const linked = AbortSignal.any([signal, controller.signal]);
    const promise = body(linked);
    const entry: ActiveOperation = { controller, done: promise.catch(() => undefined) };
    let set = active.get(account.id);
    if (set === undefined) {
      set = new Set();
      active.set(account.id, set);
    }
    set.add(entry);
    const owner = set;
    void entry.done.then(() => {
      owner.delete(entry);
      if (owner.size === 0 && active.get(account.id) === owner) active.delete(account.id);
    });
    return promise;
  };

  /**
   * Aborts this account's running operations and waits until their app-server processes are
   * gone. Two app-servers must never initialise the same CODEX_HOME at once: a login started
   * while a cancelled identity read was still shutting down died with `protocol-error` on a
   * brand-new profile (log 26.09.19 12:01, DECISIONS 26.09.20 10:51).
   */
  const quiesce = async (accountId: string): Promise<void> => {
    const running = [...(active.get(accountId) ?? [])];
    for (const operation of running) operation.controller.abort();
    await Promise.all(running.map((operation) => operation.done));
  };

  const sessionLifetime = (rpcCount: number): number => timeouts.initMs + rpcCount * timeouts.rpcMs + 10_000;

  /** Adds process-exit context to failures (lifetime timeout vs. crash). */
  const explainFailure = (error: unknown, session: CodexSession | null, signal: AbortSignal): CodexFailure => {
    if (signal.aborted) return { state: 'error', code: 'cancelled' };
    const exit = session?.exitInfo() ?? null;
    if (error instanceof JsonRpcClosedError && exit !== null) {
      if (exit.timedOut) return { state: 'error', code: 'timeout' };
      if (exit.aborted) return { state: 'error', code: 'cancelled' };
    }
    return classifyFailure(error);
  };

  const readAccount = async (session: CodexSession, signal: AbortSignal) => {
    const raw = await session.client.request(METHOD.accountRead, {}, { timeoutMs: timeouts.rpcMs, signal });
    const info = parseAccountRead(raw);
    if (info === null) throw new ProviderError('parse-error', 'invalid account/read response');
    return info;
  };

  const failedSnapshot = (account: Account, failure: CodexFailure): UsageSnapshot =>
    createEmptySnapshot({
      accountId: account.id,
      provider: 'codex',
      source: SOURCE,
      state: failure.state,
      errorCode: failure.code,
    });

  const adapter: ProviderAdapter = {
    id: 'codex',
    // Documented device page is auth.openai.com/codex/device (RESEARCH 3-2); confirm in T1.
    loginUrlHosts: ['openai.com'],

    async detectCli(signal?: AbortSignal): Promise<CliInfo> {
      const resolved = resolveCli(deps.env);
      if (!resolved.ok) return { found: false, errorCode: resolveFailureCode(resolved.code) };
      // `--version` initialises CODEX_HOME, so it runs against a widget-owned folder, never ~/.codex.
      const detectHome = path.join(deps.localDataRoot, 'cli-detect', 'codex');
      try {
        await mkdir(detectHome, { recursive: true });
        const result = await run(resolved.command, ['--version'], {
          env: codexEnvPolicy(detectHome),
          cwd: detectHome,
          timeoutMs: timeouts.versionMs,
          signal,
          parentEnv: deps.env,
          maxOutputBytes: 64 * 1024,
        });
        const info: CliInfo = { found: true, path: resolved.source };
        if (result.aborted) return { ...info, errorCode: 'cancelled' };
        if (result.timedOut) return { ...info, errorCode: 'timeout' };
        if (result.exitCode !== 0) return { ...info, errorCode: 'spawn-failed' };
        const version = VERSION_RE.exec(result.stdout)?.[1] ?? LOOSE_VERSION_RE.exec(result.stdout)?.[1];
        if (version !== undefined) info.version = version;
        return info;
      } catch (error) {
        const failure = classifyFailure(error);
        logger.warn('codex --version failed', { code: failure.code });
        return failure.code === 'cli-not-found'
          ? { found: false, errorCode: 'cli-not-found' }
          : { found: true, path: resolved.source, errorCode: failure.code };
      }
    },

    async ensureProfileDir(account: Account): Promise<void> {
      await mkdir(profileDirOf(account), { recursive: true });
    },

    async startLogin(account: Account, emit: (event: LoginEvent) => void, signal: AbortSignal): Promise<void> {
      let finished = false;
      const send = (event: LoginEvent): void => {
        if (finished) return;
        if (event.type === 'success' || event.type === 'error') finished = true;
        try {
          emit(event);
        } catch (error) {
          logger.warn('login event listener threw', error);
        }
      };
      const fail = (code: ErrorCode): void => {
        logger.info('codex login finished', { accountId: account.id, result: code });
        send({ type: 'error', code });
      };

      let codexHome: string;
      try {
        codexHome = profileDirOf(account);
      } catch (error) {
        fail(classifyFailure(error).code);
        return;
      }
      send({ type: 'progress', stage: 'starting' });
      const resolved = resolveCli(deps.env);
      if (!resolved.ok) {
        fail(resolveFailureCode(resolved.code));
        return;
      }

      await quiesce(account.id);
      if (signal.aborted) {
        fail('cancelled');
        return;
      }

      await trackOperation(account, signal, async (opSignal) => {
        let session: CodexSession | null = null;
        let loginId: string | null = null;
        try {
          await mkdir(codexHome, { recursive: true });
          session = await openCodexSession({
            command: resolved.command,
            codexHome,
            appVersion: deps.appVersion,
            parentEnv: deps.env,
            lifetimeMs: timeouts.initMs + timeouts.loginStartMs + timeouts.loginMs + 60_000,
            timeouts,
            signal: opSignal,
            killOnAbort: false,
            logger,
          });
          const current = session;

          // Subscribe before starting so an early completion cannot be missed.
          let onCompleted: (completed: LoginCompleted) => void = () => undefined;
          const completedPromise = new Promise<LoginCompleted>((resolve) => {
            onCompleted = resolve;
          });
          const unsubscribe = current.client.onNotification(METHOD.loginCompleted, (params) => {
            const completed = parseLoginCompleted(params);
            if (completed === null) return;
            if (loginId !== null && completed.loginId !== null && completed.loginId !== loginId) return;
            onCompleted(completed);
          });

          try {
            let start: DeviceCodeStart | null;
            try {
              const raw = await current.client.request(
                METHOD.loginStart,
                { type: 'chatgptDeviceCode' },
                { timeoutMs: timeouts.loginStartMs, signal: opSignal },
              );
              start = parseLoginStartResult(raw);
            } catch (error) {
              const failure = explainFailure(error, current, opSignal);
              const code =
                failure.code === 'provider-error' || failure.code === 'network'
                  ? classifyLoginError(error instanceof Error ? error.message : '')
                  : failure.code;
              fail(code);
              return;
            }
            if (start === null) {
              fail('protocol-error');
              return;
            }
            loginId = start.loginId;
            send({ type: 'device-code', userCode: start.userCode, verificationUrl: start.verificationUrl });
            send({ type: 'progress', stage: 'waiting-device-code' });

            const outcome = await waitForLogin(completedPromise, current, opSignal, timeouts.loginMs);
            if (outcome.kind === 'aborted' || outcome.kind === 'timeout') {
              await cancelLogin(current, start.loginId);
              fail(outcome.kind === 'aborted' ? 'cancelled' : 'timeout');
              return;
            }
            if (outcome.kind === 'closed') {
              fail(current.exitInfo()?.timedOut === true ? 'timeout' : 'protocol-error');
              return;
            }
            if (!outcome.completed.success) {
              logger.info('codex login reported failure', { accountId: account.id, stage: 'completed' });
              fail(classifyLoginError(outcome.completed.error ?? ''));
              return;
            }

            // The app-server re-reads auth.json on a timer (about once a second), so account/read
            // right after a successful login can still answer "no account". That made a login that
            // had worked show as failed (profile log 26.09.19 12:02, DECISIONS 26.09.20 11:54).
            send({ type: 'progress', stage: 'verifying' });
            let identity: CodexAccountInfo | null = null;
            for (let attempt = 0; attempt < timeouts.verifyAttempts; attempt += 1) {
              if (attempt > 0) await sleep(timeouts.verifyDelayMs, opSignal);
              if (opSignal.aborted) break;
              try {
                identity = await readAccount(current, opSignal);
              } catch (error) {
                logger.warn('account/read after login failed', { code: explainFailure(error, current, opSignal).code });
                identity = null;
                break;
              }
              if (identity.kind !== 'none') break;
            }
            if (opSignal.aborted) {
              fail('cancelled');
              return;
            }
            if (identity?.kind === 'none') {
              // The CLI said the login succeeded; a lagging account view must not turn that into a failure.
              logger.warn('codex login succeeded but account/read still reports no account', { accountId: account.id });
              identity = null;
            }
            const success: Extract<LoginEvent, { type: 'success' }> = { type: 'success' };
            if (identity?.kind === 'chatgpt') {
              if (identity.emailMasked !== undefined) success.emailMasked = identity.emailMasked;
              if (identity.planType !== undefined) success.plan = identity.planType;
            }
            logger.info('codex login finished', { accountId: account.id, result: 'success' });
            send(success);
          } finally {
            unsubscribe();
          }
        } catch (error) {
          fail(explainFailure(error, session, opSignal).code);
        } finally {
          await session?.close();
          if (!finished) fail('internal');
        }
      });
    },

    async getIdentity(account: Account, signal: AbortSignal): Promise<ProviderIdentity> {
      if (redeeming.has(account.id)) throw new ProviderError('cancelled', 'reset redemption in progress');
      const codexHome = profileDirOf(account);
      if (!existsSync(codexHome)) return { loggedIn: false };
      const resolved = resolveCli(deps.env);
      if (!resolved.ok) throw new ProviderError(resolveFailureCode(resolved.code));

      return trackOperation(account, signal, async (opSignal) => {
        let session: CodexSession | null = null;
        try {
          session = await openCodexSession({
            command: resolved.command,
            codexHome,
            appVersion: deps.appVersion,
            parentEnv: deps.env,
            lifetimeMs: sessionLifetime(1),
            timeouts,
            signal: opSignal,
            killOnAbort: true,
            logger,
          });
          const info = await readAccount(session, opSignal);
          if (info.kind === 'none') return { loggedIn: false };
          const identity: ProviderIdentity = { loggedIn: true };
          if (info.kind === 'chatgpt') {
            if (info.emailMasked !== undefined) identity.emailMasked = info.emailMasked;
            if (info.planType !== undefined) identity.plan = info.planType;
          }
          return identity;
        } catch (error) {
          const failure = explainFailure(error, session, opSignal);
          if (failure.state === 'logged-out') return { loggedIn: false };
          logger.warn('codex identity read failed', { accountId: account.id, code: failure.code });
          throw new ProviderError(failure.code, 'codex identity read failed', { cause: error });
        } finally {
          await session?.close();
        }
      });
    },

    async fetchUsage(account: Account, signal: AbortSignal): Promise<UsageSnapshot> {
      if (redeeming.has(account.id)) return failedSnapshot(account, { state: 'error', code: 'cancelled' });
      let codexHome: string;
      try {
        codexHome = profileDirOf(account);
      } catch (error) {
        return failedSnapshot(account, classifyFailure(error));
      }
      // No profile folder means the account never signed in; do not create folders from a read.
      if (!existsSync(codexHome)) return failedSnapshot(account, { state: 'logged-out', code: 'not-logged-in' });
      const resolved = resolveCli(deps.env);
      if (!resolved.ok) {
        const code = resolveFailureCode(resolved.code);
        return failedSnapshot(account, { state: stateForCode(code), code });
      }

      return trackOperation(account, signal, async (opSignal) => {
        let session: CodexSession | null = null;
        try {
          session = await openCodexSession({
            command: resolved.command,
            codexHome,
            appVersion: deps.appVersion,
            parentEnv: deps.env,
            lifetimeMs: sessionLifetime(2),
            timeouts,
            signal: opSignal,
            killOnAbort: true,
            logger,
          });
          const identity = await readAccount(session, opSignal);
          if (identity.kind === 'none') return failedSnapshot(account, { state: 'logged-out', code: 'not-logged-in' });
          if (identity.kind === 'other') {
            return failedSnapshot(account, { state: 'unavailable', code: 'quota-unavailable' });
          }

          const raw = await session.client.request(
            METHOD.rateLimitsRead,
            { excludeResetCreditDetails: true },
            { timeoutMs: timeouts.rpcMs, signal: opSignal },
          );
          const limits = parseRateLimits(raw);
          if (limits === null) throw new ProviderError('parse-error', 'invalid account/rateLimits/read response');
          const plan = identity.planType ?? limits.planType;
          if (limits.windows.length === 0) {
            const snapshot = failedSnapshot(account, { state: 'unavailable', code: 'quota-unavailable' });
            if (plan !== undefined) snapshot.plan = plan;
            return snapshot;
          }
          const now = deps.now();
          const snapshot: UsageSnapshot = {
            accountId: account.id,
            provider: 'codex',
            state: 'ok',
            windows: limits.windows,
            measuredAt: now,
            lastSuccessAt: now,
            source: SOURCE,
          };
          if (plan !== undefined) snapshot.plan = plan;
          if (limits.resetCreditCount !== undefined) snapshot.resetCreditsAvailable = limits.resetCreditCount;
          logger.debug('codex usage read', {
            accountId: account.id,
            windows: limits.windows.length,
            hasCredits: limits.credits?.hasCredits,
            limitReached: limits.rateLimitReachedType,
          });
          return snapshot;
        } catch (error) {
          const failure = explainFailure(error, session, opSignal);
          logger.warn('codex usage read failed', { accountId: account.id, code: failure.code });
          return failedSnapshot(account, failure);
        } finally {
          await session?.close();
        }
      });
    },

    async redeemResetCredit(account, confirm, signal) {
      const codexHome = profileDirOf(account);
      if (!existsSync(codexHome)) return 'unavailable';
      const resolved = resolveCli(deps.env);
      if (!resolved.ok) return 'unavailable';
      if (redeeming.has(account.id)) return 'unavailable';
      redeeming.add(account.id);
      try {
        await quiesce(account.id);
        return await trackOperation(account, signal, async (opSignal) => {
          let session: CodexSession | null = null;
          try {
            session = await openCodexSession({
              command: resolved.command, codexHome, appVersion: deps.appVersion, parentEnv: deps.env,
              lifetimeMs: sessionLifetime(5) + 120_000, timeouts, signal: opSignal,
              killOnAbort: true, logger,
            });
            const identity = await readAccount(session, opSignal);
            if (identity.kind !== 'chatgpt') return 'unavailable';
            const readOffer = async () => parseResetOffer(await session!.client.request(
              METHOD.rateLimitsRead, { excludeResetCreditDetails: false },
              { timeoutMs: timeouts.rpcMs, signal: opSignal },
            ), deps.now());
            const offer = await readOffer();
            if (offer === null) return 'unavailable';
            if (!await confirm({ availableCount: offer.availableCount, expiresAt: offer.expiresAt })) return 'cancelled';
            if (opSignal.aborted) return 'cancelled';
            const current = await readOffer();
            if (current === null || current.backendAccountId !== offer.backendAccountId || current.creditId !== offer.creditId) {
              return 'unavailable';
            }
            const raw = await session.client.request(METHOD.resetCreditConsume,
              { idempotencyKey: randomUUID(), creditId: offer.creditId },
              { timeoutMs: timeouts.rpcMs, signal: opSignal });
            return parseConsumeResetOutcome(raw) ?? 'unavailable';
          } finally {
            await session?.close();
          }
        });
      } finally {
        redeeming.delete(account.id);
      }
    },

    async removeProfile(account: Account): Promise<void> {
      const codexHome = profileDirOf(account);
      if (!isPathInside(deps.profilesRoot, codexHome)) {
        throw new ProviderError('internal', 'refusing to delete outside the profiles root');
      }
      await quiesce(account.id);
      await rm(codexHome, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
    },
  };

  async function cancelLogin(session: CodexSession, loginId: string): Promise<void> {
    try {
      await session.client.request(METHOD.loginCancel, { loginId }, { timeoutMs: timeouts.loginCancelMs });
    } catch {
      // Best effort: closing the app-server ends the device-code poll anyway.
    }
  }

  return adapter;
}

/** Resolves after `ms` or as soon as `signal` aborts; never rejects. */
function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise<void>((resolve) => {
    if (signal.aborted) {
      resolve();
      return;
    }
    const onAbort = (): void => {
      clearTimeout(timer);
      resolve();
    };
    const timer = setTimeout(() => {
      signal.removeEventListener('abort', onAbort);
      resolve();
    }, ms);
    signal.addEventListener('abort', onAbort, { once: true });
  });
}

function waitForLogin(
  completed: Promise<LoginCompleted>,
  session: CodexSession,
  signal: AbortSignal,
  timeoutMs: number,
): Promise<LoginOutcome> {
  return new Promise<LoginOutcome>((resolve) => {
    let settled = false;
    const finish = (outcome: LoginOutcome): void => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      signal.removeEventListener('abort', onAbort);
      resolve(outcome);
    };
    const onAbort = (): void => finish({ kind: 'aborted' });
    const timer = setTimeout(() => finish({ kind: 'timeout' }), timeoutMs);
    if (signal.aborted) {
      finish({ kind: 'aborted' });
      return;
    }
    signal.addEventListener('abort', onAbort, { once: true });
    void completed.then((value) => finish({ kind: 'completed', completed: value }));
    void session.process.exited.then(() => finish({ kind: 'closed' }));
  });
}
