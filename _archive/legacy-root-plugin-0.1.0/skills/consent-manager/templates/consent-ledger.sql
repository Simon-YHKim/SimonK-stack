-- consent-ledger — append-only versioned consent ledger.
--
-- Hard rules:
--   * Append-only: UPDATE and DELETE are blocked by trigger. Every change is a NEW row.
--   * Audit: each row captures who/when/which-policy/which-categories/how (source).
--   * Retention: rows are immutable evidence of consent. Do not prune within the
--     retention window required by GDPR/PIPA/CCPA.
--
-- Adapt types if not on Postgres. Designed to sit alongside an existing users table.

CREATE TABLE IF NOT EXISTS consent_ledger (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Subject. user_id is null for pre-auth (anonymous) banners; anon_id ties
  -- a pre-login decision to a device/session so it can be reconciled at login.
  user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
  anon_id         TEXT,

  -- What was decided.
  policy_version  TEXT        NOT NULL,                 -- e.g. '2026-06-01'
  region          TEXT        NOT NULL,                 -- EU | KR | US | OTHER | UNKNOWN
  -- Per-category booleans. necessary is always true (disclosed, not toggleable).
  necessary       BOOLEAN     NOT NULL DEFAULT true,
  functional      BOOLEAN     NOT NULL DEFAULT false,
  analytics       BOOLEAN     NOT NULL DEFAULT false,
  advertising     BOOLEAN     NOT NULL DEFAULT false,

  -- How / who.
  source          TEXT        NOT NULL,                 -- banner | settings | gpc | dnt | guardian | default
  actor           TEXT        NOT NULL DEFAULT 'user',  -- user | guardian | system
  is_minor        BOOLEAN     NOT NULL DEFAULT false,
  -- Verifiable parental consent evidence (when actor='guardian'); set by auth-builder handoff.
  guardian_verification TEXT,                           -- e.g. 'pass-ci', 'card-auth', 'email-loop'

  -- Provenance for disputes.
  ip_address      INET,
  user_agent      TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT consent_subject_present CHECK (user_id IS NOT NULL OR anon_id IS NOT NULL),
  CONSTRAINT consent_necessary_true  CHECK (necessary = true),
  CONSTRAINT consent_minor_guardian  CHECK (
    -- A minor enabling advertising/analytics must have a verified guardian record.
    NOT (is_minor = true AND (advertising = true OR analytics = true))
    OR (actor = 'guardian' AND guardian_verification IS NOT NULL)
  )
);

-- Fast lookup of a subject's latest decision.
CREATE INDEX IF NOT EXISTS consent_ledger_user_idx ON consent_ledger (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS consent_ledger_anon_idx ON consent_ledger (anon_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- Append-only enforcement: block UPDATE and DELETE at the DB level.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION consent_ledger_block_mutation()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'consent_ledger is append-only: % is not allowed. Insert a new row instead.', TG_OP;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS consent_ledger_no_update ON consent_ledger;
CREATE TRIGGER consent_ledger_no_update
  BEFORE UPDATE ON consent_ledger
  FOR EACH ROW EXECUTE FUNCTION consent_ledger_block_mutation();

DROP TRIGGER IF EXISTS consent_ledger_no_delete ON consent_ledger;
CREATE TRIGGER consent_ledger_no_delete
  BEFORE DELETE ON consent_ledger
  FOR EACH ROW EXECUTE FUNCTION consent_ledger_block_mutation();

-- ---------------------------------------------------------------------------
-- Current effective consent = the latest row per subject. View for convenience.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW consent_current AS
SELECT DISTINCT ON (COALESCE(user_id::text, anon_id))
  COALESCE(user_id::text, anon_id) AS subject,
  user_id, anon_id, policy_version, region,
  necessary, functional, analytics, advertising,
  source, actor, is_minor, created_at
FROM consent_ledger
ORDER BY COALESCE(user_id::text, anon_id), created_at DESC;

-- RLS note: enable RLS so a user can read only their own rows; INSERT allowed,
-- UPDATE/DELETE never granted (triggers above are defense-in-depth).
-- ALTER TABLE consent_ledger ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY consent_self_read ON consent_ledger FOR SELECT USING (auth.uid() = user_id);
-- CREATE POLICY consent_self_insert ON consent_ledger FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);
