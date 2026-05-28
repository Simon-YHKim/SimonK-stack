# SimonK-Stack

> **Claude 를 1인 회사로 만드는 skill 라이브러리.** 120+ 개 skill 이 8 개 부서로 나뉘어 있고, `simonK` 가 CEO 사무실에서 자율 진행. 사용자 = 창업자.

[![skills](https://img.shields.io/badge/skills-120%2B-brightgreen)]() [![validator](https://img.shields.io/badge/validator-0_errors-brightgreen)]() [![harness](https://img.shields.io/badge/simonK-autonomous-blueviolet)]() [![license](https://img.shields.io/badge/license-MIT-blue)]()

**Site**: [simonk-stack.pages.dev](https://simonk-stack.pages.dev) · **English**: [README.en.md](README.en.md) · **자매 레포**: [SimonKWiki](https://github.com/Simon-YHKim/SimonKWiki) (PRIVATE) — 세션 간 학습 누적

---

## 회사 비유 — 한 페이지로 보기

```
                  ┌─────────────────────────┐
                  │  사용자 = Founder / CEO │
                  └────────────┬────────────┘
                               │
                  ┌────────────▼────────────┐
                  │  /simonK = Chief of Staff │  ← 단일 자율 진입점 (6-phase)
                  └────────────┬────────────┘
                               │
   ┌───────────┬───────────┬───┴───────┬───────────┬───────────┬───────────┬───────────┐
   ▼           ▼           ▼           ▼           ▼           ▼           ▼           ▼
Strategy   Product    Engineering DevEx      Security   Growth     Knowledge  Skill
Office     & Design               & Platform & Compl.   & Revenue  & Memory   DevOps
```

각 부서 = skill 묶음. 같은 책임은 같은 부서, 다른 책임은 다른 부서.

---

## 🏢 8 부서 — 무엇을 어디서 처리하나

### 1. Strategy Office (전략실) — 비전·계획·의사결정

새 프로젝트 시작 시 *무엇을 왜* 만들지 결정. simonK 가 작업 의뢰 받자마자 가장 먼저 들르는 곳.

| 핵심 skill | 역할 |
|---|---|
| `/founder-context` | me.md / vision.md / design.md / workingstyle.md 4-file 부트스트랩 — 창업자의 정체성·비전·디자인·작업 패턴을 한 번에 |
| `/office-hours` (gstack) | YC 파트너 스타일 6-Q forcing question — "이거 만들 가치 있나?" |
| `/plan-ceo-review` (gstack) | 10-star 스코프 재정의, 임원실 한 명이 본 후 plan 락 |
| `/plan-eng-review` (gstack) | 엔지니어링 리더 시각으로 plan 검증 |
| `/spec` (gstack) | 모호한 의도를 실행 가능한 spec 으로 5-phase 변환 |
| `/grill-me` | 1Q-at-a-time 인터뷰로 plan/spec stress test (simon-tdd RED 전) |

### 2. Product & Design (제품·디자인) — UI·UX·시각 방향

전략실이 *왜* 정하면 여기가 *어떻게 보일지* 정한다. 코드 작성 전에 톤·레퍼런스·폰트·팔레트 확정.

| 핵심 skill | 역할 |
|---|---|
| `/simon-design-first` | UI 코드 작성 전 강제 진단 (audience/purpose/tone) + 레퍼런스 3-5 + 폰트 선택지. AI slop 방지 게이트 |
| `/plan-design-review` (gstack) | 디자이너 시각의 plan 리뷰 (10-star, 인터랙티브) |
| `/design-shotgun` (gstack) | AI 디자인 N 변형 → 비교 보드 → 피드백 → iterate |
| `/design-html` (gstack) | HTML 시안 생성 |
| `/design-review` (gstack) | 실제 사이트 시각 감사 |
| `/stitch-design-flow` | Google Stitch 용 Safe/Bold/Wild 프롬프트 3 종 생성 |

### 3. Engineering (개발) — 구현·테스트·디버깅

`founder-context` + `simon-design-first` 가 끝나야 여기 들어옴. TDD 강제, 검증 루프 강제.

| 핵심 skill | 역할 |
|---|---|
| `/simon-tdd` | RED → GREEN → REFACTOR 사이클 강제, 검증 루프 (서버 URL + 테스트 명령) 명시 |
| `/test-gen` | Happy / Sad / Bad / Race / Boundary / Permission / State 7-카테고리 시나리오 |
| `/debug` | 에러 보고서 → root-cause 진단 + fix + reproduction |
| `/refactor` | 구조 개선 |
| `/explain` | 모듈·시스템 walkthrough (entry points, data flow, invariants) |
| `/simon-worktree` | 병렬 작업 시 git worktree 격리 |

### 4. DevEx & Platform (플랫폼) — 인프라·툴체인·배포

코드는 됐고, 어떻게 실행하고 배포할지. Vercel / Cloudflare / Fly.io / Railway 선택부터 CI/CD 자동화.

| 핵심 skill | 역할 |
|---|---|
| `/deploy-configurator` | 배포 플랫폼 선택 + CI/CD + custom domain + env 관리 |
| `/setup-deploy` (gstack) | `/land-and-deploy` 용 deploy 설정을 CLAUDE.md 에 박음 |
| `/land-and-deploy` (gstack) | 머지 → CI 대기 → 프로덕션 canary 검증 |
| `/ship` (gstack) | VERSION + CHANGELOG + push + PR 한 흐름 |
| `/canary` (gstack) | 프로덕션 헬스 카나리 검증 |
| `/stack-update` | SimonK Stack 본체 + Wiki + gstack + 5 vendored stacks 홀리스틱 최신화 |
| `/multi-terminal-dispatcher` | 모델 라우터 + 다중 터미널 병렬 작업 dispatch |

### 5. Security & Compliance (보안·법무) — 위협·규제·인증

`simonk` 가 매 sprint 마다 무조건 통과시킴. RLS · authz · 한국 PIPA · GDPR · ad-policy · 결제 ToS.

| 핵심 skill | 역할 |
|---|---|
| `/security-orchestrator` | 4 단계 보안 감사 순차 실행 (checklist → authz → rate-limit → budget cap) |
| `/security-checklist` | RLS / 구독 변조 / dual-layer rate-limit / 예산 cap 4 pillar |
| `/authz-designer` | 역할·권한 설계 |
| `/cso` (gstack) | Chief Security Officer 모드 — 종합 보안 결정 |
| `/paid-api-guard` | 유료 API 호출 가드 (예산 cap) |
| `/keepass-helper` | 시크릿 매니지먼트 |

### 6. Growth & Revenue (그로스·재무) — 사용자·돈·시장

런칭 후 *돈이 들어오나*. AARRR, 결제·구독, 광고, 스토어 출시, exit 전략까지.

| 핵심 skill | 역할 |
|---|---|
| `/aarrr-growth-planner` | Acquisition→Activation→Retention→Referral→Revenue 분석 + ICE 백로그 |
| `/aha-moment-optimizer` | TTFV 단축 + activation 실험 설계 |
| `/payment-integrator` | Stripe / PortOne / RevenueCat / 인앱결제 통합 |
| `/monetization-planner` | 수익 모델 설계 (구독/광고/거래/freemium) |
| `/revenue-scenario-tester` | 80+ 결제 시나리오 통합 테스트 (7 specialized agents) |
| `/store-launcher` | Play Store / App Store 등록 + ASO |
| `/viral-launch` | 채널별 바이럴 플레이북 (인스타 / 한국 커뮤니티 / in-app share) |
| `/pmf-analyzer` | 3-case PMF 예측 (낙관/보통/비관) + Sean Ellis 시뮬레이션 |
| `/exit-strategy-planner` | IPO / M&A / SPAC 로드맵 + Seed→Series 단계별 KPI |

### 7. Knowledge & Memory (지식관리) — 위키·문서·세션·감사

매 세션 끝에 학습이 *어디 저장되나*. wiki + instincts + handoff + perspectives 가 누적 메모리.

| 핵심 skill | 역할 |
|---|---|
| `/simon-handoff` | docs/HANDOFF.md prepend + main 머지까지 자동. 다음 세션이 `git pull` 한 번에 복원 |
| `/perspectives` | 세션 blind-spot 감사 — Core 5 (User/Business/Technical/Security/Future-self) + 세션 특화 N stakeholder, perspectives.md 누적 |
| `/simon-instincts` | `~/.claude/instincts/` 에 cross-project 실수·관용·도구 함정 append |
| `/llm-wiki-builder` | SimonKWiki 페이지 작성 (T-xxx 결정, M-xxx 실수, entities) |
| `/wiki-query` | 위키 인덱스 검색 + [[wikilink]] 인용 답변. 새 결론은 wiki 페이지로 환원 |
| `/wiki-lint` / `/wiki-ingest` | 위키 무결성 + 외부 문서 흡수 |
| `/context-guardian` | 컨텍스트 고갈 예방 + 실측 한도 관리 + 복구 4 mode |
| `/document-release` (gstack) | post-ship README/CHANGELOG/ARCHITECTURE 동기화 |
| `/domain-glossary` | 프로젝트 `CONTEXT.md` 용어집 |
| `/project-context-md` | 프로젝트 `CLAUDE.md` (Claude 검증 도구 명시) 생성 |

### 8. Skill DevOps (자체 도구) — 메타·외부 통합

회사 자체가 쓰는 도구를 만들고 동기화하는 IT 부서. 새 skill 작성·검증, 외부 stack import.

| 핵심 skill | 역할 |
|---|---|
| `/skill-gen-agent` | 새 skill 작성 시 7-단계 검증 파이프라인 (description 점수·네이밍·길이) |
| `/skillify` | 외부 패턴을 simonkstack skill 로 흡수 |
| `/gstack-upgrade` | gstack 자체 업그레이드 (install type 자동 감지) |
| `/omc-upgrade` / `/omo-upgrade` / `/openharness-upgrade` / `/opencowork-upgrade` / `/designmd-upgrade` | 각 vendored 외부 stack 단독 최신화 |
| `/update-config` | settings.json·hooks·permissions 관리 |
| `/init` / `/loop` / `/verify` / `/run` | 일반 개발 유틸 |

---

## 🤖 simonK — CEO 사무실 + Chief of Staff

회사의 모든 부서를 묶어주는 자율 진입점. 단일 명령으로 6 phase 자율 흐름.

```bash
# PowerShell — 어디서든
simonK "사용자 인증 + Stripe 결제 + 한국 결제 추가"

# Claude Code 슬래시 — 세션 내
/simonK <task>
```

### 6 phase 흐름

| Phase | 무엇을 | 어느 부서가 |
|---|---|---|
| 1 | Ambiguity Score (4 차원 0-10) — <6 면 Socratic 3-5 Q | Strategy Office |
| 2 | Sprint plan → `.simonk/plan.md` (trivial 작업은 skip) | Strategy Office |
| 3 | Parallel Task tool delegation (general / Explore / Plan) | 부서별 분배 |
| 4 | Verification — `validate_skill.py` / `wiki-lint` / `bash -n` / 작업별 | QA + Security |
| 5 | Persistence — commit + push (PR 자동 X, .env / 파괴적 작업 STOP) | DevOps |
| 6 | Final report — 구조화 요약 | Strategy Office (CEO 보고) |

자세한 protocol: [`skills-src/simonk/SKILL.md`](skills-src/simonk/SKILL.md) + [`references/orchestration-protocol.md`](skills-src/simonk/references/orchestration-protocol.md)

---

## 🚀 빠른 시작 — 3 가지 설치 모드

### A. Direct install — "내 ~/.claude/ 에만 박아"

```bash
git clone https://github.com/Simon-YHKim/SimonK-stack.git ~/SimonK-stack
cd ~/SimonK-stack && ./scripts/install.sh
```

global `~/.claude/skills/` 에 120+ skill + shared scripts + instincts 배포. SessionStart hook 은 settings.json 에 수동 등록.

### B. Vendor mode — "이 target repo 안에 통째로"

```bash
cd ~/SimonK-stack && ./scripts/setup-repo.sh /path/to/your-project
cd /path/to/your-project && git add .claude && git commit -m "chore(claude): add simon-stack"
```

target repo 의 `.claude/` 에 hook + skill + script 전부 vendor. 다른 사람이 그 repo clone 만 해도 즉시 작동. 가장 자족적.

### C. Bootstrap mode — "2-file drop-in, 매 세션 fresh sync"

```bash
cd ~/SimonK-stack && ./scripts/setup-repo.sh --mode bootstrap /path/to/your-project
```

target repo 에는 hook + settings 만 (2 파일). 매 세션 SimonK-stack clone + 동기화. 가장 가벼움.

### Claude Code 웹 사용

위 B 또는 C 로 setup 한 후 GitHub push → Claude Code 웹에서 해당 repo 열기. SessionStart hook 이 자동 실행되고 simonK 즉시 사용 가능.

---

## 🔁 자동 동기화 — 3-hook 무인 매트릭스

| Hook | 시점 | 동작 | 토큰 비용 |
|---|---|---|---|
| **SessionStart** | 세션 시작 | bootstrap (skill 설치) + upgrade 감지 + auto-pull (clean tree + on main) | 0 |
| **UserPromptSubmit** | 매 사용자 발화 전 | SimonKWiki 5초 인덱스 + 최근 3 log + M/T totals 를 컨텍스트에 inject | ~300-500 |
| **Stop** | LLM 응답 종료 | wiki·instincts dirty 시 자동 commit + push (md/json 변경 위주 필터) | 0 |

**효과**: 사용자가 "wiki", "오답노트" 같은 키워드 안 써도 _LLM 이 스스로_ M-xxx / T-xxx append 가능. 영속화 누락 방지.

**자동 업데이트 출처**:
- SimonK-stack 본체 (this repo)
- SimonKWiki (PRIVATE) — 세션 간 학습
- gstack (upstream) — 실행 파이프라인
- 5 vendored stacks: oh-my-claudecode, oh-my-openagent, OpenHarness, open-cowork, design.md

`/stack-update` 한 명령으로 위 전부 동기화. 개별은 `/<name>-upgrade`.

---

## 🧩 기본 단위 — `skill` 이란?

```
skills-src/<name>/
├── SKILL.md           # 트리거 + 본문 (frontmatter: name, description, tools)
├── evals/cases.json   # 트리거 매칭 테스트 케이스 (최소 2개)
└── (선택) templates/ scripts/ references/
```

- **Description 규칙**: "Use when..." 시작, 한국어+영어 트리거 병기, 400-1024 chars
- **검증**: `python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py skills-src/<name>` — 0 errors 필수
- **저장소**: `skills-src/` 는 배포용 (Claude Code 로딩 X), `.claude/skills/` 는 개발용 (로딩 O — 토큰 부담 줄이려 분리)
- **새 skill**: 반드시 `/skill-gen-agent` 경유. 직접 SKILL.md 작성 시 description 점수·네이밍·길이 한도 위반 누락

---

## 📚 더 알아보기

| 문서 | 내용 |
|---|---|
| [`.claude/skills/INDEX.md`](.claude/skills/INDEX.md) | 120+ skill 카탈로그 (이 README 의 부서 표보다 자세) |
| [`CLAUDE.md`](CLAUDE.md) | 이 레포에서 작업할 때의 Claude 지침 (검증 도구, 컨벤션, 금기) |
| [`CHANGELOG.md`](CHANGELOG.md) | Keep a Changelog 형식 |
| [`docs/INSTALL.md`](docs/INSTALL.md) | 설치 상세 |
| [`docs/MORNING-START.md`](docs/MORNING-START.md) | 매일 작업 시작 패턴 |
| [`docs/USING-IN-OTHER-REPOS.md`](docs/USING-IN-OTHER-REPOS.md) | 다른 프로젝트에서 사용 |

---

## 🔬 검증 (Verification Loop)

```bash
# 단일 skill 검증
python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py skills-src/<name>

# 전체 repo 검증 (120+ skill sweep)
for d in skills-src/*/ .claude/skills/*/; do
  [ -f "${d}SKILL.md" ] || continue
  python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py "${d%/}" 2>&1 | grep Result
done

# 24-check 통합 테스트
python3 .claude/skills/skill-gen-agent/scripts/tests/run_all.py

# Bash 스크립트 문법
for f in scripts/*.sh .claude/hooks/*.sh; do bash -n "$f" && echo "OK: $f"; done
```

**원칙** (Boris Cherny): Claude 가 *눈으로 확인 가능* 한 검증 명령을 명시. "확인해 주세요" 가 아니라 자신이 실행.

---

## 라이선스

MIT — 상세는 [LICENSE](LICENSE). upstream credits (gstack: garrytan, mattpocock skills 등) 동일 라이선스 명시.

---

> *이 README 는 회사 비유로 정리한 요약본. 부서별 전체 skill 표는 [.claude/skills/INDEX.md](.claude/skills/INDEX.md), 자율 진입점 protocol 은 [`skills-src/simonk/`](skills-src/simonk/) 를 보세요.*
