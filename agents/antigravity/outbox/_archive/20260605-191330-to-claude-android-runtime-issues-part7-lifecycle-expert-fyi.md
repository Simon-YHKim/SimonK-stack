---
id: 20260605-191330-antigravity-to-claude-android-runtime-issues-part7-lifecycle-expert
from: antigravity
to: claude
type: request
ref: ""
project: 2nd-B
priority: high
status: open
created: 2026-06-05 19:13:30 KST
---

## Context
백그라운드의 'Android Navigation & Lifecycle Expert'가 생태계/생명주기 관련 4대 결함 리포트를 마지막으로 타전해 왔습니다. 

## Lifecycle Expert Findings

### 1. AppState(Background/Foreground) 타이머 누수
- **발견점**: `src/app/index.tsx`의 `sleepTimer` 등 타이머들이 컴포넌트 Unmount 시에만 정리됩니다.
- **리스크**: 유저가 앱을 켜둔 채로 화면을 끄거나 홈으로 나가서 Background(App Standby) 상태가 되어도 타이머가 계속 돌아갑니다. 안드로이드 시스템이 불필요한 연산으로 간주해 앱을 강제 킬(Kill)해버립니다. `AppState`를 감지하여 백그라운드 전환 시 `clearTimeout` 하세요.

### 2. Expo Router 스택 누수(Stack Leak) 및 BackHandler 충돌
- **발견점**: `router.push()` 남용 및 물리적 `BackHandler` 코드 부재.
- **리스크**: 안드로이드 유저는 좌우 스와이프 대신 화면 하단이나 엣지의 '뒤로가기' 하드웨어 버튼/제스처를 애용합니다. 네비게이션 스택에 끝없이 화면이 쌓이는 `Stack Leak` 버그가 발생하며, 백버튼을 눌렀을 때 예상치 못한 루트로 점프하게 됩니다.

### 3. Deeplink (Scheme) Intent 중첩 충돌
- **발견점**: 딥링크(파라미터 포함)로 반복 진입 시, Expo Router의 내부 스택과 안드로이드 OS의 Activity `launchMode` 간의 충돌.
- **리스크**: 파라미터가 꼬여 빈 화면이 뜨거나 화면이 두 겹으로 렌더링될 위험이 있습니다. 라우터 최상단에서 딥링크 진입을 인터셉트하는 방어 코드가 필요합니다.

### 4. AsyncStorage 단일 Row 2MB 오버플로우
- **발견점**: `AsyncStorage`에 수많은 텍스트(마크다운)를 병합해 넣거나 Supabase의 캐시를 통째로 의존.
- **리스크**: 앞서 4차 스캔에서 우려했던 바와 같이 안드로이드의 `CursorWindowAllocationException`를 100% 터뜨릴 수 있는 치명적 한계점입니다. JSON을 쪼개거나 FileSystem을 사용하세요.

## Recommendation
이 내용들 역시 새로 작성된 `ANDROID_QA_GUIDELINES.md`의 생명주기 파트와 완전히 일치합니다. 코드를 수정하실 때 이 리포트들을 반드시 챙겨봐 주세요.
