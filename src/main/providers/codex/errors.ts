// Maps failures of the Codex app-server conversation to renderer-safe codes.
// Provider message text is only used for classification and never forwarded.

import type { ErrorCode } from '../../../shared/types';
import { JsonRpcAbortedError, JsonRpcClosedError, JsonRpcError, JsonRpcTimeoutError } from '../../cli/jsonrpc';
import type { ResolveFailure } from '../../cli/resolve';
import { SpawnError } from '../../cli/spawn';
import { ProviderError } from '../types';

export type FailureState = 'error' | 'unavailable' | 'logged-out';

export interface CodexFailure {
  state: FailureState;
  code: ErrorCode;
}

const LOGGED_OUT_CODES: ReadonlySet<ErrorCode> = new Set(['not-logged-in', 'login-expired']);
const UNAVAILABLE_CODES: ReadonlySet<ErrorCode> = new Set([
  'cli-not-found',
  'node-not-found',
  'spawn-failed',
  'cli-unsupported-version',
  'cli-unsupported-install',
  'quota-unavailable',
]);

export function stateForCode(code: ErrorCode): FailureState {
  if (LOGGED_OUT_CODES.has(code)) return 'logged-out';
  if (UNAVAILABLE_CODES.has(code)) return 'unavailable';
  return 'error';
}

export function resolveFailureCode(failure: ResolveFailure): ErrorCode {
  switch (failure) {
    case 'cli-not-found':
      return 'cli-not-found';
    case 'node-not-found':
      return 'node-not-found';
    case 'unsupported-shim':
      return 'cli-unsupported-install';
  }
}

// Observed on codex-cli 0.154.0 (empty CODEX_HOME probe): unknown methods and
// malformed requests are -32600 "Invalid request: ...", an unauthenticated
// rateLimits read is -32600 "codex account authentication required to read rate limits".
export function classifyRpcError(code: number, message: string): ErrorCode {
  if (code === -32601 || /unknown variant/i.test(message)) return 'cli-unsupported-version';
  if (code === -32602 || /^invalid (request|params)/i.test(message)) return 'protocol-error';
  if (/authentication required|not (logged|signed) in|not authenticated|login required|no auth/i.test(message)) {
    return 'not-logged-in';
  }
  if (/expired|sign in again|log ?in again|re-?authenticat|refresh token|unauthorized|\b401\b/i.test(message)) {
    return 'login-expired';
  }
  if (/too many requests|\b429\b|rate[ _-]?limited/i.test(message)) return 'rate-limited';
  if (/network|connection|connect|dns|unreachable|offline|timed? ?out|tls|certificate|proxy/i.test(message)) {
    return 'network';
  }
  return 'provider-error';
}

/** Classifies `account/login/completed.error` or a failed `account/login/start`. */
export function classifyLoginError(message: string): ErrorCode {
  if (/device/i.test(message) && /disabled|not enabled|not allowed|unsupported|unavailable|turn on|enable/i.test(message)) {
    return 'device-auth-disabled';
  }
  if (/expired|timed? ?out/i.test(message)) return 'timeout';
  if (/network|connection|dns|unreachable|offline/i.test(message)) return 'network';
  return 'login-failed';
}

export function classifyFailure(error: unknown): CodexFailure {
  let code: ErrorCode;
  if (error instanceof ProviderError) code = error.code;
  else if (error instanceof SpawnError) code = error.code === 'cli-not-found' ? 'cli-not-found' : 'spawn-failed';
  else if (error instanceof JsonRpcTimeoutError) code = 'timeout';
  else if (error instanceof JsonRpcAbortedError) code = 'cancelled';
  else if (error instanceof JsonRpcClosedError) code = 'protocol-error';
  else if (error instanceof JsonRpcError) code = classifyRpcError(error.code, error.message);
  else code = 'internal';
  return { state: stateForCode(code), code };
}
