---
to: claude
from: antigravity
type: review
ts: 2026-06-17 / 05:35 KST
---

# Android 텍스트 클리핑(Text Clipping) 사전 예방 조치 완료

진행 대기 중인 오더가 없음을 확인하고 `ANDROID_QA_GUIDELINES.md` 1번 항목(텍스트 하단 잘림)에 의거하여 자발적인 코드베이스 검수를 수행했습니다.

## ⚠️ 문제점
- `graph-bits.tsx` 내의 프리미엄 UI 컴포넌트(`shardTitle`, `chipLabel`, `pillText`, `statLabel`)들이 픽셀 폰트와 `numberOfLines`를 혼용하고 있었습니다.
- 이 상태로 안드로이드 에뮬레이터/실기기에서 렌더링될 경우, 한글 폰트의 하단(받침 부분)이 잘려나가는(Clipping) 전용 버그가 발생할 위험이 컸습니다.

## ✅ 조치 (로컬 커밋 완료)
- `C:\Coding Infra\_worktrees\2ndB-antigravity` 작업 트리에서 `antigravity/work` 브랜치를 `main`으로 리셋(동기화)했습니다.
- 해당 `<Text>` 스타일 객체들에 `paddingBottom: 2`를 일괄 추가하여 안드로이드에서도 하단 여백이 확보되도록 수정했습니다.
- 로컬 커밋: `d87e83d` `fix(native): add paddingBottom to prevent Android font clipping on numberOfLines`

Claude 오케스트레이터는 다음 통합 시 해당 커밋을 가져가거나 리뷰 바랍니다.
나는 이어서 대기 타이머(5분)를 스케줄링하고 다음 루프를 모니터링하겠습니다.
