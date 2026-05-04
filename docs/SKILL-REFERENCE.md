# Skill Reference — Simon-stack 상세 문서

> 각 skill 의 **역할 / 구조 / 알고리즘**을 설명합니다.
> README 에서는 카탈로그 테이블만 제공하고, 이 문서에서 상세를 다룹니다.

---

## 목차

1. [Orchestrators (3)](#orchestrators--상위-지휘-3개)
2. [Meta (2)](#meta--기반-원칙-2개)
3. [Security (3)](#security--보안-3개)
4. [Method (5)](#method--방법론-5개)
5. [Knowledge (1)](#knowledge--지식-관리-1개)
6. [Tools (5)](#tools--특수-목적-5개)
7. [Session (2)](#session--세션-관리-2개)
8. [General Dev (6)](#general-dev-6개)

---

## Orchestrators — 상위 지휘 (3개)

### `app-dev-orchestrator`

**역할**: 제로베이스 앱 개발 전 과정 자동화. 21단계 파이프라인.

**알고리즘 (21단계)**:
```
 0. 인터뷰 — 플랫폼/타깃/레포/예산/API/마감
 1. /office-hours — YC forcing questions
 2. simon-research — 경쟁 제품 3개 비교
 3. /plan-ceo-review — 10-star 스코프
 4. simon-design-first — AI slop 방지 디자인 진단
 5. /design-consultation — DESIGN.md
 6. stitch-design-flow — Safe/Bold/Wild 프롬프트
 7. /design-shotgun — 변형 탐색
 8. UltraPlan — 대형 플래닝
 9. authz-designer — RBAC/ABAC/ReBAC
10. paid-api-guard — API 설계 리뷰
11. /plan-eng-review → /autoplan — 플랜 잠금
12. 레포·.env·.gitignore·gitleaks hook
13. simon-worktree — 병렬 격리
14. simon-tdd — RED-GREEN-REFACTOR (Guard Mode)
15. code-health-guard — 아키텍처 검증
16. /design-review → /design-html
17. /qa — QA + 버그 수정
18. security-orchestrator — 보안 5단 감사
19. /benchmark — Core Web Vitals
20. /review → /ship — PR
21. /land-and-deploy → /canary
22. /document-release → /retro
23. simon-instincts → /checkpoint
```

핵심: 이 skill 은 스스로 코드를 쓰지 않음. 각 단계는 다른 skill 호출만 함.

---

### `dev-orchestrator`

**역할**: 일상 개발 작업 (기능 추가, 버그 수정, 리팩토링) 전 과정 자동화. 7단계 파이프라인.

**알고리즘 (7단계)**:
```
1. 진단 — 코드 읽기, 요청 분석 (기능/버그/리팩토링 분류)
2. code-health-guard (proactive) — 파일 위치, import 방향, 함수 크기
3. simon-tdd (Guard Mode) — RED→GREEN→REFACTOR, source-test 동기화 강제
4. test-gen (Scenario Planning) — 복잡 변경 시 7카테고리 시나리오
5. code-health-guard (reactive) — 순환 의존, 중복, naming 재점검
6. review (Pre-Merge Cleanup) — unused import, dead code, 주석 코드 제거
7. commit — Conventional Commits
```

**축약 모드**: 단순 변경 (1파일, 1함수)은 단계 4·5 skip, 단계 6은 unused import만.

---

### `security-orchestrator`

**역할**: 5단계 적대적 보안 감사 → 통합 SUMMARY 리포트.

```
Step 1. security-checklist    → 4대 영역 적대적 테스트
Step 2. authz-designer (감사) → IDOR·권한 상승 스캔
Step 3. paid-api-guard         → 결제 API 6층 방어
Step 4. /cso comprehensive     → 인프라·시크릿·공급망
Step 5. /codex challenge       → 적대적 리뷰

→ docs/security/<date>-SUMMARY.md (심각도 정렬)
→ Critical/High 모두 해결될 때까지 수정 루프
```

---

## Meta — 기반 원칙 (2개)

### `karpathy-guidelines`

**역할**: 모든 코딩 작업의 base behavioral layer. Andrej Karpathy 4원칙 강제.

| 원칙 | 핵심 | 자가 검증 |
|---|---|---|
| **Think Before Coding** | 가정 명시, 모호하면 질문, 트레이드오프 제시 | "50% 미만 확신이면 물어라" |
| **Simplicity First** | 투기 기능 금지, 200줄→50줄 재작성 테스트 | "시니어가 오버엔지니어링이라 할까?" |
| **Surgical Changes** | 인접 코드 개선 금지, 기존 스타일 유지 | "모든 diff 라인이 요청과 연결되는가?" |
| **Goal-Driven Execution** | 명령형→선언형 변환, test-first 목표 | "자동 검증 방법이 있는가?" |

다른 orchestrator (app-dev-orchestrator, dev-orchestrator, simon-tdd) 에서 base 참조.
출처: [Karpathy 트윗](https://x.com/karpathy/status/2015883857489522876) + [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills)

---

### `simon-instincts`

**역할**: Claude 실수를 4개 md 파일에 누적. 세션 시작 시 자동 로드.

| 파일 | 내용 | 예시 |
|---|---|---|
| `mistakes-learned.md` | Claude 실수 | grep -c exit 1 함정 |
| `project-patterns.md` | 프로젝트별 관용 | WORDGE는 Drizzle |
| `korean-context.md` | 한국 시장 특이사항 | 토스 웹훅 헤더 |
| `tool-quirks.md` | CLI 함정 | git clone default branch |

각 entry: `### YYYY-MM-DD — <제목>` + 증상/원인/예방책/출처 4필드.

---

## Security — 보안 (3개)

### `security-checklist`

**역할**: 웹 앱 4대 보안 구조 적대적 감사. 각 영역 5개 공격 시나리오 + SQL drop-in.

**4대 영역**:
- **A. RLS** — ENABLE+FORCE 확인, pg_policies 스캔, 적대적 SELECT/UPDATE 5종
- **B. 구독 상태** — 민감 필드 9개 보호, 웹훅 HMAC+idempotency, audit_log
- **C. 이중 Rate Limit** — user_id+IP 2중키, Edge+App 2층, 티어 차등
- **D. 예산 한도** — Provider/App/User 3계층, circuit breaker

---

### `authz-designer`

**역할**: 프로젝트에 맞는 권한 모델 선택 + DDL 템플릿 + IDOR 감사.

**모델 선택**:
- 역할 소수+고정 → RBAC (Casbin / Postgres RLS)
- 속성 조건 복잡 → ABAC (Oso / Casbin ABAC)
- 문서·팀 협업 그래프 → ReBAC (OpenFGA / SpiceDB)
- 대부분 SaaS → Hybrid

**DDL 4테이블**: `authz_roles`, `authz_role_assignments`, `authz_policies`, `authz_audit_log`

---

### `paid-api-guard`

**역할**: 유료 API 6층 방어 (결제·SMS·지도·이메일).

| Layer | 내용 |
|---|---|
| 1. 네트워크 경계 | BFF 강제, 브라우저 직접 호출 금지, NEXT_PUBLIC_* 금지 |
| 2. 서명·멱등성 | HMAC+nonce+timestamp, Idempotency-Key, raw body 서명 |
| 3. 남용 탐지 | 사용자별 비용 대시보드, 10배 이상 자동 정지, Turnstile |
| 4. 결제 전용 | 시크릿 매니저, tokenize, 환불 OTP, 금액 서버 재계산 |
| 5. 키 탈취 대응 | Canary 키, INCIDENT-PLAYBOOK, push protection, 90일 로테이션 |
| 6. 관측 | 모든 호출 로깅 (user_id, cost, latency), 주간 /retro |

---

## Method — 방법론 (5개)

### `simon-tdd`

**역할**: RED → GREEN → REFACTOR 사이클 강제 + Boris Cherny 검증 루프.

```
RED:      실패하는 테스트 먼저 → npm test FAIL 확인
GREEN:    최소 코드로 통과 → 전체 스위트 재실행
REFACTOR: 동작 보존 구조 개선 → 매 리팩토링마다 테스트
COMMIT:   git add -p → git commit
```

**Guard Mode**: source 파일 변경 시 대응 test 파일 변경이 없으면 BLOCKER.
`bash skills-src/simon-tdd/scripts/tdd-guard-check.sh`

검증 도구 제공 원칙: CLAUDE.md에 서버/테스트/브라우저/DB 접근 명시 필수.

---

### `simon-worktree`

**역할**: 병렬 Claude 세션을 `git worktree`로 격리.

```
1. git worktree add ../myapp-auth -b feat/auth
2. 각 worktree에 독립 Claude 세션 배정
3. .env 심볼릭 링크 또는 복사
4. 메인 worktree 직접 commit ❌ (PR만)
5. 완료 후 git worktree remove + branch delete
```

---

### `simon-research`

**역할**: 플래닝 전 외부 리서치 의무화. 출처 없는 주장 금지.

```
1. 주제 3줄 요약 (What/Why/Success)
2. 검색 키워드 5-10개 (한/영)
3. 1차 자료 병렬 WebFetch (공식 문서 > GitHub > RFC > 블로그)
4. 경쟁 제품 3개+ 비교표
5. docs/research/<date>-<topic>.md 저장
```

금기: 1년+ 블로그 단일 출처, AI 요약 기사 2차 가공.

---

### `agent-delegate`

**역할**: 작업을 sub-agent에 위임하는 3가지 패턴 제공.

| 패턴 | 용도 |
|---|---|
| **Fan-out** | 독립 작업 N개 병렬 (파일별 리팩토링, 테스트 카테고리별 생성) |
| **Pipeline** | 순차 체인 (리서치 → 설계 → 구현 → 검증) |
| **Supervisor** | 장기 작업 감독 (CI 모니터링, 점진적 마이그레이션) |

**핵심 원칙**: file path만 전달 (content 복사 금지), output contract 명시, round-trip 없이 완료.

---

## Knowledge — 지식 관리 (1개)

### `llm-wiki-builder`

**역할**: Karpathy [llm-wiki 패턴](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 구현. RAG 대신 LLM이 영속 wiki를 유지보수.

**3계층 아키텍처**:
```
~/.claude/wiki/Simon-LLM-Wiki/
├── raw/       ← 불변 원본 (사람이 큐레이션)
├── wiki/      ← LLM 소유 (entities, concepts, sources, index.md, log.md)
└── CLAUDE.md  ← schema (wiki 규약)
```

**3개 연산**:

| 연산 | 스크립트 | 동작 |
|---|---|---|
| **Ingest** | `ingest.sh` | 소스 → raw/ 에 stage → LLM이 wiki 페이지 작성 → log.md append |
| **Query** | `query.sh` | index.md 검색 → 답변 + 인용 → 답변도 wiki에 file back |
| **Lint** | `lint.sh` | orphan/broken-link/stale-page 감지 → report |

**Helper scripts**: `wiki-init.sh` (clone+bootstrap), `log-append.sh` (parseable log entry)

**자동화**: SessionStart hook이 매 세션 wiki를 자동 clone or pull. `simon-research` 결과가 자동으로 wiki에 누적.

Wiki 레포: `Simon-YHKim/Simon-LLM-Wiki` (기본, `SIMON_WIKI_REPO` 환경변수로 override)

---

## Tools — 특수 목적 (5개)

### `code-health-guard`

**역할**: 코드 아키텍처 품질 검증. Proactive (코딩 전) + Reactive (코딩 후).

**Proactive 체크리스트**:
- File placement: decision tree로 올바른 위치 결정
- Naming convention: 파일/변수/타입 일관성
- Import direction: 상위 레이어가 하위만 의존
- Function size: > 40 lines → 분리 후보

**Reactive 스캔** (스크립트):
- `check-circular-deps.sh` — 순환 의존 감지 (madge)
- Dead export / unused import 검출
- Large file flagging (> 300 lines)

---

### `simon-design-first`

**역할**: 디자인 작업의 진입 게이트. AI가 바로 HTML/CSS를 쓰는 것을 차단.

**워크플로**:
```
1. 진단 (청중/목적/톤 파악)
2. 레퍼런스 URL 3-5개 수집
3. 폰트 옵션 + Google Fonts 링크 제시
4. 사용자 방향 선택 확인
5. → /design-consultation, /design-html, /design-shotgun 등에 위임
```

**AI Trope Detection** (Impeccable 기반):
| 트랩 | 금지 패턴 |
|---|---|
| Font Mono-culture | 무조건 Inter/Geist/DM Sans 사용 |
| Pure Black | `#000000` 배경/텍스트 |
| Emoji Icons | 실제 아이콘 대신 이모지 |
| Multi-color | 3색 이상 메인 팔레트 |

---

### `nextjs-optimizer`

**역할**: Next.js 13+ App Router 5대 성능 영역 감사.

| 영역 | 목표 |
|---|---|
| 이미지 | `<img>` → next/image, width/height 필수, CLS 방지 |
| 렌더링 전략 | 페이지별 SSG/ISR/SSR/CSR 라벨링 |
| 코드 분할 | next/dynamic, 초기 번들 < 200KB |
| 서드파티 스크립트 | next/script strategy, FCP < 1.8s |
| 데이터 캐싱 | unstable_cache + revalidateTag |

Core Web Vitals 목표: LCP < 2.5s / CLS < 0.1 / INP < 200ms

---

### `stitch-design-flow`

**역할**: Google Stitch용 디자인 프롬프트 생성기. API 없음, 순수 텍스트.

```
1. DESIGN.md 읽기 (없으면 /design-consultation 먼저)
2. 6가지 브랜드 요소 추출
3. 3변형 생성: Safe (Stripe·Linear) / Bold (Figma·Arc) / Wild (Awwwards)
4. docs/design/stitch-prompts-<date>.md 저장
```

---

### `project-context-md`

**역할**: 프로젝트 CLAUDE.md 생성/갱신. Boris Cherny 검증 루프의 핵심.

9개 필수 섹션: 프로젝트 설명, 스택, **검증 도구** (가장 중요), 주요 경로, 디렉토리 구조, 환경변수, 금기, 관용, 참고 skill.

---

## Session — 세션 관리 (2개)

### `skill-gen-agent`

**역할**: Skill 생성·검증·리팩토링·테스트 도구 묶음.

```bash
# 검증
python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py skills-src/<name>

# JSON test case dry-run
python3 .claude/skills/skill-gen-agent/scripts/test_skill.py \
  skills-src/<name> --cases skills-src/<name>/evals/cases.json --dry-run

# 통합 테스트 (24 checks)
python3 .claude/skills/skill-gen-agent/scripts/tests/run_all.py
```

validator 검사: kebab-case, 64자, reserved word, semver, description 점수, 500줄 한도, TODO 마커, 깨진 링크, Windows 경로.

---

### `context-guardian`

**역할**: 컨텍스트 고갈 3단계 대응.

| Mode | 산출물 |
|---|---|
| Prevention | CLAUDE.md 규칙 블록 + .claudeignore |
| Monitoring | context_limit_log.json (80%/90% 경고) |
| Recovery | SESSION_RECOVERY.md (git 상태 + 시크릿 패턴 검사) |

---

## General Dev (6개)

| Skill | 역할 | 산출물 |
|---|---|---|
| `commit` | Conventional Commits | `type(scope): subject` |
| `debug` | 근본 원인 진단 | 수정 + 재현 불가 확인 |
| `explain` | 코드 워크스루 | entry point, 데이터 플로우, 불변식 |
| `refactor` | 동작 보존 구조 개선 | 기존 테스트 통과 |
| `review` | 코드 리뷰 | blocker/major/minor/nit |
| `test-gen` | 테스트 생성 | 골든 패스 + 엣지 + 에러 경로 |
