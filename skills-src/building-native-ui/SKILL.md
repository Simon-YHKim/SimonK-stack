---
name: building-native-ui
description: >
  Use when implementing React Native + Expo UI (Simon 2nd-B stack — Expo SDK 56, RN 0.85, React 19) — triggers "React Native 만들어", "Expo 화면 짜줘", "FlashList로 바꿔", "Reanimated 애니메이션", "Hermes 빌드 깨짐", "EAS 빌드", "react native screen", "expo router", "flashlist perf", "reanimated worklet", "native list optimization", or /building-native-ui. Produces expo-router file-routed screens, FlashList v2 lists (no estimatedItemSize), Reanimated 4 + react-native-worklets gestures, NativeWind styling, safe-area + keyboard handling, platform-specific files, and the Hermes dynamic-import metro fix that 2nd-B hit (unstable_enablePackageExports=false). Includes precheck (expo-doctor), perf budgets, and EAS build/submit verification. Different from /vercel-react (web React) and /app-platform-selector (hybrid-vs-native decision) — this assumes RN/Expo is already chosen.
version: 2.0.0
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

React Native + Expo 네이티브 UI를 **현재 스택 기준**(Expo SDK 56 · RN 0.85 · React 19 · New Architecture)으로 구현한다. 2nd-B(`E:\2ndB`)에서 실제로 밟은 함정(Hermes 동적 import, Reanimated 4 worklets 분리)을 미리 막는다.

## When to use / boundaries

- RN/Expo 화면·리스트·제스처·애니메이션 구현 또는 성능 개선 요청
- "FlatList 느려", "리스트 스크롤 끊김", "키보드가 입력창 가림" 류 증상
- `expo run:android` / EAS 빌드가 Hermes "Invalid expression" 으로 깨질 때
- `app-dev-orchestrator` 구현 단계에서 RN 트랙으로 분기됐을 때

쓰지 않는 경우:
- 웹 React → `/vercel-react`
- 하이브리드 vs 네이티브 vs PWA 결정 → `/app-platform-selector`
- 디자인 시스템·토큰 → `/design-system-keeper`
- iOS 실기기 QA → `/ios-qa`, 시각 리뷰 → `/design-review`

## 선행 체크 (precheck)

```bash
# 1) Expo 프로젝트인지 + New Architecture 켜졌는지
test -f package.json && grep -q '"expo"' package.json && echo "EXPO_OK" || { echo "NOT_EXPO — skip"; exit 0; }
grep -q '"newArchEnabled": *true' app.json 2>/dev/null && echo "NEW_ARCH_ON" || echo "NEW_ARCH: check app.json (FlashList v2 / Reanimated 4 require it)"

# 2) 설치 정합성 — 버전 mismatch 가 런타임 크래시의 1순위 원인
npx expo install --check        # SDK 와 안 맞는 패키지 리포트
npx expo-doctor                 # 17개 항목 헬스체크

# 3) 핵심 의존성 버전 확인 (2nd-B 기준값)
node -e "const p=require('./package.json').dependencies; ['react-native','react-native-reanimated','react-native-worklets','@shopify/flash-list','nativewind','expo-router'].forEach(k=>console.log(k, p[k]||'(none)'))"
```

기준 스택(2nd-B): `react-native@0.85`, `react@19.2`, `react-native-reanimated@4.3`, `react-native-worklets@0.8`, `nativewind@4.2`, `expo-router@56`. Reanimated 4는 **worklets 가 별도 패키지**다 — `react-native-worklets` 없으면 빌드 실패.

## Workflow

### 1. 네비게이션 — expo-router (파일 기반)

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

규칙: `GestureHandlerRootView` 는 **앱 최상단 1회만**. `Stack.Screen` 의 `name` 은 파일명과 정확히 일치(`note/[id]` 처럼 대괄호 포함). 과거 `<Stack.Screen>` 프레임워크 오해로 위양성 리뷰 난 적 있음(MEMORY 참조) — name 매칭을 반드시 확인.

### 2. 리스트 — FlashList v2 (FlatList 금지)

| | FlatList | FlashList v2 |
|---|---|---|
| 재활용 | 화면 밖 뷰 unmount/remount | 셀 재활용(recycling) |
| 사이즈 추정 | 수동 `getItemLayout` | **자동** (estimate 불필요) |
| New Arch | 무관 | **필수** |
| 권장 | ❌ 긴 리스트 | ✅ 기본값 |

```tsx
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={notes}
  renderItem={({ item }) => <NoteRow note={item} />}
  keyExtractor={(item) => item.id}
  // v2: estimatedItemSize 제거됨 (있으면 deprecation 경고). 자동 측정.
  // 높이가 종류별로 다르면 getItemType 으로 재활용 풀 분리:
  getItemType={(item) => item.kind}     // 'text' | 'image' | 'divider'
  drawDistance={250}                     // 미리 그릴 거리(px)
  onEndReachedThreshold={0.5}
  onEndReached={loadMore}
/>
```

마이그레이션 시: `estimatedItemSize` / `estimatedListSize` 제거, New Architecture 확인(`newArchEnabled: true`). v2는 구아키텍처에서 동작 안 함.

### 3. 이미지 — expo-image (RN Image 금지)

```tsx
import { Image } from 'expo-image';

<Image
  source={{ uri }}
  style={{ width: 80, height: 80, borderRadius: 12 }}
  contentFit="cover"
  transition={150}                                  // fade-in (cut 금지)
  placeholder={{ blurhash: 'L6Pj0^...' }}           // LQIP
  cachePolicy="memory-disk"
  recyclingKey={item.id}                            // FlashList 셀 재활용 시 잔상 방지
/>
```

`recyclingKey` 는 FlashList 안에서 이미지 쓸 때 필수 — 없으면 스크롤 시 이전 이미지가 새 셀에 잠깐 남는다.

### 4. 애니메이션·제스처 — Reanimated 4 + worklets

**핵심 변경(R3→R4)**: worklet 런타임이 `react-native-worklets` 로 분리됨. `runOnJS`/`runOnUI` 가 `scheduleOnRN`/`scheduleOnUI` 로 바뀜(구 API는 점진 deprecate). import 경로 주의.

`babel.config.js` — worklets 플러그인은 **반드시 마지막**:

```js
module.exports = (api) => {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: ['react-native-worklets/plugin'],  // R4: reanimated/plugin 아님. 항상 last.
  };
};
```

```tsx
import Animated, { useSharedValue, useAnimatedStyle, withTiming, withSpring } from 'react-native-reanimated';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import { scheduleOnRN } from 'react-native-worklets';   // R4 신 API (구 runOnJS)

function Card({ onDismiss }: { onDismiss: () => void }) {
  const x = useSharedValue(0);

  const pan = Gesture.Pan()
    .onUpdate((e) => { x.value = e.translationX; })       // worklet (UI 스레드)
    .onEnd((e) => {
      if (Math.abs(e.translationX) > 120) {
        x.value = withTiming(e.translationX > 0 ? 400 : -400);
        scheduleOnRN(onDismiss);                          // JS 스레드 콜백
      } else {
        x.value = withSpring(0);                          // 부드러운 ease (bounce/elastic 금지)
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

규칙(제품 UX 4원칙): `withTiming`/`withSpring(부드러운 config)` 사용, **bounce/elastic easing 금지**, press 피드백은 즉각 cut 말고 짧은 transition. 무거운 JS 계산을 worklet 안에서 하지 말 것(UI 스레드 블록).

### 5. 스타일 — NativeWind v4

```tsx
import { View, Text, Pressable } from 'react-native';

<Pressable className="active:opacity-70 rounded-2xl bg-violet-600 px-4 py-3">
  <Text className="text-base font-medium text-white">저장</Text>
</Pressable>
```

`global.css` 입력 + `metro.config.js` 의 `withNativeWind(config, { input: './global.css' })` 필요. 색은 tinted-neutral(약간 violet/blue tint), 전체 3색 이내(accent+text+bg). pure black/gray 금지.

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

Android 는 `app.json` 의 `android.softwareKeyboardLayoutMode: "resize"`(2nd-B 가 이미 설정) 로 대부분 해결.

### 7. 플랫폼별 파일

```
Button.tsx          # 공통
Button.ios.tsx      # iOS 전용 (자동 선택)
Button.android.tsx  # Android 전용
Button.web.tsx      # expo web 전용
```

코드 분기는 `Platform.OS === 'ios'` 보다 파일 분리가 깔끔. import 는 확장자 없이 `import Button from './Button'`.

### 8. Hermes 동적 import 함정 (2nd-B 실제 사고)

증상: `expo run:android` 또는 EAS 빌드가 **"Invalid expression encountered"** (Hermes bytecode 컴파일 실패). 원인: `@supabase/supabase-js`(OTEL 로더), `pdfjs-dist`(fake-worker) 등이 exports map 에서 **런타임 값으로 `import()`** 하는 ESM 변형을 노출 → Metro 가 정적 변환 못 함 → 번들에 살아남아 Hermes 가 거부.

해결(`metro.config.js`): 패키지 exports 맵 해석을 끄고 CJS/UMD 폴백:

```js
const { getDefaultConfig } = require('expo/metro-config');
const { withNativeWind } = require('nativewind/metro');
const config = getDefaultConfig(__dirname);

// Hermes 가 거부하는 동적 import() 회피 — exports map 대신 main/react-native/browser 필드 사용
config.resolver.unstable_enablePackageExports = false;

module.exports = withNativeWind(config, { input: './global.css' });
```

pdfjs 워커 잔여 이슈는 `patch-package`(2nd-B 의 `postinstall: patch-package`) 로 봉합. 로컬 `npx expo export` 로 먼저 검증한 뒤 EAS 에 태운다(EAS 크레딧/시간 절약).

## 검증 (verification)

```bash
# 1) 정적 — 2nd-B 의 verify 게이트 통과 필수 (push/merge 전)
npx expo install --check        # 0 mismatch
npx expo-doctor                 # 0 issue
npm run type-check              # tsc --noEmit
npm run lint

# 2) 번들이 Hermes 에서 컴파일되는지 — EAS 안 태우고 로컬 선검증
npx expo export --platform android    # 성공 = Invalid-expression 없음

# 3) 라이브 동작 (택1)
npm run web                                   # 빠른 UI/스크린샷
npx expo run:android                          # 에뮬 Pixel_9_Pro_XL (adb reverse 8081 필요)

# 4) EAS 빌드 프로필 검증
npx eas build --profile preview --platform android --local   # 또는 클라우드
npx eas build --profile production --platform ios            # 스토어용
npx eas submit --profile production --platform ios
```

성능 예산:
- 리스트 스크롤 60fps 유지(Reanimated/FlashList devtools 의 dropped-frame 0 목표)
- 이미지: `expo-image` + `recyclingKey`, 원본 풀해상도 직접 렌더 금지(`image-manipulator` 로 리사이즈)
- JS 번들 초기 화면 < 화면당 의미 있는 코드만(무거운 모듈은 라우트 단위 lazy)

## Anti-patterns

- ❌ 긴 리스트에 `FlatList`/`ScrollView+map` → FlashList v2 로
- ❌ FlashList v2 에 `estimatedItemSize` 남김 → 제거(v2는 자동)
- ❌ New Architecture 끄고 FlashList v2/Reanimated 4 → 런타임 크래시
- ❌ Reanimated 4 에서 `reanimated/plugin` 사용 → `react-native-worklets/plugin` (그리고 항상 last)
- ❌ `runOnJS` import 깨짐 방치 → R4 는 `scheduleOnRN`(`react-native-worklets`)
- ❌ worklet 안에서 무거운 JS 연산 → UI 스레드 블록, 프레임 드랍
- ❌ bounce/elastic easing → 부드러운 `withTiming`/`withSpring`
- ❌ RN `Image` 로 리스트 썸네일 → `expo-image` + `recyclingKey`(잔상)
- ❌ `GestureHandlerRootView` 여러 군데/누락 → 루트 1회만
- ❌ EAS 에 바로 태워서 Hermes 에러 디버깅 → `expo export` 로 로컬 선검증
- ❌ 버전 mismatch 방치 → `expo install --check` 로 SDK 정합 맞추기

## Related skills

- `/app-platform-selector` — 네이티브로 갈지 결정 (이 skill 의 선행)
- `/vercel-react` — 웹 React (별개 트랙)
- `/design-system-keeper` — 색/타이포/모션 토큰
- `/design-review` · `/ios-qa` — 시각·실기기 QA
- `simon-tdd` — 컴포넌트/로직 테스트 (jest)
- `app-dev-orchestrator` — 구현 단계에서 호출
