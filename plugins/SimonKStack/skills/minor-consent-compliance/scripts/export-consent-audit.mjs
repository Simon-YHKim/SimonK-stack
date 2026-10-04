#!/usr/bin/env node
/**
 * export-consent-audit.mjs — deterministic COPPA / PIPA §22-2 audit export.
 *
 * Reads minor_consent_ledger rows (JSON array) and produces a per-subject
 * current-state summary plus non-compliance flags. Pure function of the input:
 * same rows in -> same report out. No network, no randomness, no clock reads
 * for decisions (the only Date use is the report's generatedAt stamp, which can
 * be pinned with --now for reproducible diffs).
 *
 * Usage:
 *   node export-consent-audit.mjs --in ledger.json [--format json|md] [--policy 2026-06-01] [--now ISO]
 *   cat ledger.json | node export-consent-audit.mjs --format md
 *
 * Input row shape (snake_case from SQL or camelCase from the TS module — both accepted):
 *   { user_id, policy_version, age_tier, region, state, actor,
 *     verification_step, verification_method, sensitivity, scope, created_at }
 *
 * Exit codes:
 *   0 — report produced, no non-compliance flags
 *   3 — report produced, but one or more flags were raised
 *   1 — bad input (not a JSON array / unreadable)
 *   2 — bad arguments
 */

import { readFileSync } from 'node:fs';

const FLAGS = {
  MINOR_GRANTED_WITHOUT_GUARDIAN: 'under_14 account is granted without a verified guardian actor',
  WEAK_VERIFICATION_FOR_SENSITIVE: 'sensitive scope granted on step-1 (email) only',
  STALE_POLICY_VERSION: 'granted under a policy version older than the current one (needs re-consent)',
  EXPIRED_STILL_ACTIVE: 'latest state is expired/revoked but an earlier granted row could be mistaken for active',
  MUTATION_DETECTED: 'two rows share the exact same timestamp for one subject (possible mutation/duplication of an append-only ledger)',
};

const ACTIVE_STATE = 'granted';

function parseArgs(argv) {
  const a = { in: null, format: 'json', policy: null, now: null };
  for (let i = 0; i < argv.length; i++) {
    const t = argv[i];
    if (t === '--in') a.in = argv[++i];
    else if (t === '--format') a.format = argv[++i];
    else if (t === '--policy') a.policy = argv[++i];
    else if (t === '--now') a.now = argv[++i];
    else if (t === '--help' || t === '-h') a.help = true;
    else return { error: `unknown argument: ${t}` };
  }
  if (a.format !== 'json' && a.format !== 'md') return { error: `--format must be json|md, got ${a.format}` };
  return a;
}

/** Accept both snake_case (SQL) and camelCase (TS) keys. */
function normalize(r) {
  return {
    userId: r.user_id ?? r.userId,
    policyVersion: r.policy_version ?? r.policyVersion,
    ageTier: r.age_tier ?? r.ageTier,
    region: r.region,
    state: r.state,
    actor: r.actor,
    verificationStep: Number(r.verification_step ?? r.verificationStep ?? 0),
    verificationMethod: r.verification_method ?? r.verificationMethod ?? null,
    sensitivity: r.sensitivity ?? 'basic',
    scope: r.scope ?? {},
    createdAt: r.created_at ?? r.createdAt,
  };
}

/** Compare policy version strings. Date-like 'YYYY-MM-DD' sorts lexicographically; falls back to string compare. */
function policyOlder(a, b) {
  if (!a || !b) return false;
  return String(a) < String(b);
}

/** Deterministic ordering: by createdAt, ties broken by a stable key so output never depends on input order. */
function chronological(rows) {
  return [...rows].sort((x, y) => {
    const t = String(x.createdAt).localeCompare(String(y.createdAt));
    if (t !== 0) return t;
    return JSON.stringify(x).localeCompare(JSON.stringify(y));
  });
}

function auditSubject(userId, rawRows, currentPolicy) {
  const rows = chronological(rawRows);
  const latest = rows[rows.length - 1];
  const flags = [];

  // MUTATION_DETECTED — order-INDEPENDENT signal. Input row order is arbitrary
  // (a SQL query without ORDER BY may return rows in any order), so we must NOT
  // infer mutation from the as-supplied sequence. The real tell on an append-only
  // ledger is two rows claiming the EXACT same instant for one subject, or two
  // distinct rows that are byte-identical except their PK — i.e. a duplicated /
  // back-dated entry. Both are derived from the data, not its ordering.
  const tsCounts = new Map();
  for (const r of rawRows) {
    const ts = String(r.createdAt);
    tsCounts.set(ts, (tsCounts.get(ts) ?? 0) + 1);
  }
  let mutation = false;
  for (const [, n] of tsCounts) if (n > 1) mutation = true; // duplicate timestamp for this subject
  if (mutation) flags.push('MUTATION_DETECTED');

  const active = latest.state === ACTIVE_STATE;

  // Find the row that granted (latest granted row) for evidence checks.
  const grantedRows = rows.filter((r) => r.state === ACTIVE_STATE);
  const latestGranted = grantedRows[grantedRows.length - 1];

  if (active && latestGranted) {
    if (latestGranted.ageTier === 'under_14') {
      const guardianVerified = rows.some(
        (r) => r.actor === 'guardian' && r.verificationStep >= 1 && r.verificationMethod,
      );
      if (!(guardianVerified && latestGranted.actor === 'guardian')) {
        flags.push('MINOR_GRANTED_WITHOUT_GUARDIAN');
      }
    }
    if (latestGranted.sensitivity === 'sensitive' && latestGranted.verificationStep < 2) {
      flags.push('WEAK_VERIFICATION_FOR_SENSITIVE');
    }
    if (currentPolicy && policyOlder(latestGranted.policyVersion, currentPolicy)) {
      flags.push('STALE_POLICY_VERSION');
    }
  }

  // EXPIRED_STILL_ACTIVE: there was a grant, but the latest state revoked/expired
  // while a stale consumer might still treat an earlier grant as live.
  if (!active && grantedRows.length > 0 && (latest.state === 'revoked' || latest.state === 'expired')) {
    flags.push('EXPIRED_STILL_ACTIVE');
  }

  return {
    userId,
    currentState: latest.state,
    accountActive: active,
    ageTier: latest.ageTier,
    region: latest.region,
    policyVersion: latest.policyVersion,
    verificationStep: latestGranted ? latestGranted.verificationStep : latest.verificationStep,
    verificationMethod: latestGranted ? latestGranted.verificationMethod : latest.verificationMethod,
    sensitivity: latest.sensitivity,
    rowCount: rawRows.length,
    flags: [...new Set(flags)].sort(),
  };
}

function buildReport(rawRows, currentPolicy, nowIso) {
  const norm = rawRows.map(normalize).filter((r) => r.userId && r.state && r.createdAt);
  const bySubject = new Map();
  for (const r of norm) {
    if (!bySubject.has(r.userId)) bySubject.set(r.userId, []);
    bySubject.get(r.userId).push(r);
  }
  const subjects = [...bySubject.keys()].sort().map((uid) => auditSubject(uid, bySubject.get(uid), currentPolicy));

  const flagCounts = {};
  for (const s of subjects) for (const f of s.flags) flagCounts[f] = (flagCounts[f] ?? 0) + 1;

  return {
    generatedAt: nowIso,
    currentPolicyVersion: currentPolicy,
    summary: {
      subjects: subjects.length,
      active: subjects.filter((s) => s.accountActive).length,
      under14: subjects.filter((s) => s.ageTier === 'under_14').length,
      withFlags: subjects.filter((s) => s.flags.length > 0).length,
      flagCounts,
    },
    flagLegend: FLAGS,
    subjects,
  };
}

function toMarkdown(rep) {
  const L = [];
  L.push('# Minor / Guardian Consent Audit (COPPA / PIPA §22-2)');
  L.push('');
  L.push(`- Generated: ${rep.generatedAt}`);
  L.push(`- Current policy version: ${rep.currentPolicyVersion ?? '(not supplied)'}`);
  L.push(`- Subjects: ${rep.summary.subjects} | Active: ${rep.summary.active} | Under-14: ${rep.summary.under14} | With flags: ${rep.summary.withFlags}`);
  L.push('');
  L.push('## Non-compliance flags');
  const fc = rep.summary.flagCounts;
  if (Object.keys(fc).length === 0) {
    L.push('');
    L.push('None. All subjects pass.');
  } else {
    L.push('');
    L.push('| Flag | Count | Meaning |');
    L.push('|---|---|---|');
    for (const k of Object.keys(fc).sort()) L.push(`| ${k} | ${fc[k]} | ${rep.flagLegend[k]} |`);
  }
  L.push('');
  L.push('## Subjects');
  L.push('');
  L.push('| user_id | state | active | tier | region | policy | step | sensitivity | flags |');
  L.push('|---|---|---|---|---|---|---|---|---|');
  for (const s of rep.subjects) {
    L.push(
      `| ${s.userId} | ${s.currentState} | ${s.accountActive ? 'yes' : 'no'} | ${s.ageTier} | ${s.region} | ${s.policyVersion} | ${s.verificationStep} | ${s.sensitivity} | ${s.flags.join(', ') || '-'} |`,
    );
  }
  L.push('');
  return L.join('\n');
}

function readInput(path) {
  const raw = path ? readFileSync(path, 'utf8') : readFileSync(0, 'utf8');
  const data = JSON.parse(raw);
  if (!Array.isArray(data)) throw new Error('input must be a JSON array of ledger rows');
  return data;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.error) {
    process.stderr.write(`[consent-audit] ${args.error}\n`);
    process.exit(2);
  }
  if (args.help) {
    process.stdout.write('Usage: node export-consent-audit.mjs --in ledger.json [--format json|md] [--policy VER] [--now ISO]\n');
    process.exit(0);
  }

  let rows;
  try {
    rows = readInput(args.in);
  } catch (e) {
    process.stderr.write(`[consent-audit] bad input: ${e.message}\n`);
    process.exit(1);
  }

  const nowIso = args.now ?? new Date().toISOString();
  const report = buildReport(rows, args.policy, nowIso);
  const out = args.format === 'md' ? toMarkdown(report) : JSON.stringify(report, null, 2);
  process.stdout.write(out + '\n');

  process.exit(report.summary.withFlags > 0 ? 3 : 0);
}

main();
