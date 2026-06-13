---
name: i18n-localizer
description: >-
  Use when the user asks to internationalize or localize an app — triggers
  "다국어 지원", "국제화", "번역 붙여줘", "i18n 세팅", "l10n", "RTL 지원",
  "로케일별 포맷", "여러 나라 지원", "아랍어 미러링", "internationalization",
  "localization", "translation workflow", "add multiple languages",
  "locale routing", "right-to-left". Produces a framework i18n setup
  (next-intl v4 / react-i18next / expo-localization with real code), ICU
  message format for plurals·gender·select, RTL via CSS logical properties +
  dir attribute + a mirroring checklist (Arabic/Hebrew), locale-aware Intl.*
  formatting (date·number·currency), a translation-file structure with key
  naming rules, and a per-locale QA checklist (DE/FI overflow, CJK line-break,
  pseudo-localization). Wires in as a stage of app-dev-orchestrator. Do NOT use
  for one-off string translation — this is the full i18n/l10n infrastructure.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebSearch
version: 0.1.0
compatibility: [claude-code]
author: simon-stack
---

# i18n-localizer

다국어(i18n) + 현지화(l10n) 인프라를 실제 코드로 구축하고, 로케일별 QA 체크리스트를 산출한다.

## When to use / boundaries

**쓸 때**
- 앱을 2개국어 이상 지원해야 할 때 ("여러 나라 지원", "다국어")
- RTL(아랍어·히브리어) 레이아웃이 필요할 때
- 날짜·숫자·통화를 로케일별로 포맷해야 할 때
- `app-dev-orchestrator` 단계 15.5 diversity-gate(D-16)에서 호출될 때

**안 쓸 때 (다른 곳으로)**
- 문자열 1~2개 단발 번역 → 그냥 인라인 처리
- 결제 규제·통화 정산 → `global-payment-planner`
- 디자인 토큰·폰트 일관성 → `design-system-keeper`
- 번역 *문체*·카피 품질 → 사람 번역가/`human-voice-guard`

## 선행 체크 (precheck)

```bash
# 어떤 스택인지부터 확정 — 잘못된 라이브러리 설치 방지
test -f package.json || { echo "no package.json — 스택부터 정하라"; }
grep -q '"next"' package.json 2>/dev/null   && echo "STACK=next"
grep -q '"expo"' package.json 2>/dev/null   && echo "STACK=expo"
grep -qE '"react"' package.json 2>/dev/null && ! grep -q '"next"' package.json && echo "STACK=react-spa"
# 이미 i18n 깔려 있나? 중복 설치 금지
grep -qE '"(next-intl|react-i18next|i18next|expo-localization)"' package.json 2>/dev/null \
  && echo "WARN: i18n lib already present — 기존 설정 먼저 Read"
```

## 1. 라이브러리 선택

| 스택 | 라이브러리 | 이유 |
|---|---|---|
| **Next.js App Router** (13+/16) | `next-intl` v4 | App Router·RSC·라우팅·타입세이프 네이티브 |
| **Next.js Pages Router** | `next-i18next` | Pages 라우터 전용 래퍼 |
| **React SPA** (Vite/CRA) | `react-i18next` + `i18next` | 사실상 표준, 6M+ weekly DL |
| **React Native / Expo** | `react-i18next` + `expo-localization` | `getLocales()`로 기기 언어 감지 |
| **ICU 메시지(복수형/성별)** | `+ i18next-icu` | i18next 스택에 ICU 파서 추가 |

> 기준: SPA·RN 은 `react-i18next` 단일 스택으로 통일하면 번역 파일·키 컨벤션을 공유할 수 있다.

## 2. 프레임워크 셋업 (실제 코드)

### 2-A. next-intl v4 (App Router)

```bash
npm install next-intl
```

```ts
// src/i18n/routing.ts
import { defineRouting } from 'next-intl/routing';

export const routing = defineRouting({
  locales: ['en', 'ko', 'ar', 'de'],
  defaultLocale: 'en',
  localePrefix: 'as-needed', // 기본 로케일은 prefix 생략
});
```

```ts
// src/proxy.ts  (v4: middleware → proxy.ts 로 명칭 변경)
import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';
export default createMiddleware(routing);
export const config = {
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)'],
};
```

```ts
// src/i18n/request.ts — 서버에서 메시지 로드
import { getRequestConfig } from 'next-intl/server';
import { routing } from './routing';

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;
  if (!locale || !routing.locales.includes(locale as any)) {
    locale = routing.defaultLocale;
  }
  return { locale, messages: (await import(`../../messages/${locale}.json`)).default };
});
```

```tsx
// app/[locale]/layout.tsx — dir 속성은 RTL 의 핵심
import { NextIntlClientProvider } from 'next-intl';
import { setRequestLocale } from 'next-intl/server';

const RTL = new Set(['ar', 'he', 'fa', 'ur']);
export default async function LocaleLayout({ children, params }) {
  const { locale } = await params;
  setRequestLocale(locale); // 정적 생성(SSG) 가능하게
  return (
    <html lang={locale} dir={RTL.has(locale) ? 'rtl' : 'ltr'}>
      <body><NextIntlClientProvider>{children}</NextIntlClientProvider></body>
    </html>
  );
}
```

```tsx
// 사용처 — 서버/클라이언트 동일 훅
'use client';
import { useTranslations } from 'next-intl';
export function Greeting() {
  const t = useTranslations('home');
  return <h1>{t('title')}</h1>;
}
```

### 2-B. react-i18next (React SPA)

```bash
npm install i18next react-i18next i18next-browser-languagedetector i18next-icu
```

```ts
// src/i18n.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import ICU from 'i18next-icu';
import en from './locales/en/common.json';
import ko from './locales/ko/common.json';

i18n
  .use(ICU)                 // ICU plural/select 파서
  .use(LanguageDetector)    // navigator.language / querystring / localStorage
  .use(initReactI18next)
  .init({
    resources: { en: { common: en }, ko: { common: ko } },
    fallbackLng: 'en',
    defaultNS: 'common',
    interpolation: { escapeValue: false }, // React 가 XSS 방어하므로 끔
  });
export default i18n;
```

```tsx
import { useTranslation } from 'react-i18next';
function Cart() {
  const { t } = useTranslation();
  return <p>{t('cart.items', { count: 3 })}</p>; // ICU plural
}
```

### 2-C. expo-localization (React Native / Expo)

```bash
npx expo install expo-localization
npm install i18next react-i18next i18next-icu
```

```ts
// src/i18n.ts (RN)
import { getLocales } from 'expo-localization';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import ICU from 'i18next-icu';
import en from './locales/en.json';
import ko from './locales/ko.json';

const device = getLocales()[0]?.languageCode ?? 'en'; // 항상 [0] = 1순위
i18n.use(ICU).use(initReactI18next).init({
  resources: { en: { translation: en }, ko: { translation: ko } },
  lng: device,
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});
export default i18n;
```

```ts
// RTL 강제 + 앱 재시작 (RN 은 dir 속성이 없으므로 I18nManager 사용)
import { I18nManager } from 'react-native';
import * as Updates from 'expo-updates';
const isRTL = ['ar', 'he', 'fa', 'ur'].includes(device);
if (I18nManager.isRTL !== isRTL) {
  I18nManager.forceRTL(isRTL);
  Updates.reloadAsync(); // 미러링은 reload 후 적용됨
}
```

## 3. ICU Message Format (복수형·성별·select)

`{ }` 안에 변수, `plural`/`select`/`selectordinal` 로 분기. 영어 != 한국어 != 아랍어 복수 규칙이라 절대 `if(count===1)` 하드코딩 금지.

```json
{
  "cart": {
    "items": "{count, plural, =0 {장바구니가 비었습니다} one {# 개 담김} other {# 개 담김}}"
  },
  "invite": {
    "msg": "{gender, select, male {그가} female {그녀가} other {그들이}} 초대했습니다"
  },
  "rank": "{place, selectordinal, one {#st} two {#nd} few {#rd} other {#th}} place"
}
```

- 아랍어는 `zero/one/two/few/many/other` **6범주**, 한국어는 `other` 1범주 → CLDR plural rules 가 알아서 처리. 번역가에게 빈 범주는 비워두게 한다.
- `#` 은 숫자 자리. 천단위 구분은 `{count, number}` 로 ICU 에 맡긴다.
- next-intl 은 ICU 가 기본 내장, i18next 는 `i18next-icu` 필요.

## 4. 로케일별 Intl.* 포맷 (날짜·숫자·통화)

직접 문자열 조립 금지 → `Intl.*` 를 로케일로 호출. (next-intl 은 `useFormatter` 가 래핑.)

```ts
const n = new Intl.NumberFormat('de-DE').format(1234567.89); // "1.234.567,89"
const cur = new Intl.NumberFormat('ja-JP', {
  style: 'currency', currency: 'JPY',
}).format(2980); // "￥2,980" — 엔은 소수 0자리 자동
const date = new Intl.DateTimeFormat('ar-EG', { dateStyle: 'long' })
  .format(new Date()); // 아랍어 월·동방 아라비아 숫자
const rel = new Intl.RelativeTimeFormat('ko', { numeric: 'auto' })
  .format(-1, 'day'); // "어제"
```

| 함정 | 잘못 | 맞게 |
|---|---|---|
| 통화 소수자리 | `${n}.00` 고정 | `currency` 옵션이 KRW/JPY는 0자리 |
| 천단위 구분 | `,` 하드코딩 | DE는 `.`, FR은 공백 |
| 날짜 순서 | `MM/DD/YYYY` 고정 | `dateStyle` 로 로케일 위임 |
| 통화 코드 | 로케일에서 추론 | 통화는 **데이터**, 로케일과 분리해 명시 |

## 5. 번역 파일 구조 + 키 네이밍

```
messages/                 # next-intl (locale당 단일 파일)
  en.json   ko.json   ar.json
locales/                  # i18next (namespace 분할)
  en/{common,auth,settings}.json
  ko/{common,auth,settings}.json
```

키 네이밍 규칙:
- **계층 = 화면/도메인**: `cart.empty.title` (영어 문장 자체를 키로 쓰지 말 것 — 문장 바뀌면 키 깨짐)
- **재사용 액션은 `common`** 네임스페이스: `common.save`, `common.cancel`
- **변수는 ICU 플레이스홀더**: `welcome: "{name}님 환영합니다"`
- 절대 금지: 키에 번역 텍스트 섞기, locale별 키 개수 불일치(누락 = 폴백 노출)

```bash
# 키 누락 점검 — 기준(en) 대비 다른 로케일 키 diff
node -e "const a=require('./messages/en.json'),b=require('./messages/ko.json');
const flat=(o,p='')=>Object.entries(o).flatMap(([k,v])=>typeof v==='object'?flat(v,p+k+'.'):[p+k]);
const ka=new Set(flat(a)),kb=new Set(flat(b));
console.log('ko 누락:',[...ka].filter(k=>!kb.has(k)));
console.log('ko 잉여:',[...kb].filter(k=>!ka.has(k)));"
```

## 6. RTL (아랍어·히브리어) 미러링 체크리스트

CSS 는 `left/right` 대신 **logical properties** 로 작성하면 LTR/RTL 자동 대칭.

```css
/* ❌ 물리적 속성 — RTL 에서 안 뒤집힘 */
.card { margin-left: 16px; text-align: left; border-left: 2px solid; }
/* ✅ 논리적 속성 — dir=rtl 에서 자동 미러 */
.card { margin-inline-start: 16px; text-align: start; border-inline-start: 2px solid; }
```

미러링 QA 체크리스트 (`<html dir="rtl">` 또는 `I18nManager.forceRTL` 적용 후):
- [ ] `margin/padding-left|right` → `*-inline-start|end` 전환
- [ ] `text-align:left|right` → `start|end`
- [ ] `float`, `position:left` → 논리값 또는 `[dir=rtl]` 오버라이드
- [ ] 방향성 아이콘(뒤로가기 `←`, chevron, send)은 `transform: scaleX(-1)` 로 뒤집기
- [ ] 방향성 **아닌** 아이콘(로고·재생▶·체크)은 **뒤집지 말 것**
- [ ] 숫자·코드·전화번호·URL 은 LTR 유지 (`<bdi>` 또는 `direction:ltr` 격리)
- [ ] 슬라이더·프로그레스·캐러셀 진행 방향 반전 확인
- [ ] 폰트가 아랍어/히브리어 글리프 포함하는지 (Pretendard 는 미포함 → Noto Sans Arabic 폴백)

## 7. 페르소나 교차 QA — 로케일별 체크리스트 (산출물)

각 로케일을 첫 실행 + 핵심 루프로 걸으며 막힘·깨짐·이탈 지점 기록.

| 검사 | 대상 로케일 | 무엇을 본다 |
|---|---|---|
| **문자열 오버플로** | DE, FI, RU | 독일어/핀란드어는 영어 대비 +30~40% 길다 → 버튼·탭 줄바꿈·잘림 |
| **CJK 줄바꿈** | ko, ja, zh | 단어 경계 없음 → `word-break:keep-all`(ko) / `auto-phrase`, 어절 중간 끊김 |
| **RTL 미러** | ar, he | §6 체크리스트 전체 |
| **복수형** | ar, ru, pl | CLDR 6범주 다 채워졌나, `#` 위치 |
| **폰트 글리프** | ar, th, hi | 누락 글리프 □(tofu) 박스 안 뜨는지 |
| **하드코딩 잔존** | 전체 | 코드에 직접 박힌 한국어/영어 리터럴 |

**Pseudo-localization** — 번역 전에 누락·오버플로를 자동 노출:

```bash
# en.json 값을 액센트+30% 확장으로 변환 → 화면에 안 깨진 문자열·잘린 영역 즉시 발견
node -e "const m=require('./messages/en.json');
const ps=s=>'⟦'+[...s].map(c=>({a:'á',e:'é',i:'í',o:'ó',u:'ú'}[c]||c)).join('')+'··⟧';
const walk=o=>Object.fromEntries(Object.entries(o).map(([k,v])=>[k,typeof v==='string'?ps(v):walk(v)]));
require('fs').writeFileSync('./messages/en-XA.json',JSON.stringify(walk(m),null,2));"
# routing.ts locales 에 'en-XA' 임시 추가 후 전 화면 순회
```

하드코딩 문자열 스캔:

```bash
# JSX/TS 안의 한글 리터럴 (번역 안 빠진 것) 탐지
grep -rnP "[\xea\xb0-\xed\x9e]" src/ app/ --include=*.tsx --include=*.ts | grep -v "i18n\|locales\|messages"
```

## 8. 검증 (verification)

```bash
# 1) 빌드/타입 — next-intl 은 타입세이프, 누락 키 컴파일 에러
npm run build 2>&1 | tail -20
# 2) 로케일 라우트 응답 (next-intl)
curl -sI http://localhost:3000/ar | grep -i "content-language\|location"
# 3) 모든 로케일 키 동수 확인 (5번 스크립트가 '누락: []' '잉여: []' 면 통과)
# 4) RTL 시각 확인 — /ar 접속해 dir=rtl + 레이아웃 미러 육안/스크린샷
# 5) Intl 포맷 스모크
node -e "console.log(new Intl.NumberFormat('de-DE',{style:'currency',currency:'EUR'}).format(1234.5))"
```

통과 기준: 빌드 0 에러 · 로케일별 키 동수 · RTL dir 적용 · pseudo-loc 에서 잘림 없음 · 하드코딩 스캔 0건.

## Anti-patterns (하지 말 것)

- **문장 자체를 키로 사용** (`t("Save your changes")`) — 카피 한 글자 바뀌면 모든 로케일 키 깨짐. 의미 기반 키만.
- **복수형 if 분기** (`count===1 ? "item" : "items"`) — 아랍어/러시아어 6범주 못 다룸. ICU plural 강제.
- **`left/right` CSS 하드코딩** — RTL 에서 안 뒤집힘. logical properties.
- **날짜·통화 문자열 직접 조립** (`${y}/${m}/${d}`, `$${n}`) — `Intl.*` 위임.
- **모든 아이콘 미러링** — 로고·재생·체크는 뒤집으면 안 됨. 방향성 아이콘만.
- **로케일에서 통화 추론** — `ko-KR`라고 KRW 가정 금지. 통화는 별도 데이터.
- **번역 파일 한 덩어리** (수천 키 단일 JSON) — namespace/route 단위 분할 + lazy load.
- **폰트 글리프 미검증** — Pretendard 로 아랍어 렌더 → tofu(□). 스크립트별 폴백 폰트 명시.

## app-dev-orchestrator 연동

이 skill 은 `app-dev-orchestrator` 단계 15.5 diversity-gate(D-16)에서 호출된다. 디자인·QA *이후*, ship 단계 *이전*에 배치:
1. 스택 감지(precheck) → 라이브러리 선택(1)
2. 프레임워크 셋업(2) — 라우팅·provider·dir
3. 번역 파일 구조 확정(5) — 키 네이밍 합의
4. RTL 대상이면 logical properties 마이그레이션(6)
5. ship 전 per-locale QA + pseudo-loc(7~8)
