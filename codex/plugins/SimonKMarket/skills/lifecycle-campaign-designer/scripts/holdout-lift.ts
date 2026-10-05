#!/usr/bin/env node
/**
 * holdout-lift.ts — 캠페인 incremental lift 계산기
 *
 * 처치군(메시지 받음)과 holdout 대조군(안 받음)의 전환 수에서
 * 절대/상대 증분과 근사 유의성(2-proportion z-test)을 계산한다.
 * 개봉률/클릭률이 아니라 "보냈을 때 행동/전환이 얼마나 더 일어났는가"를 본다.
 *
 * 사용:
 *   npx tsx holdout-lift.ts --tn 9000 --tc 540 --cn 1000 --cc 40
 *     tn=처치군 인원, tc=처치군 전환, cn=대조군 인원, cc=대조군 전환
 *
 * 시크릿/외부 호출 없음. 순수 계산. 데이터는 호출자가 분석 도구에서 추출해 전달.
 */

interface Args { tn: number; tc: number; cn: number; cc: number; }

function parseArgs(argv: string[]): Args {
  const m: Record<string, number> = {};
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i]?.replace(/^--/, "");
    const val = Number(argv[i + 1]);
    if (key) m[key] = val;
  }
  const a = { tn: m.tn, tc: m.tc, cn: m.cn, cc: m.cc };
  if ([a.tn, a.tc, a.cn, a.cc].some((v) => !Number.isFinite(v))) {
    throw new Error("필수 인자: --tn --tc --cn --cc (모두 숫자)");
  }
  if (a.tc > a.tn || a.cc > a.cn) throw new Error("전환 수가 인원보다 클 수 없음");
  return a;
}

/** 표준정규 누적분포 근사 (Abramowitz-Stegun 7.1.26 기반). */
function normalCdf(z: number): number {
  const t = 1 / (1 + 0.2316419 * Math.abs(z));
  const d = 0.3989423 * Math.exp(-(z * z) / 2);
  const p =
    d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
  return z > 0 ? 1 - p : p;
}

function run(a: Args) {
  const pt = a.tc / a.tn; // 처치군 전환율
  const pc = a.cc / a.cn; // 대조군 전환율
  const absLift = pt - pc; // 절대 증분
  const relLift = pc > 0 ? absLift / pc : Infinity; // 상대 증분
  const incrementalConversions = absLift * a.tn; // 처치군 규모 기준 순증 전환

  // 2-proportion z-test (pooled)
  const pPool = (a.tc + a.cc) / (a.tn + a.cn);
  const se = Math.sqrt(pPool * (1 - pPool) * (1 / a.tn + 1 / a.cn));
  const z = se > 0 ? absLift / se : 0;
  const pValue = 2 * (1 - normalCdf(Math.abs(z))); // 양측

  const pct = (x: number) => (x * 100).toFixed(2) + "%";
  console.log("=== Campaign Incremental Lift ===");
  console.log(`처치군 전환율 : ${pct(pt)}  (${a.tc}/${a.tn})`);
  console.log(`대조군 전환율 : ${pct(pc)}  (${a.cc}/${a.cn})`);
  console.log(`절대 증분     : ${pct(absLift)} (pp)`);
  console.log(`상대 증분     : ${Number.isFinite(relLift) ? pct(relLift) : "n/a (대조군 0)"}`);
  console.log(`순증 전환(추정): ${incrementalConversions.toFixed(1)}건`);
  console.log(`z = ${z.toFixed(3)},  p ≈ ${pValue.toFixed(4)}  ${pValue < 0.05 ? "(유의, p<0.05)" : "(유의 부족)"}`);
  if (a.cn < 1000 || a.tn < 1000) {
    console.log("주의: 표본이 작으면 p값을 신뢰하지 말 것. 캠페인 합치거나 기간 연장.");
  }
}

try {
  run(parseArgs(process.argv.slice(2)));
} catch (e) {
  console.error("오류:", (e as Error).message);
  process.exit(1);
}
