// Error shapes observed on grok 1.0.30 with an empty GROK_HOME (probe 26.09.15):
// `_x.ai/billing` -> {-32000, "Authentication required", data "...to fetch billing data"},
// unknown extension -> {-32601, "Method not found"}. Other messages are from grok.exe strings.
import { describe, expect, it } from 'vitest';
import { JsonRpcError } from '../../cli/jsonrpc';
import { classifyRpcError } from './acp';

describe('classifyRpcError', () => {
  it('treats a missing billing method as unavailable', () => {
    expect(classifyRpcError(new JsonRpcError(-32601, 'Method not found', 'unknown ACP extension method: x.ai/billing'))).toEqual({
      state: 'unavailable',
      code: 'quota-unavailable',
    });
  });

  it('maps the observed authentication error to logged-out', () => {
    expect(
      classifyRpcError(new JsonRpcError(-32000, 'Authentication required', 'Authentication required to fetch billing data')),
    ).toEqual({ state: 'logged-out', code: 'not-logged-in' });
    expect(
      classifyRpcError(new JsonRpcError(-32000, 'Billing data requires auth with grok.com. Run `grok login` to authenticate.')),
    ).toEqual({ state: 'logged-out', code: 'not-logged-in' });
  });

  it('classifies upstream failures without leaking text', () => {
    expect(classifyRpcError(new JsonRpcError(-32000, 'Billing service error', 'HTTP 429 Too Many Requests'))).toEqual({
      state: 'error',
      code: 'rate-limited',
    });
    expect(classifyRpcError(new JsonRpcError(-32000, 'Failed to parse billing data: missing field'))).toEqual({
      state: 'error',
      code: 'parse-error',
    });
    expect(classifyRpcError(new JsonRpcError(-32000, 'Failed to fetch billing data: HTTP 503'))).toEqual({
      state: 'error',
      code: 'provider-error',
    });
    expect(classifyRpcError(new JsonRpcError(-32000, 'Failed to fetch billing data: error sending request', { kind: 'connect' }))).toEqual({
      state: 'error',
      code: 'network',
    });
    expect(classifyRpcError(new JsonRpcError(-32603, 'Internal error'))).toEqual({ state: 'error', code: 'provider-error' });
  });
});
