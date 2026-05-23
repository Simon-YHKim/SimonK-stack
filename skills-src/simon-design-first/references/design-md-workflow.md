# DESIGN.md 워크플로우 + AI 디자인 레퍼런스 (Jeongmin Lee 2026 큐레이션)

> *2026-05-25 통합* — LinkedIn Jeongmin Lee (jyoung105) 두 게시물 통합 본. simon-design-first 스킬의 *레퍼런스 단계* 강화.

---

## Part 1 — DESIGN.md 워크플로우 (6단계)

`DESIGN.md` = **YAML design token + markdown 본문**. 코드와 같은 위치 (`/DESIGN.md`) — version control + AI 호출 가능 + 검증 가능.

### YAML token 표준

```yaml
---
tokens:
  colors:
    primary: "#0f172a"
    accent: "#7c3aed"
    text: "#e2e8f0"
    bg: "#0a0d14"     # tinted neutral, NOT pure black
  typography:
    headline: "Pretendard Bold 32px"
    body: "Pretendard Regular 14px"
    mono: "JetBrains Mono 13px"
  spacing:
    base: 4
    scale: [4, 8, 16, 24, 32, 48, 64]
  radius: [0, 4, 8, 16]
  shadow:
    sm: "0 1px 2px rgba(0,0,0,0.04)"
    md: "0 4px 12px rgba(0,0,0,0.08)"
---
# 디자인 근거

## 톤
[누가 볼 사이트 + 목적 + 어느 레퍼런스 채택]

## Anti-pattern (이 프로젝트에서 금지)
- Inter 폰트 사용 X (Pretendard)
- pure black X (tinted neutral)
- 4색 이상 multi-color X
```

### 6단계 흐름

| # | 단계 | 도구 | 비용 |
|---|---|---|---|
| **1** | DESIGN.md 정의 | 수동 작성 (YAML + markdown) | 무료 |
| **2** | **자동 추출** (URL → DESIGN.md) | AI에게 *"이 사이트 [URL]의 DESIGN.md 추출"* 요청 | LLM 토큰 |
| **3** | **레퍼런스 확보** | styles.refero.design / getdesign.md | 무료 |
| **4** | **MCP 리서치** | Lazyweb (25만+ 앱 스크린) / Mobbin | 무료/유료 |
| **5** | **시각 시안 검증** (코드 전) | taste-skill imagegen-frontend-web | LLM |
| **6** | **AI 슬롭 검수** (코드 후) | impeccable.style (24 패턴 자동 탐지) | 무료 |

### simon-design-first 매핑

| 본 skill Step | DESIGN.md 단계 |
|---|---|
| Step 1 진단 | 1. DESIGN.md 정의 (사용자 답변 → YAML 초안) |
| Step 2 레퍼런스 | 3. 레퍼런스 확보 + 4. MCP 리서치 |
| Step 3 폰트 선택 | 1. typography token 확정 |
| Step 3.5 AI Trope Detection | 6. AI 슬롭 검수 (impeccable.style 자동화 가능) |
| Step 4 사용자 방향 확정 | 5. 시각 시안 검증 (선택) |
| Step 5 하위 skill 위임 | 코드 작성 → 다시 6 검수 cycle |

---

## Part 2 — AI 디자인 10 레퍼런스 (Jeongmin Lee 큐레이션)

simon-design-first **Step 2 레퍼런스 추천**에 추가 가능한 자료 카탈로그.

### 설계·시스템 (3)

| 사이트 | URL | 가치 |
|---|---|---|
| **Refero Styles** | https://styles.refero.design | AI 에이전트용 DESIGN.md 추출 (URL → token) |
| **open-design** | github 검색 "open-design" | Claude Design 오픈소스 대안, 로컬 + CLI |
| **Montage Design System** | (원티드랩 공개) | 한국 제품 디자인 시스템 사례 |

### 컴포넌트·애니메이션 (3)

| 사이트 | URL | 가치 |
|---|---|---|
| **21st.dev** | https://21st.dev | AI 에이전트 호환 UI 컴포넌트 마켓 |
| **transitions.dev** | https://transitions.dev | 웹/React 트랜지션 CSS (복붙 즉시 적용) |
| **diagram-design** | (lnkd.in 검색) | 13가지 에디토리얼 다이어그램 (HTML+SVG) |

### 코드 변환 (1)

| 사이트 | URL | 가치 |
|---|---|---|
| **Pencil** | https://pencil.dev | IDE 캔버스 → 코드 즉시 변환 |

### 영감·레퍼런스 (3)

| 사이트 | URL | 가치 |
|---|---|---|
| **Font of Web** | https://fontofweb.com | AI 기반 웹 폰트/디자인 영감 피드 |
| **Logo System** | https://logosystem.co | 1,000+ 로고 라이브러리 |
| **UXSnaps** | https://uxsnaps.com | 실제 앱 UI/UX 분석 (무료) |

### 한국 프로젝트 — 우선 추천 (5)

본 skill의 한국 컨텍스트 + Pretendard default에 호환:

1. **UXSnaps** — 동종 한국 앱 UI 분석 (헤이/마인드카페 등)
2. **Refero Styles** — AI 에이전트 호환 DESIGN.md
3. **Montage** — 원티드랩 한국 사례
4. **transitions.dev** — 즉시 적용 가능
5. **Pencil** — 작업 가속

---

## Part 3 — Step 2 레퍼런스 추천 갱신 권장

### 탐색용 사이트 (기존)

- https://dribbble.com
- https://www.awwwards.com
- https://www.lapa.ninja
- https://21st.dev (← 이미 있음)

### 신규 추가 (5)

- https://uxsnaps.com (실제 앱 분석)
- https://styles.refero.design (DESIGN.md 추출)
- https://transitions.dev (CSS 트랜지션)
- https://pencil.dev (캔버스 → 코드)
- https://fontofweb.com (폰트 영감)

---

## Part 4 — impeccable.style 자동 검수 통합

본 skill의 **AI Slop 방지 3원칙** + **Step 3.5 AI Trope Detection**에 자동화 옵션:

```
사용자: "이 사이트 [URL]에 AI slop 있는지 점검해줘"
LLM (이 skill 호출): impeccable.style에 URL 제출 → 24 패턴 자동 탐지
→ 결과: { "ai_slop_score": 0.23, "detected": ["Inter font", "pure black bg"], "fixes": [...] }
```

→ 코드 작성 후 *자동 retro check* 가능.

---

## 출처

- LinkedIn: [Jeongmin Lee - DESIGN.md 워크플로우](https://kr.linkedin.com/posts/jyoung105_디자인-킬러-designmd-activity-7457313919489974272)
- LinkedIn: [Jeongmin Lee - AI 디자인 10 레퍼런스](https://kr.linkedin.com/posts/jyoung105_제가-좋아하는-ai-디자인-관련-레퍼런스를-모두-모았습니다-activity-7459140357981868032)
- SimonKWiki:
  - `wiki/concepts/design-md-workflow.md`
  - `wiki/concepts/ai-design-references.md`
