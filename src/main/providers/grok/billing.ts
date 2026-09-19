// Parser for the result of grok's ACP extension `_x.ai/billing`.
// The shape is undocumented. Field names come from grok.exe 1.0.30 serde strings
// (crates/codegen/xai-grok-shell/src/extensions/billing.rs) and RESEARCH-auth-quota §3-3.
// Unknown fields are ignored; anything missing stays null (never 0).

import type { QuotaWindow } from '../../../shared/types';
import { WEEKLY_WINDOW_MINUTES, normalizePercent } from '../../../shared/usage';

export type BillingPeriodType = 'weekly' | 'monthly' | 'unknown';

export interface GrokBilling {
  windows: QuotaWindow[];
  plan?: string;
  periodType: BillingPeriodType;
  /**
   * Usage can continue past the included credits (on-demand or prepaid balance).
   * Grok never hard-stops at 100% (docs.x.ai FAQ), so 100% must not render as blocked.
   * null = the response did not say.
   */
  overageAvailable: boolean | null;
}

type JsonObject = Record<string, unknown>;

function isRecord(value: unknown): value is JsonObject {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

const NUMERIC_RE = /^-?\d+(?:\.\d+)?$/;

/** Numbers, numeric strings (int64 JSON) and `{val}` / `{value}` wrappers; otherwise null. */
export function parseAmount(value: unknown, depth = 0): number | null {
  if (typeof value === 'number') return Number.isFinite(value) ? value : null;
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return NUMERIC_RE.test(trimmed) ? Number(trimmed) : null;
  }
  if (isRecord(value) && depth < 2) {
    if ('val' in value) return parseAmount(value.val, depth + 1);
    if ('value' in value) return parseAmount(value.value, depth + 1);
  }
  return null;
}

const MIN_EPOCH_SECONDS = 1_000_000_000;
const MIN_EPOCH_MS = 1_000_000_000_000;

/** ISO-8601 strings, epoch seconds or ms (number or numeric string), `{seconds}` objects. */
export function parseTimestamp(value: unknown): number | null {
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return null;
    if (value >= MIN_EPOCH_MS) return Math.round(value);
    if (value >= MIN_EPOCH_SECONDS) return Math.round(value * 1000);
    return null;
  }
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (trimmed.length === 0) return null;
    if (NUMERIC_RE.test(trimmed)) return parseTimestamp(Number(trimmed));
    const ms = Date.parse(trimmed);
    return Number.isFinite(ms) ? ms : null;
  }
  if (isRecord(value) && 'seconds' in value) {
    const seconds = parseAmount(value.seconds);
    return seconds !== null && seconds >= MIN_EPOCH_SECONDS ? Math.round(seconds * 1000) : null;
  }
  return null;
}

/** Orca maps `USAGE_PERIOD_TYPE_WEEKLY`; the TUI shows WEEKLY/MONTHLY. Accept both spellings. */
export function parsePeriodType(value: unknown): BillingPeriodType {
  if (typeof value !== 'string') return 'unknown';
  const upper = value.toUpperCase();
  if (upper.includes('WEEK')) return 'weekly';
  if (upper.includes('MONTH')) return 'monthly';
  return 'unknown';
}

const TIER_PREFIX_RE = /^(?:SUBSCRIPTION_TIER_|TIER_)/i;
const TIER_CHARS_RE = /^[A-Za-z0-9 _.+-]+$/;
const TIER_EMPTY_RE = /^(?:UNSPECIFIED|UNKNOWN|NONE)$/i;

/** `SUBSCRIPTION_TIER_SUPER_GROK` -> `Super Grok`; mixed-case names are kept. */
export function normalizeTier(value: unknown): string | undefined {
  if (typeof value !== 'string') return undefined;
  let tier = value.trim().replace(TIER_PREFIX_RE, '');
  if (tier.length === 0 || tier.length > 64 || !TIER_CHARS_RE.test(tier) || TIER_EMPTY_RE.test(tier)) {
    return undefined;
  }
  if (tier === tier.toUpperCase()) {
    tier = tier
      .split(/[_\s]+/)
      .filter((word) => word.length > 0)
      .map((word) => word.charAt(0) + word.slice(1).toLowerCase())
      .join(' ');
  }
  return tier.length > 0 ? tier : undefined;
}

const BILLING_KEYS = ['creditUsagePercent', 'currentPeriod', 'monthlyLimit', 'used', 'billingPeriodEnd'];

function hasBillingKeys(value: JsonObject): boolean {
  return BILLING_KEYS.some((key) => key in value);
}

function findBillingRoot(result: JsonObject): JsonObject {
  if (hasBillingKeys(result)) return result;
  for (const inner of Object.values(result)) {
    if (isRecord(inner) && hasBillingKeys(inner)) return inner;
  }
  return result;
}

function findTier(result: JsonObject, root: JsonObject): string | undefined {
  const candidates = [root, result, ...Object.values(result).filter(isRecord)];
  for (const candidate of candidates) {
    const tier = normalizeTier(candidate.subscriptionTier ?? candidate.subscription_tier);
    if (tier !== undefined) return tier;
  }
  return undefined;
}

function detectOverage(root: JsonObject): boolean | null {
  const enabled = root.on_demand_enabled ?? root.onDemandEnabled;
  const prepaid = parseAmount(root.prepaidBalance);
  const cap = parseAmount(root.onDemandCap);
  const onDemandUsed = parseAmount(root.onDemandUsed);
  if (enabled === true) return true;
  if (prepaid !== null && prepaid > 0) return true;
  if (cap !== null && cap > 0 && (onDemandUsed === null || onDemandUsed < cap)) return true;
  if (enabled === false) return false;
  return null;
}

/** Fields the billing config always carries next to `currentPeriod` (measured 26.09.20, grok 1.0.34). */
const CONFIG_COMPANION_KEYS = ['billingPeriodEnd', 'isUnifiedBillingUser', 'onDemandCap', 'onDemandUsed', 'prepaidBalance'];

/**
 * The payload is proto3 JSON, which leaves zero-valued scalars out: a weekly config right
 * after its reset arrives with every companion field but no `creditUsagePercent`
 * (DECISIONS 26.09.20). That absence is a measured 0 only when the rest of the config is
 * there; a present-but-unreadable value, or a bare object, stays unknown.
 */
function creditPercentOmittedAsZero(root: JsonObject, periodType: BillingPeriodType, periodEnd: number | null): boolean {
  if ('creditUsagePercent' in root || periodType !== 'weekly' || periodEnd === null) return false;
  return CONFIG_COMPANION_KEYS.filter((key) => key in root).length >= 2;
}

function minutesBetween(start: number | null, end: number | null): number | null {
  if (start === null || end === null || end <= start) return null;
  return Math.round((end - start) / 60_000);
}

function roundPercent(value: number | null): number | null {
  return value === null ? null : Math.round(value * 100) / 100;
}

/**
 * Maps a billing result to quota windows.
 * - weekly: `creditUsagePercent` + `currentPeriod.end`, only when `currentPeriod.type` is weekly.
 *   A full weekly config without the percent field reads as 0 % (see creditPercentOmittedAsZero).
 * - otherwise one 'other' window: `used / monthlyLimit` (label `monthly`), or the credit percent
 *   when the monthly amounts are missing.
 * Returns null when `result` is not an object.
 */
export function parseBillingResponse(result: unknown): GrokBilling | null {
  if (!isRecord(result)) return null;
  const root = findBillingRoot(result);
  const period = isRecord(root.currentPeriod) ? root.currentPeriod : {};
  const periodType = parsePeriodType(period.type ?? period.periodType);
  const periodStart = parseTimestamp(period.start);
  const periodEnd = parseTimestamp(period.end);
  const creditPercent = creditPercentOmittedAsZero(root, periodType, periodEnd)
    ? 0
    : roundPercent(normalizePercent(parseAmount(root.creditUsagePercent)));
  const windows: QuotaWindow[] = [];

  if (periodType === 'weekly' && creditPercent !== null) {
    windows.push({
      kind: 'weekly',
      usedPercent: creditPercent,
      resetsAt: periodEnd,
      windowMinutes: WEEKLY_WINDOW_MINUTES,
      label: 'credits',
    });
  } else {
    const limit = parseAmount(root.monthlyLimit);
    const used = parseAmount(root.used);
    if (limit !== null && limit > 0 && used !== null) {
      const start = parseTimestamp(root.billingPeriodStart) ?? (periodType === 'monthly' ? periodStart : null);
      const end = parseTimestamp(root.billingPeriodEnd) ?? (periodType === 'monthly' ? periodEnd : null);
      windows.push({
        kind: 'other',
        usedPercent: roundPercent(normalizePercent((used / limit) * 100)),
        resetsAt: end,
        windowMinutes: minutesBetween(start, end),
        label: 'monthly',
      });
    } else if (creditPercent !== null) {
      windows.push({
        kind: 'other',
        usedPercent: creditPercent,
        resetsAt: periodEnd,
        windowMinutes: minutesBetween(periodStart, periodEnd),
        label: periodType === 'monthly' ? 'monthly' : 'credits',
      });
    }
  }

  const billing: GrokBilling = { windows, periodType, overageAvailable: detectOverage(root) };
  const plan = findTier(result, root);
  if (plan !== undefined) billing.plan = plan;
  return billing;
}
