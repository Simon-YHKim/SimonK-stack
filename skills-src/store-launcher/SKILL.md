---
name: store-launcher
description: "Use when the user asks to publish or launch an app to app stores—triggers \"스토어 출시\", \"Play Store 등록\", \"App Store 심사\", \"앱 배포\", \"publish to store\", \"app listing\", \"ASO\", \"store submission\". Produces store listing optimization (title/description/keywords/screenshots), policy compliance pre-check (Google/Apple guidelines), submission automation, and ASO (App Store Optimization) strategy."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# store-launcher

앱/서비스를 스토어에 출시하는 전 과정을 관리하는 skill.

## 발동 조건

- "스토어 출시해줘", "Play Store 등록", "App Store 심사 준비"
- "앱 배포", "ASO 최적화", "리스팅 작성"
- app-dev-orchestrator 후반에서 호출

## 지원 스토어

| 스토어 | 수수료 | 심사 기간 | 핵심 정책 |
|---|---|---|---|
| **Google Play** | 15% (첫 $1M) | 수 시간~3일 | 콘텐츠 정책, 타겟 API |
| **Apple App Store** | 15-30% | 1-7일 | HIG 준수, 4.2 최소 기능 |
| **Galaxy Store** | 0% (프로모 기간) | 1-3일 | 삼성 특화 기능 |
| **Chrome Web Store** | 5% | 수 시간~3일 | Manifest V3 |
| **Microsoft Store** | 5-15% | 1-3일 | 보안 검사 |

## 출시 체크리스트

### 공통

- [ ] 아이콘 (512x512 PNG, 모서리 라운딩 주의)
- [ ] 스크린샷 (각 스토어 규격별 최소 수량)
- [ ] 프로모 영상 (30초, 선택)
- [ ] 짧은 설명 (80자) + 긴 설명 (4000자)
- [ ] 개인정보처리방침 URL
- [ ] 콘텐츠 등급 설문 완료

### Google Play 전용

- [ ] Target API level (최신 -1 이내)
- [ ] Data Safety 섹션 작성
- [ ] 테스트 계정 (리뷰어용)
- [ ] 20명 클로즈드 테스터 14일 (신규 개발자 요구)

### Apple 전용

- [ ] App Privacy 라벨
- [ ] ATT (App Tracking Transparency) 구현
- [ ] 4.2 Minimum Functionality (웹뷰만은 리젝)
- [ ] 5.1.1 Data Collection (수집 데이터 명시)
- [ ] In-App Purchase는 반드시 Apple IAP 사용

## ASO (App Store Optimization)

1. **키워드 리서치**: 경쟁자 앱 키워드 분석
2. **타이틀**: 핵심 키워드 포함 (30자)
3. **부제**: 가치 제안 (30자)
4. **스크린샷 순서**: 핵심 기능 → 차별점 → 사회적 증거
5. **리뷰 유도**: 긍정 경험 직후 인앱 리뷰 요청

## 리젝 방지

**자주 걸리는 사유**:
- 4.2: 기능이 너무 적음 / 웹뷰 래퍼
- 2.1: 크래시 / 버그
- 4.0: 스팸 / 기존 앱 복제
- 5.1.1: 개인정보 미명시
- 3.1.1: 외부 결제 유도 (Apple)

## Related Skills

- `deploy-configurator` — CI/CD에서 자동 빌드→스토어 업로드
- `growth-engine` — 출시 후 ASO + 마케팅
- `revenue-scenario-tester` — Store Agent 정책 준수 검증

