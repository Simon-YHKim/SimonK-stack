# SimonK-Stack

> 서비스 기획부터 개발, 수익화, 그로스, Exit까지 — Claude Code가 **자동으로 올바른 절차를 따르게** 만드는 skill 라이브러리 + **simonK 통합 자율 하네스**.

**[simonk-stack.pages.dev](https://simonk-stack.pages.dev)** · [![validator](https://img.shields.io/badge/skill--validator-98%20skills-brightgreen)]() [![harness](https://img.shields.io/badge/simonK-autonomous-blueviolet)]() [![license](https://img.shields.io/badge/license-MIT-blue)]()

🔗 **자매 레포**: [SimonKWiki](https://github.com/Simon-YHKim/SimonKWiki) (PRIVATE) — 세션 간 학습 누적 wiki

---

## 이게 뭔가요?

**문제**: AI 코딩 어시스턴트는 큰 작업을 시키면 매번 다른 순서로 일하고, 같은 실수를 반복합니다.

**해결**: 98개 skill (작업 매뉴얼) + **simonK 통합 자율 하네스** (단일 진입점 → 6-phase 자율 실행). 더해 [SimonKWiki](https://github.com/Simon-YHKim/SimonKWiki) 가 세션 간 _학습 누적_ 을 담당합니다 — 매 세션 처음부터 다시 추론하지 않습니다.

```
"새 앱 만들자"        → app-dev-orchestrator    → 21단계 파이프라인
"PMF 분석해줘"        → pmf-analyzer            → 3 case 시나리오 예측
"결제 붙여줘"          → payment-integrator      → Stripe/PortOne + 웹훅 + 테스트
"수익화 테스트 돌려줘"  → revenue-scenario-tester → 7 전문 에이전트, 80+ 시나리오
"이번 패치 노트"       → release-notes           → 개발자 vs 사용자 어조 분리 산출
"바이럴 시키자"        → viral-launch            → 4채널 (인앱/인스타/커뮤니티/입소문) 플레이북
"AI 어투 빼줘"         → human-voice-guard       → LLM tell 검출 + 사람 어투로 리라이팅
"스택 정해줘"          → tech-preference-tracker → 누적 선호 매트릭스 기반 일관성 권고
"exit 전략 세워줘"     → exit-strategy-planner   → IPO/M&A 로드맵

simonK <목표>          → 통합 자율 하네스         → Ambiguity check → Sprint plan
                                                  → 병렬 Task agents → Verify → Full Auto push
```

---

## 🤖 simonK 통합 자율 하네스 (★ v2 핵심)

**단일 진입점 — 어디서든 호출 가능:**

```powershell
# PowerShell — profile 영속화 (어떤 폴더에서든)
simonK <task>

# Claude Code 인터랙티브 세션 내 — 슬래시
/simonK <task>
```

둘 다 동일 `skills-src/simonk/SKILL.md` 실행. **case-insensitive** (`simonk`, `SIMONK`, `SimonK` 모두 동일).

### 6-Phase 자율 흐름

| Phase | 작업 | 사용자 입력? |
|---|---|---|
| **1** Ambiguity Score | 4 차원 (Goal/Scope/Success/Risk) 0-10 평가 | score<6 면 Socratic 3-5 Q&A 1회 |
| **2** Sprint Plan | `≤5` sub-task 분해 + dependency 그래프 → `.simonk/plan.md` | default proceed |
| **3** Parallel Execution | 독립 sub-task → Task tool 병렬 호출 (general-purpose / Explore / Plan agents) | none |
| **4** Verification | 작업별 검증 (`validate_skill.py` / `wiki-lint` / `bash -n` / test) | none (2회 실패 시 보고) |
| **5** Persistence | `git add -A && commit && push` 양쪽 repo (Full Auto) | none |
| **6** Final Report | 작업·검증·git status·다음 step 구조화 보고 | none |

### Auto-push 정책 (Full Auto, 사용자 합의)

- ✅ 모든 repo (private + public) 자동 commit + push
- ❌ **PR 생성·머지** 절대 자동 X — 글로벌 CLAUDE.md 정책
- ❌ **파괴적 작업** (`rm -rf`, `git reset --hard`, force push to main of multi-collab, DB drop) STOP
- ❌ **.env / credentials 노출·수정** 즉시 STOP

### 진입점 설치 (one-time)

```powershell
cd "E:\Coding Infra\Harrness Eng\SimonK-stack"
.\scripts\install-simonk-profile.ps1
# → $PROFILE.CurrentUserAllHosts 에 simonk.ps1 dot-source 박힘
# → $env:SIMONK_PROJECT_DIR 영속 (User scope)
```

상세 6-phase 명세: [skills-src/simonk/SKILL.md](skills-src/simonk/SKILL.md)

---

## 설치

### Claude Code 웹 (제일 쉬움)
1. https://claude.ai/code 접속 → `Simon-YHKim/SimonK-stack` 열기 → 끝

### 로컬 CLI
```bash
git clone https://github.com/Simon-YHKim/SimonK-stack.git
cd SimonK-stack && ./scripts/install.sh
```

### 다른 프로젝트에 vendoring
```bash
/path/to/SimonK-stack/scripts/setup-repo.sh /path/to/your-project
```

상세: [docs/USING-IN-OTHER-REPOS.md](docs/USING-IN-OTHER-REPOS.md)

---

## 🔁 자동 업데이트 — 어떤 출처가 자동 최신화되나

세션 시작 시 `.claude/hooks/session-start.sh`가 출처별로 다른 정책 적용:

| 출처 | 메커니즘 | 자동? |
|---|---|---|
| **SimonK-stack 자체** (`Simon-YHKim/SimonK-stack`) | session-start hook `git fetch + pull --ff-only` (clean+main 일 때만) | ✅ 자동 |
| **SimonKWiki** (`Simon-YHKim/SimonKWiki`, PRIVATE) | 동일 메커니즘 | ✅ 자동 |
| **Gstack upstream** (`garrytan/gstack`) | hook이 ahead-count 검출 → LLM에게 `/gstack-upgrade` 호출 권장 | 🟡 반자동 |
| **kepano/obsidian-skills** (defuddle / json-canvas / obsidian-bases / obsidian-cli / obsidian-markdown) | vendored snapshot — 수동 갱신 필요 | ❌ 수동 |
| **external/** (OMC · OMO · OpenHarness · open-cowork · anthropics-skills) | shallow clone, reference 전용 | ❌ 수동 (OMC는 `/plugin install` 후 marketplace 자동 update 옵션) |
| **Graphify** (Safi Shamsi · YC S26) | `uv tool upgrade graphifyy` 수동 | ❌ 수동 |

---

## 🎯 빠른 시작 — Curated 15개

처음 보는 사람은 **`simonK <목표>` 한 줄**로 시작. 그 외 메인 15개 큐레이션은 → [docs/CURATED-SKILLS.md](docs/CURATED-SKILLS.md)

| 우선순위 | Skill (호출) |
|---|---|
| ★ 통합 진입 | `simonK <task>` |
| ★ 파이프라인 | `app-dev-orchestrator` · `dev-orchestrator` · `security-orchestrator` |
| ★ 방법론 base | `karpathy-guidelines` · `simon-tdd` · `simon-worktree` · `simon-instincts` |
| ★ 5/30 출시 | `payment-integrator` · `human-voice-guard` · `release-notes` · `viral-launch` |
| ★ 리서치/디자인 | `simon-research` · `simon-design-first` |
| ★ wiki 운영 | `wiki-ingest` · `wiki-query` · `wiki-lint` |
| ★ 일상 | `commit` |

나머지 83개 (도메인 특화 + Gstack 36 vendored + kepano 5 vendored)는 [전체 카탈로그](#skill-카탈로그--98개) 또는 [docs/CURATED-SKILLS.md § 도메인 특화](docs/CURATED-SKILLS.md#도메인-특화--별도-카탈로그-격하-83개).

---

## Skill 카탈로그 — 98개

### 0. simonK 통합 자율 하네스 (★ NEW)

| Skill | 트리거 | 역할 |
|---|---|---|
| `simonk` | `simonK <task>`, `/simonK`, "ultrawork", "ulw", "한 번에 끝내줘", "팀으로 진행해", "자율로 끝까지", "스프린트 시작" | 6-phase 자율 실행 — Ambiguity → Plan → 병렬 Task → Verify → Full Auto push → Report |

### Orchestrators — 작업 자동 파이프라인

| Skill | 트리거 | 역할 |
|---|---|---|
| `app-dev-orchestrator` | "새 앱 만들자" | 21단계 신규 앱 개발 파이프라인 |
| `dev-orchestrator` | "기능 구현해줘" | 7단계 일상 개발 (진단→TDD→품질→리뷰→커밋) |
| `security-orchestrator` | "보안 점검" | 5단계 적대적 보안 감사 → 통합 리포트 |

### Strategy & Growth — 전략/PMF/그로스

| Skill | 트리거 | 역할 |
|---|---|---|
| `aarrr-growth-planner` | "AARRR 분석", "그로스 전략" | AARRR 프레임워크 기반 아이디어 도출 + 실험 백로그 |
| `pmf-analyzer` | "PMF 분석", "시장성 분석" | 3 case PMF 예측 (Optimistic/Base/Pessimistic) + 주기적 리포팅 |
| `aha-moment-optimizer` | "아하 모먼트", "온보딩 최적화" | 가설→실험→데이터 사이클로 핵심 가치 경험 발굴 |
| `sprint-optimizer` | "스프린트 모드", "3가지 방안" | 3 case 도출 → Best 추천 → 반복 고도화 (깊이 합의) |
| `exit-strategy-planner` | "exit 전략", "IPO 로드맵" | Seed→Series A→B→C→Exit 단계별 로드맵 (쿠팡 사례) |

### Architecture & Stack — 기술 아키텍처

| Skill | 트리거 | 역할 |
|---|---|---|
| `stack-architect` | "프론트만 필요해?", "tech stack" | 프론트/백/API 판단 + 규모별 배포 + 안정성 로드맵 |
| `app-platform-selector` | "하이브리드 vs 네이티브", "PWA" | Hybrid/PWA/Native 판단 + 웹 래퍼 리젝 방지 전략 |
| `db-selector` | "DB 뭐 쓰지", "데이터베이스 선택" | 사전 카탈로그 기반 DB 추천 (Supabase/Neon/Planet 등) |
| `deploy-configurator` | "배포 설정", "CI/CD" | Cloudflare/Vercel/Fly.io + GitHub Actions + 모니터링 |
| `tech-preference-tracker` | "스택 정해줘", "이전이랑 일관성 있게" | 누적 선호 매트릭스 → 25+ 레포 일관성 권고 + drift 감지 |

### Monetization & Payment — 수익화/결제

| Skill | 트리거 | 역할 |
|---|---|---|
| `monetization-planner` | "수익 모델 설계", "가격 정하자" | 모델 선택 + tier 구조 + 무료-유료 경계 + MONETIZATION.md |
| `payment-integrator` | "결제 붙여줘", "구독 시스템" | Stripe/PortOne/RevenueCat 구현 + 웹훅 + 상태머신 |
| `global-payment-planner` | "글로벌 결제", "국가별 규제" | 국가별 PG/세금/규제 + 최적 조합 |
| `subscription-manager-selector` | "구독 관리 서비스" | RevenueCat/Stripe/Paddle/Lemon Squeezy 비교 추천 |
| `ad-monetization` | "광고 붙여줘", "AdMob" | 광고 SDK + 배치 전략 + AdBlock fallback |
| `pink-tax-advisor` | "수익 극대화", "가격 심리" | 세그먼트별 차등가격 + 심리적 가격 (명시 요청 시만) |

### Auth & Security — 인증/보안

| Skill | 트리거 | 역할 |
|---|---|---|
| `auth-builder` | "로그인 만들어줘", "OAuth" | 소셜로그인/Passkey/본인인증 + RBAC + 세션 관리 |
| `security-checklist` | "RLS 확인", "rate limit" | 4대 영역 적대적 테스트 + SQL drop-in |
| `authz-designer` | "권한 시스템 설계" | RBAC/ABAC/ReBAC 모델 + DDL + IDOR 감사 |
| `paid-api-guard` | "결제 API 보안" | 유료 API 6층 방어 체크리스트 |

### Analytics & Tracking — 분석/추적

| Skill | 트리거 | 역할 |
|---|---|---|
| `analytics-integrator` | "분석 도구 세팅", "GA4" | PostHog/Mixpanel/Amplitude/Clarity 세팅 + 이벤트 설계 |
| `tag-manager-integrator` | "GTM 세팅", "전환 추적" | GTM/gtag 이벤트 추적 + 분석 리포트 + 최적화 제안 |
| `growth-engine` | "마케팅 도구", "푸시 알림" | 이메일/푸시/어트리뷰션/A-B/피처플래그 통합 세팅 |
| `store-launcher` | "스토어 출시", "ASO" | Play Store/App Store 리스팅 최적화 + 정책 준수 |

### Launch & Communication — 런칭/공지/어조

| Skill | 트리거 | 역할 |
|---|---|---|
| `release-notes` | "패치 노트", "스토어 업데이트 내용" | 개발자용(README/CHANGELOG) + 사용자용(스토어/배너) **분리** 산출 |
| `viral-launch` | "바이럴 어떻게", "런칭 플랜" | 4채널 (인앱 공유 / 인스타 / 커뮤니티 / 입소문) 즉시 복붙 산출물 |
| `human-voice-guard` | "AI 티 나는데", "자연스럽게" | LLM tell 카탈로그 검출 + STYLE.md 생성으로 회귀 방지 + `voice-lint.sh` |

### Quality & Testing — 품질/검증

| Skill | 트리거 | 역할 |
|---|---|---|
| `revenue-scenario-tester` | "수익화 테스트" | 7 전문 에이전트 (Payment/Subscription/Ad/Analytics/Store/Security/KR) |
| `code-health-guard` | "코드 구조 점검" | 아키텍처 검증 + 순환 의존 스캔 |
| `consistency-guard` | "일관성 유지" | JSON schema 기반 서비스 일관성 판단 + 강제 |

### Development Method — 개발 방법론

| Skill | 트리거 | 역할 |
|---|---|---|
| `karpathy-guidelines` | "4원칙 적용" | Karpathy 4원칙: 가정명시/단순함/외과적변경/목표주도 |
| `simon-tdd` | "TDD", "테스트 먼저" | RED→GREEN→REFACTOR + Guard Mode |
| `simon-worktree` | "병렬 작업" | git worktree 격리 (동시 세션) |
| `simon-research` | "리서치 해줘" | 외부 리서치 의무화 → wiki 자동 누적 |
| `agent-delegate` | "에이전트 위임" | Fan-out/Pipeline/Supervisor 패턴 위임 |
| `simon-design-first` | "디자인 만들어줘" | AI slop 방지 + 레퍼런스 기반 디자인 프록시 |
| `simon-instincts` | "이거 또 틀렸어" | 실수 누적 → 4파일 자동 로드 (세션 간 학습) |

### Knowledge & Tools — 지식관리/특수도구

| Skill | 트리거 | 역할 |
|---|---|---|
| `llm-wiki-builder` | "wiki에 추가해줘" | Karpathy llm-wiki 패턴: 영속 Ingest/Query/Lint wiki |
| `wiki-ingest` | "인제스트해줘", "위키에 정리해줘" | raw/ 새 자료 → wiki/ 컴파일 (SimonKWiki v2 전용) |
| `wiki-query` | wiki 답할 만한 질문 | index.md 우선 검색 → wikilink 인용 답변 |
| `wiki-lint` | "wiki 점검", "wiki 린트" | 8-체크 정합성 보고 (자동 적용 X, 제안만) |
| `nextjs-optimizer` | "Next.js 최적화" | 5대 성능 영역 감사 (이미지/렌더링/번들/캐싱) |
| `stitch-design-flow` | "Stitch 프롬프트" | DESIGN.md → Safe/Bold/Wild 프롬프트 |
| `project-context-md` | "CLAUDE.md 만들어줘" | 프로젝트 CLAUDE.md 생성/갱신 (검증 루프 핵심) |

### Obsidian Tools (kepano-vendored 2026-05-23)

| Skill | 출처 | 역할 |
|---|---|---|
| `defuddle` | kepano/obsidian-skills | Web → clean markdown (WebFetch 대체, 토큰 절감) |
| `json-canvas` | kepano/obsidian-skills | Obsidian Canvas (.canvas) 파일 생성/읽기 |
| `obsidian-bases` | kepano/obsidian-skills | Obsidian Bases (.base) 데이터베이스 뷰 |
| `obsidian-cli` | kepano/obsidian-skills | Obsidian CLI 자동화 (cron lint 기반) |
| `obsidian-markdown` | kepano/obsidian-skills | Obsidian-format markdown 정합성 |

### Session & General — 세션관리/범용

| Skill | 트리거 | 역할 |
|---|---|---|
| `skill-gen-agent` | "스킬 만들어줘" | Skill 생성·검증·테스트 7단계 도구 |
| `context-guardian` | "세션 복구" | 컨텍스트 고갈 예방/모니터링/복구 |
| `commit` | "커밋해줘" | Conventional Commits |
| `debug` | "버그 고쳐줘" | 근본 원인 진단 + 수정 |
| `explain` | "이 코드 설명해줘" | entry point, 데이터 플로우 |
| `refactor` | "리팩토링" | 동작 보존 구조 개선 |
| `review` | "리뷰해줘" | blocker/major/minor/nit |
| `test-gen` | "테스트 작성" | 골든 패스 + 엣지 + 에러 경로 |

---

### Execution Pipeline — 실행 파이프라인 (Gstack vendored)

[Gstack](https://github.com/garrytan/gstack) 기반 36개 실행 도구가 `skills-src/`에 내장되어 있습니다 (원본 형식 유지):

| 카테고리 | Skills |
|---|---|
| **플래닝** | `office-hours` `plan-ceo-review` `plan-eng-review` `plan-design-review` `plan-devex-review` `autoplan` |
| **디자인** | `design-consultation` `design-shotgun` `design-review` `design-html` |
| **구현·QA** | `qa` `qa-only` `benchmark` `health` `codex` |
| **배포** | `ship` `land-and-deploy` `canary` `setup-deploy` `document-release` |
| **보안·품질** | `cso` `careful` `guard` `freeze` `unfreeze` `retro` |
| **리서치·DX** | `investigate` `browse` `learn` `devex-review` |
| **기타** | `checkpoint` `pair-agent` `setup-browser-cookies` `open-gstack-browser` `connect-chrome` `gstack-upgrade` `session-start-hook` |

**총 98개 skill** — 전부 `skills-src/` 또는 `.claude/skills/`에 내장, 외부 clone 불필요.

---

## 🔁 3-Hook 자동화 — 사용자 명시 0 으로 wiki 누적

매 세션의 흐름이 **자동**으로 다음 3 단계를 거칩니다. 사용자가 "wiki 갱신해줘" 같은 신호를 줄 필요 없음.

| Hook | 시점 | 동작 | 비용 |
|---|---|---|---|
| **SessionStart** | 세션 시작 | bootstrap (skills 설치 + instincts seed) → SimonK / gstack / SimonKWiki origin 의 ahead-count 자동 fetch → 안전하면 (clean+main+ff-only) `git pull` 자동 → `[UPGRADE_AVAILABLE]` 박스 + `~/.claude/.update-pending` fallback marker 이중 출력 | 0 토큰 |
| **UserPromptSubmit** | 매 사용자 발화 _직후, LLM 응답 직전_ | wiki 의 _5초 인덱스 + 최근 3 log + M/T 코드 totals + 행동 규칙_ 을 system context 에 inject | ~466 토큰 / 발화 |
| **Stop** | LLM 응답 종료 | wiki repo 가 dirty 면 `git add + commit + push` 자동 (branch=main + md/json 위주 필터 안전 가드) | 0 토큰 |

**효과**: LLM 이 _발화 0번째부터_ wiki 인지 상태. 새 mistake / 시행착오 발견 시 _자발적으로_ Edit/Write 로 wiki 에 append. Stop 이 그 변경을 _자동으로 영속화_. 결과적으로 "그냥 작업하면 알아서 누적".

**Opt-out**: `.claude/settings.json` 의 해당 hook 블록 제거 또는 `SIMON_HOOK_SILENT=1` 환경변수.

---

## 📊 Phase 3 사전 진입 (계획 6/15~6/30 → 실제 5/23~24)

Phase 3 핵심 도구 3 종이 계획보다 *3주 일찍* 사전 진입 완료.

| # | 도구 | 설치 | 결과 |
|---|---|---|---|
| **A13** | [Graphify](https://graphify.net) v0.8.16 (Safi Shamsi · YC S26) | `uv tool install graphifyy` | SimonKWiki **720 nodes** · SimonK-stack **4605 nodes** · Claude Code PreToolUse hook |
| **C02** | [OpenHarness](https://github.com/HKUDS/OpenHarness) v0.1.9 (HKUDS) | `uv tool install openharness-ai` | 4 CLIs (`oh`/`ohmo`/`openh`/`openharness`) · Phase 6 ohmo signature 진입 시 본격 |
| **VS Code** | extensions + settings | `code --install-extension ...` | claude-code v2.1.145 + 한국어 lang pack + python+pylance+debugpy + markdown-all-in-one + yaml · settings.json 표준화 (format on save / LF / utf8 / PowerShell terminal / search exclusions) · argv.json locale ko |

### Graphify 사용

```powershell
# 그래프 추출/갱신 (LLM 미사용, AST 기반, 비용 0)
cd "<vault or repo>"
graphify update .
# → graphify-out/ 생성 (graph.html + GRAPH_REPORT.md + graph.json)

# 질의 (토큰 절감)
graphify query "<질문>"
graphify path "<A>" "<B>"
graphify explain "<concept>"
```

코드베이스 질문 시 `graphify query` 자동 권장 (subgraph fetch → 토큰 절감).

### Phase 3 미완 (사용자 결정 필요)

- **A11 Zotero MCP** — `zotero-mcp` 사용자 계정 결정 후 통합
- **A12 NotebookLM** — `notebooklm-py` Google 계정 결정 후 통합
- **A14 MCP 통합** — Zotero + NotebookLM + Graphify + OpenHarness MCP 묶음 (위 두 결정 후)

상세: [SimonKWiki wiki/entities/tools/graphify](../../obsidian/SimonKWiki/wiki/entities/tools/graphify.md) · [openharness](../../obsidian/SimonKWiki/wiki/entities/tools/openharness.md)

---

## 📖 SimonKWiki 통합

SimonK Stack 은 [SimonKWiki](https://github.com/Simon-YHKim/SimonKWiki) (PRIVATE) 와 _짝_ 으로 동작합니다.

| | Instincts (`~/.claude/instincts/`) | SimonKWiki |
|---|---|---|
| 도메인 | 코딩 실수, 도구 quirks | 사용자 메타 인지, 작업 성향, 누적 결론, 인생 호 (arcs) |
| 위치 | 로컬 4 md 파일 | git repo (Obsidian-호환, Karpathy 모델 raw/+wiki/+Output/) |
| 누적 | append-only mistakes | M-xxx (mistakes), T-xxx (trials) + 7 카테고리 (concepts/entities/events/arcs/projects/protocols/assessments) |
| 진입점 | seed 4 파일 | `wiki/index.md` + `LESSONS_LEARNED.md` |

매 세션 wiki 의 `index.md` + 최근 `log.md`를 _먼저_ 읽고 사용자 요청 처리. 세션 종료 시 새 발견을 wiki 에 append. 자세한 절차는 [`CLAUDE.md § 📖 Wiki 참고 (필수)`](CLAUDE.md).

---

## 작동 원리

### 서비스 개발 전체 흐름

```
사용자 → simonK <목표>
  │
  ├─ Phase 1: Ambiguity score (0-10 × 4 dim)
  │   └─ score<6 → AskUserQuestion 3-5문항 (1회)
  │
  ├─ Phase 2: Sprint plan (.simonk/plan.md)
  │
  ├─ Phase 3: 병렬 Task agents
  │   ├─ aarrr-growth-planner      ← AARRR 프레임워크
  │   ├─ pmf-analyzer               ← 3 case PMF 예측
  │   ├─ aha-moment-optimizer       ← 아하 모먼트 발굴
  │   │
  │   ├─ stack-architect            ← 프론트/백/API/배포 결정
  │   │   ├─ app-platform-selector
  │   │   ├─ db-selector
  │   │   └─ deploy-configurator
  │   │
  │   ├─ monetization-planner       ← 수익 모델 설계
  │   │   ├─ payment-integrator
  │   │   ├─ global-payment-planner
  │   │   └─ revenue-scenario-tester
  │   │
  │   ├─ analytics-integrator
  │   │   └─ tag-manager-integrator
  │   │
  │   ├─ growth-engine → store-launcher → pmf-analyzer (리포팅)
  │   │
  │   └─ exit-strategy-planner
  │
  ├─ Phase 4: Verification (validate_skill.py / wiki-lint / test)
  ├─ Phase 5: Full Auto push (양쪽 repo)
  └─ Phase 6: Final report
```

---

## 테스트

| 테스트 | 결과 |
|---|---|
| Native skills (SimonK) | **62/62 PASS** (validator 0 errors / 0 warnings) |
| Vendored skills (Gstack + kepano) | **36 + 5 vendored** (원본 형식 유지, 기능 정상) |
| 전체 validator (lenient + **strict YAML E013**) | **98/98 PASS** |
| simonk 통합 자율 하네스 | **0 errors / 0 warnings · score 0.80** |
| SKILL.md description quotation 무결성 | **98/98** |
| Bash syntax (hooks + scripts) | **all PASS** |
| PowerShell scripts (simonk.ps1 + install-simonk-profile.ps1) | **all PASS** (Get-Command + parse check) |
| Orchestrator chain | **모든 참조 존재 확인** |
| `voice-lint.sh` (`human-voice-guard`) | **CI-ready, exit 1 on tell** |
| `lint.sh` (path-aware v2, llm-wiki-builder) | **orphans 0 / broken 0 (literal 제외) / M·T gap 0** |
| Graphify 그래프 (SimonKWiki) | **720 nodes · 644 edges · 76 communities** |

---

## FAQ

**Q. 총 몇 개 skill?**
98개 = SimonK native 57 + Gstack vendored 36 + kepano vendored 5 + 신규 simonk 통합 하네스 1. 전부 `skills-src/` 또는 `.claude/skills/` 에 내장.

**Q. simonK 와 다른 skill 차이?**
- 일반 skill = *단일 도메인 작업 매뉴얼* (예: payment-integrator = 결제만)
- **simonK = 통합 자율 하네스** (목표만 받고 — Ambiguity catch → Plan → 병렬 Task → Verify → push 전체 흐름)
- simonK 가 적절한 일반 skill 들을 Task agent로 위임

**Q. 다른 repo에서 쓰려면?**
`scripts/setup-repo.sh /path/to/target` → 상세: [docs/USING-IN-OTHER-REPOS.md](docs/USING-IN-OTHER-REPOS.md)

**Q. 한국어로만 말해도 되나요?**
네. 모든 skill에 한/영 트리거 병기.

**Q. 업데이트는?**
- SimonK-stack 자체: SessionStart hook이 `git pull --ff-only` 자동 (clean+main 일 때만)
- kepano vendored 5개: 수동 갱신 — 원본 https://github.com/kepano/obsidian-skills 정기 확인
- Graphify: `uv tool upgrade graphifyy`
- 출처별 자세한 정책은 위 [🔁 자동 업데이트](#-자동-업데이트--어떤-출처가-자동-최신화되나) 표 참조

---

## 크레딧

| 출처 | 기여 |
|---|---|
| [Gstack](https://github.com/garrytan/gstack) — garrytan | 실행 파이프라인 36 skill |
| [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | Obsidian 운영 5 skill (defuddle / json-canvas / obsidian-bases / obsidian-cli / obsidian-markdown) |
| [Karpathy](https://x.com/karpathy) | 4원칙 (코딩 가이드라인) + llm-wiki 패턴 |
| [Superpowers](https://github.com/obra/superpowers) — obra | TDD, worktree, 검증 루프 |
| [everything-claude-code](https://github.com/affaan-m/everything-claude-code) | Instincts 학습, research-first |
| [Skill-Agent](https://github.com/Simon-YHKim/Skill-Gen-Agent) | validate_skill.py 검증 도구 |
| [Impeccable](https://github.com/pbakaus/impeccable) | AI Slop 방지 디자인 원칙 |
| [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) | Karpathy 4원칙 정제 |
| [Graphify](https://graphify.net) — Safi Shamsi (YC S26) | 지식 그래프 추출·시각화 (Phase 3 통합) |

## 라이선스

[MIT](LICENSE). 상업적 사용·수정·배포 자유.
