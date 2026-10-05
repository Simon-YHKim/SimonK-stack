---
name: db-selector
description: "Use when the user needs to choose a database or data storage solution—triggers \"DB 뭐 쓰지\", \"데이터베이스 선택\", \"Supabase vs Firebase\", \"PostgreSQL vs MongoDB\", \"DB 필요해?\", \"choose database\", \"which DB\", \"data storage\". Produces a database choice and migration guide from existing and candidate workloads, with cost estimates only when current official prices and usage assumptions are known."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.1
author: simon-stack
---

# db-selector

요구사항에 맞는 DB를 비교하는 skill. 아래 카탈로그는 후보 예시이며 가격·무료 한도·기능 보장표가 아니다. 기존 프로젝트의 DB와 마이그레이션 비용을 먼저 확인한다.

## 발동 조건

- "DB 뭐 쓰지", "데이터베이스 선택", "Supabase vs Firebase"
- "DB 필요해?", "데이터 어떻게 저장하지"
- stack-architect에서 DB 결정 필요 시 호출

## 사전 카탈로그

### 관계형 (SQL)

| 서비스 | 관리형 | 검토할 특성 |
|---|---|---|
| **Supabase** (PostgreSQL) | ✓ | Auth·Storage·Realtime 통합 필요성 |
| **PlanetScale** | ✓ | 선택 엔진·브랜칭·유료 시작 조건 |
| **Neon** (PostgreSQL) | ✓ | 서버리스·브랜칭·사용량 과금 |
| **Railway PostgreSQL** | ✓ | 배포 편의·리소스 과금 |
| **AWS RDS / Cloud SQL** | ✓ | 운영형 DB·리전·가용성·과금 |
| **셀프호스팅 PostgreSQL** | ✗ | 운영 책임·백업·복구 |

### NoSQL / Document

| 서비스 | 유형 | 검토할 특성 |
|---|---|---|
| **Firebase Firestore** | Document | 실시간·오프라인 동기화 요구 |
| **MongoDB Atlas** | Document | 유연한 스키마·운영형 클러스터 |
| **DynamoDB** | Key-Value | 액세스 패턴·온디맨드/프로비저닝 과금 |

### 특수 목적

| 서비스 | 용도 |
|---|---|
| **Redis (Upstash)** | 캐시, 세션, Rate Limit |
| **Pinecone / Qdrant** | 벡터 DB (AI/RAG) |
| **ClickHouse (Tinybird)** | 분석/OLAP |
| **Cloudflare D1** | Edge SQLite |
| **Turso (libSQL)** | Edge SQLite |

## Decision Tree

```
데이터 특성?
├─ 관계형 (유저, 주문, 구독) → SQL
│   ├─ BaaS 원함 (Auth 포함) → Supabase
│   ├─ MySQL 선호 / 스키마 브랜칭 필요 → PlanetScale 등 현재 제품 비교
│   ├─ 서버리스 / 브랜칭 → Neon
│   └─ 엔터프라이즈 / 멀티 리전 → AWS RDS
├─ 유연한 스키마 / 모바일 → NoSQL
│   ├─ 실시간 + 오프라인 → Firestore
│   └─ 범용 → MongoDB Atlas
├─ 캐시 / Rate Limit → Redis (Upstash)
├─ AI 임베딩 → 벡터 DB (Qdrant)
├─ 분석 (대량 집계) → ClickHouse
└─ Edge 경량 → D1 / Turso
```

## 선택·비용 검증

- 유저 수만으로 DB나 월 비용을 확정하지 않는다. 저장량, 읽기·쓰기, 컴퓨트, 트래픽, 백업, 리전, 가용성, 초과 과금 한도를 산정한다.
- 현재 가격·무료 플랜·기능은 각 [Supabase](https://supabase.com/pricing), [PlanetScale](https://planetscale.com/pricing), [Neon](https://neon.com/pricing) 등 공식 페이지에서 선택 시점에 확인하고 확인일·가정·출처를 남긴다. PlanetScale에 무료 5GB 플랜이 있다고 전제하지 않는다.
- 비용에 필요한 입력이 없으면 금액을 미산정으로 남기고 필요한 사용량을 묻는다. 기존 DB의 이전·운영 위험도 선택 근거에 포함한다.
- 추가 과금 $0 조건에서는 유료 플랜·초과 사용·자동충전 활성화를 실행하지 않는다. 유료 서비스 생성은 별도 승인 대상이다.

## 선택 결과

- 기존 DB 유지 또는 전환 권고, 후보별 근거와 제외 이유, 확인하지 못한 가격·기능을 구분한다.
- 전환을 권고할 때는 백업·스키마/데이터 이전·읽기/쓰기 전환·검증·롤백의 개요를 제시한다. 운영 데이터 마이그레이션은 별도 승인과 실행 검증 전까지 시작하지 않는다.

## Related Skills

- `stack-architect` — 전체 아키텍처 내 DB 위치 결정
- `payment-integrator` — 결제 데이터 스키마
- `consistency-guard` — DB 스키마 일관성 검증

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
