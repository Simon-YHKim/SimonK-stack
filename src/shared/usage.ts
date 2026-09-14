import type {
  ErrorCode,
  ProviderId,
  QuotaWindow,
  QuotaWindowKind,
  UsageSnapshot,
  UsageSource,
  UsageState,
} from './types';

export const SESSION_WINDOW_MINUTES = 300;
export const WEEKLY_WINDOW_MINUTES = 10_080;
export const MIN_STALE_AFTER_MS = 5 * 60_000;
/** v1 color thresholds on used percent (SPEC §0). */
export const USAGE_WARN_PERCENT = 60;
export const USAGE_CRITICAL_PERCENT = 85;

export function classifyWindowKind(windowMinutes: number | null): QuotaWindowKind {
  if (windowMinutes === SESSION_WINDOW_MINUTES) return 'session';
  if (windowMinutes === WEEKLY_WINDOW_MINUTES) return 'weekly';
  return 'other';
}

/** Finite numbers are clamped to 0..100; anything else is unknown (null), never 0. */
export function normalizePercent(value: unknown): number | null {
  if (typeof value !== 'number' || !Number.isFinite(value)) return null;
  return Math.min(100, Math.max(0, value));
}

export function epochSecondsToMs(value: unknown): number | null {
  if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) return null;
  return Math.round(value * 1000);
}

export function staleAfterMs(refreshIntervalSec: number): number {
  return Math.max(MIN_STALE_AFTER_MS, refreshIntervalSec * 3 * 1000);
}

export function isWindowExpired(window: QuotaWindow, now: number): boolean {
  return window.resetsAt !== null && window.resetsAt <= now;
}

/** Time-dependent state for display; non-measurement states pass through unchanged. */
export function deriveDisplayState(snapshot: UsageSnapshot, now: number, refreshIntervalSec: number): UsageState {
  if (snapshot.state !== 'ok' && snapshot.state !== 'stale' && snapshot.state !== 'reset') {
    return snapshot.state;
  }
  const timed = snapshot.windows.filter((w) => w.resetsAt !== null);
  if (timed.length > 0 && timed.every((w) => isWindowExpired(w, now))) return 'reset';
  if (snapshot.measuredAt === null || now - snapshot.measuredAt > staleAfterMs(refreshIntervalSec)) {
    return 'stale';
  }
  return 'ok';
}

export interface EmptySnapshotInput {
  accountId: string;
  provider: ProviderId;
  source: UsageSource;
  state: 'loading' | 'error' | 'unavailable' | 'logged-out';
  errorCode?: ErrorCode;
}

/** Snapshot with no measured values (used for failures before any success). */
export function createEmptySnapshot(input: EmptySnapshotInput): UsageSnapshot {
  const snapshot: UsageSnapshot = {
    accountId: input.accountId,
    provider: input.provider,
    state: input.state,
    windows: [],
    measuredAt: null,
    lastSuccessAt: null,
    source: input.source,
  };
  if (input.errorCode !== undefined) snapshot.errorCode = input.errorCode;
  return snapshot;
}

/**
 * Combines a failed fetch with the previous snapshot so the last real values
 * and their measurement time stay visible (DECISIONS 26.09.15 01:36).
 */
export function applyFetchFailure(previous: UsageSnapshot | undefined, failed: UsageSnapshot): UsageSnapshot {
  if (
    previous === undefined ||
    previous.accountId !== failed.accountId ||
    previous.windows.length === 0 ||
    previous.lastSuccessAt === null
  ) {
    return failed;
  }
  const merged: UsageSnapshot = {
    ...failed,
    windows: previous.windows,
    measuredAt: previous.measuredAt,
    lastSuccessAt: previous.lastSuccessAt,
  };
  const plan = failed.plan ?? previous.plan;
  if (plan !== undefined) merged.plan = plan;
  return merged;
}

/** v1 countdown format (SPEC §1-4 `j()`): `5d 8h`, `3h 07m`, `12m`, `0m`, `--`. */
export function formatCountdown(msUntil: number | null): string {
  if (msUntil === null || !Number.isFinite(msUntil)) return '--';
  if (msUntil <= 0) return '0m';
  const totalMinutes = Math.floor(msUntil / 60_000);
  const hours = Math.floor(totalMinutes / 60);
  const days = Math.floor(hours / 24);
  if (days >= 1) return `${days}d ${hours % 24}h`;
  if (hours >= 1) return `${hours}h ${String(totalMinutes % 60).padStart(2, '0')}m`;
  return `${totalMinutes}m`;
}

export type UsageLevel = 'unknown' | 'normal' | 'warn' | 'critical';

export function usageLevel(usedPercent: number | null): UsageLevel {
  if (usedPercent === null) return 'unknown';
  if (usedPercent >= USAGE_CRITICAL_PERCENT) return 'critical';
  if (usedPercent >= USAGE_WARN_PERCENT) return 'warn';
  return 'normal';
}

/** Value shown on the widget: used% or left%, null stays null. */
export function displayPercent(usedPercent: number | null, showUsed: boolean): number | null {
  if (usedPercent === null) return null;
  return showUsed ? usedPercent : 100 - usedPercent;
}
