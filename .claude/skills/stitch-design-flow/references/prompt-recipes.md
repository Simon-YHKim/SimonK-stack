# Stitch Prompt Recipes by Industry

Use these as starting points — adjust the tone/colors/screens to match your specific DESIGN.md.

## SaaS Dashboard

**Typical screens**: signup → onboarding → dashboard → settings → billing

- **Safe**: Linear/Stripe aesthetic. Left sidebar, top breadcrumb, data tables with sparklines, muted grays, one accent color
- **Bold**: Notion/Arc aesthetic. Block-based canvas, inline commands, softer radii, expressive empty states
- **Wild**: Raycast/Rauno Freiberg. Command palette first, dense but readable, monospace accents, animated transitions

## E-commerce (한국 커머스)

**Typical screens**: 홈 → 카테고리 → 상품 상세 → 장바구니 → 결제

- **Safe**: 쿠팡/네이버 쇼핑 스타일. Bright CTA 버튼, grid 기반 상품 카드, 리뷰 배지
- **Bold**: 29CM/무신사 스타일. Editorial 느낌, 큰 이미지, 브랜드 스토리 삽입
- **Wild**: 실험적 — 수직 스크롤 마그네틱 카드, 3D 제품 뷰어, 촉각적 microinteraction

**Constraints**: 한국어 copy 필수, 결제 UI 에 "카카오페이/네이버페이/토스페이" 아이콘 자리 확보

## 부동산 / PropTech

**Typical screens**: 검색 → 지도 → 매물 상세 → 관심 매물 → 연락하기

- **Safe**: 직방/다방 패턴. 좌측 지도, 우측 리스트, 필터 chip, 가격 sort
- **Bold**: 호갱노노 스타일. 시세 그래프 강조, 학군·교통 overlay, 데이터 시각화 우선
- **Wild**: Airbnb × 부동산 — 사진 우선, 스토리텔링, 가상 투어 viewport

**Constraints**: 전세/월세/매매 toggle, 평/m² 전환, 도로명 + 지번 주소 혼용

## 핀테크 / 뱅킹

**Typical screens**: 로그인 → 홈 → 계좌 → 이체 → 카드

- **Safe**: 토스/카카오뱅크. 큰 숫자, 단일 액션 CTA, 미니멀 카드 스택
- **Bold**: Revolut/Wise. 컬러풀 카드, 환율 위젯, 해외 송금 강조
- **Wild**: 실험적 — AR 지출 시각화, neon accent, 브루탈리스트

**Constraints**: 본인인증 플로우 자리, 생체인증 아이콘, 금액 단위는 "원/만원/억"

## 교육 / 에듀테크

**Typical screens**: 강의 목록 → 강의 상세 → 수강 화면 → 진도 → 수료증

- **Safe**: 인프런/코세라. 썸네일 grid, 진도 바, 찜/저장 기능
- **Bold**: Masterclass. Cinematic hero, 강사 스토리, 블랙 background
- **Wild**: Duolingo 게임화. 레벨·배지·연속일 강조, 캐릭터 일러스트

## AI 제품 / LLM Interface

**Typical screens**: 채팅 → 설정 → 히스토리 → 공유

- **Safe**: ChatGPT. 중앙 채팅, 좌측 히스토리, message actions hover
- **Bold**: Claude.ai. 아티팩트 사이드 패널, projects
- **Wild**: Perplexity/Arc Search. 검색 결과 카드, citation chips, follow-up suggestions

## 블로그 / Publishing

**Typical screens**: 홈피드 → 기사 상세 → 작성자 프로필 → 에디터

- **Safe**: Medium/Substack. 긴 폼 typography, 푸른 링크, minimal chrome
- **Bold**: Ghost/Posts. 에디토리얼 레이아웃, 큰 타이포, 개성 있는 accent
- **Wild**: 실험적 — 수직 parallax, 인라인 데이터 vis, annotation layer

## 모빌리티 / 차량 공유

**Typical screens**: 지도 → 차량 선택 → 예약 → 주행 → 반납

- **Safe**: 카카오T/우버. 지도 중심, 요금 계산, 결제 통합
- **Bold**: Rivian/Tesla app. 차량 3D, 실시간 상태, dark mode 우선
- **Wild**: Retro futuristic — grid 선, neon accent, vehicle telemetry heads-up

## 헬스케어 / 피트니스

**Typical screens**: 대시보드 → 운동/식단 → 기록 → 목표 → 커뮤니티

- **Safe**: Apple Health. Ring progress, 데이터 chips, soft shadows
- **Bold**: Whoop/Oura. Dark mode, biometric 강조, 수면 시각화
- **Wild**: Strava social. Activity feed, 이모지 reactions, 경로 지도

## 커뮤니티 / 소셜

**Typical screens**: 피드 → 포스트 상세 → 프로필 → 알림 → 메시지

- **Safe**: Reddit/Discord. 스레드 구조, upvote, 채널 사이드바
- **Bold**: Instagram/Threads. 이미지 우선, stories bar, 미니멀 chrome
- **Wild**: Are.na/Arena. 블록 기반 큐레이션, 무한 캔버스 느낌

---

## 공통 팁

- 한국 시장은 **모바일 우선** (데스크탑 비율 낮음). 375px baseline 후 1440px 확장
- **본인인증 / 결제 / 주소** 3종 세트는 자리를 먼저 확보
- **웹뷰 / PWA** 호환 디자인은 `position: fixed` 사용 시 safe area 고려
- **다크 모드** 는 선택이지만, Safe 변형은 라이트 기본 + 옵션, Bold/Wild 는 다크 우선도 OK
