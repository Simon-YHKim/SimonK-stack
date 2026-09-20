import { describe, expect, it } from 'vitest';
import type { UsageSnapshot } from './types';
import {
  applyFetchFailure,
  classifyWindowKind,
  createEmptySnapshot,
  deriveDisplayState,
  displayPercent,
  epochSecondsToMs,
  formatCountdown,
  normalizePercent,
  usageLevel,
} from './usage';

const NOW = 1_800_000_000_000;

function okSnapshot(overrides: Partial<UsageSnapshot> = {}): UsageSnapshot {
  return {
    accountId: 'acc1',
    provider: 'codex',
    state: 'ok',
    windows: [{ kind: 'session', usedPercent: 40, resetsAt: NOW + 3_600_000, windowMinutes: 300 }],
    measuredAt: NOW - 1000,
    lastSuccessAt: NOW - 1000,
    source: 'codex-app-server',
    ...overrides,
  };
}

describe('usage helpers', () => {
  it('classifies window lengths', () => {
    expect(classifyWindowKind(300)).toBe('session');
    expect(classifyWindowKind(10_080)).toBe('weekly');
    expect(classifyWindowKind(60)).toBe('other');
    expect(classifyWindowKind(null)).toBe('other');
  });

  it('keeps unknown percent as null, never 0', () => {
    expect(normalizePercent(undefined)).toBeNull();
    expect(normalizePercent(Number.NaN)).toBeNull();
    expect(normalizePercent('50')).toBeNull();
    expect(normalizePercent(-3)).toBe(0);
    expect(normalizePercent(130)).toBe(100);
    expect(normalizePercent(42.5)).toBe(42.5);
  });

  it('converts epoch seconds', () => {
    expect(epochSecondsToMs(1_700_000_000)).toBe(1_700_000_000_000);
    expect(epochSecondsToMs(0)).toBeNull();
    expect(epochSecondsToMs(null)).toBeNull();
  });

  it('derives stale and reset states', () => {
    expect(deriveDisplayState(okSnapshot(), NOW, 60)).toBe('ok');
    expect(deriveDisplayState(okSnapshot({ measuredAt: NOW - 6 * 60_000 }), NOW, 60)).toBe('stale');
    const expired = okSnapshot({
      windows: [{ kind: 'weekly', usedPercent: 90, resetsAt: NOW - 1, windowMinutes: 10_080 }],
    });
    expect(deriveDisplayState(expired, NOW, 60)).toBe('reset');
    expect(deriveDisplayState(okSnapshot({ state: 'error', errorCode: 'timeout' }), NOW, 60)).toBe('error');
    expect(deriveDisplayState(okSnapshot({ measuredAt: null }), NOW, 60)).toBe('stale');
  });

  it('applyFetchFailure keeps last real values and their time', () => {
    const previous = okSnapshot({ plan: 'plus' });
    const failed = createEmptySnapshot({
      accountId: 'acc1',
      provider: 'codex',
      source: 'codex-app-server',
      state: 'error',
      errorCode: 'timeout',
    });
    const merged = applyFetchFailure(previous, failed);
    expect(merged.state).toBe('error');
    expect(merged.errorCode).toBe('timeout');
    expect(merged.windows).toEqual(previous.windows);
    expect(merged.measuredAt).toBe(previous.measuredAt);
    expect(merged.plan).toBe('plus');
    expect(applyFetchFailure(undefined, failed)).toBe(failed);
  });

  it('empty snapshots contain no measured values', () => {
    const snap = createEmptySnapshot({ accountId: 'a', provider: 'grok', source: 'grok-acp', state: 'unavailable' });
    expect(snap.windows).toEqual([]);
    expect(snap.measuredAt).toBeNull();
    expect(snap).not.toHaveProperty('errorCode');
  });

  it('formats countdown like v1', () => {
    expect(formatCountdown(null)).toBe('--');
    expect(formatCountdown(Number.NaN)).toBe('--');
    expect(formatCountdown(0)).toBe('0m');
    expect(formatCountdown(30_000)).toBe('0m');
    expect(formatCountdown(12 * 60_000)).toBe('12m');
    expect(formatCountdown(3 * 3_600_000 + 7 * 60_000)).toBe('3h 07m');
    expect(formatCountdown(5 * 86_400_000 + 8 * 3_600_000)).toBe('5d 8h');
  });

  it('maps usage levels and display percent', () => {
    expect(usageLevel(null)).toBe('unknown');
    expect(usageLevel(59)).toBe('normal');
    expect(usageLevel(60)).toBe('warn');
    expect(usageLevel(85)).toBe('critical');
    expect(displayPercent(30, false)).toBe(70);
    expect(displayPercent(30, true)).toBe(30);
    expect(displayPercent(null, false)).toBeNull();
  });
});
