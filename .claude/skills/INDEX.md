# Skill Index

**curated simon-stack** skill 세트의 카테고리별 맵. 세션 시작 시 참고용.
이 표는 simon-stack 큐레이션 셋(skills-src + 개발용 dev skill)을 매핑한다. gstack 홈 설치본(`~/.claude/skills/gstack/` 및 약 21개 gstack 홈 skill — `skillify`, `spec`, `scrape`, `diagram`, `make-pdf`, `ios-*` 등)은 여기에 카탈로그하지 않으며, 전체 목록은 `/gstack` 진입점으로 조회한다. 일부 자주 쓰는 gstack 홈 skill 은 아래 카테고리 표에 `(Gstack)` 표기로 교차 등재돼 있고, 나머지는 부록(맨 아래 "Gstack 홈 설치본" 표) 참고.

**skills-src/ 128개** + `.claude/skills/` 개발용 4개 = **총 132개** (simon-stack 큐레이션 셋 기준 — 약 21개 gstack 홈 skill 은 이 132 카운트에서 제외). (2026-06-13 갱신 — preamble rescope, gstack 홈 skill 부록 등재, `agent-delegate` 카테고리 표 등재. `simon-handoff` 은 Session/Context 표에 이미 등재됨.)

> **검증**: `python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py <path>` (Windows는 `PYTHONIOENCODING=utf-8` 또는 검증기 UTF-8 패치 필요). **2026-06-13 재검증**: simon-stack 스킬 전부 통과(`wiki-query` E013 수정). 검증기 cp949 크래시·E008 "Todo-list" 오탐 수정(SimonK-stack `4aacecd`). Gstack 스킬은 긴 커맨드-doc 포맷이라 E007/E008 평가 제외.
> **신규 (PR #8)**: `session-context-tracker` · `html-default-output` (+ `context-guardian` 1.1.0 / `agent-delegate` 1.1.0 보강)

## 🧭 Orchestrators (상위 지휘)

| Skill | 역할 |
|---|---|
| `app-dev-orchestrator` | 신규 앱 21단계 마스터 파이프라인 |
| `security-orchestrator` | 보안 감사 5단계 순차 실행 |
| `autoplan` (Gstack) | CEO/Design/Eng/DX 리뷰 자동 파이프라인 |
| `model-router` | task type → best LLM 모델 자동 매핑 (2026-05 매트릭스, sprint v23 Phase A) |
| `multi-terminal-dispatcher` | model-router + Windows Terminal/psmux/VS Code tasks 병렬 launcher (sprint v23 Phase B) |
| `agent-delegate` | sub-agent 위임 플랜 — task 분해 + context envelope(파일 경로만) + output contract + 패턴(Fan-out/Pipeline/Supervisor). app-dev-orchestrator·simon-worktree 가 사용 |
| `simonk` | 단일 자율 진입점 (6-phase + Boundary Check + multi-agent dispatch sprint v23 Phase B) |
| `simonk-report` | simonK Phase 6 자동 호출 — `.simonk/reports/<TS>.html` 생성 + SendUserFile 자동 첨부. 명시 `/simonk-report` 도 가능 |
| `stack-update` | SimonK Stack 전체 holistic 최신화 — 본체+Wiki+gstack+5 vendored+skill 재설치 위임 |
| `dev-orchestrator` | 일반 구현 7단계 파이프라인 (진단 → 구조 점검 → TDD → 시나리오 → 스캔 → 정리 → 커밋) |
| `phase4-game-orchestrator` | 게임 트랙 (Q3 2026) orchestrator placeholder — Godot/Phaser/Three.js · ComfyUI · Suno |
| `simon-ohmo` | OpenHarness Ohmo personal agent — Phase 6 (27Y Q1+) placeholder, 폐쇄망 운영 |


## 🧪 Meta — skill 제작·검증

| Skill | 역할 |
|---|---|
| `skill-gen-agent` | skill 생성·리팩토링·검증·테스트 (Skill-Agent vendored: validate_skill.py · test_skill.py · refactor_skill.py · version_log.py) |

## 🛡️ Session / Context 관리

| Skill | 역할 |
|---|---|
| `context-guardian` | 컨텍스트 고갈 예방 + 실측 한도 관리 + 세션 복구 (3 mode: prevention / monitoring / recovery) |
| `/checkpoint` (Gstack) | 일반 작업 스냅샷 저장·재개 (in-session, ephemeral OK) |
| `simon-handoff` | **세션 간 git-persistent 핸드오프** — docs/HANDOFF.md prepend + PR auto-merge to main. 다른 세션이 `git pull` 한 번으로 복원 |
| `perspectives` | **세션 blind-spot 감사** — Core 5 (User/Business/Technical/Security/Future-self) + 세션 특화 N stakeholder. perspectives.md 누적 append + SessionStart hook 자동 알림 |
| `session-context-export` | 세션 종료 핸드오프 — sprint state snapshot (`.simonk/session-<TS>`) export |

## 📋 Planning (플래닝)

| Skill | 역할 |
|---|---|
| `simon-research` | 리서치 우선 — 공식 문서·경쟁 제품 수집 |
| `office-hours` (Gstack) | YC 6문 forcing question |
| `plan-ceo-review` (Gstack) | 10-star 스코프 재정의 |
| `plan-eng-review` (Gstack) | 엔지니어링 플랜 락다운 |
| `plan-design-review` (Gstack) | 디자인 플랜 리뷰 |
| `plan-devex-review` (Gstack) | 개발자 경험 플랜 리뷰 |
| `grill-me` | 1-Q-at-a-time 인터뷰 — 사용자 계획의 결정 트리 청소 (simon-tdd RED 전) |
| `domain-glossary` | 프로젝트 `CONTEXT.md` 도메인 용어집 — instincts·CLAUDE.md·ADR 와 분리된 layer |
| `founder-context` | **4-file 패턴**: me.md / vision.md / design.md / workingstyle.md 를 프로젝트 루트에 한 번에 생성. wiki·instincts·simon-design-first 와 import 동기화 |
| `stack-architect` | 기술 아키텍처 결정 — 프론트/백엔드/API/배포를 규모에 맞게 매칭 |
| `sprint-optimizer` | 스프린트 3안 비교 → best case 추천 → 반복 고도화 |
| `app-platform-selector` | Hybrid / PWA / Native 플랫폼 결정 + 스토어 승인 전략 |
| `db-selector` | DB·스토리지 선택 (Supabase/Firebase/PostgreSQL …) + 비용 추정 |
| `tech-preference-tracker` | 언어·프레임워크 선택을 이전 프로젝트 결정과 일관되게 유지 |

## 🎨 Design

| Skill | 역할 |
|---|---|
| `design-consultation` (Gstack) | DESIGN.md 생성, 브랜드 시스템 |
| `stitch-design-flow` | Google Stitch 프롬프트 생성기 (수동) |
| `design-shotgun` (Gstack) | 디자인 변형 탐색 |
| `design-review` (Gstack) | 시각 QA, AI slop 탐지 |
| `design-html` (Gstack) | production HTML/CSS 변환 |
| `design-system-page` | design.md → design-system.html + A4 brand-book PDF 자동 생성 |
| `design-system-keeper` | 디자인 시스템 영속·강제: 6 방향 선택 → `.design-system/system.md` 토큰 캡처/자동로드 → 코드서 extract → drift audit. frontend-design(distinctiveness) + interface-design(persistence) 종합, anti-slop 조화 |
| `slides` | zero-dep HTML 슬라이드 (16:9, 3 preview → 선택) — frontend-slides 패턴 |
| `simon-design-first` | UI 코드 전 강제 진단 (audience/purpose/tone) + 레퍼런스 3-5 + 폰트 선택지 — AI slop 방지 게이트 |

## 🛠️ Implementation

| Skill | 역할 |
|---|---|
| `simon-tdd` | RED-GREEN-REFACTOR 강제 + 검증 루프 |
| `vercel-react` | React (Next.js + Vercel) 안정성·성능 best practices |
| `vue-best-practices` | Vue 3 Composition API + Pinia 표준 |
| `building-native-ui` | React Native + Expo (FlashList, Reanimated, EAS) |
| `remotion-best-practices` | 프로그래밍 비디오 (TypeScript + React) |
| `scientific-paper` | LaTeX 논문 + BibTeX + matplotlib/plotly 시각화 |
| `simon-worktree` | 병렬 세션 git worktree 격리 |
| `nextjs-optimizer` | Next.js 5대 영역 성능 최적화 |
| `project-context-md` | 프로젝트 CLAUDE.md 생성 |
| `claude-api` (built-in/runtime) | Claude API / Anthropic SDK 빌드 |
| `auth-builder` | 인증·회원가입·소셜로그인 (Supabase/Clerk/NextAuth + Kakao/Naver + 한국 CI/DI) |
| `karpathy-guidelines` | 코딩 4원칙 강제 — Think Before Coding · surgical only 등 |

## 🔍 Review / QA

| Skill | 역할 |
|---|---|
| `review` (Gstack) | PR 사전 리뷰 (SQL·LLM boundary·side effects) |
| `review` (local) | 일반 코드 리뷰 |
| `qa` (Gstack) | QA 테스트 + 자동 수정 |
| `qa-only` (Gstack) | QA 리포트 only (수정 없음) |
| `codex` (Gstack) | Codex CLI 통합 (review/challenge/consult) |
| `health` (Gstack) | 코드 품질 대시보드 |
| `benchmark` (Gstack) | Core Web Vitals 성능 측정 |
| `devex-review` (Gstack) | 개발자 경험 실측 |
| `browse` (Gstack) | 헤드리스 브라우저 검증 |
| `code-health-guard` | 스파게티 방지 — 파일 배치·레이어 방향·순환의존(madge)·dead export 스캔 |
| `consistency-guard` | JSON-schema 기반 데이터·UI 일관성 검증 (API contract · design token · config) |
| `human-voice-guard` | LLM 어투 탐지·교정 — 사람 목소리로 재작성 |

## 🔒 Security

| Skill | 역할 |
|---|---|
| `security-checklist` | RLS/구독/RateLimit/예산 4대 감사 |
| `authz-designer` | RBAC/ABAC/ReBAC 모델 + IDOR 감사 |
| `paid-api-guard` | 유료 API 6층 방어 + API 설계 |
| `cso` (Gstack) | CSO 모드 — 인프라·시크릿·공급망·STRIDE |
| `careful` (Gstack) | 파괴적 명령 가드 |
| `guard` (Gstack) | 디렉토리 freeze + careful 통합 |
| `freeze` / `unfreeze` (Gstack) | 편집 범위 제한 |
| `keepass-helper` | KeePassXC vault 시크릿 관리 — one-time inject, 키 노출 방지 |

## 🚀 Ship & Deploy

| Skill | 역할 |
|---|---|
| `ship` (Gstack) | 테스트·VERSION·CHANGELOG·PR 생성 |
| `land-and-deploy` (Gstack) | 머지·CI·배포·health 검증 |
| `canary` (Gstack) | 배포 후 라이브 모니터링 |
| `setup-deploy` (Gstack) | 배포 플랫폼 설정 |
| `document-release` (Gstack) | 배포 후 문서 갱신 |
| `deploy-configurator` | 배포 플랫폼 선택 (Cloudflare/Vercel/Fly.io/Railway) + CI/CD + 도메인 + env |
| `release-notes` | 릴리즈 노트·패치 노트·스토어 업데이트 공지 작성 |

## 📈 Growth & Revenue (그로스·수익화)

| Skill | 역할 |
|---|---|
| `pmf-analyzer` | 3-case PMF 예측 (낙관/보통/비관) + Sean Ellis 시뮬레이션 |
| `aarrr-growth-planner` | AARRR 퍼널 전략 + 단계별 KPI + ICE 실험 백로그 |
| `aha-moment-optimizer` | Aha Moment 가설·실험 설계 — TTFV 단축 |
| `analytics-integrator` | GA4/PostHog/Clarity 분석 스택 + 이벤트 택소노미 + consent 관리 |
| `tag-manager-integrator` | GTM/gtag 이벤트·전환 추적 세팅 |
| `growth-engine` | 이메일(Resend)·푸시(OneSignal/FCM)·어트리뷰션·A/B 그로스 인프라 |
| `viral-launch` | 채널별 바이럴 런칭 플레이북 (인스타·한국 커뮤니티·in-app share) |
| `monetization-planner` | 수익 모델 설계 (구독/광고/거래/freemium) |
| `payment-integrator` | Stripe / PortOne / RevenueCat / 인앱결제 통합 |
| `global-payment-planner` | 국가별 결제 규제·PG 조합·세금/VAT 전략 |
| `subscription-manager-selector` | 구독 관리 플랫폼 비교·선택 (RevenueCat vs Stripe …) |
| `revenue-scenario-tester` | 80+ 결제 시나리오 통합 테스트 (7 specialized agents) |
| `ad-monetization` | 광고 SDK (AdMob/AdSense) 통합 + 배치 전략 + 정책 준수 |
| `pink-tax-advisor` | 공격적 수익 극대화·가격 심리 전략 (명시 요청 시에만) |
| `store-launcher` | Play Store / App Store 등록 + ASO |
| `exit-strategy-planner` | IPO / M&A / SPAC exit 로드맵 + 단계별 KPI |

## 🐛 Debug

| Skill | 역할 |
|---|---|
| `investigate` (Gstack) | root cause 체계적 조사 (4단계) |
| `debug` (local) | 일반 디버깅 |
| `zoom-out` | 한 layer 위에서 모듈 맵 — `/explain` 의 escalation (manual-only) |

## 📚 Learning / Memory

| Skill | 역할 |
|---|---|
| `simon-instincts` | 실수·패턴 누적 (~/.claude/instincts/) |
| `learn` (Gstack) | 프로젝트 학습 관리 |
| `retro` (Gstack) | 주간 엔지니어링 회고 |
| `checkpoint` (Gstack) | 상태 스냅샷·재개 |
| `notebooklm-import` | YouTube 자막 + PDF + 웹 → SimonKWiki 페이지로 변환·통합 |
| `llm-wiki-builder` | SimonKWiki 페이지 작성·인제스트·유지 (T-xxx / M-xxx / entities) |
| `wiki-query` | 위키 인덱스 검색 + [[wikilink]] 인용 답변 |
| `wiki-lint` | 위키 무결성·건강검진 |
| `wiki-ingest` | raw 소스 자료 → 위키 컴파일 |
| `obsidian-markdown` | Obsidian Flavored Markdown (wikilink·callout·properties) 작성·편집 |
| `obsidian-bases` | Obsidian Bases (.base) 뷰·필터·포뮬러 |
| `obsidian-cli` | Obsidian CLI 로 노트·태스크·플러그인 제어 |
| `json-canvas` | JSON Canvas (.canvas) 노드·엣지·마인드맵 작성 |

## 🧰 Utilities

| Skill | 역할 |
|---|---|
| `commit` (local) | Conventional Commits 생성 |
| `refactor` (local) | 구조 개선 |
| `explain` (local) | 코드 설명 |
| `test-gen` (local) | 테스트 생성 |
| `simplify` (built-in/runtime) | 코드 단순화 |
| `find-skill` | 외부 awesome-claude-skills (26k★) + 내부 INDEX 자동 검색 |
| `office-docs` | Docx / Xlsx / Pptx / PDF 사무 문서 (Anthropic Big Four) |
| `web-publisher` | 웹사이트 자동 로그인·폼 작성·업로드 (browse + auth) |
| `defuddle` | 웹페이지 → 클린 마크다운 추출 (Defuddle CLI, WebFetch 대체) |
| `gcloud-helper` | gcloud 인증 진단 + ghost project 자동 수정 + env vars inject |
| `loop` (built-in/runtime) | 주기 작업 실행 |
| `update-config` (built-in/runtime) | settings.json 구성 |
| `keybindings-help` (built-in/runtime) | 키바인딩 커스터마이징 |
| `session-start-hook` | 세션 시작 hook 관리 |
| `caveman` | 응답 75% 토큰 압축 모드 — 긴 세션 시 토글 |
| `pair-agent` (Gstack) | 원격 에이전트 페어링 |
| `setup-browser-cookies` (Gstack) | 브라우저 쿠키 가져오기 |
| `open-gstack-browser` (Gstack) | GStack Browser 실행 |
| `gstack-upgrade` (Gstack) | Gstack 버전 업데이트 (gstack-only) |
| `stack-update` | **전체 SimonK Stack holistic 최신화** — SimonK-stack + Wiki + gstack + 5 vendored + skill 재설치 |
| `omc-upgrade` | vendored oh-my-claudecode 단독 최신화 |
| `omo-upgrade` | vendored oh-my-openagent 단독 최신화 |
| `openharness-upgrade` | vendored OpenHarness 단독 최신화 |
| `opencowork-upgrade` | vendored open-cowork 단독 최신화 |
| `designmd-upgrade` | vendored design.md 단독 최신화 |
| `gstack` (Gstack 메타, built-in/runtime) | Gstack 전체 진입점 |

---

## 부록 — Gstack 홈 설치본 (이 132 카운트 제외)

> 아래는 **gstack 홈 설치본**(`~/.claude/skills/`)에 함께 깔리는 gstack skill 로, simon-stack 큐레이션 셋이 아니다 (위 132 카운트에 미포함). 전체 목록·진입점은 `/gstack` 로 조회. 여기 등재는 가시성 용도이며, **gstack skill 자체는 SimonK-stack 에서 수정하지 않는다** (upstream garrytan/gstack 책임 도메인).

| Skill | 역할 |
|---|---|
| `_gstack-command` (Gstack) | gstack 내부 커맨드 디스패처 |
| `benchmark-models` (Gstack) | gstack skill 크로스-모델 벤치마크 |
| `context-save` (Gstack) | 작업 컨텍스트 저장 |
| `context-restore` (Gstack) | `/context-save` 로 저장한 컨텍스트 복원 |
| `diagram` (Gstack) | 영문 설명 → diagram triplet (source + `.excalidraw` + 렌더) |
| `document-generate` (Gstack) | 기능·모듈·프로젝트 문서 신규 생성 |
| `landing-report` (Gstack) | workspace-aware ship 큐 대시보드 (read-only) |
| `make-pdf` (Gstack) | PDF 생성 |
| `plan-tune` (Gstack) | 플랜 튜닝 |
| `scrape` (Gstack) | 웹 스크레이핑 |
| `setup-gbrain` (Gstack) | gbrain 셋업 |
| `sync-gbrain` (Gstack) | gbrain 동기화 |
| `skillify` (Gstack) | skill 화 (OMC 계열) |
| `spec` (Gstack) | 스펙 생성 |
| `ios-clean` (Gstack) | iOS DebugBridge SPM + `#if DEBUG` 배선 제거 |
| `ios-fix` (Gstack) | 자율 iOS 버그 수정 |
| `ios-qa` (Gstack) | SwiftUI 앱 실기기 QA |
| `ios-sync` (Gstack) | iOS 디버그 브리지 upstream 템플릿 동기화 |
| `ios-design-review` (Gstack) | iOS 앱 실기기 시각 디자인 감사 |

---

## 우선순위 규칙

### 1. "새 앱 만들고 싶어" 류
→ **app-dev-orchestrator** 최우선. 다른 플래닝 skill 은 그 안에서 호출됨.

### 2. "보안 점검" 류
→ **security-orchestrator** 최우선. 단독 영역만 필요하면 개별 skill.

### 3. 중복 영역 구분

| 상황 | 선택 |
|---|---|
| PR 전 코드 리뷰 | Gstack `/review` (SQL·LLM·side effects 특화) |
| 일반 코드 리뷰 | local `review` |
| 근본 원인 디버깅 | Gstack `/investigate` (4단계 체계) |
| 단순 버그 고치기 | local `debug` |
| 프로젝트 학습 저장 | Gstack `/learn` (프로젝트 scope) |
| Claude 실수 누적 | `simon-instincts` (글로벌 scope) |
| TDD 사이클 | `simon-tdd` (구현 단계) |
| 배포용 테스트 | `/ship` 내부 테스트 단계 |

### 4. Gstack vs simon-stack

- **Gstack**: 실행 파이프라인 (명령어·스크립트 있음, bin/ 활용)
- **simon-stack**: 방법론·보안·학습 (markdown 가이드 중심)
- 충돌 시 Gstack 이 구체 실행, simon-stack 이 상위 원칙 제공

---

## 업데이트

새 skill 추가 시 이 파일도 갱신. `/retro` 주간 회고 시 체크.
