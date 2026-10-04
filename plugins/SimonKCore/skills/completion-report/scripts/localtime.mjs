#!/usr/bin/env node
// localtime.mjs — 현재 시각을 로케일 형식의 완료 타임스탬프로 출력.
//
// 사용:
//   node localtime.mjs                  # 시스템 타임존 자동 감지
//   node localtime.mjs --tz Asia/Seoul  # 타임존 강제
//   node localtime.mjs --locale en-US   # 날짜 순서 힌트
//
// 형식:
//   한국(Asia/Seoul)   [YYYY-MM-DD / HH:MM:SS KST]
//   일본(Asia/Tokyo)   [YYYY-MM-DD / HH:MM:SS JST]
//   미국(America/*)    [MM/DD/YYYY / hh:MM:SS AM/PM <TZ>]
//   영국·EU(Europe/*)  [DD/MM/YYYY / HH:MM:SS <TZ>]
//   그 외              [YYYY-MM-DD / HH:MM:SS ±HH:MM]   (ISO + 오프셋)

const args = {};
for (let i = 2; i < process.argv.length; i++) {
  const a = process.argv[i];
  if (a.startsWith('--')) args[a.slice(2)] = process.argv[i + 1] && !process.argv[i + 1].startsWith('--') ? process.argv[++i] : true;
}

const SYS_TZ = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
const tz = typeof args.tz === 'string' ? args.tz : SYS_TZ;
const now = new Date();

// 무 DST 고정 약어 (Intl이 GMT+9 형태로 줄 수 있어 보정)
const FIXED_ABBR = { 'Asia/Seoul': 'KST', 'Asia/Tokyo': 'JST', 'Asia/Shanghai': 'CST', 'Asia/Kolkata': 'IST' };

function parts(opts) {
  const f = new Intl.DateTimeFormat('en-US', { timeZone: tz, hour12: false, ...opts });
  const o = {};
  for (const p of f.formatToParts(now)) o[p.type] = p.value;
  return o;
}

const base = parts({ year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', timeZoneName: 'short' });
const { year: Y, month: Mo, day: D, hour: H, minute: Mi, second: S } = base;
let abbr = FIXED_ABBR[tz] || base.timeZoneName || '';

// ISO 오프셋 (그 외 지역 fallback)
const off = parts({ timeZoneName: 'shortOffset' }).timeZoneName || 'UTC'; // e.g. GMT+9
const isoOff = off.replace(/^GMT/, '').replace(/^UTC/, '') || '+00:00';

function region() {
  if (tz === 'Asia/Seoul') return 'KR';
  if (tz === 'Asia/Tokyo') return 'JP';
  if (tz.startsWith('America/')) return 'US';
  if (tz.startsWith('Europe/')) return 'EU';
  return 'ISO';
}

let out;
switch (region()) {
  case 'KR':
  case 'JP':
    out = `[${Y}-${Mo}-${D} / ${H}:${Mi}:${S} ${abbr}]`;
    break;
  case 'US': {
    const p12 = parts({ hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true, timeZoneName: 'short' });
    out = `[${Mo}/${D}/${Y} / ${p12.hour}:${p12.minute}:${p12.second} ${p12.dayPeriod} ${p12.timeZoneName}]`;
    break;
  }
  case 'EU':
    out = `[${D}/${Mo}/${Y} / ${H}:${Mi}:${S} ${abbr}]`;
    break;
  default:
    out = `[${Y}-${Mo}-${D} / ${H}:${Mi}:${S} ${isoOff}]`;
}

console.log(out);
console.error(`tz=${tz} region=${region()}`); // 진단(stderr)
