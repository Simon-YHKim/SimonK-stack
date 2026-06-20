# Codex 방향 제안: 메인 그래프를 수직 크리스탈 트리로 재설계

작성: 2026-06-08 KST  
범위: 방향 제안만. `E:/2ndB` 체크아웃은 읽기만 했고 수정하지 않았음.

## 1. 레퍼런스 직접 판독

두 이미지는 "그래프를 예쁘게 꾸민 원형 네트워크"가 아니라, 하단 Soul Core에서 위로 자라는 발광 크리스탈 생장 구조다.

REF1의 첫인상은 하단 중앙의 큰 Soul Core가 뿌리이자 에너지 원천이고, 거기서 여러 줄기의 신경 링크가 위로 뻗어 5개의 Pattern Core 큐브와 다수의 눈송이 데이터로 갈라진다는 점이다. 화면의 중심은 기하학적 중앙이 아니라 하단 루트다. 큰 큐브는 3D 와이어프레임 오브젝트이고, 작은 코어들도 같은 큐브 언어를 공유한다. 데이터는 점이나 로그북이 아니라 파란 6각 눈송이 결정이며, 링크는 얇은 시안/민트 신경선이다. 하단 2개 카드는 그래프를 가리지 않는 "상태 번역 레이어"다. 첫 카드는 SecondB가 최근 변화와 부족한 영역을 말하고, 둘째 카드는 특정 코어/조각을 다음 탐색 대상으로 제안한다.

REF2는 같은 문법을 한 코어에 적용한 드릴다운이다. 초록 Growth Core가 하단 루트 역할을 맡고, 그 코어의 데이터 눈송이들이 위쪽으로 가지를 친다. 즉 드릴다운도 원형 확대가 아니라 "선택한 코어를 임시 루트로 삼은 작은 수직 트리"다. 하단 2개 카드는 캐릭터 설명 카드와 선택 데이터 카드로 바뀐다.

Claude 분석과 큰 차이는 없다. 다만 내가 본 이미지 기준으로는 "정확히 중앙 수직 축만"이 아니라, 하단 루트에서 위로 올라가되 좌우 가지가 비대칭으로 흔들리는 자연스러운 트리다. 좌표 모델은 엄격한 원형/방사형보다 trunk + branch + twig 모델이어야 한다.

## 2. 현재 코드 대비 가장 큰 갭

가장 큰 갭은 아트 자산의 유무가 아니라 좌표 모델이다.

- `src/components/graph/world-layout.ts`는 `WORLD_CENTER`, `RING2`, `RING3`, `RING4` 중심의 원형 섹터 모델이다. `worldMenuPositions()`는 tier-2를 중심 주위 링에 균등 배치하고, `worldDataPositions()`는 각 도메인 섹터 바깥 링에 데이터를 뿌린다. 이 구조는 레퍼런스의 "하단 뿌리에서 위로 자람"과 정반대다.
- `src/components/graph/NavGraph.tsx`도 같은 가정을 강화한다. `positions`는 `worldToScreen()`으로 원형 월드를 화면 중앙에 맞추고, center node는 edge 계산에서 `{ x: cx, y: cy }`로 특수 처리된다. Soul Core를 하단 루트로 내리려면 `world-layout.ts`만 바꾸면 안 되고, center 위치 특수 처리도 제거해야 한다.
- 드릴다운도 아직 루트 트리가 아니다. `NavGraph.tsx`의 `drilldownCoreCenter`는 대략 화면 42-56% y에 놓이고, `renderDataPositions`는 `angle = -0.84π .. -0.16π`의 부채꼴 배치다. REF2처럼 코어가 하단 루트가 되고 데이터가 위로 가지치는 모델로 바꿔야 한다.
- 코어 렌더는 레퍼런스에 가까운 PNG가 이미 있지만 조립 방식이 덜 명확하다. `IslandArt`가 `FinalCoreArt`를 호출하고, `FinalCoreArt`의 기본 variant는 `v10`이다. 레퍼런스는 `public/assets/cosmic-pixel-v4-tesseract-v49/app_256`의 256px 큐브와 거의 같은 언어다. 메인 그래프는 v49를 명시적으로 써야 한다.
- `FinalPatternDataSnowflakeArt`는 이미 좋지만 overview에서 tier-4는 기본적으로 zoom bucket 2에서만 강하게 드러난다. 레퍼런스 overview는 데이터 눈송이가 그래프의 기본 구성요소로 항상 보인다.
- 링크는 현재 직선 `Svg Line` 두 겹 + dash flow다. 기능은 맞지만 trunk/branch/twig 계층과 "뿌리 근처가 더 밝다"는 거리 문법이 없다.
- 하단 2 카드는 `src/app/index.tsx`에 비슷한 구조가 이미 있다. 하지만 `NavGraph`의 선택/드릴다운 상태와 별도이고, 그래프 좌표가 카드 높이를 고려하지 않는다. 레퍼런스에서는 카드가 그래프 레이아웃의 예약 영역이다.

## 3. 구현 방향 요약

기존 데이터 분류, 탭 라우팅, bottom sheet, reduced-motion, SVG line의 `useNativeDriver:false` 제약은 유지한다. 바꿀 것은 그래프의 "공간 문법"이다.

1. 원형 `world-layout`을 메인 렌더에서 빼고, 새 순수 좌표 모델 `tree-layout.ts`를 추가한다.
2. Soul Core와 Pattern Core를 `IslandArt` 의미가 아니라 `TesseractCoreNode` 의미로 직접 렌더한다.
3. overview에서도 대표 데이터 눈송이를 항상 보여주고, zoom은 "더 많은 데이터/관계선 공개" 용도로 낮춘다.
4. edge는 parent-child 선이 아니라 trunk/branch/twig 역할을 가진 발광 세그먼트로 그린다.
5. 하단 2 카드를 그래프 레이아웃과 결합해 graph frame의 하단을 명확히 예약한다.

## 4. 수직 트리 좌표 모델 제안

새 파일: `src/components/graph/tree-layout.ts`

핵심 타입:

```ts
export interface TreeFrame {
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface TreeNodePosition {
  x: number;
  y: number;
  angle: number;
  depth: number;
  branchId: string;
}

export type TreeEdgeRole = "root" | "trunk" | "branch" | "twig" | "related";

export interface TreeEdgeDef {
  fromId: string;
  toId: string;
  key: string;
  role: TreeEdgeRole;
  opacity: number;
  points?: Array<{ x: number; y: number }>;
}
```

프레임 계산:

- `graphFrame(width, height, bottomReserved, topReserved)`를 둔다.
- 하단 카드 2장의 높이와 safe-area를 `bottomReserved`로 받아, 트리의 `bottom`이 카드 위에서 끝나게 한다.
- Soul Core center는 `frame.x + frame.width * 0.5`, `frame.y + frame.height * 0.80~0.84`.
- Pattern Core는 Soul Core 위쪽 5개 고정 앵커에 둔다. 레퍼런스에 맞춰 완전 대칭보다 약한 비대칭을 허용한다.

추천 overview 앵커:

```ts
const CORE_ANCHORS = {
  records:   { x: 0.50, y: 0.20 }, // 상단 trunk 끝, narrative/teal-brown 계열
  knowledge: { x: 0.28, y: 0.42 }, // 좌상 white/silver
  taste:     { x: 0.72, y: 0.40 }, // 우상 violet
  relation:  { x: 0.30, y: 0.64 }, // 좌하 rose
  work:      { x: 0.72, y: 0.66 }, // 우하 green, REF2 Growth와 연결
} as const;
```

데이터 배치:

- `treeDataPositions(dataNodes, corePositions, frame, cap)`는 각 parent core 주변에 upward-biased twig를 만든다.
- 각 코어마다 데이터는 parent에서 더 위쪽으로 2-3개의 짧은 stem을 만든 뒤 stem 주변에 눈송이를 붙인다.
- `seeded(id, salt)`는 유지해 결정성을 보장한다.
- 데이터가 많으면 overview는 parent별 최대 6개, 전체 최대 32개만 항상 보이고 zoom bucket 2에서 나머지를 추가한다.

드릴다운 배치:

- `treeDrilldownPositions(coreId, dataNodes, frame)`를 따로 둔다.
- 코어 center는 `frame.x + frame.width * 0.26`, `frame.y + frame.height * 0.70` 정도로 하단 좌측 루트에 둔다. REF2처럼 데이터 가지가 우상향으로 올라갈 공간을 만든다.
- 데이터는 1개의 main stem과 2개의 side stem으로 나눠 `x`가 우측으로 증가하고 `y`가 위로 감소하게 배치한다.
- selected data는 stem 중간 또는 카드와 대응되는 대표 위치에 두고 halo를 강하게 준다.

테스트:

- `src/components/graph/__tests__/tree-layout.test.ts` 추가.
- Soul Core y가 모든 Pattern Core y보다 크다.
- 각 데이터 y는 parent y보다 작거나, 최소한 parent 주변에서 위쪽 비율이 70% 이상이다.
- 모든 노드가 frame bounds 안에 있고, 같은 입력은 같은 좌표를 반환한다.
- drilldown core가 데이터보다 아래에 있고, 선택 데이터 id가 안정적으로 유지된다.

## 5. NavGraph 파일 수준 변경안

대상: `src/components/graph/NavGraph.tsx`

좌표 계산:

- 기존 import `worldMenuPositions`, `worldDataPositions`, `worldToScreen`, `sectorFocus`를 메인 overview 렌더에서 제거하거나 feature flag 뒤로 보낸다.
- 새 import:

```ts
import {
  graphTreeFrame,
  treeMenuPositions,
  treeDataPositions,
  treeEdges,
  treeDrilldownPositions,
} from "./tree-layout";
```

- `positions`는 `treeMenuPositions(MENU_NODES, CENTER_NODE.id, frame)` 결과를 사용한다.
- center node도 `renderPositions.get(CENTER_NODE.id)`로 그린다. 현재 edge 계산의 `{ x: cx, y: cy }` 특수 처리는 제거한다.
- `focusWorldPoint()`와 `sectorFocus()`는 원형 섹터 확대용이므로, tree에서는 `focusTreeNode(id)`로 대체한다. 탭 시 카메라는 노드 중심을 카드 위의 여백으로 옮기는 정도면 충분하다.

edge 생성:

- 현재 `edges` useMemo는 parent-child + relatedness만 만든다.
- 새 구조에서는 `treeEdges({ menu, menuPositions, dataPositions, relatedEdges })`가 `TreeEdgeDef`를 반환하게 한다.
- `points`가 있으면 segment 단위로 여러 `AnimatedLine`을 그린다. 이러면 `Svg Path d` 애니메이션 없이도 trunk가 꺾이는 느낌을 만들 수 있고, 현재 `useNativeDriver:false` 제약과도 맞다.

spawn 순서:

- 현재 tier 기반 랜덤 spawn은 레퍼런스의 생장감을 흐린다.
- `treeSpawnOrder(positions)`를 두고 y가 큰 순서, 즉 아래에서 위로 spawn한다. 같은 branch 안에서는 parent가 먼저, 데이터는 parent 이후.
- bounce/elastic은 쓰지 않고 기존 cubic timing을 유지한다.

데이터 visibility:

- `tierVisibility()`는 유지하되 의미를 바꾼다.
- overview bucket 0에서도 `treeDataPositions(..., overviewCap)`의 대표 눈송이는 보인다.
- bucket 1/2에서 더 많은 데이터와 relatedness edge를 추가한다.

CrewLayer:

- 레퍼런스에는 메인 그래프 안에서 걸어다니는 주민이 없다. 카드의 캐릭터 아바타가 인격 레이어를 담당한다.
- 1차 프로토에서는 `CrewLayer`와 `CharacterPathLayer`를 tree 모드에서 끄거나 opacity를 크게 낮추는 편이 낫다. 그렇지 않으면 수직 크리스탈 트리의 정체성이 다시 마을/순찰 UX로 읽힌다.

## 6. 큐브 코어 렌더 조립

대상: `src/components/art/SoulcoreFinalArt.tsx`, `src/components/graph/NavGraph.tsx`

현재 `FinalCoreArt`는 충분히 가까운 PNG를 갖고 있다. 문제는 graph node assembly다.

제안:

```ts
export function TesseractCoreNode({
  id,
  size,
  selected,
  focused,
  variant = "v49",
}: {
  id: FinalCoreId;
  size: number;
  selected?: boolean;
  focused?: boolean;
  variant?: AssetVariant;
}) {
  // halo/back-glow + FinalCoreArt + subtle inner pulse
}
```

세부:

- 메인 그래프의 Soul Core와 Pattern Core는 `variant="v49"`를 명시한다. 레퍼런스의 작은 큐브는 v49 256 세트와 가장 직접적으로 맞는다.
- `FinalCoreArt`는 그대로 재사용하되 `LivingAsset` preset은 유지한다.
- wrapper에만 halo를 둔다. 사각 카드나 원형 backing은 두지 않는다.
- Soul Core size는 현재 112보다 커야 한다. 모바일 REF 기준 graph 영역에서 약 150-170px가 적절하다. Pattern Core는 70-90px, 데이터 눈송이는 34-44px.
- id 매핑을 명시한다.

```ts
const FINAL_CORE_FOR_NODE = {
  core: "core",
  work: "work_growth",
  relation: "relationship",
  knowledge: "knowledge",
  records: "records",
  taste: "inspiration",
} satisfies Record<string, FinalCoreId>;
```

`IslandArt`는 다른 화면 호환을 위해 유지하되, `NavGraph` tree mode에서는 `IslandArt`를 우회하고 `TesseractCoreNode`를 직접 호출하는 편이 명확하다.

## 7. 눈송이 데이터와 신경 글로우 링크

눈송이:

- `FinalPatternDataSnowflakeArt`는 유지한다.
- overview에서 tier-3 menu node를 눈송이로 렌더하는 현재 방식은 혼란스럽다. 레퍼런스에서 눈송이는 saved data이고 Pattern Core는 큐브다. 따라서 `MENU_NODES` tier-3를 overview tree에서는 숨기거나, zoom 이후의 보조 데이터로만 약하게 둔다.
- 실제 `dataNodes`가 없을 때도 레퍼런스형 preview가 필요한지 제품 결정이 필요하다. 데이터 진실성을 지키려면 empty 상태에서는 3-5개의 faint placeholder snowflake 대신 "첫 조각을 남기면 가지가 켜진다" 카드만 보이게 하는 것이 안전하다.

링크:

- `src/lib/graph/pattern-link.ts`에 role 기반 스타일을 추가한다.

```ts
export function patternLinkTreeStyle(role: TreeEdgeRole, proximity: number) {
  // root/trunk는 두껍고 밝게, branch는 중간, twig/related는 얇고 차갑게
}
```

- 렌더는 3겹이 좋다.
  - wide underglow: strokeWidth 6-10, opacity 낮음, 민트/시안.
  - core line: strokeWidth 1.5-3, opacity 높음.
  - flow dash: 현재 `linkSignal`을 재사용하되 root/trunk가 더 느리고 안정적으로 흐르게 한다.
- 뿌리 근처일수록 밝게: edge role + `from/to`의 y 거리로 proximity를 계산한다. Soul Core에서 가까운 trunk는 가장 밝고, 데이터 twig는 얇고 차갑게 간다.

## 8. 하단 2 인사이트 카드

대상: `src/app/index.tsx`, 새 `src/components/graph/GraphInsightCards.tsx` 또는 `NavGraph` 내부 overlay

현재 `index.tsx` 469-521 부근의 `insightCardStack`은 레퍼런스와 매우 가깝다. 그러나 위치만 겹친 overlay라서 그래프 좌표 모델과 연결되어 있지 않다.

제안:

- `GraphInsightCards`로 추출하고, 그 높이를 `NavGraph`에 `bottomReserved`로 전달한다.
- overview 카드:
  - 카드 1: SecondB sprite + 최근 변화 bullet 2개. 실제 데이터가 있으면 최근 parent core와 부족한 core를 계산한다.
  - 카드 2: featured core 큐브 아이콘 `TesseractCoreNode size={56}` + 가장 최근/대표 조각 설명.
- drilldown 카드:
  - 카드 1: core worker `WorkerSprite` + `navGraph.drilldown.coreIntro.${coreId}`.
  - 카드 2: selected data `FinalPatternDataSnowflakeArt` + title/summary/tags.
- `NodeSheet`/`DataNodeSheet`/`DrilldownSheet`는 카드와 중복된다. 1차에서는 기존 sheet를 유지하되 tree mode의 기본 하단 카드는 항상 노출하고, 탭 후 상세 sheet는 더 작은 secondary action으로 제한하는 것이 안전하다.

## 9. 단계별 작업안

1차 프로토:

- `tree-layout.ts`와 테스트 추가.
- `NavGraph`에 `USE_TREE_GRAPH` 같은 임시 상수/feature flag를 두고 tree 좌표만 연결.
- center special-case 제거: center도 positions map에서 렌더/edge 계산.
- overview에서 core 5개 + data 대표 snowflake + trunk/branch/twig edge가 보이게 한다.
- graph core art를 v49로 고정한 `TesseractCoreNode`를 사용한다.

2차 정리:

- `index.tsx`의 2 카드 계산을 `GraphInsightCards`로 추출하고, card height를 graph frame에 반영한다.
- drilldown radial fan을 `treeDrilldownPositions()`로 교체한다.
- `pattern-link.ts`에 role 기반 스타일과 테스트를 추가한다.

3차 polish:

- spawn order를 bottom-up 생장 순서로 변경.
- CrewLayer tree mode 비활성 또는 별도 낮은 opacity 처리.
- overview/zoom tier visibility 의미 재조정.
- `npm run verify`와 모바일/웹 screenshot으로 카드-그래프 overlap, asset transparency, frame rate 확인.

## 10. 결론

Simon이 지적한 핵심은 "조각은 맞는데 구조와 의도가 다르다"는 것이다. 현재 구현은 여전히 중앙 원형 마을/섹터 그래프이고, 레퍼런스는 하단 루트에서 위로 자라는 크리스탈 트리다. 따라서 이번 redesign의 첫 단추는 새 PNG 추가가 아니라 `world-layout` 계열의 원형 좌표 가정을 끊고, Soul Core를 하단 anchor로 삼는 tree coordinate system을 넣는 것이다.

가장 실용적인 경로는 새 `tree-layout.ts`를 병렬로 만들고 `NavGraph`에서 feature flag로 연결하는 방식이다. 그러면 기존 라우팅, 데이터 분류, bottom sheet, relatedness 로직은 보존하면서도 화면의 정체성을 레퍼런스에 맞게 바꿀 수 있다.
