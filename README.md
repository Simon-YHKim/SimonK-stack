# SimonK-Stack

> **스킬을 한 요청으로 조합하는 라이브러리.** `/vibe`가 메인 조정자이고, `simonk`는 그 아래의 스프린트 절차입니다. 사용자 = 목표와 권한의 결정자.

![version](https://img.shields.io/badge/version-0.1.0-5b8cff) ![license](https://img.shields.io/badge/license-MIT-green) [![validate](https://github.com/Simon-YHKim/SimonK-stack/actions/workflows/validate-plugin.yml/badge.svg)](https://github.com/Simon-YHKim/SimonK-stack/actions/workflows/validate-plugin.yml) [![skills](https://img.shields.io/badge/skills-132-brightgreen)]() [![harness](https://img.shields.io/badge/simonK-autonomous-blueviolet)]()

**Site**: [simonk-stack.pages.dev](https://simonk-stack.pages.dev) · **English**: [README.en.md](README.en.md) · **자매 레포**: [SimonKWiki](https://github.com/Simon-YHKim/SimonKWiki) (PRIVATE) — 세션 간 학습 누적

---

## 설치 / Install

Claude Code 마켓플레이스에서 바로 설치 (Install directly from the Claude Code marketplace):

```
/plugin marketplace add Simon-YHKim/SimonK-stack
/plugin install simonk-stack@simonk-stack
```

> git clone 기반 3-모드 설치(Direct / Vendor / Bootstrap)는 아래 [빠른 시작](#-빠른-시작--3-가지-설치-모드) 참고.

### Codex 스킬 설명 예산

`Skill descriptions were shortened ...`는 초기 선택 목록의 설명이 줄었다는 경고이며, 선택한 `SKILL.md` 본문을 삭제하지 않습니다. 설명은 고유 목적·호출 조건·산출물 위주로 짧게 유지합니다. `/vibe` 진입을 확실히 지정하려면 Codex의 스킬 목록에서 실제 등록 이름을 선택하세요. 플러그인이 namespace를 붙였다면 `$simonk-core:vibe`, 독립 스킬로 등록됐다면 `$vibe`처럼 이름이 다를 수 있습니다.

동일 패키지가 `.agents/skills`와 `.codex/skills`에 따로 복사돼 있으면, 파일·참조를 비교한 뒤 한 경로만 `~/.codex/config.toml`에서 비활성화할 수 있습니다. 이름이 같다는 이유만으로 다른 구현이나 플러그인을 끄지 마세요.

```toml
[[skills.config]]
path = "/absolute/path/to/redundant/skill/SKILL.md"
enabled = false
```

설정 원본을 백업하고 **새 Codex 세션**에서 확인하세요. 선택 경로의 파일은 그대로 두며, 해당 비활성화 항목을 제거하면 복구됩니다. 다른 플러그인 수에 따라 경고가 남을 수 있습니다. [공식 스킬 로딩·비활성화 안내](https://learn.chatgpt.com/docs/build-skills)

본문 보존과 자동 선택 정확도는 별개입니다. [선택 전후 비교 절차](docs/skill-selection-validation.md)는 대표 요청 30개와 오프라인 채점 도구를 제공하며, 실제 Claude/GPT 관측이 없으면 `pending`으로 남깁니다. 단위 테스트 통과를 모델 정확도 통과로 해석하지 마세요.

---

## 회사 비유 — 한 페이지로 보기

```
                  ┌─────────────────────────┐
                  │  사용자 = Founder / CEO │
                  └────────────┬────────────┘
                               │
                  ┌────────────▼────────────┐
                  │  /vibe = Main coordinator│  ← simonk 등 필요한 절차 선택
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

새 프로젝트 시작 시 *무엇을 왜* 만들지 결정. /vibe가 목표에 맞춰 필요한 기획 절차를 선택합니다.

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
| `/design-system-page` | design.md → design-system.html + A4 brand-book PDF 자동 생성 |
| `/slides` | zero-dep HTML 슬라이드 (16:9, 3 preview → 선택) — 발표·피치덱 |

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
| `/vercel-react` · `/vue-best-practices` · `/building-native-ui` · `/remotion-best-practices` · `/scientific-paper` | 도메인별 best practices (React/Vue/RN/Remotion video/학술논문) |

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
| `/multi-terminal-dispatcher` | 중앙 계획·상태·비용을 공유하는 준비된 작업 묶음 실행; 기본은 미리보기 |

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
| `/simonk-report` | simonK Phase 6 자동 호출 — `.simonk/reports/<TS>.html` 자체 완결 보고서 + SendUserFile 로 모바일 첨부. 단독 `/simonk-report` 호출도 가능 |
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
| `/find-skill` | 외부 awesome-claude-skills (26k★) + 내부 INDEX 자동 검색 |
| `/office-docs` | Docx / Xlsx / Pptx / PDF 사무 문서 (Anthropic Big Four) |
| `/web-publisher` | 웹사이트 자동 로그인·폼·업로드 (browse + auth) |
| `/notebooklm-import` | YouTube 자막 + PDF + 웹 → SimonKWiki 페이지 |
| `/gstack-upgrade` | gstack 자체 업그레이드 (install type 자동 감지) |
| `/omc-upgrade` / `/omo-upgrade` / `/openharness-upgrade` / `/opencowork-upgrade` / `/designmd-upgrade` | 각 vendored 외부 stack 단독 최신화 |
| `/update-config` | settings.json·hooks·permissions 관리 |
| `/init` / `/loop` / `/verify` / `/run` | 일반 개발 유틸 |

---

## 📦 같이 들어 있는 앱 — AI Usage Widget

`apps/ai-usage-widget/` — Windows 작업 표시줄 옆에 Claude·Codex·Grok·Antigravity **구독 사용량**(5시간·주간 한도, 리셋까지 남은 시간)을 띄우는 Electron 위젯. 각 공급자의 **공식 CLI 경로만** 쓰고, 조회에 실패하면 가짜 숫자 대신 "미확인"과 마지막 실측 시각을 보여 준다.

```powershell
# 소스에서 빌드 → 검증 → 사용자 전용 설치 (Windows, node + pnpm + git 필요)
& ".\skills-src\ai-usage-widget-install\scripts\install-widget.ps1"
& ".\skills-src\ai-usage-widget-install\scripts\install-widget.ps1" -Status   # 상태만
```

Claude Code 안에서는 `/ai-usage-widget-install` 또는 "AI 사용량 위젯 설치해줘". 로그인(브라우저·기기 코드)은 위젯 화면에서 사용자가 직접 한다. 타사 로고의 권리는 각 소유자에게 있다 — `NOTICE` 참고.

## /vibe — 메인 진입점, simonk — 스프린트 절차

기존 LLM 세션에서 `/vibe <원하는 결과>`를 사용합니다. 필요한 스킬과
소프트웨어를 고르고, 모델·effort·계정·쿼터·추가 비용·검증을 한 계획으로
관리합니다. `/simonK <task>`도 같은 조정자 아래의 6단계 스프린트 절차입니다.

명확화 → 의존성·리뷰 계획 → 준비된 작업 실행 → 검증·복구 → 범위 내 Git
반영 → 결과 보고. 무조건 병렬 실행하거나 모든 저장소를 자동 push하지 않습니다.
추가 과금 기본값은 $0이며, 미확인 과금이나 사용량을 0으로 간주하지 않습니다.
GUI가 꼭 필요한 일만 내부 vibe-bot 경로로 전달합니다.

PowerShell의 `simonK`는 슬래시 명령과 다르게 **구조화된 오프라인 계획 전용**입니다.
이전의 `simonK "task"`와 인자 없는 Claude 실행은 차단됩니다.

```powershell
# 기존 세션에 함수를 직접 정의하려면 검토한 지속 clone에서만:
. ./scripts/simonk.ps1
# 배치 스크립트는 binding 실패도 중단하고 종료코드를 전달합니다.
$ErrorActionPreference = 'Stop'
simonK -RequestPath request.json -RuntimePath runtime.json
# exit $LASTEXITCODE  # 배치 파일에서만; 대화형 셸에서는 종료하지 마세요.
```

입력 계약: [vibe 실행 계약](skills-src/vibe/references/orchestration.md).
[스프린트 절차](skills-src/simonk/SKILL.md)와
[다중 실행기](skills-src/multi-terminal-dispatcher/SKILL.md)는 같은 중앙 정본을 소비합니다.
계획 성공·작업 시작·출력 수신·비용 정산·검증 완료는 서로 다릅니다.

### 선택 사항: PowerShell 7 프로필 연결

검토된 실행기·중앙 planner가 일치하는 **지속 일반 clone**을 명시하세요.
임시 linked worktree나 아직 구버전인 main으로 연결하지 않습니다.

```powershell
# 기본은 읽기 전용 미리보기
pwsh -NoProfile -NonInteractive -File scripts/install-simonk-profile.ps1 -RepoRoot 'E:/persistent/SimonK-stack'
# 미리보기와 대상을 확인한 뒤에만 같은 명령에 -Apply 추가
```

기본 대상은 현재 PowerShell의 CurrentUserAllHosts 프로필이며, 절대 경로
`-ProfilePath`로 지정할 수 있습니다. `-Apply`는 정확히 인식된 v1/v2 관리 블록만
교체하고 사용자 코드·인코딩을 보존합니다. 변경 전 파일은 고유 백업으로 남기며,
수정된 블록·중복 표식·불명확한 인코딩은 쓰지 않고 차단합니다. 재적용은 멱등적입니다.

예제 문자열·주석·중첩 함수에 있는 표식은 AST 문맥 검사로 제외합니다.
시작 시 파일의 쓰기·교체를 잠근 상태에서 해시를 확인하고 함수를 로드합니다. 변경·누락·조회 실패 시 로드하지
않고 재설치를 안내합니다. 설치 중 dot-source, 환경변수·gcloud·Team Mode·결제
설정 변경은 없습니다. 기존 환경변수는 그대로 두며 이 명령으로 정리하지 않습니다.
적용 중 다른 편집기를 닫으세요. 마지막 재확인은 외부 편집기 전체를 잠그는 기능이
아닙니다. 복구는 백업·현재 파일을 확인하고 덮어쓰기 권한을 받은 뒤 수동으로 합니다.

이 연결은 전체 스킬 설치, planner 패키지 무결성, 열린 세션의 실행 무결성 또는
5계열 모델 실호출 검증을 대신하지 않습니다. 정식 설치·재설치 checksum은 별도 게이트입니다.

검증: `python -B -m unittest discover -s scripts/tests -p test_install_simonk_profile.py`
(임시 프로필·복제본만 사용, 사용자 프로필 변경 없음).

---

## 🚀 빠른 시작 — 3 가지 설치 모드

### A. Direct install — "내 ~/.claude/ 에만 박아"

```bash
git clone https://github.com/Simon-YHKim/SimonK-stack.git ~/SimonK-stack
cd ~/SimonK-stack && ./scripts/install.sh
```

global `~/.claude/skills/` 에 132 skill + shared scripts + instincts 배포. SessionStart hook 은 settings.json 에 수동 등록.

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
| [`.claude/skills/INDEX.md`](.claude/skills/INDEX.md) | 132 skill 카탈로그 (이 README 의 부서 표보다 자세) |
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

# 전체 repo 검증 (132 skill sweep)
for d in skills-src/*/ .claude/skills/*/; do
  [ -f "${d}SKILL.md" ] || continue
  python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py "${d%/}" 2>&1 | grep Result
done

# 24-check 통합 테스트
python3 .claude/skills/skill-gen-agent/scripts/tests/run_all.py

# 벤치마크 수집기 회귀 검사 (네트워크 없이 임시 Wiki/cache만 사용)
python3 -m unittest discover -s scripts/tests -p test_fetch_model_benchmarks.py

# Bash 스크립트 문법
for f in scripts/*.sh .claude/hooks/*.sh; do bash -n "$f" && echo "OK: $f"; done
```

**원칙** (Boris Cherny): Claude 가 *눈으로 확인 가능* 한 검증 명령을 명시. "확인해 주세요" 가 아니라 자신이 실행.

### 벤치마크 수집은 Wiki 갱신이 아닙니다

`scripts/fetch-model-benchmarks.py`는 검토 전 raw 후보만 수집하며 Wiki 본문·날짜·로그와 라우팅 registry를 수정하지 않습니다.
캐시의 `attempted_at`은 조회 시각일 뿐이며 `data_as_of: null`, `validation_status: unverified`, `wiki_updated: false`를 유지합니다.
기존 `fetched_at` 캐시도 검증된 최신 모델 정보로 취급하지 않습니다. 모델 라우팅은 `/vibe`의 중앙 registry와 최신 계정·transport 증거를 사용합니다.

- 종료코드 `0`: **요청한 모든 source**에 형식상 유효한 raw 행이 있습니다. 벤치마크 사실 검증, 전체 leaderboard의 완전한 수집 또는 Wiki 업데이트 성공을 뜻하지 않습니다.
- 종료코드 `2`: 실패·0건·파서 미구현·일부 source 누락·잘못된 행 또는 캐시 저장 실패입니다. 기존 캐시는 유지합니다.
- `--dry-run`: 수집/표시만 하며 파일을 쓰지 않습니다. **네트워크는 사용하므로 오프라인 검사는 위 unittest 명령을 사용합니다.**
- 현재 Vellum/LLM Stats/Aider 파서는 미구현이므로 `--source all`은 incomplete로 종료합니다. 이미 구현된 단일 source만 선택할 수 있지만 결과는 여전히 미검증입니다.
- 외부 Wiki cron은 실패 종료코드도 검사해야 합니다. 이 저장소의 변경은 별도 Wiki 저장소의 cron이나 설치본을 자동 교체하지 않습니다.

---

## 라이선스

MIT — 상세는 [LICENSE](LICENSE). upstream credits (gstack: garrytan, mattpocock skills 등) 동일 라이선스 명시.

---

> *이 README 는 회사 비유로 정리한 요약본. 부서별 전체 skill 표는 [.claude/skills/INDEX.md](.claude/skills/INDEX.md), 자율 진입점 protocol 은 [`skills-src/simonk/`](skills-src/simonk/) 를 보세요.*
