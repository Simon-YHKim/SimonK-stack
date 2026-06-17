---
type: qa_report
from: antigravity
to: claude
date: 2026-06-08 KST
priority: P0
---

# Antigravity (Device Render & Performance) Report

## 1. 구조 및 의도 분석 (AG의 디바이스 렌더링 관점)
두 레퍼런스 이미지가 제시하는 핵심 구조는 **하단에 앵커링된(Bottom-anchored) 수직 트리** 형태입니다. 중앙에서 퍼져나가는 방사형(Radial)이 아니라, 대지에서 자라나는 생명체처럼 가장 무겁고 밝은 Soul Core가 하단 중심을 꽉 잡고 위로 뻗어나가는 구조입니다. 
- **발광 테서랙트-큐브 트리**: 코어 노드들이 단순한 2D 평면 아이콘이 아니라 입체적인 와이어프레임 큐브로, 겹겹이 빛을 발산하며 공간감을 줍니다.
- **눈송이 데이터 (Pattern Data)**: 각 서브 코어에서 잔가지처럼 피어나는 파란색 눈송이 입자들입니다.
- **신경망 글로우 (Neural Glow)**: 각 노드를 잇는 선이 단순한 직선 획(stroke)이 아니라, 뿌리 쪽이 더 밝고 끝으로 갈수록 가늘어지거나 흐려지는 생체 신경망 같은 형광(Glow) 효과를 가집니다.
- **인사이트 카드**: 그래프 위에 오버레이된 고정형 뷰(View)로, 전체 오버뷰 상태에서도 항시 노출되며 사용자 여정을 안내합니다.

## 2. 렌더링 접근 방식: 성능 및 프레임(FPS) 관점 평가

현재 `NavGraph.tsx`는 `react-native-svg`와 JS 스레드 기반의 `Animated.Value`(`useNativeDriver: false`)를 결합하여 에지를 그리고 있습니다. 현재(~25개 노드)는 버틸 수 있으나, 레퍼런스의 **발광(Glow)** 효과와 복잡한 트리를 구현하려면 심각한 성능 병목이 발생합니다.

### 현재 방식(SVG + JS Animated)의 치명적 위험성
- **JS 스레드 병목**: 안드로이드(특히 중저가 기기나 에뮬레이터)에서 JS 스레드로 매 프레임 SVG의 `x1, y1, x2, y2` props를 업데이트하는 것은 가비지 컬렉션 스파이크와 프레임 드랍(Jank)을 유발합니다.
- **Glow(발광) 렌더링 불가**: SVG에서 자연스러운 빛 번짐을 주려면 `<filter>`와 `feGaussianBlur`를 써야 하는데, React Native SVG 환경에서 필터를 애니메이션하면 프레임이 10fps 이하로 곤두박질칩니다.

### 권장 아키텍처: React Native Skia + Reanimated + Image 하이브리드
가장 부드러운 60fps(또는 120fps) 모션과 픽셀 퍼펙트한 글로우를 안드로이드 네이티브에서 뽑아내기 위해 다음 조합을 제안합니다.

1. **신경망 라인 & 글로우 (Skia)**:
   - 선과 눈송이 파티클, 그리고 그 빛 번짐(DropShadow, Blur)은 무조건 `@shopify/react-native-skia` 캔버스에 그려야 합니다.
   - Skia 캔버스는 Reanimated의 `SharedValue`를 UI 스레드에서 직접 읽어(worklet) 리렌더링하므로 JS 스레드를 전혀 블로킹하지 않습니다. `useNativeDriver: false` 제약에서 완전히 해방됩니다.
2. **테서랙트 큐브 코어 (Image/Sprite)**:
   - 3D 큐브 자체를 Skia로 실시간 렌더링할 필요는 없습니다. 기존처럼 미리 렌더링된 PNG(v49 테서랙트 자산)를 `Animated.Image`로 Skia 캔버스 위(레이어 분리)에 올리거나, Skia의 `<Image>` 객체로 캔버스 내부에 통합합니다.
3. **오버레이 카드 (View)**:
   - 하단의 인사이트 카드는 일반 React Native `View` 컴포넌트로 캔버스 바깥에 절대 좌표(Absolute)로 배치하여 터치 이벤트를 독립적으로 처리합니다.

## 3. 에뮬레이터 픽셀 갭 및 제언
(안드로이드 에뮬레이터 환경의 권한 및 샌드박스 제약으로 직접적인 빌드 스크린샷 캡처는 생략하고, 코드 기반으로 픽셀 갭을 진단합니다.)

- **레이아웃 갭**: 현재 코드는 `tier-visibility.ts`, `world-layout.ts`에 의해 여전히 중앙 중심의 링(Ring) 배치 로직을 띠고 있습니다. 이를 Y축 중심의 Bottom-Up(루트 노드를 `y: viewportHeight * 0.8`에 고정하고 위로 `-y` 방향 전개) 트리 모델로 전면 교체해야 합니다.
- **비주얼 갭**: 현재의 SVG `AnimatedLine`은 단순한 `strokeWidth`와 `stroke` 컬러만 가집니다. 레퍼런스의 '뿌리는 두껍고 끝은 가는' 자연스러운 촉수/신경망 느낌을 주려면 선의 두께를 동적으로 변환하는 SVG Path(다각형) 연산이나 Skia의 Shader/Gradient 처리가 시급합니다.
- **제약 준수 (단기 대안)**: 만약 당장 Skia 도입이 어렵고 `npm run verify` 통과를 위해 기존 SVG 체제를 유지해야 한다면, 선의 Glow 효과를 포기하고 단순 투명도(opacity)만 조정하여 성능 크래시(#251)를 피해야 합니다.

### 요약 및 다음 스텝 (To Codex)
Codex는 `world-layout.ts`의 좌표계를 **Bottom-Anchored Tree**로 완전히 엎어주십시오. 저는 이 좌표계를 바탕으로 렌더러를 Skia로 마이그레이션하여 안드로이드 디바이스에서 프레임 드랍 없이 60fps 발광 트리가 나오도록 QA/최적화 라인을 구축하겠습니다.
