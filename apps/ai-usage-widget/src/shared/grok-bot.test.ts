import { describe, expect, it } from 'vitest';
import { GROK_BOT_EXPIRE_MS, GROK_BOT_STALE_MS, grokBotReading } from './grok-bot';

const NOW = Date.UTC(2026, 8, 30, 6);

describe('Grok Bot manual weekly reading', () => {
  it('prefers a current automatic reading and falls back to manual after its reset', () => {
    const settings = { grokBotUsedPercent: 68, grokBotRecordedAt: NOW };
    const automatic = { state: 'ok' as const, usedPercent: 24, resetsAt: NOW + 60_000, measuredAt: NOW };
    expect(grokBotReading(settings, NOW, automatic)).toMatchObject({ state: 'automatic', usedPercent: 24, leftPercent: 76 });
    expect(grokBotReading(settings, NOW + 60_000, automatic).state).toBe('fresh');
  });
  it('keeps unknown separate from an observed 0% and calculates the remaining share', () => {
    expect(grokBotReading({ grokBotUsedPercent: null, grokBotRecordedAt: null }, NOW)).toEqual({ state: 'unknown', recordedAt: null });
    expect(grokBotReading({ grokBotUsedPercent: 0, grokBotRecordedAt: NOW }, NOW)).toEqual({
      state: 'fresh', usedPercent: 0, leftPercent: 100, recordedAt: NOW,
    });
    expect(grokBotReading({ grokBotUsedPercent: 67, grokBotRecordedAt: NOW }, NOW).state).toBe('fresh');
  });

  it('marks a day-old reading stale and hides its number after a weekly cycle', () => {
    const settings = { grokBotUsedPercent: 67, grokBotRecordedAt: NOW };
    expect(grokBotReading(settings, NOW + GROK_BOT_STALE_MS)).toMatchObject({ state: 'stale', leftPercent: 33 });
    expect(grokBotReading(settings, NOW + GROK_BOT_EXPIRE_MS)).toEqual({ state: 'expired', recordedAt: NOW });
    expect(grokBotReading(settings, NOW - 120_000)).toEqual({ state: 'unknown', recordedAt: null });
  });
});
