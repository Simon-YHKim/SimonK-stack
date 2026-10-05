---
name: authz-designer
description: Use when the user asks to design or audit an authorization system—"권한 시스템 설계", "RBAC 넣어줘", "ReBAC", "IDOR 점검", "role-based access", "multi-tenant permissions", "share feature like Notion", "team workspace permissions"—and produces the right model (RBAC / ABAC / ReBAC / hybrid) plus DDL for authz_roles, authz_role_assignments, authz_policies, authz_audit_log. Also audits existing code for IDOR and privilege-escalation bugs.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon
---

# Authz Designer

인가(Authorization) 모델을 설계하고 감사한다. 인증(Authentication)과 구분: "누구인가"가 아닌 "무엇을 할 수 있는가".

## When to use

- 새 앱 기획 단계 (`app-dev-orchestrator` 단계 8)
- 기존 앱 권한 리팩토링
- 사용자가 "권한 시스템 설계", "RBAC 넣어줘", "역할 정의", "공유 기능 만들고 싶어" 요청
- 보안 감사 중 IDOR 의심

## Workflow

### 1. 모델 선택 가이드

| 모델 | 적합 시나리오 | 예시 |
|---|---|---|
| **RBAC** (Role-Based) | 역할이 소수·고정, 단순 관리자 페이지 | SaaS admin/user/viewer |
| **ABAC** (Attribute-Based) | 시간·IP·소유자·부서 등 속성 조건 복잡 | 금융(시간제한), 엔터프라이즈 |
| **ReBAC** (Relationship-Based) | 문서·팀·프로젝트 협업 그래프 | Notion, Figma, GitHub, Linear |
| **Hybrid** | RBAC 베이스 + ABAC 조건 + 민감 리소스 ReBAC | 가장 현실적 |

### 2. 추천 스택

- **ReBAC**: [OpenFGA](https://openfga.dev/) (Auth0) 또는 [SpiceDB](https://authzed.com/spicedb) (Zanzibar 기반)
- **RBAC/ABAC**: [Casbin](https://casbin.org/), [Oso](https://www.osohq.com/)
- **단순**: Postgres RLS + 정책 테이블 (Supabase 와 결합 좋음)

### 3. 스키마 템플릿 (Hybrid, Postgres)

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
  UNIQUE(user_id, role_id, resource_type, resource_id)
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
- [ ] **모든 엔드포인트**에 인가 미들웨어 적용 (누락 = IDOR)
  - 확인 스크립트:
    ```bash
    grep -r "router\.\(get\|post\|put\|delete\|patch\)" src/ | grep -v "authorize\|requireAuth"
    ```
- [ ] `user_id` 비교만 하는 경로 찾기 (role 체크 누락):
  ```bash
  grep -r "where.*user_id.*=.*req\.user\.id" src/
  ```

#### 권한 상승 시나리오
- [ ] 일반 사용자 → 관리자 승격 경로 차단
- [ ] 읽기 권한 → 쓰기 권한 우회 경로 차단
- [ ] 타인 리소스 접근 (resource_id 추측)
- [ ] 공유 링크의 scope 확대 불가

#### 정책 감사
- [ ] `authz_policies` 변경 시 `authz_audit_log` 자동 기록
- [ ] 프론트 UI 권한 분기는 **장식용** 주석 의무:
  ```tsx
  {/* UI-only gate — server remains authoritative */}
  {user.role === 'admin' && <AdminButton />}
  ```
- [ ] 서버가 **최종 권위**. 프론트 체크만으로 민감 작업 허용 금지

#### 토큰 검증
- [ ] JWT 만료·서명 검증
- [ ] 토큰 재사용 (replay) 방지: nonce 또는 짧은 TTL + refresh
- [ ] 클레임 위조 시도 테스트 (JWT payload 에 `role: admin` 주입)

### 5. 결정 문서화

`docs/authz.md` 에 다음 필수 기록:
- 선택한 모델 (RBAC/ABAC/ReBAC/Hybrid) 과 **이유**
- 역할 목록과 각 역할의 권한 범위
- 스키마 (위 DDL)
- 정책 예시 3개 이상
- 감사 테스트 체크리스트

## Checklist

- [ ] 모델 선택 완료 (이유 문서화)
- [ ] DDL 마이그레이션 작성·적용
- [ ] 인가 미들웨어 모든 엔드포인트 적용
- [ ] `authz_audit_log` 트리거 설정
- [ ] IDOR 회귀 테스트 3건 이상
- [ ] 권한 상승 회귀 테스트 3건 이상
- [ ] `docs/authz.md` 작성
- [ ] `security-checklist` B 섹션과 교차 확인 (민감 필드 보호)

## Anti-patterns

- ❌ RBAC 로 충분한데 ReBAC 오버엔지니어링
- ❌ ReBAC 필요한데 RBAC 로 억지로 밀어붙임 (권한 폭발)
- ❌ 프론트 `if (user.role === 'admin')` 만 걸고 서버 체크 누락
- ❌ `user_id = req.user.id` 비교만 하고 role 체크 누락 (IDOR)
- ❌ 정책 변경 시 audit log 기록 안 함
- ❌ JWT 에서 role 만 읽고 DB 재검증 skip (탈취 시 영구 유효)
- ❌ 관리자 전용 엔드포인트를 `/admin/*` 경로만으로 보호 (URL 숨김 = 보안 아님)

## Related skills

- `security-checklist` — B 구독상태 변경 섹션과 교차
- `paid-api-guard` — 결제 엔드포인트 인가
- `/cso` — Gstack 전체 보안 감사
- `simon-tdd` — 감사 회귀 테스트
