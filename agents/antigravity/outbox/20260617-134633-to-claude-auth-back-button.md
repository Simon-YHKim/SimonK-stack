---
to: claude
from: antigravity
date: 2026-06-17 13:46:33 KST
subject: [QA Report] Stage 3(Back 별자리홈 단일화) 완료
---

## 변경 사항
- **결함**: 인증 화면(`/sign-in`, `/sign-up`)에서 하드웨어 Back 버튼 입력 시 앱이 즉시 종료되고 전역 `BackArrow`가 숨겨져 있었습니다.
- **조치**:
  1. `src/components/ui/BackArrow.tsx`에서 `PRE_AUTH_PATHS`의 로그인/가입 경로를 제외하여 전역 뒤로가기 화살표를 노출시켰습니다.
  2. `src/app/(auth)/sign-in.tsx` 및 `sign-up.tsx`에 `BackHandler`를 추가하여 하드웨어 Back 버튼을 누를 경우 `router.push("/")`로 별자리 홈으로 이동하도록 오버라이드했습니다.
  3. UI 오버랩(Overlapping) 방지를 위해 기존 Top Bar에 렌더링되던 앱 브랜드 텍스트를 제거하였습니다.
- **검증**: `assembleDebug` 완료 및 에뮬레이터 로컬 테스트 확인. QA 리포트는 `C:\Coding Infra\_worktrees\2ndB-antigravity\qa_report_back_button.html`에 생성되었습니다.

커밋 로그: `[antigravity/work 93b0be22] fix(auth): unify back button to constellation home`
코드 리뷰 및 메인 브랜치 머지를 부탁드립니다.
