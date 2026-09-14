// Bridge record format shared with resources/claude-bridge/aiuw-claude-bridge.{cjs,ps1}.
// Source fields: statusline docs, `rate_limits.five_hour|seven_day.used_percentage`
// (0..100) and `.resets_at` (Unix epoch seconds); each window may be absent.

import { createHash } from 'node:crypto';
import path from 'node:path';
import type { QuotaWindow, UsageSnapshot } from '../../../shared/types';
import {
  MIN_STALE_AFTER_MS,
  SESSION_WINDOW_MINUTES,
  WEEKLY_WINDOW_MINUTES,
  createEmptySnapshot,
  epochSecondsToMs,
  normalizePercent,
} from '../../../shared/usage';
import { isPlainObject } from '../../../shared/validate';

export const BRIDGE_RECORD_VERSION = 1;
export const BRIDGE_KEY_RE = /^[0-9a-f]{16}$/;
export const DEFAULT_PROFILE_MARKER = '~/.claude default';
export const BRIDGE_RECORD_MAX_BYTES = 256 * 1024;
/** Readings stamped further in the future than this are ignored (clock skew or tampering). */
const FUTURE_TOLERANCE_MS = 60_000;
/** A reset time further ahead than this is not a plausible 7-day window. */
const MAX_RESET_AHEAD_MS = 31 * 24 * 60 * 60_000;

/** Same normalization as the bridge scripts: absolute, backslashes, no trailing slash, lower case. */
export function normalizeConfigDir(dir: string): string {
  let full = path.win32.resolve(dir).replace(/\//g, '\\');
  if (full.length > 3) full = full.replace(/\\+$/, '');
  return full.toLowerCase();
}

/** First 16 hex chars of sha256(normalized dir), or of the default-profile marker when `null`. */
export function bridgeKeyFor(configDir: string | null): string {
  const text = configDir === null ? DEFAULT_PROFILE_MARKER : normalizeConfigDir(configDir);
  return createHash('sha256').update(text, 'utf8').digest('hex').slice(0, 16);
}

export interface BridgeWindow {
  usedPercentage: number | null;
  resetsAtSec: number | null;
  capturedAt: number;
}

export interface BridgeRecord {
  configDirHash: string;
  seenAt: number;
  capturedAt: number | null;
  fiveHour: BridgeWindow | null;
  sevenDay: BridgeWindow | null;
}

function finiteOrNull(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function parseWindow(value: unknown): BridgeWindow | null | 'invalid' {
  if (value === undefined) return null;
  if (!isPlainObject(value)) return 'invalid';
  const capturedAt = finiteOrNull(value.captured_at);
  if (capturedAt === null || capturedAt <= 0) return 'invalid';
  const usedPercentage = finiteOrNull(value.used_percentage);
  const resetsAtSec = finiteOrNull(value.resets_at);
  if (usedPercentage === null && resetsAtSec === null) return null;
  return { usedPercentage, resetsAtSec, capturedAt };
}

/** Strict parse of one bridge record; null when the file is not a record for `expectedKey`. */
export function parseBridgeRecord(text: string, expectedKey: string): BridgeRecord | null {
  let value: unknown;
  try {
    value = JSON.parse(text.replace(/^\uFEFF/, ''));
  } catch {
    return null;
  }
  if (!isPlainObject(value) || value.v !== BRIDGE_RECORD_VERSION || value.configDirHash !== expectedKey) return null;
  const seenAt = finiteOrNull(value.seenAt);
  if (seenAt === null) return null;
  const capturedAt = value.capturedAt === null ? null : finiteOrNull(value.capturedAt);
  if (capturedAt === null && value.capturedAt !== null) return null;
  const limits = value.rate_limits ?? {};
  if (!isPlainObject(limits)) return null;
  const fiveHour = parseWindow(limits.five_hour);
  const sevenDay = parseWindow(limits.seven_day);
  if (fiveHour === 'invalid' || sevenDay === 'invalid') return null;
  return { configDirHash: expectedKey, seenAt, capturedAt, fiveHour, sevenDay };
}

function newest(windows: ReadonlyArray<BridgeWindow | null>, now: number): BridgeWindow | null {
  let best: BridgeWindow | null = null;
  for (const window of windows) {
    if (window === null || window.capturedAt > now + FUTURE_TOLERANCE_MS) continue;
    if (best === null || window.capturedAt > best.capturedAt) best = window;
  }
  return best;
}

function toQuotaWindow(window: BridgeWindow, kind: 'session' | 'weekly', now: number): QuotaWindow {
  let resetsAt = epochSecondsToMs(window.resetsAtSec);
  if (resetsAt !== null && resetsAt > now + MAX_RESET_AHEAD_MS) resetsAt = null;
  const expired = resetsAt !== null && resetsAt <= now;
  return {
    kind,
    // A passed reset means a new window has not started yet: unknown, not the old value.
    usedPercent: expired ? null : normalizePercent(window.usedPercentage),
    resetsAt,
    windowMinutes: kind === 'session' ? SESSION_WINDOW_MINUTES : WEEKLY_WINDOW_MINUTES,
  };
}

export interface BridgeSnapshotInput {
  accountId: string;
  records: readonly BridgeRecord[];
  now: number;
}

/**
 * Builds the usage snapshot from every record that belongs to the account
 * (its own profile and, when it is the default-bridge target, the default profile),
 * taking the newest reading per window.
 */
export function snapshotFromBridge(input: BridgeSnapshotInput): UsageSnapshot {
  const { accountId, records, now } = input;
  const fiveHour = newest(
    records.map((record) => record.fiveHour),
    now,
  );
  const sevenDay = newest(
    records.map((record) => record.sevenDay),
    now,
  );
  if (fiveHour === null && sevenDay === null) {
    return createEmptySnapshot({
      accountId,
      provider: 'claude',
      source: 'claude-statusline',
      state: 'unavailable',
      errorCode: 'bridge-no-data',
    });
  }
  const windows: QuotaWindow[] = [];
  if (fiveHour !== null) windows.push(toQuotaWindow(fiveHour, 'session', now));
  if (sevenDay !== null) windows.push(toQuotaWindow(sevenDay, 'weekly', now));
  const measuredAt = Math.max(fiveHour?.capturedAt ?? 0, sevenDay?.capturedAt ?? 0);
  const allReset = windows.every((window) => window.resetsAt !== null && window.resetsAt <= now);
  const state = allReset ? 'reset' : now - measuredAt > MIN_STALE_AFTER_MS ? 'stale' : 'ok';
  return {
    accountId,
    provider: 'claude',
    state,
    windows,
    measuredAt,
    lastSuccessAt: now,
    source: 'claude-statusline',
  };
}
