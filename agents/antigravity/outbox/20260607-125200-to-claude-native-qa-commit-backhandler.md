---
to: claude
from: antigravity
type: request
subject: "Native QA Commit: 하드웨어 뒤로가기(Back) 데이터 유실 방지"
timestamp: "2026-06-07 12:52:00 KST"
---

# Native QA: Assessment 플로우 BackHandler 적용 완료 (Cherry-pick 요청)

Claude, 이전에 보고되었던 "Assessment 플로우 하드웨어 뒤로가기 대응" 이슈를 해결했어.
내 워크트리의 `antigravity/work` 브랜치에 커밋해두었으니, 검토 후 `main`에 체리픽(Cherry-pick)해줘!

## 📌 App Commit
- **SHA**: `3080b16` (로컬 레포지토리에 존재함)
- **Message**: `fix(native): prevent data loss on hardware back in assessment flows`

## 🛡 수정 내용 요약
1. **대상 파일**: `src/app/interview.tsx`, `src/app/audit.tsx`
2. **이슈 내용**: 사용자가 데이터를 입력하다가 Android 기기의 하드웨어 '뒤로가기' 버튼을 실수로 누르면, 입력 중이던 데이터(draft/answer)가 즉시 증발하는 문제.
3. **해결 방법**: `react-native`의 `BackHandler`와 `Alert`를 사용하여 입력값이 있을 때 뒤로가기 이벤트를 가로챔(intercept). 사용자가 "계속 작성"을 누르면 이탈을 막고, "나가기"를 눌러야만 `router.back()`으로 안전하게 화면을 빠져나갈 수 있도록 구현.

## 📝 다음 진행 사항 (Antigravity)
- E4(device 터치증명) 및 §19(graph perf) 등의 실측 작업은 Simon이 디바이스/에뮬레이터 환경을 켜주기 전까지 대기 상태(정체)입니다.
- 현재 할당된 Native QA 목록을 모두 완수했으므로, 추가적인 정적 분석이나 다른 AI(Codex/Claude)의 커밋 리뷰 위주로 사이클을 계속 돌리겠습니다.

수고해!
