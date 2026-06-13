---
name: ad-monetization
description: "Use when the user asks to implement advertising in their app or site—triggers \"광고 붙여줘\", \"AdMob 연동\", \"AdSense 세팅\", \"보상형 광고\", \"ad placement\", \"implement ads\", \"monetize with ads\", \"banner ad\", \"interstitial\". Produces ad SDK integration (AdMob/AdSense/Carbon), placement strategy (non-intrusive positions), A/B testing for ad formats, AdBlock fallback, and policy compliance checks (Google Ad Policy)."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# ad-monetization

광고 수익화를 구현하는 skill.

## 발동 조건

- "광고 붙여줘", "AdMob 연동", "AdSense 세팅"
- "보상형 광고 추가", "배너 광고 위치"
- monetization-planner에서 "광고 모델" 선택 시 자동 체인

## 플랫폼별 SDK

| 플랫폼 | SDK | 용도 |
|---|---|---|
| Android/iOS | Google AdMob | 모바일 앱 광고 |
| 웹 | Google AdSense | 웹사이트 광고 |
| 개발자 타겟 | Carbon Ads | 기술 블로그/도구 |
| 게임 | Unity Ads / AppLovin | 보상형 + 인터스티셜 |

## 광고 유형 + 배치 전략

| 유형 | 위치 | eCPM | 유저 경험 |
|---|---|---|---|
| **배너** | 하단 고정 / 콘텐츠 사이 | 낮음 | 침입 최소 |
| **인터스티셜** | 화면 전환 시 | 높음 | 빈도 제한 필수 |
| **보상형 동영상** | 유저 선택 (리워드) | 매우 높음 | 긍정적 |
| **네이티브** | 콘텐츠 피드 내 | 중간 | 자연스러움 |

## 핵심 원칙

1. **빈도 제한**: 인터스티셜은 최소 60초 간격
2. **적절한 시점**: 자연스러운 전환점 (레벨 클리어, 글 읽기 완료)
3. **유료 전환과 균형**: 광고 → "광고 제거는 Pro에서" CTA
4. **AdBlock 대응**: fallback 메시지 or 대체 수익원 안내

## 정책 준수

- Google Ad Policy: 자기 클릭 금지, 콘텐츠 정책, 배치 가이드
- Apple: SKAdNetwork 4.0 어트리뷰션
- GDPR/한국: 개인화 광고 동의 (ATT prompt on iOS)

## 검증 체크리스트

- [ ] 테스트 광고 ID로 표시 확인
- [ ] 인터스티셜 빈도 제한 동작
- [ ] 보상형 광고: 보상 콜백 수신 확인
- [ ] AdBlock 감지 + fallback 동작
- [ ] 광고 미동의 시 비개인화 광고 표시
- [ ] revenue-scenario-tester Ad Agent 통과

## Related Skills

- `monetization-planner` — 광고 모델 결정
- `analytics-integrator` — 광고 수익 추적 (ROAS)
- `revenue-scenario-tester` — Ad Agent 검증

