-- minor-consent-ledger — append-only ledger for the minor / guardian consent lifecycle.
--
-- Distinct from consent-manager's tracker-category ledger. This one records the
-- verifiable-parental-consent lifecycle for a minor's account.
--
-- Hard rules:
--   * Append-only: UPDATE and DELETE blocked by trigger. Every state change = NEW row.
--   * fail-closed: account is active ONLY when the latest row for the subject is 'granted'.
--   * Data minimization: store a HASH/MASK of the guardian verification reference
--     (CI/DI, card BIN, email), never the raw PII.
--
-- Adapt types if not on Postgres. Sits alongside an existing users table.

CREATE TABLE IF NOT EXISTS minor_consent_ledger (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Subject = the minor's account (handed off by auth-builder, held inactive).
  user_id               UUID REFERENCES users(id) ON DELETE CASCADE,

  -- Versioned policy + tier so the audit export can flag stale grants.
  policy_version        TEXT        NOT NULL,                 -- e.g. '2026-06-01'
  age_tier              TEXT        NOT NULL,                 -- under_14 | minor_14_17 | adult
  region                TEXT        NOT NULL,                 -- KR | US | OTHER

  -- Lifecycle state. Transition = new row (never mutate).
  --   requested -> email_confirmed -> verified -> granted | denied | expired | revoked
  state                 TEXT        NOT NULL,
  actor                 TEXT        NOT NULL DEFAULT 'system', -- minor | guardian | system

  -- Verification evidence (data-minimized).
  verification_step     SMALLINT    NOT NULL DEFAULT 0,       -- 0=none, 1=email, 2=strong (pass/card/form)
  verification_method   TEXT,                                 -- email_double_optin | pass_guardian | card_auth | signed_form_reviewed
  verification_ref_hash TEXT,                                 -- HASH/MASK of guardian email / CI-DI / card BIN — NEVER raw PII
  sensitivity           TEXT        NOT NULL DEFAULT 'basic', -- basic | sensitive (drives required step)

  -- Consent scope: what the guardian agreed the minor's data may be used for.
  scope                 JSONB       NOT NULL DEFAULT '{}'::jsonb,

  -- Single-use, short-lived guardian-confirmation token (store hash only).
  token_hash            TEXT,
  token_expires_at      TIMESTAMPTZ,

  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT minor_state_valid CHECK (
    state IN ('requested','email_confirmed','verified','granted','denied','expired','revoked')
  ),
  CONSTRAINT minor_step_range CHECK (verification_step BETWEEN 0 AND 2),
  -- A granted under_14 row must carry a guardian actor with at least step-1 evidence.
  CONSTRAINT minor_granted_needs_guardian CHECK (
    NOT (age_tier = 'under_14' AND state = 'granted')
    OR (actor = 'guardian' AND verification_step >= 1 AND verification_method IS NOT NULL)
  ),
  -- Sensitive scope cannot be granted on step-1 (email) alone.
  CONSTRAINT minor_sensitive_needs_strong CHECK (
    NOT (state = 'granted' AND sensitivity = 'sensitive')
    OR verification_step >= 2
  )
);

CREATE INDEX IF NOT EXISTS minor_consent_user_idx
  ON minor_consent_ledger (user_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- Append-only enforcement: block UPDATE and DELETE at the DB level.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION minor_consent_block_mutation()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'minor_consent_ledger is append-only: % is not allowed. Insert a new row instead.', TG_OP;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS minor_consent_no_update ON minor_consent_ledger;
CREATE TRIGGER minor_consent_no_update
  BEFORE UPDATE ON minor_consent_ledger
  FOR EACH ROW EXECUTE FUNCTION minor_consent_block_mutation();

DROP TRIGGER IF EXISTS minor_consent_no_delete ON minor_consent_ledger;
CREATE TRIGGER minor_consent_no_delete
  BEFORE DELETE ON minor_consent_ledger
  FOR EACH ROW EXECUTE FUNCTION minor_consent_block_mutation();

-- ---------------------------------------------------------------------------
-- Current effective state = the latest row per subject. Account is active
-- (fail-closed) only when current state = 'granted'.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW minor_consent_current AS
SELECT DISTINCT ON (user_id)
  user_id, policy_version, age_tier, region, state, actor,
  verification_step, verification_method, sensitivity, scope, created_at,
  (state = 'granted') AS account_active
FROM minor_consent_ledger
ORDER BY user_id, created_at DESC;

-- RLS note: enable RLS so a guardian/minor can read only their own rows; INSERT
-- allowed, UPDATE/DELETE never granted (triggers above are defense-in-depth).
-- ALTER TABLE minor_consent_ledger ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY minor_self_read ON minor_consent_ledger FOR SELECT USING (auth.uid() = user_id);
-- CREATE POLICY minor_self_insert ON minor_consent_ledger FOR INSERT WITH CHECK (auth.uid() = user_id);
