---
name: db-selector
description: "Use when the user needs to choose a database or data storage solution—triggers "DB 뭐 쓰지", "데이터베이스 선택", "Supabase vs Firebase", "PostgreSQL vs MongoDB", "DB 필요해?", "choose database", "which DB", "data storage". Produces database selection based on pre-cataloged service list, scale/requirements matching, migration guide, and cost projection."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# db-selector

최적 DB를 선택하는 skill. 사전 리스트업된 서비스 카탈로그 기반.

## 발동 조건

- "DB 뭐 쓰지", "데이터베이스 선택", "Supabase vs Firebase"
- "DB 필요해?", "데이터 어떻게 저장하지"
- stack-architect에서 DB 결정 필요 시 호출

## 사전 카탈로그

### 관계형 (SQL)

| 서비스 | 관리형 | 무료 티어 | 적합 규모 | 특징 |
|---|---|---|---|---|
| **Supabase** (PostgreSQL) | ✓ | 500MB | MVP~중규모 | Auth+Storage+Realtime 통합 |
| **PlanetScale** (MySQL) | ✓ | 5GB | 중~대규모 | Branching, 무정지 스키마 변경 |
| **Neon** (PostgreSQL) | ✓ | 512MB | MVP~중규모 | 서버리스, 브랜칭, 자동 스케일 |
| **Railway PostgreSQL** | ✓ | $5 크레딧 | 소~중규모 | 간편 배포 |
| **AWS RDS / Cloud SQL** | ✓ | 프리티어 12개월 | 대규모 | 엔터프라이즈 |
| **셀프호스팅 PostgreSQL** | ✗ | - | 모든 규모 | 완전 제어, 운영 부담 |

### NoSQL / Document

| 서비스 | 유형 | 무료 티어 | 적합 | 특징 |
|---|---|---|---|---|
| **Firebase Firestore** | Document | 관대 | 모바일 앱 | 실시간, 오프라인 sync |
| **MongoDB Atlas** | Document | 512MB | 유연한 스키마 | 범용 NoSQL |
| **DynamoDB** | Key-Value | 25 RCU/WCU | 초대규모 | 무한 스케일 |

### 특수 목적

| 서비스 | 용도 | 무료 티어 |
|---|---|---|
| **Redis (Upstash)** | 캐시, 세션, Rate Limit | 10K 명령/일 |
| **Pinecone / Qdrant** | 벡터 DB (AI/RAG) | 제한적 |
| **ClickHouse (Tinybird)** | 분석/OLAP | 제한적 |
| **Cloudflare D1** | Edge SQLite | 5GB |
| **Turso (libSQL)** | Edge SQLite | 8GB |

## Decision Tree

```
데이터 특성?
├─ 관계형 (유저, 주문, 구독) → SQL
│   ├─ BaaS 원함 (Auth 포함) → Supabase
│   ├─ MySQL 선호 / 무정지 마이그레이션 → PlanetScale
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

## 규모별 추천

| 규모 | DB | 이유 | 월 비용 |
|---|---|---|---|
| MVP (0-100 유저) | Supabase Free | 통합 BaaS, 빠른 시작 | $0 |
| 소규모 (100-1K) | Supabase Pro | 8GB, 백업 | $25 |
| 중규모 (1K-10K) | Neon / PlanetScale | 스케일링, 브랜칭 | $39-79 |
| 대규모 (10K-100K) | AWS RDS + Redis | 리플리카, 고가용성 | $200-500 |
| 초대규모 (100K+) | Multi-DB 아키텍처 | 용도별 분리 | $1000+ |

## Related Skills

- `stack-architect` — 전체 아키텍처 내 DB 위치 결정
- `payment-integrator` — 결제 데이터 스키마
- `consistency-guard` — DB 스키마 일관성 검증
