---
name: vercel-react
description: >-
  Use when implementing or debugging React/Next.js in a Vercel deployment context — "React 최적화", "Next.js 안정성", "Vercel 성능", "하이드레이션 에러", "react best practices", or /vercel-react. Produces measured, project-compatible boundary, caching, rendering and deployment changes; excludes RN/Expo, generic platform migration and unapproved production or paid settings.
version: 0.1.3
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebSearch
compatibility: [claude-code]
author: simon-stack
---

# vercel-react

기존 React/Next.js 앱의 실제 병목을 재현하고, Vercel 배포 맥락에서 필요한 최소 변경을 구현한다. App Router의 Server/Client 경계·캐싱·스트리밍·Server Actions는 **해당 라우터와 버전일 때만** 적용한다. 시각적 UI 코드 전에 `simon-design-first` 진단을 수행한다.

## When to use / boundaries

쓸 때:
- Vercel에 배포되는 React/Next.js 화면·라우트의 성능·안정성 문제를 해결할 때
- `'use client'` 가 트리 위쪽에 박혀 번들이 부풀거나 하이드레이션 에러가 날 때
- 데이터 패칭이 waterfall 로 느릴 때, 캐시 전략(ISR/`use cache`)을 정할 때
- App Router에서 Server Action / route handler / Suspense streaming이 실제로 필요할 때
- Vercel 배포 설정(`next.config`, ISR, 이미지, env, runtime)을 점검할 때

쓰지 말 것 (다른 skill 로):
- RN/Expo **네이티브** 모바일 → `building-native-ui`
- Vercel 맥락 없는 일반 Next.js 최적화 → `nextjs-optimizer`
- 하이브리드 vs 네이티브 **플랫폼 결정** → `app-platform-selector`
- Vue/Nuxt → `vue-best-practices`

## 선행 체크

`package.json`·lockfile·`next.config.*`·`app/`/`pages/`·배포 설정·기존 테스트를 읽고, 프레임워크 버전, App/Pages Router, 실제 호스팅, 패키지 매니저와 현재 baseline을 기록한다. React 단독 앱이나 비Vercel 배포에는 해당되는 지침만 적용하고 Vercel/Next.js 이식을 강제하지 않는다. 지연·번들·하이드레이션·캐시 오동작을 재현 URL, 브라우저/빌드 로그와 조건으로 구분한다. 미측정 LCP·번들 크기·비용을 추정치처럼 쓰지 않는다.

문자열 검색은 후보 위치를 찾는 도구일 뿐이다. `'use client'` 파일 수나 `layout.tsx`의 존재만으로 결함을 판정하지 말고 실제 import graph, 서버 비밀값 경계, 빌드와 브라우저 동작을 확인한다.

## Workflow

1. **경계**: App Router라면 Server/Client import graph를, Pages Router나 React 단독 앱이라면 해당 렌더링·번들 경계를 확인한다.
2. **캐시/렌더링**: 라우트별 신선도·개인화 요구를 분류하고 Next 버전 및 `cacheComponents` 활성 여부에 맞는 **한 가지** 모델을 선택한다. 전역 캐시·호스팅 변경을 기본값으로 두지 않는다.
3. **지연**: 실측 waterfall에서 독립 요청만 병렬화하고, 느린 하위 트리에 Suspense를 둔다. 의존 요청을 무조건 `Promise.all`로 바꾸지 않는다.
4. **변경 작업**: 폼에 Server Action이 적합한지, 외부 API·webhook에는 Route Handler가 필요한지 판단한다. 두 경로 모두 서버 인증·권한·입력 검증을 수행한다.
5. **런타임/배포**: 필요한 경우에만 Node/Edge 제약, 함수·DB 리전, 이미지·폰트·서드파티 스크립트와 환경변수를 확인한다. 프리뷰/운영 배포와 유료 설정은 별도 권한·비용 게이트를 따른다.
6. **검증**: 기존 lint/typecheck/test/build와 같은 URL·조건의 전후 측정을 수행한다. 측정 못 한 항목은 미검증으로 표시하고 위험·롤백을 기록한다.

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

App Router에서는 Client 경계를 필요한 상호작용 범위로 제한한다. Provider처럼 상위에 둘 이유가 있으면 가능하며, 실제 import graph와 번들을 확인한다:

```tsx
// app/dashboard/page.tsx  ← Server Component (기본, 'use client' 없음)
import { getStats } from '@/lib/data';
import Chart from './chart';           // Client (아래)

export default async function Page() {
  const stats = await getStats();      // 서버에서 패칭 — 키/DB 노출 없음
  return (
    <main>
      <h1>대시보드</h1>
      <Chart data={stats} />             {/* 직렬화 가능한 props 만 넘김 */}
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

여기서는 `getStats()`를 이미 기다렸으므로 Chart 주변에 Suspense만 씌워도 스트리밍되지 않는다. 지연되는 데이터 fetch는 별도 async 하위 Server Component로 내려야 한다. `'use client'`가 있는 파일의 **import 대상**이 클라이언트 번들에 포함되는지를 점검하고, 상위 파일이라는 이유만으로 무조건 오류로 표시하지 않는다.

---

### 2. 데이터 패칭 + 캐싱 결정표

| 확인된 모드 | 전략 | 적용 범위 |
|---|---|---|
| App Router, Cache Components **꺼짐** | 기존 fetch/segment 캐시 모델에서 정적·ISR·동적 선택 | `fetch(..., { next: { revalidate: N } })` 등 해당 버전 API |
| App Router, Cache Components **켜짐** | 캐시 가능한 함수/컴포넌트에 `use cache`·`cacheLife`·`cacheTag`; 요청별 데이터는 Suspense 경계 | segment `revalidate`/`dynamic`/`fetchCache`와 혼용하지 않음 |
| Pages Router | 기존 `getStaticProps`/`getServerSideProps` 등과 호스팅 캐시 정책 | App Router 지시문을 억지로 적용하지 않음 |

기본 `fetch`의 관측 동작은 버전·라우트·프리렌더/개발 모드에 따라 달라진다. `no-store`처럼 보인다는 이유로 전체 페이지가 항상 요청마다 재생성된다고 단정하지 않는다. 개인정보·인증 데이터는 캐시 키·공유 범위를 별도로 검토한다.

Cache Components가 **꺼진 App Router**에서만 사용할 ISR 예시:

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

Cache Components가 **켜진 지원 버전**에서만 사용할 예시:

```tsx
import { cacheLife, cacheTag } from 'next/cache';

async function getProducts() {
  'use cache';
  cacheTag('products');        // updateTag('products') 또는 revalidateTag('products', 'max')
  cacheLife('hours');          // 빌트인 프로필 (seconds|minutes|hours|days|max)
  // 또는: cacheLife({ stale: 60, revalidate: 3600, expire: 86400 })
  const res = await fetch('https://api.example.com/products');
  return res.json();
}
```

> `cacheLife()`/`cacheTag()` 는 모듈 최상위(top-level)에서 호출하면 throw 한다.
> 반드시 `'use cache'` 가 붙은 함수/컴포넌트 **본문 안**에서 호출할 것.

`next.config.ts` (프로젝트가 Cache Components 도입을 명시적으로 선택한 경우에만):

```ts
import type { NextConfig } from 'next';
const nextConfig: NextConfig = {
  cacheComponents: true, // 지원 버전에서 PPR + 'use cache'; 기존 프로젝트에 무단 적용 금지
};
export default nextConfig;
```

Cache Components가 꺼진 프로젝트는 해당 버전의 이전 캐시 모델과 기존 코드를 유지한다. `cacheComponents` 변경은 캐시 의미와 런타임을 바꾸므로 별도 마이그레이션·회귀 검증이 필요하다.

---

### 3. Suspense + 스트리밍 (waterfall 제거)

**서로 독립적인** 요청이 실제 지연 원인일 때 병렬로 시작한다. 선행 응답의 ID·권한이 필요한 요청은 순서를 유지한다:

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

App Router의 `loading.tsx`는 해당 라우트 세그먼트의 fallback이다. 위젯 단위 스트리밍에는 느린 async 하위 트리 주위에 Suspense를 둔다. 개발 서버가 아니라 실제 빌드/브라우저에서 fallback과 전환을 확인한다.

---

### 4. Server Actions / Route Handlers (mutation)

App Router의 폼 변경에는 Server Action과 React `useActionState`를 검토한다. 외부 클라이언트·webhook·REST 계약에는 Route Handler가 적합할 수 있다. 기존 API를 요청 없이 이식하지 않는다. 다음 예시의 인증·권한·DB helper는 대상 프로젝트의 실제 구현으로 연결하고, `zod`가 없다면 기존 입력 검증기를 사용한다:

```tsx
// app/actions.ts
'use server';
import { updateTag } from 'next/cache';
import { z } from 'zod';

const schema = z.object({ title: z.string().min(1) });

export async function createPost(prev: unknown, formData: FormData) {
  const user = await getCurrentUser();          // 프로젝트의 서버 인증 helper
  if (!user || !(await canCreatePost(user))) return { error: '권한이 없습니다' };
  const parsed = schema.safeParse({ title: formData.get('title') });
  if (!parsed.success) return { error: '제목을 입력하세요' };
  await db.post.create({ data: parsed.data });
  updateTag('posts');                     // 지원 버전의 Server Action: 즉시 새 데이터
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
| 용도 | UI와 결합된 폼/버튼 mutation | 외부 API, webhook, REST 또는 기존 API 계약 |
| 호출 | `<form action>` / 직접 import | `fetch('/api/..')` / 외부 클라 |
| 보안 | 반드시 입력 검증 + authz **재확인** | 동일 |

Server Action은 공개 엔드포인트처럼 취급해 서버에서 매번 인증·권한·입력을 검증한다. `updateTag`는 지원 버전의 Server Action에서만 즉시 read-your-writes를 제공한다. 약간의 stale 허용 시 `revalidateTag(tag, 'max')`를, 구버전에서는 해당 버전의 API를 사용한다. 단일 인자 `revalidateTag(tag)`를 새 코드의 기본값으로 복사하지 않는다.

---

### 5. Edge vs Node runtime

| 검토 항목 | Node | Edge |
|---|---|---|
| 호환성 | Node API·기존 서버 SDK를 프로젝트에서 확인 | Edge가 지원하는 API·SDK·호스팅 제약 확인 |
| 데이터·지연 | DB/함수 리전과 실제 왕복 지연 측정 | 요청 경로·리전 이점과 제약을 측정 |
| Cache Components | 지원 버전의 Node 경로 | `cacheComponents`와 Edge 혼용 불가 |

```ts
// app/api/geo/route.ts
export const runtime = 'edge';   // 가벼운 변환만. DB·Node SDK 쓰면 충돌
export async function GET(req: Request) { /* Web API 만 */ }
```

기본은 기존 runtime을 유지한다. `cacheComponents`를 켠 App Router는 Node runtime이 필요하다. Proxy/이전 Middleware는 버전·배포 어댑터별 런타임이 다르므로 Edge라고 가정하지 않는다. 인증/권한을 Proxy만으로 보장하지 않고 Server Action·Route Handler에서 다시 확인한다.

---

### 6. 배포 config (Vercel)

- **이미지**: `next/image` + `next.config` `images.remotePatterns` 로 외부 호스트 허용.
- **env**: secret 은 서버 전용(접두사 없음). 클라 노출은 `NEXT_PUBLIC_*` 만. Vercel
  Project Settings → Environment Variables 로 주입. `.env` 는 `.gitignore` 필수.
- **ISR/캐시**: 위 2번. on-demand 무효화는 `revalidateTag`/`revalidatePath`.

`'use client'` 파일 한 줄 검색으로 secret 누출을 판정할 수 없다. import graph와 빌드 산출물을 확인하고, 공개 값이 아닌 서버 secret을 `NEXT_PUBLIC_*`에 넣지 않는다. 로그·보고서에 실제 secret 값을 출력하지 않는다.

프리뷰 배포도 기존 워크플로와 권한, 구독 포함 사용량 및 초과 과금 차단을 확인한 뒤에만 실행한다. 추가 과금 $0 조건에서는 유료 기능·초과 사용·자동충전을 활성화하지 않는다. 운영 배포·요금제 변경·새 서비스 생성은 별도 승인 없이는 실행하지 않는다.

## 검증 (verification)

```bash
# 1) 프로젝트의 실제 패키지 매니저·기존 스크립트로 빌드
npm run build      # npm 프로젝트의 예시; 성공·라우트 모드 확인

# 2) 로컬 실행 후 하이드레이션 에러 점검 (사용 가능한 start 스크립트가 있을 때)
npm run start
# 별도 터미널
# 설치된 Lighthouse/브라우저 도구가 있으면 동일 URL·조건으로 전후 계측

# 3) 타입/린트
npm run lint       # 정의된 경우에만; typecheck/test도 기존 스크립트 사용
```

통과 기준:
- [ ] `next build` 성공, 라우트별 렌더링 모드가 의도와 일치
- [ ] 콘솔에 hydration mismatch 0건
- [ ] Client 경계가 필요한 범위에 있고 서버 전용 import·secret이 새지 않음
- [ ] 변경 후 지원 버전의 무효화 방식으로 화면 갱신이 실제 관측됨
- [ ] 서버 secret이 클라이언트 번들에 없음 (`NEXT_PUBLIC_*`는 공개 값만)

## Anti-patterns

- `'use client'` 위치·파일 수만으로 성능 결함을 단정하거나 상위 Provider를 무조건 제거.
- Server Component 에 `useState`/`onClick` → 빌드 에러. 클라로 분리.
- 의존 요청까지 무조건 `Promise.all`로 병렬화하거나 이미 기다린 데이터에 Suspense만 추가.
- 현재 캐시 모델·프리렌더 여부 확인 없이 `fetch` 기본 동작을 단정.
- `cacheLife()`/`cacheTag()` 를 모듈 top-level 호출 → throw. `'use cache'` 함수 본문 안에서만.
- mutation 후 지원 버전에 맞는 캐시 무효화와 화면 갱신 검증 누락.
- Server Action 에서 authz/입력 재검증 생략 → 공개 엔드포인트와 동일한 취약점.
- `cacheComponents` 활성 상태에서 Edge runtime 선언하거나 Proxy를 Edge/인증 완결로 가정.
- 서버 secret 을 `NEXT_PUBLIC_` 로 노출 → 키 유출(치명적).
- 하이드레이션 mismatch 무시(`Date.now()`/`Math.random()`/`localStorage` 를 서버 렌더에) → UI 깜빡임·에러.

## 공식 근거 (프로젝트 버전 기준으로 재확인)

- [Server/Client 경계](https://nextjs.org/docs/app/getting-started/server-and-client-components), [Cache Components](https://nextjs.org/docs/app/getting-started/partial-prerendering), [이전 캐시 모델](https://nextjs.org/docs/app/guides/caching-without-cache-components)
- [캐시 마이그레이션](https://nextjs.org/docs/app/guides/migrating-to-cache-components), [즉시 무효화 `updateTag`](https://nextjs.org/docs/app/api-reference/functions/updateTag), [지연 갱신 `revalidateTag`](https://nextjs.org/docs/app/api-reference/functions/revalidateTag)
- [Proxy 경계](https://nextjs.org/docs/app/api-reference/file-conventions/proxy), [Vercel 출시 점검표](https://vercel.com/docs/production-checklist)

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
