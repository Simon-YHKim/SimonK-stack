// Parser for `agy -p "/usage" --output-format json` (measured on agy 1.2.6, DECISIONS 26.09.19 11:42).
// Only structured fields are read; the human-readable `response` text is ignored.

import type { QuotaWindow } from '../../../shared/types';
import { SESSION_WINDOW_MINUTES, WEEKLY_WINDOW_MINUTES, normalizePercent } from '../../../shared/usage';

export const MAX_GROUP_LABEL_LENGTH = 40;

export type AgyUsageParse =
  | { kind: 'ok'; windows: QuotaWindow[] }
  /** Valid JSON that is not a zero-turn `/usage` command result: the slash command was not expanded. */
  | { kind: 'not-usage-command' }
  /** The CLI answered but reported a failure status. `reason` is the CLI's own short text, for masked logging only. */
  | { kind: 'failed'; status: string; reason?: string }
  | { kind: 'malformed' };

const WINDOW_MINUTES: Readonly<Record<string, number>> = {
  '5h': SESSION_WINDOW_MINUTES,
  weekly: WEEKLY_WINDOW_MINUTES,
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** Group names come from the CLI; keep them short and free of control characters before they reach the UI. */
export function sanitizeGroupLabel(value: unknown): string | undefined {
  if (typeof value !== 'string') return undefined;
  // eslint-disable-next-line no-control-regex
  const cleaned = value.replace(/[\u0000-\u001f\u007f]/g, ' ').replace(/\s+/g, ' ').trim();
  if (cleaned === '') return undefined;
  return cleaned.length > MAX_GROUP_LABEL_LENGTH ? `${cleaned.slice(0, MAX_GROUP_LABEL_LENGTH - 1)}…` : cleaned;
}

function parseResetTime(value: unknown): number | null {
  if (typeof value !== 'string') return null;
  const ms = Date.parse(value);
  return Number.isFinite(ms) && ms > 0 ? ms : null;
}

function toWindow(bucket: unknown, label: string | undefined): QuotaWindow | null {
  if (!isRecord(bucket)) return null;
  const windowMinutes = typeof bucket.window === 'string' ? (WINDOW_MINUTES[bucket.window] ?? null) : null;
  const remaining = bucket.remaining_fraction;
  // A missing or non-numeric fraction stays unknown (null); it is never read as 0 % or 100 %.
  const usedPercent =
    typeof remaining === 'number' && Number.isFinite(remaining) && remaining >= 0 && remaining <= 1
      ? normalizePercent((1 - remaining) * 100)
      : null;
  const resetsAt = parseResetTime(bucket.reset_time);
  if (usedPercent === null && resetsAt === null) return null;
  const window: QuotaWindow = {
    kind: windowMinutes === SESSION_WINDOW_MINUTES ? 'session' : windowMinutes === WEEKLY_WINDOW_MINUTES ? 'weekly' : 'other',
    usedPercent,
    resetsAt,
    windowMinutes,
  };
  if (label !== undefined) window.label = label;
  return window;
}

/** Session before weekly inside a group; groups keep the order the CLI reported. */
const KIND_ORDER: Readonly<Record<QuotaWindow['kind'], number>> = { session: 0, weekly: 1, other: 2 };

export function parseAgyUsage(stdout: string): AgyUsageParse {
  let root: unknown;
  try {
    root = JSON.parse(stdout.trim());
  } catch {
    return { kind: 'malformed' };
  }
  if (!isRecord(root)) return { kind: 'malformed' };
  if (typeof root.status === 'string' && root.status !== 'SUCCESS') {
    const failed: { kind: 'failed'; status: string; reason?: string } = { kind: 'failed', status: root.status.slice(0, 40) };
    // Field name unknown (no failure has been captured yet): take the first short text the CLI offers.
    for (const key of ['error', 'message', 'response']) {
      const field = root[key];
      const value = isRecord(field) ? field.message : field;
      if (typeof value === 'string' && value.trim() !== '') {
        failed.reason = value.replace(/\s+/g, ' ').trim().slice(0, 160);
        break;
      }
    }
    return failed;
  }

  const command = root.command;
  if (!isRecord(command) || command.name !== 'usage' || root.num_turns !== 0) return { kind: 'not-usage-command' };
  const data = command.data;
  if (!isRecord(data) || !Array.isArray(data.groups)) return { kind: 'malformed' };

  const windows: QuotaWindow[] = [];
  for (const group of data.groups) {
    if (!isRecord(group) || !Array.isArray(group.buckets)) continue;
    const label = sanitizeGroupLabel(group.name);
    const parsed = group.buckets.map((bucket) => toWindow(bucket, label)).filter((w): w is QuotaWindow => w !== null);
    parsed.sort((a, b) => KIND_ORDER[a.kind] - KIND_ORDER[b.kind]);
    windows.push(...parsed);
  }
  return { kind: 'ok', windows };
}
