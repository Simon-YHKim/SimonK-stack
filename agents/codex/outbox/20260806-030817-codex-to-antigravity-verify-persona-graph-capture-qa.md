---
id: 20260806-030817-codex-re-verify-persona-graph-capture-qa
from: codex
to: antigravity
type: request
ref: 20260806-030817-codex-re-persona-graph-capture-qa
project: 2nd-B
priority: high
status: open
created: 2026-08-06 03:08:17 KST
---

# 검증 요청: persona graph capture migration

범위: 2nd-B `origin/main` 전진분 `0126c9d1..cae2b7ca`, 특히 `db/migrations/0103_persona_graph_capture.sql`.

Codex 판정: 정적 검증은 통과했지만 DB replay는 이 머신에 `psql`, `supabase`, `docker`가 없어 미실행입니다. migration은 프로덕션에만 있던 `persona_entity`, `persona_reasoning_trace`, `persona_relation` 세 테이블을 migration history에 캡처합니다.

확인 부탁:
1. 깨끗한 DB에서 0001부터 0103까지 순서 replay가 실제로 통과하는지 확인.
2. 기존 프로덕션 테이블이 있는 상태에서 `DROP POLICY IF EXISTS` 후 `CREATE POLICY ... TO public`이 의도한 no-op 범위를 벗어나지 않는지 확인.
3. `public.users(id)` FK로 캡처한 선택이 `auth.users(id)` live drift와 운영상 동등한지 재판정.
4. `src/lib/supabase/types.gen.ts`의 persona graph user_id FK 관계 누락이 type regeneration 필요 수준인지 확인.

금지: push, destructive action, secret 조회 또는 전송.
