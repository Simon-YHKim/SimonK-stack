/**
 * ATT pre-prompt template (RN/Expo).
 *
 * Order matters: show this APP-OWN screen first to explain value, then only call
 * the system ATT dialog (which fires once, ever) when the user taps continue.
 * If denied, fall through to SKAdNetwork / AdServices — measurement is NOT zero.
 *
 * Deps (bare RN or Expo dev-client; not available in Expo Go):
 *   expo install expo-tracking-transparency
 * Replace copy with honest, non-coercive text. No "you must allow". No clinical
 * or exaggerated terms (project lexicon policy). One message + one CTA.
 *
 * NOTE: trackingPermission is iOS-only. On Android this is a no-op (return granted).
 */
import React from 'react';
import { Platform, Pressable, Text, View } from 'react-native';
import {
  getTrackingPermissionsAsync,
  requestTrackingPermissionsAsync,
} from 'expo-tracking-transparency';

type AttStatus = 'authorized' | 'denied' | 'not_determined' | 'unavailable';

export async function ensureAttDecision(): Promise<AttStatus> {
  if (Platform.OS !== 'ios') return 'unavailable'; // Android: no ATT
  const current = await getTrackingPermissionsAsync();
  if (current.status !== 'undetermined') {
    return current.status === 'granted' ? 'authorized' : 'denied';
  }
  // System dialog fires here — call only AFTER the user accepted the pre-prompt.
  const result = await requestTrackingPermissionsAsync();
  return result.status === 'granted' ? 'authorized' : 'denied';
}

/** App-owned pre-prompt. Render BEFORE ensureAttDecision(). */
export function AttPrePrompt({
  onContinue,
  onSkip,
}: {
  onContinue: () => void; // -> then call ensureAttDecision()
  onSkip: () => void; // user declines pre-prompt; do NOT show system dialog
}) {
  return (
    <View accessibilityRole="summary">
      {/* One message. Honest value statement, no coercion. */}
      <Text>어느 채널에서 앱을 알게 됐는지 측정해 더 나은 추천을 제공합니다.</Text>
      {/* One primary CTA. */}
      <Pressable accessibilityRole="button" onPress={onContinue}>
        <Text>다음</Text>
      </Pressable>
      <Pressable accessibilityRole="button" onPress={onSkip}>
        <Text>나중에</Text>
      </Pressable>
    </View>
  );
}

/*
 * audit hook (consent-manager 정렬): 동의 상태/시각을 기록.
 *   await logConsent({ scope: 'att', status, ts: new Date().toISOString() });
 */
