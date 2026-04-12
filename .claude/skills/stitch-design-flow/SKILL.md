---
name: stitch-design-flow
description: Google Stitch 웹 UI용 프롬프트 생성기. DESIGN.md를 읽고 3개 시안 프롬프트를 출력한다. Prompt generator for Google Stitch (stitch.withgoogle.com) — produces 3 mockup prompts from DESIGN.md for manual paste-in. 트리거 키워드 — 디자인 시안, UI 목업, Stitch, wireframe, 와이어프레임, UI 초안, mockup, 디자인 프롬프트.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon
---

# Stitch Design Flow

Google Stitch(stitch.withgoogle.com) 에 붙여넣을 프롬프트를 생성하는 텍스트 워크플로. **MCP 없음** — 사용자가 Stitch 웹 UI 에서 수동으로 프롬프트를 실행한다.

## When to use

- `app-dev-orchestrator` 단계 5
- `DESIGN.md` 가 확정된 후 첫 시안 생성
- 디자인 방향 비교가 필요할 때

## Workflow

### 1. DESIGN.md 읽기

```bash
test -f DESIGN.md && cat DESIGN.md || echo "DESIGN.md 없음 — /design-consultation 먼저"
```

없으면 `/design-consultation` 실행 요청.

### 2. 브랜드 요소 추출

DESIGN.md 에서 다음을 파싱:
- 제품명·한 줄 설명
- 타깃 사용자
- 톤 (modern / playful / minimal / editorial / brutalist / glassmorphism / neumorphic)
- 컬러 팔레트 (primary / secondary / accent / neutral)
- 타이포 (display / body / mono)
- 핵심 화면 3개 (예: 랜딩·대시보드·상세)

### 3. 프롬프트 3종 생성

각 시안은 **같은 화면**을 다른 방향으로:

**시안 A — Safe/Convention**: 업계 관용, 검증된 패턴
**시안 B — Bold/Differentiator**: 차별화, 강한 개성
**시안 C — Wild/Experimental**: 실험적, 하이 리스크 하이 리워드

프롬프트 템플릿:
```
Design a {화면 이름} for {제품명}, {한 줄 설명}.

Target users: {타깃}
Tone: {톤 A / B / C 변형}
Primary color: {hex}
Secondary color: {hex}
Typography: {display font} for headings, {body font} for body

Key elements to include:
- {요소 1}
- {요소 2}
- {요소 3}

Constraints:
- Mobile-first, 375px viewport
- WCAG AA contrast
- Korean + English copy (한/영 병기)

Style reference: {A: Stripe/Linear / B: Figma/Notion / C: Arc/Raycast}
```

### 4. 출력

`docs/design/stitch-prompts-<YYYY-MM-DD>.md` 에 3개 프롬프트를 저장하고, 사용자에게 출력.

```
[시안 A — Safe]
<프롬프트 전문>

[시안 B — Bold]
<프롬프트 전문>

[시안 C — Wild]
<프롬프트 전문>
```

### 5. 사용자 안내

> 위 3개 프롬프트를 각각 https://stitch.withgoogle.com 에 붙여넣어 이미지를 생성하고,
> 결과물을 `docs/design/stitch-output-A.png` (B/C) 로 저장해주세요.
> 완료 후 `/design-shotgun` 을 실행하면 변형 탐색으로 이어집니다.

### 6. 다음 단계 연결

사용자가 이미지를 저장한 뒤:
- `/design-shotgun` — 변형 탐색
- `/design-review` — 시각 QA
- `/design-html` — production HTML/CSS 변환

## Checklist

- [ ] DESIGN.md 존재 확인 (없으면 `/design-consultation` 먼저)
- [ ] 브랜드 요소 6개 파싱 (제품명·타깃·톤·컬러·폰트·화면)
- [ ] A/B/C 3개 변형 생성
- [ ] 각 프롬프트 한/영 병기 제약 포함
- [ ] `docs/design/stitch-prompts-<date>.md` 저장
- [ ] 사용자에게 수동 실행 가이드 제공

## Anti-patterns

- ❌ DESIGN.md 없이 프롬프트 생성 (근거 없는 디자인)
- ❌ 3개 시안이 비슷함 (탐색 가치 없음) — A/B/C 명확한 방향 차이 필수
- ❌ Stitch API 키 요청 또는 하드코딩 (MCP 없음. 수동 웹 UI 만 사용)
- ❌ 결과 저장 경로 미지정
- ❌ 한국어 서비스인데 영어 일색 프롬프트

## Related skills

- `/design-consultation` — DESIGN.md 생성 (선행 필수)
- `/design-shotgun` — 변형 탐색 (후속)
- `/design-review` — 시각 QA
- `/design-html` — HTML/CSS 변환
- `app-dev-orchestrator` — 단계 5
