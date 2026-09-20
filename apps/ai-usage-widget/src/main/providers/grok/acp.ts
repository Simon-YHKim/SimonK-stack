// One-shot ACP conversation with `grok agent stdio`: initialize, then the billing
// extension. No session is created and no prompt is sent, so no quota is consumed.
// Agent-to-client requests get "method not found" from the RPC client.

import type { ErrorCode, UsageState } from '../../../shared/types';
import {
  JsonRpcAbortedError,
  JsonRpcClosedError,
  JsonRpcError,
  JsonRpcTimeoutError,
  createJsonRpcClient,
  transportFromProcess,
} from '../../cli/jsonrpc';
import {
  SpawnError,
  spawnLongLived,
  type EnvPolicy,
  type ExitInfo,
  type LongLivedProcess,
  type ResolvedCommand,
} from '../../cli/spawn';
import type { Logger } from '../../log';

export const ACP_PROTOCOL_VERSION = 1;
/**
 * ACP puts extension methods on the wire with a leading "_". Probe on grok 1.0.30
 * (empty GROK_HOME, 26.09.15): `_x.ai/billing` -> -32000 "Authentication required",
 * `x.ai/billing` -> -32601. The unprefixed name is kept as a fallback.
 */
export const BILLING_METHODS: readonly string[] = ['_x.ai/billing', 'x.ai/billing'];
/** `--no-leader`: never attach to a shared leader that may hold another account. */
export const AGENT_ARGS: readonly string[] = ['agent', '--no-leader', 'stdio'];

const METHOD_NOT_FOUND = -32601;

export type AcpFailureState = Extract<UsageState, 'error' | 'unavailable' | 'logged-out'>;

export interface AcpFailure {
  state: AcpFailureState;
  code: ErrorCode;
}

export type AcpBillingOutcome = { kind: 'ok'; result: unknown } | { kind: 'failed'; failure: AcpFailure };

export interface AcpBillingRequest {
  command: ResolvedCommand;
  env: EnvPolicy;
  parentEnv: NodeJS.ProcessEnv;
  cwd: string;
  appVersion: string;
  logger: Logger;
  signal: AbortSignal;
  lifetimeMs: number;
  initializeMs: number;
  requestMs: number;
}

export function acpFailure(state: AcpFailureState, code: ErrorCode): AcpFailure {
  return { state, code };
}

function failed(state: AcpFailureState, code: ErrorCode): AcpBillingOutcome {
  return { kind: 'failed', failure: acpFailure(state, code) };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function errorText(error: JsonRpcError): string {
  let data = '';
  if (typeof error.data === 'string') data = error.data;
  else if (error.data !== undefined) {
    try {
      data = JSON.stringify(error.data);
    } catch {
      data = '';
    }
  }
  return `${error.message} ${data}`;
}

/** Classifies an RPC error from the billing call. The raw text is never logged or shown. */
export function classifyRpcError(error: JsonRpcError): AcpFailure {
  if (error.code === METHOD_NOT_FOUND) return acpFailure('unavailable', 'quota-unavailable');
  const text = errorText(error);
  if (/authenticat|unauthori[sz]ed|\b401\b|grok login|not logged in|sign in/i.test(text)) {
    return acpFailure('logged-out', 'not-logged-in');
  }
  if (/rate.?limit|too many requests|\b429\b/i.test(text)) return acpFailure('error', 'rate-limited');
  if (/parse/i.test(text)) return acpFailure('error', 'parse-error');
  if (/\bHTTP\s*\d{3}\b|service error/i.test(text)) return acpFailure('error', 'provider-error');
  if (/network|connect|dns|unreachable|timed? ?out|failed to fetch/i.test(text)) return acpFailure('error', 'network');
  return acpFailure('error', 'provider-error');
}

async function exitInfoSoon(proc: LongLivedProcess, waitMs: number): Promise<ExitInfo | null> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<null>((resolve) => {
    timer = setTimeout(() => resolve(null), waitMs);
  });
  try {
    return await Promise.race([proc.exited, timeout]);
  } finally {
    clearTimeout(timer);
  }
}

async function classifyFailure(error: unknown, proc: LongLivedProcess, signal: AbortSignal): Promise<AcpFailure> {
  if (signal.aborted || error instanceof JsonRpcAbortedError) return acpFailure('error', 'cancelled');
  if (error instanceof JsonRpcTimeoutError) return acpFailure('error', 'timeout');
  if (error instanceof JsonRpcError) return classifyRpcError(error);
  if (error instanceof JsonRpcClosedError) {
    const exit = await exitInfoSoon(proc, 1000);
    if (exit?.aborted === true) return acpFailure('error', 'cancelled');
    if (exit?.timedOut === true) return acpFailure('error', 'timeout');
    return acpFailure('error', 'protocol-error');
  }
  return acpFailure('error', 'internal');
}

/** Spawns the agent, reads billing once and always kills the process tree before returning. */
export async function queryAcpBilling(request: AcpBillingRequest): Promise<AcpBillingOutcome> {
  if (request.signal.aborted) return failed('error', 'cancelled');
  let proc: LongLivedProcess;
  try {
    proc = await spawnLongLived(request.command, AGENT_ARGS, {
      env: request.env,
      parentEnv: request.parentEnv,
      cwd: request.cwd,
      timeoutMs: request.lifetimeMs,
      signal: request.signal,
    });
  } catch (error) {
    if (request.signal.aborted) return failed('error', 'cancelled');
    return failed('error', error instanceof SpawnError && error.code === 'cli-not-found' ? 'cli-not-found' : 'spawn-failed');
  }

  const client = createJsonRpcClient(transportFromProcess(proc), {
    dialect: 'jsonrpc2',
    defaultTimeoutMs: request.requestMs,
    logger: request.logger,
  });
  try {
    const init = await client.request(
      'initialize',
      {
        protocolVersion: ACP_PROTOCOL_VERSION,
        clientCapabilities: { fs: { readTextFile: false, writeTextFile: false }, terminal: false },
        clientInfo: { name: 'ai-usage-widget', version: request.appVersion },
      },
      { timeoutMs: request.initializeMs, signal: request.signal },
    );
    const version = isRecord(init) ? init.protocolVersion : undefined;
    if (typeof version !== 'number') return failed('error', 'protocol-error');
    if (version !== ACP_PROTOCOL_VERSION) return failed('error', 'cli-unsupported-version');

    for (const method of BILLING_METHODS) {
      try {
        const result = await client.request(method, {}, { timeoutMs: request.requestMs, signal: request.signal });
        return { kind: 'ok', result };
      } catch (error) {
        if (error instanceof JsonRpcError && error.code === METHOD_NOT_FOUND) continue;
        throw error;
      }
    }
    return failed('unavailable', 'quota-unavailable');
  } catch (error) {
    return { kind: 'failed', failure: await classifyFailure(error, proc, request.signal) };
  } finally {
    client.close('query finished');
    await proc.kill();
  }
}
