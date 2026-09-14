// Claude provider (DECISIONS 26.09.15 02:23): official CLI login in an isolated
// CLAUDE_CONFIG_DIR, identity via `claude auth status --json`, usage only from the
// statusline bridge record. No credential files are read and no Anthropic API is called.

import { mkdir, rm } from 'node:fs/promises';
import path from 'node:path';
import type { Account, ErrorCode, UsageSnapshot } from '../../../shared/types';
import { createEmptySnapshot } from '../../../shared/usage';
import { defaultResolveDeps, resolveCommand, type ResolveResult } from '../../cli/resolve';
import { SpawnError, run as runProcess, spawnLongLived as spawnLongLivedProcess, type ResolvedCommand } from '../../cli/spawn';
import { isPathInside } from '../../paths';
import { ProviderError, type CliInfo, type ClaudeProviderAdapter, type ProviderDeps, type ProviderIdentity } from '../types';
import { errorCodeOf, type BridgeRuntime } from './bridge-files';
import { createBridgeService } from './bridge-service';
import { claudeEnvPolicy } from './env';
import { parseAuthStatus, parseClaudeVersion } from './identity';
import { CLAUDE_LOGIN_URL_HOSTS, createLoginManager } from './login';

export const CLAUDE_IDENTITY_TIMEOUT_MS = 30_000;
export const CLAUDE_VERSION_TIMEOUT_MS = 15_000;

/** Test seams; production uses the shared resolver and spawn helpers. */
export interface ClaudeAdapterOverrides {
  resolve?: (nameOrPath: string) => ResolveResult;
  run?: typeof runProcess;
  spawnLongLived?: typeof spawnLongLivedProcess;
}

function resolveFailureCode(result: ResolveResult): ErrorCode {
  if (!result.ok && result.code === 'node-not-found') return 'node-not-found';
  if (!result.ok && result.code === 'unsupported-shim') return 'cli-unsupported-install';
  return 'cli-not-found';
}

function spawnFailureCode(error: unknown): ErrorCode {
  return error instanceof SpawnError && error.code === 'cli-not-found' ? 'cli-not-found' : 'spawn-failed';
}

export function createClaudeAdapter(deps: ProviderDeps, overrides: ClaudeAdapterOverrides = {}): ClaudeProviderAdapter {
  const logger = deps.logger;
  const resolve = overrides.resolve ?? ((name: string) => resolveCommand(name, { ...defaultResolveDeps(), env: deps.env }));
  const run = overrides.run ?? runProcess;
  const login = createLoginManager({ logger, spawn: overrides.spawnLongLived ?? spawnLongLivedProcess });
  const claudeProfilesRoot = path.join(deps.profilesRoot, 'claude');
  // CLI runs per account (cwd = profile dir); removeProfile waits for them so the folder can be deleted.
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

  // Node starts ~3x faster than Windows PowerShell 5.1 (measured 260 ms vs 850 ms); fuse runAsNode is off.
  const resolveRuntime = (): BridgeRuntime => {
    const node = resolve('node');
    return node.ok && node.kind === 'exe' ? 'node' : 'powershell';
  };
  const bridge = createBridgeService(deps, resolveRuntime);

  const resolveClaude = (): ResolveResult => {
    const onPath = resolve('claude');
    if (onPath.ok) return onPath;
    const installerDefault = resolve(path.join(deps.homeDir, '.local', 'bin', 'claude.exe'));
    return installerDefault.ok ? installerDefault : onPath;
  };

  const assertProfile = (account: Account): void => {
    if (account.provider !== 'claude') throw new ProviderError('internal', 'not a claude account');
    if (!isPathInside(claudeProfilesRoot, account.profileDir)) {
      throw new ProviderError('internal', 'profile dir is outside the claude profiles root');
    }
  };

  const ensureProfileDir = async (account: Account): Promise<void> => {
    assertProfile(account);
    await mkdir(account.profileDir, { recursive: true });
    try {
      await bridge.installForProfile(account);
    } catch (error) {
      logger.warn('statusline bridge not installed for profile', { accountId: account.id, code: errorCodeOf(error) });
    }
  };

  const getIdentity = async (account: Account, signal: AbortSignal): Promise<ProviderIdentity> => {
    assertProfile(account);
    const resolved = resolveClaude();
    if (!resolved.ok) throw new ProviderError(resolveFailureCode(resolved), 'claude CLI not found');
    return track(account.id, signal, async (opSignal) => {
      await mkdir(account.profileDir, { recursive: true });
      let result;
      try {
        result = await run(resolved.command, ['auth', 'status', '--json'], {
          env: claudeEnvPolicy(account.profileDir),
          parentEnv: deps.env,
          cwd: account.profileDir,
          timeoutMs: CLAUDE_IDENTITY_TIMEOUT_MS,
          signal: opSignal,
        });
      } catch (error) {
        throw new ProviderError(spawnFailureCode(error), 'auth status did not start', { cause: error });
      }
      if (result.aborted) throw new ProviderError('cancelled');
      if (result.timedOut) throw new ProviderError('timeout');
      const parsed = parseAuthStatus(result.stdout);
      if (!parsed.ok) throw new ProviderError('parse-error', 'unexpected auth status output');
      return parsed.identity;
    });
  };

  const runVersion = async (command: ResolvedCommand, signal?: AbortSignal): Promise<CliInfo> => {
    // A widget-owned scratch config dir keeps `--version` away from the user's ~/.claude.
    const scratch = path.join(deps.localDataRoot, 'tmp', 'claude-detect');
    await mkdir(scratch, { recursive: true });
    const options = { env: claudeEnvPolicy(scratch), parentEnv: deps.env, cwd: scratch, timeoutMs: CLAUDE_VERSION_TIMEOUT_MS };
    const result = await run(command, ['--version'], signal === undefined ? options : { ...options, signal });
    const info: CliInfo = { found: true };
    const version = result.exitCode === 0 ? parseClaudeVersion(result.stdout) : undefined;
    if (version !== undefined) info.version = version;
    if (result.timedOut) info.errorCode = 'timeout';
    return info;
  };

  return {
    id: 'claude',
    loginUrlHosts: CLAUDE_LOGIN_URL_HOSTS,

    async detectCli(signal) {
      const resolved = resolveClaude();
      if (!resolved.ok) return { found: false, errorCode: resolveFailureCode(resolved) };
      try {
        const info = await runVersion(resolved.command, signal);
        return { ...info, path: resolved.source };
      } catch (error) {
        return { found: false, errorCode: error instanceof SpawnError ? spawnFailureCode(error) : 'internal' };
      }
    },

    ensureProfileDir,

    async startLogin(account, emit, signal) {
      assertProfile(account);
      const resolved = resolveClaude();
      if (!resolved.ok) {
        emit({ type: 'error', code: resolveFailureCode(resolved) });
        return;
      }
      try {
        await ensureProfileDir(account);
      } catch (error) {
        emit({ type: 'error', code: errorCodeOf(error) });
        return;
      }
      await login.start({
        accountId: account.id,
        command: resolved.command,
        env: claudeEnvPolicy(account.profileDir),
        parentEnv: deps.env,
        cwd: account.profileDir,
        emit,
        signal,
        verify: (verifySignal) => getIdentity(account, verifySignal),
      });
    },

    submitPaste(account, text) {
      return login.submitPaste(account.id, text);
    },

    getIdentity,

    async fetchUsage(account, signal): Promise<UsageSnapshot> {
      assertProfile(account);
      if (signal.aborted) {
        return createEmptySnapshot({
          accountId: account.id,
          provider: 'claude',
          source: 'claude-statusline',
          state: 'error',
          errorCode: 'cancelled',
        });
      }
      try {
        return await bridge.readUsage(account);
      } catch (error) {
        logger.warn('bridge record read failed', { accountId: account.id, code: errorCodeOf(error) });
        return createEmptySnapshot({
          accountId: account.id,
          provider: 'claude',
          source: 'claude-statusline',
          state: 'error',
          errorCode: errorCodeOf(error),
        });
      }
    },

    async removeProfile(account) {
      if (!isPathInside(claudeProfilesRoot, account.profileDir)) {
        throw new ProviderError('internal', 'refusing to delete outside the claude profiles root');
      }
      const running = [...(active.get(account.id) ?? [])];
      for (const operation of running) operation.controller.abort();
      await Promise.all(running.map((operation) => operation.done));
      await login.cancel(account.id);
      // Windows can briefly keep the folder busy after a child exits (antivirus, handle release).
      await rm(account.profileDir, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
      await bridge.removeAccountData(account);
    },

    bridge: {
      status: () => bridge.status(),
      installDefault: (target) => bridge.installDefault(target),
      uninstallDefault: () => bridge.uninstallDefault(),
    },
  };
}
