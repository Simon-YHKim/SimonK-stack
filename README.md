# Gstack-Ultraplan-Superpowers

> **한 줄 요약**: Claude Code 의 AI 어시스턴트가 "새 앱 만들자", "보안 점검해줘", "TDD 시작", "이거 또 틀렸어" 같은 말을 알아듣고 **자동으로 올바른 작업 절차를 따르게** 만드는 skill 묶음입니다.

[![validator](https://img.shields.io/badge/skill--validator-18%2F18%20PASS-brightgreen)]() [![cases](https://img.shields.io/badge/JSON%20cases-12%2F12%20PASS-brightgreen)]() [![trigger](https://img.shields.io/badge/trigger%20probe-13%2F13%20PASS-brightgreen)]() [![runtime](https://img.shields.io/badge/runtime%20smoke-24%2F24%20PASS-brightgreen)]() [![license](https://img.shields.io/badge/license-MIT-blue)]()

---

## 📖 목차

1. [이게 뭔가요? (초심자용)](#-이게-뭔가요-초심자용)
2. ["Skill" 이 뭔가요?](#-skill-이-뭔가요)
3. [누구를 위한 것인가요?](#-누구를-위한-것인가요)
4. [전체 구조 한눈에 보기](#-전체-구조-한눈에-보기)
5. [설치 — 3 가지 방법](#-설치--3-가지-방법)
6. [첫 사용 예시 5 개](#-첫-사용-예시-5-개)
7. [Simon-stack 13 개 skill 상세](#-simon-stack-13-개-skill-상세) ← 각자의 역할/구조/알고리즘
8. [Gstack 36 개 skill 카테고리](#-gstack-36-개-skill-카테고리)
9. [일반 개발 skill 6 개](#-일반-개발-skill-6-개)
10. [작동 원리: SessionStart Hook](#-작동-원리-sessionstart-hook)
11. [작동 원리: Instincts 학습 시스템](#-작동-원리-instincts-학습-시스템)
12. [테스트 결과](#-테스트-결과)
13. [자주 묻는 질문](#-자주-묻는-질문-faq)
14. [크레딧 · 라이선스](#-크레딧--라이선스)

---

## 🎯 이게 뭔가요? (초심자용)

**문제 상황**:
- AI 코딩 어시스턴트(Claude Code)는 강력하지만, 큰 작업을 시키면 "무엇부터 해야 할지" 매번 다르게 판단합니다.
- 같은 실수를 반복합니다 — RLS 보안 빠뜨리기, 테스트 없이 코드 작성, `.env` 커밋, API 키 하드코딩 등.
- 팀원마다 Claude 사용법이 달라서 품질 편차가 큽니다.

**이 레포의 해결책**:
- **55 개의 skill** 을 미리 준비해둡니다. 각 skill 은 "언제 발동하는지" + "어떤 순서로 일할지" + "어떤 함정을 피할지" 를 문서화한 작업 매뉴얼입니다.
- 사용자가 `"새 앱 만들자"` 라고 말하면 **`app-dev-orchestrator`** skill 이 자동으로 발동해서 21 단계 파이프라인을 지휘합니다.
- 사용자가 `"보안 점검"` 이라고 말하면 **`security-orchestrator`** 가 발동해서 5 단계 적대적 감사를 순차 실행합니다.
- 사용자가 `"이거 저번에도 그랬어"` 라고 말하면 **`simon-instincts`** 가 발동해서 실수를 기록하고, **다음 세션에서 자동으로 그 실수를 피합니다**.

**결과**: Claude 가 "잘못된 순서로 일하거나" "같은 실수를 반복할" 확률이 극적으로 줄어듭니다. 프로젝트 품질·보안·일관성이 한 단계 올라갑니다.

---

## 🧩 "Skill" 이 뭔가요?

**기술적 정의**: Claude Code 가 읽는 마크다운 파일(`SKILL.md`) + 선택적 스크립트·레퍼런스·애셋 번들.

**비유**: "IF 조건이 맞으면 THEN 이 매뉴얼을 따라라" 의 체크리스트.

### Skill 해부학

```
<skill-name>/
├── SKILL.md            ← 필수. YAML 헤더 + 마크다운 본문
├── scripts/            ← 선택. 실행 가능한 헬퍼 (bash, python, sql)
├── references/         ← 선택. 큰 문서를 여기에 분리 (500 줄 넘으면)
└── assets/             ← 선택. 템플릿, 아이콘, 폰트
```

### SKILL.md 구조

```yaml
---
name: my-skill                              # kebab-case, 64자 이하
description: Use when the user says "..."   # Claude 가 트리거 여부를 판단하는 근거
                                            # 반드시 구체 사용자 문구 포함
allowed-tools: Read, Write, Edit, Bash      # 이 skill 이 쓸 수 있는 도구
version: 1.0.0                              # semver
author: your-name
---

# Skill Title

본문에는 워크플로·체크리스트·안티패턴·관련 skill 을 기술.
<500 줄 권장. 넘으면 references/ 로 분리.
```

### 어떻게 "발동" 되나?

1. 사용자가 메시지 입력 ("새 앱 만들자")
2. Claude Code 가 모든 skill 의 `description` 을 스캔
3. 가장 잘 매칭되는 skill 을 로드 (metadata + body)
4. Claude 가 해당 skill 본문에 따라 작업
5. 필요 시 bundled scripts 실행

**핵심**: `description` 이 구체적일수록, 구체 사용자 문구가 많을수록, 발동 정확도가 올라갑니다. 그래서 이 레포의 모든 skill description 은 **"Use when the user says ..."** 로 시작하고 한/영 트리거 문구를 명시합니다.

---

## 👤 누구를 위한 것인가요?

| 대상 | 어떻게 쓰나 |
|---|---|
| **혼자 개발하는 한국어 사용자** | Claude Code 웹 + 이 레포 → 전체 55 개 skill 자동 사용. 같은 실수 반복 안 함 |
| **스타트업 팀** | `main` 브랜치에 이 레포 유지 → 팀 전원이 동일한 작업 표준 공유 |
| **한국 시장 앱 개발자** | 토스/네이버/카카오/부동산 API 특이사항이 `korean-context.md` instincts 에 누적 |
| **Next.js 개발자** | `nextjs-optimizer` + `simon-tdd` 로 Core Web Vitals + 테스트 품질 동시 관리 |
| **보안에 민감한 프로젝트** | `security-orchestrator` 한 번 호출로 RLS/Auth/결제/인프라 5 단계 감사 |

**요구 지식**: Claude Code 를 사용해봤다면 충분합니다. Bash·Git·JSON 기본 이해. 프로그래밍 언어 무관.

**요구 도구**:
- Claude Code 웹 (claude.ai/code) — **권장, 설치 불필요**
- 또는 Claude Code 데스크탑/CLI — `bun`, `node ≥ 20`, `git`

---

## 🏗️ 전체 구조 한눈에 보기

```
당신의 입력 ("새 앱 만들자")
        │
        ▼
┌─────────────────────────────────────────┐
│     Claude Code (세션)                  │
│                                         │
│  ①  SessionStart hook 실행              │
│      └─ Gstack clone + bun install      │
│      └─ 13 simon-stack skill 복사      │
│      └─ Instincts 4 파일 seed           │
│      └─ ~/.claude/CLAUDE.md 생성        │
│                                         │
│  ②  55 개 skill description 스캔        │
│      └─ 매칭: app-dev-orchestrator      │
│                                         │
│  ③  skill 본문 로드 (21단계 파이프라인) │
│      └─ 단계 0: 인터뷰                  │
│      └─ 단계 1: /office-hours           │
│      └─ 단계 2: simon-research          │
│      └─ ... 19개 단계 더                │
│      └─ 단계 21: simon-instincts 기록   │
└─────────────────────────────────────────┘
        │
        ▼
당신의 프로젝트 (완성)
```

---

## 📦 설치 — 3 가지 방법

### 방법 1: Claude Code 웹 (제일 쉬움)

1. https://claude.ai/code 접속
2. 이 레포 (learner-thepoorman/Gstack-Ultraplan-superpowers) 열기
3. 첫 세션 시작 시 자동으로 30 초 ~ 1 분 설정
4. 아무 메시지나 보내면 끝

**장점**: 어느 PC 에서든 동일한 환경. 집·회사·카페 모두 동일.
**단점**: 매 세션 시작에 30 초 소요 (이후는 캐시).

### 방법 2: 로컬 CLI / 데스크탑

```bash
git clone -b main https://github.com/learner-thepoorman/Gstack-Ultraplan-superpowers.git
cd Gstack-Ultraplan-superpowers
./scripts/install.sh
```

`~/.claude/` 에 영구 설치. 이후 Claude Code 데스크탑/CLI 모든 세션에서 자동 사용.

**장점**: 한 번 설치로 끝. 오프라인 가능.
**단점**: 업데이트는 수동 (`git pull && ./scripts/install.sh`).

### 방법 3: 다른 프로젝트에 vendoring

다른 프로젝트 레포에 simon-stack 을 embed 하고 싶을 때:

```bash
cd /path/to/your-other-project
/path/to/Gstack-Ultraplan-superpowers/scripts/setup-repo.sh .
git add .claude/
git commit -m "chore(claude): add simon-stack"
```

Target repo 에 24 개 파일 추가. Claude Code 웹에서 해당 레포 열면 자동 bootstrap.

상세: [docs/USING-IN-OTHER-REPOS.md](docs/USING-IN-OTHER-REPOS.md)

---

## 🚀 첫 사용 예시 5 개

이 레포를 설치한 뒤 Claude Code 에서 아래 메시지를 보내보세요:

### 예시 1: 새 앱 만들기
```
나: "한국 부동산 매물 검색 웹 앱 만들고 싶어. 타깃은 2030대 직장인."

Claude: [app-dev-orchestrator 자동 발동]
  단계 0. 인터뷰
  - 플랫폼? (Next.js 추천)
  - GitHub 레포? (신규)
  - 예산? (MVP 기준)
  - 결제 필요? (아직 X)
  ...
  단계 1. /office-hours 호출 — YC 6 가지 forcing question
  단계 2. simon-research 호출 — 직방/다방/호갱노노 3 개 비교
  ...
```

### 예시 2: 보안 감사
```
나: "배포 전에 전체 보안 점검 해줘"

Claude: [security-orchestrator 자동 발동]
  Step 1. security-checklist — RLS/구독/RateLimit/예산 4 영역 적대적 테스트
  Step 2. authz-designer — IDOR·권한 상승 스캔
  Step 3. paid-api-guard — 결제 API 6 층 방어 점검
  Step 4. /cso comprehensive — 인프라·시크릿·공급망 감사
  Step 5. /codex challenge — 적대적 리뷰
  → docs/security/<date>-SUMMARY.md 통합 리포트
```

### 예시 3: TDD 로 기능 추가
```
나: "유저 프로필에 bio 필드 추가해줘"

Claude: [simon-tdd 자동 발동]
  RED: 실패하는 테스트 먼저 작성
    test('profile.bio can be set and retrieved', ...)
    npm test → FAIL (expected)
  GREEN: 통과시키는 최소 구현
    users 테이블에 bio column 추가 + API endpoint
    npm test → PASS
  REFACTOR: validation 추가 + 테스트 재실행
  Atomic commit: feat(profile): add bio field
```

### 예시 4: 같은 실수 반복 방지
```
나: "이거 저번에도 그랬어. grep -c 쓰면 매치 0건일 때 exit 1 된다고."

Claude: [simon-instincts 자동 발동]
  ~/.claude/instincts/tool-quirks.md 에 append:

  ### 2026-04-14 — grep -c exit code 함정
  - 증상: grep -c 결과를 || echo 0 로 fallback 했더니 "0\n0" 중복 출력
  - 원인: grep -c 는 매치 0 건에도 "0" 을 stdout 에 찍고 exit 1
  - 예방책: `grep -c ... | tr -d ' \n'` 로 정규화, || fallback 제거
  - 출처: README 테스트 세션
```

### 예시 5: 디자인 프롬프트 생성
```
나: "우리 SaaS 대시보드 Stitch 프롬프트 3 개 만들어줘"

Claude: [stitch-design-flow 자동 발동]
  1. DESIGN.md 읽기
  2. 6 가지 브랜드 요소 추출 (이름, 톤, 컬러, 폰트, 타깃, 화면)
  3. Safe / Bold / Wild 3 가지 방향 프롬프트 생성
  4. docs/design/stitch-prompts-<date>.md 저장
  5. 사용자에게 "https://stitch.withgoogle.com 에 붙여넣어 주세요" 안내
```

---
## 🛠️ Simon-stack 13 개 skill 상세

이 섹션은 simon-stack 각 skill 의 **역할 / 구조 / 알고리즘** 을 초보자도 이해할 수 있도록 설명합니다.

각 skill 은 3 개 항목으로 구성:
- **역할 (Role)**: 이 skill 이 해결하는 문제
- **구조 (Structure)**: 파일 트리 + frontmatter + 주요 섹션
- **알고리즘 (Algorithm)**: skill 발동 후 Claude 가 따르는 단계별 절차

---

## 🧭 Orchestrators — 상위 지휘 skill (2 개)

상위 skill 은 스스로 많은 일을 하지 않습니다. **다른 skill 을 순차 호출**하고 결과를 조립하는 지휘자입니다.

### 1. `app-dev-orchestrator`

**역할**: 제로베이스 앱 개발 전 과정 자동화. "새 앱 만들자" 한 마디에 21 단계 파이프라인이 돌아가면서 아이디어·리서치·플랜·디자인·구현·보안·배포·회고·학습까지 순차 완료.

**구조**:
```
app-dev-orchestrator/
└── SKILL.md   ← 170 줄, 21 단계 순서도
    ├── YAML: name, description, allowed-tools, version
    ├── ## When — "새 앱 만들자", "MVP 기획" 등 트리거
    ├── ## Workflow — 21 단계 (각 단계 = 다른 skill 호출)
    ├── ## Principles — Boris Cherny 5 원칙 내장
    ├── ## Checklist — 단계별 완료 조건
    └── ## Anti-patterns — Plan 없이 구현, 레포 확인 없이 커밋 등
```

**알고리즘 (21 단계)**:
```
단계 0.  인터뷰: 플랫폼 / 타깃 / 레포 / 예산 / API / 마감 6 가지 질문
단계 1.  /office-hours 호출 — YC 6 가지 forcing question
단계 2.  simon-research 호출 — 경쟁 제품 3 개 비교
단계 3.  /plan-ceo-review — 10-star 스코프 재정의
단계 4.  /design-consultation — DESIGN.md 생성
단계 5.  stitch-design-flow — Safe/Bold/Wild 프롬프트 3 개
단계 6.  /design-shotgun — 변형 탐색
단계 7.  UltraPlan — 대형 플래닝 (CLI 내장 기능)
단계 8.  authz-designer — RBAC/ABAC/ReBAC 선택
단계 9.  API 설계 리뷰 — paid-api-guard 의 설계 섹션
단계 10. /plan-eng-review → /autoplan — 엔지니어링 플랜 잠금
단계 11. 레포·.env·.gitignore·gitleaks hook 준비
단계 12. simon-worktree — 병렬 작업 격리
단계 13. simon-tdd — RED-GREEN-REFACTOR 구현 (Next.js 면 nextjs-optimizer 동시 호출)
단계 14. /design-review → /design-html — 시각 QA + HTML 변환
단계 15. /qa — QA 테스트 + 버그 수정
단계 16. 보안 5 단 감사 (security-orchestrator 전체 루프)
단계 17. /benchmark — Core Web Vitals 측정
단계 18. /review → /ship — PR 생성
단계 19. /land-and-deploy → /canary — 배포 + 모니터링
단계 20. /document-release → /retro — 문서·회고
단계 21. simon-instincts 업데이트 → /checkpoint — 학습 저장
```

**핵심 원칙**: 이 skill 은 **스스로 코드를 쓰지 않습니다**. 각 단계는 다른 skill 을 호출만 합니다. 그래서 본문이 170 줄로 짧습니다.

---

### 2. `security-orchestrator`

**역할**: "보안 점검" 한 마디에 5 단계 적대적 감사가 순차 실행되고 통합 SUMMARY 리포트가 생성. 개별 영역(RLS, 권한, API, 인프라, 적대적)을 따로 요청할 필요 없음.

**구조**:
```
security-orchestrator/
└── SKILL.md   ← 100 줄
    ├── ## Workflow — 5 단계 순차 호출
    ├── ## 통합 보고서 — Critical/High/Medium/Low 정렬
    └── ## 원자 커밋 수정 루프 — 이슈 하나씩 fix + 재검증
```

**알고리즘 (5 단계)**:
```
Step 1. security-checklist       → 4 대 영역 적대적 테스트
Step 2. authz-designer (감사)    → IDOR·권한 상승 스캔
Step 3. paid-api-guard            → 결제·외부 API 6 층 방어 점검
Step 4. /cso comprehensive        → 인프라·시크릿·공급망·LLM·CI/CD
Step 5. /codex challenge          → 적대적 리뷰 (Codex CLI 가 취약점 찾기)

→ 결과를 docs/security/<date>-SUMMARY.md 에 심각도 정렬로 통합
→ Critical/High 가 모두 해결될 때까지 수정 루프
→ 각 수정을 회귀 테스트로 tests/security/ 에 추가
```

**발동 조건 주의**: 전체 감사만 트리거. "RLS 만 봐줘" 같은 좁은 요청은 skill 이 인식해서 개별 skill 로 delegate.

---

## 🔒 Security — 보안 상세 skill (3 개)

### 3. `security-checklist`

**역할**: 웹 앱의 **4 대 보안 구조** 를 적대적으로 감사. 각 영역은 5 개의 "공격자가 실제로 시도할 법한" 테스트 쿼리를 제공 — 바로 regression test suite 로 drop-in 가능.

**구조**:
```
security-checklist/
├── SKILL.md   ← 195 줄, 4 영역 상세
│   ├── A. RLS 시나리오 감사
│   ├── B. 구독 상태 변경 취약점
│   ├── C. 이중 Rate Limit
│   └── D. 예산 한도 3 계층
└── scripts/
    └── rls-adversarial-tests.sql   ← 5 개 SQL 쿼리 (drop-in)
```

**4 대 영역 알고리즘**:
```
A. RLS (Row Level Security)
   1. 모든 user 테이블에 ENABLE + FORCE RLS 적용 확인
   2. pg_policies 뷰로 정책 누락 테이블 스캔
   3. 적대적 테스트 5 종:
      - Test 1: 사용자 A → 사용자 B 데이터 SELECT/UPDATE → 0 rows
      - Test 2: Anon role 민감 테이블 접근 → 0 rows
      - Test 3: role='admin' 자가 승격 UPDATE → 0 rows
      - Test 4: 만료/위조 JWT → 401
      - Test 5: pg_policies 정책 커버리지 스캔

B. 구독 상태 변경
   1. 민감 필드 9 개 (subscription_tier, role, credits, is_admin, ...)
   2. RLS WITH CHECK 로 클라이언트 UPDATE 제외
   3. 웹훅 3 종 세트: HMAC 서명 + idempotency-key + timestamp 5분 window
   4. audit_log 테이블: who/when/from/to/source
   5. 적대적: PATCH 직접, GraphQL mutation, 웹훅 서명 조작

C. 이중 Rate Limit
   1. user_id + IP 2 중 키 동시 적용
   2. Edge (Cloudflare) + App (Redis) 2 층
   3. 티어 차등: anon / STANDARD / PRIME
   4. 엔드포인트 한도: 로그인 5/min/IP, LLM N/min/user, 업로드 MB/시간
   5. 429 + Retry-After + X-RateLimit-* 헤더

D. 예산 한도 3 계층
   1. Provider: OpenAI/Anthropic/GCP 대시보드 hard budget
   2. App: Redis 카운터로 일/월 집계, 80% 임계치 알림
   3. User: user_quotas 테이블, 소진 시 402 Payment Required
   4. Circuit breaker (opossum / pybreaker)
```

---

### 4. `authz-designer`

**역할**: 프로젝트에 맞는 권한 모델(RBAC / ABAC / ReBAC / 하이브리드)을 선택하고 Postgres DDL 템플릿을 제공. 기존 코드는 IDOR·권한 상승 버그 감사.

**구조**:
```
authz-designer/
└── SKILL.md   ← 160 줄
    ├── 모델 선택 가이드 (4 가지 + 트리거 조건)
    ├── 추천 스택 (OpenFGA, Casbin, Oso, Postgres RLS)
    ├── 스키마 템플릿 (4 개 테이블 DDL)
    └── 감사 체크리스트 (IDOR, 권한 상승, 토큰 위조)
```

**모델 선택 알고리즘**:
```
if (역할 소수 + 고정) → RBAC
  예: admin/user/viewer
  스택: Casbin / Postgres RLS + role column

elif (시간·IP·소유자·부서 등 속성 조건 복잡) → ABAC
  예: 9-18 시만 작업 가능, 부서별 접근
  스택: Oso / Casbin ABAC matcher

elif (문서·팀·프로젝트 협업 그래프) → ReBAC
  예: Notion, Figma, GitHub 공유
  스택: OpenFGA / SpiceDB / Zanzibar

else → Hybrid (RBAC 베이스 + ABAC 조건 + 민감 리소스 ReBAC)
  가장 현실적. 대부분의 SaaS 는 여기
```

**DDL 템플릿 (4 테이블)**:
- `authz_roles` — 역할 정의
- `authz_role_assignments` — 사용자 ↔ 역할 (ReBAC 그래프도 표현 가능)
- `authz_policies` — ABAC 조건 JSONB
- `authz_audit_log` — 정책 변경 감사 로그

**감사 체크리스트**:
- 모든 엔드포인트 인가 미들웨어 적용 (누락 = IDOR)
- `user_id` 비교만 하고 role 체크 누락 경로 스캔
- 권한 상승 3 종 시나리오 테스트
- 프론트 UI 권한 분기는 장식용 주석 의무, 서버가 최종 권위

---

### 5. `paid-api-guard`

**역할**: 결제·SMS·지도·이메일 등 **유료 API** 를 6 층 방어로 보호. 클라이언트 직접 호출 방지, 웹훅 서명, idempotency, 남용 탐지, 키 탈취 대응, 관측까지.

**구조**:
```
paid-api-guard/
└── SKILL.md   ← 175 줄
    ├── Layer 1. 네트워크 경계
    ├── Layer 2. 서명·멱등성
    ├── Layer 3. 남용 탐지
    ├── Layer 4. 결제 전용
    ├── Layer 5. 키 탈취 대응
    ├── Layer 6. 관측
    ├── 적대적 테스트 5 종
    └── API 설계 리뷰 섹션
```

**6 층 방어 알고리즘**:
```
Layer 1. 네트워크 경계
  - BFF (Backend-for-Frontend) 강제
  - 브라우저 직접 호출 금지
  - API 키는 서버 env var (NEXT_PUBLIC_* 절대 금지)
  - Cloudflare WAF 선차단

Layer 2. 서명·멱등성
  - 클라 → BFF: HMAC + nonce + timestamp 5 분 window
  - 비용 요청: Idempotency-Key 헤더
  - 웹훅: raw body 로 서명 검증 (JSON parse 후 ❌)

Layer 3. 남용 탐지
  - 사용자별 비용 대시보드 (일/월)
  - 평소 10 배 이상 → 자동 일시정지 + 알림
  - Cloudflare Turnstile / hCaptcha
  - 신규 계정 24 h 한도 축소

Layer 4. 결제 전용
  - 시크릿 매니저 별도 네임스페이스
  - Stripe Elements / Toss SDK 로 tokenize
  - 환불·취소 2 차 승인 (OTP)
  - **금액 서버 재계산** — 클라 amount 신뢰 금지

Layer 5. 키 탈취 대응
  - Canary 키 (가짜) 배치, 사용 감지 시 알림
  - docs/INCIDENT-PLAYBOOK.md 사전 작성
  - GitHub push protection + trufflehog
  - 90 일 로테이션

Layer 6. 관측
  - 모든 호출 로깅: user_id, endpoint, cost_estimate, status, latency
  - BigQuery / ClickHouse / Datadog
  - 주간 /retro 에 external_api_cost 섹션
```

**적대적 테스트**:
1. 프론트 번들 grep → `sk_live_`, `pk_live_` 0 건
2. BFF 우회 직접 호출 → 네트워크 차단
3. Idempotency-Key 10 회 반복 → 1 회만 처리
4. 웹훅 서명 조작 → 400
5. 토큰 탈취 시뮬 → 이상 탐지 발동

---
## 🧠 Method — 방법론 skill (4 개, `simon-*` 접두사)

방법론 skill 은 **특정 기술이 아닌 일하는 방식**을 강제합니다. 어느 언어·프레임워크에서도 적용됩니다.

### 6. `simon-tdd`

**역할**: 기능 구현·버그 수정 요청을 RED → GREEN → REFACTOR 사이클로 강제. 사후 정당화 테스트 금지. 또한 Boris Cherny 의 "검증 루프" 원칙을 내장 — Claude 가 서버·테스트·브라우저를 스스로 확인할 수 있도록 CLAUDE.md 에 검증 도구를 명시하게 함.

**구조**:
```
simon-tdd/
└── SKILL.md   ← 125 줄
    ├── ## Workflow — RED → GREEN → REFACTOR 사이클
    ├── ## 검증 도구 제공 원칙 (Boris Cherny)
    ├── ## Checklist
    └── ## Anti-patterns — 사후 테스트 작성, RED skip 등
```

**알고리즘**:
```
RED 단계:
  1. 요구사항을 observable behavior 로 표현 (구현 세부 ❌)
  2. 실패하는 테스트 먼저 작성
  3. npm test → 실패 확인 (스크린샷/로그로 증거 남김)
  4. 실패 원인이 의도한 것인지 확인
     (syntax error 로 실패 ≠ 유효한 RED)

GREEN 단계:
  1. 가장 작은 코드로 통과 (하드코딩도 OK)
  2. npm test → 성공
  3. 전체 스위트 재실행 — 다른 테스트 파괴 여부 확인

REFACTOR 단계:
  1. 동작 보존하며 구조 개선
  2. 중복 제거, 네이밍, 추출
  3. 각 리팩토링마다 테스트 재실행

사이클 종료:
  git add -p  # 변경 검토
  git commit -m "feat: <기능>"  # 또는 "test: ..."
```

**검증 도구 제공 원칙**:
```
프로젝트 CLAUDE.md 에 아래를 필수 명시:
  - 서버 시작: npm run dev  # http://localhost:3000
  - 테스트 실행: npm test / npm test -- <pattern>
  - 브라우저 URL + 주요 경로
  - DB 접근: psql $DATABASE_URL
  - 린트·타입: npm run lint && npm run typecheck

원칙: "Claude 가 눈으로 확인 못 하면 = 검증 실패"
→ 사용자 수동 확인 워크플로는 자동화 기회
→ Playwright / /browse / 헬스체크 엔드포인트 추가
```

---

### 7. `simon-worktree`

**역할**: 병렬 Claude 세션을 `git worktree` 로 격리. 동일 브랜치에 두 세션이 동시 작업하는 "커밋 충돌 지옥" 방지.

**구조**:
```
simon-worktree/
└── SKILL.md   ← 110 줄
    ├── ## Workflow — 6 단계 (생성 → 할당 → .env → 작업 → 완료 → 정리)
    ├── ## .env 취급 규칙
    └── ## Anti-patterns — 동일 브랜치 병렬, .env 하드코딩
```

**알고리즘**:
```
Step 1. worktree 생성 (네이밍 규칙: <repo>-<feature>)
  cd /path/to/main-repo
  git worktree add ../myapp-auth -b feat/auth

Step 2. 독립 Claude 세션 배정
  메인 worktree  → 세션 A (PR 리뷰·문서·핫픽스)
  ../myapp-auth  → 세션 B (auth 기능)
  ../myapp-bill  → 세션 C (billing 기능)

Step 3. .env 처리
  옵션 A: ln -sf ../myapp/.env .env  (심볼릭 링크)
  옵션 B: cp ../myapp/.env .env      (각 worktree 복사)
  확인:    .env 가 .gitignore 에 있는지 재확인

Step 4. 병렬 작업 원칙
  - 메인 worktree 에는 직접 commit ❌ (PR 만)
  - 각 worktree 는 자기 브랜치만 커밋
  - 공통 파일 (package.json) 은 한 번에 한 곳만 수정
  - 세션 간 통신은 git 으로만

Step 5. 완료 후 정리
  cd /path/to/main-repo
  git worktree remove ../myapp-auth
  git branch -d feat/auth   # 로컬
  # 원격은 PR 머지 시 자동

Step 6. 고아 확인
  git worktree list
  git worktree prune
```

---

### 8. `simon-research`

**역할**: 플래닝 전에 **외부 리서치 의무화**. "X 가 빠르다고 함" 같은 출처 없는 주장 금지. 공식 문서 + 경쟁 제품 3 개 + 최근 6 개월 블로그로 dated 리서치 문서 생성.

**구조**:
```
simon-research/
└── SKILL.md   ← 145 줄
    ├── ## Workflow — 7 단계 (요약 → 키워드 → fetch → 비교 → 저장)
    ├── ## 1차/2차 출처 구분
    └── ## Anti-patterns — 1 년 이상 된 블로그 단일 출처 등
```

**알고리즘**:
```
Step 1. 주제 3 줄 요약
  - What: 리서치 대상
  - Why:  의사결정 맥락
  - Success: 충분한 결과물 정의

Step 2. 검색 키워드 5-10 개 추출
  - 공식 문서 키워드
  - 경쟁 제품 이름
  - 최근 6 개월 블로그/컨퍼런스
  - 실패 사례·안티패턴 키워드
  - 한/영 병기

Step 3. 1 차 자료 병렬 WebFetch
  우선순위:
  1. 공식 문서 (anthropic.com, stripe.com, supabase.com ...)
  2. 공식 GitHub README + examples
  3. RFC·명세서 (OpenAPI, JWT, OAuth)
  4. 최근 6 개월 엔지니어링 블로그

  금기:
  - 1 년 이상 된 블로그 단일 출처 ❌
  - 출처 불명 요약 글 ❌
  - AI 요약 기사 (2 차 가공) ❌

Step 4. 경쟁 제품 3 개 이상 비교표
  | 항목 | A | B | C | 비고 |
  |---|---|---|---|---|
  | 가격 | ... | ... | ... | |
  | 핵심 기능 | ... | ... | ... | |
  | 제약 | ... | ... | ... | |
  | 커뮤니티 | ... | ... | ... | |

Step 5. Context7 MCP 활용 (있을 때)
  라이브러리 최신 문서 — training cutoff 이후 업데이트 반영

Step 6. 결과 저장
  docs/research/<YYYY-MM-DD>-<topic>.md
  필수 메타데이터:
  - URL, 발행일, 저자/기관
  - 1차 (공식) / 2차 (해설) 구분
  - 한국 특이사항 섹션 (해당 시)

Step 7. 플래닝 투입
  /office-hours, /plan-ceo-review, app-dev-orchestrator 에
  입력으로 전달
```

---

### 9. `simon-instincts`

**역할**: Claude 가 저지른 실수·프로젝트 패턴·한국 컨텍스트·도구 함정을 **4 개 마크다운 파일** 에 누적. 세션 시작 시 자동 로드돼 같은 실수를 반복하지 않게 함.

**구조**:
```
simon-instincts/
├── SKILL.md   ← 135 줄
│   ├── ## 저장소 — 4 개 파일 역할
│   ├── ## Workflow — 실수 → 기록 → 자동 로드
│   └── ## CLAUDE.md 자동 로드 블록
└── scripts/
    └── append.sh   ← 대화형/플래그 기반 헬퍼
```

**4 파일 역할**:
```
~/.claude/instincts/
├── mistakes-learned.md    ← Claude 실수 누적 로그
│   예: "grep -c 매치 0 건일 때 exit 1 + 0 출력 → || echo 0 로 중복"
├── project-patterns.md    ← 프로젝트별 관용·제약
│   예: "WORDGE 프로젝트는 Prisma 대신 Drizzle"
├── korean-context.md      ← 한국 시장 특이사항
│   예: "토스페이먼츠 웹훅은 TossPayments-Signature 헤더"
└── tool-quirks.md         ← CLI/하네스 함정
    예: "git clone 은 -b main 없으면 서버 default branch"
```

**알고리즘**:
```
발동 트리거:
  사용자: "이거 저번에도 그랬어"
  사용자: "또 틀렸네"
  사용자: "반복이야"
  사용자: "이거 기록해둬"

실행:
  1. 파일 선택 (4 개 중)
  2. 4 필드 수집:
     - 증상 (무엇이 잘못됐나)
     - 원인 (근본 원인, 피상적 ❌)
     - 예방책 (다음에 해야 할 것)
     - 출처 (세션 ID / 파일)
  3. scripts/append.sh 또는 Edit 로 append
  4. 형식: "### YYYY-MM-DD — <제목>"

자동 로드:
  ~/.claude/CLAUDE.md 상단에 auto-load 블록:
    ## Instincts (auto-loaded)
    - See ~/.claude/instincts/mistakes-learned.md
    - See ~/.claude/instincts/project-patterns.md
    - See ~/.claude/instincts/korean-context.md
    - See ~/.claude/instincts/tool-quirks.md

SessionStart hook 이 세션 시작 시 이 파일들의 최근 3 mistakes 를
자동 출력 (scripts/session-start-instincts.sh)
```

**bundled script**:
```bash
# 대화형
bash append.sh mistakes

# 플래그 모드
bash append.sh tools \
  --title "grep -c exit 1" \
  --symptom "0\n0 중복 출력" \
  --cause "grep 이 stdout 에 0 찍고 exit 1" \
  --fix "tr -d ' \n' 로 정규화" \
  --source "README 테스트"
```

---
## 🧰 Tools — 특수 목적 skill (3 개)

### 10. `nextjs-optimizer`

**역할**: Next.js (13+ App Router) 프로젝트의 **5 대 성능 영역** 을 감사하고 수정. Core Web Vitals, 번들 사이즈, CLS, LCP 개선.

**구조**:
```
nextjs-optimizer/
├── SKILL.md   ← 170 줄
│   ├── ## 선행 체크 — package.json 에 "next" 없으면 skip
│   ├── ## Workflow — 5 영역 순차 감사
│   └── ## 검증 — Core Web Vitals 목표
└── scripts/
    └── audit-img-tags.sh   ← <img> 잔존 자동 감지
```

**5 대 영역 알고리즘**:
```
Area 1. 이미지
  1. grep -rn "<img" src/ app/ components/
  2. <img> → next/image 전환 가이드
     - width/height 필수 (CLS 방지)
     - priority (above-the-fold 만)
     - sizes (반응형)
     - placeholder="blur"
  3. next.config.js: images.minimumCacheTTL = 31536000

Area 2. 렌더링 전략 라벨링
  각 페이지를 4 가지로 분류:
    SSG — 빌드 시 고정 (약관, 랜딩)
    ISR — 주기 갱신 (블로그, 상품)
    SSR — 요청마다 (대시보드, 검색)
    CSR — 클라이언트 (관리자, 에디터)
  코드에 export const dynamic/revalidate 명시

Area 3. 코드 분할
  1. 무거운 컴포넌트 찾기 (에디터/차트/PDF/지도)
  2. next/dynamic({ ssr: false }) 전환
  3. 초기 번들 < 200KB 목표
  4. ANALYZE=true npm run build 로 시각화

Area 4. 서드파티 스크립트
  1. GA, Clarity, Meta Pixel, Crisp, Intercom 식별
  2. next/script strategy=afterInteractive|lazyOnload|worker
  3. FCP < 1.8s 목표

Area 5. 데이터 캐싱
  1. unstable_cache + revalidateTag 패턴
  2. // CACHED: 주석 의무 (캐시 적용 코드 표시)
  3. 변경 mutation 에서 revalidateTag 호출

Core Web Vitals 목표:
  LCP < 2.5s / CLS < 0.1 / INP < 200ms / FCP < 1.8s
```

**bundled script**:
```bash
bash audit-img-tags.sh [path]
# → 파일별 <img> 카운트 + next/image 변환 스니펫
```

---

### 11. `stitch-design-flow`

**역할**: Google Stitch (stitch.withgoogle.com) 웹 UI 용 **디자인 프롬프트 생성기**. API 없음 — 순수 텍스트 변환. Safe / Bold / Wild 3 가지 방향으로 프롬프트를 만들어 사용자가 직접 Stitch 에 붙여넣음.

**구조**:
```
stitch-design-flow/
├── SKILL.md                         ← 140 줄
│   └── "no API, no MCP, no image generation" 명시
├── scripts/
│   └── generate-prompts.sh          ← DESIGN.md 파서 + 프롬프트 출력
└── references/
    ├── prompt-template.md           ← 하드코딩용 템플릿 (TOC 포함)
    └── prompt-recipes.md            ← 10 개 산업별 레시피
        (SaaS, 커머스, 부동산, 핀테크, 교육, AI, 블로그, 모빌리티, 헬스케어, 커뮤니티)
```

**알고리즘**:
```
Step 1. DESIGN.md 존재 확인
  없으면 /design-consultation 먼저 요청
  (이 skill 은 브랜드 방향을 만들지 않음, 번역만)

Step 2. 6 가지 브랜드 요소 추출
  - 제품명 + 한 줄 pitch
  - 타깃 사용자
  - 톤 키워드 (modern / playful / minimal / ...)
  - 컬러 (primary / secondary / accent, hex)
  - 타이포 (display / body / mono)
  - 핵심 화면 3 개

Step 3. 3 변형 생성 — 각 화면마다
  A. Safe  → Stripe, Linear, Vercel 레퍼런스
  B. Bold  → Figma, Arc Browser, Raycast
  C. Wild  → Rauno Freiberg, Awwwards winners

Step 4. 공통 제약 조건
  - Mobile-first, 375px
  - WCAG AA contrast
  - 한/영 병기 (한국 시장)
  - 스톡 사진 금지
  - 최대 3 typography weights

Step 5. 출력
  docs/design/stitch-prompts-<YYYY-MM-DD>.md 저장
  "한 번에 하나씩 붙여넣으세요" 안내
  (Stitch 는 배치 프롬프트 파싱 실패)

Step 6. 후속 skill 연결
  → /design-shotgun (변형 탐색)
  → /design-html (HTML 변환)
```

**산업별 레시피 (references/prompt-recipes.md)**:
10 개 산업에 대해 Safe/Bold/Wild 3 가지 방향 + 한국 시장 제약 정리.
예: 부동산 → Safe=직방/다방, Bold=호갱노노, Wild=Airbnb×부동산. 필수 제약: 전세/월세 toggle, 평/m² 전환.

---

### 12. `project-context-md`

**역할**: 프로젝트 루트에 `CLAUDE.md` 파일을 생성/갱신. Claude Code 가 세션 시작 시 읽는 "프로젝트 컨텍스트 문서" — 여기에 **검증 도구 (서버 시작, 테스트, 브라우저)** 를 명시하는 것이 Boris Cherny 의 "검증 루프" 원칙의 핵심.

**구조**:
```
project-context-md/
└── SKILL.md   ← 170 줄
    ├── ## Workflow — 5 단계
    └── ## 템플릿 — 필수 섹션 9 개
```

**알고리즘**:
```
Step 1. 기존 파일 확인
  test -f CLAUDE.md
  → EXISTS:  섹션 단위 merge (덮어쓰기 금지)
  → MISSING: 신규 생성

Step 2. 프로젝트 컨텍스트 수집 (병렬)
  - cat package.json / pyproject.toml / go.mod / Cargo.toml
  - ls 주요 디렉토리 구조
  - grep 주요 entry point
  - git log --oneline -10 (최근 활동)
  - .env.example (필수 변수 목록)

Step 3. 템플릿 작성 (9 섹션)
  1. 프로젝트 한 줄 설명
  2. 스택 (Language / Framework / DB / Deploy / Auth)
  3. ★ 검증 도구 (dev 서버, 테스트, 린트, 빌드, DB 접근)
     ← 이게 가장 중요. Claude 가 이걸로 자가 검증
  4. 주요 경로 (URL + 용도)
  5. 디렉토리 구조
  6. 환경변수 (값 ❌, 이름만)
  7. 금기 (migrations, lockfile, prod 브랜치)
  8. 관용 (커밋 스타일, 브랜치, 네이밍)
  9. 참고 skill 목록

Step 4. placeholder 채움
  사용자 검토 or 소스 분석 기반 자동 채움

Step 5. 커밋
  git add CLAUDE.md
  git commit -m "docs: add project CLAUDE.md with verification tools"
```

**왜 중요한가**:
Boris Cherny 원칙: **"Claude 가 스스로 확인할 수 없는 워크플로는 검증 실패"**. CLAUDE.md 에 검증 도구를 명시하지 않으면 Claude 는 매번 "사용자가 브라우저로 확인해주세요" 라고 말하게 됩니다. 이 skill 은 그 의존성을 자동화합니다.

---
## 🚀 Gstack 36 개 skill 카테고리

simon-stack 의 13 개 skill 은 **작업 방식**을 강제하지만, 실제 **실행** 은 Gstack (garrytan/gstack) 의 36 개 skill 이 담당합니다. Gstack 은 매 세션 시작 시 upstream 에서 clone + `bun install` 돼서 `~/.claude/skills/gstack/` 에 설치됩니다.

### 플래닝 (6)
| Skill | 역할 |
|---|---|
| `/office-hours` | YC 6 가지 forcing question (demand·status quo·specificity·wedge·observation·future-fit) |
| `/plan-ceo-review` | CEO 모드 10-star 스코프 재정의 (4 모드: SCOPE EXPANSION / SELECTIVE / HOLD / MINIMAL) |
| `/plan-eng-review` | 엔지니어링 매니저 모드 — 아키텍처·데이터플로우·엣지케이스·테스트 커버리지 락다운 |
| `/plan-design-review` | 디자이너 모드 — 각 디자인 차원 0-10 점수 + 개선 플랜 |
| `/plan-devex-review` | DX 모드 — 개발자 페르소나·벤치마크·마법의 순간 |
| `/autoplan` | 위 4 개 리뷰를 자동 순차 실행 + 결정 원칙으로 자동 판단 |

### 디자인 (4)
| Skill | 역할 |
|---|---|
| `/design-consultation` | 제품 이해 → 디자인 시스템 (타이포·컬러·레이아웃·모션) → DESIGN.md 생성 |
| `/design-shotgun` | 여러 변형 생성 + 비교 보드 + 피드백 수렴 |
| `/design-review` | 시각 QA — 일관성·spacing·hierarchy·AI slop 탐지 + 소스 수정 |
| `/design-html` | 승인된 목업 → production HTML/CSS 변환 |

### 구현·QA (6)
| Skill | 역할 |
|---|---|
| `/qa` | QA 테스트 + 발견 버그 자동 수정 + 원자적 commit |
| `/qa-only` | QA 리포트만 생성 (수정 없음) — health score·스크린샷·repro |
| `/review` | PR 사전 리뷰 — SQL safety, LLM trust boundary, conditional side effects |
| `/benchmark` | Core Web Vitals 성능 측정 + baseline·트렌드 |
| `/health` | 코드 품질 대시보드 — type check, lint, test, dead code, shell lint 가중 합성 |
| `/codex` | OpenAI Codex CLI 래퍼 — review / challenge / consult 3 모드 |

### 배포 (5)
| Skill | 역할 |
|---|---|
| `/ship` | 머지 베이스 감지 → 테스트 → diff 리뷰 → VERSION/CHANGELOG → commit → push → PR |
| `/land-and-deploy` | PR 머지 → CI 대기 → 배포 → production health 검증 |
| `/canary` | 배포 후 라이브 모니터링 — console 에러, 성능 회귀, 페이지 실패 감시 |
| `/setup-deploy` | 배포 플랫폼 감지 (Fly/Render/Vercel/...) → CLAUDE.md 에 설정 저장 |
| `/document-release` | 배포 후 문서 갱신 — README/ARCHITECTURE/CONTRIBUTING/CLAUDE.md 동기화 |

### 보안·품질 (6)
| Skill | 역할 |
|---|---|
| `/cso` | Chief Security Officer 모드 — 시크릿 archaeology·공급망·CI/CD·LLM 보안·OWASP·STRIDE |
| `/careful` | 파괴적 명령 가드 — `rm -rf`, `DROP TABLE`, `force-push`, `git reset --hard` 경고 |
| `/guard` | `/careful` + `/freeze` 통합 — 최대 안전 모드 |
| `/freeze` | 특정 디렉토리로 편집 범위 제한 — 디버깅 중 무관한 코드 수정 방지 |
| `/unfreeze` | freeze 해제 |
| `/retro` | 주간 엔지니어링 회고 — commit 히스토리, 팀별 기여, 트렌드 |

### 리서치·DX (4)
| Skill | 역할 |
|---|---|
| `/investigate` | 체계적 디버깅 4 단계 — investigate → analyze → hypothesize → implement (Iron Law: 근본원인 없이 수정 금지) |
| `/browse` | 헤드리스 브라우저 — 페이지 nav, 상태 검증, before/after diff, 스크린샷 |
| `/learn` | 프로젝트 학습 관리 — 검색, prune, export (simon-instincts 의 프로젝트 scope 버전) |
| `/devex-review` | DX 실측 — 문서 탐색, getting started 시도, TTHW 측정, CLI 평가 |

### 기타 (5)
| Skill | 역할 |
|---|---|
| `/checkpoint` | 작업 상태 저장/재개 — git 상태, 결정 내역, 남은 작업 |
| `/pair-agent` | 원격 에이전트 페어링 — OpenClaw/Hermes/Codex/Cursor 와 브라우저 공유 |
| `/setup-browser-cookies` | 실제 Chromium 쿠키를 headless 브라우저로 import — 인증 페이지 QA 용 |
| `/open-gstack-browser` | GStack Browser (사이드바 확장 내장 Chromium) 실행 |
| `/gstack-upgrade` | Gstack 최신 버전 업데이트 |

---

## 📝 일반 개발 skill 6 개

`.claude/skills/` 에 미리 있는 원본 스킬들. simon-stack 설치 전에도 사용 가능. 이번 리뷰 패스에서 description 을 pushy 형태로 강화했습니다.

| Skill | 트리거 예시 | 산출물 |
|---|---|---|
| `commit` | "commit this", "커밋해줘", "stage and commit" | Conventional Commits 형식 (`type(scope): subject`) |
| `debug` | "디버깅", "버그 고쳐줘", "why is X broken" | 근본 원인 진단 + 수정 + 재현 불가 확인 |
| `explain` | "이 코드 설명해줘", "walk me through" | entry point, 데이터 플로우, 불변식, 수정 지점 |
| `refactor` | "리팩토링", "clean up", "extract function" | 동작 보존 구조 개선 + 기존 테스트 통과 |
| `review` | "리뷰해줘", "code review", "feedback on code" | blocker / major / minor / nit 우선순위 리뷰 |
| `test-gen` | "테스트 작성", "unit tests", "add test coverage" | 골든 패스 + 엣지 케이스 + 에러 경로 테스트 |

---
## 🛡️ Meta + Session 관리 skill 2 개 (v1.2.0 new)

v1.2.0 에서 추가된 skill 2 개 — skill 제작 도구 벤더링 + 컨텍스트 고갈 대응.

### 14. `skill-gen-agent`

**역할**: repo 내부에서 skill 을 만들고, 검증하고, 리팩토링하고, 테스트할 수 있는 도구 묶음. `github.com/Learner-thepoorman/Skill-Agent` 를 벤더링.

**구조**:
```
skill-gen-agent/
├── SKILL.md                       ← 269 줄 (<500 OK)
├── scripts/
│   ├── validate_skill.py          ← 필수. 모든 skill 수정 후 실행
│   ├── test_skill.py              ← evals/cases.json dry-run 하네스
│   ├── refactor_skill.py          ← voice-ratio + reference-leak 탐지
│   ├── version_log.py             ← semver bump + CHANGELOG
│   ├── install_skill.py           ← 검증 후 ~/.claude/skills/ 로 복사
│   └── tests/run_all.py           ← 24-check 통합 테스트
├── references/                    ← anatomy, best-practices, design-principles,
│                                    interview, refactor-playbook, testing, i18n, quickstart
├── templates/                     ← SKILL.md.tmpl, script.py.tmpl, reference.md.tmpl, cases.json.tmpl
└── evals/cases.json
```

**주요 사용**:
```bash
# 1. Skill 검증 (이 레포에서 skill 수정 후 반드시 실행)
python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py .claude/skills/<name>

# 2. JSON test case dry-run
python3 .claude/skills/skill-gen-agent/scripts/test_skill.py \
  .claude/skills/<name> --cases .claude/skills/<name>/evals/cases.json --dry-run

# 3. 전체 통합 테스트 (24 checks)
python3 .claude/skills/skill-gen-agent/scripts/tests/run_all.py
```

**validator 가 잡는 것들**: kebab-case 이름, 64 자 초과, reserved word (`claude`/`anthropic`), 잘못된 semver, description 점수 < 0.6, 500 줄 초과, TODO/FIXME/XXX 마커, 깨진 상대 링크, Windows 경로, 중첩 references/, 긴 reference 파일 TOC 누락.

---

### 15. `context-guardian`

**역할**: Claude Code 세션이 context window 한도에 도달해 응답이 느려지거나 끊기는 문제를 3 단계 (Prevention / Monitoring / Recovery) 로 대응.

**구조**:
```
context-guardian/
├── SKILL.md                       ← 200 줄
├── scripts/
│   ├── install-rules.sh           ← Prevention: CLAUDE.md 규칙 + .claudeignore
│   ├── update-context-log.sh      ← Monitoring: 실측 한도 JSON 관리
│   └── create-recovery.sh         ← Recovery: SESSION_RECOVERY.md 생성
├── references/templates.md        ← 4 산출물 템플릿 + TOC
└── evals/cases.json               ← 4 test cases
```

**3 mode 알고리즘**:

```
Mode 1. Prevention (install-rules.sh)
  1. CLAUDE.md 에 "<!-- context-guardian-rules:v1 -->" 블록 append
     (idempotent: 마커 있으면 skip)
  2. .claudeignore 생성 (없을 때만) — node_modules/.next/dist/.git/lock 등
  3. .gitignore 업데이트 안내 (SESSION_RECOVERY.md, context_limit_log.json)

Mode 2. Monitoring (update-context-log.sh)
  --load              → 현재 effective_limit 출력
  --record --model X --measured N → history append + 현재 측정값 갱신
  --check <tokens>    → 80% / 90% 임계치 경고

  context_limit_log.json 스키마:
    {
      "model": "claude-opus-4-6",
      "measured_limit": 200000,
      "safety_margin": 0.8,
      "effective_limit": 160000,
      "history": [...]
    }

  ★ 한도 하드코딩 금지 — 모델 업데이트 시 stale 되지 않도록 측정값 기반

Mode 3. Recovery (create-recovery.sh)
  1. git 상태 수집 (브랜치, 커밋, status, diff-stat)
  2. .env.example 에서 env var 이름만 추출 (값은 절대 포함 ❌)
  3. SESSION_RECOVERY.md 생성 + 수동 필드 템플릿 (완료/미완료 작업)
  4. 시크릿 패턴 (sk-, sk_live_, pk_live_, AKIA, ghp_, xox[bps]-) grep
     → 발견 시 abort + 경고
  5. 다음 세션 시작 프롬프트 (복사용) 포함
```

**`/checkpoint` 와의 관계**:

| | `/checkpoint` (Gstack) | `context-guardian` |
|---|---|---|
| 목적 | 일반 작업 스냅샷 | 컨텍스트 고갈 **예방** + **복구** |
| 트리거 | 명시적 저장 요청 | 80% 임박 · 세션 끊긴 후 |
| 산출물 | Git + 결정 로그 | CLAUDE.md 규칙 + .claudeignore + SESSION_RECOVERY.md + context_limit_log.json |

**상호보완적** — 같이 사용 가능. `/checkpoint` 로 중간 저장, `context-guardian` 으로 고갈 방지 + 세션 연속성.

---

### 🔄 이 레포 자체에 자동 적용 (v1.2.0)

v1.2.0 에서 이 레포 (simon-stack development workspace) 자체에 context-guardian prevention mode 를 **사전 설치**했습니다. Claude Code 로 이 레포를 열면 자동으로 보호 규칙이 활성화됩니다.

| 파일 | 역할 |
|---|---|
| `CLAUDE.md` (신규, repo root) | 이 레포 특화 작업 맥락 + 검증 도구 목록 + 금기 경로 + Context Guardian Rules 블록 (마커 포함) |
| `.claudeignore` (신규) | `.claude/skills/gstack/` (12 MB / 450 files 차단) · `.claude.bak-*` · 세션 state 파일 · 표준 (node_modules, .next, build, ...) |
| `.gitignore` 확장 | `SESSION_RECOVERY.md`, `context_limit_log.json`, `CLAUDE.md.bak-*` 제외 |
| `.claude/hooks/session-start.sh` 개선 | **self-healing**: 세션 시작 시 CLAUDE.md 의 `<!-- context-guardian-rules:v1 -->` 마커 존재 확인, 없으면 `install-rules.sh` 자동 재실행 |

**이 레포 특이 규칙** (CLAUDE.md 에 문서화):
- Tool call 마다 55+ skill description 이 system-reminder 로 반복되어 컨텍스트가 빠르게 쌓임
- 따라서: Bash 호출 최소화 (하나의 Bash 에 배치), `python3 <<PY ... PY` heredoc 으로 다중 파일 생성, Write tool 이 Bash 보다 reminder 적음, 불필요한 Read 금지

**drift 방지**: 사용자가 실수로 `CLAUDE.md` 를 삭제해도 다음 세션 시작 시 hook 이 자동 감지 + 복구.

---

## ⚙️ 작동 원리: SessionStart Hook

Claude Code 웹 환경은 매 세션마다 VM 이 새로 시작되고 `~/.claude/` 가 초기화됩니다. 그래서 skill 을 매번 재설치해야 하는데, 이걸 자동화하는 게 **SessionStart hook** 입니다.

### 파일 위치
```
<repo>/
├── .claude/
│   ├── hooks/
│   │   └── session-start.sh   ← 매 세션 시작 시 실행
│   └── settings.json          ← hook 등록
```

### 실행 순서 (세션 시작 시)

```
1. 사용자가 Claude Code 웹에서 repo 열기
2. VM spin up (fresh, ~/.claude 비어있음)
3. Claude Code 가 .claude/settings.json 읽기
4. settings.json 의 SessionStart hook 발견
5. .claude/hooks/session-start.sh 실행
6. hook 이 반환될 때까지 Claude 는 메시지 입력 대기
7. hook 완료 → 모든 skill 로드 완료 상태로 세션 시작
```

### Hook 알고리즘 (`.claude/hooks/session-start.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# [1] Idempotency 체크 — 이미 설치됐으면 skip
MARKER=~/.claude/.simon-stack-installed
CURRENT_SHA=$(cd "$REPO_DIR" && git rev-parse HEAD)
if [ -f "$MARKER" ] && [ "$(cat "$MARKER")" = "$CURRENT_SHA" ]; then
  echo "Already installed at $CURRENT_SHA, skipping"
  exit 0
fi

# [2] 디렉토리 준비
mkdir -p ~/.claude/skills ~/.claude/instincts

# [3] Gstack runtime — upstream 에서 clone
if [ ! -d ~/.claude/skills/gstack ]; then
  TMP=$(mktemp -d)
  git clone --depth 1 https://github.com/garrytan/gstack "$TMP/gstack-src"
  cp -a "$TMP/gstack-src" ~/.claude/skills/gstack
  rm -rf "$TMP"

  # bun install — 90+ packages, Gstack bin/ 스크립트 의존
  (cd ~/.claude/skills/gstack && bun install)
fi

# [4] Gstack sub-skill 36 개 노출
for d in ~/.claude/skills/gstack/*/; do
  name=$(basename "$d")
  [ -f "$d/SKILL.md" ] || continue
  [ -e ~/.claude/skills/"$name" ] && continue
  cp -r "$d" ~/.claude/skills/"$name"
done

# [5] simon-stack skill 복사 (이 repo 에서)
for d in "$REPO_DIR"/.claude/skills/*/; do
  name=$(basename "$d")
  [ -f "$d/SKILL.md" ] || continue
  [ -e ~/.claude/skills/"$name" ] && continue
  cp -r "$d" ~/.claude/skills/"$name"
done

# [6] Instincts seed — 4 개 파일
for f in mistakes-learned.md project-patterns.md korean-context.md tool-quirks.md; do
  [ ! -f ~/.claude/instincts/"$f" ] && \
    cp "$REPO_DIR/.claude/instincts/$f" ~/.claude/instincts/"$f"
done

# [7] Global CLAUDE.md 템플릿 설치
[ ! -f ~/.claude/CLAUDE.md ] && \
  cp "$REPO_DIR/templates/CLAUDE.md" ~/.claude/CLAUDE.md

# [8] Marker 기록 — 다음 세션에서 skip 가능하도록
echo "$CURRENT_SHA" > "$MARKER"

# [9] 환경변수 export (이번 세션용)
echo "export SIMON_STACK_INSTALLED=1" >> "$CLAUDE_ENV_FILE"
```

### `settings.json` 등록

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh"
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": ["Skill"]
  }
}
```

### 핵심 속성
- **Idempotent**: 재실행 안전 (marker 로 skip)
- **Synchronous**: hook 완료까지 세션 대기 (race condition 방지)
- **Self-healing**: 파일 누락 시 자동 재설치
- **환경 감지**: `CLAUDE_CODE_REMOTE=true` 로 웹 환경 구분
- **첫 실행 시간**: ~30-60 초 (Gstack clone + bun install)
- **재실행 시간**: < 1 초 (marker match → skip)

---

## 🧠 작동 원리: Instincts 학습 시스템

Instincts 는 Claude 가 저지른 실수를 기억하게 만드는 **4 파일 마크다운 메모리** 입니다. ECC (everything-claude-code) 의 개념을 추출·확장했습니다.

### 4 파일 역할 분리

```
~/.claude/instincts/
├── mistakes-learned.md    ← Claude 실수 (시간순)
│   - 증상 / 원인 / 예방책 / 출처 4 필드
│   - "### YYYY-MM-DD — 제목" 형식
│
├── project-patterns.md    ← 프로젝트별 관용
│   - WORDGE 는 Drizzle (Prisma ❌)
│   - 부동산 크롤러는 robots.txt 존중
│   - "## <project-name>" 섹션별 누적
│
├── korean-context.md      ← 한국 시장 특이사항
│   - 토스페이먼츠 웹훅 헤더
│   - 카카오 3 종 키 분리
│   - 주민번호 수집 금지
│   - 전세/월세 용어 처리
│
└── tool-quirks.md         ← CLI/하네스 함정
    - git clone default branch
    - grep -c exit 1 quirk
    - RLS FORCE 필요성
    - .env gitignore 재확인
```

### 4 파일로 분리한 이유

- **라이프사이클 다름**: mistakes 는 매일 쌓임, korean-context 는 거의 불변
- **탐색 경로 다름**: 새 프로젝트 진입 시 project-patterns 먼저, 한국 API 연동 시 korean-context 먼저
- **삭제 정책 다름**: mistakes 는 해결되면 `~~취소선~~`, korean-context 는 거의 영구
- **PR 리뷰 가능성**: tool-quirks 는 팀 공유 가치, mistakes 는 개인

### 작동 사이클

```
┌─────────────────────────────────────────────┐
│ 1. 세션 시작 (SessionStart hook 실행)        │
│    └─ scripts/session-start-instincts.sh   │
│       └─ 4 파일 entry 수 표시               │
│       └─ 최근 3 mistakes 자동 로드           │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 2. 세션 중 작업                              │
│    └─ Claude 가 ~/.claude/CLAUDE.md 읽음    │
│    └─ CLAUDE.md 에 auto-load 블록:          │
│       ## Instincts (auto-loaded)            │
│       - See ~/.claude/instincts/*.md        │
│    └─ Claude 는 같은 실수 반복 회피          │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 3. 사용자 실수 지적                          │
│    "이거 저번에도 그랬어"                    │
│    "또 틀렸네"                               │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 4. simon-instincts skill 발동                │
│    └─ scripts/append.sh 실행                │
│    └─ 4 필드 수집 (증상/원인/예방책/출처)    │
│    └─ mistakes-learned.md 에 append         │
│    └─ "### 2026-04-14 — <제목>" 추가        │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 5. 다음 세션 시작                            │
│    └─ SessionStart hook 재실행               │
│    └─ "Recent mistakes to avoid:"           │
│       으로 최근 3 개 출력                    │
│    └─ Claude 는 시작부터 해당 실수 인식       │
└─────────────────────────────────────────────┘
```

### `session-start-instincts.sh` 핵심 로직

```bash
# 4 파일 entry 수 표시
for f in mistakes-learned project-patterns korean-context tool-quirks; do
  entries=$(grep -c "^### " "$INSTINCTS/$f.md")
  # mistakes 는 "YYYY-MM-DD" 템플릿 1개 제외
  if [ "$f" = "mistakes-learned" ]; then
    entries=$((entries - $(grep -c "^### YYYY" "$INSTINCTS/$f.md")))
  fi
  printf '  - %-18s %s entries\n' "$f:" "$entries"
done

# 최근 3 mistakes 출력 (날짜 prefix 만)
awk '
  /^### [0-9]/ { count++; show=1; if (count>3) exit }
  show { print "    " $0 }
  /^- \*\*증상\*\*/ && show { show=0 }
' "$INSTINCTS/mistakes-learned.md"
```

### CLAUDE.md Auto-load 블록 (모든 세션에 공통 적용)

```md
## Instincts (auto-loaded)

세션 시작 시 아래 4 개 파일을 참조하여 누적 학습을 활용한다. 같은 실수는 반복하지 않는다.

- See ~/.claude/instincts/mistakes-learned.md
- See ~/.claude/instincts/project-patterns.md
- See ~/.claude/instincts/korean-context.md
- See ~/.claude/instincts/tool-quirks.md

사용자가 "저번에도 그랬어", "또 틀렸어" 라고 지적하면
**즉시** simon-instincts 스킬로 해당 파일에 append.
```

### 누적 효과

```
세션 1: Claude 가 grep -c 실수 → 사용자 지적 → 기록
세션 2: Claude 가 같은 상황 → CLAUDE.md 에서 자동 로드된 "recent mistakes"
        에서 "grep -c exit 1" 기억 → 회피
세션 N: 수십 개 실수 누적 → Claude 품질이 세션마다 향상
```

이게 "학습하는 Claude" 의 핵심 메커니즘입니다.

---
## ✅ 테스트 결과

이 레포의 모든 skill 은 아래 4 종 테스트를 통과합니다 (총 **67 체크**).

### 요약

| 테스트 | 통과 | 비고 |
|---|---|---|
| Static validation (Skill-Gen Agent) | **18 / 18** | validate_skill.py 0 errors / 0 warnings |
| JSON dry-run (Skill-Gen Agent) | **12 / 12** | test_skill.py --dry-run |
| Trigger probe (substring) | **13 / 13** | 각 skill description 이 test prompt 키워드 포함 |
| Runtime smoke | **24 / 24** | Script 실행 + Bash 문법 + JSON 파싱 |
| **총합** | **67 / 67** | **100% PASS** |

### 1. Static Validation (validate_skill.py)

Skill-Gen Agent (`github.com/Learner-thepoorman/Skill-Agent`) 의 validator 를 사용합니다. 검사 항목:

- SKILL.md 존재 + YAML frontmatter 파싱
- 필수 필드: name, description, version
- `name` kebab-case + 64 자 이하 + reserved word (claude/anthropic) 차단
- `description` 점수 ≥ 0.6 (트리거 휴리스틱)
- 본문 < 500 줄 (400 줄에서 warning)
- TODO/FIXME/`<placeholder>` 마커 금지
- 깨진 상대 링크 차단
- Windows 경로 (`\`) 차단
- 중첩 references/ 금지
- 긴 references/ 파일 (100 줄+) 에 `## Contents` TOC 의무

**결과**:
```
app-dev-orchestrator     0 errors, 0 warnings   PASS
security-orchestrator    0 errors, 0 warnings   PASS
security-checklist       0 errors, 0 warnings   PASS
authz-designer           0 errors, 0 warnings   PASS
paid-api-guard           0 errors, 0 warnings   PASS
simon-tdd                0 errors, 0 warnings   PASS
simon-worktree           0 errors, 0 warnings   PASS
simon-instincts          0 errors, 0 warnings   PASS
simon-research           0 errors, 0 warnings   PASS
nextjs-optimizer         0 errors, 0 warnings   PASS
stitch-design-flow       0 errors, 0 warnings   PASS
project-context-md       0 errors, 0 warnings   PASS
commit                   0 errors, 0 warnings   PASS  (general)
debug                    0 errors, 0 warnings   PASS  (general)
explain                  0 errors, 0 warnings   PASS  (general)
refactor                 0 errors, 0 warnings   PASS  (general)
review                   0 errors, 0 warnings   PASS  (general)
test-gen                 0 errors, 0 warnings   PASS  (general)
```

### 2. JSON Dry-run (test_skill.py)

각 simon-stack skill 은 `evals/cases.json` 에 test case 정의를 포함합니다. `test_skill.py --dry-run` 으로 스키마 검증.

**cases.json 스키마**:
```json
{
  "skill": "skill-name",
  "version": "1.0.0",
  "cases": [
    {
      "id": "case-id",
      "prompt": "사용자가 보낼 법한 문구",
      "assertions": [
        { "id": "a1", "text": "Claude 가 반드시 해야 할 행동 #1" },
        { "id": "a2", "text": "행동 #2" }
      ]
    }
  ]
}
```

**실행 결과**:
```
[PASS] app-dev-orchestrator   (3 cases)
[PASS] security-orchestrator  (2 cases)
[PASS] security-checklist     (1 case)
[PASS] authz-designer         (1 case)
[PASS] paid-api-guard         (1 case)
[PASS] simon-tdd              (1 case)
[PASS] simon-worktree         (1 case)
[PASS] simon-instincts        (1 case)
[PASS] simon-research         (1 case)
[PASS] nextjs-optimizer       (1 case)
[PASS] stitch-design-flow     (1 case)
[PASS] project-context-md     (1 case)
────────────────────────────────
Total: 15 cases across 12 skills, 12/12 files valid
```

예시 case (authz-designer):
```json
{
  "id": "notion-like-sharing",
  "prompt": "우리 앱에 Notion 처럼 문서 공유 기능 넣으려고 하는데 권한 시스템 어떻게 설계해?",
  "assertions": [
    { "id": "picks-rebac",
      "text": "The agent recommends ReBAC because the use case is document-sharing with a permission graph." },
    { "id": "provides-ddl",
      "text": "The agent provides DDL templates for authz_roles, authz_role_assignments, authz_policies, authz_audit_log." }
  ]
}
```

### 3. Trigger Probe

각 test case 의 **prompt** 에서 핵심 키워드를 추출해서 해당 skill 의 **description** 에 포함되는지 검사. 트리거 정확도의 필요조건.

**실행 결과**:
```
[PASS] app-dev-orchestrator    korean-new-app        2/2 ['앱', '만들']
[PASS] app-dev-orchestrator    english-mvp           3/3 ['MVP', 'scaffold', 'new']
[PASS] security-orchestrator   comprehensive-audit   3/3 ['보안', '감사', '배포']
[PASS] security-checklist      rls-supabase          2/2 ['RLS', 'Supabase']
[PASS] authz-designer          notion-like-sharing   2/3 ['권한', 'Notion']
[PASS] paid-api-guard          stripe-integration    3/3 ['Stripe', '결제', '보안']
[PASS] simon-tdd               add-feature           2/2 ['구현', '기능']
[PASS] simon-worktree          parallel-features     2/2 ['동시', '작업']
[PASS] simon-instincts         repeated-mistake      2/2 ['저번', '이거']
[PASS] simon-research          stack-comparison      4/4 ['Supabase', 'Firebase', '리서치', '비교']
[PASS] nextjs-optimizer        lcp-audit             2/3 ['Next', 'LCP']
[PASS] stitch-design-flow      korean-saas-prompts   3/3 ['Stitch', '프롬프트', '시안']
[PASS] project-context-md      bootstrap-claude-md   2/2 ['CLAUDE.md', '프로젝트']
```

### 4. Runtime Smoke Test

Bundled script 들이 실제로 실행되는지, hook 이 idempotent 한지, 모든 bash/JSON 파일이 문법에 맞는지 확인.

**실행 결과**:
```
[PASS] stitch-design-flow/generate-prompts.sh  — fake DESIGN.md 파싱 → 3 variant × 3 screen 출력
[PASS] simon-instincts/append.sh               — fake HOME 에 entry 추가 확인
[PASS] nextjs-optimizer/audit-img-tags.sh      — fake Next.js 프로젝트에서 <img> 감지
[PASS] .claude/hooks/session-start.sh          — idempotent 재실행 (marker match → skip)
[PASS] scripts/install.sh                      — bash 문법 OK
[PASS] scripts/setup-repo.sh                   — bash 문법 OK
[PASS] scripts/session-start-instincts.sh      — bash 문법 OK
[PASS] templates/bootstrap-session-start.sh    — bash 문법 OK
[PASS] .claude/skills/*/scripts/*.sh × 3       — bash 문법 OK
[PASS] .claude/skills/*/evals/cases.json × 12  — JSON 파싱 OK
```

### 테스트 재현 방법

```bash
# Skill-Gen Agent clone
git clone https://github.com/Learner-thepoorman/Skill-Agent /tmp/Skill-Agent

# Static validation
for d in .claude/skills/*/; do
  [ -f "$d/SKILL.md" ] || continue
  python3 /tmp/Skill-Agent/skills/skill-gen-agent/scripts/validate_skill.py "${d%/}"
done

# JSON dry-run
for d in .claude/skills/*/evals/cases.json; do
  python3 /tmp/Skill-Agent/skills/skill-gen-agent/scripts/test_skill.py \
    "$(dirname $(dirname $d))" --cases "$d" --dry-run
done

# Runtime smoke (생략 — 상단 Runtime Smoke 섹션의 스크립트 실행)
```

---
## ❓ 자주 묻는 질문 (FAQ)

### Q. Gstack 이 뭐예요? 왜 있어야 해요?
`github.com/garrytan/gstack` 은 Claude Code 용 실행 파이프라인 skill 36 개 모음입니다 (`/ship`, `/qa`, `/cso`, `/retro` 등). **이 레포의 13 개 simon-stack skill 은 방법론만 정의** 하고 실제 실행은 Gstack 에 위임합니다. 그래서 SessionStart hook 이 매 세션마다 Gstack 을 upstream 에서 clone + `bun install` 합니다.

### Q. `bun install` 이 느려요
첫 세션만 느립니다 (약 30 초). 이후는 marker 파일 (`~/.claude/.simon-stack-installed`) 로 skip 해서 1 초 이내 완료. Claude Code 웹의 VM 스냅샷 캐시에도 저장되므로 같은 레포를 다시 열면 더 빠릅니다.

### Q. Skill 이 발동 안 해요
3 가지 가능성:
1. **Description 트리거 키워드 미매칭** — 사용자 문구에 skill description 의 구체 구문이 없으면 Claude 가 못 찾음. 해결: 더 구체적으로 말하거나 `simon-tdd` 처럼 skill 이름을 명시
2. **Hook 미실행** — `.claude/settings.json` 에 `SessionStart` 등록 확인, `~/.claude/.simon-stack-installed` marker 존재 확인
3. **Default branch 아닌 브랜치 열기** — Claude Code 웹은 default branch 를 체크아웃하므로 feature 브랜치의 skill 변경은 안 보임. main 에 병합 필요

디버깅:
```bash
cat /tmp/simon-stack-session-start-*.log  # 최근 hook 실행 로그
ls ~/.claude/skills/                        # 설치된 skill 목록 (55+ 개)
~/.claude/session-start-instincts.sh         # instincts hook 수동 실행
```

### Q. Skill 간에 충돌하면?
Skill 은 **description 매칭 점수** 로 선택됩니다. "보안 점검" 이라고 하면 `security-orchestrator`, `security-checklist`, `/cso` 가 모두 후보입니다. 해결책:
- **Orchestrator 를 먼저 작성** — 이 레포의 `security-orchestrator` 가 "전체 감사" 문구를 가장 명시적으로 매칭해서 이기고, 하위 skill 은 그 안에서 순차 호출됨
- **좁은 요청은 구체 skill 이름 사용** — "RLS 만 점검" → `security-checklist` 가 발동

### Q. 다른 repo 에서 쓰려면?
[`scripts/setup-repo.sh`](scripts/setup-repo.sh) 실행. 두 가지 모드:
- `vendor` (기본, 권장) — 이 repo 의 skill 파일 전체를 target repo 에 복사. 네트워크 독립
- `bootstrap` — target repo 에 2 파일만 drop-in, 매 세션 이 repo 를 clone. 가볍지만 네트워크 의존

상세: [docs/USING-IN-OTHER-REPOS.md](docs/USING-IN-OTHER-REPOS.md)

### Q. 한국어로만 말해도 되나요?
네. 모든 simon-stack skill 의 description 은 한/영 트리거 구문 병기되어 있습니다. 실수 기록(`mistakes-learned.md`), 프로젝트 패턴(`project-patterns.md`), 한국 컨텍스트(`korean-context.md`) 도 한국어로 작성됩니다. Skill 본문은 한/영 혼용.

### Q. Instincts 가 너무 많이 쌓이면?
주간 `/retro` 실행 시 instincts 를 함께 리뷰합니다. 해결된 실수는 `~~취소선~~` + 이유, 중복은 병합, 오래된 프로젝트 섹션은 아카이빙. `tool-quirks.md` 는 반대로 거의 영구 보존.

### Q. `project-claude-md` 가 `project-context-md` 로 바뀌었어요
Skill-Gen Agent validator 가 skill 이름에 `claude` 예약어를 차단합니다 (Anthropic 혼동 방지). 역할은 동일 — 프로젝트 CLAUDE.md 파일을 생성/갱신.

### Q. Stitch API 를 쓸 수 있나요?
**아니요**. 공개 Stitch API 는 존재하지 않습니다. `stitch-design-flow` skill 은 **순수 텍스트 프롬프트 생성기** 입니다 — DESIGN.md 를 읽고 Safe/Bold/Wild 프롬프트를 만들어주고, 사용자가 `https://stitch.withgoogle.com` 에 직접 붙여넣습니다. 누군가가 "Stitch API key" 를 대화에 붙이면 skill 은 저장/호출하지 않고 로테이션을 권장합니다.

### Q. 로컬 CLI / 데스크탑 설치는 어떻게 업데이트?
```bash
cd /path/to/Gstack-Ultraplan-superpowers
git pull
./scripts/install.sh   # idempotent, 재실행 안전
```

### Q. 제거하려면?
```bash
# 백업에서 복구
ls ~/.claude.bak-*
mv ~/.claude.bak-<최신> ~/.claude

# 또는 simon-stack 만 제거
rm -rf ~/.claude/skills/{app-dev-orchestrator,security-orchestrator,security-checklist,authz-designer,paid-api-guard,simon-tdd,simon-worktree,simon-instincts,simon-research,nextjs-optimizer,stitch-design-flow,project-context-md}
rm ~/.claude/.simon-stack-installed
```

---

## 📚 더 읽어볼 문서

| 문서 | 내용 |
|---|---|
| [docs/INSTALL.md](docs/INSTALL.md) | 로컬 CLI / 데스크탑 설치 상세 |
| [docs/MORNING-START.md](docs/MORNING-START.md) | 빠른 시작 가이드 (3 단계) |
| [docs/USING-IN-OTHER-REPOS.md](docs/USING-IN-OTHER-REPOS.md) | 다른 repo 에서 사용하는 4 가지 시나리오 |
| [.claude/skills/INDEX.md](.claude/skills/INDEX.md) | 전체 55 skill 카테고리 맵 |
| [.claude/instincts/](.claude/instincts/) | 누적 학습 4 파일 seed |
| [templates/CLAUDE.md](templates/CLAUDE.md) | 글로벌 CLAUDE.md 템플릿 |
| [CHANGELOG.md](CHANGELOG.md) | 버전 히스토리 (v0.1.0 / v1.0.0 / v1.1.0) |

---

## 🎁 크레딧

이 레포는 4 개의 오픈소스 아이디어를 통합합니다:

| 출처 | 기여 |
|---|---|
| [Gstack](https://github.com/garrytan/gstack) — garrytan | 실행 파이프라인 36 skill (ship·qa·cso·retro·checkpoint 등) |
| [Superpowers](https://github.com/obra/superpowers) — obra | TDD 사이클 강제, git worktree 격리, 검증 루프 철학 |
| [everything-claude-code](https://github.com/affaan-m/everything-claude-code) — affaan-m | Instincts 누적 학습, research-first |
| [UltraPlan](https://code.claude.com/docs/en/ultraplan) — Anthropic | Claude Code 대형 플래닝 (CLI 내장) |
| [skill-creator](https://github.com/anthropics/skills) — Anthropic | Skill 작성 표준 + description 최적화 원칙 |
| [Skill-Agent](https://github.com/Learner-thepoorman/Skill-Agent) — Skill-Gen Agent | validate_skill.py, test_skill.py 검증 도구 |

**Boris Cherny 원칙** (Claude Code PM) 5 가지를 모든 skill 에 내장:
1. **Plan 모드 기본** — 세션 시작은 Plan 모드. 실행 전 사용자 승인
2. **병렬은 worktree** — 병렬 Claude 세션은 git worktree 로 격리
3. **검증 루프 = 도구 제공** — Claude 가 스스로 서버·테스트·브라우저로 확인 가능하도록
4. **`--dangerously-skip-permissions` 금지** — `/permissions` allowlist 사용
5. **CLAUDE.md 팀 체크인** — 프로젝트 CLAUDE.md 는 git 에 포함, PR 마다 갱신

---

## 📄 라이선스

[MIT](LICENSE). 상업적 사용·수정·배포 자유. 책임 없음.

Upstream 컴포넌트는 각자의 라이선스를 따릅니다:
- Gstack, Superpowers, everything-claude-code 는 각 repo 참조
- 이 repo 는 그 코드를 vendoring 하지 않고 세션 시작 시 clone 만 함

---

## 🤝 기여

PR 환영합니다. 새 skill 추가 시:
1. `.claude/skills/<new-skill>/SKILL.md` 작성 (skill-creator 표준 준수)
2. `validate_skill.py` 통과 확인
3. `evals/cases.json` 에 2-3 test case 추가
4. `.claude/skills/INDEX.md` 에 등록
5. `CHANGELOG.md` 업데이트
6. Conventional Commits (`feat(skills):`, `fix:`, `docs:`)

버그 리포트: GitHub Issues.

---

**질문·제안은 GitHub Issues 또는 이 레포의 CLAUDE.md 에 직접 기록해주세요.**
