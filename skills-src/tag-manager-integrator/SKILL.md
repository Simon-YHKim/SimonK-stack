---
name: tag-manager-integrator
description: "Use when the user wants to set up event tracking via Google Tag Manager or similar—triggers "GTM 세팅", "gtag 설치", "태그 관리자", "이벤트 추적 설정", "전환 추적", "setup GTM", "tag manager", "conversion tracking", "event tracking setup". Produces GTM/gtag configuration, event taxonomy aligned with analytics-integrator, conversion tracking for ads, and periodic analysis reports with optimization suggestions."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# tag-manager-integrator

GTM/gtag 기반 이벤트 추적 + 분석 + 최적화 제안.

## 발동 조건

- "GTM 세팅해줘", "gtag 설치", "태그 관리자 설정"
- "전환 추적 붙여줘", "이벤트 추적 설정"
- analytics-integrator와 연동하여 이벤트 계층 구축

## GTM vs Direct gtag

| 방법 | 장점 | 단점 | 추천 |
|---|---|---|---|
| **GTM** | 코드 변경 없이 태그 관리, 버전 관리, 미리보기 | 초기 설정 복잡 | 마케팅팀 있을 때 |
| **Direct gtag** | 단순, 빠른 구현 | 태그 추가마다 배포 | 1인 개발 |
| **PostHog/Mixpanel SDK** | 제품 분석 최적화 | 광고 추적 별도 | 제품 중심 |

## 이벤트 계층 설계

```
Layer 1: Page-level (자동)
  - page_view, scroll_depth, time_on_page

Layer 2: Interaction (반자동)
  - button_click, form_submit, video_play

Layer 3: Business (수동 구현)
  - signup_completed, subscription_started, purchase_completed

Layer 4: Custom (비즈니스 로직)
  - aha_moment_reached, feature_X_used, invite_sent
```

## 전환 추적 (Conversion Tracking)

| 플랫폼 | 전환 이벤트 | 설정 방법 |
|---|---|---|
| Google Ads | purchase, sign_up | gtag conversion linker |
| Meta (Facebook) | Purchase, Lead | Meta Pixel + CAPI |
| Kakao | 구매, 가입 | Kakao Pixel |
| Naver | 구매완료 | Naver 전환 스크립트 |

## 주기적 분석 리포트

```markdown
# Tag Analysis Report — 주간

## 이벤트 발화 현황
| 이벤트 | 발화 수 | 전주 대비 | 이상 여부 |
|---|---|---|---|
| page_view | 12,340 | +5% | 정상 |
| signup | 234 | -12% | ⚠️ 하락 |

## 전환 퍼널
방문 → 가입 → 활성화 → 결제
100% → 8% → 45% → 12%

## 최적화 제안
1. signup -12% 하락: 가입 폼 변경 확인 필요
2. 활성화→결제 전환 12%: 온보딩 개선 검토
```

## Related Skills

- `analytics-integrator` — 분석 도구 기반 (이 skill은 태그 계층)
- `growth-engine` — 전환 추적 → 마케팅 최적화
- `aarrr-growth-planner` — 퍼널별 전환 지표 정의
- `consistency-guard` — 이벤트 명명 일관성 강제
