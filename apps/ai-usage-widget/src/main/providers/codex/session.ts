// One short-lived `codex app-server` conversation over stdio for one account.

import { createJsonRpcClient, transportFromProcess, type JsonRpcClient } from '../../cli/jsonrpc';
import { spawnLongLived, type EnvPolicy, type ExitInfo, type LongLivedProcess, type ResolvedCommand } from '../../cli/spawn';
import type { Logger } from '../../log';
import { ProviderError } from '../types';
import { CLIENT_NAME, METHOD, parseInitializeResult, samePath, type InitializeInfo } from './protocol';

export interface CodexTimeouts {
  initMs: number;
  rpcMs: number;
  /** `account/login/start` contacts the auth server, so it gets more than a plain rpc. */
  loginStartMs: number;
  /** Waiting for the user to finish device-code sign-in. */
  loginMs: number;
  loginCancelMs: number;
  /** Grace period after closing stdin before the process tree is killed. */
  exitGraceMs: number;
  versionMs: number;
  /** account/read tries after a successful login, while the app-server still reloads auth.json. */
  verifyAttempts: number;
  verifyDelayMs: number;
}

export const DEFAULT_TIMEOUTS: Readonly<CodexTimeouts> = {
  initMs: 30_000,
  rpcMs: 10_000,
  loginStartMs: 30_000,
  loginMs: 10 * 60_000,
  loginCancelMs: 3_000,
  exitGraceMs: 1_500,
  versionMs: 15_000,
  // The reload timer ticks about once a second: five tries cover four ticks.
  verifyAttempts: 5,
  verifyDelayMs: 1_000,
};

/**
 * Parent variables passed to codex (verified sufficient by the empty-home probe).
 * Everything else, including OPENAI_API_KEY / CODEX_API_KEY and proxy settings, is dropped.
 */
export const CODEX_ENV_ALLOW: readonly string[] = [
  'PATH',
  'PATHEXT',
  'SystemRoot',
  'windir',
  'ComSpec',
  'USERPROFILE',
  'APPDATA',
  'LOCALAPPDATA',
  'TEMP',
  'TMP',
  'HOME',
];

/** Credential/endpoint overrides removed even if a future allow list would include them. */
export const CODEX_ENV_REMOVE: readonly string[] = [
  'OPENAI_API_KEY',
  'CODEX_API_KEY',
  'OPENAI_BASE_URL',
  'OPENAI_ORGANIZATION',
  'OPENAI_PROJECT',
  'CODEX_HOME',
];

export function codexEnvPolicy(codexHome: string): EnvPolicy {
  return { allow: CODEX_ENV_ALLOW, remove: CODEX_ENV_REMOVE, set: { CODEX_HOME: codexHome } };
}

export interface CodexSession {
  readonly client: JsonRpcClient;
  readonly process: LongLivedProcess;
  readonly init: InitializeInfo;
  /** Exit information once the process is gone, otherwise null. */
  exitInfo(): ExitInfo | null;
  /** Closes stdin, waits `exitGraceMs`, then kills the process tree. Never throws. */
  close(): Promise<void>;
}

export interface OpenSessionOptions {
  command: ResolvedCommand;
  codexHome: string;
  appVersion: string;
  parentEnv: NodeJS.ProcessEnv;
  /** Hard cap on the process lifetime. */
  lifetimeMs: number;
  timeouts: CodexTimeouts;
  /** Aborts the initialize request. */
  signal: AbortSignal;
  /** Kill the process tree as soon as `signal` aborts (false for login, which cancels first). */
  killOnAbort: boolean;
  logger: Logger;
}

function delay(ms: number): { promise: Promise<void>; cancel: () => void } {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const promise = new Promise<void>((resolve) => {
    timer = setTimeout(resolve, ms);
  });
  return { promise, cancel: () => clearTimeout(timer) };
}

const MAX_LOGGED_STDERR_LINES = 5;

export async function openCodexSession(options: OpenSessionOptions): Promise<CodexSession> {
  const proc = await spawnLongLived(options.command, ['app-server'], {
    env: codexEnvPolicy(options.codexHome),
    cwd: options.codexHome,
    timeoutMs: options.lifetimeMs,
    signal: options.killOnAbort ? options.signal : undefined,
    parentEnv: options.parentEnv,
  });

  let exitInfo: ExitInfo | null = null;
  void proc.exited.then((info) => {
    exitInfo = info;
  });

  let stderrLines = 0;
  proc.onStderrLine((line) => {
    stderrLines += 1;
    if (stderrLines <= MAX_LOGGED_STDERR_LINES) options.logger.debug('app-server stderr', { line: line.slice(0, 300) });
  });

  const client = createJsonRpcClient(transportFromProcess(proc), {
    dialect: 'codex',
    defaultTimeoutMs: options.timeouts.rpcMs,
    logger: options.logger,
  });

  let closing: Promise<void> | null = null;
  const close = (): Promise<void> => {
    closing ??= (async () => {
      client.close('session closed');
      proc.closeStdin();
      const grace = delay(options.timeouts.exitGraceMs);
      const exitedInTime = await Promise.race([proc.exited.then(() => true), grace.promise.then(() => false)]);
      grace.cancel();
      if (exitedInTime) return;
      const guard = delay(10_000);
      await Promise.race([proc.kill(), guard.promise]);
      guard.cancel();
    })();
    return closing;
  };

  try {
    const raw = await client.request(
      METHOD.initialize,
      { clientInfo: { name: CLIENT_NAME, version: options.appVersion } },
      { timeoutMs: options.timeouts.initMs, signal: options.signal },
    );
    const init = parseInitializeResult(raw);
    if (init === null) throw new ProviderError('protocol-error', 'invalid initialize response');
    if (!samePath(init.codexHome, options.codexHome)) {
      throw new ProviderError('protocol-error', 'app-server reported a different CODEX_HOME');
    }
    client.notify(METHOD.initialized);
    return { client, process: proc, init, exitInfo: () => exitInfo, close };
  } catch (error) {
    await close();
    throw error;
  }
}
