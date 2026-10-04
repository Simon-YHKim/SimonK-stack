# Direction & Aesthetics — 6 방향 프리셋 + Distinctiveness 기법

> `design-system-keeper`의 참조. 방향별 토큰 프리셋과, 제네릭 AI 디자인을 벗어나는 distinctiveness 기법.
> 모든 프리셋은 **출발점**이다 — 프로젝트 anti-slop 규칙(루트 CLAUDE.md / 2nd-B DESIGN.md)이 충돌하면 그쪽이 이긴다.

## 1. 6 방향 프리셋

각 방향은 personality + 토큰 기본값. 한 프로젝트는 **하나만** 고른다.

### Precision & Density (관리도구·어드민)
- 느낌: 타이트·모노크롬·기술적. 정보 밀도 높음.
- spacing-base 4px, 좁은 scale(4,8,12,16). radius sm(4~6). 
- color: 거의 무채(slate tinted-neutral) + accent 1. depth=테두리 위주(그림자 최소).
- type: 모노 또는 중성 산세리프, 작은 본문(13~14px), 촘촘한 line-height(1.4).

### Warmth & Approachability (소비자 앱)
- 느낌: 여백 넉넉·부드러움·따뜻함.
- spacing 넉넉(16,24,32). radius md~lg(8~12).
- color: warm tinted-neutral + 부드러운 accent. depth=은은한 그림자/레이어.
- type: 친근한 산세리프(한국어 Pretendard), 큰 본문(15~16px), 여유 line-height(1.6).

### Sophistication & Trust (엔터프라이즈)
- 느낌: 차분·신뢰·깊이 있는 레이어.
- spacing 정연. radius md. color: cool slate + 절제된 accent. depth=다층 레이어/미묘한 그림자.
- type: 격조 있는 페어링(display + 본문), 안정적 위계.

### Boldness & Clarity (데이터 대시보드)
- 느낌: 고대비·극적·즉시 읽힘.
- color: 강한 figure/ground 대비 + 의미 고정 시그널색(절제). depth=대비로.
- type: 굵은 위계, 큰 숫자/지표.

### Utility & Function (개발자 도구)
- 느낌: 절제된 밀도·기능 우선.
- 모노 톤, 모노 폰트 옵션, 장식 0. radius sm. accent 1(상태색).

### Data & Analysis (분석·BI)
- 느낌: 차트 최적화·중립 배경.
- 중립 배경 + 데이터에만 색. 범주형 팔레트는 의미 고정·색맹 안전. type=tabular numerals.

## 2. Distinctiveness 기법 (제네릭 AI 탈피)

`frontend-design` 원칙. **의도가 핵심, 강도가 아님.**

- **타이포로 차별화**: 흔한 기본 폰트(Inter/Roboto/Poppins/Montserrat 등) 회피. 개성 있는 display + 읽기 좋은 본문 페어링. 한국어는 Pretendard 기본, display 대안 별도.
- **지배색 + accent**: 색을 균등 분산하지 말고 한 색이 지배하고 accent를 전략적으로.
- **구성으로 차별화**: 비대칭·겹침·대각선·그리드 깨기. 또는 의도적 여백/밀도. (제약 프로젝트에선 이게 그라데이션보다 안전한 distinctiveness 수단.)
- **깊이/분위기**: 테두리·레이어·미묘한 그림자·(허용 시)그레인. 평면 단색 탈피.
- **시그니처 모먼트 1개**: 페이지 로드 스태거, 한 곳의 특별한 전환 등 "기억에 남을 단 하나". 흩뿌리지 말 것.

## 3. 제네릭 AI 디자인 = 피해야 할 것

- 흔한 폰트(Inter 등) · 보라-on-화이트 그라데이션 · 쿠키커터 카드 그리드 · 맥락 없는 장식 · 이모지 아이콘 · 4색+ 멀티컬러 · pill 버튼 남발 · bounce/elastic 모션.

## 4. 제약 프로젝트(2nd-B 등)에서의 distinctiveness

그라데이션·맥시멀리즘이 금지된 곳에서 개성을 내는 법:
1. **타이포 선택**(예: NeoDunggeunmo 픽셀 폰트) — 그 자체가 강한 정체성.
2. **여백·리듬·정렬 규율** — 절제가 곧 스타일.
3. **의미 고정 시그널색**(accent budget) — 일관성이 신뢰를 만든다.
4. **시그니처 모먼트 1개**(예: 한 곳의 "뽁" overshoot) — 나머지는 무모션.
5. **일러스트/마스코트 통일**(예: 픽셀 주민 6종) — 자산 일관성이 브랜드.

→ 결론: 제약은 distinctiveness의 적이 아니라 **방향**이다. maximalism이 막히면 typography·composition·consistency로 낸다.
