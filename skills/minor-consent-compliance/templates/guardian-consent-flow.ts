/**
 * guardian-consent-flow.ts — verifiable parental consent state machine.
 *
 * Owns the *guardian consent route*. The age gate and account blocking live in
 * auth-builder; tracker gating lives in consent-manager. This module:
 *   1. takes a minor account that auth-builder handed off (held inactive),
 *   2. drives the guardian through double opt-in (step 1) and, for sensitive
 *      data, a strong verification (step 2: PASS-guardian / card / signed form),
 *   3. appends one ledger row per transition (never mutate),
 *   4. returns an activation signal only when the latest state is 'granted'.
 *
 * Platform split:
 *   - Web: token links over HTTPS, secrets in server env.
 *   - RN : send the guardian link via email/SMS to a *separate* device; the
 *          minor's device must not be able to self-confirm.
 *
 * Secrets (token signing/HMAC key, PASS/card API keys) come from server env
 * ONLY. Never embed in client bundles or EXPO_PUBLIC_* vars. Store only a HASH
 * of the token and of any guardian verification reference.
 */

export type AgeTier = 'under_14' | 'minor_14_17' | 'adult';
export type Region = 'KR' | 'US' | 'OTHER';
export type Sensitivity = 'basic' | 'sensitive';

export type ConsentState =
  | 'requested'
  | 'email_confirmed'
  | 'verified'
  | 'granted'
  | 'denied'
  | 'expired'
  | 'revoked';

export type VerificationMethod =
  | 'email_double_optin'
  | 'pass_guardian'
  | 'card_auth'
  | 'signed_form_reviewed';

export interface LedgerRow {
  userId: string;
  policyVersion: string;
  ageTier: AgeTier;
  region: Region;
  state: ConsentState;
  actor: 'minor' | 'guardian' | 'system';
  verificationStep: 0 | 1 | 2;
  verificationMethod?: VerificationMethod;
  /** HASH/MASK of guardian email / CI-DI / card BIN — never raw PII. */
  verificationRefHash?: string;
  sensitivity: Sensitivity;
  scope: Record<string, boolean>;
  tokenHash?: string;
  tokenExpiresAt?: string; // ISO
  createdAt: string; // ISO
}

/** Host app provides storage + crypto + clock. Keeps this module deterministic & testable. */
export interface ConsentPorts {
  /** Append one row to minor_consent_ledger. MUST NOT update/delete. */
  appendRow(row: LedgerRow): Promise<void>;
  /** Latest row for the subject, or null. */
  latest(userId: string): Promise<LedgerRow | null>;
  /** HMAC/SHA-256 hex of a value using a server-env secret. Never logs the input. */
  hash(value: string): Promise<string>;
  /** Send the single-use confirmation link to the guardian (email/SMS). */
  sendGuardianLink(guardianContact: string, token: string): Promise<void>;
  /** Strong verification (PASS-guardian / card). Returns a masked reference, never raw PII. */
  runStrongVerification?(method: VerificationMethod): Promise<{ ok: boolean; refMasked: string }>;
  /** Random single-use token (e.g. 32 bytes base64url). */
  newToken(): string;
  now(): Date;
}

const STEP1_METHOD: VerificationMethod = 'email_double_optin';

function ttlIso(now: Date, hours: number): string {
  return new Date(now.getTime() + hours * 3_600_000).toISOString();
}

function base(
  ctx: { userId: string; policyVersion: string; ageTier: AgeTier; region: Region; sensitivity: Sensitivity; scope: Record<string, boolean> },
  now: Date,
): Omit<LedgerRow, 'state' | 'actor' | 'verificationStep'> {
  return {
    userId: ctx.userId,
    policyVersion: ctx.policyVersion,
    ageTier: ctx.ageTier,
    region: ctx.region,
    sensitivity: ctx.sensitivity,
    scope: ctx.scope,
    createdAt: now.toISOString(),
  };
}

export interface StartArgs {
  userId: string;
  policyVersion: string;
  ageTier: AgeTier;
  region: Region;
  sensitivity: Sensitivity;
  scope: Record<string, boolean>;
  guardianContact: string; // email or phone; hashed before storage
  tokenTtlHours?: number; // default 72
}

/**
 * Step 0 -> 1: minor submits guardian contact. Sends a single-use link and writes
 * a 'requested' row. Returns the plaintext token to deliver out-of-band (the
 * ledger stores only its hash).
 */
export async function startGuardianConsent(p: ConsentPorts, a: StartArgs): Promise<{ token: string }> {
  const now = p.now();
  const token = p.newToken();
  const [tokenHash, refHash] = await Promise.all([p.hash(token), p.hash(a.guardianContact)]);
  await p.sendGuardianLink(a.guardianContact, token);
  await p.appendRow({
    ...base(a, now),
    state: 'requested',
    actor: 'minor',
    verificationStep: 0,
    verificationMethod: STEP1_METHOD,
    verificationRefHash: refHash,
    tokenHash,
    tokenExpiresAt: ttlIso(now, a.tokenTtlHours ?? 72),
  });
  return { token };
}

/**
 * Step 1: guardian clicks the link. Validates single-use + not expired, then
 * writes 'email_confirmed'. Expired/invalid -> 'expired' (fail-closed).
 */
export async function confirmGuardianEmail(
  p: ConsentPorts,
  args: { userId: string; token: string },
): Promise<{ state: ConsentState }> {
  const now = p.now();
  const prev = await p.latest(args.userId);
  if (!prev || prev.state !== 'requested' || !prev.tokenHash) {
    return { state: prev?.state ?? 'denied' };
  }
  const expired = !prev.tokenExpiresAt || new Date(prev.tokenExpiresAt).getTime() < now.getTime();
  const tokenHash = await p.hash(args.token);
  const match = tokenHash === prev.tokenHash;
  if (expired || !match) {
    await p.appendRow({ ...prev, state: 'expired', actor: 'system', createdAt: now.toISOString(), tokenHash: undefined });
    return { state: 'expired' };
  }
  await p.appendRow({
    ...prev,
    state: 'email_confirmed',
    actor: 'guardian',
    verificationStep: 1,
    createdAt: now.toISOString(),
    tokenHash: undefined, // consume the single-use token
    tokenExpiresAt: undefined,
  });
  return { state: 'email_confirmed' };
}

/**
 * Step 2 (sensitive data only): strong verification. Writes 'verified' on success.
 * Requires a runStrongVerification port. Stores only a masked reference.
 */
export async function runStrongStep(
  p: ConsentPorts,
  args: { userId: string; method: VerificationMethod },
): Promise<{ state: ConsentState }> {
  const now = p.now();
  const prev = await p.latest(args.userId);
  if (!prev || prev.state !== 'email_confirmed') return { state: prev?.state ?? 'denied' };
  if (!p.runStrongVerification) throw new Error('runStrongVerification port required for sensitive scope');
  const res = await p.runStrongVerification(args.method);
  const refHash = await p.hash(res.refMasked);
  if (!res.ok) {
    await p.appendRow({ ...prev, state: 'denied', actor: 'guardian', createdAt: now.toISOString() });
    return { state: 'denied' };
  }
  await p.appendRow({
    ...prev,
    state: 'verified',
    actor: 'guardian',
    verificationStep: 2,
    verificationMethod: args.method,
    verificationRefHash: refHash,
    createdAt: now.toISOString(),
  });
  return { state: 'verified' };
}

/**
 * Final grant. Enforces the same invariants the DB CHECK constraints do:
 *   - under_14 grant needs a guardian actor with >= step 1,
 *   - sensitive scope needs >= step 2.
 * Returns accountActive=true ONLY on a valid grant (fail-closed otherwise).
 */
export async function grantConsent(p: ConsentPorts, args: { userId: string }): Promise<{ accountActive: boolean; reason?: string }> {
  const now = p.now();
  const prev = await p.latest(args.userId);
  if (!prev) return { accountActive: false, reason: 'no consent record' };

  const requiredStep = prev.sensitivity === 'sensitive' ? 2 : 1;
  const ready = prev.state === 'verified' || (requiredStep === 1 && prev.state === 'email_confirmed');
  if (!ready) return { accountActive: false, reason: `not ready (state=${prev.state})` };
  if (prev.ageTier === 'under_14' && prev.actor !== 'guardian') {
    return { accountActive: false, reason: 'under_14 requires guardian actor' };
  }
  if (prev.verificationStep < requiredStep) {
    return { accountActive: false, reason: `needs verification step ${requiredStep}` };
  }

  await p.appendRow({ ...prev, state: 'granted', actor: 'guardian', createdAt: now.toISOString() });
  return { accountActive: true };
}

/** Guardian withdrawal. Writes 'revoked' and signals deactivation + tracker OFF. */
export async function revokeConsent(p: ConsentPorts, args: { userId: string }): Promise<{ accountActive: false }> {
  const now = p.now();
  const prev = await p.latest(args.userId);
  if (prev) {
    await p.appendRow({ ...prev, state: 'revoked', actor: 'guardian', createdAt: now.toISOString() });
  }
  return { accountActive: false };
}

/** fail-closed read: account is active only if the latest row is 'granted'. */
export async function isAccountActive(p: ConsentPorts, userId: string): Promise<boolean> {
  const prev = await p.latest(userId);
  return prev?.state === 'granted';
}
