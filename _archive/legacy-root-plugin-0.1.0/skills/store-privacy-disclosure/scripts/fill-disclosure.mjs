#!/usr/bin/env node
// fill-disclosure.mjs — Convert a data-flow-mapper inventory (data-flow.md)
// into store privacy disclosures: Apple App Privacy Nutrition Label,
// Google Play Data Safety questionnaire, and an ATT-required verdict.
//
// This is a deterministic TRANSFORM of facts already written in the
// inventory — not an automatic classification of source code. Mapping
// that is ambiguous is emitted as [검토필요] for a human to resolve.
//
// Usage:
//   node fill-disclosure.mjs <path/to/data-flow.md> [--out disclosure.md]
//
// With --out, writes the disclosure markdown to the given file.
// Without --out, prints to stdout.
//
// Exit codes:
//   0 — completed
//   1 — input file missing / unreadable
//   2 — no parseable inventory table found

import { readFileSync, writeFileSync } from 'node:fs';

const args = process.argv.slice(2);
if (args.length === 0 || args.includes('-h') || args.includes('--help')) {
  console.error('Usage: node fill-disclosure.mjs <data-flow.md> [--out disclosure.md]');
  process.exit(args.length === 0 ? 1 : 0);
}

const outIdx = args.indexOf('--out');
const outPath = outIdx >= 0 ? args[outIdx + 1] : null;
const inputPath = args.find((a, i) => a !== '--out' && (outIdx < 0 || i !== outIdx + 1) && !a.startsWith('--'));

if (!inputPath) {
  console.error('[disclosure] ERROR: no input data-flow.md path given');
  process.exit(1);
}

let raw;
try {
  raw = readFileSync(inputPath, 'utf8');
} catch (e) {
  console.error(`[disclosure] ERROR: cannot read '${inputPath}': ${e.message}`);
  process.exit(1);
}

// --- Markdown table parsing -------------------------------------------------

/** Split a markdown table row into trimmed cells (drops leading/trailing pipe). */
function splitRow(line) {
  let s = line.trim();
  if (s.startsWith('|')) s = s.slice(1);
  if (s.endsWith('|')) s = s.slice(0, -1);
  return s.split('|').map((c) => c.trim());
}

/** True if a line is a markdown table separator row (|---|---|). */
function isSeparator(line) {
  return /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$/.test(line);
}

/**
 * Find the first markdown table whose header cells contain ALL of `mustHave`
 * (case-insensitive substring match). Returns { headers, rows } or null.
 * Stops the table at the first non-table line.
 */
function findTable(text, mustHave) {
  const lines = text.split(/\r?\n/);
  for (let i = 0; i < lines.length - 1; i++) {
    if (!lines[i].includes('|')) continue;
    if (!isSeparator(lines[i + 1])) continue;
    const headers = splitRow(lines[i]);
    const hLower = headers.map((h) => h.toLowerCase());
    const ok = mustHave.every((m) => hLower.some((h) => h.includes(m.toLowerCase())));
    if (!ok) continue;
    const rows = [];
    for (let j = i + 2; j < lines.length; j++) {
      const ln = lines[j];
      if (!ln.includes('|')) break;
      if (isSeparator(ln)) continue;
      const cells = splitRow(ln);
      // skip blank/placeholder rows (all cells empty or angle-bracket templates)
      const meaningful = cells.some((c) => c && !/^<.*>$/.test(c) && c !== '...');
      if (!meaningful) continue;
      rows.push(cells);
    }
    return { headers, rows };
  }
  return null;
}

/** Index of the first header containing any of the given keywords. */
function colIndex(headers, keywords) {
  const lower = headers.map((h) => h.toLowerCase());
  for (let i = 0; i < lower.length; i++) {
    if (keywords.some((k) => lower[i].includes(k.toLowerCase()))) return i;
  }
  return -1;
}

// --- Classification tables --------------------------------------------------

// Each entry: regex on the (lowercased) data-type label → mapping.
// apple: { category, linked, tracking }  tracking 'auto' = depends on processor.
// play:  { type, purpose }
const RULES = [
  {
    re: /(이메일|e-?mail|이름|name|전화|phone|mobile|연락처\s*정보)/,
    apple: { category: 'Contact Info', linked: 'Linked', tracking: 'no' },
    play: { type: 'Personal info', purpose: 'Account management' },
  },
  {
    re: /(정밀\s*위치|precise[_\s]?location|gps)/,
    apple: { category: 'Location (Precise)', linked: 'Linked', tracking: 'auto' },
    play: { type: 'Location (Precise)', purpose: 'App functionality' },
  },
  {
    re: /(위치|location|geo|좌표|lat|lng)/,
    apple: { category: 'Location (Coarse)', linked: 'Linked', tracking: 'auto' },
    play: { type: 'Location (Approximate)', purpose: 'App functionality' },
  },
  {
    re: /(idfa|광고\s*id|advertis|aaid|gaid)/,
    apple: { category: 'Identifiers', linked: 'Linked', tracking: 'yes' },
    play: { type: 'Device or other IDs', purpose: 'Advertising or marketing' },
  },
  {
    re: /(device[_\s]?id|디바이스\s*id|기기\s*id|push\s*token|fcm|디바이스\s*토큰)/,
    apple: { category: 'Identifiers', linked: 'Linked', tracking: 'auto' },
    play: { type: 'Device or other IDs', purpose: 'App functionality' },
  },
  {
    re: /(크래시|crash|진단|diagnostic|성능|performance|로그|\blog\b)/,
    apple: { category: 'Diagnostics', linked: 'Not Linked', tracking: 'no' },
    play: { type: 'App info and performance', purpose: 'App functionality' },
  },
  {
    re: /(사용\s*이벤트|usage|이벤트|event|분석|analytics|행동|activity)/,
    apple: { category: 'Usage Data', linked: 'Linked', tracking: 'auto' },
    play: { type: 'App activity', purpose: 'Analytics' },
  },
  {
    re: /(결제|payment|card|카드|구매|purchase|청구|billing|iban)/,
    apple: { category: 'Purchases', linked: 'Linked', tracking: 'no' },
    play: { type: 'Financial info', purpose: 'App functionality' },
  },
  {
    re: /(건강|health|생체|biometric|fitness)/,
    apple: { category: 'Health & Fitness', linked: 'Linked', tracking: 'no' },
    play: { type: 'Health and fitness', purpose: 'App functionality' },
  },
  {
    re: /(사진|photo|image|avatar|영상|video|미디어|media)/,
    apple: { category: 'User Content', linked: 'Linked', tracking: 'no' },
    play: { type: 'Photos and videos', purpose: 'App functionality' },
  },
  {
    re: /(생년월일|birth|dob|나이|\bage\b|성별|gender|인구통계|demographic)/,
    apple: { category: 'Contact Info', linked: 'Linked', tracking: 'no' },
    play: { type: 'Personal info', purpose: 'App functionality' },
  },
  {
    re: /(주민|ssn|여권|passport)/,
    apple: { category: 'Sensitive Info', linked: 'Linked', tracking: 'no' },
    play: { type: 'Personal info', purpose: 'Account management' },
  },
];

function classify(dataType) {
  for (const rule of RULES) {
    if (rule.re.test(dataType.toLowerCase())) return rule;
  }
  return null;
}

// --- Parse inventory --------------------------------------------------------

// §1 inventory: needs a data-type column + purpose + processor.
const inv =
  findTable(raw, ['데이터 타입', '처리자']) ||
  findTable(raw, ['data type', 'processor']) ||
  findTable(raw, ['데이터 타입', '목적']);

if (!inv) {
  console.error('[disclosure] ERROR: no inventory table found in input.');
  console.error('  Expected a §1 table with columns like 데이터 타입 / 수집 목적 / 처리자.');
  console.error('  Run data-flow-mapper first to produce data-flow.md.');
  process.exit(2);
}

const cType = colIndex(inv.headers, ['데이터 타입', 'data type', '항목']);
const cPurpose = colIndex(inv.headers, ['목적', 'purpose']);
const cProc = colIndex(inv.headers, ['처리자', 'processor', '3rd', 'third']);
// Code-evidence column only. Must NOT match the legal-basis column ("법적 근거"),
// so we key on '코드'/'evidence' and accept bare '근거' only when it is not the
// legal-basis header.
let cEvidence = colIndex(inv.headers, ['코드 근거', '코드', 'evidence', 'source']);
if (cEvidence < 0) {
  const lower = inv.headers.map((h) => h.toLowerCase());
  cEvidence = lower.findIndex((h) => h.includes('근거') && !h.includes('법적') && !h.includes('legal'));
}

// §2 processor map (optional): used to decide "shared" + cross-border.
const procMap = findTable(raw, ['처리자', '국외']) || findTable(raw, ['processor', 'cross']);

// A processor cell counts as "third party share" when it names a real
// processor (not 'self'/'없음'/'내부'/blank/placeholder).
function isThirdParty(cell) {
  if (!cell) return false;
  const c = cell.toLowerCase();
  if (/^<.*>$/.test(cell) || c === '...' || c === '-') return false;
  if (/(없음|none|n\/a|self|내부|자체|own backend|first[- ]?party|일차)/.test(c)) return false;
  return true;
}

// Build rows.
const rows = inv.rows.map((cells) => {
  const dataType = cType >= 0 ? cells[cType] || '' : cells[0] || '';
  const purpose = cPurpose >= 0 ? cells[cPurpose] || '' : '';
  const processor = cProc >= 0 ? cells[cProc] || '' : '';
  const evidence = cEvidence >= 0 ? cells[cEvidence] || '' : '';
  const rule = classify(dataType);
  const shared = isThirdParty(processor);
  const crossBorder = /국외|cross|overseas|\bus\b|미국/i.test(processor) || /\[국외이전\]/.test(cells.join(' '));
  return { dataType, purpose, processor, evidence, rule, shared, crossBorder };
});

// --- Tracking verdict -------------------------------------------------------
// ATT/Tracking is required when an advertising identifier is collected OR
// any data is shared with an advertising/broker processor.
const AD_PROC = /(admob|adsense|meta|facebook|appsflyer|adjust|ad\s*sdk|광고|broker|브로커|criteo|applovin|unity ads|ironsource)/i;

let trackingRequired = false;
const trackingReasons = [];
for (const r of rows) {
  if (r.rule && r.rule.apple.tracking === 'yes') {
    trackingRequired = true;
    trackingReasons.push(`광고 식별자 수집: "${r.dataType}"`);
  }
  if (r.shared && AD_PROC.test(r.processor)) {
    trackingRequired = true;
    trackingReasons.push(`광고/브로커 처리자 공유: "${r.dataType}" → ${r.processor}`);
  }
}

// Resolve 'auto' tracking now that we know whether tracking is in play.
for (const r of rows) {
  if (!r.rule) continue;
  if (r.rule.apple.tracking === 'auto') {
    const adShare = r.shared && AD_PROC.test(r.processor);
    r.resolvedTracking = adShare ? 'Tracking' : 'Not Tracking';
  } else {
    r.resolvedTracking = r.rule.apple.tracking === 'yes' ? 'Tracking' : 'Not Tracking';
  }
}

// --- Mismatch / risk inheritance -------------------------------------------
// Carry over §3 declaration↔code risks verbatim if present, and flag any
// data type we could not map.
const risksSection = (() => {
  const m = raw.match(/##\s*3\.[^\n]*위험[\s\S]*?(?=\n##\s|\n#\s|$)/);
  return m ? m[0].trim() : null;
})();

const unmapped = rows.filter((r) => !r.rule).map((r) => r.dataType);

// --- Render -----------------------------------------------------------------

const esc = (s) => (s || '').replace(/\|/g, '\\|');
const today = new Date().toISOString().slice(0, 10);

const lines = [];
lines.push(`# 스토어 개인정보 공시 — 자동 채움`);
lines.push('');
lines.push(`> 입력: \`${inputPath}\` (data-flow-mapper 인벤토리)`);
lines.push(`> 생성일: ${today} · 생성기: fill-disclosure.mjs`);
lines.push(`> 모든 항목은 인벤토리의 코드 근거에서 파생. \`[검토필요]\`는 사람이 확정.`);
lines.push('');

lines.push(`## 1. Apple App Privacy Nutrition Label`);
lines.push('');
lines.push(`| 데이터 타입 | Apple 카테고리 | Linked to You | Used for Tracking | 코드 근거 |`);
lines.push(`|---|---|---|---|---|`);
for (const r of rows) {
  if (!r.rule) {
    lines.push(`| ${esc(r.dataType)} | \`[검토필요]\` | \`[검토필요]\` | \`[검토필요]\` | ${esc(r.evidence)} |`);
    continue;
  }
  lines.push(
    `| ${esc(r.dataType)} | ${r.rule.apple.category} | ${r.rule.apple.linked} | ${r.resolvedTracking} | ${esc(r.evidence)} |`,
  );
}
lines.push('');

lines.push(`## 2. Google Play Data Safety`);
lines.push('');
lines.push(`| 데이터 타입 | Play 유형 | 수집 | 공유 | 수집 목적 | 코드 근거 |`);
lines.push(`|---|---|---|---|---|---|`);
for (const r of rows) {
  if (!r.rule) {
    lines.push(`| ${esc(r.dataType)} | \`[검토필요]\` | 예 | \`[검토필요]\` | ${esc(r.purpose)} | ${esc(r.evidence)} |`);
    continue;
  }
  const shared = r.shared ? `예 (${esc(r.processor)})` : '아니오';
  lines.push(`| ${esc(r.dataType)} | ${r.rule.play.type} | 예 | ${shared} | ${esc(r.purpose) || r.rule.play.purpose} | ${esc(r.evidence)} |`);
}
lines.push('');
lines.push(`> 전송 중 암호화(in transit)·삭제 요청 제공은 코드(https·DSAR 흐름) 확인 후 사람이 \`예/아니오\`로 확정.`);
lines.push('');

lines.push(`## 3. ATT (App Tracking Transparency)`);
lines.push('');
if (trackingRequired) {
  lines.push(`**ATT 필수 = 예.** 다음 근거로 추적이 발생한다:`);
  lines.push('');
  for (const reason of [...new Set(trackingReasons)]) lines.push(`- ${reason}`);
  lines.push('');
  lines.push(`조치(필수):`);
  lines.push(`- [ ] ATT 프리프롬프트 노출 후 시스템 \`requestTrackingAuthorization\` 호출 (templates/att-copy.md)`);
  lines.push(`- [ ] \`ios.infoPlist.NSUserTrackingUsageDescription\` 설정 (빈 값/포괄 문구 금지)`);
  lines.push(`- [ ] Apple 라벨에서 해당 항목 Used for Tracking = Tracking 으로 표기 (위 §1)`);
} else {
  lines.push(`**ATT 필수 = 아니오.** 광고 식별자 수집·광고/브로커 공유가 인벤토리에서 관측되지 않음.`);
  lines.push(`- ATT 프리프롬프트와 \`NSUserTrackingUsageDescription\`을 추가하지 말 것 (불필요한 추적 선언은 신뢰 저하).`);
  lines.push(`- 이후 광고 SDK를 붙이면 이 판정이 바뀐다 — 인벤토리 갱신 후 재실행.`);
}
lines.push('');

lines.push(`## 4. 불일치 / 검토 경고 (필수)`);
lines.push('');
if (unmapped.length) {
  lines.push(`### 매핑 미결 (\`[검토필요]\`)`);
  for (const u of unmapped) lines.push(`- "${esc(u)}" — 자동 매핑 규칙에 걸리지 않음. Apple 카테고리/Play 유형을 사람이 지정.`);
  lines.push('');
}
lines.push(`### 선언 ↔ 수집 불일치 (data-flow.md §3에서 승계)`);
if (risksSection) {
  lines.push('');
  lines.push(risksSection);
} else {
  lines.push(`- data-flow.md에 §3 위험 섹션을 찾지 못함. 기존 라벨/Data Safety 선언과 위 §1·§2를 수동 대조하라.`);
  lines.push(`  - 과소 선언(코드 수집 O, 라벨 X) = Apple 5.1.1 / Play 부정확 신고 → 리젝.`);
  lines.push(`  - 과대 선언(라벨 O, 코드 근거 X) = 정리 권고.`);
}
lines.push('');

const output = lines.join('\n');

if (outPath) {
  try {
    writeFileSync(outPath, output, 'utf8');
    console.error(`[disclosure] wrote ${outPath} (${rows.length} data types, ATT=${trackingRequired ? '필수' : '불필요'})`);
  } catch (e) {
    console.error(`[disclosure] ERROR: cannot write '${outPath}': ${e.message}`);
    process.exit(1);
  }
} else {
  process.stdout.write(output + '\n');
  console.error(`[disclosure] ${rows.length} data types parsed · ATT=${trackingRequired ? '필수' : '불필요'} · 미매핑 ${unmapped.length}건`);
}

process.exit(0);
