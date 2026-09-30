import {
  QUOTA_WINDOW_KINDS,
  USAGE_SOURCES,
  USAGE_STATES,
  isErrorCode,
  type Account,
  type QuotaWindow,
  type UsageSnapshot,
} from '../../shared/types';
import { normalizePercent } from '../../shared/usage';
import { isFiniteNumber, isOneOf, isPlainObject, normalizeLabel } from '../../shared/validate';
import { SOURCE_BY_PROVIDER } from '../scheduler';

export const MAX_WINDOWS = 16;

const positiveOrNull = (value: unknown): number | null => (isFiniteNumber(value) && value > 0 ? value : null);

function sanitizeWindow(input: unknown): QuotaWindow | null {
  if (!isPlainObject(input)) return null;
  const window: QuotaWindow = {
    kind: isOneOf(QUOTA_WINDOW_KINDS, input.kind) ? input.kind : 'other',
    usedPercent: normalizePercent(input.usedPercent),
    resetsAt: positiveOrNull(input.resetsAt),
    windowMinutes: positiveOrNull(input.windowMinutes),
  };
  const label = normalizeLabel(input.label);
  if (label !== null) window.label = label;
  return window;
}

/**
 * Rebuilds an adapter snapshot field by field before it is stored or sent to a
 * renderer: ids come from the account, unknown values stay null, and nothing
 * outside the contract (paths, raw errors, tokens) can ride along.
 */
export function sanitizeSnapshot(account: Account, input: UsageSnapshot): UsageSnapshot {
  const raw = input as unknown as Record<string, unknown>;
  const state = isOneOf(USAGE_STATES, raw.state) ? raw.state : 'error';
  const windows = Array.isArray(raw.windows)
    ? raw.windows
        .slice(0, MAX_WINDOWS)
        .map(sanitizeWindow)
        .filter((w): w is QuotaWindow => w !== null)
    : [];
  const snapshot: UsageSnapshot = {
    accountId: account.id,
    provider: account.provider,
    state,
    windows,
    measuredAt: positiveOrNull(raw.measuredAt),
    lastSuccessAt: positiveOrNull(raw.lastSuccessAt),
    source: isOneOf(USAGE_SOURCES, raw.source) ? raw.source : SOURCE_BY_PROVIDER[account.provider],
  };
  const plan = normalizeLabel(raw.plan);
  if (plan !== null) snapshot.plan = plan;
  if (account.provider === 'codex' && typeof raw.resetCreditsAvailable === 'number' &&
      Number.isSafeInteger(raw.resetCreditsAvailable) && raw.resetCreditsAvailable >= 0 && raw.resetCreditsAvailable <= 1_000) {
    snapshot.resetCreditsAvailable = raw.resetCreditsAvailable;
  }
  if (isErrorCode(raw.errorCode)) snapshot.errorCode = raw.errorCode;
  else if (state === 'error') snapshot.errorCode = 'internal';
  return snapshot;
}
