---
name: nextjs-optimizer
description: Audits and optimizes Next.js (13+ App Router) projects across 5 performance areas — images (next/image, CLS prevention), render strategy (SSG/ISR/SSR/CSR per-page labeling), code splitting (dynamic imports, bundle < 200KB), script loading (next/script strategies), and data caching (unstable_cache + revalidateTag). Use this skill whenever the user says things like "Next.js 최적화", "Core Web Vitals 개선", "번들 너무 커", "LCP 개선", "optimize Next app", "improve bundle size", "Lighthouse score bad", "slow page load"—and package.json contains "next". Do NOT trigger for Next.js tutorials, project setup, or non-Next.js React apps. Produces an actionable audit with specific file paths and replacement snippets.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon
---

# Next.js Optimizer

Next.js (13+ App Router 기준) 프로젝트의 5대 성능 영역을 점검·수정한다.

## When to use

- `package.json` 에 `"next"` 의존성 존재
- Core Web Vitals 점수 저조
- `/benchmark` 결과 회귀 감지
- 번들 사이즈 증가
- LCP·CLS·INP 개선 요청
- `app-dev-orchestrator` 단계 13 내 자동 호출 (Next.js 감지 시)

## 선행 체크

```bash
test -f package.json && grep -q '"next"' package.json && echo "NEXT_OK" || { echo "NOT_NEXT — skip"; exit 0; }
```

Next.js 아니면 즉시 종료. 이 skill 은 Next 전용.

## Workflow — 5대 영역

### 1. 이미지 최적화

```bash
# 1. <img> 태그 잔존 확인
grep -rn "<img" src/ app/ components/ 2>/dev/null
```

체크리스트:
- [ ] `<img>` → `next/image` 전량 전환
- [ ] `priority` 는 above-the-fold 이미지에만 (과용 금지)
- [ ] `sizes` 속성 명시 (반응형)
- [ ] `placeholder="blur"` + `blurDataURL` (LQIP)
- [ ] `width`·`height` 명시로 **CLS** 방지
- [ ] `next.config.js` 에 `images.minimumCacheTTL = 31536000`
- [ ] 대량 이미지는 Cloudflare Images / Imgix 오프로드 검토

### 2. 렌더링 전략 라벨링

모든 페이지를 하나로 분류:

| 전략 | 언제 | 예시 |
|---|---|---|
| **SSG** | 빌드 시 고정 | 약관, 랜딩 |
| **ISR** | 주기 갱신 | 블로그, 상품, 카탈로그 |
| **SSR** | 요청마다 | 대시보드, 검색 |
| **CSR** | 클라이언트 후처리 | 관리자, 에디터 |

구현 체크:
- [ ] `export const dynamic = 'force-static' | 'force-dynamic'` 명시
- [ ] ISR 은 `export const revalidate = <seconds>` + 주기 근거 주석
- [ ] SSR 은 캐시 무효화 이유 주석 필수
- [ ] CSR 은 Server Component 기본값 깨는 이유 주석

### 3. 코드 분할

무거운 컴포넌트 리스트업 (에디터, 차트, PDF 뷰어, 지도, 웹뷰):

```tsx
// Before
import RichEditor from '@/components/RichEditor';

// After
import dynamic from 'next/dynamic';
const RichEditor = dynamic(() => import('@/components/RichEditor'), {
  ssr: false,  // 서버 렌더 스킵
  loading: () => <EditorSkeleton />,
});
```

체크리스트:
- [ ] 초기 번들 < **200KB** gzipped (App Router 기준)
- [ ] Above-the-fold 외 컴포넌트는 `next/dynamic`
- [ ] `@next/bundle-analyzer` 로 시각화: `ANALYZE=true npm run build`
- [ ] Tree-shaking 확인 (named import 사용)

### 4. 서드파티 스크립트

GA · Clarity · Meta Pixel · 광고 SDK · Crisp · Intercom:

```tsx
import Script from 'next/script';

<Script
  src="https://www.googletagmanager.com/gtag/js?id=G-12345"
  strategy="afterInteractive"  // 또는 'lazyOnload'
/>
```

체크리스트:
- [ ] 전량 `next/script` 사용, `<script>` 잔존 0건
- [ ] 전략 명시: `beforeInteractive` / `afterInteractive` / `lazyOnload` / `worker`
- [ ] **FCP < 1.8s** 유지
- [ ] Partytown 활용 검토 (무거운 서드파티)

### 5. 데이터 캐싱 (App Router)

```tsx
import { unstable_cache, revalidateTag } from 'next/cache';

// CACHED: not realtime, invalidate via revalidateTag('products')
export const getProducts = unstable_cache(
  async () => db.product.findMany(),
  ['products'],
  { tags: ['products'], revalidate: 3600 }
);
```

체크리스트:
- [ ] `unstable_cache` 사용 함수에는 **// CACHED:** 주석 의무
- [ ] 태그 네이밍 규칙 (`<resource>` 또는 `<resource>:<id>`)
- [ ] 변경 mutation 에서 `revalidateTag` 호출
- [ ] `fetch` 옵션 `{ next: { revalidate: N, tags: [...] } }` 활용
- [ ] Edge runtime 고려 (`export const runtime = 'edge'`)

## 검증

```bash
npm run build
ANALYZE=true npm run build  # 번들 분석
npm run start
# 별도 터미널에서
npx lighthouse http://localhost:3000 --only-categories=performance --view
```

Gstack `/benchmark` 로 전후 비교.

Core Web Vitals 목표:
- LCP < 2.5s
- CLS < 0.1
- INP < 200ms
- FCP < 1.8s
- TBT < 200ms

## Checklist (전체)

- [ ] `<img>` 전량 `next/image` 전환
- [ ] 페이지별 렌더링 전략 라벨링 + 주석
- [ ] 초기 번들 < 200KB
- [ ] 서드파티 스크립트 `next/script` 전환
- [ ] `unstable_cache` + `revalidateTag` 전략 문서화
- [ ] Core Web Vitals 목표 달성
- [ ] `/benchmark` baseline 갱신

## Anti-patterns

- ❌ `<img>` 잔존 → LCP·CLS 둘 다 악화
- ❌ 모든 이미지에 `priority` → 의미 없음
- ❌ 모든 페이지 `force-dynamic` → ISR·SSG 이점 포기
- ❌ 에디터·차트를 초기 번들에 포함 → TTI 망침
- ❌ `unstable_cache` 사용 후 `revalidateTag` 안 함 → stale data
- ❌ `'use client'` 남발 → Server Component 이점 상실
- ❌ 벤치마크 없이 "빨라진 느낌"

## Related skills

- `/benchmark` — 성능 전후 비교
- `/design-review` — 시각 regression
- `simon-tdd` — 성능 회귀 테스트
- `app-dev-orchestrator` — 단계 13
