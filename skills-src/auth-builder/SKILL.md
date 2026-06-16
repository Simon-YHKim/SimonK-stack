---
name: auth-builder
description: "Use when the user asks to implement authentication, signup, login, or user management—triggers \"로그인 만들어줘\", \"회원가입 구현\", \"OAuth 연동\", \"소셜 로그인\", \"Passkey 추가\", \"본인인증\", \"implement auth\", \"add login\", \"user management\". Produces auth system with provider selection (Supabase/Clerk/NextAuth), social login (Google/Apple/Kakao/Naver), session management, role-based access, and Korea CI/DI verification."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# auth-builder

인증 + 회원관리 시스템을 실제 코드로 구현하는 skill.

## 발동 조건

- "로그인 만들어줘", "회원가입 구현", "OAuth 연동"
- "소셜 로그인 추가", "Passkey", "본인인증"
- "Clerk 세팅", "Supabase Auth", "NextAuth"

## Provider 선택

```
프레임워크?
├─ Next.js
│   ├─ 빠른 구현 → Clerk (프리빌트 UI, 조직 관리)
│   ├─ 커스텀 UI → Auth.js (NextAuth v5)
│   └─ Supabase 이미 사용 → Supabase Auth
├─ 모바일 (React Native / Flutter)
│   ├─ Firebase 생태계 → Firebase Auth
│   └─ Supabase 생태계 → Supabase Auth
├─ 풀 커스텀 / 셀프호스팅
│   └─ Keycloak 또는 Ory
└─ 노코드/로코드
    └─ Memberstack / Outseta
```

## 인증 방법 구현 우선순위

| 순위 | 방법 | 구현 복잡도 | 전환율 |
|---|---|---|---|
| 1 | Google OAuth | 낮음 | 높음 (원클릭) |
| 2 | Apple Sign-in | 낮음 | iOS 필수 |
| 3 | Kakao Login | 낮음 | 한국 필수 |
| 4 | Magic Link (이메일) | 낮음 | 비밀번호 피로 해소 |
| 5 | 이메일+비밀번호 | 중간 | 폴백 |
| 6 | Passkey (WebAuthn) | 높음 | 미래 표준 |
| 7 | 전화번호 OTP | 중간 (SMS 비용) | 한국 높음 |

## 구현 단계

### 1. 스키마

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE,
  phone TEXT UNIQUE,
  name TEXT,
  avatar_url TEXT,
  role TEXT NOT NULL DEFAULT 'free', -- free | pro | team_admin | enterprise
  email_verified BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  last_login_at TIMESTAMPTZ
);

CREATE TABLE auth_providers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL, -- google | apple | kakao | naver | email | phone
  provider_user_id TEXT NOT NULL,
  UNIQUE(provider, provider_user_id)
);

CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### 2. 소셜 로그인 플로우

```
Client → Provider (Google/Kakao) → Callback URL
  → 서버: provider_user_id로 auth_providers 조회
    → 있으면: 기존 user 로그인
    → 없으면: 새 user 생성 + auth_providers 연결
  → 세션/JWT 발급
```

### 3. 한국 본인인증 (CI/DI)

- **PASS 인증** (SKT/KT/LGU+): 14세 미만 차단, 1인 1계정 강제
- **NICE 본인인증**: 실명 확인 + 성별/연령대
- 사용 시점: 결제 / 민감 정보 접근 / 법적 요구

### 4. 권한 체계 (authz-designer 연동)

```
Free → 기본 기능
Pro → 전 기능 + 용량 확장
Team Admin → 팀원 초대/제거 + 결제 관리
Enterprise → SSO/SAML + 감사 로그 + 전용 인프라
```

### 5. 보안 필수사항

- CSRF 토큰 (상태 변경 API)
- Rate limiting (로그인 시도 5회/분)
- 세션 만료 + 리프레시 토큰 로테이션
- Password hashing: Argon2id (bcrypt 최소)
- OAuth state parameter (CSRF 방지)

## 검증 체크리스트

- [ ] 각 소셜 로그인 OAuth 플로우 동작
- [ ] 계정 연결 (같은 이메일 다른 provider)
- [ ] 세션 만료 + 자동 갱신
- [ ] Rate limiting (brute-force 차단)
- [ ] RBAC 권한 분리 동작
- [ ] 탈퇴 시 데이터 삭제 (GDPR/개인정보보호법)
- [ ] 한국 본인인증 플로우 (해당 시)

## Related Skills

- `authz-designer` — 복잡한 RBAC/ReBAC 설계
- `payment-integrator` — 유료 tier 연동
- `security-checklist` — RLS + IDOR 감사
- `revenue-scenario-tester` — Security Agent 검증


## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
