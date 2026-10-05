-- purge-audit-log — append-only record of every purge execution.
--
-- Hard rules:
--   * Append-only: UPDATE and DELETE are blocked by trigger. Every run is a NEW row.
--   * Evidence: proves PIPA §21 "지체 없이 파기" was actually carried out, and when.
--   * Always log, even 0 rows. A silent purge job is an unprovable purge job.
--
-- Adapt types if not on Postgres. The purge job (templates/purge-job.ts) and the
-- generated purge-plan.sql both INSERT here.

CREATE TABLE IF NOT EXISTS purge_audit_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- What was purged.
  data_class      TEXT        NOT NULL,                 -- matches retention-classes.json id
  table_name      TEXT        NOT NULL,
  action          TEXT        NOT NULL,                 -- soft_delete | hard_delete | ttl_delete | hard_delete_legal
  rows_affected   INTEGER     NOT NULL DEFAULT 0,       -- 0 is valid and MUST still be logged

  -- How / who.
  trigger_source  TEXT        NOT NULL DEFAULT 'cron',  -- cron | account_deletion | consent_withdrawal | manual
  policy_version  TEXT,                                 -- retention policy version in force at run time
  executor        TEXT        NOT NULL DEFAULT 'system',-- system | <admin id> for manual runs

  -- Outcome. A failed run is logged too (status='error') so retries are visible.
  status          TEXT        NOT NULL DEFAULT 'ok',    -- ok | error
  error_detail    TEXT,

  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT purge_action_valid CHECK (
    action IN ('soft_delete', 'hard_delete', 'ttl_delete', 'hard_delete_legal')
  ),
  CONSTRAINT purge_status_valid CHECK (status IN ('ok', 'error'))
);

CREATE INDEX IF NOT EXISTS purge_audit_class_idx ON purge_audit_log (data_class, created_at DESC);
CREATE INDEX IF NOT EXISTS purge_audit_status_idx ON purge_audit_log (status, created_at DESC);

-- ---------------------------------------------------------------------------
-- Append-only enforcement: block UPDATE and DELETE at the DB level.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION purge_audit_block_mutation()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'purge_audit_log is append-only: % is not allowed. Insert a new row instead.', TG_OP;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS purge_audit_no_update ON purge_audit_log;
CREATE TRIGGER purge_audit_no_update
  BEFORE UPDATE ON purge_audit_log
  FOR EACH ROW EXECUTE FUNCTION purge_audit_block_mutation();

DROP TRIGGER IF EXISTS purge_audit_no_delete ON purge_audit_log;
CREATE TRIGGER purge_audit_no_delete
  BEFORE DELETE ON purge_audit_log
  FOR EACH ROW EXECUTE FUNCTION purge_audit_block_mutation();

-- ---------------------------------------------------------------------------
-- Convenience: last run per class (for a retention dashboard / health check).
-- An alert should fire if a class has no 'ok' row within its expected cadence.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW purge_last_run AS
SELECT DISTINCT ON (data_class)
  data_class, table_name, action, rows_affected, status, created_at
FROM purge_audit_log
ORDER BY data_class, created_at DESC;

-- RLS note: this table is admin/service-only. Never grant SELECT to anon.
-- ALTER TABLE purge_audit_log ENABLE ROW LEVEL SECURITY;
-- (no anon policy — service role only)
