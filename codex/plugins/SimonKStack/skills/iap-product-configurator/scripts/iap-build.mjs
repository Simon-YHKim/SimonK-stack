#!/usr/bin/env node
// iap-build.mjs — Deterministic IAP product/price manifest builder + validator.
//
// Reads a product manifest (JSON, schema in templates/products.schema.json) and:
//   1. validates product IDs, subscription-group integrity, and upgrade paths
//   2. expands a base price (in a base currency) into per-country prices using
//      the nearest App Store / Play "price point" for each currency
//   3. emits a normalized plan: App Store Connect rows, Play Console rows, and a
//      human review table — all to stdout as JSON (use --table for a text table)
//
// This is PURE LOGIC, no network, no SDK. Same input always yields same output.
//
// Usage:
//   node iap-build.mjs <manifest.json>            # validate + emit JSON plan
//   node iap-build.mjs <manifest.json> --table    # emit a review table to stderr too
//   node iap-build.mjs <manifest.json> --check    # validate only, exit 0/1
//
// Exit codes:
//   0  valid (and plan emitted)
//   1  validation error(s) — printed to stderr
//   2  usage / file error

import { readFileSync } from 'node:fs';

// ---------------------------------------------------------------------------
// Price points. Apple/Google publish fixed "tiers" per currency; you cannot
// charge an arbitrary amount. These are representative anchor ladders used to
// SNAP a converted amount to the nearest legal point. Refresh from the store
// console when tiers change — see SKILL.md "가격 포인트 갱신".
// Values are the actual charged amount in each currency's minor-unit-free form
// (KRW/JPY have no decimals; USD/EUR/GBP shown as major units).
// ---------------------------------------------------------------------------
const PRICE_POINTS = {
  USD: [0.99, 1.99, 2.99, 3.99, 4.99, 5.99, 6.99, 7.99, 8.99, 9.99, 10.99, 11.99, 12.99, 14.99, 19.99, 24.99, 29.99, 39.99, 49.99, 59.99, 79.99, 99.99],
  EUR: [0.99, 1.99, 2.99, 3.99, 4.99, 5.99, 6.99, 7.99, 8.99, 9.99, 10.99, 11.99, 12.99, 14.99, 19.99, 24.99, 29.99, 39.99, 49.99, 59.99, 79.99, 99.99],
  GBP: [0.99, 1.99, 2.99, 3.99, 4.99, 5.99, 6.99, 7.99, 8.49, 9.99, 10.99, 11.99, 12.99, 14.99, 18.99, 22.99, 28.99, 38.99, 47.99, 57.99, 76.99, 96.99],
  JPY: [160, 250, 400, 500, 650, 800, 900, 1000, 1200, 1500, 1800, 2000, 2500, 3000, 4000, 5000, 6000, 8000, 10000, 12000, 16000, 20000],
  KRW: [1200, 2500, 3900, 4900, 5900, 6900, 7900, 8900, 9900, 12000, 14000, 15000, 19000, 24000, 29000, 39000, 49000, 59000, 79000, 99000, 119000, 149000],
};

// Indicative FX vs USD. Deterministic, intentionally static — store pricing is
// NOT live-FX; you set it and revisit quarterly. Override via manifest.fx if set.
const DEFAULT_FX = { USD: 1, EUR: 0.92, GBP: 0.79, JPY: 157, KRW: 1370 };

const ZERO_DECIMAL = new Set(['KRW', 'JPY']);

function fmtMoney(cur, amount) {
  if (ZERO_DECIMAL.has(cur)) return `${cur} ${Math.round(amount).toLocaleString('en-US')}`;
  return `${cur} ${amount.toFixed(2)}`;
}

// Snap a raw converted amount to the nearest available price point for a currency.
function snapToPoint(cur, raw) {
  const points = PRICE_POINTS[cur];
  if (!points) return { amount: raw, snapped: false, note: `no price-point ladder for ${cur}` };
  let best = points[0];
  let bestDiff = Math.abs(points[0] - raw);
  for (const p of points) {
    const d = Math.abs(p - raw);
    if (d < bestDiff) { best = p; bestDiff = d; }
  }
  return { amount: best, snapped: true };
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------
const ID_RE = /^[a-z0-9]+([._][a-z0-9]+)*$/; // reverse-dns-ish, lowercase, no leading/trailing sep
const TYPES = new Set(['consumable', 'non_consumable', 'auto_renewable', 'non_renewing']);
const PERIODS = new Set(['P1W', 'P1M', 'P2M', 'P3M', 'P6M', 'P1Y']);

function validate(manifest) {
  const errs = [];
  const warns = [];

  if (!manifest || typeof manifest !== 'object') {
    errs.push('manifest root must be an object');
    return { errs, warns };
  }
  const baseCur = manifest.baseCurrency || 'USD';
  if (!PRICE_POINTS[baseCur]) errs.push(`baseCurrency "${baseCur}" has no price-point ladder`);

  const targets = manifest.targetCurrencies || Object.keys(PRICE_POINTS);
  for (const c of targets) if (!PRICE_POINTS[c]) warns.push(`targetCurrency "${c}" has no price-point ladder — will pass through raw`);

  const products = Array.isArray(manifest.products) ? manifest.products : null;
  if (!products) { errs.push('products[] missing or not an array'); return { errs, warns }; }

  const seenIds = new Set();
  const groups = {}; // groupId -> [products]

  for (let i = 0; i < products.length; i++) {
    const p = products[i];
    const where = `products[${i}]${p && p.id ? ` (${p.id})` : ''}`;
    if (!p || typeof p !== 'object') { errs.push(`${where}: not an object`); continue; }

    if (!p.id) errs.push(`${where}: missing id`);
    else {
      if (!ID_RE.test(p.id)) errs.push(`${where}: id "${p.id}" not lowercase reverse-dns (a-z0-9, "." or "_" separators)`);
      if (p.id.length > 100) errs.push(`${where}: id exceeds 100 chars (Play limit)`);
      if (seenIds.has(p.id)) errs.push(`${where}: duplicate id "${p.id}" — product IDs are permanent + global, never reuse`);
      seenIds.add(p.id);
    }

    if (!TYPES.has(p.type)) errs.push(`${where}: type must be one of ${[...TYPES].join(', ')}`);

    if (typeof p.basePrice !== 'number' || p.basePrice <= 0) errs.push(`${where}: basePrice must be a positive number (in baseCurrency)`);

    if (p.type === 'auto_renewable') {
      if (!p.group) errs.push(`${where}: auto_renewable requires a group (subscription group)`);
      else { (groups[p.group] ||= []).push(p); }
      if (!PERIODS.has(p.period)) errs.push(`${where}: auto_renewable requires period one of ${[...PERIODS].join(', ')}`);
      if (p.rank != null && (!Number.isInteger(p.rank) || p.rank < 1)) errs.push(`${where}: rank must be a positive integer (1 = highest tier)`);
    }

    if (p.trial && !PERIODS.has(p.trial)) warns.push(`${where}: trial "${p.trial}" not a standard period (P1W/P1M/...) — verify the store offers it`);
    if (!p.refName) warns.push(`${where}: no refName (internal reference name) — required by App Store Connect`);
  }

  // Subscription-group integrity: ranks must be unique within a group.
  for (const [gid, members] of Object.entries(groups)) {
    const ranked = members.filter((m) => m.rank != null);
    const ranks = ranked.map((m) => m.rank);
    if (new Set(ranks).size !== ranks.length) errs.push(`group "${gid}": duplicate ranks — each tier needs a unique rank (controls upgrade vs downgrade)`);
    if (ranked.length && ranked.length !== members.length) warns.push(`group "${gid}": some members have no rank — App Store needs a rank on every level to order upgrade paths`);
  }

  // Upgrade-path sanity: an upgrade must point to a higher-tier (lower rank number) member in the SAME group.
  for (let i = 0; i < products.length; i++) {
    const p = products[i];
    if (!p || !Array.isArray(p.upgradesTo)) continue;
    for (const targetId of p.upgradesTo) {
      const t = products.find((q) => q && q.id === targetId);
      if (!t) { errs.push(`products[${i}] (${p.id}): upgradesTo "${targetId}" not found`); continue; }
      if (t.group !== p.group) errs.push(`${p.id}: upgradesTo "${targetId}" is in a different subscription group — cross-group changes are NOT upgrades (user resubscribes)`);
      if (p.rank != null && t.rank != null && !(t.rank < p.rank)) errs.push(`${p.id}: upgradesTo "${targetId}" does not have a higher tier (rank ${t.rank} should be < ${p.rank})`);
    }
  }

  return { errs, warns, groups };
}

// ---------------------------------------------------------------------------
// Build the localized plan
// ---------------------------------------------------------------------------
function buildPlan(manifest) {
  const baseCur = manifest.baseCurrency || 'USD';
  const targets = manifest.targetCurrencies || Object.keys(PRICE_POINTS);
  const fx = { ...DEFAULT_FX, ...(manifest.fx || {}) };

  const rows = [];
  for (const p of manifest.products) {
    const baseInUsd = p.basePrice / (fx[baseCur] ?? 1);
    const prices = {};
    for (const cur of targets) {
      const raw = baseInUsd * (fx[cur] ?? 1);
      const snapped = snapToPoint(cur, raw);
      prices[cur] = { charged: snapped.amount, display: fmtMoney(cur, snapped.amount), rawConverted: Number(raw.toFixed(4)), snapped: snapped.snapped };
    }
    rows.push({
      id: p.id,
      type: p.type,
      group: p.group ?? null,
      period: p.period ?? null,
      rank: p.rank ?? null,
      trial: p.trial ?? null,
      refName: p.refName ?? p.id,
      basePrice: { currency: baseCur, amount: p.basePrice, display: fmtMoney(baseCur, p.basePrice) },
      prices,
    });
  }
  return { baseCurrency: baseCur, targetCurrencies: targets, fx, products: rows };
}

function printTable(plan) {
  const cols = plan.targetCurrencies;
  const head = ['product id', 'type', ...cols];
  const lines = [head.join(' | ')];
  lines.push(head.map((h) => '-'.repeat(Math.max(3, h.length))).join('-|-'));
  for (const r of plan.products) {
    const cells = [r.id, r.type, ...cols.map((c) => r.prices[c].display)];
    lines.push(cells.join(' | '));
  }
  process.stderr.write('\n' + lines.join('\n') + '\n\n');
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------
function main(argv) {
  const args = argv.slice(2);
  const file = args.find((a) => !a.startsWith('--'));
  const wantTable = args.includes('--table');
  const checkOnly = args.includes('--check');

  if (!file) { process.stderr.write('usage: node iap-build.mjs <manifest.json> [--table] [--check]\n'); return 2; }

  let manifest;
  try { manifest = JSON.parse(readFileSync(file, 'utf8')); }
  catch (e) { process.stderr.write(`[error] cannot read/parse ${file}: ${e.message}\n`); return 2; }

  const { errs, warns } = validate(manifest);
  for (const w of warns) process.stderr.write(`[warn] ${w}\n`);
  if (errs.length) {
    for (const e of errs) process.stderr.write(`[FAIL] ${e}\n`);
    process.stderr.write(`\n${errs.length} error(s). Fix the manifest before configuring the stores.\n`);
    return 1;
  }
  process.stderr.write(`[ok] manifest valid — ${manifest.products.length} product(s)\n`);

  if (checkOnly) return 0;

  const plan = buildPlan(manifest);
  if (wantTable) printTable(plan);
  process.stdout.write(JSON.stringify(plan, null, 2) + '\n');
  return 0;
}

process.exit(main(process.argv));
