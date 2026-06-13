---
name: analytics-ad-wiring
description: "Use when the user asks to actually wire analytics or ad SDKs into a running app or site—triggers \"GA 붙여줘\", \"Clarity 연동\", \"AdMob 세팅\", \"AdSense 적용\", \"분석 코드 심어줘\", \"광고 코드 넣어줘\", \"wire up GA4\", \"add AdMob\", \"implement analytics\", /analytics-ad-wiring. Produces the real integration code (web gtag + Clarity + AdSense snippets, RN Firebase Analytics + AdMob init), an env.example with measurement/ad-unit IDs, a consent-gated wrapper so nothing fires before consent, and fail-open guards so a missing/wrong env key never bricks the runtime. analytics-integrator/ad-monetization choose the tools and strategy; this skill is the wiring."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# analytics-ad-wiring

분석·광고 도구를 앱·사이트에 **실제로 배선**하는 skill.
`analytics-integrator`/`ad-monetization`/`tag-manager-integrator`가 "무엇을 어떻게 쓸지"(선택·전략·이벤트 택소노미)를 정한다면, 이 skill은 그 결정을 **돌아가는 코드**로 옮긴다.

## 발동 조건

- "GA 붙여줘", "GA4 연동", "Clarity 연동", "분석 코드 심어줘"
- "AdMob 세팅", "AdSense 적용", "광고 코드 넣어줘"
- `/analytics-ad-wiring`
- `dev-orchestrator` / `app-dev-orchestrator` 가 "택소노미 확정 후 배선" 단계에서 호출

## 선결 조건 (없으면 먼저 확보)

배선은 결정이 끝난 뒤에만 한다. 아래가 비어 있으면 해당 skill을 먼저 돌리고 산출물을 입력으로 받는다.

| 입력 | 출처 skill | 없을 때 |
|---|---|---|
| 측정 도구 선택 (GA4/Clarity/PostHog/Firebase) | `analytics-integrator` | 먼저 호출 |
| 이벤트 택소노미 (`object_action`) | `analytics-integrator` | 먼저 호출 |
| 광고 SDK·배치 전략 | `ad-monetization` | 먼저 호출 |
| 동의 게이트 (consent state) | `consent-manager` | 게이트가 없으면 no-op consent 헬퍼를 임시 생성하되 TODO 표기 |
| 수집 항목 등록부 | `data-flow-mapper` | 수집 필드를 등록부에 추가 (없으면 TODO) |

## 4대 불변식 (강제 — 위반 시 배선 중단)

이 4개는 협상 불가다. `scripts/verify-wiring.sh` 가 정적으로 검사한다.

| # | 불변식 | 왜 |
|---|---|---|
| **I1 동의 게이트** | 모든 트래커·광고 호출은 `consent-manager`의 동의 상태가 `granted`일 때만 발화. 동의 전에는 SDK 로드·init 자체를 미룬다(스니펫을 `<head>`에 무조건 박지 않는다). | PIPA·정보통신망법·GDPR. 비개인화/미동의 상태에서 추적 금지. |
| **I2 fail-open 가드** | 잘못되거나 누락된 analytics·ad env 키가 런타임을 **절대** 죽이지 않는다. lazy init + try/catch + no-op fallback. env 미설정이면 조용히 비활성(앱은 정상 동작). | 아웃리지 교훈: analytics env 값 하나가 앱 전체를 블랙스크린으로 만든 사고(2ndB #363). 분석은 부가기능이지 의존성이 아니다. |
| **I3 택소노미 일치** | 발화하는 이벤트명·속성은 `analytics-integrator` 택소노미와 1:1 일치. 코드에 임의 이벤트명 금지. 택소노미 상수 파일을 단일 소스로 import. | 데이터 신뢰성. 오타·중복 이벤트가 퍼널을 오염시킨다. |
| **I4 등록** | 수집하는 모든 항목(user_id, device, 페이지, 광고 식별자 등)은 `data-flow-mapper` 등록부에 등재. 미등재 수집 금지. | 데이터 흐름 추적성·개인정보 처리방침 동기화. |

## 플랫폼 분기

배선 코드는 플랫폼마다 다르다. 먼저 무엇을 빌드 중인지 확인하고 분기한다.

| 플랫폼 | 분석 | 광고 | 비고 |
|---|---|---|---|
| **웹 (Vercel/Next/정적)** | GA4 gtag + MS Clarity 스니펫 | Google AdSense | 스니펫은 consent 후 동적 주입. Next는 `next/script` `strategy="afterInteractive"` |
| **RN / Expo** | Firebase Analytics (`@react-native-firebase/analytics`) 또는 GA4 via gtag in WebView | AdMob (`react-native-google-mobile-ads`) | iOS는 ATT 프롬프트 후 개인화. Expo는 config plugin 필요 (managed면 dev client) |
| **하이브리드 (Capacitor 등)** | 웹 스택 재사용 + 네이티브 브리지 | 웹/네이티브 혼용 | `app-platform-selector` 결정 따름 |

플랫폼이 모호하면 `AskUserQuestion`으로 확인한다 (웹 / RN-Expo / 하이브리드).

## Workflow

### 1. 입력 수집 + 플랫폼 확정
- 택소노미·도구·동의 게이트 산출물 확인 (선결 조건 표).
- 플랫폼 분기 결정. 모호하면 질문.

### 2. env 템플릿 주입
- `templates/env.example` 를 프로젝트 루트에 추가/병합.
- **측정 ID·광고 단위 ID는 절대 하드코딩하지 않는다.** 전부 env 주입.
- 테스트 모드 분리: 개발/CI에서는 AdMob/AdSense **테스트 ID** 강제 (운영 단위 노출 금지 → 정책 위반·노출 차단 위험).
- `.env` 가 `.gitignore` 에 있는지 확인. 없으면 추가.

### 3. fail-open init 레이어 작성
- `templates/failopen-init.ts` 패턴으로 lazy·try/catch·no-op fallback init.
- env 키 누락·형식 오류 시 `console.warn` 후 no-op 반환. throw 금지.

### 4. consent-gated wrapper 작성
- `templates/consent-gated-wrapper.ts` 로 모든 발화를 동의 게이트 뒤로 통과.
- 동의 전 큐잉 → 동의 후 flush (또는 단순 drop). drop 기본, 큐잉은 명시 요청 시.

### 5. 플랫폼별 배선
- 웹: `templates/web-snippet.html` (gtag + Clarity + AdSense) 동적 주입.
- RN: `templates/rn-init.ts` (Firebase Analytics + AdMob) consent 후 init.

### 6. 택소노미 상수 연결 (I3)
- 이벤트명은 `analytics-integrator` 택소노미 상수에서만 import. 인라인 리터럴 금지.

### 7. 등록 (I4)
- 수집 필드를 `data-flow-mapper` 등록부에 추가.

### 8. 검증
- `bash scripts/verify-wiring.sh [src-dir]` 실행 → 4대 불변식 정적 통과 확인.
- 런타임: env 비운 상태로 부팅 → 앱이 죽지 않는지(I2), 동의 토글 → 발화 on/off(I1) 확인.

## 키 형식 빠른 참조

| 키 | 형식 예 | 검사 |
|---|---|---|
| GA4 Measurement ID | `G-XXXXXXXXXX` | `^G-[A-Z0-9]{10}$` |
| Clarity Project ID | 10자 영숫자 | `^[a-z0-9]{10}$` |
| AdSense Publisher ID | `ca-pub-0000000000000000` | `^ca-pub-\d{16}$` |
| AdMob App ID | `ca-app-pub-…~…` | `~` 포함 |
| AdMob 광고 단위 ID | `ca-app-pub-…/…` | `/` 포함 |
| AdMob 테스트 배너 (Android) | `ca-app-pub-3940256099942544/6300978111` | 공식 테스트 ID |

## 안티패턴 (하지 말 것)

- `<head>` 에 gtag/Clarity/AdSense 스니펫을 동의와 무관하게 무조건 삽입 (I1 위반).
- `init(process.env.X!)` 처럼 non-null 단언으로 env 강제 (I2 위반 — 누락 시 크래시).
- 컴포넌트 안에서 `track("buttonClickkk", …)` 같은 인라인 임의 이벤트명 (I3 위반).
- 운영 광고 단위 ID를 개발/테스트 빌드에 노출 (정책 위반).
- 측정/광고 ID를 소스에 하드코딩 (env로).

## 검증 체크리스트

- [ ] env 비운 채 부팅 → 앱 정상 동작 (I2 fail-open)
- [ ] 동의 미부여 시 네트워크 탭에 트래커/광고 요청 0건 (I1)
- [ ] 동의 부여 후 핵심 이벤트 발화 + 택소노미명 일치 (I1·I3)
- [ ] 개발/CI 빌드는 테스트 광고 ID만 사용
- [ ] 수집 필드 전부 `data-flow-mapper` 등록 (I4)
- [ ] 측정·광고 ID 소스 하드코딩 0건 (`scripts/verify-wiring.sh`)
- [ ] iOS: ATT 프롬프트 후에만 개인화 광고

## Related Skills

- `consent-manager` — 동의 게이트 (I1 의존). 이 skill은 그 상태를 읽기만 한다.
- `data-flow-mapper` — 수집 항목 등록부 (I4 의존).
- `analytics-integrator` — 도구 선택 + 이벤트 택소노미 (I3 소스).
- `ad-monetization` — 광고 SDK·배치 전략 (입력).
- `tag-manager-integrator` — GTM 기반 태그 계층 (대안 경로).
