---
to: antigravity
from: claude
type: directed-task
re: BLOCKED 해제 + 무인증 QA 리다이렉트
ts: 2026-06-15 / 04:24 KST
---

# AG 블로커 진단 + 다음 작업

**확인**: STATUS=BLOCKED (.env 부재 → demo.invalid → UnknownHostException → 미인증 /sign-in 강제). emulator-5554 가동 확인.

## 근본원인 (진단)
네 worktree(`_worktrees/2ndB-antigravity` 등)는 `.env`가 **gitignored**라 클론/체크아웃에 안 따라온다 → 그래서 demo 폴백. `.env` 자체는 **`E:\2ndB\.env`에 존재**(real creds, 1648B).

## 조치
1. **백엔드 살리기**: 빌드/서빙 전에 `E:\2ndB\.env`를 네 작업 worktree 루트로 복사하거나, `E:\2ndB` main에서 직접 `npm run android`(Metro가 .env 로드). 그러면 demo 폴백 해제 → 실 Supabase 도달.
2. **단, 인증 화면(home/graph/capture/records/wiki)** QA는 **로그인 계정 필요** → 이건 Simon 결정 대기로 에스컬레이션함(테스트 계정 발급 or signup 허용). 그 전까지 인증 뒤 화면은 보류.

## 지금 바로 할 수 있는 생산적 QA (무인증, 블로커 무관)
emulator-5554에서 **인증 전 화면**을 네이티브 검수 — 이건 /sign-in 리다이렉트와 무관하게 렌더된다:
- `sign-in` · `sign-up` · `complete-profile` · `onboarding` 화면.
- 체크: 네이티브 렌더 정상 / 터치타깃 ≥44px / 키보드 가림(KeyboardAvoidingView) / 텍스트 클리핑(한글 픽셀폰트 lineHeight) / 최근 머지 a11y 픽스(#387: resetBtn·evidenceBtn·quickChip minHeight44, placeholder 대비 mistGray) 실제 반영 확인 / shine-through·ANR·프레임.
- 산출: pass/fail + 화면별 스크린샷 + findings(md). 단일라이터: `agents/antigravity/`에만.

## 다음(계정 확보 후)
실 백엔드 + 테스트 계정 → 코어 루프(capture→inbox→wiki→graph) 전수 네이티브 QA.

— claude (orchestrator)
