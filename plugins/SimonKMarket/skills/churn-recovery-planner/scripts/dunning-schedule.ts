#!/usr/bin/env node
/**
 * dunning-schedule.ts — 결제 실패 리트라이 스케줄 생성기
 *
 * 결제 주기 + 실패 코드 유형 + 최대 시도 횟수에서 결정론적 dunning 스케줄을
 * 생성한다. soft decline은 시간차 재시도, hard decline은 즉시 중단(갱신만 유도),
 * expired는 리트라이 없이 갱신 유도. 주말은 자동 회피(평일로 시프트).
 *
 * 사용:
 *   npx tsx dunning-schedule.ts --cycle monthly --code soft --max 5
 *   npx tsx dunning-schedule.ts --cycle annual --code expired
 *     cycle = monthly | annual   (기본 monthly)
 *     code  = soft | hard | expired | generic   (기본 soft)
 *     max   = 최대 시도 횟수 (soft/generic만 유효, 기본 5, 1~8)
 *     start = D0 기준 요일 0=일~6=토 (주말 시프트 계산용, 기본 1=월)
 *
 * 시크릿/외부 호출 없음. 순수 계산. 출력은 JSON(스케줄) + 사람용 요약.
 */

type Cycle = "monthly" | "annual";
type Code = "soft" | "hard" | "expired" | "generic";

interface Args {
  cycle: Cycle;
  code: Code;
  max: number;
  start: number;
}

interface Attempt {
  attempt: number;
  dayOffset: number; // D0 기준 경과일 (주말 시프트 반영 후)
  rawDayOffset: number; // 시프트 전 기본 간격
  retry: boolean; // 실제 재청구를 수행하는가
  message: string | null; // 동반 메시지 (없으면 null = 조용한 재시도)
  channel: string | null;
}

const VALID_CYCLE: Cycle[] = ["monthly", "annual"];
const VALID_CODE: Code[] = ["soft", "hard", "expired", "generic"];

function parseArgs(argv: string[]): Args {
  const m: Record<string, string> = {};
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i]?.replace(/^--/, "");
    const val = argv[i + 1];
    if (key && val !== undefined) m[key] = val;
  }
  const cycle = (m.cycle ?? "monthly") as Cycle;
  const code = (m.code ?? "soft") as Code;
  const max = m.max !== undefined ? Number(m.max) : 5;
  const start = m.start !== undefined ? Number(m.start) : 1;

  if (!VALID_CYCLE.includes(cycle)) {
    throw new Error(`--cycle 은 ${VALID_CYCLE.join(" | ")} 중 하나`);
  }
  if (!VALID_CODE.includes(code)) {
    throw new Error(`--code 는 ${VALID_CODE.join(" | ")} 중 하나`);
  }
  if (!Number.isInteger(max) || max < 1 || max > 8) {
    throw new Error("--max 는 1~8 정수");
  }
  if (!Number.isInteger(start) || start < 0 || start > 6) {
    throw new Error("--start 는 0(일)~6(토) 정수");
  }
  return { cycle, code, max, start };
}

/** 기본 간격(일): soft/generic은 점증, 연간은 윈도를 늘린다. */
function baseOffsets(cycle: Cycle, max: number): number[] {
  // 월간 기준 골격: D0, D2, D4, D6, D7, D10, D12, D14
  const monthly = [0, 2, 4, 6, 7, 10, 12, 14];
  // 연간은 금액 충격이 커서 윈도를 늘림: D0, D3, D7, D14, D21, D28, D35, D42
  const annual = [0, 3, 7, 14, 21, 28, 35, 42];
  const seq = cycle === "annual" ? annual : monthly;
  return seq.slice(0, max);
}

/** 주말(토=6, 일=0)이면 다음 평일(월)로 시프트한 오프셋을 반환. */
function shiftWeekend(dayOffset: number, startDow: number): number {
  const dow = (startDow + dayOffset) % 7;
  if (dow === 6) return dayOffset + 2; // 토 → 월
  if (dow === 0) return dayOffset + 1; // 일 → 월
  return dayOffset;
}

function buildSoftLike(a: Args): Attempt[] {
  const offsets = baseOffsets(a.cycle, a.max);
  const attempts: Attempt[] = [];
  offsets.forEach((raw, idx) => {
    const attemptNo = idx + 1;
    const isFirst = attemptNo === 1;
    const isLast = attemptNo === offsets.length;
    const shifted = shiftWeekend(raw, a.start);

    let message: string | null = null;
    let channel: string | null = null;
    if (isFirst) {
      message = "결제가 처리되지 않았어요 (부드러운 안내, 비난 금지)";
      channel = "inapp+email";
    } else if (isLast) {
      message = "최종 안내 + 결제수단 갱신 1-클릭 + 다운셀 옵션";
      channel = "email+push";
    } else if (attemptNo === offsets.length - 1) {
      message = "곧 서비스가 중단돼요 (grace period 고지)";
      channel = "push+email";
    } else if (attemptNo % 2 === 1) {
      message = "결제수단 갱신 1-클릭 링크 (단일 CTA)";
      channel = "email";
    }
    // 짝수번째 중간 시도는 조용한 재청구(message=null)

    attempts.push({
      attempt: attemptNo,
      dayOffset: shifted,
      rawDayOffset: raw,
      retry: true,
      message,
      channel,
    });
  });
  return attempts;
}

function buildHard(a: Args): Attempt[] {
  // hard decline: 재시도 금지. 결제수단 교체만 유도.
  return [
    {
      attempt: 1,
      dayOffset: 0,
      rawDayOffset: 0,
      retry: false,
      message:
        "카드가 거절되었어요. 다른 결제수단으로 변경해 주세요 (재시도 안 함 — 발급사 차단 회피)",
      channel: "inapp+email",
    },
  ];
}

function buildExpired(a: Args): Attempt[] {
  // expired: 리트라이 무의미. 만료 → 갱신 유도. 프리덩닝(2단계)이 본질.
  const d3 = shiftWeekend(3, a.start);
  return [
    {
      attempt: 1,
      dayOffset: 0,
      rawDayOffset: 0,
      retry: false,
      message:
        "카드가 만료되었어요. 새 카드로 갱신해 주세요 (프리덩닝으로 사전 예방 권장)",
      channel: "inapp+email",
    },
    {
      attempt: 2,
      dayOffset: d3,
      rawDayOffset: 3,
      retry: false,
      message: "갱신 리마인드 + Account Updater 자동갱신 확인",
      channel: "email",
    },
  ];
}

function build(a: Args): Attempt[] {
  switch (a.code) {
    case "hard":
      return buildHard(a);
    case "expired":
      return buildExpired(a);
    case "soft":
    case "generic":
    default:
      return buildSoftLike(a);
  }
}

function run(a: Args) {
  const attempts = build(a);
  const retryCount = attempts.filter((x) => x.retry).length;
  const lastDay = attempts.length ? attempts[attempts.length - 1].dayOffset : 0;

  const schedule = {
    cycle: a.cycle,
    failureCode: a.code,
    maxAttempts: a.code === "soft" || a.code === "generic" ? a.max : attempts.length,
    actualRetries: retryCount,
    gracePeriodDays: lastDay,
    notes:
      a.code === "hard"
        ? "hard decline: 재시도 금지. 결제수단 교체만 유도."
        : a.code === "expired"
        ? "expired: 리트라이 무의미. 갱신 유도 + 프리덩닝(D-30/-7/-1) 선행 권장."
        : "soft/generic: 시간차 재시도. 주말은 평일로 시프트. 급여일 정렬은 PG 데이터로 추가 조정.",
    attempts,
  };

  console.log(JSON.stringify(schedule, null, 2));
  console.log("");
  console.log("=== 요약 ===");
  console.log(`주기: ${a.cycle} / 실패코드: ${a.code}`);
  console.log(`실제 재청구 횟수: ${retryCount} / grace period: D+${lastDay}`);
  attempts.forEach((x) => {
    const tag = x.retry ? "재청구" : "안내만";
    const msg = x.message ? `${x.channel}: ${x.message}` : "(조용한 재시도, 메시지 없음)";
    const shifted = x.dayOffset !== x.rawDayOffset ? ` [주말→D+${x.dayOffset}]` : "";
    console.log(`  #${x.attempt} D+${x.rawDayOffset}${shifted} [${tag}] ${msg}`);
  });
}

try {
  run(parseArgs(process.argv.slice(2)));
} catch (e) {
  console.error("오류:", (e as Error).message);
  process.exit(1);
}
