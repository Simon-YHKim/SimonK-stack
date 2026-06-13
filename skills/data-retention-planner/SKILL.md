---
name: data-retention-planner
description: "Use when the user asks to design a data retention/deletion schedule—triggers \"보존정책\", \"데이터 삭제 주기\", \"TTL purge\", \"파기 정책\", \"retention policy\", \"data deletion schedule\", \"purge job\", \"backup expiry\", and /data-retention-planner. Produces a per-data-class retention table (보유 근거 + 보존기간 + 파기 트리거), TTL/cron purge jobs (soft-delete grace → hard delete), backup expiry alignment, and an append-only purge audit log. Enforces PIPA §21 (목적 달성 시 지체 없이 파기) and GDPR storage-limitation. Hands off to data-flow-mapper (what data exists), consent-manager (consent-withdrawal deletes), auth-builder (account-deletion cascade)."
allowed-tools: Read, Write, Bash, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# data-retention-planner

데이터 클래스별 **보존기간 + 파기 스케줄**을 실제 코드로 설계하는 skill. TTL/cron purge 잡, 백업 만료 정렬, append-only 파기 감사로그까지 산출한다. 임의의 앱(웹/RN + 서버)에 적용하는 범용 스킬이다.

## 발동 조건

- "보존정책", "데이터 삭제 주기", "TTL purge", "파기 정책 짜줘"
- "retention policy", "backup expiry", "언제까지 보관해", "탈퇴하면 데이터 언제 지워"
- data-flow-mapper(데이터 인벤토리 완성) 후 "그럼 이거 언제 지워?" 로 이어질 때
- consent-manager(동의 철회 시 삭제) / auth-builder(탈퇴 시 cascade) 에서 파기 규칙이 필요할 때

## 강제 베스트프랙티스 (절대 약화 금지)

| 원칙 | 규칙 |
|---|---|
| **목적 종료 = 파기** | PIPA §21: 보유 목적 달성 시 **지체 없이 파기**. 보존기간은 "최대 상한"이지 "기본 보관 기간"이 아니다. |
| **법정 보존 분리** | 법정 의무 보존(전자상거래법 거래기록 5년, 전자금융 5년 등)은 **다른 클래스로 분리** 보관 + 목적 외 접근 차단. 만료 후 자동 파기. |
| **soft → hard 2단계** | 즉시 hard delete 금지. soft-delete(`deleted_at`) → grace 기간 → hard delete. grace 안에 복구·법적 hold 가능. |
| **백업 정렬** | 운영 DB 에서 지웠는데 백업에 남으면 파기 아님. 백업 보존주기 ≤ (해당 클래스 보존기간 + grace) 로 정렬. |
| **파기 감사로그** | 모든 파기 실행을 append-only 로 기록(언제·어느 클래스·몇 건·트리거·실행자). UPDATE/DELETE 차단. |
| **fail-safe** | purge 잡 실패는 silent 금지. 0건 삭제도 로그. 예외 시 알림 + 다음 주기 재시도(건너뛰기 금지). |

> 보존기간은 **법적 상한 또는 명시 동의 범위 내 최소값**으로 잡는다. "혹시 몰라서 오래" 는 storage-limitation 위반.

## 데이터 클래스 분류 (예시 — 프로젝트에 맞게 조정)

| 클래스 | 예시 데이터 | 근거(retention basis) | 보존기간(상한) | 파기 트리거 |
|---|---|---|---|---|
| `account_core` | 프로필, 인증 식별자 | 서비스 제공 계약 | 탈퇴 + grace 30일 | 회원 탈퇴 |
| `user_content` | 사용자 생성 데이터 | 서비스 제공 | 탈퇴 + grace 30일 | 탈퇴 / 콘텐츠 삭제 |
| `consent_ledger` | 동의 원장 | 입증 책임(GDPR Art.7) | 동의 효력 + 분쟁시효 | 시효 만료 |
| `legal_txn` | 거래·결제 기록 | **법정 의무**(전자상거래법) | 5년(법정) | 법정기간 만료 |
| `ai_audit_log` | LLM 호출 감사 | 안전·책임 추적 | 1년 | 기간 만료 |
| `analytics_event` | 행동 이벤트 | 동의(analytics) | 14개월(GA4 기본) | 기간 / 동의 철회 |
| `support_ticket` | 문의 내역 | 응대·분쟁 | 처리완료 + 3년 | 기간 만료 |
| `transient` | 세션·OTP·임시토큰 | 기능 동작 | 분~시간(TTL) | TTL 만료 |
| `marketing` | 마케팅 수신 동의 정보 | 동의 | 철회 시 / 2년 미접속 | 철회 / 휴면 |

- 클래스는 `templates/retention-classes.json` 가 **단일 소스**. 코드·cron·문서가 여기서 파생.
- 법정 보존(`legal_txn`)은 다른 클래스가 만료돼도 **독립** 만료. 목적 외 조회 차단(접근 로그).

## 한국 법정 보존기간 참고 (앵커값 — 실제 적용 전 최신 확인)

| 데이터 | 법 | 기간 |
|---|---|---|
| 계약·청약철회 기록 | 전자상거래법 | 5년 |
| 대금결제·재화공급 기록 | 전자상거래법 | 5년 |
| 소비자 불만·분쟁처리 | 전자상거래법 | 3년 |
| 표시·광고 기록 | 전자상거래법 | 6개월 |
| 전자금융 거래기록 | 전자금융거래법 | 5년 |
| 통신사실확인자료(로그인 IP 등) | 통신비밀보호법 | 3개월 |
| 세무 관련 장부·증빙 | 국세기본법 | 5년(일반) |

> GDPR 은 고정 기간을 정하지 않음 → "목적에 필요한 기간"을 스스로 정의·문서화(storage-limitation, Art.5(1)(e)). 위 한국 값은 상한 앵커일 뿐, 목적 종료 시 그 전에 파기.

## Workflow

### 1. 진단 (AskUserQuestion)
- 데이터 인벤토리 있나? (없으면 → data-flow-mapper 먼저)
- DB/스토리지? (Postgres/Supabase / MySQL / Mongo / S3·R2 객체스토리지) — purge 방식 분기
- 법정 보존 대상 있나? (결제·거래 → `legal_txn` 분리 필수)
- 백업 운영? (주기·보존 — 백업 만료 정렬 대상)
- 스케줄러? (Supabase pg_cron / GitHub Actions cron / Cloud Scheduler / Vercel Cron)

### 2. 현황 스캔 (결정론 스크립트)
```
bash skills/data-retention-planner/scripts/scan-retention.sh [project-root]
```
- 타임스탬프 컬럼(`created_at`/`deleted_at`/`expires_at`), TTL/cron 설정, 백업 설정, 객체스토리지 lifecycle 후보를 **인덱싱**(자동 분류 아님 — 사람이 클래스에 매핑).

### 3. 클래스 정의 (단일 소스)
- `templates/retention-classes.json` 를 프로젝트에 맞게 채운다. 각 클래스: `retentionDays`, `graceDays`, `basis`, `trigger`, `table`, `timestampColumn`, `softDelete`(bool), `legalHold`(bool).

### 4. purge 계획 생성 (결정론 스크립트)
```
node skills/data-retention-planner/scripts/gen-purge-plan.mjs <classes.json> [--out <dir>]
```
- classes.json → 클래스별 **cron 표현식 + soft/hard DELETE SQL 스켈레톤 + 감사로그 INSERT** 를 생성. 입력 같으면 출력 같음(stub 아님, 실제 로직).
- `legalHold:true` 클래스는 hard-delete SQL 을 생성하되 **법정기간 만료 조건**을 강제로 끼운다(즉시 삭제 SQL 생성 안 함).

### 5. purge 잡 설치
- `templates/purge-job.ts` — soft→hard 2단계 + 클래스 루프 + 감사로그 + fail-safe(예외 시 throw → 스케줄러 재시도). Supabase 엣지/Node cron 양쪽 주석.
- 시크릿(서비스 롤 키 등)은 반드시 **환경변수**. 하드코딩 금지.

### 6. 감사로그 + 백업 정렬
- `templates/purge-audit-log.sql` — append-only(UPDATE/DELETE 트리거 차단). 매 purge 실행마다 INSERT.
- 백업 보존주기를 가장 짧은 클래스 보존기간에 맞춰 점검: 운영에서 지운 데이터가 백업 만료 전까지만 잔존하도록.

## 검증 체크리스트

- [ ] 모든 데이터 클래스가 `retention-classes.json` 에 명시 (분류 누락 0)
- [ ] 법정 보존 데이터(`legal_txn`)가 별도 클래스 + 목적 외 접근 차단
- [ ] 즉시 hard-delete 없음 — soft-delete → grace → hard 2단계 동작
- [ ] `legalHold:true` 클래스에 무조건 만료조건 없는 DELETE SQL 미생성
- [ ] cron 표현식이 클래스 보존주기와 일치 (gen-purge-plan 출력 == 입력 기반 결정론)
- [ ] purge 잡 실패 시 알림 + 재시도 (silent skip 금지), 0건도 로그
- [ ] 파기 감사로그 append-only (UPDATE/DELETE 트리거 차단 확인)
- [ ] 백업 보존주기 ≤ 최단 클래스 보존기간 + grace (운영 삭제분 백업 잔존 점검)
- [ ] 객체스토리지(S3/R2) lifecycle 규칙이 DB 클래스와 정렬
- [ ] 탈퇴/동의철회 트리거가 즉시 soft-delete 를 발생 (배치 대기 아님)
- [ ] 시크릿 하드코딩 0 (서비스 롤 키 등 전부 env)

## Related Skills

- `data-flow-mapper` — 어떤 데이터가 어디 있는지(인벤토리). 보존정책의 입력. 먼저 실행 권장.
- `consent-manager` — 동의 철회 시 해당 카테고리 데이터 파기 트리거 연결.
- `auth-builder` — 회원 탈퇴 시 `account_core`/`user_content` cascade soft-delete 진입점.
