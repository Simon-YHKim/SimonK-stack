---
name: security-orchestrator
description: "Sequentially runs the full 5-stage security audit (security-checklist → authz-designer → paid-api-guard → /cso comprehensive → /codex challenge) and produces a consolidated SUMMARY report with issues sorted by severity. Use this skill PROACTIVELY whenever the user says things like \"보안 점검\", \"보안 감사\", \"배포 전 보안\", \"전체 보안 확인\", \"comprehensive security review\", \"security audit\", \"production readiness security check\", \"check for vulnerabilities\"—even without explicit framing. Use ONLY for whole-stack audits. For narrower scopes, delegate to the specific skill: RLS only → security-checklist, RBAC design → authz-designer, payment API → paid-api-guard, infrastructure → /cso."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon
---

# Security Orchestrator

보안 감사 요청이 들어오면 `security-checklist`, `authz-designer`, `paid-api-guard`, Gstack `/cso`, Gstack `/codex challenge` 를 순차 실행한다. 각 skill 이 단독으로 잡히면 일부만 돌아가므로 상위 오케스트레이터로 강제 연쇄.

## When to use

- "보안 점검해줘", "종합 감사", "출시 전 보안", "전체 보안" 요청
- `app-dev-orchestrator` 단계 16
- 정기 월간 보안 감사

**단독 영역만 원하면** 상위 skill 사용하지 말고 직접:
- RLS 만 → `security-checklist`
- 권한 모델만 → `authz-designer`
- 결제 API 만 → `paid-api-guard`
- 인프라만 → `/cso`

## Workflow

### 1. 감사 범위 합의

사용자에게 확인:
- [ ] 범위: 애플리케이션 / 인프라 / 결제 / 전체?
- [ ] 배포 전 / 정기 / 사후 대응?
- [ ] 시간 제약: 30분(fast) / 2시간(standard) / 반나절(comprehensive)?

### 2. 순차 실행 (Comprehensive 기준)

#### Step 1 — `security-checklist`
4대 영역(RLS / 구독상태 / 이중 RateLimit / 예산한도) 감사. 적대적 테스트 5종 실행. 결과 → `docs/security/<date>-checklist.md`.

#### Step 2 — `authz-designer` 감사 섹션
모든 엔드포인트 인가 미들웨어 확인, IDOR 스캔, 권한 상승 시나리오 테스트. 결과 → `docs/security/<date>-authz.md`.

#### Step 3 — `paid-api-guard`
외부 API 호출 있는 경우 6층 방어 점검. 없으면 skip. 결과 → `docs/security/<date>-api.md`.

#### Step 4 — Gstack `/cso comprehensive`
인프라·시크릿·공급망·LLM·CI/CD·STRIDE 위협모델링. Gstack 내부 도구 사용. 결과 → `docs/security/<date>-cso.md`.

#### Step 5 — Gstack `/codex challenge`
적대적 리뷰. Codex CLI 가 의도적으로 취약점 찾기 시도. 결과 → `docs/security/<date>-codex.md`.

### 3. 통합 보고서

모든 결과를 `docs/security/<date>-SUMMARY.md` 에 합치고 심각도별 정렬:

```
## Critical (배포 차단)
- [ ] 이슈 1 (출처: security-checklist)

## High (배포 전 수정)
- [ ] 이슈 2 (출처: cso)

## Medium (2주 내 수정)
- [ ] 이슈 3 (출처: paid-api-guard)

## Low (백로그)
- [ ] 이슈 4 (출처: authz-designer)
```

### 4. 원자 커밋 수정 루프

발견 이슈를 하나씩 수정 → 테스트 → 원자 commit (`fix(security): <이슈>`) → 재검증.

Critical/High 가 전부 해결될 때까지 반복. `/ship` 은 그 뒤.

### 5. 회귀 테스트

모든 이슈를 `tests/security/` 아래 regression test 로 추가. `simon-tdd` 원칙 준수.

## Checklist

- [ ] 감사 범위·모드 확인
- [ ] 5단계 전부 실행 (또는 명시적 skip 사유 기록)
- [ ] 결과 각 파일에 저장
- [ ] SUMMARY.md 생성
- [ ] Critical/High 전부 수정·재검증
- [ ] 회귀 테스트 추가
- [ ] `/retro` 에 보안 세션 기록

## Anti-patterns

- ❌ 한 skill 만 돌리고 "완료" 선언
- ❌ Critical 이슈 발견했는데 배포 진행
- ❌ 회귀 테스트 없이 수정만 (다시 같은 구멍)
- ❌ SUMMARY.md 없이 흩어진 파일만
- ❌ `/cso comprehensive` 를 skip 하고 애플리케이션 감사만

## Related skills

- `security-checklist`, `authz-designer`, `paid-api-guard` — 구성원
- `/cso`, `/codex` — Gstack 통합
- `simon-tdd` — 회귀 테스트
- `app-dev-orchestrator` — 단계 16 호출자
- `/ship` — 감사 통과 후 배포
