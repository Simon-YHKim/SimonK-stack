# Skill Index

이 환경에 설치된 모든 skill 의 카테고리별 맵. 세션 시작 시 참고용.

**총 51개** skill (Gstack 36 + simon-stack 13 + 기타 2).

## 🧭 Orchestrators (상위 지휘)

| Skill | 역할 |
|---|---|
| `app-dev-orchestrator` | 신규 앱 21단계 마스터 파이프라인 |
| `security-orchestrator` | 보안 감사 5단계 순차 실행 |
| `autoplan` (Gstack) | CEO/Design/Eng/DX 리뷰 자동 파이프라인 |

## 📋 Planning (플래닝)

| Skill | 역할 |
|---|---|
| `simon-research` | 리서치 우선 — 공식 문서·경쟁 제품 수집 |
| `office-hours` (Gstack) | YC 6문 forcing question |
| `plan-ceo-review` (Gstack) | 10-star 스코프 재정의 |
| `plan-eng-review` (Gstack) | 엔지니어링 플랜 락다운 |
| `plan-design-review` (Gstack) | 디자인 플랜 리뷰 |
| `plan-devex-review` (Gstack) | 개발자 경험 플랜 리뷰 |

## 🎨 Design

| Skill | 역할 |
|---|---|
| `design-consultation` (Gstack) | DESIGN.md 생성, 브랜드 시스템 |
| `stitch-design-flow` | Google Stitch 프롬프트 생성기 (수동) |
| `design-shotgun` (Gstack) | 디자인 변형 탐색 |
| `design-review` (Gstack) | 시각 QA, AI slop 탐지 |
| `design-html` (Gstack) | production HTML/CSS 변환 |

## 🛠️ Implementation

| Skill | 역할 |
|---|---|
| `simon-tdd` | RED-GREEN-REFACTOR 강제 + 검증 루프 |
| `simon-worktree` | 병렬 세션 git worktree 격리 |
| `nextjs-optimizer` | Next.js 5대 영역 성능 최적화 |
| `project-context-md` | 프로젝트 CLAUDE.md 생성 |
| `claude-api` | Claude API / Anthropic SDK 빌드 |

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

## 🚀 Ship & Deploy

| Skill | 역할 |
|---|---|
| `ship` (Gstack) | 테스트·VERSION·CHANGELOG·PR 생성 |
| `land-and-deploy` (Gstack) | 머지·CI·배포·health 검증 |
| `canary` (Gstack) | 배포 후 라이브 모니터링 |
| `setup-deploy` (Gstack) | 배포 플랫폼 설정 |
| `document-release` (Gstack) | 배포 후 문서 갱신 |

## 🐛 Debug

| Skill | 역할 |
|---|---|
| `investigate` (Gstack) | root cause 체계적 조사 (4단계) |
| `debug` (local) | 일반 디버깅 |

## 📚 Learning / Memory

| Skill | 역할 |
|---|---|
| `simon-instincts` | 실수·패턴 누적 (~/.claude/instincts/) |
| `learn` (Gstack) | 프로젝트 학습 관리 |
| `retro` (Gstack) | 주간 엔지니어링 회고 |
| `checkpoint` (Gstack) | 상태 스냅샷·재개 |

## 🧰 Utilities

| Skill | 역할 |
|---|---|
| `commit` (local) | Conventional Commits 생성 |
| `refactor` (local) | 구조 개선 |
| `explain` (local) | 코드 설명 |
| `test-gen` (local) | 테스트 생성 |
| `simplify` | 코드 단순화 |
| `loop` | 주기 작업 실행 |
| `update-config` | settings.json 구성 |
| `keybindings-help` | 키바인딩 커스터마이징 |
| `session-start-hook` | 세션 시작 hook 관리 |
| `pair-agent` (Gstack) | 원격 에이전트 페어링 |
| `setup-browser-cookies` (Gstack) | 브라우저 쿠키 가져오기 |
| `open-gstack-browser` (Gstack) | GStack Browser 실행 |
| `gstack-upgrade` (Gstack) | Gstack 버전 업데이트 |
| `gstack` (Gstack 메타) | Gstack 전체 진입점 |

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
