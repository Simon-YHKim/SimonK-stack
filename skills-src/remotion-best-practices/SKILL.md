---
name: remotion-best-practices
description: >
  Use when building or fixing programmatic video with Remotion (TypeScript + React) — triggers "Remotion 비디오", "프로그래밍 비디오", "코드로 영상 만들어", "데이터 기반 비디오", "영상 렌더링 자동화", "remotion video", "programmatic video", "code-driven video", "data-driven video", "render mp4 from react", or /remotion-best-practices. Produces correct Composition/Sequence structure, frame-driven animation via useCurrentFrame + interpolate + spring, audio/video asset sync (Audio, OffthreadVideo, staticFile), data-driven compositions with calculateMetadata, server-side render via renderMedia (@remotion/renderer) or scaled render via renderMediaOnLambda (@remotion/lambda), and verified output (npx remotion studio / npx remotion render). Targets Remotion v4 (4.0.x). Different from /design-shotgun (static visual exploration) and /make-pdf (document export) — this emits actual rendered MP4/WebM.
version: 2.0.0
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - Glob
compatibility: [claude-code]
---

# Remotion Best Practices

Remotion v4 로 프로그래밍 가능한 비디오를 만들고 렌더링한다. 모든 애니메이션은 **프레임 함수**다: `frame` → 화면. 시간이 아니라 프레임이 진실의 원천이며, 렌더는 결정론적(deterministic)이어야 한다.

## When to use / boundaries

쓸 때:
- TypeScript + React 로 MP4/WebM 영상을 코드로 생성 (자막, 차트 애니메, 데이터 기반 리포트 영상, 소셜 클립)
- 데이터(JSON/DB)를 props 로 주입해 N개 영상을 batch 렌더
- 서버/CI 또는 Lambda 에서 헤드리스 렌더 자동화

안 쓸 때 (다른 skill 로):
- 정적 UI/디자인 탐색 → `/design-shotgun`, `simon-design-first`
- 문서 PDF 출력 → `/make-pdf`, `office-docs`
- 슬라이드 → `/slides`
- Remotion 은 React Native 와 무관 (네이티브 앱 = `building-native-ui`)

핵심 제약:
- 렌더는 헤드리스 Chrome 을 띄운다 → CI 에 Chrome 의존성 필요
- `Math.random()`, `Date.now()`, 비결정 데이터는 프레임마다 값이 바뀌어 영상이 깜빡인다. seed 고정 또는 `random()`(remotion) 사용
- Lambda 는 AWS 과금 발생 → 비용 게이트 (CLAUDE.md §11 예외). 배포·렌더 전 사용자 확인

## 선행 체크

```bash
test -f package.json && grep -q '"remotion"' package.json && echo "REMOTION_OK" \
  || { echo "NOT_REMOTION — npx create-video@latest 로 스캐폴드 먼저"; }
# 버전 확인 (v4.0.x 권장, 2026 기준 최신 4.0.4xx)
node -e "console.log(require('remotion/package.json').version)" 2>/dev/null
npx remotion versions   # 설치된 @remotion/* 패키지 버전 일치 검사 (불일치 = 런타임 깨짐)
```

`@remotion/*` 패키지 버전이 하나라도 어긋나면 즉시 동기화한다 — Remotion 은 전 패키지 버전 락스텝이 필수다.

```bash
npx remotion upgrade   # 모든 @remotion/* 를 같은 버전으로 정렬
```

## 핵심 API 지도 (v4)

| API | import | 역할 |
|---|---|---|
| `Composition` | `remotion` | 영상 정의 (id, component, durationInFrames, fps, width, height) |
| `registerRoot` | `remotion` | `src/index.ts` 진입점에서 Root 등록 |
| `useCurrentFrame()` | `remotion` | 현재 프레임 번호 (애니메이션의 유일한 입력) |
| `useVideoConfig()` | `remotion` | fps/width/height/durationInFrames 읽기 |
| `interpolate()` | `remotion` | 프레임→값 선형/이징 매핑 |
| `spring()` | `remotion` | 물리 기반 자연스러운 전환 |
| `Sequence` | `remotion` | 타임라인상 시간 이동(from)·길이(durationInFrames) 분할 |
| `Series` | `remotion` | 시퀀스를 연속 배치 (자동 오프셋) |
| `AbsoluteFill` | `remotion` | position:absolute + inset:0 레이어 |
| `Audio` | `remotion` | 오디오 트랙 (volume, startFrom, trimBefore) |
| `OffthreadVideo` | `remotion` | 비디오 임베드 (렌더 시 `Video` 대신 필수) |
| `Img` | `remotion` | `<img>` 대신 — 로드 완료까지 프레임 대기 |
| `staticFile()` | `remotion` | `public/` 에셋 경로 해석 |
| `delayRender()/continueRender()` | `remotion` | 비동기 데이터 로드 동안 프레임 캡처 지연 |
| `bundle()` | `@remotion/bundler` | 프로젝트 번들 → serveUrl |
| `selectComposition()`, `renderMedia()` | `@remotion/renderer` | 서버사이드 렌더 |
| `renderMediaOnLambda()`, `getRenderProgress()` | `@remotion/lambda/client` | Lambda 스케일 렌더 |

## Workflow

### 1. 진입점 + Composition 등록

`src/index.ts`:
```tsx
import {registerRoot} from 'remotion';
import {RemotionRoot} from './Root';
registerRoot(RemotionRoot);
```

`src/Root.tsx` — 데이터 기반은 `defaultProps` + `calculateMetadata` 로 duration 을 데이터에서 산출:
```tsx
import {Composition} from 'remotion';
import {MyVideo, myVideoSchema} from './MyVideo';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MyVideo"
      component={MyVideo}
      durationInFrames={150}   // 30fps * 5s = 150 (calculateMetadata 로 덮어쓸 수 있음)
      fps={30}
      width={1080}
      height={1920}            // 9:16 세로 (소셜). 16:9=1920x1080
      schema={myVideoSchema}   // zod 스키마 → Studio 에서 props 편집 가능
      defaultProps={{title: 'Hello', items: []}}
      calculateMetadata={({props}) => ({
        durationInFrames: Math.max(60, props.items.length * 30),
      })}
    />
  );
};
```

### 2. 프레임 함수로 애니메이션 (interpolate)

```tsx
import {useCurrentFrame, useVideoConfig, interpolate, AbsoluteFill} from 'remotion';

export const Title: React.FC<{title: string}> = ({title}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // 0~20프레임 동안 페이드인 + 위로 슬라이드. extrapolate 클램프 필수.
  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const y = interpolate(frame, [0, 20], [40, 0], {
    extrapolateRight: 'clamp',
    easing: (t) => t * t,   // ease-in. bounce/elastic 금지 (CLAUDE.md §20)
  });

  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      <h1 style={{opacity, transform: `translateY(${y}px)`}}>{title}</h1>
    </AbsoluteFill>
  );
};
```

`extrapolate*: 'clamp'` 를 안 주면 입력 범위 밖에서 값이 무한 외삽되어 화면 밖으로 튄다 — 가장 흔한 버그.

### 3. 자연스러운 전환 (spring)

```tsx
import {spring, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';

const frame = useCurrentFrame();
const {fps} = useVideoConfig();

const scale = spring({
  frame,
  fps,
  config: {damping: 200, mass: 1, stiffness: 100}, // damping↑ = 오버슈트 없음
  durationInFrames: 30,
});
// spring 출력(0→1)을 실제 값으로 매핑
const size = interpolate(scale, [0, 1], [0.8, 1]);
```

규칙: 텍스트/카드 등장은 `spring`, 색·투명도 페이드는 `interpolate`. 오버슈트(bounce)는 UX 4원칙(자연스러움)상 금지 → `damping` 충분히 크게.

### 4. 타임라인 분할 (Sequence / Series)

```tsx
import {Sequence, Series} from 'remotion';

// from: 이 프레임부터 시작. 내부 컴포넌트의 useCurrentFrame 은 0부터 재시작.
<Sequence from={0} durationInFrames={60}><Intro /></Sequence>
<Sequence from={60} durationInFrames={90}><Body /></Sequence>

// 또는 자동 오프셋:
<Series>
  <Series.Sequence durationInFrames={60}><Intro /></Series.Sequence>
  <Series.Sequence durationInFrames={90} offset={-10}><Body /></Series.Sequence>
</Series>
```

### 5. 에셋: 오디오 / 비디오 / 이미지

```tsx
import {Audio, OffthreadVideo, Img, staticFile, useVideoConfig, interpolate, useCurrentFrame} from 'remotion';

const {durationInFrames} = useVideoConfig();
const frame = useCurrentFrame();

// 끝 30프레임 페이드아웃 — 결정론적 볼륨 램프
<Audio
  src={staticFile('bgm.mp3')}
  volume={(f) => interpolate(f, [durationInFrames - 30, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'})}
/>

// 렌더 시 반드시 OffthreadVideo (HTML <video>/<Video>는 프레임 누락/검은 화면)
<OffthreadVideo src={staticFile('clip.mp4')} />

// <img> 대신 <Img> — 디코드 완료 전 프레임이 캡처되는 것 방지
<Img src={staticFile('logo.png')} />
```

비동기 데이터(fetch/폰트)는 로드 완료까지 캡처를 지연:
```tsx
import {delayRender, continueRender} from 'remotion';
const [handle] = useState(() => delayRender('loading data'));
useEffect(() => { loadData().then(() => continueRender(handle)); }, [handle]);
```

### 6. 데이터 기반 batch 렌더 (서버사이드)

`render.mjs`:
```js
import {bundle} from '@remotion/bundler';
import {selectComposition, renderMedia} from '@remotion/renderer';
import path from 'node:path';

const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});

const rows = [{id: 1, title: 'A'}, {id: 2, title: 'B'}]; // DB/JSON 에서
for (const row of rows) {
  const composition = await selectComposition({serveUrl, id: 'MyVideo', inputProps: row});
  await renderMedia({
    composition,           // selectComposition 결과 (calculateMetadata 반영됨)
    serveUrl,
    codec: 'h264',
    outputLocation: `out/${row.id}.mp4`,
    inputProps: row,
    logLevel: 'info',      // v4: verbose/dumpBrowserLogs 폐기 → logLevel
    concurrency: null,     // null = CPU 코어 자동
  });
  console.log('rendered', row.id);
}
```
실행: `node render.mjs`. 코덱: `h264`(mp4 기본), `vp8`/`vp9`(webm), `gif`, `prores`.

### 7. 스케일 렌더 (Lambda) — 비용 게이트

긴 영상/대량 batch 만. **AWS 과금 → 사용자 확인 필수.** 먼저 1회 배포:
```bash
npx remotion lambda functions deploy
npx remotion lambda sites create src/index.ts --site-name my-video
```
코드에서 호출 + 진행률 폴링:
```tsx
import {renderMediaOnLambda, getRenderProgress} from '@remotion/lambda/client';

const {bucketName, renderId} = await renderMediaOnLambda({
  region: 'us-east-1',
  functionName: 'remotion-render-xxxx',
  serveUrl: 'https://...s3...amazonaws.com/sites/my-video',
  composition: 'MyVideo',
  inputProps: {title: 'Hi'},
  codec: 'h264',
});
let p;
do {
  p = await getRenderProgress({bucketName, renderId, functionName: 'remotion-render-xxxx', region: 'us-east-1'});
  if (p.fatalErrorEncountered) throw new Error(p.errors[0]?.message);
} while (!p.done);   // p.overallProgress: 0~1
console.log(p.outputFile); // S3 URL
```
CLI 대안: `npx remotion lambda render <serve-url> MyVideo out.mp4`

## Decision tables

애니메이션 선택:
| 원하는 것 | 도구 |
|---|---|
| 페이드/색/위치 선형 변화 | `interpolate` (+ easing) |
| 등장·팝업·자연스러운 settle | `spring` |
| 일정 구간만 표시 | `Sequence from/durationInFrames` |
| 장면 연속 배치 | `Series` |
| 반복(루프) | `frame % period` 또는 `<Loop>` |

렌더 경로 선택:
| 상황 | 방법 |
|---|---|
| 프리뷰·디버그 | `npx remotion studio` |
| 단건/소량, 로컬·CI | `npx remotion render` 또는 `renderMedia()` |
| 대량 batch | `renderMedia()` 루프 (`concurrency` 튜닝) |
| 초대량/긴 영상·동시성 | `renderMediaOnLambda()` (비용 확인) |

해상도/포맷:
| 용도 | width×height / codec |
|---|---|
| YouTube/가로 | 1920×1080 / h264 |
| Shorts/Reels/TikTok | 1080×1920 / h264 |
| 투명 오버레이 | webm `vp8` + `pixelFormat: 'yuva420p'` |
| 고품질 편집본 | `prores` |

## 성능

- **리마운트 금지**: 컴포넌트 key 를 frame 으로 바꾸지 말 것 → 매 프레임 마운트로 느려지고 깜빡임. 애니메이션은 항상 `useCurrentFrame()` 읽어서 스타일만 갱신.
- 무거운 계산은 `useMemo`, 인라인 객체/함수 prop 은 안정화. 큰 데이터 파싱은 컴포넌트 밖 또는 `calculateMetadata` 에서 1회.
- 렌더 동시성: `renderMedia({concurrency})` — 기본 null(자동). 메모리 부족 시 낮춤.
- 무거운 영상 소스는 `OffthreadVideo`(별도 프로세스 디코드)로. `<Video>`는 프리뷰 전용.
- 큰 PNG 시퀀스보다 코드 애니메이션이 가볍다. 폰트는 `@remotion/google-fonts` 로 결정론적 로드.

## Anti-patterns

- ❌ `interpolate` 에 `extrapolate: 'clamp'` 누락 → 값이 화면 밖으로 폭주
- ❌ 렌더에서 `<video>`/`<Video>` 사용 → 검은 화면·프레임 누락 (반드시 `OffthreadVideo`)
- ❌ `<img>` 사용 → 미디드코드 프레임 캡처 (반드시 `Img`)
- ❌ `setInterval`/`requestAnimationFrame`/`Date.now()` 로 애니메이션 → 비결정·렌더 불일치 (오직 `useCurrentFrame`)
- ❌ `Math.random()` 직접 호출 → 매 프레임 다른 값 = 깜빡임 (remotion `random(seed)` 사용)
- ❌ 비동기 데이터 로드에 `delayRender` 미사용 → 빈 화면 캡처
- ❌ `@remotion/*` 패키지 버전 불일치 → 런타임 크래시 (`npx remotion upgrade`)
- ❌ duration 을 코드와 무관하게 하드코딩 → 데이터 길어지면 영상 잘림 (`calculateMetadata`)
- ❌ bounce/elastic spring (오버슈트) → UX 4원칙 위반 (`damping` 키워 제거)
- ❌ Lambda 배포·렌더를 사용자 확인 없이 → AWS 과금 (CLAUDE.md §11 비용 게이트)

## 검증

```bash
# 1) 프리뷰 (Studio) — 브라우저에서 타임라인 스크럽으로 깜빡임·잘림 육안 확인
npx remotion studio

# 2) 단일 프레임 still 로 빠른 시각 검증
npx remotion still MyVideo out/frame.png --frame=15

# 3) 실제 렌더 (산출물 = 사용자 확인 가능한 MP4)
npx remotion render MyVideo out/video.mp4 --codec=h264

# 4) 패키지 버전 정합성
npx remotion versions
```

확인 포인트:
- [ ] 첫 프레임/마지막 프레임에서 요소가 화면 밖으로 안 튐 (clamp)
- [ ] 영상 길이 = 데이터 길이와 일치 (calculateMetadata)
- [ ] 오디오/비디오가 영상 끝까지 동기 (트림·페이드 정상)
- [ ] 두 번 렌더해도 바이트 동일 수준 (결정론 — random/Date 미사용)
- [ ] `npx remotion versions` 전 패키지 동일 버전

## Related skills

- `building-native-ui` — RN/Expo (Remotion 과 무관, 혼동 주의)
- `/make-pdf`, `office-docs` — 문서 산출물
- `deploy-configurator` — Lambda/AWS 자격증명·CI 렌더 파이프라인
- `simon-tdd` — render.mjs batch 로직 테스트
- `paid-api-guard` — Lambda 비용 가드
