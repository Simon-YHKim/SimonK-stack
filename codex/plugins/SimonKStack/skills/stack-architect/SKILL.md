---
name: stack-architect
description: "Use when the user needs to decide on technical architecture—triggers \"프론트만 필요해?\", \"백엔드 필요해?\", \"API 뭐 쓰지\", \"규모에 맞는 배포\", \"tech stack 정해줘\", \"architecture decision\", \"do I need a backend\", \"what API do I need\". Produces a frontend/backend and API decision, deployment candidates grounded in the existing stack and measured workload, and a stability roadmap without assumed pricing."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.1
author: simon-stack
---

# stack-architect

서비스의 기술 아키텍처를 결정하는 skill. 기존 프로젝트의 스택·운영 계약을 먼저 확인하고 프론트/백/API/배포 변경의 필요성을 판단한다.

## 발동 조건

- "프론트만 필요해?", "백엔드도 필요해?", "API 뭐 쓰지"
- "tech stack 정해줘", "규모에 맞는 배포 방법"
- app-dev-orchestrator 초기 단계에서 호출

## Decision Tree

### 백엔드 필요 여부

```
서비스에 다음이 있는가?
├─ 유저 간 데이터 공유 → 신뢰 가능한 서버/관리형 백엔드 검토
├─ 인증/결제 → 비밀키·검증 책임을 둘 신뢰 경계 검토
├─ AI/ML 추론 → 온디바이스/로컬 가능성, 원격 비용·데이터 경계 비교
├─ 실시간 (채팅, 알림) → 요구 지연에 맞춰 관리형 실시간/WebSocket/폴링 비교
├─ 위 모두 아님 (정적 도구/계산기) → 프론트만으로 가능한지 검토
└─ 개인 데이터 저장만 → 기기 내 저장과 동기화 필요 여부를 비교
```

### API 선택

| API 유형 | 적합한 경우 | 예시 |
|---|---|---|
| **REST** | CRUD 중심, 단순 | 블로그, 이커머스 |
| **GraphQL** | 복잡한 관계형 데이터, 모바일 최적화 | SNS, 대시보드 |
| **tRPC** | TypeScript 풀스택, 빠른 개발 | Next.js + 1인 개발 |
| **gRPC** | 서버 간 통신, 고성능 | 마이크로서비스 |
| **없음 (BaaS SDK)** | 클라이언트 접근을 검증된 권한 정책으로 제한하고 비밀키를 노출하지 않을 때 | 관리형 백엔드 사용 |

### 규모별 배포 검토

| 단계 | 검토할 구성 | 확장 신호 |
|---|---|---|
| **MVP** | 기존 스택·정적 호스팅·관리형 백엔드 중 최소 구성 | 핵심 기능과 측정 가능한 사용량 |
| **Growth** | CI/CD·관측성·백업·필요 시 캐시 | 지연·실패율·DB 부하·운영시간 |
| **Scale** | 부하에 맞춘 캐시·복제·지역 분산 | 실제 병목과 가용성 요구 |

유저 수만으로 특정 공급자·월 비용·Kubernetes 도입을 확정하지 않는다. 기존 배포 계약과 실측 부하를 먼저 확인하고, 비용은 후보별 공식 가격·리전·무료 한도·초과 사용 조건으로 산정해 출처·확인일·가정을 남긴다. 입력이 부족하면 비용은 미산정으로 표시한다. 추가 과금 $0 요청에서는 유료 리소스 생성·초과 사용·자동충전 활성화를 실행하지 않는다.

### 안정성 로드맵

```
Phase 1 (MVP): 단일 서버, 수동 배포, 기본 모니터링
Phase 2 (Growth): CI/CD, 에러 추적 (Sentry), 업타임 모니터링
Phase 3 (Scale): 오토스케일, 로드밸런서, DB 리플리카, CDN
Phase 4 (Enterprise): 필요 시 Multi-AZ, DR 계획, 목표 SLO·계약 검토, 보안 감사
```

단계는 구현 의무나 일정표가 아니다. 실제 장애·복구·가용성 요구가 없는 구성요소를 사용자 수만으로 추가하지 않는다.

## 산출물

`ARCHITECTURE.md` 생성:
- 선택된 스택 (프론트/백/DB/API)
- 배포 플랫폼 후보 + 출처·확인일·사용량 가정이 있는 예상 비용(근거 없으면 미산정)
- 안정성 단계별 로드맵
- 스케일링 트리거 지표

아키텍처 결정 문서는 배포나 마이그레이션 승인으로 간주하지 않는다. 운영 변경은 별도 권한·비용·검증 게이트를 따른다.

## Related Skills

- `db-selector` — DB 상세 선택
- `app-platform-selector` — Hybrid/PWA/Native 판단
- `deploy-configurator` — 선택된 플랫폼 실제 세팅
- `monetization-planner` — 규모에 맞는 수익 모델

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
