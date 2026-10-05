/**
 * consent-gated-wrapper.ts — 불변식 I1 (동의 게이트) 패턴.
 *
 * 모든 트래커/광고 발화는 consent-manager 의 동의 상태가 'granted' 일 때만 통과한다.
 * 동의 전에는 SDK 로드/init 자체를 미루고, 발화는 drop(기본) 또는 queue(명시 요청 시) 한다.
 *
 * 이 래퍼는 consent 상태를 "읽기만" 한다. 상태 관리는 consent-manager 소관.
 */

import { getTracker } from "./failopen-init";
// 택소노미 단일 소스 (I3). 인라인 이벤트명 금지 — 반드시 상수에서 import.
// import { EVENTS } from "@/lib/analytics/taxonomy";

/** consent-manager 가 노출하는 상태 형태(예시). 실제 import 로 교체. */
type ConsentState = "granted" | "denied" | "unknown";

/** consent-manager 연결 지점. 실제 구현으로 교체. */
function getAnalyticsConsent(): ConsentState {
  try {
    // 예: return useConsentStore.getState().analytics;
    // consent-manager 미설치 시 임시 no-op: 안전을 위해 'denied' 기본.
    return "denied"; // TODO: consent-manager 연결
  } catch {
    return "denied"; // 읽기 실패 시 보수적으로 차단
  }
}

const QUEUE_MODE = false; // 기본 drop. true 면 동의 전 이벤트를 큐잉 후 flush.
const pending: Array<{ event: string; props?: Record<string, unknown> }> = [];

/** 동의 게이트를 통과한 track. 미동의 시 발화하지 않는다. */
export function trackGated(event: string, props?: Record<string, unknown>): void {
  const consent = getAnalyticsConsent();

  if (consent !== "granted") {
    if (QUEUE_MODE && consent === "unknown") {
      pending.push({ event, props }); // 미정 상태만 큐잉
    }
    return; // denied/unknown → drop. 절대 발화 안 함.
  }

  // 동의 됨 → fail-open tracker 로 위임 (I2).
  getTracker().track(event, props);
}

/** 동의 부여 직후 호출 — 큐잉된 이벤트 flush (QUEUE_MODE 시). */
export function onConsentGranted(): void {
  if (!QUEUE_MODE) {
    pending.length = 0;
    return;
  }
  const t = getTracker();
  while (pending.length) {
    const item = pending.shift()!;
    t.track(item.event, item.props);
  }
}

/** 동의 철회 — 큐 비우고 이후 발화 차단(게이트가 이미 막지만 명시적으로). */
export function onConsentRevoked(): void {
  pending.length = 0;
  // 필요 시 SDK opt-out 호출 (예: gtag('consent','update',{analytics_storage:'denied'}))
}
