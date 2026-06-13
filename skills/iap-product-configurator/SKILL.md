---
name: iap-product-configurator
description: "Use when the user configures in-app purchase products or store pricing—triggers \"인앱결제 상품\", \"구독 그룹\", \"IAP 가격\", \"스토어 상품 등록\", \"App Store Connect 상품\", \"Play Console 구독\", \"국가별 가격\", \"in-app purchase products\", \"subscription group\", \"store product setup\", or /iap-product-configurator. Produces a validated product manifest, App Store Connect / Play Console product IDs, subscription groups, upgrade/downgrade paths, per-country localized prices (₩↔$↔¥) snapped to legal price points, and a sandbox test checklist. Fills the gap between payment-integrator (code) and store-launcher (listing)."
allowed-tools: Read, Write, WebFetch, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# iap-product-configurator

앱스토어 인앱결제(IAP) 상품과 가격을 **스토어 콘솔에 등록할 수 있는 형태로** 구성하는 skill.

`payment-integrator`(결제 코드)와 `store-launcher`(스토어 리스팅) 사이의 공백을 메운다.
결제 SDK는 상품 ID가 콘솔에 정확히 등록돼 있어야 동작하고, 리스팅 도구는 가격·구독 구조를
다루지 않는다. 이 skill은 그 중간 — 상품 ID 체계, 구독 그룹, 업그레이드 경로, 국가별 가격을
결정론적으로 만들어 낸다.

## 발동 조건

- "인앱결제 상품 만들어줘", "구독 그룹 설계해줘", "IAP 가격 책정"
- "App Store Connect 상품 등록", "Play Console 구독 세팅", "스토어 상품 ID 정해줘"
- "국가별 가격 (원/달러/엔) 뽑아줘"
- `payment-integrator` 또는 `subscription-manager-selector` 실행 후, 실제 상품 등록 단계에서 체인

## 다루지 않는 것 (경계)

| 이 skill | 인접 skill |
|---|---|
| 상품 ID·구독 그룹·가격 manifest | 결제 코드·webhook·영수증 검증 → `payment-integrator` |
| 가격 포인트·국가별 현지화 | 스토어 리스팅·스크린샷·심사 제출 → `store-launcher` |
| IAP 상품 구조 | 어떤 구독 관리 SaaS를 쓸지 → `subscription-manager-selector` |

## 상품 타입

| 타입 | 의미 | 예시 | 복원 |
|---|---|---|---|
| `consumable` | 쓰면 소진, 재구매 가능 | 코인, 힌트, 1회 크레딧 | ✗ |
| `non_consumable` | 1회 구매 영구 소유 | 광고 제거, 프로 잠금해제 | ✓ |
| `auto_renewable` | 자동 갱신 구독 | 월간/연간 멤버십 | ✓ |
| `non_renewing` | 기간제, 자동갱신 없음 | 시즌 패스 30일 | 직접 관리 |

## 상품 ID 규칙 (가장 흔한 사고 지점)

- **영구·전역**: 한 번 만든 ID는 삭제해도 재사용 불가. 오타 = 영구 폐기 → 새 ID로.
- **소문자 reverse-dns**: `com.회사.앱.상품` 형태. 정규식 `^[a-z0-9]+([._][a-z0-9]+)*$`.
- **양 스토어 동일 권장**: App Store와 Play의 product ID를 같게 맞춰야 코드가 분기 없이 단순해진다.
- **길이**: Play는 최대 100자. 짧고 의미 있게.
- 코드의 product identifier와 콘솔 등록값이 **글자 단위로** 일치해야 한다 (대소문자·점 위치 포함).

## 구독 그룹과 업그레이드 경로

핵심 원칙: **하나의 제공물(offering)의 모든 tier는 하나의 구독 그룹에 묶는다.**

- 같은 그룹 안에서 tier를 바꾸면 OS가 **업그레이드/다운그레이드**로 처리 (중복 청구 없음).
- 다른 그룹으로 옮기면 **새 구독** — 사용자가 두 개를 동시에 결제하게 된다 (사고).
- `rank`로 tier 서열을 매긴다: **숫자가 작을수록 상위 tier** (rank 1 = 최상위).
  - 업그레이드(상위로): 즉시 적용 + 프로레이션.
  - 다운그레이드(하위로): 다음 갱신 시점에 적용.

```
구독 그룹 "pro"
├─ pro.yearly   (rank 1, 최상위)
└─ pro.monthly  (rank 2)  ──업그레이드──▶ pro.yearly

별도 그룹 "pro" 와 "team" 사이 전환은 업그레이드 아님 → 재구독
```

App Store Connect는 그룹 내 **모든** 레벨에 rank가 있어야 업그레이드 경로를 정렬한다.
manifest의 `upgradesTo`는 같은 그룹 + 더 높은 tier(작은 rank)만 가리켜야 하며, 빌더가 검증한다.

## 국가별 현지화 가격

스토어는 임의 금액을 못 받는다 — 통화별 **가격 포인트(price point/tier)** 사다리에서 고른다.
이 skill의 빌더는 base 가격을 FX로 환산한 뒤 **가장 가까운 합법 포인트로 스냅**한다.

| 통화 | 소수점 | 비고 |
|---|---|---|
| USD / EUR / GBP | 2자리 | `4.99`, `49.99` |
| KRW | 없음 | `4,900`, `49,000` — 원화 0자리 정수 |
| JPY | 없음 | `800`, `8,000` — 엔화 0자리 정수 |

원칙:
- 환율은 **고정값으로 둔다**. 스토어 가격은 실시간 FX가 아니라 "설정하고 분기마다 재검토"하는 값.
- 라운드 가격을 유지하라 — `5,870원` 같은 환산 잔값이 아니라 `5,900원` 포인트로 스냅.
- manifest의 `fx`로 환율을 덮어쓸 수 있다 (예: `{"KRW": 1370}`).

## 도구 (결정론, 네트워크 없음)

manifest 하나가 단일 진실원천(single source of truth). 빌더는 같은 입력 → 항상 같은 출력.

```bash
# 검증만 (CI에 넣기 좋음, 실패 시 exit 1)
node scripts/iap-build.mjs products.json --check

# 검증 + 국가별 가격 plan 생성(JSON) + 리뷰 테이블
node scripts/iap-build.mjs products.json --table > products.plan.json

# 또는 크로스플랫폼 래퍼 (plan 파일 자동 저장)
bash scripts/iap-configure.sh products.json --table
```

빌더가 잡아내는 것:
- 상품 ID 형식 위반, 중복 ID, 길이 초과
- `auto_renewable`인데 그룹/period 누락
- 구독 그룹 내 rank 중복
- `upgradesTo`가 다른 그룹을 가리키거나 상위 tier가 아닌 경우
- base 가격을 통화별 포인트로 스냅한 plan 출력

## 구현 단계

### 1. 요구사항 확인 (`AskUserQuestion`)

먼저 물어볼 것: ① 무료 / 일회성 / 구독 중 무엇인가 ② 구독이면 tier 몇 개 (월/연) ③ base 통화와
타깃 국가 ④ 무료 체험 제공 여부.

### 2. manifest 작성

`templates/products.schema.json` 스키마, `templates/products.example.json` 예시 참고.
`Write`로 프로젝트 루트(또는 `store/`)에 `products.json` 생성.

### 3. 검증 + 가격 plan 생성

위 빌더 실행. 에러 0개가 될 때까지 manifest 수정. plan JSON으로 콘솔 입력값 확보.

### 4. 콘솔 등록

- **App Store Connect**: My Apps → 앱 → In-App Purchases / Subscriptions. 구독은 먼저 그룹 생성 → 그 안에 tier. 각 tier에 refName·기간·가격·체험 입력. plan JSON의 통화별 값으로 가격 설정.
- **Play Console**: Monetize → Products → In-app products / Subscriptions. 구독은 base plan + offer 구조. product ID를 App Store와 동일하게.

### 5. Sandbox 테스트

`templates/sandbox-checklist.md` 따라 양 스토어 sandbox에서 구매·갱신·복원·환불을 끝까지 검증.

## 시크릿 / env 규칙

- App Store Connect API Key(`.p8`), Play Console 서비스 계정 JSON은 **절대 커밋 금지**. `.gitignore` 확인.
- 영수증/구매토큰 서버 검증에 쓰는 키는 env로만 주입 (`EXPO_PUBLIC_` 접두사 금지 — 클라이언트 노출됨).
- product ID·가격 manifest 자체는 시크릿이 아니므로 커밋 OK (오히려 git으로 변경 추적 권장).

## 가격 포인트 갱신

`scripts/iap-build.mjs`의 `PRICE_POINTS` / `DEFAULT_FX`는 정적 앵커다. 스토어가 가격 tier를
개편하면(드물지만 발생) `WebFetch`로 최신 App Store Connect / Play Console 가격표를 받아
사다리를 갱신한다. 환율은 분기마다 재검토.

## 검증 체크리스트

- [ ] 모든 product ID가 소문자 reverse-dns, 중복 없음, 양 스토어 동일
- [ ] 구독 tier가 단일 그룹에 묶여 있고 rank가 유일
- [ ] 업그레이드 경로가 같은 그룹 + 상위 tier만 가리킴
- [ ] 국가별 가격이 합법 포인트로 스냅됨 (₩·¥ 정수, 라운드 가격)
- [ ] 무료 체험은 계정당 1회 정책 반영
- [ ] `node scripts/iap-build.mjs products.json --check` 통과 (exit 0)
- [ ] sandbox-checklist 양 스토어 통과
- [ ] 결제 코드 검증은 `payment-integrator`로 이어감

## Related Skills

- `payment-integrator` — 등록된 상품 ID를 받아 결제/구독 코드·webhook·영수증 검증 구현
- `store-launcher` — 스토어 리스팅·스크린샷·심사 제출 (가격이 아닌 노출)
- `subscription-manager-selector` — RevenueCat/Stripe Billing 등 구독 관리 SaaS 선택
- `monetization-planner` — 어떤 수익 모델·tier 구조를 만들지 상위 결정
- `global-payment-planner` — 국가별 세금/VAT·결제 규제 처리
