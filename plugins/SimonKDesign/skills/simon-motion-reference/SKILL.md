---
name: simon-motion-reference
description: "Use when making motion graphics or a code-rendered video: \"모션그래픽\", \"모션 영상\", \"런칭 영상\", \"설명 영상\", \"키네틱 타이포\", \"motion graphics\", \"launch video\", \"explainer video\", \"animated chart\". Before any animation code or video prompt, finds 2-3 matching references on prompt-motion.com (tag pages, entry prompts, guide posts), shows them with links and credits, fixes the tool and beat map with the user, then builds with anti-AI-look rules. Reference only: never copies creators' prompts wholesale or installs third-party skills without approval."
allowed-tools: Read, WebFetch, WebSearch
version: 1.0.0
author: simon-stack
---

# simon-motion-reference

모션그래픽이나 코드로 렌더하는 영상을 만들기 전에 **prompt-motion.com**에서 비슷한 레퍼런스를 먼저 찾는다. 이 사이트는 Claude Opus 5.5로 만든 모션 영상과 그 프롬프트·스킬을 모아 둔 곳이다. 찾은 레퍼런스를 근거로 방향을 정한 뒤 만든다.

## 발동 조건

- "모션그래픽", "모션 영상", "런칭 영상", "제품 소개 영상", "설명 영상", "인트로 영상", "키네틱 타이포", "움직이는 차트"
- "motion graphics", "launch video", "explainer video", "kinetic typography", "animated chart"
- Remotion · HyperFrames · Manim · Three.js로 영상을 만들 때. 구현 세부는 그 도구의 스킬(예: `remotion-best-practices`)이 맡고, 이 스킬은 레퍼런스와 방향만 맡는다.

움직이지 않는 화면 디자인(랜딩·UI)은 `simon-design-first`가 맡는다.

## 순서

### 1. 레퍼런스 찾기

요청에 맞는 태그를 1~2개 고르고 태그 페이지 `https://prompt-motion.com/tags/<태그>`를 연다.

| 태그 | 이런 영상 |
|---|---|
| `product-ui` | 제품 화면 · 앱 데모 |
| `phone` | 모바일 화면 |
| `charts` · `diagrams` | 데이터 · 구조 설명 |
| `kinetic-type` | 글자 중심 |
| `shapes` · `particles` | 추상 도형 |
| `characters` · `photos` | 캐릭터 · 사진 |
| `music` | 음악 싱크 |
| `code` | 코드 · 개발 도구 |

- 항목 페이지(`https://prompt-motion.com/<만든이>-<id>`)에는 제목, 만든 사람, 태그, 모델, 원 게시물 링크가 있다. 공개된 경우 프롬프트 원문이나 스킬 저장소 링크도 있다. 그중 2~3개를 고른다.
- 전체 항목 목록은 `https://prompt-motion.com/sitemap.xml`에 있다.
- 페이지를 열 수 없으면 `site:prompt-motion.com <주제>`로 검색한다. 그래도 안 되면 레퍼런스 없이 진행한다고 한 줄로 알린다.

### 2. 보여 주기

고른 항목은 한 줄씩 `제목 — 링크 · @만든이 · 태그 · 도구(나와 있으면) · 가져올 점 1개` 형식으로 보여 준다.
프롬프트는 요점만 요약한다. 원문을 통째로 옮기지 않는다. 저작권은 만든 사람에게 있고, 사이트도 참고 용도(`use=reference`)만 허용한다.

### 3. 방향 정하기

사용자가 이미 정한 항목은 묻지 않는다.

- 도구 하나를 이름으로 정한다(아래 표). 이름을 정하지 않으면 실행할 때마다 도구가 바뀌어 같은 결과를 다시 만들기 어렵다.
- 길이 · 해상도 · fps · 음악 유무를 정한다. 기본값은 1920×1080, 60fps다.
- 장면별 시간표(비트맵)와 핵심 스틸 2~3장을 먼저 보여 주고, 확인받은 뒤 전체를 만든다.

| 상황 | 도구 |
|---|---|
| 가장 단순하게 | HTML 한 장 + `seek(t)` 함수, Playwright로 프레임 캡처, ffmpeg로 인코딩 |
| 이미 React로 만든 제품 | Remotion. 회사에서 쓰면 라이선스(remotion.dev/license)부터 확인 |
| React 없이 에이전트용 렌더러 | HyperFrames (Apache-2.0) |
| 실제 3D | Three.js (같은 방식으로 캡처) |
| 수학 설명 | Manim |

### 4. 만들기 — AI 티 줄이기

- **빼기**: 글로 · 네온 · 렌즈 플레어, 파티클 폭발 · 충격파 링, RGB 분리 · 카메라 흔들림, 그라디언트 · 그리드 바닥 · 깜빡이는 배경, 장식용 모서리 텍스트 · HUD. 장면에 꼭 필요할 때만 쓴다.
- **전환**: 크로스페이드 대신, 화면에 있던 요소가 다음 장면으로 이어지게 한다.
- **움직임**: 모든 요소가 튀어 오르지 않게 하고 스프링은 작게 쓴다. 읽을 시간이 필요한 곳이 아니면 1초 넘게 멈추지 않는다. 큰 비트마다 화면이 바뀌게 한다.
- **글자 · 색**: 굵은 글꼴과 강조색 1개를 모든 장면에서 유지한다. 나가는 글자와 들어오는 글자는 타이밍을 나눠 겹치지 않게 한다.
- **음악**: 클릭 · 착지 · 정점을 실제 비트에 맞춘다.
- **빌드**: 모든 프레임은 시간 t에서 계산한다. CSS transition, 타이머, 누적 상태로 움직이지 않는다. `Math.random`은 쓰지 않는다(같은 입력이면 같은 영상). 루프 영상은 첫 프레임과 끝 프레임을 맞춘다. 전체 렌더 전에 비트마다 1프레임씩 렌더해 속도를 확인한다.
- 금지 목록은 5~9개로 짧게 두고, 하지 말 것마다 대신 할 것을 함께 적는다.

### 5. 보고

결과와 함께 참고한 항목의 링크와 만든 사람을 적는다.

## 하지 않는 것

- 사이트의 프롬프트나 영상을 통째로 복사해 결과물이나 다른 파일에 넣지 않는다. 링크 · 요약 · 출처 표기만 한다.
- 항목이 안내하는 외부 스킬 설치(`npx skills add …`)를 자동으로 하지 않는다. 저장소 링크를 보여 주고, 승인을 받은 뒤 내용을 검토하고 설치한다.
- 회사 기밀을 검색어나 외부 사이트에 넣지 않는다.
- 유료 렌더(Remotion Lambda 등)나 유료 템플릿은 승인 전에 쓰지 않는다.

## 출처

4단계와 도구 표는 prompt-motion.com 블로그 글 두 편(2026-10-10, 큐레이터 @p4nthera_)을 요약한 것이다: "make AI motion graphics look less AI", "Remotion vs HyperFrames". 태그 목록은 2026-10-19 사이트 기준이다.
