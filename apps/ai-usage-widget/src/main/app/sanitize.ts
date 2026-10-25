import {
  QUOTA_WINDOW_KINDS,
  USAGE_SOURCES,
  USAGE_STATES,
  isErrorCode,
  type Account,
  type ExtraUsage,
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

/** $1,000,000 in cents: anything larger is not a plausible personal balance. */
const MAX_CENTS = 100_000_000;
const cents = (value: unknown): number | undefined =>
  typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 && value <= MAX_CENTS ? value : undefined;

function sanitizeExtraUsage(input: unknown): ExtraUsage | undefined {
  if (!isPlainObject(input)) return undefined;
  const extra: ExtraUsage = {};
  const prepaid = cents(input.prepaidCents);
  if (prepaid !== undefined) extra.prepaidCents = prepaid;
  const used = cents(input.onDemandUsedCents);
  if (used !== undefined) extra.onDemandUsedCents = used;
  const cap = cents(input.onDemandCapCents);
  if (cap !== undefined) extra.onDemandCapCents = cap;
  const credits = input.credits;
  if (isPlainObject(credits) && typeof credits.unlimited === 'boolean') {
    const balance = isFiniteNumber(credits.balance) && credits.balance >= 0 && credits.balance <= 1e9 ? credits.balance : null;
    extra.credits = { balance, unlimited: credits.unlimited };
  }
  return Object.keys(extra).length > 0 ? extra : undefined;
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
  const extraUsage = sanitizeExtraUsage(raw.extraUsage);
  if (extraUsage !== undefined) snapshot.extraUsage = extraUsage;
  if (isErrorCode(raw.errorCode)) snapshot.errorCode = raw.errorCode;
  else if (state === 'error') snapshot.errorCode = 'internal';
  return snapshot;
}
