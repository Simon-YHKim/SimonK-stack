import type { Settings } from './settings';

export interface GrokBotAutoUsage {
  state: 'ok' | 'unavailable' | 'login-expired' | 'error';
  usedPercent: number | null;
  resetsAt: number | null;
  measuredAt: number;
  plan?: string;
}

/** Manual readings are no longer treated as current after a day or as numeric after a week. */
export const GROK_BOT_STALE_MS = 24 * 60 * 60 * 1000;
export const GROK_BOT_EXPIRE_MS = 7 * GROK_BOT_STALE_MS;

export type GrokBotReading =
  | { state: 'unknown'; recordedAt: null }
  | { state: 'fresh' | 'stale'; usedPercent: number; leftPercent: number; recordedAt: number }
  | { state: 'expired'; recordedAt: number }
  | { state: 'automatic'; usedPercent: number; leftPercent: number; recordedAt: number; resetsAt: number | null; plan?: string };

export function grokBotReading(settings: Pick<Settings, 'grokBotUsedPercent' | 'grokBotRecordedAt'>, now: number,
  automatic?: GrokBotAutoUsage): GrokBotReading {
  if (automatic?.state === 'ok' && automatic.usedPercent !== null && now - automatic.measuredAt < GROK_BOT_STALE_MS &&
    (automatic.resetsAt === null || automatic.resetsAt > now)) {
    return { state: 'automatic', usedPercent: automatic.usedPercent, leftPercent: 100 - automatic.usedPercent,
      recordedAt: automatic.measuredAt, resetsAt: automatic.resetsAt, ...(automatic.plan ? { plan: automatic.plan } : {}) };
  }
  const used = settings.grokBotUsedPercent;
  const at = settings.grokBotRecordedAt;
  if (used === null || at === null || !Number.isInteger(used) || used < 0 || used > 100 || !Number.isSafeInteger(at)) {
    return { state: 'unknown', recordedAt: null };
  }
  const age = now - at;
  if (age < -60_000 || !Number.isFinite(age)) return { state: 'unknown', recordedAt: null };
  if (age >= GROK_BOT_EXPIRE_MS) return { state: 'expired', recordedAt: at };
  return { state: age >= GROK_BOT_STALE_MS ? 'stale' : 'fresh', usedPercent: used, leftPercent: 100 - used, recordedAt: at };
}
