---
name: accessibility-audit
description: >-
  Use when the user asks to check or fix accessibility — triggers "접근성",
  "a11y", "접근성 점검", "WCAG", "WCAG 검사", "스크린리더", "키보드 네비게이션",
  "색약 대비", "포커스 안 보임", "screen reader", "keyboard navigation",
  "axe", "lighthouse a11y", "alt text", "aria 점검". Runs axe-core (CLI or
  DevTools) plus Lighthouse accessibility, then validates WCAG 2.2 AA by hand —
  contrast 4.5:1 / 3:1, target size 24px (44px mobile), focus-visible, focus
  not obscured, prefers-reduced-motion, semantic HTML + ARIA landmarks/roles,
  keyboard nav and focus order, form label association, color-blind safety, and
  screen-reader sanity (NVDA / VoiceOver / TalkBack). Produces a WCAG 2.2 AA
  conformance report with violations grouped by severity and a prioritized
  fix list (file, selector, before→after). Complements design-review — invoke
  on an explicit a11y request or when automated audits alone fall short.
version: 0.1.0
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
compatibility: [claude-code]
author: simon-stack
---

# accessibility-audit

웹/하이브리드 UI를 **WCAG 2.2 Level AA** 기준으로 점검하고 우선순위 수정안을 낸다.
자동 도구(axe-core + Lighthouse)는 위반의 ~30~40%만 잡는다. 나머지는 키보드·SR·대비 수동 검증이 필수다.

## When to use / boundaries

쓸 때:
- "접근성 점검", "a11y 검사", "WCAG 맞춰줘", "스크린리더 테스트", "키보드로 안 돼요"
- 공공/B2B/금융/의료 서비스 (법적 준수: KWCAG 2.2, ADA, EN 301 549, European Accessibility Act 2025-06 시행)
- 출시 전 게이트, `design-review` 후 정밀 a11y 패스가 필요할 때

안 쓸 때 (다른 skill 로):
- 시각 일관성·spacing·AI slop → `design-review`
- 디자인 토큰·대비 비율 설계 자체 → `design-system-keeper`
- 순수 성능(LCP/CLS) → `nextjs-optimizer`

경계: 이 skill 은 **진단 + 수정 제안**까지. RN/Expo 네이티브 a11y(`accessibilityRole`, `accessibilityLabel`)는 §8 참고하되 깊은 구현은 `building-native-ui` 와 병행.

## 선행 체크 (precheck)

```bash
# 1) 프런트엔드 프로젝트인지 확인
test -f package.json && echo "WEB_OK" || echo "no package.json — confirm target (URL or static html)"

# 2) 점검 대상 URL 또는 서버 확인 (로컬이면 먼저 띄운다)
#    npm run dev / npm run web 로 서버 올린 뒤 그 URL 을 axe/lighthouse 에 넘긴다
curl -sI http://localhost:3000 | head -1 || echo "dev 서버 먼저 기동 필요"

# 3) Chrome/Edge 존재 확인 (axe-core/cli, lighthouse 둘 다 headless chrome 필요)
which google-chrome chrome chromium 2>/dev/null || echo "win: Edge/Chrome 경로 확인"
```

URL 이 없고 정적 HTML 만 있으면 `npx serve .` 로 임시 서버를 띄워 점검한다.

## Workflow

### 1. 자동 스캔 — axe-core (위반의 1차 그물)

axe-core/cli 는 axe-core 버전을 따라간다(현재 **4.11.x**, 비표준 버전관리). 글로벌 설치 없이 npx 권장.

```bash
# 단일 페이지, WCAG 2.2 AA 룰셋만, 결과 JSON 저장
npx @axe-core/cli http://localhost:3000 \
  --tags wcag2a,wcag2aa,wcag21a,wcag21aa,wcag22aa,best-practice \
  --save a11y-axe.json --exit

# 여러 페이지 한 번에
npx @axe-core/cli http://localhost:3000 http://localhost:3000/login \
  --tags wcag22aa --timer --save a11y-axe.json

# 로그인 뒤 화면처럼 늦게 그려지는 경우
npx @axe-core/cli http://localhost:3000/dashboard --load-delay 1500 --save a11y-axe.json
```

`--exit` 는 위반이 있으면 non-zero 로 종료 → CI 게이트로 쓸 수 있다. 결과 JSON 의
`violations[].impact`(critical/serious/moderate/minor)로 우선순위를 잡는다.

CI(GitHub Actions)용 jest+Playwright 통합이 필요하면:

```js
// a11y.spec.ts — Playwright + @axe-core/playwright
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('홈 a11y (WCAG 2.2 AA)', async ({ page }) => {
  await page.goto('/');
  const { violations } = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(violations, JSON.stringify(violations, null, 2)).toEqual([]);
});
```

### 2. 자동 스캔 — Lighthouse a11y (점수 + 보완 룰)

```bash
# 접근성 카테고리만, JSON+HTML 리포트
npx lighthouse http://localhost:3000 \
  --only-categories=accessibility \
  --output=json --output=html --output-path=./a11y-lh \
  --chrome-flags="--headless=new"
```

Lighthouse a11y 점수는 **참고용**(가중 합산이라 0.9여도 critical 위반 가능). 점수보다
axe `violations` 와 Lighthouse `audits` 의 `score: 0` 항목을 본다. 두 도구는 룰이 겹치되
서로 놓치는 게 있어 **둘 다** 돌린다.

### 3. WCAG 2.2 AA 수동 체크 — 자동이 못 잡는 핵심

| SC | 내용 | 자동? | 수동 검증 방법 |
|---|---|---|---|
| 1.4.3 대비(텍스트) | 4.5:1, 큰 텍스트 3:1 | 부분 | DevTools color picker / 대비 계산 |
| 1.4.11 비텍스트 대비 | UI/그래픽 3:1 | △ | 버튼 테두리·아이콘·차트 수동 |
| 2.1.1 키보드 | 모든 기능 키보드로 | ✗ | Tab/Shift+Tab/Enter/Space/Esc/방향키 |
| 2.4.3 포커스 순서 | 논리적 순서 | ✗ | Tab 으로 시각 흐름과 일치 확인 |
| 2.4.7 포커스 보임 | focus 표시 | △ | `:focus-visible` 링 육안 |
| **2.4.11 포커스 안 가림(신규 2.2)** | 고정헤더/모달에 포커스 안 가려짐 | ✗ | sticky/overlay 아래로 포커스 숨는지 |
| **2.5.8 타깃 크기 24px(신규 2.2)** | 인터랙티브 ≥24×24 CSS px | △ | 작은 아이콘 버튼 측정 |
| 3.3.2 라벨/지시 | 입력에 라벨 | △ | label↔input 연결 |
| **3.3.7 중복 입력 회피(신규 2.2)** | 이전 입력 재요구 금지 | ✗ | 멀티스텝 폼 흐름 |
| **3.3.8 접근가능 인증(신규 2.2)** | 인지테스트 없는 로그인 | ✗ | CAPTCHA·암기 요구 여부 |
| 1.4.13 호버/포커스 콘텐츠 | tooltip 닫힘/지속 | ✗ | hover 콘텐츠 Esc·hover 유지 |

> 2nd-B 등 모바일/터치 우선이면 타깃 ≥**44×44px**(Apple HIG)로 더 엄격히. WCAG 최저는 24px.

대비 빠른 측정(임의 두 색):

```bash
# 명도대비 계산 (요구치: 본문 4.5, 큰글/UI 3.0)
python - <<'PY'
def L(c):
    c=[int(c[i:i+2],16)/255 for i in (0,2,4)]
    c=[(x/12.92 if x<=.03928 else ((x+.055)/1.055)**2.4) for x in c]
    return .2126*c[0]+.7152*c[1]+.0722*c[2]
def ratio(a,b):
    a,b=L(a),L(b); hi,lo=max(a,b),min(a,b); return round((hi+.05)/(lo+.05),2)
print("text/bg:", ratio("767676","ffffff"))   # 4.54 → 4.5:1 통과 경계
print("accent :", ratio("6d28d9","ffffff"))
PY
```

### 4. 키보드 네비게이션 (직접 손으로)

```
Tab          → 모든 인터랙티브 요소에 순차 도달 (마우스 전용 없음)
Shift+Tab    → 역순 정상
Enter/Space  → 버튼·링크 활성화 (div onClick 만 있으면 실패)
Esc          → 모달/드롭다운/팝오버 닫힘 + 포커스 트리거로 복귀
방향키        → 라디오·탭·메뉴·슬라이더 내 이동
포커스 트랩    → 모달 열리면 포커스가 모달 안에 갇히고, 닫으면 원위치
```

흔한 실패: `<div onClick>` (키보드 도달·활성화 불가), `outline:none` 후 대체 없음,
모달 뒤 배경 포커스 유출, `tabindex` 양수 남용.

### 5. 시맨틱 HTML + ARIA 랜드마크

```bash
# 시맨틱 회피 안티패턴 스캔
grep -rnE '<div[^>]*onClick' src/ app/ components/ 2>/dev/null   # button 이어야
grep -rnE 'role="button"' src/ 2>/dev/null                       # 네이티브 <button> 우선
grep -rnE '<img(?![^>]*alt=)' src/ 2>/dev/null                   # alt 누락 의심
```

원칙: **ARIA 0순위 규칙 = 안 쓰는 게 최선**. 네이티브 요소(`<button> <nav> <main>
<header> <footer> <ul> <a href>`)면 role 불필요. 랜드마크 1세트만:

```html
<header> … </header>
<nav aria-label="주 메뉴"> … </nav>
<main id="main"> … </main>   <!-- 페이지당 단 1개 -->
<footer> … </footer>
<a href="#main" class="skip-link">본문 바로가기</a>  <!-- 첫 탭 정지점 -->
```

### 6. 폼 라벨 + 에러

before → after:

```html
<!-- BEFORE: placeholder 가 라벨 대용 (SR 미낭독, 입력 시 사라짐) -->
<input type="email" placeholder="이메일">

<!-- AFTER: 라벨 연결 + 에러 연결 + 필수 표시 -->
<label for="email">이메일</label>
<input id="email" type="email" autocomplete="email"
       required aria-required="true"
       aria-invalid="true" aria-describedby="email-err">
<p id="email-err" role="alert">유효한 이메일 형식이 아닙니다.</p>
```

체크: 모든 입력에 연결된 `<label for>` 또는 `aria-label`; 에러는 `aria-describedby`+
`role="alert"`; `autocomplete` 토큰; 그룹은 `<fieldset><legend>`.

### 7. 모션 / 색약 / 포커스 CSS

```css
/* 포커스 항상 보이게 — outline:none 단독 금지 */
:focus-visible { outline: 2px solid #6d28d9; outline-offset: 2px; }

/* prefers-reduced-motion 존중 (전정기관 장애) */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
    scroll-behavior: auto !important;
  }
}
```

색약 안전: 색만으로 의미 전달 금지(1.4.1) — 빨강/초록 상태에 아이콘·텍스트·패턴 병행.
Chrome DevTools → Rendering → "Emulate vision deficiencies"(protanopia/deuteranopia)로 육안 확인.

### 8. 스크린리더 점검 (실기기/실 SR 권장)

| 플랫폼 | SR | 기동 | 핵심 동작 |
|---|---|---|---|
| Windows | **NVDA**(무료) | Ctrl+Alt+N | ↓ 한 줄씩, H 제목, K 링크, F 폼, D 랜드마크, Tab |
| macOS/iOS | **VoiceOver** | ⌘+F5 / 측면3클릭 | VO+→, 로터로 제목/링크 탐색, 1탭 선택→2탭 활성 |
| Android | **TalkBack** | 음량2초 | 스와이프 →, 더블탭 활성, 읽기제어로 제목 이동 |

확인 항목: 제목만 ↓ 으로 들으면 문서 구조가 잡히나(H1→H2 위계), 이미지 alt 가 의미 전달하나
(장식은 빈 alt), 버튼/링크 이름이 명확한가("여기 클릭" 금지), 폼 라벨·에러가 낭독되나,
동적 변경(토스트·검색결과)이 `aria-live` 로 안내되나.

## 산출물 — WCAG 2.2 AA 리포트

심각도 그룹 + 우선순위 수정표. 결정용이므로 §13 규칙대로 **HTML 파일**로 낸다(`a11y-report.html`).

```
## 요약
- 대상: <URL>   기준: WCAG 2.2 AA + KWCAG 2.2
- axe: critical N / serious N / moderate N | Lighthouse a11y: 0.NN
- 결론: [통과 | 조건부 | 미달]

## Critical (즉시 — 기능 차단)
| # | SC | 위치(file:selector) | 문제 | before→after | 출처 |
|---|----|---------------------|------|--------------|------|
| 1 | 2.1.1 | LoginForm.tsx:<div onClick> | 키보드 활성화 불가 | <button>로 교체 | axe+수동 |

## Serious / Moderate / Minor (동일 표)
## 자동 미검출(수동 발견) — 포커스순서·SR 낭독·색약
## 권장 게이트: CI 에 axe --exit 추가, PR 마다 회귀 차단
```

## Anti-patterns

- 자동 점수만 보고 "통과" 선언 — axe/LH 는 30~40%만 잡음. 키보드·SR 수동 필수.
- `outline: none` 으로 포커스 링 제거하고 대체 없음 → 2.4.7 위반.
- placeholder 를 라벨로 사용 → 입력 시 사라지고 SR 누락.
- `<div onClick>`/`<span>` 클릭 → 키보드·SR 불가. `<button>`/`<a href>` 사용.
- `aria-label` 남발로 보이는 텍스트와 낭독 불일치(2.5.3 Label in Name 위반).
- 페이지에 `<h1>` 없음·위계 건너뜀(h2→h4)·`<main>` 다중·랜드마크 중복.
- 색만으로 상태 표현(빨강=에러)·`role="presentation"` 으로 의미 요소 숨김.
- ARIA 로 네이티브 요소 흉내(`role="button"` on div) — 네이티브가 항상 우위.

## 검증 (verify)

```bash
# 1) 수정 후 axe 재실행 — critical/serious 0 확인 (CI 게이트)
npx @axe-core/cli http://localhost:3000 --tags wcag22aa --save a11y-axe.json --exit
echo "exit=$?  (0 이면 위반 없음)"

# 2) Lighthouse a11y 재측정 — 점수 상승 확인
npx lighthouse http://localhost:3000 --only-categories=accessibility \
  --output=json --output-path=./a11y-lh.json --chrome-flags="--headless=new"

# 3) 수동 게이트 (사람이 직접, 자동 불가)
#    - 마우스 뽑고 Tab 만으로 핵심 플로우 1회 완주 가능?
#    - NVDA/VoiceOver 로 폼 1개 제출까지 낭독으로 완료 가능?
#    - DevTools 색각이상 에뮬에서 상태 구분 가능?
```

수동 3종이 모두 통과해야 "WCAG 2.2 AA 조건부 통과 → 통과"로 격상한다. axe `--exit` 0 은
필요조건이지 충분조건이 아니다.

## 참고 (current)

- WCAG 2.2 권고안: https://www.w3.org/TR/WCAG22/ (2.2 신규 AA: 2.4.11, 2.4.13, 2.5.8, 3.3.7, 3.3.8)
- @axe-core/cli: https://www.npmjs.com/package/@axe-core/cli (4.11.x)
- 라이브러리 최신 API·룰셋은 Context7 `resolve-library-id` → `query-docs` 로 재확인.
