import { describe, expect, it } from 'vitest';
import {
  GROK_BOT_EXPIRE_MS,
  GROK_BOT_MAX_RESET_AHEAD_MS,
  GROK_BOT_STALE_MS,
  formatUsdCents,
  grokBotOnDemand,
  grokBotReading,
  grokBotWeeklyExhausted,
  parseUsdToCents,
} from './grok-bot';

const NOW = Date.UTC(2026, 8, 30, 6);
const HOUR = 60 * 60 * 1000;

describe('Grok Bot manual weekly reading', () => {
  it('keeps unknown separate from an observed 0% and calculates the remaining share', () => {
    expect(grokBotReading({ grokBotUsedPercent: null, grokBotRecordedAt: null }, NOW)).toEqual({ state: 'unknown', recordedAt: null });
    expect(grokBotReading({ grokBotUsedPercent: 0, grokBotRecordedAt: NOW }, NOW)).toEqual({
      state: 'fresh', usedPercent: 0, leftPercent: 100, recordedAt: NOW, resetsAt: null,
    });
    expect(grokBotReading({ grokBotUsedPercent: 67, grokBotRecordedAt: NOW }, NOW).state).toBe('fresh');
  });

  it('marks a day-old reading stale and hides its number after a weekly cycle', () => {
    const settings = { grokBotUsedPercent: 67, grokBotRecordedAt: NOW };
    expect(grokBotReading(settings, NOW + GROK_BOT_STALE_MS)).toMatchObject({ state: 'stale', leftPercent: 33 });
    expect(grokBotReading(settings, NOW + GROK_BOT_EXPIRE_MS)).toEqual({ state: 'expired', recordedAt: NOW });
    expect(grokBotReading(settings, NOW - 120_000)).toEqual({ state: 'unknown', recordedAt: null });
  });

  it('counts down to an entered weekly reset and stops showing the number once it passes', () => {
    const settings = { grokBotUsedPercent: 80, grokBotRecordedAt: NOW, grokBotResetAt: NOW + 50 * HOUR };
    expect(grokBotReading(settings, NOW + HOUR)).toMatchObject({ state: 'fresh', usedPercent: 80, resetsAt: NOW + 50 * HOUR });
    expect(grokBotReading(settings, NOW + 30 * HOUR)).toMatchObject({ state: 'stale', resetsAt: NOW + 50 * HOUR });
    // The window rolled over: the recorded 80% belongs to the previous week.
    expect(grokBotReading(settings, NOW + 50 * HOUR)).toEqual({ state: 'reset', recordedAt: NOW, resetAt: NOW + 50 * HOUR });
  });

  it('ignores a reset time before the reading or further than a weekly window ahead', () => {
    const before = { grokBotUsedPercent: 10, grokBotRecordedAt: NOW, grokBotResetAt: NOW - HOUR };
    expect(grokBotReading(before, NOW + HOUR)).toMatchObject({ state: 'fresh', resetsAt: null });
    const tooFar = { grokBotUsedPercent: 10, grokBotRecordedAt: NOW, grokBotResetAt: NOW + GROK_BOT_MAX_RESET_AHEAD_MS + HOUR };
    expect(grokBotReading(tooFar, NOW + HOUR)).toMatchObject({ state: 'fresh', resetsAt: null });
  });

  it('flags a used-up weekly allowance only for a current numeric reading', () => {
    expect(grokBotWeeklyExhausted(grokBotReading({ grokBotUsedPercent: 100, grokBotRecordedAt: NOW }, NOW))).toBe(true);
    expect(grokBotWeeklyExhausted(grokBotReading({ grokBotUsedPercent: 99, grokBotRecordedAt: NOW }, NOW))).toBe(false);
    expect(grokBotWeeklyExhausted(grokBotReading({ grokBotUsedPercent: 100, grokBotRecordedAt: NOW }, NOW + GROK_BOT_EXPIRE_MS))).toBe(false);
  });
});

describe('Grok Bot on-demand amounts', () => {
  it('returns null until at least one amount is entered', () => {
    expect(grokBotOnDemand({ grokBotOnDemandSpentCents: null, grokBotOnDemandLimitCents: null })).toBeNull();
    expect(grokBotOnDemand({ grokBotOnDemandSpentCents: 1230, grokBotOnDemandLimitCents: null })).toEqual({ spentCents: 1230, limitCents: null });
  });

  it('parses dollars to whole cents without floating-point drift and formats them back', () => {
    expect(parseUsdToCents('12.3')).toBe(1230);
    expect(parseUsdToCents(' 0.05 ')).toBe(5);
    expect(parseUsdToCents('40')).toBe(4000);
    expect(parseUsdToCents('0.29')).toBe(29);
    for (const bad of ['', '-1', '1.234', 'abc', '1,000', '$5']) expect(parseUsdToCents(bad), bad).toBeUndefined();
    expect(formatUsdCents(1230)).toBe('$12.30');
    expect(formatUsdCents(5)).toBe('$0.05');
    expect(formatUsdCents(123_456_789)).toBe('$1,234,567.89');
  });
});
