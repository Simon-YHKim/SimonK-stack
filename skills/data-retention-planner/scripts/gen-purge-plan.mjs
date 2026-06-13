#!/usr/bin/env node
// gen-purge-plan.mjs — Deterministic purge-plan generator.
//
// Reads a retention-classes JSON (single source of truth) and emits, per class:
//   * a cron expression sized to the class retention window,
//   * a soft-delete SQL skeleton (purpose-end / expiry → set deleted_at),
//   * a hard-delete SQL skeleton (after grace; legalHold forces an expiry clause),
//   * a purge-audit-log INSERT.
//
// Same input → same output. No network, no randomness, no clock reads in the
// emitted SQL (uses now() inside SQL so the DB is the time authority).
//
// Usage:
//   node gen-purge-plan.mjs <classes.json> [--out <dir>] [--dialect postgres|mysql]
//
// Without --out, prints the full plan to stdout. With --out, writes:
//   <dir>/purge-plan.sql   (all classes, ordered)
//   <dir>/cron-schedule.txt (one cron line per class)
//   <dir>/purge-plan.json  (machine-readable plan)
//
// Exit codes:
//   0 — plan generated
//   1 — bad args / file not found
//   2 — schema validation failed (a class is unsafe to purge)

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve, join } from "node:path";

// ---------------------------------------------------------------------------
// Arg parsing (no deps).
// ---------------------------------------------------------------------------
const argv = process.argv.slice(2);
if (argv.length === 0 || argv.includes("-h") || argv.includes("--help")) {
  console.error(
    "Usage: node gen-purge-plan.mjs <classes.json> [--out <dir>] [--dialect postgres|mysql]"
  );
  process.exit(1);
}

const positional = argv.filter((a) => !a.startsWith("--") && argv[argv.indexOf(a) - 1] !== "--out" && argv[argv.indexOf(a) - 1] !== "--dialect");
const classesPath = positional[0];
const outIdx = argv.indexOf("--out");
const outDir = outIdx >= 0 ? argv[outIdx + 1] : null;
const dialectIdx = argv.indexOf("--dialect");
const dialect = dialectIdx >= 0 ? argv[dialectIdx + 1] : "postgres";

if (!classesPath || !existsSync(classesPath)) {
  console.error(`[gen-purge-plan] ERROR: classes file not found: ${classesPath ?? "(none)"}`);
  process.exit(1);
}
if (!["postgres", "mysql"].includes(dialect)) {
  console.error(`[gen-purge-plan] ERROR: unsupported dialect '${dialect}' (postgres|mysql)`);
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Load + validate classes.
// ---------------------------------------------------------------------------
let parsed;
try {
  parsed = JSON.parse(readFileSync(resolve(classesPath), "utf8"));
} catch (e) {
  console.error(`[gen-purge-plan] ERROR: invalid JSON in ${classesPath}: ${e.message}`);
  process.exit(1);
}
const classes = Array.isArray(parsed) ? parsed : parsed.classes;
if (!Array.isArray(classes)) {
  console.error("[gen-purge-plan] ERROR: expected an array of classes or { classes: [...] }");
  process.exit(1);
}

const REQUIRED = ["id", "table", "retentionDays", "graceDays", "timestampColumn"];
const errors = [];
for (const [i, c] of classes.entries()) {
  for (const k of REQUIRED) {
    if (c[k] === undefined || c[k] === null) errors.push(`class[${i}] (${c.id ?? "?"}): missing '${k}'`);
  }
  if (typeof c.retentionDays === "number" && c.retentionDays < 0) errors.push(`class[${i}] (${c.id}): retentionDays must be >= 0`);
  if (typeof c.graceDays === "number" && c.graceDays < 0) errors.push(`class[${i}] (${c.id}): graceDays must be >= 0`);
  // Safety rule: a legalHold class with no retention floor would generate an
  // unconditional delete — refuse. legalHold REQUIRES retentionDays > 0.
  if (c.legalHold === true && !(c.retentionDays > 0)) {
    errors.push(`class[${i}] (${c.id}): legalHold=true requires retentionDays > 0 (no unconditional delete)`);
  }
}
if (errors.length) {
  console.error("[gen-purge-plan] SCHEMA VALIDATION FAILED:");
  for (const e of errors) console.error("  - " + e);
  process.exit(2);
}

// ---------------------------------------------------------------------------
// Deterministic cron sizing: derive a sweep cadence from the retention window.
// Shorter retention → sweep more often. Fixed thresholds = deterministic.
// All times in UTC; pick 03:00 for daily/weekly to dodge peak load.
// ---------------------------------------------------------------------------
function cronFor(retentionDays) {
  if (retentionDays <= 1) return { expr: "*/15 * * * *", human: "every 15 minutes" };
  if (retentionDays <= 7) return { expr: "0 * * * *", human: "hourly" };
  if (retentionDays <= 90) return { expr: "0 3 * * *", human: "daily at 03:00 UTC" };
  return { expr: "0 3 * * 0", human: "weekly Sunday 03:00 UTC" };
}

// SQL interval literal per dialect, deterministic from integer days.
function interval(days) {
  if (dialect === "mysql") return `INTERVAL ${days} DAY`;
  return `INTERVAL '${days} days'`; // postgres
}
function nowExpr() {
  return dialect === "mysql" ? "UTC_TIMESTAMP()" : "now()";
}

// ---------------------------------------------------------------------------
// Emit SQL per class.
// ---------------------------------------------------------------------------
function emitClass(c) {
  const ts = c.timestampColumn;
  const softCol = c.softDeleteColumn || "deleted_at";
  const cron = cronFor(c.retentionDays);
  const retInt = interval(c.retentionDays);
  const graceInt = interval(c.graceDays);
  const now = nowExpr();
  const usesSoft = c.softDelete !== false; // default true

  const lines = [];
  lines.push(`-- ===========================================================================`);
  lines.push(`-- CLASS: ${c.id}   table=${c.table}`);
  lines.push(`-- basis: ${c.basis ?? "(unspecified)"}   trigger: ${c.trigger ?? "(time-based)"}`);
  lines.push(`-- retention: ${c.retentionDays}d   grace: ${c.graceDays}d   legalHold: ${c.legalHold === true}`);
  lines.push(`-- sweep: ${cron.human}  (cron: ${cron.expr})`);
  lines.push(`-- ===========================================================================`);

  if (c.legalHold === true) {
    // Legal-retention class: never soft-delete early; hard-delete ONLY after the
    // statutory floor. Always carries the retention WHERE clause — no unconditional delete.
    lines.push(`-- legalHold: statutory floor enforced. Hard-delete only past the retention window.`);
    lines.push(`WITH purged AS (`);
    lines.push(`  DELETE FROM ${c.table}`);
    lines.push(`  WHERE ${ts} < ${now} - ${retInt}`);
    lines.push(`  RETURNING 1`);
    lines.push(`)`);
    lines.push(`INSERT INTO purge_audit_log (data_class, table_name, action, rows_affected, trigger_source)`);
    lines.push(`SELECT '${c.id}', '${c.table}', 'hard_delete_legal', count(*), 'cron'`);
    lines.push(`FROM purged;`);
    lines.push("");
    return { sql: lines.join("\n"), cron, id: c.id };
  }

  if (usesSoft) {
    // Step 1: soft-delete once retention window passes (purpose-end mark).
    lines.push(`-- step 1: soft-delete rows past retention window (purpose end).`);
    lines.push(`WITH softened AS (`);
    lines.push(`  UPDATE ${c.table}`);
    lines.push(`  SET ${softCol} = ${now}`);
    lines.push(`  WHERE ${softCol} IS NULL`);
    lines.push(`    AND ${ts} < ${now} - ${retInt}`);
    lines.push(`  RETURNING 1`);
    lines.push(`)`);
    lines.push(`INSERT INTO purge_audit_log (data_class, table_name, action, rows_affected, trigger_source)`);
    lines.push(`SELECT '${c.id}', '${c.table}', 'soft_delete', count(*), 'cron'`);
    lines.push(`FROM softened;`);
    lines.push("");
    // Step 2: hard-delete after grace from soft-delete mark.
    lines.push(`-- step 2: hard-delete rows whose grace period has elapsed since soft-delete.`);
    lines.push(`WITH purged AS (`);
    lines.push(`  DELETE FROM ${c.table}`);
    lines.push(`  WHERE ${softCol} IS NOT NULL`);
    lines.push(`    AND ${softCol} < ${now} - ${graceInt}`);
    lines.push(`  RETURNING 1`);
    lines.push(`)`);
    lines.push(`INSERT INTO purge_audit_log (data_class, table_name, action, rows_affected, trigger_source)`);
    lines.push(`SELECT '${c.id}', '${c.table}', 'hard_delete', count(*), 'cron'`);
    lines.push(`FROM purged;`);
  } else {
    // No soft-delete column (e.g. transient: sessions, OTP). Single TTL delete.
    lines.push(`-- single-step TTL delete (transient class, no soft-delete column).`);
    lines.push(`WITH purged AS (`);
    lines.push(`  DELETE FROM ${c.table}`);
    lines.push(`  WHERE ${ts} < ${now} - ${retInt}`);
    lines.push(`  RETURNING 1`);
    lines.push(`)`);
    lines.push(`INSERT INTO purge_audit_log (data_class, table_name, action, rows_affected, trigger_source)`);
    lines.push(`SELECT '${c.id}', '${c.table}', 'ttl_delete', count(*), 'cron'`);
    lines.push(`FROM purged;`);
  }
  lines.push("");
  return { sql: lines.join("\n"), cron, id: c.id };
}

// Stable ordering: by id so output is deterministic regardless of input order.
const ordered = [...classes].sort((a, b) => String(a.id).localeCompare(String(b.id)));
const emitted = ordered.map(emitClass);

const sqlDoc =
  `-- purge-plan.sql — generated by gen-purge-plan.mjs (dialect=${dialect})\n` +
  `-- Source: ${classesPath}\n` +
  `-- Run each block on its class cadence (see cron-schedule.txt). Wrap in a tx per class.\n` +
  `-- Requires purge_audit_log (see templates/purge-audit-log.sql).\n\n` +
  emitted.map((e) => e.sql).join("\n");

const cronDoc =
  `# cron-schedule.txt — one sweep line per data class\n` +
  `# Wire each into pg_cron / GitHub Actions / Cloud Scheduler. Times are UTC.\n\n` +
  emitted.map((e) => `${e.cron.expr}\t${e.id}\t# ${e.cron.human}`).join("\n") +
  "\n";

const jsonDoc = JSON.stringify(
  emitted.map((e) => ({ id: e.id, cron: e.cron.expr, cadence: e.cron.human })),
  null,
  2
);

if (outDir) {
  mkdirSync(outDir, { recursive: true });
  writeFileSync(join(outDir, "purge-plan.sql"), sqlDoc);
  writeFileSync(join(outDir, "cron-schedule.txt"), cronDoc);
  writeFileSync(join(outDir, "purge-plan.json"), jsonDoc);
  console.error(`[gen-purge-plan] wrote 3 files to ${outDir} (${emitted.length} classes)`);
} else {
  process.stdout.write(sqlDoc + "\n\n");
  process.stdout.write(cronDoc + "\n");
}
process.exit(0);
