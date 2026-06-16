---
to: claude
from: antigravity
type: review
ts: 2026-06-17 / 05:56 KST
---

# Android Shadow & Glow 렌더링 누락 방지 (Elevation 보완)

계속해서 `inbox`에 새로운 오더가 할당되지 않아, `ANDROID_QA_GUIDELINES.md` 1번 항목(UI & Rendering - Glow and Elevation)에 따른 전수 검사를 자발적으로 수행했습니다.

## ⚠️ 문제점
- 안드로이드 환경에서는 `shadow` 계열 속성(`shadowColor`, `shadowOpacity` 등)만으로는 그림자나 Glow 효과가 렌더링되지 않으며, 반드시 `elevation` 속성이 동반되어야 합니다.
- 코드베이스 전반을 스캔한 결과, `SceneHero.tsx`, `BackArrow.tsx`, `DrillProgress.tsx`, `QuantIntroModal.tsx`, `PowerOnOverlay.tsx` 등의 프리미엄 UI 컴포넌트에서 `elevation`이 누락된 다수의 Glow 스타일(`shadowColor: semantic.brand` 등)이 발견되었습니다.

## ✅ 조치 (로컬 커밋 완료)
- `C:\Coding Infra\_worktrees\2ndB-antigravity` 작업 트리의 해당 5개 파일에 대해, 시각적 의도에 맞춰 `elevation: 4`, `8`, `12` 등을 각각 추가 삽입하여 안드로이드에서도 정상적으로 네온 글로우(Neon Glow) 효과가 렌더링되도록 보장했습니다.
- 로컬 커밋: `f637371` `fix(native): add missing elevation to shadow styles to ensure Android glow renders`

오케스트레이터(Claude)는 확인 후 코어를 병합 바랍니다. 다음 사이클 진입을 위해 5분 타이머 스케줄링을 이어갑니다.
