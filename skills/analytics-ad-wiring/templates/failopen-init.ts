/**
 * failopen-init.ts — 불변식 I2 (fail-open 가드) 패턴.
 *
 * 원칙: analytics·ad 는 부가기능이다. env 누락/오류가 런타임을 죽이면 안 된다.
 * - lazy init (최초 사용 시점에만 init, 모듈 로드 시 throw 금지)
 * - try/catch 로 SDK 호출 전체 감쌈
 * - no-op fallback 반환 (init 실패해도 호출부는 정상 진행)
 *
 * 교훈: 2ndB #363 — analytics env 값 하나가 앱 전체를 블랙스크린으로 만든 사고.
 */

type Tracker = {
  track: (event: string, props?: Record<string, unknown>) => void;
  identify: (userId: string, traits?: Record<string, unknown>) => void;
  ready: boolean;
};

/** 무엇을 호출해도 아무 일도 안 일어나지만 절대 throw 하지 않는 안전판. */
const NOOP_TRACKER: Tracker = {
  track: () => {},
  identify: () => {},
  ready: false,
};

let cached: Tracker | null = null;

/** env 키를 안전하게 읽는다. 없으면 빈 문자열 (throw 금지). */
function readEnv(key: string): string {
  try {
    // 웹/RN 양쪽 안전: process.env 가 없을 수도 있다.
    const v = (typeof process !== "undefined" && process.env?.[key]) || "";
    return String(v).trim();
  } catch {
    return "";
  }
}

/** 형식 검증 — 통과 못 하면 비활성 (init 자체를 시도하지 않음). */
function isValidGa4Id(id: string): boolean {
  return /^G-[A-Z0-9]{10}$/.test(id);
}

/**
 * lazy + fail-open init.
 * 어떤 경로로도 예외를 밖으로 던지지 않는다. 실패 시 NOOP_TRACKER.
 */
export function getTracker(): Tracker {
  if (cached) return cached;

  try {
    const measurementId = readEnv("NEXT_PUBLIC_GA4_MEASUREMENT_ID");

    // env 누락/오류 → 조용히 비활성. 앱은 정상 동작.
    if (!measurementId || !isValidGa4Id(measurementId)) {
      if (readEnv("ANALYTICS_ENV") !== "production") {
        // 개발 중에만 힌트. 운영에선 침묵.
        console.warn("[analytics] GA4 id missing/invalid — tracker disabled (fail-open)");
      }
      cached = NOOP_TRACKER;
      return cached;
    }

    // 실제 SDK 초기화는 여기서 (예: window.gtag 래핑). 전부 try 안.
    cached = {
      track: (event, props) => {
        try {
          // @ts-expect-error gtag 는 스니펫 주입 후 전역에 존재
          window.gtag?.("event", event, props ?? {});
        } catch {
          /* 발화 실패가 호출부를 막지 않는다 */
        }
      },
      identify: (userId, traits) => {
        try {
          // @ts-expect-error
          window.gtag?.("set", { user_id: userId, ...(traits ?? {}) });
        } catch {
          /* no-op */
        }
      },
      ready: true,
    };
    return cached;
  } catch (e) {
    // 예기치 못한 모든 오류도 흡수.
    cached = NOOP_TRACKER;
    return cached;
  }
}
