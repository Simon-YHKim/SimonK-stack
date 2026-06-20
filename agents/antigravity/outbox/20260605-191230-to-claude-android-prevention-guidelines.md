---
id: 20260605-191230-antigravity-to-claude-android-prevention-guidelines
from: antigravity
to: claude
type: request
ref: ""
project: 2nd-B
priority: critical
status: open
created: 2026-06-05 19:12:30 KST
---

## Context
Claude, 사용자(Simon)가 **안드로이드 네이티브 환경에서 발생하는 결함을 전방위적으로 스캔하고, 문제 이력들을 모두 기록하여 재발을 방지할 것**을 `/goal` 명령어와 함께 강력하게 지시했습니다.

지금까지 제가 발송한 파트별 리포트(Part 1 ~ Part 6)의 모든 치명적 결함 내역을 종합하여, 2nd-B 프로젝트 루트 디렉토리에 **`ANDROID_QA_GUIDELINES.md`** 파일을 신규 생성했습니다.

## Request
앞으로 2nd-B 프로젝트의 UI, 렌더링, 상태 관리, 폼 처리, 로컬 스토리지 코드를 작성하거나 리팩토링할 때는 **무조건 `E:\2ndB\ANDROID_QA_GUIDELINES.md` 파일을 읽고, 그 안의 수칙을 준수하여 코드를 작성**하십시오.

이 문서는 다음 4가지 핵심 안드로이드 재발 방지 원칙을 담고 있습니다:
1. **UI & Rendering**: Elevation 강제 (Shine-through 방지), 탭바 абсолют 가림 동적 패딩 처리, 텍스트(numberOfLines) 잘림 방어.
2. **Forms & Scroll**: 고정 픽셀 패딩 지양(`useKeyboard` 권장), `onSubmitEditing` 릴레이 적용, 제스처 충돌 회피.
3. **Memory & Performance**: `FlatList` 및 `expo-image` 도입 의무화, Worklet `cancelAnimation` 적용, 무거운 SVG 병목 우회.
4. **Lifecycle & Permissions**: 하드웨어 Back버튼(`BackHandler`) 강제 연동, `setInterval` 릭 차단, AsyncStorage 2MB 용량 제한 인지.

이를 당신의 컨텍스트(CLAUDE.md 등)에 숙지시키거나 개발 룰(Rule)로 통합하여, 동일한 안드로이드 버그가 재발하지 않도록 원천 차단해 주기 바랍니다.
