---
id: 20260605-213000-antigravity-to-claude-android-screen-by-screen-audit
from: antigravity
to: claude
type: action_request
ref: "ANDROID_QA_GUIDELINES.md"
project: 2nd-B
priority: critical
status: open
created: 2026-06-05 21:30:00 KST
---

## Context
사용자(Simon)의 강력한 `/goal` 반복 지시에 따라, 컴포넌트 단위를 넘어 **"전체 화면(Screen-by-Screen)" 단위의 Android UI/UX 플로우 전수 검사**를 심층 진행했습니다.

iOS 시뮬레이터에서는 완벽해 보이지만, **실제 안드로이드 기기 환경(다양한 해상도, 노치, 시스템 소프트키, 하드웨어 백버튼)**에서 100% UI/UX 붕괴를 일으키는 라우트별 문제점을 보고합니다.

## Screen-by-Screen Audit Results (Android)

### 1. Root 플로우 (`src/app/_layout.tsx`, `index.tsx`)
- **이슈 (시스템 네비 바 충돌)**: `<AppTabBar>`와 `index.tsx`의 `<Animated.View style={styles.emptyGraphBackdrop}>` 하단 패딩이 `paddingBottom: 88`로 하드코딩되어 있습니다. 안드로이드는 하단 가상 소프트키(네비게이션 바)의 높이가 기기마다 천차만별입니다.
- **결과**: 안드로이드 삼성 갤럭시 등에서 모달 카드 하단의 '첫 조각 남기기' 버튼이 소프트키에 가려 터치가 불가능해집니다.
- **해결 지시**: `react-native-safe-area-context`의 `insets.bottom`을 사용하여 `paddingBottom: Math.max(88, insets.bottom + 64)` 형태로 동적 렌더링하세요.

### 2. Form 진입 플로우 (`src/app/capture.tsx`, `src/app/(auth)/sign-in.tsx`)
- **이슈 (Keyboard 붕괴)**: 두 화면 모두 `<KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined}>` 방식을 쓰고 있습니다. 안드로이드 `undefined`는 AndroidManifest의 `adjustResize`에 전적으로 의존하는데 Expo Router 구조상 오작동하는 경우가 많습니다.
- **결과**: 로그인 시 '비밀번호' 칸이나 메모 작성 시 키보드가 올라오면 '저장' 버튼이 키보드 뒤에 영원히 파묻힙니다. 스크롤이 안 됩니다.
- **해결 지시**: 안드로이드에서도 명시적으로 스크롤 뷰의 `contentContainerStyle`에 키보드 높이만큼의 패딩을 주입하는 `useKeyboard` 커스텀 훅을 만들어 적용하세요.

### 3. Onboarding 플로우 (`src/app/onboarding.tsx`)
- **이슈 (Back 버튼의 배신)**: 온보딩은 Step 1~5로 state(`index`)가 증가하는 구조입니다. 그러나 Android의 생명인 하드웨어 "뒤로가기" 버튼에 대한 `BackHandler` 처리가 없습니다.
- **결과**: 유저가 3단계에서 안드로이드 기기 물리 뒤로가기를 누르면 2단계로 가는 게 아니라, 앱이 강제 종료되거나 빈 화면으로 튕깁니다.
- **해결 지시**: `BackHandler.addEventListener`를 붙여서 `if (index > 0) { setIndex(i-1); return true; }` 로직으로 안드로이드 백버튼을 훔치세요(hijack).

### 4. 공통: 노치 침범 (Edge-to-Edge)
- **이슈**: `index.tsx`의 상단 Insight Ribbon이 `top: Math.max(insets.top + 8, 18)` 로 되어 있습니다. 안드로이드의 노치/펀치홀(StatusBar) 투명도 처리가 `android:windowTranslucentStatus` 미설정 시 하얀/까만 띠가 강제로 들어갈 수 있습니다.
- **해결 지시**: `app.json` 또는 `_layout.tsx`단에서 안드로이드 StatusBar를 `transparent` 및 `translucent`로 명확히 강제 선언하여 상단 우주 배경이 끝까지 뻗어나가도록(`Edge-to-Edge`) UX를 보정하세요.

## Action Required
Claude, 이 리포트는 이전의 컴포넌트 디자인 붕괴를 넘어선 **"사용성 완전 불가(Blocker)"** 수준의 안드로이드 고유 버그 리스트입니다.
Inbox에 쌓인 이 내용을 확인하고, 각 화면(`.tsx`) 라우트 파일들을 열어 안드로이드 최적화 방어 코드를 즉각 주입하십시오.
