import { describe, expect, it } from 'vitest';
import { JsonRpcAbortedError, JsonRpcClosedError, JsonRpcError, JsonRpcTimeoutError } from '../../cli/jsonrpc';
import { SpawnError } from '../../cli/spawn';
import { ProviderError } from '../types';
import { classifyFailure, classifyLoginError, classifyRpcError, resolveFailureCode, stateForCode } from './errors';

describe('classifyRpcError', () => {
  it('maps messages observed on codex-cli 0.154.0 with an empty CODEX_HOME', () => {
    expect(classifyRpcError(-32600, 'codex account authentication required to read rate limits')).toBe('not-logged-in');
    expect(classifyRpcError(-32600, 'Invalid request: unknown variant `nonexistent/method`, expected one of ...')).toBe(
      'cli-unsupported-version',
    );
    expect(classifyRpcError(-32600, 'Invalid request: missing field `params`')).toBe('protocol-error');
  });

  it('maps other failure families', () => {
    expect(classifyRpcError(-32601, 'Method not found')).toBe('cli-unsupported-version');
    expect(classifyRpcError(-32603, 'Your access token could not be refreshed; please log in again')).toBe('login-expired');
    expect(classifyRpcError(-32603, 'unexpected status 429 Too Many Requests')).toBe('rate-limited');
    expect(classifyRpcError(-32603, 'error sending request: connection refused')).toBe('network');
    expect(classifyRpcError(-32603, 'backend returned 500')).toBe('provider-error');
  });
});

describe('classifyLoginError', () => {
  it('detects disabled device-code sign-in, expiry and generic failures', () => {
    expect(classifyLoginError('Device code authorization is disabled for this workspace')).toBe('device-auth-disabled');
    expect(classifyLoginError('Enable device code login in ChatGPT security settings')).toBe('device-auth-disabled');
    expect(classifyLoginError('device code expired')).toBe('timeout');
    expect(classifyLoginError('network unreachable')).toBe('network');
    expect(classifyLoginError('access denied')).toBe('login-failed');
    expect(classifyLoginError('')).toBe('login-failed');
  });
});

describe('classifyFailure', () => {
  it('assigns widget states per error type', () => {
    expect(classifyFailure(new SpawnError('cli-not-found', 'x'))).toEqual({ state: 'unavailable', code: 'cli-not-found' });
    expect(classifyFailure(new SpawnError('invalid-command', 'x'))).toEqual({ state: 'unavailable', code: 'spawn-failed' });
    expect(classifyFailure(new JsonRpcTimeoutError('account/read'))).toEqual({ state: 'error', code: 'timeout' });
    expect(classifyFailure(new JsonRpcAbortedError('account/read'))).toEqual({ state: 'error', code: 'cancelled' });
    expect(classifyFailure(new JsonRpcClosedError('transport closed'))).toEqual({ state: 'error', code: 'protocol-error' });
    expect(classifyFailure(new JsonRpcError(-32600, 'codex account authentication required to read rate limits'))).toEqual({
      state: 'logged-out',
      code: 'not-logged-in',
    });
    expect(classifyFailure(new ProviderError('parse-error'))).toEqual({ state: 'error', code: 'parse-error' });
    expect(classifyFailure(new Error('boom'))).toEqual({ state: 'error', code: 'internal' });
  });

  it('maps resolve failures and code states', () => {
    expect(resolveFailureCode('cli-not-found')).toBe('cli-not-found');
    expect(resolveFailureCode('node-not-found')).toBe('node-not-found');
    expect(resolveFailureCode('unsupported-shim')).toBe('spawn-failed');
    expect(stateForCode('login-expired')).toBe('logged-out');
    expect(stateForCode('quota-unavailable')).toBe('unavailable');
    expect(stateForCode('rate-limited')).toBe('error');
  });
});
