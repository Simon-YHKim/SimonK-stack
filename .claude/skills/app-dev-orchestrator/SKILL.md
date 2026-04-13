---
name: app-dev-orchestrator
description: Use when the user asks to build a new app from scratch—"새 앱 만들자", "MVP 기획", "scaffold a new project", "처음부터 만들어줘", "let's build X"—and delegate the 21-stage pipeline (office-hours → research → plan → design → TDD → security → ship → deploy → retro → instincts) to Gstack and simon-stack skills. Produces a populated repo with CLAUDE.md, tests, security audit, and a first deploy. Do NOT use for bug fixes, refactors, or improving existing code—delegate to simon-tdd, investigate, or refactor instead.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.1.0
author: simon
---

# App Dev Orchestrator

새 앱을 처음부터 만들 때 발동하는 21단계 마스터 파이프라인. 각 단계는 Gstack 또는 simon-stack 스킬을 호출하고, 단계 간 산출물을 다음 단계에 전달한다.

## When to use

- 사용자가 "새 앱 만들고 싶어", "프로젝트 시작", "MVP 기획", "신규 서비스", "앱 만들자" 등의 요청을 한 경우
- 기존 코드 수정이 아닌 **zero-to-one** 상황
- 플랫폼이 명확히 지정되지 않았거나, 지정돼도 전체 라이프사이클 지원이 필요한 경우

**발동 안 되는 경우**: 버그 수정, 기존 기능 개선, 리팩토링, 단일 파일 작업 → 해당 전용 스킬 사용

## Workflow — 21 단계 파이프라인

### 단계 0. 인터뷰 (사용자 질문)

진행 전에 아래 6가지를 먼저 명확하게 잡아둔다. 이 중 하나라도 불분명하면 뒤의 플래닝이 공중에 뜬다:
1. **플랫폼**: 웹 / React Native / CLI / 하이브리드 / 데스크탑?
2. **타깃 사용자**: 누구? 얼마나 많나?
3. **GitHub 레포**: 기존 재사용 / 신규 생성? 비공개/공개?
4. **예산·스케일**: 개인·사이드 / MVP / 실사용자 100+ / 엔터프라이즈?
5. **필수 외부 API**: 결제, LLM, 지도, 이메일 등
6. **마감**: 급함 / 여유 / TBD?

답변을 `docs/kickoff-<YYYY-MM-DD>.md` 에 저장.

### 단계 1. `/office-hours` — YC 6문 forcing questions

> Gstack `/office-hours` 스킬 호출. 6가지 forcing question 으로 demand·상태quo·구체성·wedge·관찰·future-fit 검증.

### 단계 2. `simon-research` — 외부 리서치 선행

> `simon-research` 호출. 공식 문서·경쟁 제품 3개·레퍼런스 구현·기술 비교 → `docs/research/<date>-<topic>.md`.

### 단계 3. `/plan-ceo-review` — 10-star 스코프

> Gstack `/plan-ceo-review` (SCOPE EXPANSION / SELECTIVE / HOLD 모드 중 선택). 문제 재정의·야망 확장.

### 단계 4. `/design-consultation` — DESIGN.md 생성

> Gstack `/design-consultation`. 제품 톤·타이포·컬러·레이아웃·스페이싱·모션 시스템. `DESIGN.md` 산출.

### 단계 5. `stitch-design-flow` — 시안 프롬프트 3종

> simon-stack `stitch-design-flow` 호출. DESIGN.md 를 읽어 Stitch 웹 UI 에 붙여넣을 프롬프트 3개 생성 → 사용자가 Stitch(stitch.withgoogle.com)에서 수동 생성 → 결과 이미지 저장.

### 단계 6. `/design-shotgun` — 변형 탐색

> Gstack `/design-shotgun`. 여러 디자인 변형을 생성하고 비교 보드에서 피드백 수렴.

### 단계 7. 대형 플래닝

> 스코프가 큰 경우 Claude Code 의 UltraPlan 기능(code.claude.com/docs/en/ultraplan — CLI/웹의 내장 기능, skill 아님) 활용. 소·중 규모는 Gstack `/autoplan` 로 충분. 둘 중 선택.

### 단계 8. `authz-designer` — 인가 모델 선택

> simon-stack `authz-designer`. RBAC/ABAC/ReBAC 중 프로젝트 맞는 것 선택, DDL 스키마 생성. `docs/authz.md` 산출.

### 단계 9. API 설계 리뷰

> `paid-api-guard` SKILL 의 "API 설계 리뷰" 섹션 호출. REST/GraphQL/tRPC 선택, N+1 탐지, cursor 페이지네이션, ETag, OpenAPI 생성 전략.

### 단계 10. `/plan-eng-review` → `/autoplan`

> Gstack `/plan-eng-review` 로 엔지니어링 플랜 잠그고 `/autoplan` 으로 자동 리뷰 파이프라인 실행.

### 단계 11. 레포·환경 준비

체크리스트:
- [ ] GitHub 레포 생성 또는 기존 브랜치 확인
- [ ] `.env.example` 작성 (키 placeholder)
- [ ] `.gitignore` 에 `.env`, `node_modules/`, `dist/`, `.DS_Store`, `*.log` 포함 확인
- [ ] gitleaks pre-commit hook 설치: `pre-commit install` + `.pre-commit-config.yaml`
- [ ] README 초안·LICENSE 선택
- [ ] CI 워크플로 템플릿 (lint + test + build)
- [ ] `CLAUDE.md` 초안 작성 (프로젝트 컨텍스트)

### 단계 12. `simon-worktree` — 병렬 작업 격리

> simon-stack `simon-worktree` 호출. 병렬 Claude 세션 필요 시 `git worktree add` 로 분리.

### 단계 13. `simon-tdd` — RED-GREEN-REFACTOR 구현

> simon-stack `simon-tdd` 호출. 실패 테스트 먼저 → 최소 구현 → 리팩토링. Next.js 프로젝트일 경우 `nextjs-optimizer` 동시 호출 (있을 때만).

### 단계 14. `/design-review` → `/design-html`

> Gstack `/design-review` 로 시각적 QA (spacing / hierarchy / AI slop 탐지) → `/design-html` 로 production HTML/CSS 생성.

### 단계 15. `/qa` — QA 및 버그 수정

> Gstack `/qa` 표준 모드. 자동 테스트 + 버그 발견 시 원자적 커밋으로 수정.

### 단계 16. 보안 4단 감사

순차 실행:
1. simon-stack `security-checklist` (RLS / 구독 / RateLimit / 예산)
2. simon-stack `authz-designer` 감사 섹션
3. simon-stack `paid-api-guard` 6층 방어 점검
4. Gstack `/cso comprehensive` — 인프라·시크릿·공급망·LLM·CI/CD
5. Gstack `/codex challenge` — 적대적 리뷰

각 단계 발견 이슈는 원자 커밋으로 수정 후 재검증.

### 단계 17. `/benchmark` — 성능 측정

> Gstack `/benchmark`. Core Web Vitals · 페이지 로드 · 리소스 사이즈 baseline. 트렌드 추적.

### 단계 18. `/review` → `/ship`

> Gstack `/review` 로 PR 사전 리뷰 → `/ship` 으로 VERSION·CHANGELOG·커밋·푸시·PR 생성.

### 단계 19. `/land-and-deploy` → `/canary`

> Gstack `/land-and-deploy` 로 머지·CI·배포·health 검증 → `/canary` 로 라이브 모니터링.

### 단계 20. `/document-release` → `/retro`

> Gstack `/document-release` 로 README·ARCHITECTURE·CONTRIBUTING·CLAUDE.md 갱신 → `/retro` 로 주간 회고.

### 단계 21. `simon-instincts` 업데이트 → `/checkpoint`

> 이번 사이클에서 배운 것을 `simon-instincts` 로 `~/.claude/instincts/` 에 기록 → Gstack `/checkpoint` 로 상태 스냅샷.

---

## Principles — Boris Cherny 내장

모든 단계에서 다음 원칙을 준수한다:

1. **Plan 모드 기본**: 세션 시작은 Plan 모드. 실행 전 사용자 승인.
2. **병렬은 worktree**: 병렬 Claude 실행은 `simon-worktree` 로 격리해야 브랜치 충돌 없이 작업 병렬화가 가능하다.
3. **CLAUDE.md 팀 체크인**: 프로젝트 `CLAUDE.md` 는 git 에 포함, PR 마다 갱신.
4. **검증 루프 = 도구 제공**: Claude 에게 서버 시작 방법·브라우저 URL·테스트 실행 명령을 명시적으로 알려줄 것.
5. **Permission allowlist 우선**: `--dangerously-skip-permissions` 는 쓰지 말고 `/permissions` 로 allowlist 를 관리 — 한 번의 사고가 전체 세션을 돌릴 가치보다 크다.
6. **최신 모델**: Opus 4.6 자동 사용.
7. **슬래시 명령어 = 스킬**: Gstack `/ship` 도 `ship` 스킬과 동일 개념으로 취급.

---

## Checklist

파이프라인 실행 시 단계마다 확인:

- [ ] 이전 단계 산출물을 읽고 시작했는가
- [ ] 사용자 confirm 받아야 할 파괴적 작업은 없는가
- [ ] 시크릿이 커밋에 들어가지 않는가
- [ ] 각 단계의 산출물이 `docs/` 에 저장됐는가
- [ ] 실패 시 롤백 경로가 있는가
- [ ] 다음 단계 진입 전 현재 단계 완료 기준을 만족하는가

---

## Anti-patterns

- ❌ **Plan 없이 코딩 시작** — 단계 1-10 건너뛰고 바로 구현
- ❌ **레포 확인 없이 커밋** — 단계 11 skip
- ❌ **민감 필드(subscription_tier, role, credits, is_admin)를 클라이언트에서 수정 가능하게 둠** — 단계 16 RLS 감사 필수
- ❌ **`simon-research` 건너뛰고 플래닝 진입** — 출처 없는 추측 플랜
- ❌ **한 번에 20단계 실행** — 단계별 사용자 검증 없이 무한 자동화
- ❌ **Gstack 스킬 존재 여부 확인 없이 호출** — 없으면 degrade 안내 텍스트로 대체

---

## Related skills

- **Gstack 파이프라인**: `/office-hours`, `/plan-ceo-review`, `/plan-eng-review`, `/autoplan`, `/design-consultation`, `/design-shotgun`, `/design-review`, `/design-html`, `/qa`, `/cso`, `/benchmark`, `/review`, `/ship`, `/land-and-deploy`, `/canary`, `/document-release`, `/retro`, `/checkpoint`, `/codex`
- **simon-stack**: `simon-research`, `simon-tdd`, `simon-worktree`, `simon-instincts`, `security-checklist`, `authz-designer`, `paid-api-guard`, `stitch-design-flow`
- **유틸리티**: `/careful`, `/guard`, `/freeze`, `/unfreeze`
