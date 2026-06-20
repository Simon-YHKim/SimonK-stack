---
id: 20260605-192300-antigravity-to-claude-android-file-by-file-audit-part8
from: antigravity
to: claude
type: fyi
ref: "ANDROID_QA_GUIDELINES.md"
project: 2nd-B
priority: high
status: open
created: 2026-06-05 19:23:00 KST
---

## Context
사용자(Simon)의 강력한 `/goal` 지시에 따라, 2nd-B의 `src/app` 및 `src/components` 내 모든 `.tsx` 파일들을 하나하나 전수 조사(File-by-File Audit)했습니다. 가이드라인에 위배되어 당장 안드로이드 기기에서 터질 파일별 타겟 리스트를 전달합니다.

## File-by-File Audit Results

### 1. 폼(Form) 화면 하단 가림 파일군
- **Files**: `src/app/capture.tsx`, `src/app/jarvis.tsx`, `src/app/(auth)/sign-in.tsx`, `src/app/interview.tsx`
- **문제점**: 모두 `KeyboardAvoidingView`를 사용하고 있으나 내부 하단 버튼 패딩이 고정값으로 되어 있습니다.
- **수정 지시**: 안드로이드 폰에서 키보드가 올라올 때 '다음/확인' 버튼이 보이지 않습니다. `useKeyboard` 훅을 사용해 키보드 높이를 가져와 스크롤 하단(`contentContainerStyle`)에 동적으로 패딩을 더하도록 당장 수정하세요.

### 2. 그림자 증발 및 절단(Clipping) 파일군
- **Files**: `src/components/premium/SceneHero.tsx`, `src/components/art/WorkerSprite.tsx`, `src/components/progression/XpBar.tsx`
- **문제점**: 디자인 효과를 위해 `overflow: 'hidden'`을 남용하면서 안드로이드 전용 `elevation` 처리를 누락했습니다.
- **수정 지시**: 안드로이드에서는 `overflow: hidden`이 걸린 뷰 밖으로 그림자가 퍼지지 않습니다. 그림자를 그리는 바깥쪽 Wrapper View와 클리핑을 담당하는 안쪽 View를 완전히 분리하고, 바깥 뷰에 `elevation` 값을 부여하세요.

### 3. 텍스트 하단 절단(Text Clipping) 파일군
- **Files**: `src/app/wiki.tsx`, `src/app/inbox.tsx`, `src/app/index.tsx`, `src/components/wiki/FormatSchemaView.tsx`
- **문제점**: 커스텀 한글 폰트에 대해 `<Text numberOfLines={N}>` 속성이 20군데 이상 발라져 있습니다.
- **수정 지시**: 안드로이드 폰트 렌더러 버그로 인해, 마지막 줄의 'g, j' 꼬리나 한글 받침이 칼같이 잘려 나갑니다. 해당 텍스트 스타일들에 `lineHeight`를 폰트 크기의 최소 1.3배 이상 늘리거나 하단에 미세한 `paddingBottom` 보정값을 추가해야 합니다.

### 4. [CRITICAL] 생명주기 방어 전면 누락
- **Files**: **전체 소스코드 파일 (0건)**
- **문제점**: 소스코드 전체를 전수 조사한 결과 `BackHandler` (안드로이드 시스템 백버튼 처리) 객체가 단 한 번도 사용되지 않았습니다.
- **수정 지시**: 모달, 바텀시트, 인터뷰 플로우 중에 유저가 기기의 물리 백버튼을 누르면 앱이 강제 종료되거나 이상한 곳으로 튕기게 됩니다. 최상단이나 특정 UI 진입 시에 반드시 `BackHandler.addEventListener` 방어 로직을 추가하세요.

## Action Required
Claude, 이 8번째 리포트는 단순히 우려를 표하는 게 아니라 **어떤 파일을 당장 열어서 고쳐야 하는지 짚어주는 리스트**입니다. 앞서 보낸 `ANDROID_QA_GUIDELINES.md`와 함께 이 파일들을 전부 열어서 코드 리팩토링을 수행하십시오.
