---
name: building-native-ui
description: >
  Use when implementing or debugging React Native/Expo UI after the native path is chosen — "React Native 만들어", "Expo 화면 짜줘", "FlashList로 바꿔", "Android APK", "Hermes 빌드 깨짐", or /building-native-ui. Produces project-compatible screens and Android/iOS verification evidence; excludes web React, platform selection, unapproved cloud builds and store submission.
version: 2.0.1
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - Glob
compatibility: [claude-code]
---

# /building-native-ui

React Native/Expo UI를 **작업 대상의 실제 스택**에 맞춰 구현한다. 2nd-B의 과거 오류는 진단 단서이지 다른 앱의 기본 버전·설정이 아니다.

## When to use / boundaries

- RN/Expo 화면·리스트·제스처·애니메이션 구현 또는 성능 개선 요청
- "FlatList 느려", "리스트 스크롤 끊김", "키보드가 입력창 가림" 류 증상
- Android/Hermes 빌드 오류 또는 설치 가능한 APK 검증이 필요할 때
- `app-dev-orchestrator` 구현 단계에서 RN 트랙으로 분기됐을 때

쓰지 않는 경우:
- 웹 React → `/vercel-react`
- 하이브리드 vs 네이티브 vs PWA 결정 → `/app-platform-selector`
- 디자인 시스템·토큰 → `/design-system-keeper`
- iOS 실기기 QA → `/ios-qa`, 시각 리뷰 → `/design-review`

## 선행 체크와 구현 순서

1. 작업 위치·브랜치·변경사항, `package.json`/lockfile, `app.json` 또는 `app.config.*`, `eas.json`, `app/`·`src/app/`·`android/`·`ios/`를 확인한다. 실제 Expo SDK/RN 버전, 라우터, 상태 관리, 패키지 매니저, 테스트 명령, Android/iOS 도구를 파악한다. Expo가 없는 RN 앱도 이 스킬의 대상이며, 요청 없이 Expo로 이식하거나 네이티브 디렉터리를 재생성하지 않는다.
2. UI 코드 작성 전에 `simon-design-first` 진단을 수행하고 화면의 주 행동, 접근성, 로딩·오류·빈 상태를 정한다. 기존 라우터·저장소·스타일 패턴을 유지한다. 새 Expo 앱에만 Expo Router를 우선 검토하고, 기존 React Navigation의 이식은 별도 요청이 있을 때만 한다.
3. 카메라·알림·위치처럼 네이티브 기능이 필요하면 OS별 권한·config plugin·Expo Go 지원 여부를 확인한다. development build가 필요하거나 네이티브 설정이 바뀌면 해당 플랫폼에서 다시 빌드한다. 직접 수정된 `android/`·`ios/`에는 `prebuild --clean`을 적용하지 않는다.
4. 기존 스크립트로 lint·typecheck·테스트를 실행하고 변경 화면의 진입·뒤로 가기·딥링크·권한 거절·오류 상태를 기기에서 확인한다. Expo 프로젝트라면 설치된 CLI로 `expo install --check`와 `expo-doctor`를 실행해 SDK 정합성을 점검한다. `npx`의 자동 패키지 다운로드가 필요한 환경에서는 먼저 확인한다.
5. Android SDK/Android Studio가 준비되면 로컬 `expo run:android` 또는 기존 Gradle 경로를 검증한다. 네이티브 프로젝트가 있으면 Android Studio 열기·동기화·빌드 가능 여부를 확인한다. APK 요청에는 실제 `.apk` 경로와 기기/에뮬레이터 설치 결과를 제시한다. AAB를 설치 가능한 APK로 부르지 않는다. iOS는 macOS/Xcode·실기기·허가된 빌드 경로가 없으면 미검증으로 남긴다.

아래는 **프로젝트에 해당 의존성이 있고 요구가 있을 때만** 적용하는 구현·진단 참고다. 버전과 호환성은 프로젝트 파일과 해당 버전의 공식 문서에서 다시 확인한다.

## Workflow

### 1. 네비게이션 — Expo Router가 이미 있거나 도입을 선택한 경우

라우트 = 파일. `app/` 폴더 구조가 곧 네비게이션 트리.

```
app/
  _layout.tsx          # 루트 Stack
  (tabs)/
    _layout.tsx        # Tabs navigator
    index.tsx          # /            (홈 탭)
    profile.tsx        # /profile
  note/[id].tsx        # /note/123    (동적 라우트)
  +not-found.tsx       # 404
```

```tsx
// app/_layout.tsx — 루트는 SafeArea + GestureHandler 프로바이더로 감싼다
import { Stack } from 'expo-router';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="note/[id]" options={{ presentation: 'modal' }} />
        </Stack>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
```

```tsx
// 화면 이동 + 파라미터
import { router, useLocalSearchParams, Link } from 'expo-router';

router.push(`/note/${id}`);              // 명령형
<Link href={{ pathname: '/note/[id]', params: { id } }}>열기</Link>;  // 선언형
const { id } = useLocalSearchParams<{ id: string }>();  // 수신
```

이 예시는 프로젝트에 Gesture Handler가 있을 때의 루트 구성이다. `GestureHandlerRootView` 중복을 피하고 `Stack.Screen`의 `name`을 실제 파일 경로와 대조한다. 신규 도입 시 현재 SDK에 맞는 패키지·진입점·딥링크를 확인한다. 기존 다른 라우터의 경로를 자동 교체하지 않는다.

### 2. 리스트 — 측정 결과가 교체를 뒷받침할 때 FlashList 검토

| | FlatList | FlashList v2 |
|---|---|---|
| 재활용 | 화면 밖 뷰 unmount/remount | 셀 재활용(recycling) |
| 사이즈 추정 | 수동 `getItemLayout` | **자동** (estimate 불필요) |
| New Arch | 무관 | **필수** |
| 선택 | 기존 리스트가 요구를 충족하면 유지 | 큰/복잡한 리스트에서 측정 후 검토 |

```tsx
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={notes}
  renderItem={({ item }) => <NoteRow note={item} />}
  keyExtractor={(item) => item.id}
  // FlashList v2라면 estimatedItemSize를 쓰지 않는다. 자동 측정.
  // 높이가 종류별로 다르면 getItemType 으로 재활용 풀 분리:
  getItemType={(item) => item.kind}     // 'text' | 'image' | 'divider'
  drawDistance={250}                     // 미리 그릴 거리(px)
  onEndReachedThreshold={0.5}
  onEndReached={loadMore}
/>
```

v2 마이그레이션에만 기존 size-estimation props 제거와 New Architecture 활성 상태 확인이 필요하다. v1·다른 리스트 구현에는 v2 규칙을 강요하지 않는다. 스크롤 성능은 실제 기기에서 전후 비교한다.

### 3. 이미지 — 재활용 셀의 잔상이 관측될 때

```tsx
import { Image } from 'expo-image';

<Image
  source={{ uri }}
  style={{ width: 80, height: 80, borderRadius: 12 }}
  contentFit="cover"
  transition={150}                                  // fade-in (cut 금지)
  // 실제 유효한 BlurHash가 있을 때만 placeholder를 추가한다.
  cachePolicy="memory-disk"
  recyclingKey={item.id}                            // FlashList 셀 재활용 시 잔상 방지
/>
```

`expo-image`를 사용하는 재활용 셀에서 이전 이미지가 비치는 경우 `recyclingKey`를 검토한다. RN `Image`의 일괄 교체나 새 의존성 추가는 요구·측정·기존 패턴에 맞춰 결정한다.

### 4. 애니메이션·제스처 — 설치된 Reanimated 버전에 맞춰

R3→R4 이행 시 worklet 런타임이 `react-native-worklets`로 분리된다. 설치된 버전과 호환 표를 확인하고, 새 코드의 스레드 간 호출은 해당 버전의 API를 사용한다. 기존 API를 무조건 고장으로 간주하지 않는다.

Expo의 `babel-preset-expo`는 호환 버전의 플러그인을 자동 구성하므로 중복 등록하지 않는다. React Native Community CLI나 사용자 지정 Babel 설정에서 수동 플러그인이 필요한 경우에만 현재 설치 문서를 따라 마지막에 둔다:

```js
module.exports = (api) => {
  api.cache(true);
  return {
    presets: ['module:@react-native/babel-preset'],
    plugins: ['react-native-worklets/plugin'],  // 수동 구성이 필요한 RN CLI + R4 예시
  };
};
```

```tsx
import Animated, { useSharedValue, useAnimatedStyle, withTiming } from 'react-native-reanimated';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import { scheduleOnRN } from 'react-native-worklets';   // R4 예시

function Card({ onDismiss }: { onDismiss: () => void }) {
  const x = useSharedValue(0);

  const pan = Gesture.Pan()
    .onUpdate((e) => { x.value = e.translationX; })       // worklet (UI 스레드)
    .onEnd((e) => {
      if (Math.abs(e.translationX) > 120) {
        x.value = withTiming(e.translationX > 0 ? 400 : -400);
        scheduleOnRN(onDismiss);                          // JS 스레드 콜백
      } else {
        x.value = withTiming(0);                          // 바운스 없는 복귀 예시
      }
    });

  const style = useAnimatedStyle(() => ({ transform: [{ translateX: x.value }] }));
  return (
    <GestureDetector gesture={pan}>
      <Animated.View style={style}>{/* ... */}</Animated.View>
    </GestureDetector>
  );
}
```

제품 UX 4원칙에 따라 bounce/elastic 효과를 피하고 reduced-motion 설정도 고려한다. 무거운 계산을 UI worklet 안에 두지 않는다. React Native/Expo 버전별 사용 가능 여부를 먼저 확인한다.

### 5. 스타일 — NativeWind가 기존 스택일 때

```tsx
import { View, Text, Pressable } from 'react-native';

<Pressable className="active:opacity-70 rounded-2xl bg-violet-600 px-4 py-3">
  <Text className="text-base font-medium text-white">저장</Text>
</Pressable>
```

설정은 설치된 NativeWind 버전과 프로젝트의 `global.css`·Metro 구성에 맞춘다. 기존 StyleSheet·디자인 토큰을 요청 없이 NativeWind로 이식하지 않는다.

### 6. Safe-area + 키보드

```tsx
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { KeyboardAvoidingView, Platform } from 'react-native';

const insets = useSafeAreaInsets();
// 헤더/탭바 패딩에 insets.top / insets.bottom 적용 (SafeAreaView 대신 insets 권장 — FlashList 와 충돌 적음)

<KeyboardAvoidingView
  behavior={Platform.OS === 'ios' ? 'padding' : undefined}  // Android 는 보통 불필요
  style={{ flex: 1 }}
>
  {/* 입력 폼 */}
</KeyboardAvoidingView>
```

Android 키보드 동작은 현재 앱 설정·화면 구조에서 확인한다. 과거 2nd-B의 `resize` 설정을 다른 앱의 기본값으로 가정하지 않는다.

### 7. 플랫폼별 파일

```
Button.tsx          # 공통
Button.ios.tsx      # iOS 전용 (자동 선택)
Button.android.tsx  # Android 전용
Button.web.tsx      # expo web 전용
```

분기가 반복되고 플랫폼 구현이 의미 있게 다를 때 파일 분리를 고려한다. 작은 분기는 `Platform.OS`도 가능하다.

### 8. Hermes 동적 import 오류 (2nd-B에서 관측된 사례)

`Invalid expression encountered`를 만나면 로그·번들·의존성의 실제 `import()` 경로를 추적한다. 2nd-B에서는 패키지 exports 해석과 동적 import가 원인이었지만, 다른 프로젝트의 동일 문구가 같은 원인이라는 보장은 없다.

특정 패키지의 exports 조건 교정이 가능하면 그 범위에서 해결한다. 그 방법이 불가능하고 원인이 재현될 때만 Metro의 광역 폴백을 검토한다. 영향받는 다른 의존성과 타입 해석도 재검증한다:

```js
const { getDefaultConfig } = require('expo/metro-config');
const config = getDefaultConfig(__dirname);

// 재현된 package exports 충돌을 진단할 때만 임시 비교한다.
config.resolver.unstable_enablePackageExports = false;

module.exports = config;
```

2nd-B의 `pdfjs-dist` patch-package 사례를 다른 앱에 복사하지 않는다. 해당 플랫폼의 로컬 export/빌드로 수정 효과를 확인하고, EAS 호출은 별도 비용·권한 게이트를 따른다.

## 검증 (verification)

```bash
# 1) 정적 — 프로젝트에 실제 정의된 스크립트와 설치된 도구만 실행
npx expo install --check        # Expo 프로젝트에서만
npx expo-doctor                 # Expo 프로젝트에서만; 자동 다운로드 여부 확인
npm run type-check              # 스크립트가 있을 때
npm run lint                    # 스크립트가 있을 때

# 2) EAS 이전의 로컬 번들 선검증; Hermes 네이티브 컴파일까지 증명하지는 않음
npx expo export --platform android    # Expo 프로젝트에서만

# 3) 화면 동작: 지원 플랫폼의 실제 기기/에뮬레이터에서 핵심 흐름 확인
npx expo run:android                          # Expo + Android SDK가 준비됐을 때

# 4) 빌드 산출물: 기존 Gradle 또는 Expo 경로로 APK 생성·설치 확인
# EAS Build/Submit은 여기서 자동 실행하지 않는다.
```

성능은 대상 기기에서 프레임 시간·스크롤 끊김·메모리와 초기 화면 체감 시간을 전후 측정한다. 수치 목표는 제품 요구와 기기 범위에서 정하며, 도구 실행만으로 라이브 동작이나 APK 설치를 검증했다고 하지 않는다.

EAS가 필요한 경우 CLI·로그인·프로젝트 연결·현재 구독 사용량·초과 과금 차단·서명 자격을 먼저 확인한다. 구독 포함분이라는 추정만으로 클라우드 빌드를 호출하지 않는다. Windows에서는 `eas build --local`이 공식 지원 경로가 아니므로 로컬 Android Studio/Gradle 등 실제 가능한 경로를 우선한다. 추가 과금, 자동충전, 계정·자격증명 변경, `eas submit`·`--auto-submit`·스토어 공개는 별도 승인 없이 실행하지 않는다. APK 생성, 스토어 업로드, 공개 심사는 서로 다른 상태다.

## Anti-patterns

- ❌ 성능 측정 없이 리스트 라이브러리 전체 교체
- ❌ FlashList v2에서 제거된 size-estimation props 유지 또는 구아키텍처와 v2 혼용
- ❌ Expo의 자동 Babel 구성에 Worklets 플러그인 중복 등록
- ❌ Reanimated 4에서 Worklets 호환 버전·마이그레이션 경로 미확인
- ❌ worklet 안에서 무거운 JS 연산 → UI 스레드 블록, 프레임 드랍
- ❌ bounce/elastic easing → 부드러운 `withTiming`/`withSpring`
- ❌ 이미지 잔상 원인 확인 없이 모든 RN `Image` 일괄 교체
- ❌ Gesture Handler 사용 시 루트 wrapper 중복·누락
- ❌ 원인 확인 없이 Metro exports 전역 비활성화 또는 EAS 클라우드 빌드 호출
- ❌ 버전 mismatch 방치 → `expo install --check` 로 SDK 정합 맞추기

## 공식 근거 (버전·요금은 실행 시 재확인)

- [Expo SDK 호환표](https://docs.expo.dev/versions/latest/), [Expo Router 기존 앱 도입](https://docs.expo.dev/router/installation/), [Reanimated Expo 설치](https://docs.expo.dev/versions/latest/sdk/reanimated/)
- [FlashList v2 마이그레이션](https://shopify.github.io/flash-list/docs/v2-migration/), [Reanimated 3→4 이행](https://docs.swmansion.com/react-native-reanimated/docs/guides/migration-from-3.x/), [Metro exports 설정](https://docs.expo.dev/versions/latest/config/metro/)
- [APK/AAB 구분](https://docs.expo.dev/build-reference/apk/), [Windows 로컬 EAS 제약](https://docs.expo.dev/build-reference/local-builds/), [EAS 과금 경계](https://docs.expo.dev/billing/plans/)

## Related skills

- `/app-platform-selector` — 네이티브로 갈지 결정 (이 skill 의 선행)
- `/vercel-react` — 웹 React (별개 트랙)
- `/design-system-keeper` — 색/타이포/모션 토큰
- `/design-review` · `/ios-qa` — 시각·실기기 QA
- `simon-tdd` — 컴포넌트/로직 테스트 (jest)
- `app-dev-orchestrator` — 구현 단계에서 호출

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
