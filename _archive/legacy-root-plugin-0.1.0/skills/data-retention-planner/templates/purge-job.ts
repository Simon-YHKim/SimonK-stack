// purge-job.ts — scheduled data-retention purge runner.
//
// Reads retention-classes.json (the single source of truth), runs the
// generated purge SQL per class, and records every run in purge_audit_log.
//
// Design rules (mirrors SKILL.md "강제 베스트프랙티스"):
//   * soft -> hard 2-step (handled by the generated SQL; see gen-purge-plan.mjs).
//   * fail-safe: a class failure is logged (status='error') and RE-THROWN so the
//     scheduler marks the run failed and retries on the next tick. Never swallow.
//   * 0 rows is still logged (the audit INSERT runs unconditionally inside the SQL).
//   * secrets come from env ONLY — never hard-code service-role keys / DB URLs.
//
// Runtimes:
//   - Supabase Edge Function: invoke from pg_cron or a scheduled trigger.
//   - Node cron (GitHub Actions / Cloud Scheduler hitting an endpoint): call run().
//
// This template assumes Postgres via the supabase-js service-role client. Swap
// the executor for `pg` / Prisma if you are not on Supabase — the contract is
// just: run a SQL string, return affected row count, never leak the connection.

import { createClient } from "@supabase/supabase-js";
import retentionClasses from "./retention-classes.json" assert { type: "json" };

// --- secrets: env only -----------------------------------------------------
const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY; // server-side ONLY
if (!SUPABASE_URL || !SERVICE_ROLE_KEY) {
  throw new Error("purge-job: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars are required");
}

const db = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
  auth: { persistSession: false },
});

type RetentionClass = {
  id: string;
  table: string;
  timestampColumn: string;
  retentionDays: number;
  graceDays: number;
  softDelete?: boolean;
  softDeleteColumn?: string;
  legalHold?: boolean;
};

const POLICY_VERSION =
  (retentionClasses as { _policyVersion?: string })._policyVersion ?? "unversioned";
const CLASSES: RetentionClass[] = (retentionClasses as { classes: RetentionClass[] }).classes;

// Run a single SQL statement and return rows affected. Replace with your driver.
// Here we assume a Postgres RPC `exec_purge(sql text)` that returns the row count
// (a thin SECURITY DEFINER function — do NOT expose raw SQL execution to clients).
async function execPurge(sql: string): Promise<number> {
  const { data, error } = await db.rpc("exec_purge", { p_sql: sql });
  if (error) throw new Error(error.message);
  return typeof data === "number" ? data : 0;
}

// Always-log helper. Logs ok OR error; the audit log itself is append-only.
async function logRun(params: {
  dataClass: string;
  table: string;
  action: string;
  rows: number;
  trigger: string;
  status: "ok" | "error";
  errorDetail?: string;
}): Promise<void> {
  await db.from("purge_audit_log").insert({
    data_class: params.dataClass,
    table_name: params.table,
    action: params.action,
    rows_affected: params.rows,
    trigger_source: params.trigger,
    policy_version: POLICY_VERSION,
    executor: "system",
    status: params.status,
    error_detail: params.errorDetail ?? null,
  });
}

// Build the per-class purge SQL inline. Prefer the file produced by
// gen-purge-plan.mjs (purge-plan.sql) and load it instead — kept here so the
// job is self-contained and the logic is auditable in one place.
function buildSql(c: RetentionClass): { action: string; sql: string }[] {
  const ts = c.timestampColumn;
  const soft = c.softDeleteColumn ?? "deleted_at";
  const ret = `INTERVAL '${c.retentionDays} days'`;
  const grace = `INTERVAL '${c.graceDays} days'`;
  const usesSoft = c.softDelete !== false;

  if (c.legalHold === true) {
    // Statutory floor: only hard-delete past the retention window. Never early.
    return [
      { action: "hard_delete_legal", sql: `DELETE FROM ${c.table} WHERE ${ts} < now() - ${ret}` },
    ];
  }
  if (!usesSoft) {
    return [{ action: "ttl_delete", sql: `DELETE FROM ${c.table} WHERE ${ts} < now() - ${ret}` }];
  }
  return [
    {
      action: "soft_delete",
      sql: `UPDATE ${c.table} SET ${soft} = now() WHERE ${soft} IS NULL AND ${ts} < now() - ${ret}`,
    },
    {
      action: "hard_delete",
      sql: `DELETE FROM ${c.table} WHERE ${soft} IS NOT NULL AND ${soft} < now() - ${grace}`,
    },
  ];
}

export async function run(trigger = "cron"): Promise<{ ok: number; failed: number }> {
  let ok = 0;
  let failed = 0;
  const failures: string[] = [];

  for (const c of CLASSES) {
    for (const step of buildSql(c)) {
      try {
        const rows = await execPurge(step.sql);
        await logRun({ dataClass: c.id, table: c.table, action: step.action, rows, trigger, status: "ok" });
        ok++;
      } catch (err) {
        const detail = err instanceof Error ? err.message : String(err);
        // Log the failure (so retries are visible), then remember it. Do NOT
        // abort the loop — other classes must still be swept this run.
        await logRun({
          dataClass: c.id,
          table: c.table,
          action: step.action,
          rows: 0,
          trigger,
          status: "error",
          errorDetail: detail,
        }).catch(() => {/* logging best-effort; never mask the original failure */});
        failed++;
        failures.push(`${c.id}/${step.action}: ${detail}`);
      }
    }
  }

  // fail-safe: surface failures to the scheduler so it retries next tick.
  if (failed > 0) {
    throw new Error(`purge-job: ${failed} step(s) failed, ${ok} ok. Details: ${failures.join("; ")}`);
  }
  return { ok, failed };
}

// Supabase Edge entrypoint (Deno). Comment out if running under Node cron.
// Deno.serve(async () => {
//   const result = await run("cron");
//   return new Response(JSON.stringify(result), { headers: { "content-type": "application/json" } });
// });
