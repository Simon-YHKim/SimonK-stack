---
id: 20260605-182300-antigravity-to-claude-android-runtime-issues-fyi
from: antigravity
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-06-05 18:23:00 KST
---

## Context
사용자 직접 지시로 2nd-B 앱의 안드로이드 실행(런타임) 시 예상되는 구조적·UI적 문제점을 스캔했습니다. 안드로이드 기기 QA 전 선제적 조치(또는 집중 검수 포인트)로 활용하시기 바랍니다.

## Findings (Android 잠재 이슈)

### 1. KeyboardAvoidingView 충돌 및 하단 가림 현상
- `capture.tsx`, `sign-in.tsx`, `jarvis.tsx` 등 수많은 입력 폼 화면에서 `<KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined}>` 패턴을 사용 중입니다.
- **리스크**: 안드로이드의 `windowSoftInputMode`가 `adjustResize`로 동작하고 있을 경우 `KeyboardAvoidingView`와 이중으로 간섭하거나, 반대로 뷰를 제대로 밀어올리지 못해 하단 확인 버튼이 키보드에 가려지는(Unclickable) 현상이 잦습니다.

### 2. 하드웨어 백버튼 (Hardware BackHandler) 누수
- `components/premium/feedback.tsx` 등에서 `PremiumBottomSheet`나 `Modal`을 띄우고 있습니다.
- **리스크**: 안드로이드는 시스템 하드웨어 백버튼이 존재합니다. 커스텀 바텀시트나 모달이 열려 있을 때 물리 백버튼을 누르면 시트가 닫히는 대신 Navigation이 뒤로 가버려 앱 흐름이 끊기거나 종료되는 문제가 흔하게 발생합니다. 커스텀 모달 내 `BackHandler` 연동이 필수입니다.

### 3. SafeArea & 투명 시스템 바 (Translucent Navigation)
- `index.tsx` 등에서 `useSafeAreaInsets()`를 사용하고 있습니다.
- **리스크**: Expo의 기본 안드로이드 세팅에서는 하단 소프트키 영역(Navigation Bar)을 그릴 때 Insets 처리가 OS 버전에 따라 달라지거나, 투명화 설정이 꼬여서 `PremiumTabBar`가 하단 소프트 버튼 영역과 겹쳐 눌리지 않을 수 있습니다.

### 4. 폰트 줄바꿈 및 상하단 잘림 (Font Line-height/Clipping)
- 이전 진단과 동일. `Pretendard` 시스템 폰트가 안드로이드 기기에 내장되어 있지 않으므로 `sans-serif`로 강제 대체됩니다. 이때 한글 텍스트의 상하 패딩(Ascender/Descender) 계산이 달라져 버튼 내 텍스트 정렬이 어긋나거나 잘릴 수 있습니다.

## Recommendation
Claude, 위 항목들은 코드를 보완해야 하는 부분입니다. 특히 1, 2번은 안드로이드 빌드 직후 가장 흔한 크래시/UX 결함이므로 구현부 코드 점검 후 필요하다면 수정 브랜치로 반영해 주세요.
