---
name: vercel-react
description: >-
  Use when building or hardening a Next.js App Router app for Vercel production
  — triggers "Next.js 앱 만들어", "서버 컴포넌트 vs 클라이언트", "use client 남발",
  "스트리밍 적용", "Server Action 구현", "ISR 설정", "Vercel 배포 최적화", "하이드레이션 에러",
  "next build 느려", "Next.js best practices", "App Router data fetching",
  "server vs client component", "fix hydration mismatch", "streaming with Suspense",
  "server actions", "edge vs node runtime", "next.config tuning". Produces a
  Server/Client boundary decision table, data-fetching plus caching patterns
  (fetch revalidate, use cache, cacheLife/cacheTag), Suspense streaming and
  Server Action snippets, runtime (edge vs node) guidance, next.config plus ISR
  plus image plus env config, a precheck grep for boundary smells, and a verify
  step (next build, Lighthouse). For RN/Expo native use building-native-ui; for
  pure Core Web Vitals tuning of an existing app use nextjs-optimizer.
version: 0.1.0
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebSearch
compatibility: [claude-code]
author: simon-stack
---

# vercel-react

Next.js (App Router) + Vercel 프로덕션 베스트프랙티스. Server/Client 경계, 데이터 패칭/캐싱,
스트리밍, Server Actions, runtime 선택, 배포 config 를 실제 코드로 잡는다.

> 기준 버전: **Next.js 16** (App Router, React 19). 16 에서 `cacheComponents: true` 가
> PPR + `use cache` 를 켠다. 13~15 프로젝트는 `unstable_cache`/`fetch revalidate` 경로를 쓴다.

## When to use / boundaries

쓸 때:
- 새 Next.js App Router 화면/라우트를 설계하거나, 기존 라우트를 프로덕션 기준으로 손볼 때
- `'use client'` 가 트리 위쪽에 박혀 번들이 부풀거나 하이드레이션 에러가 날 때
- 데이터 패칭이 waterfall 로 느릴 때, 캐시 전략(ISR/`use cache`)을 정할 때
- Server Action / route handler / Suspense streaming 을 추가할 때
- Vercel 배포 설정(`next.config`, ISR, 이미지, env, runtime)을 점검할 때

쓰지 말 것 (다른 skill 로):
- RN/Expo **네이티브** 모바일 → `building-native-ui`
- 이미 도는 앱의 순수 **Core Web Vitals** 튜닝(LCP/CLS/번들) → `nextjs-optimizer`
- 하이브리드 vs 네이티브 **플랫폼 결정** → `app-platform-selector`
- Vue/Nuxt → `vue-best-practices`

## 선행 체크 (precheck — 경계 냄새 grep)

```bash
# 0) Next 프로젝트 + 버전 확인
test -f package.json && grep -q '"next"' package.json || { echo "NOT_NEXT — skip"; exit 0; }
node -p "require('./package.json').dependencies.next" 2>/dev/null

# 1) 'use client' 분포 — 적을수록 좋다. layout/page 상단에 있으면 적신호
grep -rln "^['\"]use client" app/ src/ components/ 2>/dev/null | wc -l
grep -rl "use client" app/**/layout.tsx app/**/page.tsx 2>/dev/null   # 거의 항상 잘못

# 2) Client 컴포넌트가 서버 전용 라이브러리를 import (번들 누수/빌드 깨짐)
#    'use client' 파일에서 fs / crypto / @prisma / server-only import 가 나오면 적신호
grep -rln "use client" -l app/ src/ 2>/dev/null | xargs grep -lnE "(from .(fs|crypto|@prisma|server-only))" 2>/dev/null

# 3) await fetch 가 순차로 줄지어 있으면 waterfall 후보
grep -rnE "const .*= await fetch" app/ 2>/dev/null

# 4) 캐시 의도 불명 fetch (revalidate/cache/use cache 주석 없는 것)
grep -rnE "await fetch\(" app/ 2>/dev/null

# 5) runtime 선언 — Node 전용 API 쓰는데 edge 선언돼 있으면 충돌
grep -rn "export const runtime" app/ 2>/dev/null
```

해석: `'use client'` 파일 수가 서버 컴포넌트보다 많거나 `layout/page` 최상단에 있으면
"use client 남발" → 아래 1번 표로 경계를 내린다.

## Workflow

1. **경계 라벨링**: 모든 컴포넌트를 Server / Client 로 분류 (표 1). 기본은 Server.
2. **데이터 패칭 + 캐시 전략**: 라우트별 정적/ISR/동적 결정 (표 2), 캐시 주석 의무화.
3. **waterfall 제거**: 병렬 `Promise.all` + `<Suspense>` 스트리밍.
4. **mutation 은 Server Action**: 폼·버튼은 action + `useActionState`, 변경 후 `revalidateTag`.
5. **runtime 선택**: route handler/페이지에 node vs edge 명시 (표 3).
6. **배포 config**: `next.config`, 이미지, env, ISR 점검.
7. **검증**: `next build` + Lighthouse + 하이드레이션 에러 0.

---

### 1. Server vs Client Component 결정표

| 필요한 것 | 컴포넌트 | 근거 |
|---|---|---|
| 데이터 패칭 / DB 직접 접근 / secret 사용 | **Server** | 번들에서 제외, 키 노출 없음 |
| `useState`/`useEffect`/`useRef` 등 hook | **Client** | 상태·생명주기는 클라에서만 |
| `onClick`/`onChange` 등 이벤트 핸들러 | **Client** | 인터랙션 |
| `window`/`localStorage`/브라우저 API | **Client** | 서버에 없음 |
| `framer-motion`/차트/에디터 등 클라 라이브러리 | **Client** (가능하면 `next/dynamic` 로 leaf) | 무거운 번들 격리 |
| 정적 마크업·레이아웃·텍스트 | **Server** (기본) | RSC 페이로드만 |

핵심 패턴 — **Client 는 잎(leaf)으로 밀고, Server 가 children 으로 감싼다**:

```tsx
// app/dashboard/page.tsx  ← Server Component (기본, 'use client' 없음)
import { getStats } from '@/lib/data';
import Chart from './chart';           // Client (아래)
import { Suspense } from 'react';

export default async function Page() {
  const stats = await getStats();      // 서버에서 패칭 — 키/DB 노출 없음
  return (
    <main>
      <h1>대시보드</h1>
      <Suspense fallback={<ChartSkeleton />}>
        <Chart data={stats} />          {/* 직렬화 가능한 props 만 넘김 */}
      </Suspense>
    </main>
  );
}
```

```tsx
// app/dashboard/chart.tsx  ← Client Component (leaf 만)
'use client';
import { useState } from 'react';
export default function Chart({ data }: { data: Stat[] }) {
  const [range, setRange] = useState('7d');
  // recharts 등 클라 전용 라이브러리는 여기서만
}
```

안티패턴: `'use client'` 를 `layout.tsx`/`page.tsx` 최상단에 두면 그 하위 트리 전체가
클라 번들로 빨려 들어간다. 인터랙션이 필요한 작은 조각만 클라로 분리할 것.

---

### 2. 데이터 패칭 + 캐싱 결정표

| 라우트 성격 | 전략 | 코드 |
|---|---|---|
| 빌드 시 고정 (약관, 랜딩) | SSG | 아무 캐시 옵션 없이 fetch (기본 정적) |
| 주기 갱신 (블로그, 카탈로그) | ISR | `export const revalidate = N` 또는 `fetch(.., { next: { revalidate: N } })` |
| 요청마다 신선 (대시보드, 검색) | Dynamic | `fetch(.., { cache: 'no-store' })` 또는 동적 API 사용 |
| 비싼 계산·외부 API 결과 재사용 | `use cache` (16) | `'use cache'` + `cacheLife()` + `cacheTag()` |

> Next.js 16 은 **명시적 캐싱**. fetch 는 기본 캐시되지 않으며(`no-store` 동작), 캐시하려면
> 옵션을 적거나 `use cache` 를 쓴다. 13~14 의 "fetch 자동 캐시" 가정은 버린다.

ISR (페이지 레벨 또는 fetch 레벨):

```tsx
// app/blog/page.tsx
export const revalidate = 3600; // 1h — 백그라운드 재생성

export default async function Page() {
  const res = await fetch('https://api.example.com/posts', {
    next: { revalidate: 3600, tags: ['posts'] }, // 태그로 on-demand 무효화 가능
  });
  const posts = await res.json();
  return <PostList posts={posts} />;
}
```

`use cache` (Next.js 16, `cacheComponents: true` 필요) — fetch 가 아닌 임의 비싼 함수도 캐시:

```tsx
import { cacheLife, cacheTag } from 'next/cache';

async function getProducts() {
  'use cache';
  cacheTag('products');        // revalidateTag('products') 로 무효화
  cacheLife('hours');          // 빌트인 프로필 (seconds|minutes|hours|days|max)
  // 또는: cacheLife({ stale: 60, revalidate: 3600, expire: 86400 })
  const res = await fetch('https://api.example.com/products');
  return res.json();
}
```

> `cacheLife()`/`cacheTag()` 는 모듈 최상위(top-level)에서 호출하면 throw 한다.
> 반드시 `'use cache'` 가 붙은 함수/컴포넌트 **본문 안**에서 호출할 것.

`next.config.ts` (16 에서 캐싱·PPR 켜기):

```ts
import type { NextConfig } from 'next';
const nextConfig: NextConfig = {
  cacheComponents: true, // PPR + 'use cache' 활성화 (16). 13~15 는 experimental.ppr
};
export default nextConfig;
```

13~15 레거시 경로는 `import { unstable_cache, revalidateTag } from 'next/cache'`
(`nextjs-optimizer` 5번 참조).

---

### 3. Suspense + 스트리밍 (waterfall 제거)

순차 await 는 느리다. 병렬로 시작하고 Suspense 로 흘려보낸다:

```tsx
// Before (waterfall): user 끝나야 orders 시작 → 합산 지연
const user = await getUser();
const orders = await getOrders();

// After (parallel): 동시에 시작
const [user, orders] = await Promise.all([getUser(), getOrders()]);
```

느린 데이터는 페이지를 막지 말고 스트리밍:

```tsx
// app/page.tsx — 빠른 부분 먼저 보내고 느린 위젯은 도착하는 대로 스트림
import { Suspense } from 'react';

export default function Page() {
  return (
    <>
      <Header />                                   {/* 즉시 렌더 */}
      <Suspense fallback={<FeedSkeleton />}>
        <SlowFeed />                               {/* 내부에서 await — 도착 시 swap */}
      </Suspense>
    </>
  );
}
```

`loading.tsx` 는 라우트 세그먼트 전체에 자동 Suspense 경계를 깐다 (route-level fallback).

응답을 막지 않을 사이드이펙트(로깅/분석)는 `after()`:

```tsx
import { after } from 'next/server';
export default async function Page() {
  after(() => { logView(); }); // 응답 전송 후 실행 — 사용자 대기 없음
  return <Content />;
}
```

---

### 4. Server Actions (mutation)

폼·버튼 변경은 route handler 대신 Server Action 으로. React 19 `useActionState` 로 pending/error 관리:

```tsx
// app/actions.ts
'use server';
import { revalidateTag } from 'next/cache';
import { z } from 'zod';

const schema = z.object({ title: z.string().min(1) });

export async function createPost(prev: unknown, formData: FormData) {
  const parsed = schema.safeParse({ title: formData.get('title') });
  if (!parsed.success) return { error: '제목을 입력하세요' };
  await db.post.create({ data: parsed.data });
  revalidateTag('posts');                 // 캐시 무효화 → 목록 즉시 갱신
  return { ok: true };
}
```

```tsx
// app/new/form.tsx
'use client';
import { useActionState } from 'react';
import { createPost } from '../actions';

export default function NewPostForm() {
  const [state, action, pending] = useActionState(createPost, null);
  return (
    <form action={action}>
      <input name="title" />
      {state?.error && <p role="alert">{state.error}</p>}
      <button disabled={pending}>{pending ? '저장 중…' : '저장'}</button>
    </form>
  );
}
```

Server Action vs Route Handler:

| | Server Action | Route Handler (`route.ts`) |
|---|---|---|
| 용도 | 앱 내부 mutation (폼/버튼) | 외부 API, webhook, 서드파티 호출, REST |
| 호출 | `<form action>` / 직접 import | `fetch('/api/..')` / 외부 클라 |
| 보안 | 반드시 입력 검증 + authz **재확인** | 동일 |

> Server Action 은 공개 엔드포인트와 같다. 클라가 신뢰됐다고 가정하지 말고 모든 action 에서
> auth/authz 와 입력 스키마를 **서버에서** 재검증한다 (`authz-designer` 참조).

---

### 5. Edge vs Node runtime

| | Node (기본) | Edge |
|---|---|---|
| 콜드스타트 | 느림 | 거의 없음 |
| Node API (`fs`, `crypto`, 대부분 SDK) | O | 제한적 (Web API 만) |
| Prisma / 무거운 ORM | O | X (대부분) |
| 지연 민감 미들웨어·지오라우팅·간단 변환 | 가능하나 과함 | 적합 |

```ts
// app/api/geo/route.ts
export const runtime = 'edge';   // 가벼운 변환만. DB·Node SDK 쓰면 충돌
export async function GET(req: Request) { /* Web API 만 */ }
```

판단: DB/Node SDK 를 쓰면 **node** 유지. 단순 변환·리다이렉트·헤더 조작·지오라우팅만이면 edge.
Vercel 미들웨어(`middleware.ts`)는 edge 에서 돌므로 무거운 로직 금지.

---

### 6. 배포 config (Vercel)

- **이미지**: `next/image` + `next.config` `images.remotePatterns` 로 외부 호스트 허용.
- **env**: secret 은 서버 전용(접두사 없음). 클라 노출은 `NEXT_PUBLIC_*` 만. Vercel
  Project Settings → Environment Variables 로 주입. `.env` 는 `.gitignore` 필수.
- **ISR/캐시**: 위 2번. on-demand 무효화는 `revalidateTag`/`revalidatePath`.

```bash
# 클라 번들에 secret 이 새지 않는지 — NEXT_PUBLIC_ 아닌 키가 클라에서 참조되면 위험
grep -rnE "process\.env\.[A-Z_]+" app/ src/ components/ 2>/dev/null \
  | grep -v "NEXT_PUBLIC_" | grep -iE "use client" -l
```

## 검증 (verification)

```bash
# 1) 빌드 — RSC/경계 오류, 직렬화 불가 props 를 여기서 잡는다
npm run build      # 라우트별 ○(Static)/f(Dynamic)/ISR 마킹을 출력에서 확인

# 2) 로컬 실행 후 하이드레이션 에러 점검 (콘솔 "Hydration failed" 0건)
npm run start
# 별도 터미널
npx lighthouse http://localhost:3000 --only-categories=performance,best-practices --view

# 3) 타입/린트
npx tsc --noEmit && npm run lint
```

통과 기준:
- [ ] `next build` 성공, 라우트별 렌더링 모드가 의도와 일치
- [ ] 콘솔에 hydration mismatch 0건
- [ ] `'use client'` 가 leaf 에만, layout/page 최상단에 없음
- [ ] 변경(mutation) 후 `revalidateTag`/`revalidatePath` 로 화면 갱신됨
- [ ] secret 이 `NEXT_PUBLIC_` 없이 클라 번들에 들어가지 않음

## Anti-patterns

- `'use client'` 를 layout/page 상단에 → 하위 트리 전체 클라화. leaf 로 내려라.
- Server Component 에 `useState`/`onClick` → 빌드 에러. 클라로 분리.
- 순차 `await fetch` 줄세우기 → waterfall. `Promise.all` + Suspense.
- Next 16 에서 "fetch 가 알아서 캐시됨" 가정 → 16 은 기본 no-store. 명시하라.
- `cacheLife()`/`cacheTag()` 를 모듈 top-level 호출 → throw. `'use cache'` 함수 본문 안에서만.
- mutation 후 `revalidateTag` 누락 → stale UI.
- Server Action 에서 authz/입력 재검증 생략 → 공개 엔드포인트와 동일한 취약점.
- edge runtime 선언 후 Prisma/Node SDK 사용 → 런타임 폭발. node 유지.
- 서버 secret 을 `NEXT_PUBLIC_` 로 노출 → 키 유출(치명적).
- 하이드레이션 mismatch 무시(`Date.now()`/`Math.random()`/`localStorage` 를 서버 렌더에) → UI 깜빡임·에러.

## Related skills

- `nextjs-optimizer` — 기존 앱 Core Web Vitals/번들 튜닝
- `building-native-ui` — RN/Expo 네이티브 (웹 아님)
- `app-platform-selector` — 하이브리드/PWA/네이티브 결정
- `auth-builder` / `authz-designer` — Server Action authz
- `deploy-configurator` — 배포 설정
- `simon-tdd` — 라우트/Server Action 테스트

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
