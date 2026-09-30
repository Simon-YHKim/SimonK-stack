import { describe, expect, it, vi } from 'vitest';
import { createGrokBotService, parseGrokBotUsage } from './service';

const NOW = Date.parse('2026-09-30T00:00:00Z');

describe('Grok Bot weekly usage', () => {
  it('parses the separate weekly percent and server reset, including fractional usage', () => {
    expect(parseGrokBotUsage({ usagePercent: 19.150778, nextResetTimestampUtc: '2026-10-05T00:00:00Z',
      grokPlanLabel: 'SuperGrok Heavy' }, NOW)).toEqual({ state: 'ok', usedPercent: 19,
      resetsAt: Date.parse('2026-10-05T00:00:00Z'), measuredAt: NOW, plan: 'SuperGrok Heavy' });
    expect(parseGrokBotUsage({ usagePercent: 0, hasNonZeroIncludedLimit: false }, NOW).state).toBe('unavailable');
    expect(() => parseGrokBotUsage({ usagePercent: '19' }, NOW)).toThrow();
  });

  it('uses the signed-in desktop token only for the Cursor usage request', async () => {
    const onChange = vi.fn();
    const request = vi.fn((_url: string | URL | Request, init?: RequestInit) => {
      expect(init?.method).toBe('POST');
      expect(init?.headers).toMatchObject({ Authorization: 'Bearer sample-token', 'Connect-Protocol-Version': '1' });
      return Promise.resolve(new Response(JSON.stringify({ usagePercent: 52, nextResetTimestampUtc: '2026-10-05T00:00:00Z' }), { status: 200 }));
    });
    const service = createGrokBotService({ readToken: () => 'sample-token', request,
      now: () => NOW, onChange });
    await service.refresh();
    expect(request).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ state: 'ok', usedPercent: 52 }));
  });

  it('never reports zero when login is missing, expired, or the response drifts', async () => {
    const onChange = vi.fn();
    const request = vi.fn(() => Promise.resolve(new Response('{}', { status: 401 })));
    const service = createGrokBotService({ readToken: () => null, request, now: () => NOW, onChange });
    await service.refresh();
    expect(request).not.toHaveBeenCalled();
    expect(onChange).toHaveBeenLastCalledWith({ state: 'unavailable', usedPercent: null, resetsAt: null, measuredAt: NOW });
    const expired = createGrokBotService({ readToken: () => 'sample-token', request,
      now: () => NOW, onChange });
    await expired.refresh();
    expect(onChange).toHaveBeenLastCalledWith({ state: 'login-expired', usedPercent: null, resetsAt: null, measuredAt: NOW });
    const drift = createGrokBotService({ readToken: () => 'sample-token',
      request: () => Promise.resolve(new Response('{}', { status: 200 })), now: () => NOW, onChange });
    await drift.refresh();
    expect(onChange).toHaveBeenLastCalledWith({ state: 'error', usedPercent: null, resetsAt: null, measuredAt: NOW });
  });
});
