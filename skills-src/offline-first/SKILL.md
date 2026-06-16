---
name: offline-first
description: "Use when building for low-income, emerging-market (SEA/rural), or low-end-device users on metered, intermittent, slow networks — triggers \"오프라인\", \"offline-first\", \"저대역폭\", \"low bandwidth\", \"2G\", \"3G\", \"데이터 절약\", \"save-data\", \"약한 네트워크\", \"intermittent connection\", \"feature phone\", \"emerging market\", \"오프라인 우선\". Produces an offline-first architecture (service worker / Workbox 7 cache strategy or Expo SQLite + TanStack Query persist) plus optimistic UI + background sync, a payload-budget checklist (JS/image/initial-load targets per network class), Save-Data + adaptive-loading code, an image strategy (responsive AVIF/WebP, lazy), a low-end-device test matrix, and graceful-degradation rules. Writes config, code, and a budget table — does not silently degrade UX."
version: 0.1.0
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
author: simon-stack
compatibility: [claude-code]
---

# offline-first

저소득·신흥시장(SEA·농촌)·저사양 단말 사용자가 종량제(metered)·간헐적·느린 네트워크에서도 앱을 쓸 수 있게 만드는 skill. 캐시 전략, 낙관적 UI + 백그라운드 동기화, 페이로드 예산, Save-Data 적응 로딩, 이미지 전략, 저사양 테스트 매트릭스, graceful degradation 을 실제 코드/설정으로 산출한다.

## When to use / boundaries

쓸 때:
- "오프라인에서도 동작해야 함", "데이터 아껴야 함", "2G/3G 에서 너무 느림"
- SEA(인니·필리핀·베트남)·인도·아프리카·농촌 타깃, RAM 2~3GB · Android Go · feature-phone-ish 단말
- 종량제·선불 데이터 사용자(가격 민감 — 1MB 도 비용), 지하철·엘리베이터·시골 같은 간헐 연결

쓰지 말 것 (경계):
- 순수 고사양·고대역 전제 앱(사내 대시보드 등) → 일반 `nextjs-optimizer` / `building-native-ui` 로 충분
- 단말/플랫폼 미결정 → 먼저 `app-platform-selector`
- 결제 자체 → `payment-integrator` / `global-payment-planner` (이 skill 은 결제 화면의 오프라인 큐만 다룸)
- 측정 도구만 필요 → `analytics-integrator`

연계: 웹 PWA 는 `nextjs-optimizer`·`vercel-react` 와, RN 은 `building-native-ui` 와 같이 쓴다. CLAUDE.md UX 4원칙(자연스러움·직관성·정보위계·자산 일관성) + 페르소나 시뮬(저소득·고령·신흥시장)을 항상 교차 적용한다.

## 0. Precheck (현재 상태 진단)

작업 시작 전 무엇이 무거운지부터 측정한다. 추정 금지.

```bash
# 번들 크기 — Next.js
npx next build && du -sh .next/static/chunks 2>/dev/null

# 번들 분석 (web)
npx -y source-map-explorer 'dist/**/*.js' || ANALYZE=true npx next build

# RN/Expo 번들 크기
npx expo export --platform android && du -sh dist 2>/dev/null

# 이미지 무게 — 가장 큰 에셋 상위 20개
find . -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \) \
  -not -path '*/node_modules/*' -printf '%s %p\n' | sort -rn | head -20

# 서비스워커 존재 여부
ls -la public/sw.js public/service-worker.js 2>/dev/null || echo "no SW"
```

Lighthouse 를 모바일+throttle 로 돌려 baseline 을 박는다(검증 단계에서 재사용):

```bash
npx -y lighthouse https://localhost:3000 \
  --preset=desktop=false --form-factor=mobile \
  --throttling-method=simulate --only-categories=performance \
  --output=json --output-path=./lh-before.json --quiet
```

## 1. 네트워크 클래스 × 페이로드 예산

저사양·저대역에서 **체감 지표는 초기 페이로드와 메인스레드 JS**다. 네트워크 클래스별 예산을 먼저 고정하고 그 안에서 설계한다.

| 항목 | Slow-2G/2G 목표 | 3G 목표 | 4G+ 상한 | 측정 |
|---|---|---|---|---|
| 초기 HTML+critical CSS | ≤ 14KB(첫 RTT) | ≤ 30KB | ≤ 50KB | view-source / network |
| 초기 JS (gzip/br) | ≤ 50KB | ≤ 120KB | ≤ 170KB | bundle analyzer |
| 초기 이미지(LCP 1장) | ≤ 30KB | ≤ 80KB | ≤ 150KB | DevTools size |
| 초기 라우트 총합 | ≤ 100KB | ≤ 250KB | ≤ 500KB | network har |
| TTI (simulated) | ≤ 8s | ≤ 5s | ≤ 3s | Lighthouse |
| 폰트 | system stack 우선 | woff2 1개 ≤ 30KB, `swap` | 동일 | network |

규칙:
- 첫 화면은 **JS 없이도 의미를 보여준다**(SSR/SSG + progressive enhancement). JS 는 상호작용을 "추가"할 뿐.
- 라우트별 code-split, 무거운 위젯(지도·차트·에디터)은 dynamic import + 가시영역(IntersectionObserver) 진입 시 로드.
- 폰트는 신흥시장 기본 system-ui 스택. 커스텀 폰트는 한 weight, `font-display: swap`, subset.

```js
// next.config.js — 예산을 CI로 강제 (초과 시 빌드 실패)
module.exports = {
  experimental: { optimizePackageImports: ['lucide-react', 'date-fns'] },
  webpack(config) {
    config.performance = { hints: 'error', maxEntrypointSize: 170_000, maxAssetSize: 150_000 };
    return config;
  },
};
```

## 2. 캐시 전략 선택 (웹: Workbox 7)

전략은 데이터 성격으로 정한다. 하나로 통일하지 말 것.

| 리소스 | 전략 | 이유 |
|---|---|---|
| 앱 셸(HTML/JS/CSS 빌드 산출물) | Precache (`precacheAndRoute`) | 버전 고정, 즉시 오프라인 |
| API 읽기(목록·프로필) | StaleWhileRevalidate | 즉답 + 백그라운드 갱신 |
| API 쓰기(POST/PUT) | NetworkOnly + BackgroundSync | 오프라인 시 큐잉 후 재전송 |
| 이미지/아바타 | CacheFirst + 만료(maxEntries/maxAge) | 재다운로드 비용 제거 |
| 환율·재고 등 민감 데이터 | NetworkFirst(timeout) | 최신성 우선, 끊기면 캐시 폴백 |

```js
// service-worker.js — Workbox 7
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate, CacheFirst, NetworkFirst } from 'workbox-strategies';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';
import { ExpirationPlugin } from 'workbox-expiration';
import { BackgroundSyncPlugin } from 'workbox-background-sync';

precacheAndRoute(self.__WB_MANIFEST); // 앱 셸

registerRoute(({ url }) => url.pathname.startsWith('/api/feed'),
  new StaleWhileRevalidate({ cacheName: 'api-read' }));

registerRoute(({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'img',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 60, maxAgeSeconds: 30 * 24 * 3600, purgeOnQuotaError: true }),
    ],
  }));

// 오프라인 쓰기 → 큐잉 후 연결되면 자동 재전송 (최대 24h 보관)
const bgSync = new BackgroundSyncPlugin('mutations', { maxRetentionTime: 24 * 60 });
registerRoute(({ url, request }) =>
  url.pathname.startsWith('/api/') && request.method === 'POST',
  new NetworkFirst({ plugins: [bgSync] }), 'POST');
```

## 3. 모바일(Expo/RN) 오프라인 아키텍처

웹이 아니면 SW 대신 **로컬 DB + 동기화 엔진**을 쓴다. 멘탈 모델: Cache → Queue → DB → Sync.

| 규모 | 권장 스택 | 비고 |
|---|---|---|
| 가벼움(읽기 캐시 + 소수 mutation) | TanStack Query + `persistQueryClient` + MMKV | 가장 단순, 2nd-B 호환 |
| 중간(쿼리 가능한 오프라인 데이터) | expo-sqlite + TanStack Query | SQLite 직접 쿼리 |
| 무거움(대량 동기화·충돌 해결) | WatermelonDB + PowerSync/ElectricSQL | 본격 sync engine |

```ts
// TanStack Query — 오프라인 캐시 영속 + mutation 큐잉 (Expo)
import { MMKV } from 'react-native-mmkv';
import { QueryClient } from '@tanstack/react-query';
import { persistQueryClient } from '@tanstack/query-persist-client-core';

const storage = new MMKV();
export const queryClient = new QueryClient({
  defaultOptions: { queries: { networkMode: 'offlineFirst', gcTime: 1000 * 60 * 60 * 24, staleTime: 1000 * 60 } },
});
persistQueryClient({
  queryClient,
  persister: {
    persistClient: (c) => storage.set('rq', JSON.stringify(c)),
    restoreClient: () => { const v = storage.getString('rq'); return v ? JSON.parse(v) : undefined; },
    removeClient: () => storage.delete('rq'),
  },
  maxAge: 1000 * 60 * 60 * 24 * 7,
});
```

```ts
// 낙관적 mutation — 끊겨도 UI 즉시 반영, 연결 시 자동 flush + 충돌 롤백
const m = useMutation({
  mutationFn: postNote,
  networkMode: 'offlineFirst',
  onMutate: async (next) => {
    await queryClient.cancelQueries({ queryKey: ['notes'] });
    const prev = queryClient.getQueryData(['notes']);
    queryClient.setQueryData(['notes'], (o: Note[] = []) => [...o, { ...next, _pending: true }]);
    return { prev };
  },
  onError: (_e, _v, ctx) => queryClient.setQueryData(['notes'], ctx?.prev), // 롤백
  onSettled: () => queryClient.invalidateQueries({ queryKey: ['notes'] }),
});
```

## 4. Save-Data + 적응 로딩

NetworkInformation API(`navigator.connection`, `Save-Data`)는 **Chromium 한정**이라 반드시 feature-detect 하고, 없으면 보수적 기본값(데이터 절약 ON 가정)으로 폴백한다.

```ts
type NetHint = { saveData: boolean; effective: '4g'|'3g'|'2g'|'slow-2g' };
export function netHint(): NetHint {
  const c = (navigator as any).connection;
  if (!c) return { saveData: true, effective: '3g' }; // 미지원 → 보수적
  return { saveData: !!c.saveData, effective: c.effectiveType ?? '3g' };
}
// 사용: 자동재생·prefetch·고해상도 이미지를 절약 모드에서 끈다
const { saveData, effective } = netHint();
const allowHeavy = !saveData && effective === '4g';
```

```nginx
# 서버에서 Save-Data 헤더 존중 — 클라가 데이터절약이면 경량 변형 응답
# (Vercel/Cloudflare 는 Edge function 으로 동일 처리; Vary 로 캐시 분리)
map $http_save_data $img_quality { default "q_auto:good"; "~*on" "q_auto:low"; }
add_header Vary "Save-Data";
```

규칙: 절약 모드에서는 비디오 자동재생·이미지 캐러셀 자동슬라이드·과도한 prefetch·웹폰트 다운로드를 끄고, "탭하면 로드" 플레이스홀더로 대체한다.

## 5. 이미지 전략 (보통 페이로드의 60%+)

```html
<!-- 반응형 + 차세대 포맷 + lazy. AVIF→WebP→JPEG 폴백 -->
<picture>
  <source type="image/avif" srcset="hero-320.avif 320w, hero-640.avif 640w" sizes="100vw">
  <source type="image/webp" srcset="hero-320.webp 320w, hero-640.webp 640w" sizes="100vw">
  <img src="hero-320.jpg" width="640" height="360" loading="lazy" decoding="async"
       fetchpriority="low" alt="...">
</picture>
```

- LCP 이미지 1장만 `fetchpriority="high"` + preload, 나머지는 `loading="lazy"`.
- 항상 `width`/`height` 명시(CLS 0). blur/LQIP placeholder 로 체감 개선.
- Next.js 는 `next/image`(자동 AVIF/WebP·sizes), `images.formats: ['image/avif','image/webp']`.
- 변환: `npx @squoosh/cli --avif auto --webp auto src/*.jpg` 또는 sharp 빌드 스텝.
- 아이콘은 inline SVG(요청 0). 마스코트/일러스트는 SVG 통일(CLAUDE.md 자산 일관성).

## 6. Graceful degradation 규칙

- 모든 화면에 3상태: **온라인 / 동기화 대기 / 오프라인** 을 명시적 배너로 보여준다(조용히 실패 금지 = 불신 유발).
- mutation 은 낙관적 반영 + `pending` 뱃지. 영구 실패 시에만 사용자에게 재시도 노출.
- `navigator.onLine` + `online`/`offline` 이벤트로 상태 전환, RN 은 `@react-native-community/netinfo`.
- 핵심 루프(읽기·작성)는 오프라인에서 끝까지 동작. 비핵심(추천·분석)만 연결 시 보강.
- 타임아웃·재시도는 지수 백오프 + jitter, 사용자 토스트는 1회만.

## 7. 저사양 단말 테스트 매트릭스

| 축 | 하한 시나리오 | 검증 방법 |
|---|---|---|
| CPU | 4~6x slowdown | DevTools Performance → CPU throttle |
| 네트워크 | Slow 3G / offline 토글 | DevTools Network throttle / 비행기모드 |
| RAM | Android Go(2GB) | 실기기 또는 `emulator -memory 2048` |
| 화면 | 360x640, dpr 2 | DevTools device toolbar |
| 데이터 | Save-Data ON | `--enable-features` / 헤더 주입 |
| 입력 | 터치타깃 ≥44px, 글자 ≥16px | 수동 + axe |

```bash
# 저속/오프라인 회귀를 CI로 (Lighthouse Slow 4G 프리셋)
npx -y lighthouse $URL --form-factor=mobile --throttling-method=simulate \
  --output=json --output-path=./lh-after.json --quiet
# 예산 게이트: lighthouse budgets.json 으로 LCP/TBT/byte 상한 enforce
```

## Anti-patterns (하지 말 것)

- ❌ 전부 CacheFirst 로 통일 → 오래된 데이터가 영구히 박힘. 데이터 성격별로 전략 분리.
- ❌ Save-Data/effectiveType 를 feature-detect 없이 사용 → Safari/Firefox 에서 `undefined` 크래시.
- ❌ 오프라인 실패를 조용히 삼킴 → 사용자는 "저장됐겠지" 오해 후 데이터 유실 불신. 항상 상태 표시.
- ❌ 무한 재시도 → 종량제 사용자 데이터 폭증(비용). 백오프 + 상한 필수.
- ❌ 큰 폰트 패밀리 다중 weight 로딩 → system stack 우선, 커스텀은 1 weight subset.
- ❌ JS 없으면 빈 화면(CSR-only) → 첫 의미 콘텐츠는 SSR/SSG 로 JS 0 에서도 보이게.
- ❌ 이미지 width/height 누락 → CLS 폭증. 항상 명시 + lazy.
- ❌ 예산 없이 "최적화" → 측정 가능한 KB/TTI 목표(1절)부터 고정.

## Verification (산출물이 실제로 작동하는지)

1. **예산 통과**: `lh-before.json` 대비 `lh-after.json` 에서 초기 JS·LCP·TBT 가 1절 목표 이내인지.
2. **오프라인 동작**: DevTools Network=Offline 또는 비행기모드로 앱 셸·핵심 읽기·작성 큐잉이 되는지.
3. **재연결 flush**: 오프라인 작성 → 온라인 복귀 시 BackgroundSync/mutation 큐가 자동 전송되는지(서버 로그 확인).
4. **Save-Data 분기**: `--enable-features` 또는 헤더 주입으로 절약 모드일 때 경량 변형이 응답되는지(`Vary: Save-Data`).
5. **저사양**: CPU 6x + Slow 3G + 2GB RAM 에뮬에서 핵심 루프가 8s 내 인터랙티브인지.
6. **상태 가시성**: 오프라인/동기화 대기 배너가 모든 핵심 화면에 노출되는지(페르소나 시뮬: 저소득·고령 교차).

```bash
# 최종 게이트 — 빌드 + 예산 검사 + Lighthouse 가 모두 green 이어야 푸시
npm run build && npx -y lighthouse $URL --budget-path=./budgets.json --quiet \
  && echo "offline-first checks PASS"
```

## 산출물

- 캐시 전략 설정(`service-worker.js` / Workbox 또는 Expo `queryClient` + persist)
- 낙관적 UI + 백그라운드 동기화 코드
- 페이로드 예산표(네트워크 클래스별) + CI 게이트(`budgets.json`, webpack performance hints)
- Save-Data 적응 로딩 유틸 + 서버 헤더 처리
- 이미지 전략(반응형 AVIF/WebP, lazy, LQIP)
- 저사양 단말 테스트 매트릭스 + Lighthouse 회귀 명령

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
