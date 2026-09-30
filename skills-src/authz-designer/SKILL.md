---
name: authz-designer
description: Use when designing or auditing authorization—"권한 시스템 설계", "RBAC 넣어줘", "ReBAC", "IDOR 점검", "multi-tenant permissions", "share feature like Notion", or /authz-designer. Produces a scoped access-control model, security findings, or provider-specific schema after inspecting existing policy and trust boundaries; an audit request stays read-only.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.1
author: simon
---

# Authz Designer

인가(Authorization) 모델을 설계하거나 감사한다. 인증(Authentication)과 구분: "누구인가"가 아닌 "무엇을 할 수 있는가". 기존 서비스의 정책·데이터 소유권을 먼저 확인하고, 감사 요청은 읽기 전용으로 유지한다.

## When to use

- 새 앱 기획 단계 (`app-dev-orchestrator` 단계 8)
- 기존 앱 권한 리팩토링
- 사용자가 "권한 시스템 설계", "RBAC 넣어줘", "역할 정의", "공유 기능 만들고 싶어" 요청
- 보안 감사 중 IDOR 의심

## Workflow

먼저 요청을 **설계·구현**과 **감사·진단**으로 구분한다. 후자에서는 엔드포인트·서비스 계층·DB/RLS·공유 링크의 실제 권한 경계를 읽고 확인한 사실만 보고한다. 테스트 계정이나 로컬 픽스처가 없다면 교차 테넌트 요청을 운영 서비스에 보내지 않는다. 운영 권한·DB·정책·사용자 데이터를 변경하거나 DDL을 적용하지 않는다. 수정 요청에서도 마이그레이션과 운영 적용은 별도 승인·롤백 검토 대상이다.

### 1. 모델 선택 가이드

| 모델 | 적합 시나리오 | 예시 |
|---|---|---|
| **RBAC** (Role-Based) | 역할이 소수·고정, 단순 관리자 페이지 | SaaS admin/user/viewer |
| **ABAC** (Attribute-Based) | 시간·IP·소유자·부서 등 속성 조건 복잡 | 금융(시간제한), 엔터프라이즈 |
| **ReBAC** (Relationship-Based) | 문서·팀·프로젝트 협업 그래프 | Notion, Figma, GitHub, Linear |
| **Hybrid** | 역할·속성·관계 조건이 모두 실제로 필요한 경우 | 복잡도와 정책 일관성 비용을 함께 평가 |

문서 공유라는 제품 비유만으로 ReBAC 엔진을 필수로 결정하지 않는다. 주체·행동·리소스·테넌트·공유 범위·상속/철회 규칙을 먼저 나열하고, 기존 데이터 모델로 표현 가능한지 확인한다.

### 2. 구현 선택지 (기존 스택 확인 후)

- **ReBAC**: [OpenFGA](https://openfga.dev/) (Auth0) 또는 [SpiceDB](https://authzed.com/spicedb) (Zanzibar 기반)
- **RBAC/ABAC**: [Casbin](https://casbin.org/), [Oso](https://www.osohq.com/)
- **단순**: Postgres RLS + 정책 테이블 (서비스 경계와 RLS의 역할을 구분)

새 엔진·의존성은 규모, 운영 역량, 라이선스·비용, 기존 정책과의 일치 여부를 확인한 뒤 제안한다. 제공자 전환이나 유료 서비스 생성은 이 스킬의 기본 동작이 아니다.

### 3. 설계 요청의 선택적 스키마 예시 (Supabase + PostgreSQL 15+)

아래는 요청한 설계를 설명하기 위한 예시이지 적용 가능한 범용 마이그레이션이 아니다. `auth.users`는 Supabase 전용이며 테넌트 격리, RLS, 역할 상속, 정책 평가 순서, 감사 로그 원자성은 프로젝트별로 설계해야 한다. 범위 열 둘 다 NULL이면 전역 할당이므로 전역 역할 부여 권한을 별도로 제한해야 한다. PostgreSQL 15 미만에서는 `UNIQUE NULLS NOT DISTINCT` 대신 동등한 부분 고유 인덱스 등을 설계한다. 실제 DB 버전·스키마를 모르면 SQL을 실행하지 않는다.

```sql
-- 역할 정의
CREATE TABLE authz_roles (
  id          TEXT PRIMARY KEY,  -- 'admin', 'editor', 'viewer'
  name        TEXT NOT NULL,
  description TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 역할 할당 (사용자 ↔ 역할, ReBAC 관계 표현 가능)
CREATE TABLE authz_role_assignments (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES auth.users(id),
  role_id       TEXT NOT NULL REFERENCES authz_roles(id),
  resource_type TEXT,           -- 'workspace', 'project', NULL=global
  resource_id   UUID,           -- 특정 리소스에 한정 시
  granted_by    UUID REFERENCES auth.users(id),
  granted_at    TIMESTAMPTZ DEFAULT NOW(),
  expires_at    TIMESTAMPTZ,    -- ABAC: 시간 제한
  CHECK ((resource_type IS NULL) = (resource_id IS NULL)),
  UNIQUE NULLS NOT DISTINCT (user_id, role_id, resource_type, resource_id)
);

-- 정책 (ABAC 조건)
CREATE TABLE authz_policies (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  role_id    TEXT NOT NULL REFERENCES authz_roles(id),
  resource   TEXT NOT NULL,     -- 'projects', 'invoices'
  action     TEXT NOT NULL,     -- 'read', 'write', 'delete'
  condition  JSONB,             -- {"time_of_day": "09-18", "ip_range": "10.0.0.0/8"}
  effect     TEXT NOT NULL DEFAULT 'allow' CHECK (effect IN ('allow', 'deny'))
);

-- 감사 로그
CREATE TABLE authz_audit_log (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id     UUID REFERENCES auth.users(id),
  action       TEXT NOT NULL,   -- 'grant', 'revoke', 'policy_change'
  target_type  TEXT,
  target_id    TEXT,
  before_state JSONB,
  after_state  JSONB,
  source       TEXT,            -- 'admin_ui', 'api', 'migration'
  ip           INET,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_actor ON authz_audit_log(actor_id, created_at DESC);
CREATE INDEX idx_audit_target ON authz_audit_log(target_type, target_id);
```

### 4. 감사 체크리스트

#### IDOR 방지
- [ ] 관련 요청 경로를 인벤토리화하고 각 read/write/share 작업에서 **해당 리소스에 대한** 서버 측 인가가 실행되는지 추적한다. 미들웨어가 아니라 서비스·DB 정책에서 집행할 수도 있다.
- [ ] 추측 가능한 리소스 ID로 다른 사용자·테넌트의 객체에 접근할 수 있는지, 로컬/격리 테스트에서 확인한다. URL 난독화·프론트 버튼 숨김은 인가가 아니다.
- [ ] `user_id` 비교가 실제 소유권 정책을 충족하면 유효할 수 있다. 공유·팀·관리자 권한이 필요한 작업에서 그 비교만으로 충분한지 별도로 검증한다. 단순 문자열 검색은 조사 단서일 뿐 취약점 판정이 아니다.

#### 권한 상승 시나리오
- [ ] 일반 사용자 → 관리자 승격 경로 차단
- [ ] 읽기 권한 → 쓰기 권한 우회 경로 차단
- [ ] 타인 리소스 접근 (resource_id 추측)
- [ ] 공유 링크의 scope 확대 불가

#### 정책 감사
- [ ] 정책 변경의 승인·감사 기록을 기존 트랜잭션·트리거·이벤트 흐름과 대조한다. 단순 로그 테이블 존재를 감사 완비로 취급하지 않는다.
- [ ] 프론트 UI 권한 분기는 사용성 표시로만 사용한다. 프론트 주석 유무를 서버 인가의 증거로 취급하지 않는다.
- [ ] 서버가 **최종 권위**. 프론트 체크만으로 민감 작업 허용 금지

#### 토큰 검증
- [ ] 사용 중인 토큰 방식의 서명·발급자·대상·만료를 검증하고 키 회전·철회/권한 변경 반영 시점을 확인한다.
- [ ] 역할 클레임만 신뢰할 경우 그 신선도와 철회 정책이 요구사항을 충족하는지 확인한다. 모든 요청에 DB 재조회가 항상 필수라고 단정하지 않는다.
- [ ] 로컬 테스트에서 변조된 권한 클레임이 거부되는지 확인한다. 토큰·시크릿 값은 기록이나 보고서에 남기지 않는다.

### 5. 결정 문서화

설계·구현 요청이라면 프로젝트의 기존 설계 문서(없으면 `docs/authz.md`)에 다음을 기록한다. 감사 전용 요청에서는 근거·재현 조건·영향·불확실성을 보고하면 된다.
- 선택한 모델 (RBAC/ABAC/ReBAC/Hybrid) 과 **이유**
- 역할 목록과 각 역할의 권한 범위
- 필요한 스키마와 정책 평가 위치(서버·DB·외부 엔진)
- 대표 허용·거부 사례와 교차 테넌트 실패 사례
- 회귀 테스트 및 운영 전환·롤백 계획

## 구현 완료 체크리스트 (감사 전용 요청에는 적용하지 않음)

- [ ] 모델 선택 완료 (이유 문서화)
- [ ] 요청 범위의 스키마·정책 변경과 적용·롤백 승인을 구분
- [ ] 관련 서버/DB 경계에서 주체·행동·리소스·테넌트별 권한 검사 확인
- [ ] 정책 변경 감사 기록의 누락·중복 확인
- [ ] 허용·거부·교차 테넌트·권한 상승 회귀 테스트
- [ ] 기존 설계 문서와 배포/롤백 절차 갱신

## Anti-patterns

- ❌ RBAC 로 충분한데 ReBAC 오버엔지니어링
- ❌ ReBAC 필요한데 RBAC 로 억지로 밀어붙임 (권한 폭발)
- ❌ 프론트 `if (user.role === 'admin')` 만 걸고 서버 체크 누락
- ❌ 소유권 비교가 필요한 정책 조건을 충족하지 못하는데도 `user_id` 일치만으로 공유·관리 작업을 허용
- ❌ 정책 변경 시 audit log 기록 안 함
- ❌ 권한 변경·철회가 필요한데 토큰 클레임의 만료/갱신 정책을 정의하지 않음
- ❌ 관리자 전용 엔드포인트를 `/admin/*` 경로만으로 보호 (URL 숨김 = 보안 아님)

## Related skills

- `security-checklist` — B 구독상태 변경 섹션과 교차
- `paid-api-guard` — 결제 엔드포인트 인가
- `/cso` — Gstack 전체 보안 감사
- `simon-tdd` — 감사 회귀 테스트

## 공식 근거

- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP API1:2023 Broken Object Level Authorization](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/)
- [PostgreSQL unique constraints and null semantics](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [Supabase Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
