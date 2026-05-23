# Curated Skills — Stage 2 메인 노출 15개

> SimonK-stack 98 skill 중 *실제 사용 빈도 + 핵심 가치* 기반으로 선별한 메인 15개. SystemBlueprint v05 §6 Stage 2 (6/15~6/30) 큐레이션 계획의 사전 진입판.

나머지 83개는 *실험중·도메인 특화* 폴더로 격하 — 본 카탈로그에서 찾지 못한 작업이면 [전체 카탈로그](../README.md#skill-카탈로그--98개) 참조.

---

## 0. 통합 진입점 (1)

| Skill | 트리거 | 가치 |
|---|---|---|
| **`simonk`** | `simonK <task>` · `/simonK` · "한 번에 끝내줘" · "자율로 끝까지" | 단일 진입점, 6-Phase 자율 (Ambiguity → Plan → 병렬 Task → Verify → Auto push → Report). *다른 14개를 자동 호출.* |

---

## 1. Orchestrators — 작업 파이프라인 (3)

| Skill | 언제 | 결과물 |
|---|---|---|
| **`app-dev-orchestrator`** | "새 앱 만들자" | 21단계 신규 앱 파이프라인 (office-hours → plan → design → TDD → 보안 → ship → 배포 → 회고 → instincts) |
| **`dev-orchestrator`** | "기능 구현해줘" · "버그 고쳐줘" · "리팩토링" | 7단계 일상 개발 (진단→TDD→품질→리뷰→커밋) |
| **`security-orchestrator`** | "보안 점검" | 5단계 적대적 보안 감사 → 통합 리포트 |

---

## 2. 방법론 — 매 작업 base layer (4)

| Skill | 가치 |
|---|---|
| **`karpathy-guidelines`** | 4원칙 (가정명시/단순함/외과적변경/목표주도) — 모든 코딩 base behavior |
| **`simon-tdd`** | RED→GREEN→REFACTOR + Guard Mode — 새 feature/script 추가 시 |
| **`simon-worktree`** | git worktree 격리 — 병렬 Claude 세션 안전 |
| **`simon-instincts`** | 4 파일 누적 학습 (mistakes/patterns/korean/quirks) — 같은 실수 반복 방지 |

---

## 3. 리서치·디자인 — Slop 방지 (2)

| Skill | 언제 |
|---|---|
| **`simon-research`** | "리서치 해줘" — 외부 자료 의무화 + wiki 자동 누적 |
| **`simon-design-first`** | "디자인 만들어줘" · "UI 만들어줘" — AI slop 방지 + 레퍼런스 진단 (코드 작성 전 필수) |

---

## 4. 5/30 안드 앱 출시 직전 — 필수 4

| Skill | 언제 |
|---|---|
| **`payment-integrator`** | 결제 붙일 때 (Stripe/PortOne/RevenueCat + 웹훅 + 상태머신) |
| **`human-voice-guard`** | 사용자 대면 문구 — LLM tell 검출 + `voice-lint.sh` |
| **`release-notes`** | 패치 노트 — 개발자용(README) + 사용자용(스토어/배너) **분리** |
| **`viral-launch`** | 4채널 (인앱 / 인스타 / 커뮤니티 / 입소문) 복붙 산출물 |

---

## 5. 일상 운영 (1)

| Skill | 언제 |
|---|---|
| **`commit`** | "커밋해줘" — Conventional Commits 자동 |

---

## 6. SimonKWiki 운영 (3)

| Skill | 언제 |
|---|---|
| **`wiki-ingest`** | "인제스트해줘" · raw/에 새 자료 박을 때 — 3섹션 요약 → 4질문 → wiki 반영 |
| **`wiki-query`** | wiki 답할 만한 질문 — index.md 우선 + wikilink 인용 |
| **`wiki-lint`** | "wiki 점검" — 8-체크 정합 (자동 적용 X, 제안만) |

---

## Anti-pattern — 이럴 땐 쓰지 마세요

| 상황 | skill 호출 X | 대신 |
|---|---|---|
| 단일 typo 수정 | `simonK` 또는 `dev-orchestrator` | 직접 Edit |
| "X가 뭐야" 정보 lookup | 어떤 skill도 X | Read/Grep 직접 |
| 대화·취향 의견 | `simon-design-first` X | 직접 대답 |
| 사용자 PR 자동 머지 | 어떤 skill도 X | 사용자 명시 OK 받기 (글로벌 CLAUDE.md 정책) |
| `.env` 파일 수정 | 어떤 skill도 X | STOP (글로벌 정책) |
| `rm -rf` · `git reset --hard` · force push to main | 어떤 skill도 X | STOP + 사용자 확인 |

---

## 도메인 특화 — 별도 카탈로그 (격하 83개)

Stage 2 메인에서 격하된 도메인별 skill (필요 시 명시 호출):

| 도메인 | Skill 예시 |
|---|---|
| **수익화·결제 advanced** | `monetization-planner` · `subscription-manager-selector` · `global-payment-planner` · `pink-tax-advisor` · `ad-monetization` |
| **인증·권한** | `auth-builder` · `authz-designer` · `security-checklist` · `paid-api-guard` |
| **그로스·분석** | `aarrr-growth-planner` · `pmf-analyzer` · `aha-moment-optimizer` · `analytics-integrator` · `tag-manager-integrator` · `growth-engine` · `store-launcher` |
| **아키텍처** | `stack-architect` · `app-platform-selector` · `db-selector` · `deploy-configurator` · `tech-preference-tracker` |
| **품질 advanced** | `revenue-scenario-tester` · `code-health-guard` · `consistency-guard` |
| **Strategy/Exit** | `sprint-optimizer` · `exit-strategy-planner` |
| **Gstack 36개** (vendored) | `office-hours` · `plan-ceo-review` · `plan-eng-review` · `plan-design-review` · `plan-devex-review` · `autoplan` · `design-consultation` · `design-shotgun` · `design-review` · `design-html` · `qa` · `qa-only` · `benchmark` · `health` · `codex` · `ship` · `land-and-deploy` · `canary` · `setup-deploy` · `document-release` · `cso` · `careful` · `guard` · `freeze` · `unfreeze` · `retro` · `investigate` · `browse` · `learn` · `devex-review` · `checkpoint` · `pair-agent` · 외 4개 |
| **kepano Obsidian 5개** (vendored) | `defuddle` · `json-canvas` · `obsidian-bases` · `obsidian-cli` · `obsidian-markdown` |
| **개발 보조** | `debug` · `explain` · `refactor` · `review` · `test-gen` · `nextjs-optimizer` · `stitch-design-flow` |
| **메타** | `skill-gen-agent` · `context-guardian` · `project-context-md` · `agent-delegate` |

---

## 사용 흐름 (Stage 2 추천)

```
일반 작업 → simonK <목표>           ★ 90% 흐름
명확한 작업 → 메인 15개 중 직접 호출
도메인 특화 → 격하 83개 중 호출
완전 새로운 작업 → skill-gen-agent (새 skill 작성)
```

---

## 다음 (Stage 3 진입 시, 11월~)

- 6개월 실사용 데이터 분석 → 실제 호출 빈도 기반 재선별
- 글로벌 영어 README 풀 작성
- HackerNews Show HN · r/ClaudeAI 노출
- 27Y Q1 Simon-ohmo 시그니처 발표 시 통합

---

*2026-05-25 작성 (Phase 3 사전 진입판) — Stage 2 정식 발행은 6/15~6/30. 본 docs는 v0.1, 실사용 데이터 누적 후 v1.0.*
