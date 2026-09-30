// Parsers for Codex app-server messages. Shapes follow the stable schema from
// `codex app-server generate-json-schema` (codex-cli 0.154.0); unknown fields are ignored.

import path from 'node:path';
import { maskEmail } from '../../../shared/mask';
import type { QuotaWindow } from '../../../shared/types';
import { classifyWindowKind, epochSecondsToMs, normalizePercent } from '../../../shared/usage';

export const CLIENT_NAME = 'ai-usage-widget';

/** Only these methods are ever sent. Reset redemption is called only after native user confirmation. */
export const METHOD = {
  initialize: 'initialize',
  initialized: 'initialized',
  accountRead: 'account/read',
  rateLimitsRead: 'account/rateLimits/read',
  resetCreditConsume: 'account/rateLimitResetCredit/consume',
  loginStart: 'account/login/start',
  loginCancel: 'account/login/cancel',
  loginCompleted: 'account/login/completed',
} as const;

/** Bucket id of the historical single-bucket view when the server does not name it. */
export const DEFAULT_LIMIT_ID = 'codex';

type Obj = Record<string, unknown>;

function isObj(value: unknown): value is Obj {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function nonEmptyString(value: unknown): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}

// eslint-disable-next-line no-control-regex
const CONTROL_OR_BIDI_RE = /[\u0000-\u001f\u007f\u200e\u200f\u202a-\u202e\u2066-\u2069]/;
const TOKEN_LIKE_RE = /^[A-Za-z0-9_.:-]{1,64}$/;

/** Plan types and bucket ids: short identifier-like strings only (unknown values pass through). */
export function sanitizeIdentifier(value: unknown): string | undefined {
  const text = nonEmptyString(value);
  return text !== undefined && TOKEN_LIKE_RE.test(text) ? text : undefined;
}

/** Normalized, case-insensitive path equality (strips the `\\?\` verbatim prefix). */
export function samePath(a: string, b: string): boolean {
  const norm = (value: string): string => {
    const stripped = value.startsWith('\\\\?\\') ? value.slice(4) : value;
    const resolved = path.win32.resolve(stripped).replace(/[\\/]+$/, '');
    return resolved.toLowerCase();
  };
  return norm(a) === norm(b);
}

export function isSafeHttpsUrl(value: unknown): value is string {
  if (typeof value !== 'string' || value.length === 0 || value.length > 2048) return false;
  if (CONTROL_OR_BIDI_RE.test(value)) return false;
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    return false;
  }
  return url.protocol === 'https:' && url.username === '' && url.password === '' && url.hostname.length > 0;
}

// ---------------------------------------------------------------------------
// initialize (v1/InitializeResponse.json)

export interface InitializeInfo {
  codexHome: string;
  platformOs?: string;
}

export function parseInitializeResult(value: unknown): InitializeInfo | null {
  if (!isObj(value)) return null;
  const codexHome = nonEmptyString(value.codexHome);
  if (codexHome === undefined) return null;
  const info: InitializeInfo = { codexHome };
  const platformOs = sanitizeIdentifier(value.platformOs);
  if (platformOs !== undefined) info.platformOs = platformOs;
  return info;
}

// ---------------------------------------------------------------------------
// account/login/start (v2/LoginAccountResponse.json, chatgptDeviceCode variant)

export interface DeviceCodeStart {
  loginId: string;
  userCode: string;
  verificationUrl: string;
}

export function parseLoginStartResult(value: unknown): DeviceCodeStart | null {
  if (!isObj(value)) return null;
  if (value.type !== undefined && value.type !== 'chatgptDeviceCode') return null;
  const loginId = nonEmptyString(value.loginId);
  const userCode = nonEmptyString(value.userCode)?.trim();
  if (loginId === undefined || loginId.length > 256 || userCode === undefined) return null;
  if (userCode.length === 0 || userCode.length > 64 || CONTROL_OR_BIDI_RE.test(userCode)) return null;
  if (!isSafeHttpsUrl(value.verificationUrl)) return null;
  return { loginId, userCode, verificationUrl: value.verificationUrl };
}

// ---------------------------------------------------------------------------
// account/login/completed (v2/AccountLoginCompletedNotification.json)

export interface LoginCompleted {
  loginId: string | null;
  success: boolean;
  /** Raw provider text: classify it, never forward it to the renderer. */
  error: string | null;
}

export function parseLoginCompleted(value: unknown): LoginCompleted | null {
  if (!isObj(value) || typeof value.success !== 'boolean') return null;
  return {
    loginId: nonEmptyString(value.loginId) ?? null,
    success: value.success,
    error: nonEmptyString(value.error) ?? null,
  };
}

// ---------------------------------------------------------------------------
// account/read (v2/GetAccountResponse.json)

export type CodexAccountInfo =
  | { kind: 'none' }
  | { kind: 'chatgpt'; emailMasked?: string; planType?: string }
  /** apiKey / amazonBedrock / future types: signed in, but no subscription limits. */
  | { kind: 'other' };

export function parseAccountRead(value: unknown): CodexAccountInfo | null {
  if (!isObj(value)) return null;
  const account = value.account;
  if (account === undefined || account === null) return { kind: 'none' };
  if (!isObj(account) || typeof account.type !== 'string') return null;
  if (account.type !== 'chatgpt') return { kind: 'other' };
  const info: { kind: 'chatgpt'; emailMasked?: string; planType?: string } = { kind: 'chatgpt' };
  const email = nonEmptyString(account.email);
  if (email !== undefined) info.emailMasked = maskEmail(email);
  const planType = sanitizeIdentifier(account.planType);
  if (planType !== undefined) info.planType = planType;
  return info;
}

// ---------------------------------------------------------------------------
// account/rateLimits/read (v2/GetAccountRateLimitsResponse.json)

export interface CodexCredits {
  hasCredits: boolean;
  unlimited: boolean;
  balance: string | null;
}

export interface CodexRateLimits {
  windows: QuotaWindow[];
  planType?: string;
  credits?: CodexCredits;
  rateLimitReachedType?: string;
  resetCreditCount?: number;
}

export interface CodexResetOffer {
  /** Backend account returned by the same account-specific usage read. Never sent to a renderer. */
  backendAccountId: string;
  /** Opaque credit identifier. Never sent to a renderer or log. */
  creditId: string;
  availableCount: number;
  expiresAt: number | null;
}

export type ConsumeResetOutcome = 'reset' | 'nothingToReset' | 'noCredit' | 'alreadyRedeemed';

function resetCreditCount(value: unknown): number | undefined {
  if (!isObj(value)) return undefined;
  const count = value.availableCount;
  return typeof count === 'number' && Number.isSafeInteger(count) && count >= 0 && count <= 1_000 ? count : undefined;
}

/** A count-only background read is not enough to offer redemption. */
export function parseResetOffer(value: unknown, now: number): CodexResetOffer | null {
  if (!isObj(value) || !isObj(value.rateLimitResetCredits)) return null;
  const backendAccountId = nonEmptyString(value.accountId);
  if (backendAccountId === undefined || backendAccountId.length > 256 || CONTROL_OR_BIDI_RE.test(backendAccountId)) return null;
  const availableCount = resetCreditCount(value.rateLimitResetCredits);
  if (availableCount === undefined || availableCount === 0) return null;
  const rows = value.rateLimitResetCredits.credits;
  if (!Array.isArray(rows)) return null;
  const eligible = rows.flatMap((row): CodexResetOffer[] => {
    if (!isObj(row) || row.resetType !== 'codexRateLimits' || row.status !== 'available') return [];
    const creditId = nonEmptyString(row.id);
    if (creditId === undefined || creditId.length > 256 || CONTROL_OR_BIDI_RE.test(creditId)) return [];
    const expiresAt = row.expiresAt == null ? null : epochSecondsToMs(row.expiresAt);
    if (expiresAt === null && row.expiresAt != null) return [];
    if (expiresAt !== null && expiresAt <= now) return [];
    return [{ backendAccountId, creditId, availableCount, expiresAt }];
  });
  eligible.sort((a, b) => (a.expiresAt ?? Infinity) - (b.expiresAt ?? Infinity));
  return eligible[0] ?? null;
}

export function parseConsumeResetOutcome(value: unknown): ConsumeResetOutcome | null {
  if (!isObj(value)) return null;
  const outcome = value.outcome;
  return outcome === 'reset' || outcome === 'nothingToReset' || outcome === 'noCredit' || outcome === 'alreadyRedeemed'
    ? outcome
    : null;
}

function parseWindowMinutes(value: unknown): number | null {
  if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) return null;
  return Math.round(value);
}

function toQuotaWindow(raw: unknown, label: string | undefined): QuotaWindow | null {
  if (!isObj(raw)) return null;
  const windowMinutes = parseWindowMinutes(raw.windowDurationMins);
  const usedPercent = normalizePercent(raw.usedPercent);
  const resetsAt = epochSecondsToMs(raw.resetsAt);
  if (usedPercent === null && resetsAt === null && windowMinutes === null) return null;
  const kind = classifyWindowKind(windowMinutes);
  const window: QuotaWindow = { kind, usedPercent, resetsAt, windowMinutes };
  if (label !== undefined) window.label = label;
  return window;
}

function parseCredits(value: unknown): CodexCredits | undefined {
  if (!isObj(value) || typeof value.hasCredits !== 'boolean' || typeof value.unlimited !== 'boolean') {
    return undefined;
  }
  const balance = typeof value.balance === 'string' && value.balance.length <= 64 ? value.balance : null;
  return { hasCredits: value.hasCredits, unlimited: value.unlimited, balance };
}

/**
 * Buckets come from `rateLimitsByLimitId` (multi-bucket view); the legacy
 * `rateLimits` view mirrors one of them and is used when the map is absent.
 * The primary bucket is listed first; its session/weekly windows carry no
 * label, every other window is labelled with its bucket id.
 */
export function parseRateLimits(value: unknown): CodexRateLimits | null {
  if (!isObj(value)) return null;
  const legacy = isObj(value.rateLimits) ? value.rateLimits : undefined;
  const byId = isObj(value.rateLimitsByLimitId) ? value.rateLimitsByLimitId : undefined;
  if (legacy === undefined && byId === undefined) return null;

  const primaryId = sanitizeIdentifier(legacy?.limitId) ?? DEFAULT_LIMIT_ID;
  const buckets: Array<[string, Obj]> = [];
  if (byId !== undefined) {
    for (const [key, bucket] of Object.entries(byId)) {
      const id = sanitizeIdentifier(key);
      if (id !== undefined && isObj(bucket)) buckets.push([id, bucket]);
    }
  }
  if (legacy !== undefined && !buckets.some(([id]) => id === primaryId)) buckets.push([primaryId, legacy]);
  buckets.sort(([a], [b]) => {
    if (a === primaryId) return -1;
    if (b === primaryId) return 1;
    return a < b ? -1 : a > b ? 1 : 0;
  });

  const windows: QuotaWindow[] = [];
  for (const [id, bucket] of buckets) {
    for (const slot of [bucket.primary, bucket.secondary]) {
      const unlabeled = toQuotaWindow(slot, undefined);
      if (unlabeled === null) continue;
      const needsLabel = id !== primaryId || unlabeled.kind === 'other';
      windows.push(needsLabel ? { ...unlabeled, label: id } : unlabeled);
    }
  }

  const primary = buckets[0]?.[0] === primaryId ? buckets[0][1] : undefined;
  const result: CodexRateLimits = { windows };
  const planType =
    sanitizeIdentifier(legacy?.planType) ??
    sanitizeIdentifier(primary?.planType) ??
    buckets.map(([, bucket]) => sanitizeIdentifier(bucket.planType)).find((plan) => plan !== undefined);
  if (planType !== undefined) result.planType = planType;
  const credits = parseCredits(primary?.credits ?? legacy?.credits);
  if (credits !== undefined) result.credits = credits;
  const reached = sanitizeIdentifier(primary?.rateLimitReachedType ?? legacy?.rateLimitReachedType);
  if (reached !== undefined) result.rateLimitReachedType = reached;
  const resetCount = resetCreditCount(value.rateLimitResetCredits);
  if (resetCount !== undefined) result.resetCreditCount = resetCount;
  return result;
}
