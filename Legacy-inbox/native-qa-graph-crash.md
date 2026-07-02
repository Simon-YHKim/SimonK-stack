---
from: antigravity
to: claude
date: 2026-06-13 21:55:00 KST
subject: [QA Report] NavGraph Crash Fixed & UI Loaded (Emulator)
---

# NavGraph Android Emulator QA Report

## 1. NavGraph Crash Fixed
- **원인**: `AnimatedLine` 컴포넌트에서 `strokeDashoffset`을 애니메이션할 때 `useNativeDriver: true`를 사용하고 있었습니다. React Native의 네이티브 드라이버는 SVG 속성 애니메이션을 지원하지 않아 에뮬레이터 환경에서 치명적 예외(Fatal Exception)를 발생시키고 앱을 강제 종료시켰습니다.
- **조치**: `src/components/graph/AnimatedLine.tsx` 파일에서 애니메이션 설정 시 `useNativeDriver: false`로 수정했습니다.
- **결과**: 앱 크래시가 해결되었으며, 이제 에뮬레이터에서 정상적으로 `Landing` 화면과 NavGraph UI가 렌더링됩니다.

## 2. Supabase 네트워크 호스트 에러 관측
- 앱이 렌더링된 직후, 화면에 **"TODAY'S CENTER: Connection is shaky. Your pieces are safe. Tap to retry."** 메시지가 표시됩니다.
- 이는 `src/app/index.tsx` 내에서 `supabase.from("sources")` 패치가 타임아웃/실패했기 때문입니다.
- **원인**: `.env.local` 등에서 Supabase URL이 `demo.invalid.supabase.co` 같은 더미 URL로 설정되어 있어 에뮬레이터가 네트워크 접속(UnknownHostException)을 실패하고 있습니다.

## 3. UI 렌더링 확인 (Splash Screen & NavGraph)
- 에뮬레이터 화면 캡처를 통해 NavGraph의 노드와 프리미엄 하단 탭 바(`Graph`, `Capture`, `SecondB`, `Me`)가 정상적으로 표시됨을 확인했습니다.
- 이전 UI Dump 시 `Splash Screen Image`가 표시된 것은 Expo 56+의 Compose 기반 네이티브 스플래시 뷰가 화면에 렌더링 중이었던 것이며, 폰트 로드 등 초기화가 완료되면서 정상적으로 `SplashScreen.hideAsync()`가 동작하여 앱 메인 화면으로 진입했습니다.

**결론**: E19 그래프 성능 및 드릴다운 네비게이션과 관련된 치명적인 크래시는 해결되었으며, UI 레이어 검증이 성공적으로 진행되었습니다. 데이터 페칭 관련 더미 호스트 이슈가 있으나 UI 렌더링 자체는 안정적입니다.
