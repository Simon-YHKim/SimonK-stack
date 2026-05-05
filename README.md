# SimonK-Stack

> 서비스 기획부터 개발, 수익화, 그로스, Exit까지 — Claude Code가 **자동으로 올바른 절차를 따르게** 만드는 skill 라이브러리.

**[simonk-stack.pages.dev](https://simonk-stack.pages.dev)** · [![validator](https://img.shields.io/badge/skill--validator-48%2F48%20PASS-brightgreen)]() [![license](https://img.shields.io/badge/license-MIT-blue)]()

---

## 이게 뭔가요?

**문제**: AI 코딩 어시스턴트는 큰 작업을 시키면 매번 다른 순서로 일하고, 같은 실수를 반복합니다.

**해결**: 48개 skill (작업 매뉴얼)을 미리 준비해 Claude Code가 **일관된 절차**를 따르게 합니다.

```
"새 앱 만들자"        → app-dev-orchestrator  → 21단계 파이프라인
"PMF 분석해줘"        → pmf-analyzer          → 3 case 시나리오 예측
"결제 붙여줘"          → payment-integrator    → Stripe/PortOne + 웹훅 + 테스트
"수익화 테스트 돌려줘"  → revenue-scenario-tester → 7 전문 에이전트, 80+ 시나리오
"exit 전략 세워줘"     → exit-strategy-planner → IPO/M&A 로드맵
```

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

## Skill 카탈로그 — 48개

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
| `nextjs-optimizer` | "Next.js 최적화" | 5대 성능 영역 감사 (이미지/렌더링/번들/캐싱) |
| `stitch-design-flow` | "Stitch 프롬프트" | DESIGN.md → Safe/Bold/Wild 프롬프트 |
| `project-context-md` | "CLAUDE.md 만들어줘" | 프로젝트 CLAUDE.md 생성/갱신 (검증 루프 핵심) |

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

## 실행 파이프라인 (36 skills)

위 48개 skill 외에, [Gstack](https://github.com/garrytan/gstack) 기반 36개 실행 도구가 자동 설치됩니다:

`/office-hours` `/plan-ceo-review` `/plan-eng-review` `/plan-design-review` `/plan-devex-review` `/autoplan` `/design-consultation` `/design-shotgun` `/design-review` `/design-html` `/qa` `/qa-only` `/review` `/benchmark` `/health` `/codex` `/ship` `/land-and-deploy` `/canary` `/setup-deploy` `/document-release` `/cso` `/careful` `/guard` `/freeze` `/unfreeze` `/retro` `/investigate` `/browse` `/learn` `/devex-review` `/checkpoint` `/pair-agent` `/setup-browser-cookies` `/open-gstack-browser` `/gstack-upgrade`

**총 84개 skill** — 기획부터 Exit까지 전 과정 커버.

---

## 작동 원리

### 서비스 개발 전체 흐름

```
아이디어
  │
  ├─ aarrr-growth-planner      ← AARRR 프레임워크
  ├─ pmf-analyzer               ← 3 case PMF 예측
  ├─ aha-moment-optimizer       ← 아하 모먼트 발굴
  │
  ├─ stack-architect            ← 프론트/백/API/배포 결정
  │   ├─ app-platform-selector  ← Hybrid/PWA/Native
  │   ├─ db-selector            ← DB 선택
  │   └─ deploy-configurator   ← CI/CD + 호스팅
  │
  ├─ monetization-planner       ← 수익 모델 설계
  │   ├─ payment-integrator     ← 결제 구현
  │   ├─ global-payment-planner ← 글로벌 규제
  │   └─ revenue-scenario-tester ← 80+ 시나리오 검증
  │
  ├─ analytics-integrator       ← 분석 도구
  │   └─ tag-manager-integrator ← 이벤트 추적
  │
  ├─ growth-engine → store-launcher → pmf-analyzer (리포팅)
  │
  └─ exit-strategy-planner      ← IPO/M&A/Exit
```

### SessionStart Hook

```
세션 시작 → .claude/hooks/session-start.sh 실행
  ├─ 실행 도구 설치 (첫 실행만, ~30초)
  ├─ 48개 skill → ~/.claude/skills/ 복사
  ├─ Instincts 4파일 seed (세션 간 학습)
  ├─ LLM Wiki 자동 bootstrap
  └─ marker 기록 (재실행 시 <1초)
```

---

## 테스트

| 테스트 | 결과 |
|---|---|
| Static validation | **48/48 PASS** |
| Bash syntax | **18/18 PASS** |
| YAML frontmatter | **48/48 PASS** |
| Trigger conflict | **2건 (의도적 핸드오프)** |

---

## FAQ

**Q. 총 몇 개 skill?**
48개 (전략+개발+수익화+보안+분석) + 36개 실행 도구 = **84개**.

**Q. 다른 repo에서 쓰려면?**
`scripts/setup-repo.sh /path/to/target` → 상세: [docs/USING-IN-OTHER-REPOS.md](docs/USING-IN-OTHER-REPOS.md)

**Q. 한국어로만 말해도 되나요?**
네. 모든 skill에 한/영 트리거 병기.

**Q. 업데이트는?**
```bash
cd SimonK-stack && git pull && ./scripts/install.sh
```

---

## 크레딧

| 출처 | 기여 |
|---|---|
| [Gstack](https://github.com/garrytan/gstack) — garrytan | 실행 파이프라인 36 skill |
| [Karpathy](https://x.com/karpathy) | 4원칙 (코딩 가이드라인) + llm-wiki 패턴 |
| [Superpowers](https://github.com/obra/superpowers) — obra | TDD, worktree, 검증 루프 |
| [everything-claude-code](https://github.com/affaan-m/everything-claude-code) | Instincts 학습, research-first |
| [Skill-Agent](https://github.com/Simon-YHKim/Skill-Gen-Agent) | validate_skill.py 검증 도구 |
| [Impeccable](https://github.com/pbakaus/impeccable) | AI Slop 방지 디자인 원칙 |
| [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) | Karpathy 4원칙 정제 |

## 라이선스

[MIT](LICENSE). 상업적 사용·수정·배포 자유.
