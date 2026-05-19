---
name: viral-launch
description: "Use when the user wants to brainstorm or execute viral marketing for an app launch or update—triggers \"바이럴 어떻게 하지\", \"홍보 아이디어\", \"인스타 마케팅\", \"커뮤니티 홍보\", \"앱 내 공유 기능\", \"입소문 만들기\", \"viral marketing\", \"how to go viral\", \"organic growth tactics\", \"instagram launch\", \"community launch\", \"share feature design\". Different from aarrr-growth-planner (which is a framework analysis) and growth-engine (which sets up infrastructure like push/email): this skill produces a CHANNEL-BY-CHANNEL viral playbook — in-app share mechanics, Instagram post sequence, Korean community thread templates (Reddit/Disquiet/긱뉴스/뽐뿌), word-of-mouth seed list, and launch-day timeline. Each tactic has a concrete artifact (post draft, screenshot spec, share-button copy) not just abstract advice."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# viral-launch

채널별 **바이럴 플레이북**을 생성합니다. 추상 조언이 아니라 _복붙 가능한 산출물_ 을 만듭니다.

## 발동 조건

- "이거 어떻게 바이럴 시키지?"
- "인스타에 어떻게 올려야 잘 될까?"
- "커뮤니티 홍보 글 써줘"
- "앱 내부에서 공유 기능 어떻게 넣지?"
- "launch day 플랜"

## 다른 스킬과의 차이

| 스킬 | 결과물 |
|---|---|
| `aarrr-growth-planner` | 프레임워크 분석 (Acquisition → Revenue) |
| `growth-engine` | 인프라 셋업 (push, email, A/B 도구) |
| **`viral-launch`** | **채널별 즉시 복붙 가능한 콘텐츠 + 메커니즘** |

## 4가지 채널 (사용자가 명시한 우선순위)

### 1. 앱 내부 기능 (가장 강력, K-factor 직접 영향)

| 메커니즘 | 적합한 앱 |
|---|---|
| 결과물 공유 (이미지/카드 생성) | 도구, 게임, 진단 앱 |
| 초대 링크 + 양쪽 보상 | 커뮤니티, 게임 |
| 친구 활동 표시 ("X님이 시작했어요") | 소셜, 챌린지 |
| 워터마크 공유 카드 | 사진/디자인 앱 |
| 챌린지 / 랭킹 | 게임, 학습 |

산출:
- 공유 버튼 위치 (와이어프레임 스케치)
- 공유 카드 디자인 spec (1080×1920, 1080×1080)
- CTA 문구 3안

### 2. 인스타그램

| 포맷 | 용도 |
|---|---|
| 릴스 (≤ 15초) | demo, before/after |
| 캐러셀 (5-10장) | 사용법, 스토리텔링 |
| 스토리 (24h) | 출시 카운트다운, 베타 모집 |
| 고정 게시물 | 가치 제안 + 다운로드 링크 |

산출:
- 7일 게시 캘린더 (구체 일자별 포스트 안)
- 릴스 스크립트 1개 (영상 컷별 대사)
- 캐러셀 슬라이드 5장 카피
- 해시태그 30개 (대-중-소 비율 5:15:10)
- 사용자가 직접 만들기 어려운 자산 명시 (디자이너 의뢰 항목)

### 3. 커뮤니티

**한국**:
- 디스콰이엇 (Disquiet) — 인디 메이커
- 긱뉴스 — 개발자
- 뽐뿌 / 클리앙 / 디시 — 일반 사용자
- 인벤 — 게임
- 카카오톡 오픈채팅 — 타겟 커뮤니티

**글로벌**:
- Product Hunt — 글로벌 인디
- Reddit (subreddit 선정 중요) — 영문
- Hacker News — 개발자/기술
- Indie Hackers — SaaS / 메이커

산출 (커뮤니티당):
- 게시 글 초안 (제목 + 본문)
- 댓글 응대 가이드 (자주 나올 질문 5개 + 답변)
- 게시 _시점_ 권고 (요일/시간대)
- _금기_ — 자기홍보 강도 한도, 룰 위반 항목

### 4. 입소문 / 시드

- 베타 테스터 → 출시일 _동시 게시_ 약속
- 친구 10명 메시지 템플릿
- 트위터 / 스레드 / X 출시 트윗 1개
- 블로그 / 노션 페이지 1개 (장문 — SEO 자산)

## 워크플로

1. **앱 정보 수집**: 이름, 한 줄 설명, 타겟, 핵심 가치, 차별점
2. **K-factor 추정**: 현재 공유 메커니즘이 있는가? 없으면 § 1 우선
3. **채널 우선순위 결정**: 타겟에 맞는 2-3개 채널 집중
4. **산출물 생성**: 채널별 § 위 항목
5. **출시일 타임라인**: D-7부터 D+7까지 1시간 단위
6. **회수 메트릭**: 채널별 추적 UTM 파라미터 + KPI (다운로드, signup, share 클릭)

## 산출 파일

```
viral-launch/
├── README.md                   ← 마스터 플랜
├── timeline.md                 ← D-7 ~ D+7
├── channels/
│   ├── in-app-share.md
│   ├── instagram-7day.md
│   ├── community-disquiet.md
│   ├── community-reddit.md
│   └── word-of-mouth.md
├── assets/
│   ├── share-card-spec.md
│   ├── reels-script.md
│   └── carousel-copy.md
└── metrics.md                  ← UTM + KPI
```

## 안티패턴

- ❌ "SNS에 적극 홍보하세요" (구체성 0)
- ❌ 모든 채널 균등 분산 (타겟 무관)
- ❌ 한국 앱인데 Product Hunt 만 추천
- ❌ 자기홍보 강도 무시 (커뮤니티 ban 위험)
- ❌ AI 직역 마케팅 카피 (`human-voice-guard` 적용 필수)

## Related Skills

- `aarrr-growth-planner` — 큰 그림 프레임워크
- `growth-engine` — push/email 인프라
- `human-voice-guard` — 카피 어투 검사
- `aha-moment-optimizer` — Activation 최적화 (공유 동기)
- `store-launcher` — 스토어 런칭 (관련 사전 작업)
