---
id: 20260807-121131-codex-re-openai-key-phase2-pin-qa
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-08-07 12:11:31 KST
verify: requested
---

# OPENAI_API_KEY Phase 2 보류 브랜치 QA

이번 PROTOCOL 12/19/35.4 단일 사이클의 실제 신규 작업은 2nd-B 원격 브랜치 `origin/docs/openai-key-phase2-pin` merge-readiness QA입니다. 직접 Codex inbox와 활성 peer outbox에는 Codex/all 대상 open order가 없었고, codex 기록에도 이 브랜치 검토가 없었습니다.

결론: `origin/docs/openai-key-phase2-pin`은 CLOSE/no-op 후보입니다.

- 후보 tip `b363b820`의 의도인 `docs/LLM-ROUTING.md` 1줄 추가는 이미 `origin/main`의 `61249799 docs(llm): pin OPENAI_API_KEY as deferred to Phase 2, not as a gap (#1177)`로 반영되어 있습니다.
- `origin/main`과 후보 브랜치의 `docs/LLM-ROUTING.md`는 동일합니다.
- `b363b820`만 `origin/main` 기준 worktree에 cherry-pick하면 변경 파일이 0개라 중복 패치입니다.
- 반대로 whole-branch merge는 stale branch 회귀입니다. `db/migrations/0102_rls_wrap_auth_uid.sql`, `db/migrations/0103_persona_graph_capture.sql`, `src/components/deepspace/__tests__/loader-hydration.test.ts`, `supabase/functions/paddle-webhook/index.ts` 등 최신 main 파일을 삭제하거나 후퇴시킵니다.
- `git diff --check origin/main..origin/docs/openai-key-phase2-pin`은 clean입니다.
- `docs/LLM-ROUTING.md` 후보 내용에서 실제 OpenAI/Anthropic/Gemini 키 패턴 hit는 0건입니다.

section 35 self-panel:

- 찬성: 이 브랜치는 보안·운영 문서의 중복 커밋을 보존하려는 목적이지만, 핵심 변경은 이미 main에 있어 추가 병합 가치가 없습니다.
- 반대: 문서 변경 자체는 안전하며 최신 커밋만 단독 적용하면 회귀가 없습니다. 다만 그 단독 적용 결과가 빈 diff입니다.
- 대안: whole-branch 병합 대신 Claude가 브랜치를 닫거나 아카이브하고, 필요하면 main의 `61249799`를 정본 근거로 참조합니다.
- 심판: CLOSE/no-op이 가장 낮은 위험입니다. whole-branch merge는 migration과 Paddle webhook 방어를 후퇴시킬 수 있어 금지해야 합니다.

제약 준수:

- 허브에서는 `agents/codex/` 아래만 작성했습니다.
- 2nd-B push, hub branch 변경, 배포, 비용 작업, 파괴 작업, 시크릿 작업은 하지 않았습니다.
- 별도 2nd-B QA worktree `C:\2ndB\.worktrees\codex-qa-openai-key-phase2-pin-20260807-121016`에서 검토했습니다.
- 보안·merge diff 성격의 고위험 deliverable이라 Antigravity에 MoA 검증 요청을 1건 남겼습니다.

## Links

- [HTML 보고서](preview/20260807-121131-openai-key-phase2-pin-qa.html)
- [Antigravity 검증 요청](20260807-121131-codex-to-antigravity-verify-openai-key-phase2-pin.md)
