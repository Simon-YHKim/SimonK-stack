---
name: stack-architect
description: "Use when the user needs to decide on technical architecture—triggers "프론트만 필요해?", "백엔드 필요해?", "API 뭐 쓰지", "규모에 맞는 배포", "tech stack 정해줘", "architecture decision", "do I need a backend", "what API do I need". Produces a tech stack decision (frontend-only vs fullstack), API selection (REST/GraphQL/tRPC), scale-matched deployment plan, and stability roadmap to production-ready service."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# stack-architect

서비스의 기술 아키텍처를 결정하는 skill. 프론트/백/API/배포를 규모에 맞게 선택.

## 발동 조건

- "프론트만 필요해?", "백엔드도 필요해?", "API 뭐 쓰지"
- "tech stack 정해줘", "규모에 맞는 배포 방법"
- app-dev-orchestrator 초기 단계에서 호출

## Decision Tree

### 백엔드 필요 여부

```
서비스에 다음이 있는가?
├─ 유저 간 데이터 공유 → YES (백엔드 필수)
├─ 인증/결제 → YES (최소 BaaS)
├─ AI/ML 추론 → YES (서버 or 서버리스)
├─ 실시간 (채팅, 알림) → YES (WebSocket 서버)
├─ 위 모두 아님 (정적 도구/계산기) → NO (프론트만)
└─ 개인 데이터 저장만 → BaaS (Supabase/Firebase)
```

### API 선택

| API 유형 | 적합한 경우 | 예시 |
|---|---|---|
| **REST** | CRUD 중심, 단순 | 블로그, 이커머스 |
| **GraphQL** | 복잡한 관계형 데이터, 모바일 최적화 | SNS, 대시보드 |
| **tRPC** | TypeScript 풀스택, 빠른 개발 | Next.js + 1인 개발 |
| **gRPC** | 서버 간 통신, 고성능 | 마이크로서비스 |
| **없음 (BaaS)** | Supabase/Firebase 직접 호출 | MVP, 소규모 |

### 규모별 배포 전략

| 규모 | 유저 수 | 추천 스택 | 월 비용 |
|---|---|---|---|
| **MVP** | ~100 | Vercel + Supabase Free | $0 |
| **소규모** | ~1K | Cloudflare + Supabase Pro | $25-50 |
| **중규모** | ~10K | Vercel Pro + Railway + Redis | $100-300 |
| **대규모** | ~100K | AWS/GCP + k8s + CDN | $1000+ |
| **초대규모** | 1M+ | Multi-region + Edge + 전용 DB | 맞춤 |

### 안정성 로드맵

```
Phase 1 (MVP): 단일 서버, 수동 배포, 기본 모니터링
Phase 2 (Growth): CI/CD, 에러 추적 (Sentry), 업타임 모니터링
Phase 3 (Scale): 오토스케일, 로드밸런서, DB 리플리카, CDN
Phase 4 (Enterprise): Multi-AZ, DR 계획, SLA 99.9%+, 보안 감사
```

## 산출물

`ARCHITECTURE.md` 생성:
- 선택된 스택 (프론트/백/DB/API)
- 배포 플랫폼 + 예상 비용
- 안정성 단계별 로드맵
- 스케일링 트리거 지표

## Related Skills

- `db-selector` — DB 상세 선택
- `app-platform-selector` — Hybrid/PWA/Native 판단
- `deploy-configurator` — 선택된 플랫폼 실제 세팅
- `monetization-planner` — 규모에 맞는 수익 모델
