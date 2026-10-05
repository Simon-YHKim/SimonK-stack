#!/usr/bin/env node
// napkin 단위경제성 계산기 — unit-economics-modeler skill 보조 도구 (Node ESM, 의존성 0).
//
// 코호트 LTV(생존곡선 + 확장매출 + 마진 + 선택적 할인) → payback(누적 기여이익이
// CAC를 넘는 첫 월) → LTV:CAC → 보수/기본/공격 3시나리오 → 가드레일 판정.
// 정밀 회계가 아니라 의사결정용 러프 추정이다.
//
// 사용:
//   node unit_economics_napkin.mjs \
//     --arpu 9900 --churn 0.08 --expansion 0.01 \
//     --cac 18000 --var-cost-rate 0.20 --horizon 36 --discount 0.0

function parseArgs(argv) {
  const a = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) {
      const key = argv[i].slice(2);
      const val = argv[i + 1];
      a[key] = val !== undefined && !val.startsWith('--') ? Number(val) : true;
      if (a[key] !== true) i++;
    }
  }
  return a;
}

const won = (x) => `₩${Math.round(x).toLocaleString('en-US')}`;

// 월별 코호트 LTV + 누적 기여이익 곡선(payback 계산용)
function cohortLtv(arpu, churn, expansion, gm, horizon, discount) {
  let ltv = 0;
  let survival = 1;
  const cumulative = [];
  for (let t = 0; t < horizon; t++) {
    const revenue = arpu * Math.pow(1 + expansion, t);
    let contribution = survival * revenue * gm;
    if (discount > 0) contribution /= Math.pow(1 + discount, t);
    ltv += contribution;
    cumulative.push(ltv);
    survival *= 1 - churn;
  }
  return { ltv, cumulative };
}

function paybackMonth(cumulative, cac) {
  for (let i = 0; i < cumulative.length; i++) {
    if (cumulative[i] >= cac) return i + 1;
  }
  return null;
}

function verdict(ratio, payback, horizon) {
  const okRatio = ratio >= 1.0;
  const okPayback = payback !== null && payback < 12;
  if (ratio >= 3.0 && okPayback) return 'PASS (건강)';
  if (okRatio && okPayback) return 'PASS (취약 — LTV:CAC<3)';
  if (!okRatio) return 'FAIL (적자 구조: LTV<CAC)';
  if (payback === null) return `FAIL (지평선 ${horizon}개월 내 CAC 미회수)`;
  return `FAIL (payback ${payback}개월 >= 12)`;
}

function runScenario(name, arpu, churn, expansion, gm, cac, horizon, discount) {
  const { ltv, cumulative } = cohortLtv(arpu, churn, expansion, gm, horizon, discount);
  const pb = paybackMonth(cumulative, cac);
  const ratio = cac > 0 ? ltv / cac : Infinity;
  const pbStr = pb !== null ? `${pb}개월` : `>${horizon}개월`;
  return { name, ltv, cac, ratio, payback: pb, pbStr, verdict: verdict(ratio, pb, horizon) };
}

function die(msg) {
  console.error(msg);
  process.exit(1);
}

function main() {
  const a = parseArgs(process.argv.slice(2));
  const arpu = a.arpu, churn = a.churn, cac = a.cac;
  const expansion = a.expansion || 0;
  const varCostRate = a['var-cost-rate'] || 0;
  const horizon = a.horizon || 36;
  const discount = a.discount || 0;

  if (!(arpu > 0) || !(churn > 0) || !(cac > 0)) {
    die('필수: --arpu --churn --cac (모두 양수). --help는 파일 상단 주석 참고.');
  }
  if (churn <= expansion) die('churn > expansion 이어야 한다 (아니면 LTV가 발산).');
  if (!(varCostRate >= 0 && varCostRate < 1)) die('var-cost-rate 는 0 이상 1 미만.');

  const gm = 1 - varCostRate;
  const cmUnit = arpu * gm;

  console.log('== 입력 (base) ==');
  console.log(`ARPU ${won(arpu)} / 월 churn ${(churn * 100).toFixed(1)}% / 확장 g ${(expansion * 100).toFixed(1)}%`);
  console.log(`변동비율 ${(varCostRate * 100).toFixed(0)}% → 기여 마진율 GM ${(gm * 100).toFixed(0)}%`);
  console.log(`CAC ${won(cac)} / 지평선 ${horizon}개월 / 할인율 ${(discount * 100).toFixed(1)}%`);
  console.log(`단위 기여이익(월): ${won(cmUnit)}  (평균 유지 ${(1 / churn).toFixed(1)}개월)`);
  console.log('');

  const scenarios = [
    runScenario('보수', arpu, churn * 1.5, 0, Math.max(gm - 0.1, 0.01), cac * 1.3, horizon, discount),
    runScenario('기본', arpu, churn, expansion, gm, cac, horizon, discount),
    runScenario('공격', arpu, churn * 0.7, expansion * 1.5, gm, cac * 0.8, horizon, discount),
  ];

  console.log('== 시나리오 민감도 ==');
  console.log('시나리오   LTV              CAC          LTV:CAC   payback   판정');
  console.log('-'.repeat(78));
  for (const s of scenarios) {
    const row = `${s.name.padEnd(6)} ${won(s.ltv).padStart(14)} ${won(s.cac).padStart(12)} `
      + `${s.ratio.toFixed(2).padStart(7)}x ${s.pbStr.padStart(9)}  ${s.verdict}`;
    console.log(row);
  }
  console.log('');

  const cons = scenarios[0];
  const base = scenarios[1];
  console.log('== 가드레일 (보수 시나리오 기준) ==');
  console.log(`  보수 LTV:CAC ${cons.ratio.toFixed(2)}x  /  payback ${cons.pbStr}`);
  console.log(`  -> ${cons.verdict}`);
  if (cons.verdict.includes('FAIL')) {
    console.log('  레버: 가격↑(ARPU) · 이탈↓(churn) · CAC↓ · 변동비↓(GM↑) · 연간선결제');
  }
  console.log('');
  console.log('주의: napkin 추정. 세금/고정비 별도. 입력값 출처를 UNIT_ECONOMICS.md에 명시할 것.');
  console.log(`      기본 시나리오 판정: ${base.verdict}`);
}

main();
