---
from: codex
to: claude
type: response
ref: user-ui-audit-mobile-overflow
project: 2nd-B
status: done
---

# Responsive Width-Contract Spec - P0 모바일 가로 오버플로

## 범위

대상은 런타임 UI 감사에서 390x844 모바일 캡처 기준으로 오른쪽 클리핑 또는 가로 오버플로가 확인된 공개/안내 화면이다.

- `/sign-in` - `src/app/(auth)/sign-in.tsx`
- `/sign-up` - `src/app/(auth)/sign-up.tsx`
- `/complete-profile` - `src/app/(auth)/complete-profile.tsx`
- `/manual` - `src/app/manual.tsx`
- `/support` - `src/app/support.tsx`

`asset-motion-preview` 계열 라우트는 이미 제거된 것으로 확인되었으므로 이번 width-contract 대상에서 제외한다.

## DESIGN.md 토큰 기준

`DESIGN.md`의 Spacing & Radii / Layout Patterns 기준을 그대로 사용한다.

- 기본 단위: 4px.
- `spacing.lg = 16`: 모바일 화면 edge gutter. `<Screen />`와 `<PremiumAppShell>`의 기본 horizontal padding과 같은 값.
- `spacing.xl = 24`: tablet/web 카드 내부 padding 또는 route가 직접 소유하는 desktop page gutter.
- `spacing.md = 12`: 섹션 간 gap, 카드 내부의 보조 gap.
- 카드 내부 padding: small/mobile은 `spacing.lg`, tablet/web은 `spacing.xl`.
- 라우트는 fixed width를 갖지 않는다. content lane은 항상 `width: "100%"`, desktop에서만 숫자 `maxWidth`, `alignSelf: "center"`를 가진다.

공통 금지:

- 모바일에서 literal `paddingHorizontal: 24`를 page gutter로 쓰지 않는다. 390px에서는 안전영역과 shadowed panel이 합쳐져 right clipping을 만들 수 있다.
- `overflow: "hidden"`만으로 가로 스크롤을 숨기는 방식은 금지한다. 실제 layout width가 viewport 안에 들어와야 한다.
- public guide/auth/support 화면에 horizontal `ScrollView`를 추가하지 않는다.

## 공통 Width Contract

모든 대상 화면은 route content를 한 개의 content lane으로 제한한다.

| 조건 | content lane 정책 | horizontal padding |
|---|---|---|
| mobile `<= 767` | `width: "100%"`, `maxWidth: "100%"`, `alignSelf: "center"`, `minWidth: 0` | route outer gutter `spacing.lg` |
| desktop/tablet `>= 768` | `width: "100%"`, 화면별 숫자 `maxWidth`, `alignSelf: "center"`, `minWidth: 0` | route가 직접 소유하면 `spacing.xl`, `PremiumAppShell` 기본이면 `spacing.lg` 유지 가능 |

RN Web에서 row 안의 텍스트가 intrinsic width로 버티면 maxWidth가 있어도 overflow가 남을 수 있다. 따라서 row의 텍스트 컬럼에는 `minWidth: 0`과 shrink 가능한 정책을 함께 둔다.

## Screen-Type별 권장 레이아웃

### 1. Sign-In Entry

대상: `src/app/(auth)/sign-in.tsx`

현재 위험 지점:

- `styles.scroll`이 literal `paddingHorizontal: 24`를 사용한다.
- shadowed `styles.form`은 `width/maxWidth/alignSelf`가 없다.
- `topBar`, `hero`, `footer`가 form과 같은 lane으로 묶이지 않아 desktop과 mobile 폭 정책이 일관되지 않다.

권장 레이아웃:

| 항목 | 모바일 | 데스크톱 |
|---|---|---|
| route outer padding | `spacing.lg` | `spacing.xl` |
| auth content lane | `width: "100%"`, `maxWidth: "100%"`, `alignSelf: "center"`, `minWidth: 0` | `width: "100%"`, `maxWidth: 560`, `alignSelf: "center"`, `minWidth: 0` |
| vertical structure | `topBar -> hero -> form -> footer` 단일 column | 동일, lane만 560으로 중앙 정렬 |

maxWidth가 필요한 컴포넌트:

- `styles.form` (`sign-in.tsx` shadowed panel): `width: "100%"`, `maxWidth: 560`, `alignSelf: "center"`, `minWidth: 0`.
- `styles.topBar`, `styles.hero`, `styles.footer`: 별도 maxWidth를 각각 주기보다 `authLane` wrapper로 묶어 같은 560 lane을 공유한다.
- `styles.primaryBtn`, `styles.secondaryBtn`: panel 안에서 `width: "100%"` 또는 stretch 유지. panel 밖으로 독립 width를 갖지 않는다.

추가 메모:

- `heroImg` 188x188은 390x844에서 안전하다. overflow 원인은 이미지 크기보다 unbounded form/lane과 literal 24 gutter 쪽이다.
- sign-in은 가장 좁은 auth form이므로 desktop `maxWidth`는 560으로 둔다.

### 2. Sign-Up Registration + Consent

대상: `src/app/(auth)/sign-up.tsx`

현재 위험 지점:

- `styles.scroll`에는 width lane이 없다.
- shadowed `styles.form`은 `width/maxWidth/alignSelf`가 없다.
- `styles.heroRow`가 row 고정이며 `heroCopy` 텍스트 컬럼이 shrink 계약을 갖지 않는다.
- `ConsentNotice` 내부 긴 동의문과 체크 row label이 RN Web에서 intrinsic width로 overflow할 수 있다.

권장 레이아웃:

| 항목 | 모바일 | 데스크톱 |
|---|---|---|
| route outer padding | `PremiumAppShell`의 `spacing.lg` 유지 | `PremiumAppShell` 기본 유지. 필요 시 lane 내부만 640으로 제한 |
| registration content lane | `width: "100%"`, `maxWidth: "100%"`, `alignSelf: "center"`, `minWidth: 0` | `width: "100%"`, `maxWidth: 640`, `alignSelf: "center"`, `minWidth: 0` |
| header layout | `heroCopy -> heroImg` column, `alignItems: "center"` | 기존 row 가능, `heroCopy: flex: 1, minWidth: 0` |
| form padding | `spacing.lg` | `spacing.xl` |

maxWidth가 필요한 컴포넌트:

- `styles.form` (`sign-up.tsx` shadowed panel): `width: "100%"`, `maxWidth: 640`, `alignSelf: "center"`, `minWidth: 0`.
- `styles.header`, `styles.footer`: 같은 `registrationLane` 안에 포함하거나 각각 `width: "100%"`, `maxWidth: 640`, `alignSelf: "center"`.
- `ConsentNotice`의 root `styles.card`: 부모 form 안에서 `width: "100%"`, `maxWidth: "100%"`, `minWidth: 0`.
- `ConsentNotice`의 `purposes`, `group`, `checkLabel`: `minWidth: 0`을 가져야 동의문과 체크 label이 390px 안에서 줄바꿈된다.

추가 메모:

- desktop `maxWidth`는 법적/동의문 가독성을 위해 sign-in보다 넓은 640으로 둔다.
- 모바일에서는 header image와 긴 제목을 row로 유지하지 않는다. 390px에서 hero와 consent body가 함께 clipped 되었으므로 header부터 column 계약으로 고정한다.

### 3. Complete-Profile OAuth Completion

대상: `src/app/(auth)/complete-profile.tsx`

현재 위험 지점:

- `styles.scroll`에는 width lane이 없다.
- shadowed `styles.form`은 `width/maxWidth/alignSelf`가 없다.
- `styles.heroRow`가 sign-up과 같은 row 구조이며 shrink 계약이 없다.
- `ConsentNotice`를 재사용하므로 sign-up과 같은 긴 동의문 overflow 위험을 공유한다.

권장 레이아웃:

| 항목 | 모바일 | 데스크톱 |
|---|---|---|
| route outer padding | `PremiumAppShell`의 `spacing.lg` 유지 | `PremiumAppShell` 기본 유지 |
| completion content lane | `width: "100%"`, `maxWidth: "100%"`, `alignSelf: "center"`, `minWidth: 0` | `width: "100%"`, `maxWidth: 640`, `alignSelf: "center"`, `minWidth: 0` |
| header layout | `heroCopy -> heroImg` column, `alignItems: "center"` | 기존 row 가능, `heroCopy: flex: 1, minWidth: 0` |
| form padding | `spacing.lg` | `spacing.xl` |

maxWidth가 필요한 컴포넌트:

- `styles.form` (`complete-profile.tsx` shadowed panel): `width: "100%"`, `maxWidth: 640`, `alignSelf: "center"`, `minWidth: 0`.
- `styles.header`: 같은 completion lane에 포함하거나 `width: "100%"`, `maxWidth: 640`, `alignSelf: "center"`.
- `ConsentNotice` root/card와 내부 long-text row는 sign-up과 동일한 `width: "100%"`, `maxWidth: "100%"`, `minWidth: 0` 계약을 따른다.

추가 메모:

- complete-profile은 OAuth 후 첫 필수 입력 화면이다. sign-up과 폭이 다르면 같은 consent surface가 흔들려 보이므로 desktop `maxWidth`를 동일하게 640으로 둔다.

### 4. Manual Long-Form Guide

대상: `src/app/manual.tsx`

현재 위험 지점:

- `styles.scroll`에 content lane maxWidth가 없다.
- `SceneHero`와 `styles.card` shadowed surfaces가 lane에 묶이지 않았다.
- `styles.glossaryRow`는 row 고정이고 `glossaryTerm`이 140px fixed width라 390px에서 definition 컬럼이 쉽게 부족해진다.
- `styles.cardBody`, `glossaryDef`, `recentLine` 같은 긴 본문이 row/flex 부모에서 shrink 계약을 갖지 않는다.

권장 레이아웃:

| 항목 | 모바일 | 데스크톱 |
|---|---|---|
| route outer padding | `PremiumAppShell`의 `spacing.lg` 유지 | `PremiumAppShell` 기본 유지 |
| manual content lane | `width: "100%"`, `maxWidth: "100%"`, `alignSelf: "center"`, `minWidth: 0` | `width: "100%"`, `maxWidth: 720`, `alignSelf: "center"`, `minWidth: 0` |
| section gap | `spacing.lg` 현재 유지 | `spacing.lg` 현재 유지 |
| card padding | `spacing.lg` | `spacing.xl` |
| glossary row | column, term/definition 모두 `width: "100%"` | row, `glossaryTerm` 140px 유지 가능 |

maxWidth가 필요한 컴포넌트:

- `SceneHero` root/wrap 및 내부 shadowed shell: `width: "100%"`, `maxWidth: 720`, `alignSelf: "center"`, `minWidth: 0`.
- `styles.cards`: `width: "100%"`, `maxWidth: 720`, `alignSelf: "center"`.
- `styles.card` (`manual.tsx` repeated shadowed card): `width: "100%"`, `maxWidth: 720`, `alignSelf: "center"`, `minWidth: 0`.
- `styles.glossary`, `styles.recentList`, `styles.actions`, `styles.versionFootnote`: 같은 720 lane 안에서 `width: "100%"`, `maxWidth: 720`, `alignSelf: "center"`.

추가 메모:

- manual은 long-form guide라 desktop `maxWidth`를 720으로 둔다. 560/640보다 넓어야 본문이 과도하게 줄바꿈되지 않는다.
- 모바일 glossary는 반드시 column으로 바꾼다. fixed 140px term + gap + 긴 definition 조합은 390px에서 가장 취약하다.

### 5. Support Contact Cards

대상: `src/app/support.tsx`

현재 위험 지점:

- `styles.scroll`에 content lane maxWidth가 없다.
- `SceneHero`와 `styles.section` shadowed cards가 lane에 묶이지 않았다.
- support email과 FAQ copy가 카드 내부에서 shrink/wrap 계약 없이 렌더될 수 있다.

권장 레이아웃:

| 항목 | 모바일 | 데스크톱 |
|---|---|---|
| route outer padding | `PremiumAppShell`의 `spacing.lg` 유지 | `PremiumAppShell` 기본 유지 |
| support content lane | `width: "100%"`, `maxWidth: "100%"`, `alignSelf: "center"`, `minWidth: 0` | `width: "100%"`, `maxWidth: 640`, `alignSelf: "center"`, `minWidth: 0` |
| section gap | `spacing.lg` 현재 유지 | `spacing.lg` 현재 유지 |
| section padding | `spacing.lg` | `spacing.xl` |

maxWidth가 필요한 컴포넌트:

- `SceneHero` root/wrap 및 내부 shadowed shell: `width: "100%"`, `maxWidth: 640`, `alignSelf: "center"`, `minWidth: 0`.
- `styles.section` (`support.tsx` repeated shadowed card): `width: "100%"`, `maxWidth: 640`, `alignSelf: "center"`, `minWidth: 0`.
- section 내부 `Text`와 email line: `maxWidth: "100%"`, `minWidth: 0`, wrap 허용.
- section 내부 CTA button: mobile `width: "100%"`, desktop `maxWidth: 320` 또는 content-sized 버튼. 단, 카드 폭을 밀어내는 fixed width는 금지.

추가 메모:

- support는 manual보다 짧은 task screen이므로 desktop `maxWidth`를 640으로 둔다.

## 검수 기준

다음 viewport에서 확인한다.

- Mobile: 390x844
- Desktop: 1440x1100

합격 기준:

- 각 대상 route에서 `document.documentElement.scrollWidth <= window.innerWidth`.
- 오른쪽 edge에서 form, consent notice, manual card body, support section border/shadow가 잘리지 않는다.
- desktop에서는 sign-in 560, sign-up/complete-profile/support 640, manual 720 lane이 중앙 정렬된다.
- screenshot 기준으로 mobile에서 x축 스크롤바가 없어야 한다.
- shadow가 보이는 것은 허용하지만 shadow 때문에 layout width가 커지면 실패다.

## 우선 구현 순서

1. `ConsentNotice` 내부 long-text row shrink 계약을 먼저 고친다. sign-up과 complete-profile이 동시에 안정된다.
2. sign-in의 literal 24 gutter를 token 기반 mobile `spacing.lg`로 낮추고 560 auth lane을 추가한다.
3. sign-up과 complete-profile에 640 content lane과 mobile column hero를 적용한다.
4. manual에 720 content lane과 mobile glossary column을 적용한다.
5. support에 640 content lane을 적용한다.
