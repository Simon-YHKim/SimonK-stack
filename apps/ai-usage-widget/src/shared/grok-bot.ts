import type { MessageKey } from './i18n';
import type { Settings } from './settings';

/** Manual readings are no longer treated as current after a day or as numeric after a week. */
export const GROK_BOT_STALE_MS = 24 * 60 * 60 * 1000;
export const GROK_BOT_EXPIRE_MS = 7 * GROK_BOT_STALE_MS;
/**
 * A weekly window never resets more than a week ahead; one extra day absorbs a countdown
 * transcribed as whole days. Later values are ignored rather than trusted.
 */
export const GROK_BOT_MAX_RESET_AHEAD_MS = 8 * GROK_BOT_STALE_MS;

type GrokBotFields = Pick<
  Settings,
  'grokBotUsedPercent' | 'grokBotRecordedAt' | 'grokBotResetAt' | 'grokBotOnDemandSpentCents' | 'grokBotOnDemandLimitCents'
>;

export interface GrokBotOnDemand {
  /** US cents, or null when not entered. */
  spentCents: number | null;
  limitCents: number | null;
}

export type GrokBotReading =
  | { state: 'unknown'; recordedAt: null }
  | {
      state: 'fresh' | 'stale';
      usedPercent: number;
      leftPercent: number;
      recordedAt: number;
      /** Next weekly reset the user entered, still in the future; null when not entered. */
      resetsAt: number | null;
    }
  /** Older than a week: the number is hidden. */
  | { state: 'expired'; recordedAt: number }
  /** The weekly reset the user entered has passed since the reading: the number no longer applies. */
  | { state: 'reset'; recordedAt: number; resetAt: number };

/** Status text per reading state, shared by the popup card and the taskbar item. */
export const GROK_BOT_STATUS_KEYS: Readonly<Record<GrokBotReading['state'], MessageKey>> = {
  unknown: 'grokBotUnknown',
  fresh: 'grokBotManual',
  stale: 'grokBotStale',
  expired: 'grokBotExpired',
  reset: 'grokBotResetPassed',
};

/** The entered reset time only counts when it lies after the reading and within a week of it. */
function plausibleReset(resetAt: number | null, recordedAt: number): number | null {
  if (resetAt === null || !Number.isSafeInteger(resetAt)) return null;
  return resetAt > recordedAt && resetAt - recordedAt <= GROK_BOT_MAX_RESET_AHEAD_MS ? resetAt : null;
}

export function grokBotReading(
  settings: Pick<GrokBotFields, 'grokBotUsedPercent' | 'grokBotRecordedAt'> & Partial<Pick<GrokBotFields, 'grokBotResetAt'>>,
  now: number,
): GrokBotReading {
  const used = settings.grokBotUsedPercent;
  const at = settings.grokBotRecordedAt;
  if (used === null || at === null || !Number.isInteger(used) || used < 0 || used > 100 || !Number.isSafeInteger(at)) {
    return { state: 'unknown', recordedAt: null };
  }
  const age = now - at;
  if (age < -60_000 || !Number.isFinite(age)) return { state: 'unknown', recordedAt: null };
  const resetAt = plausibleReset(settings.grokBotResetAt ?? null, at);
  if (resetAt !== null && now >= resetAt) return { state: 'reset', recordedAt: at, resetAt };
  if (age >= GROK_BOT_EXPIRE_MS) return { state: 'expired', recordedAt: at };
  return {
    state: age >= GROK_BOT_STALE_MS ? 'stale' : 'fresh',
    usedPercent: used,
    leftPercent: 100 - used,
    recordedAt: at,
    resetsAt: resetAt,
  };
}

/** Entered on-demand amounts, or null when neither was entered. */
export function grokBotOnDemand(settings: Partial<Pick<GrokBotFields, 'grokBotOnDemandSpentCents' | 'grokBotOnDemandLimitCents'>>): GrokBotOnDemand | null {
  const spentCents = settings.grokBotOnDemandSpentCents ?? null;
  const limitCents = settings.grokBotOnDemandLimitCents ?? null;
  return spentCents === null && limitCents === null ? null : { spentCents, limitCents };
}

/**
 * The weekly included usage is used up. Per Cursor's plan page, usage then draws on credits and
 * then on paid on-demand usage when it is enabled, so the card says so instead of implying a stop.
 */
export function grokBotWeeklyExhausted(reading: GrokBotReading): boolean {
  return (reading.state === 'fresh' || reading.state === 'stale') && reading.usedPercent >= 100;
}

/** `$12.30`. Cents are integers, so no floating-point rounding reaches the UI. */
export function formatUsdCents(cents: number): string {
  const whole = Math.floor(cents / 100);
  const rest = String(cents % 100).padStart(2, '0');
  return `$${whole.toLocaleString('en-US')}.${rest}`;
}

/** `"12.3"` / `"12"` / `"0.05"` → cents; anything else (negative, 3+ decimals, text) → undefined. */
export function parseUsdToCents(text: string): number | undefined {
  const trimmed = text.trim();
  if (!/^\d{1,7}(?:\.\d{1,2})?$/.test(trimmed)) return undefined;
  const [whole = '0', fraction = ''] = trimmed.split('.');
  return Number(whole) * 100 + Number(fraction.padEnd(2, '0'));
}
