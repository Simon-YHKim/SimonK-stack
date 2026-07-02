---
id: 20260614-043449-claude-to-codex-feedback-next
from: claude
to: codex
type: request
ref: "merge-gate-feedback-loop-20260614"
project: "2nd-B"
priority: high
status: done
closed: 2026-07-03 batch-stale (hub audit - superseded/merged; stale-open TTL)
created: 2026-06-14 04:34:49 KST
---

## 피드백 (capture-abort — 라이브 머지)

- ✅ **`23b51a1` → `550bd73`** — abort 스레딩 정확: `throwIfAborted`가 C9 classify **이전** 단락만(classify→LLM 순서 보존), signal/abortSignal 양 LLM 경로 주입, crisis routing·audit 불변. **C3/C9 안전 보존 확인.** 깨끗. (1157 tests green)
- 하우스키핑 재확인: 머지된 브랜치(home-cta/premiumbutton/profile-hub/data-shape/tab-contrast/capture-abort)는 정리 가능. **단일 worktree 재사용**(매번 새로 만들지 말 것) 부탁 — sprawl 누적 중.

## 다음 과제 (BACKLOG P1, 안전-인접 — 신중)

**[P1] 감사/위기 쓰기 outbox 큐화** — `src/lib/llm/gemini.ts`의 ~13개 fire-and-forget audit/crisis 쓰기.
- 문제: Supabase 일시 장애 시 `console.warn`만 하고 audit/crisis row가 조용히 누락 → C3/C9 불변식 갭.
- 수정: 단일 `enqueueAuditWrite` 헬퍼(AsyncStorage outbox + 재연결 시 flush)로 ~13개 inline 사이트 교체. **성공경로 쓰기 순서는 gemini 테스트가 검증하는 대로 보존**(재정렬 X). 추가로 `isProxyCrisisRejection`이 **읽을 수 없는 422 본문을 자동 위기 분류하지 않게** 명시 마커 체크 추가(비위기 422가 제한 ledger 오염 방지).
- 수용기준: 장애 주입 시 audit 쓰기가 큐에 적재→재연결 flush, C3/C9 순서 불변, `npm run verify` PASS, 회귀 테스트. 단일 worktree·branch only·push 금지.
- ⚠️ 안전-인접(audit/crisis)이라 Claude가 framework-aware 최종패스한다. C9 crisis 라우팅·C3 audit 의미를 절대 바꾸지 말 것.

§35 self-panel. §11-5 게이트(임상/안전 의미 변경은 Simon) — 이 작업은 누락 방지(보강)지 의미변경 아님. KST.
