---
name: design-system-keeper
description: "Use when the user wants to establish, persist, or enforce a design system across sessions—triggers \"디자인 시스템 만들어\", \"디자인 일관성 유지\", \"design drift 막아줘\", \"토큰 추출해줘\", \"design system\", \"design tokens\", \"audit my UI\", \"interface design\", \"keep the design consistent\". Picks one of 6 design directions, captures decisions (spacing/color/type/depth/motion tokens) into a persistent .design-system/system.md that auto-loads next session, EXTRACTS tokens from existing code, and AUDITS components against the system to flag drift. Folds in an anti-generic distinctiveness layer (intentional aesthetic, not maximalism) reconciled with project AI-slop rules. Different from simon-design-first (intake interview) and consistency-guard (data/config schema)."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# design-system-keeper

디자인 **시스템을 한 번 정하고 세션을 넘어 유지·강제**하는 skill. 한 번 고른 spacing·color·type·depth·motion 토큰을 `.design-system/system.md`에 박아두고, 다음 세션이 자동으로 로드하며, 기존 코드에서 토큰을 **추출(extract)**하고, 컴포넌트가 시스템에서 **이탈(drift)**했는지 **감사(audit)**한다.

> **차용·종합 출처**: ① Anthropic `frontend-design` skill(비-제네릭 distinctiveness·방향성·분위기) ② `Dammyjay93/interface-design` 플러그인(영속 system.md·6 방향성·audit/extract). 둘을 SimonKStack 네이티브로 통합하고 Simon의 anti-slop 규칙과 조화시킨 버전.

## 발동 조건

- "디자인 시스템 만들어/유지", "디자인 일관성", "design drift 막아줘", "토큰 추출", "UI audit"
- "design system", "design tokens", "audit my UI", "interface design", "keep design consistent"
- `/design-system-keeper`

## 파이프라인에서의 위치

```
simon-design-first(인테이크: 누구/목적/톤·레퍼런스·폰트 선택)
        │
        ▼
design-system-keeper  ← 방향 확정 → 토큰 codify → system.md 영속 → audit
        │
        ▼
design-html · vercel-react · building-native-ui (구현, 토큰 경유)
        │
        ▼
design-review (시각 QA)
```

- **simon-design-first**와 다름: 그건 코드 전 "방향 인테이크 인터뷰". 이 skill은 그 결정을 **토큰으로 굳히고 영속·감사**한다.
- **consistency-guard**와 다름: 그건 데이터/config/JSON-schema 일관성. 이 skill은 **시각 디자인 토큰** 일관성.
- **design-system-page**와 다름: 그건 1회성 브랜드북 카탈로그 페이지 생성. 이 skill은 **상시 유지되는 system.md + audit 루프**.

## 핵심 산출물: `.design-system/system.md`

프로젝트 루트에 `.design-system/system.md`를 만들고 유지한다. **이미 프로젝트에 권위 있는 디자인 SoT가 있으면(예: 2nd-B `DESIGN.md`) 그것을 정본으로 쓰고 이 파일은 만들지 않는다** — 중복 SoT 금지.

```markdown
# Design System — <project>
direction: <6 방향 중 1>
updated: <YYYY-MM-DD>

## Direction
<personality 한 줄 + 근거>

## Tokens
- spacing-base: 4px / scale: 4,8,12,16,24,32,48
- color: bg / surface / text / muted / + accent(1) [+ signal colors with fixed meaning]
- type: <display font> / <body font> / scale / line-height
- radius: input·button md(8) / card·modal lg(12) / chip sm(4) — never pill
- depth: <border vs shadow 전략>
- motion: state 200ms / press 80ms / no bounce·elastic

## Patterns
- button height, card padding, input height, focus ring …

## What we never do
<금지 목록 — anti-slop>
```

## 단계

### 1) Direction 선택 (6 방향)

용도에 맞는 방향 1개를 고른다(둘 이상 섞지 않는다 — 섞으면 무방향).

| Direction | 느낌 | 용도 |
|---|---|---|
| Precision & Density | 타이트·모노크롬·기술적 | 관리도구·어드민 |
| Warmth & Approachability | 여백 넉넉·부드러움 | 소비자 앱 |
| Sophistication & Trust | 차분·깊이 있는 레이어 | 엔터프라이즈 |
| Boldness & Clarity | 고대비·극적 | 데이터 대시보드 |
| Utility & Function | 절제된 밀도 | 개발자 도구 |
| Data & Analysis | 차트 최적화 | 분석·BI |

방향 미정이면 **simon-design-first**로 인테이크 먼저(누구·목적·톤). `references/direction-and-aesthetics.md`에 각 방향의 톤·distinctiveness 기법이 있다.

### 2) Distinctiveness 레이어 (제네릭 AI 디자인 탈피)

`frontend-design` 원칙: "Bold maximalism과 refined minimalism 둘 다 통한다 — 핵심은 강도가 아니라 **의도(intentionality)**." 제네릭 AI 티(흔한 폰트·보라-on-화이트 그라데이션·쿠키커터 레이아웃·맥락 없는 디자인)를 피한다.

- **타이포**: 흔한 기본 폰트 대신 **개성 있는 서체**. display/body 페어링으로 격을 올린다.
- **색**: dominant 1색 + 전략적 accent. 균등 분산보다 한 색이 지배.
- **공간**: 비대칭·겹침·그리드 깨기·의도적 여백 또는 밀도.
- **분위기**: 깊이(테두리/그림자/레이어/그레인)로 평면 탈피.
- **시그니처 모먼트 1개**: "이 디자인을 기억하게 만들 단 하나"를 정한다(스태거 등장 등).

### 3) ⚠️ 제약과의 조화 (최적화 — CRITICAL)

`frontend-design`의 "그라데이션·노이즈·극적 그림자·맥시멀리즘"은 **Simon 규칙·프로젝트 SoT와 충돌**할 수 있다. **충돌 시 프로젝트 규칙이 이긴다.**

- **글로벌 anti-slop(루트 CLAUDE.md)**: 색 3개 이내, 이모지·장식 금지, tinted-neutral(pure black/gray 금지), **금지 폰트 Inter**(한국어 Pretendard 기본), bounce/elastic 금지.
- **2nd-B `DESIGN.md`**: hex 리터럴 금지(`semantic.*` 토큰), gradient 전면 금지·glass/blur 금지·pill 금지, 폰트 NeoDunggeunmo, accent budget(primary 1 + 시그널 5, 한 화면 ≤3).
- **조화 원칙**: 제약 프로젝트에서 distinctiveness는 **그라데이션·맥시멀리즘이 아니라 타이포·구성·여백·시그니처 모먼트 1개**로 낸다. 맥시멀 분위기 기법(그라데이션/그레인/극적 그림자)은 **그런 제약이 없는 신규/외부 프로젝트에만** opt-in.

### 4) Extract (기존 코드 → 토큰)

기존 코드베이스가 있으면 토큰을 역추출한다.

```bash
# 색 리터럴·spacing·radius·font 사용 빈도 스캔
grep -rEo '#[0-9a-fA-F]{3,8}' src | sort | uniq -c | sort -rn   # 색 팔레트
grep -rEo '(padding|margin|gap)[^;]*[0-9]+px' src | sort | uniq -c | sort -rn  # spacing
grep -rEo 'borderRadius[^,]*[0-9]+' src | sort | uniq -c   # radius
```

가장 많이 쓰인 값을 토큰 후보로 system.md에 적재 → 이상치(one-off)는 정리 대상으로 표시.

### 5) Audit (코드 ↔ system.md drift 검사)

컴포넌트를 system.md 토큰과 대조해 이탈을 찾는다.

- hex 리터럴(토큰 미경유), 스케일 밖 spacing(예: `margin: 7px`), pill(`borderRadius: 9999`), 금지 폰트, accent budget 초과(한 화면 4색+), 그라데이션/glass(금지 프로젝트), em-dash·이모지 장식.
- 발견을 `[심각도] 파일:줄 — 위반 — 토큰 대체안` 으로 리포트. **자동 수정하지 않고 제안만**(design-review가 적용).
- 결과는 HTML 리포트로(다크·3색·무장식, 루트 CLAUDE.md §13).

### 6) 영속·자동로드

- 세션 시작 시 `.design-system/system.md`(또는 프로젝트 DESIGN.md)를 읽고 그 토큰을 따른다. "결정은 누적된다 — 한 번 고른 spacing 값이 패턴이 된다."
- 새 결정이 생기면 system.md를 갱신(append + updated 날짜). 우발적 drift가 아니라 **의도적 진화**로.

## 산출 체크리스트

- [ ] direction 1개 확정(섞지 않음)
- [ ] `.design-system/system.md` 생성/갱신 — 단 권위 SoT(DESIGN.md) 있으면 그걸 사용
- [ ] 토큰: spacing·color(≤3 + 시그널)·type·radius·depth·motion
- [ ] 프로젝트 anti-slop 규칙과 조화 확인(충돌 시 프로젝트 우선)
- [ ] 기존 코드 extract → 이상치 표시
- [ ] audit 리포트(HTML, 제안만)
- [ ] simon-design-first(인테이크)·design-review(QA)와 연결

## 안티패턴

- 6 방향을 섞기(무방향) · system.md와 DESIGN.md 이중 SoT · audit에서 자동 수정(제안만) · 제약 프로젝트에 그라데이션/맥시멀리즘 강행 · accent budget 무시(한 화면 4색+) · 토큰 없이 hex 리터럴 직접.

## 참조

- `references/direction-and-aesthetics.md` — 6 방향별 톤·토큰 프리셋 + distinctiveness 기법 상세.
