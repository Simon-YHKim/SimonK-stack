#!/usr/bin/env node
/**
 * recovery-kpi.ts — 이탈 회복 funnel KPI 계산기
 *
 * 단계별 카운트(결제 실패·dunning·프리덩닝·취소·윈백)에서 회복률과
 * 구제 매출(recovered MRR), 비자발 이탈률, funnel 누수를 계산한다.
 * "보낸 메시지 수"가 아니라 "구제된 구독·매출"을 본다.
 *
 * 사용:
 *   npx tsx recovery-kpi.ts \
 *     --renewals 10000 --failed 800 \
 *     --dunningRecovered 480 \
 *     --expiringCards 600 --predunningSaved 420 \
 *     --cancelEntered 300 --cancelSaved 90 \
 *     --winbackTargeted 500 --winbackReturned 55 \
 *     --arpu 12000 --activeSubs 9200
 *
 *   필수: --renewals --failed
 *   나머지는 해당 단계를 운영 중일 때만. 생략 시 그 지표는 n/a.
 *
 * 시크릿/외부 호출 없음. 순수 계산. 데이터는 호출자가 PG/분석 도구에서 추출해 전달.
 */

interface Args {
  renewals: number;
  failed: number;
  dunningRecovered?: number;
  expiringCards?: number;
  predunningSaved?: number;
  cancelEntered?: number;
  cancelSaved?: number;
  winbackTargeted?: number;
  winbackReturned?: number;
  arpu?: number;
  activeSubs?: number;
}

const NUMERIC_KEYS: (keyof Args)[] = [
  "renewals",
  "failed",
  "dunningRecovered",
  "expiringCards",
  "predunningSaved",
  "cancelEntered",
  "cancelSaved",
  "winbackTargeted",
  "winbackReturned",
  "arpu",
  "activeSubs",
];

function parseArgs(argv: string[]): Args {
  const m: Partial<Record<keyof Args, number>> = {};
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i]?.replace(/^--/, "") as keyof Args | undefined;
    const val = Number(argv[i + 1]);
    if (key && NUMERIC_KEYS.includes(key)) {
      if (!Number.isFinite(val)) throw new Error(`--${key} 는 숫자여야 함`);
      if (val < 0) throw new Error(`--${key} 는 음수일 수 없음`);
      m[key] = val;
    }
  }
  if (m.renewals === undefined || m.failed === undefined) {
    throw new Error("필수 인자: --renewals --failed");
  }
  if (m.failed > m.renewals) throw new Error("--failed 는 --renewals 보다 클 수 없음");
  return m as Args;
}

const pct = (x: number) => (x * 100).toFixed(2) + "%";
const won = (x: number) => "₩" + Math.round(x).toLocaleString("ko-KR");

/** numerator/denominator 안전 비율. denominator 없거나 0이면 null. */
function ratio(num?: number, den?: number): number | null {
  if (num === undefined || den === undefined || den === 0) return null;
  return num / den;
}

function line(label: string, r: number | null, extra = "") {
  if (r === null) {
    console.log(`${label.padEnd(20)}: n/a (데이터 미입력)`);
  } else {
    console.log(`${label.padEnd(20)}: ${pct(r)}${extra ? "  " + extra : ""}`);
  }
}

function run(a: Args) {
  const failRate = a.failed / a.renewals;
  const dunningRate = ratio(a.dunningRecovered, a.failed);
  const predunningRate = ratio(a.predunningSaved, a.expiringCards);
  const cancelSaveRate = ratio(a.cancelSaved, a.cancelEntered);
  const winbackRate = ratio(a.winbackReturned, a.winbackTargeted);

  // 회복된 구독 총합 = dunning + 프리덩닝 + 취소방어 + 윈백 (운영 중인 단계만)
  const recoveredSubs =
    (a.dunningRecovered ?? 0) +
    (a.predunningSaved ?? 0) +
    (a.cancelSaved ?? 0) +
    (a.winbackReturned ?? 0);

  console.log("=== Churn Recovery Funnel KPI ===");
  line("결제 실패율", failRate, `(${a.failed}/${a.renewals})`);
  line("dunning 회복률", dunningRate, dunningRate !== null ? `(${a.dunningRecovered}/${a.failed})` : "");
  line(
    "프리덩닝 예방율",
    predunningRate,
    predunningRate !== null ? `(${a.predunningSaved}/${a.expiringCards})` : ""
  );
  line(
    "취소 save율",
    cancelSaveRate,
    cancelSaveRate !== null ? `(${a.cancelSaved}/${a.cancelEntered})` : ""
  );
  line(
    "윈백율",
    winbackRate,
    winbackRate !== null ? `(${a.winbackReturned}/${a.winbackTargeted})` : ""
  );

  console.log("");
  console.log(`회복된 구독 합계   : ${recoveredSubs.toLocaleString("ko-KR")}건`);

  if (a.arpu !== undefined) {
    const recoveredMrr = recoveredSubs * a.arpu;
    console.log(`구제 매출(MRR)     : ${won(recoveredMrr)}  (ARPU ${won(a.arpu)} 기준)`);
    console.log(`연환산(ARR 영향)   : ${won(recoveredMrr * 12)}`);
  } else {
    console.log("구제 매출(MRR)     : n/a (--arpu 미입력)");
  }

  // 비자발 이탈률: 결제 실패 중 회복 못한 건 (dunning+프리덩닝 회복 제외)
  if (a.activeSubs !== undefined) {
    const involuntaryLost = Math.max(
      0,
      a.failed - (a.dunningRecovered ?? 0) - (a.predunningSaved ?? 0)
    );
    const involRate = involuntaryLost / a.activeSubs;
    line("비자발 이탈률", involRate, `(${involuntaryLost}/${a.activeSubs} 활성)`);
  }

  console.log("");
  console.log("=== funnel 누수 진단 ===");
  if (failRate > 0.05) {
    console.log("- 결제 실패율 5% 초과: 프리덩닝(2단계)·Account Updater부터 강화. 입구를 줄여라.");
  }
  if (dunningRate !== null && dunningRate < 0.3) {
    console.log("- dunning 회복률 30% 미만: 실패코드 분기·리트라이 타이밍 점검. 평일 오전·급여일 정렬.");
  }
  if (cancelSaveRate !== null && cancelSaveRate < 0.1) {
    console.log("- 취소 save율 10% 미만: 이유별 분기·pause 옵션 노출 점검.");
  }
  console.log("- save-offer/윈백 혜택은 holdout 대조군으로 순증 효과 확인 (holdout-lift.ts).");
}

try {
  run(parseArgs(process.argv.slice(2)));
} catch (e) {
  console.error("오류:", (e as Error).message);
  process.exit(1);
}
