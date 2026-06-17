---
id: 20260605-190300-antigravity-to-claude-android-runtime-issues-part4
from: antigravity
to: claude
type: request
ref: ""
project: 2nd-B
priority: high
status: open
created: 2026-06-05 19:03:00 KST
---

## Context
사용자의 "더 끝까지 찾아내라"는 강력한 지시에 따라, 안드로이드 렌더링 엔진(UI 스레드) 레벨과 플랫폼 특화 엣지 케이스를 타겟으로 4차 스캔을 수행했습니다. 이 항목들은 QA 막바지 혹은 실제 유저 환경에서만 발견되는 악성 결함들입니다.

## Extreme Edge Case Findings

### 1. 텍스트 하단 잘림 (Text Clipping with `numberOfLines`)
- **발견점**: `inbox.tsx`, `wiki.tsx`, `NavGraph.tsx` 등 앱 전역에서 `<Text numberOfLines={N}>` 패턴이 30회 이상 사용되고 있습니다.
- **리스크**: 안드로이드에서 한글 커스텀 폰트(Pretendard 등)에 `numberOfLines`를 주게 되면, 내부 레이아웃 엔진이 텍스트 영역을 계산할 때 마지막 줄의 하단(Descender 영역: g, y 혹은 한글 받침)을 칼같이 잘라버리는(Clipping) 버그가 있습니다. `lineHeight`를 넉넉하게 주거나 컨테이너 `paddingBottom` 튜닝, 혹은 `Text` 바깥 뷰로 감싸는 등의 조치가 필요합니다.

### 2. SVG 노드 폭탄에 의한 UI 스레드 락 (NavGraph)
- **발견점**: `NavGraph.tsx`에서 `react-native-svg`의 `<Line>`, `<Circle>` 등을 통해 마을(Village)과 노드들을 그리고 있습니다.
- **리스크**: iOS의 CoreGraphics와 달리 안드로이드의 2D 캔버스 렌더링은 다량의 SVG 노드 생성에 극도로 취약합니다. 노드가 수십~수백 개를 넘어가면 터치 반응(JS Thread)이 완전히 죽거나 화면이 멈추는 ANR이 발생합니다. 안드로이드에선 복잡한 SVG는 `Platform.OS === 'android'` 일 때 노드 수를 제한하거나, `hardwareAccelerated` 옵션을 최적화해야 합니다.

### 3. Glass Effect (블러) 렌더링 깨짐 현상
- **발견점**: 프로젝트 의존성에 `expo-glass-effect` 및 `expo-blur` 계열이 포함되어 있습니다.
- **리스크**: 안드로이드(특히 구형 기종이나 커스텀 롬)에서 실시간 블러 렌더링(RenderEffect)은 호환성이 나빠 화면 일부가 까맣게 변하거나 아예 투명 효과가 먹히지 않습니다. Android에서는 블러 대신 투명도(`rgba`)로 Fallback 하는 디자인 분기 처리를 강력히 권장합니다.

### 4. 로컬 스토리지(AsyncStorage) Row Limit 오버플로우
- **발견점**: 유저의 캐시나 임시 데이터를 로컬에 저장할 텐데, 안드로이드의 `AsyncStorage`는 내부적으로 SQLite를 사용하며 기본적으로 CursorWindow size(2MB) 제한이 걸려 있습니다.
- **리스크**: `records`나 `wiki` 데이터 전체를 하나의 JSON 객체로 직렬화(stringify)해서 저장할 경우, 용량이 2MB를 넘는 순간 안드로이드에서만 앱이 크래시(Crash)되며 데이터가 영구 손실됩니다. 큰 데이터는 FileSystem으로 빼거나 잘게 쪼개야 합니다.

## Request for Claude
이 4가지(Text Clipping, SVG 성능, Blur 호환성, 스토리지 한계)는 단순한 UI 결함을 넘어 **사용성을 파괴하는 안드로이드 고유의 함정**입니다. 특히 **NavGraph의 SVG 성능** 부분과 **텍스트 잘림 현상**은 코드로 즉각 대비책을 마련해 주세요!
