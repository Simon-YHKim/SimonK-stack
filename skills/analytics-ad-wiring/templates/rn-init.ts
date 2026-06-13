/**
 * rn-init.ts — RN / Expo 분석(Firebase Analytics) + 광고(AdMob) 배선.
 *
 * 불변식:
 *   I1 — consent granted 후에만 init/발화. iOS 는 ATT 프롬프트 후 개인화.
 *   I2 — env 누락/오류·모듈 미설치가 앱을 죽이지 않는다 (try/catch + no-op).
 *
 * 설치(택소노미·전략 확정 후):
 *   @react-native-firebase/app @react-native-firebase/analytics
 *   react-native-google-mobile-ads
 *   Expo managed 면 config plugin + dev client 필요.
 */

import { Platform } from "react-native";

const isProd = (process.env.ANALYTICS_ENV ?? "development") === "production";

function env(key: string): string {
  try {
    return String((process.env as Record<string, string | undefined>)[key] ?? "").trim();
  } catch {
    return "";
  }
}

// ── AdMob 광고 단위 ID 해석 (개발이면 SDK 테스트 ID 폴백) ──
// 운영 빌드에서만 운영 단위 노출. 테스트 빌드에 운영 ID 노출 금지(정책 위반).
const ADMOB_TEST_BANNER = {
  android: "ca-app-pub-3940256099942544/6300978111", // Google 공식 테스트 ID
  ios: "ca-app-pub-3940256099942544/2934735716",
};

export function resolveBannerUnitId(): string {
  if (!isProd) {
    return Platform.OS === "ios" ? ADMOB_TEST_BANNER.ios : ADMOB_TEST_BANNER.android;
  }
  const id =
    Platform.OS === "ios"
      ? env("EXPO_PUBLIC_ADMOB_BANNER_UNIT_IOS")
      : env("EXPO_PUBLIC_ADMOB_BANNER_UNIT_ANDROID");
  // 운영인데 단위 ID 누락 → 광고 끄되 앱은 산다(fail-open). 테스트 ID로 폴백하지 않음.
  return id; // 빈 문자열이면 호출부에서 배너 렌더 스킵
}

// ── Firebase Analytics init (consent 후 호출) ──
let analyticsReady = false;

export async function initAnalyticsWithConsent(granted: boolean): Promise<void> {
  if (!granted) return; // I1: 미동의 시 init 안 함
  if (analyticsReady) return;
  if (env("EXPO_PUBLIC_FIREBASE_ANALYTICS_ENABLED") !== "true") return; // 토글 off

  try {
    const analytics = (await import("@react-native-firebase/analytics")).default;
    await analytics().setAnalyticsCollectionEnabled(true);
    analyticsReady = true;
  } catch (e) {
    // 모듈 미설치 / 네이티브 빌드 누락 등 → no-op (앱 정상 동작)
    if (!isProd) console.warn("[analytics] Firebase Analytics init skipped (fail-open)", e);
  }
}

/** 동의 게이트를 통과한 track. 택소노미 상수에서만 event 전달(I3). */
export async function trackGatedRN(
  event: string,
  params?: Record<string, unknown>,
): Promise<void> {
  if (!analyticsReady) return; // 미init(=미동의/실패) 시 발화 안 함
  try {
    const analytics = (await import("@react-native-firebase/analytics")).default;
    await analytics().logEvent(event, params as Record<string, string | number> | undefined);
  } catch {
    /* fail-open: 발화 실패가 호출부를 막지 않음 */
  }
}

// ── AdMob init (consent + iOS ATT 후) ──
export async function initAdMobWithConsent(granted: boolean): Promise<void> {
  if (!granted) return; // I1
  try {
    const mobileAds = (await import("react-native-google-mobile-ads")).default;
    // iOS: ATT 프롬프트는 별도(expo-tracking-transparency 등)에서 먼저 처리해야 개인화 가능.
    await mobileAds().initialize();
  } catch (e) {
    if (!isProd) console.warn("[ads] AdMob init skipped (fail-open)", e);
  }
}
