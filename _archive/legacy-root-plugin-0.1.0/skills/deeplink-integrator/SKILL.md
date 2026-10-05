---
name: deeplink-integrator
description: "Use when the user asks to wire up deep links, universal links, app links, or deferred deep links in a React Native / Expo app—triggers \"딥링크 붙여줘\", \"유니버설 링크 연동\", \"앱 링크 설정\", \"deferred deep link\", \"AASA 파일\", \"assetlinks.json\", \"링크 라우팅\", \"add deep linking\", \"universal links\", \"app links\". Produces end-to-end deep link wiring: iOS Universal Links (AASA) + Android App Links (assetlinks.json) + domain verification, expo-router route mapping, deferred deep link recovery, attribution parameter pass-through, and a real-device verification checklist."
allowed-tools: Read, Write, Edit, Bash, Grep, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# deeplink-integrator

딥링크를 end-to-end 로 배선하는 skill. RN/Expo 앱이 도메인 링크(`https://app.example.com/...`)와 커스텀 스킴(`myapp://...`)을 모두 받아 올바른 화면으로 라우팅하고, 설치 전 클릭된 링크(deferred)와 attribution 파라미터까지 끝까지 전달하도록 만든다.

## 발동 조건

- "딥링크 붙여줘", "유니버설 링크 연동", "앱 링크 설정"
- "deferred deep link", "AASA 파일", "assetlinks.json"
- "공유 링크 누르면 앱 특정 화면 열리게", "링크 라우팅"
- `/deeplink-integrator`

## 경계 (Boundaries)

- `building-native-ui` — expo-router 자체 셋업/네비게이션 구조. 이 skill 은 그 위에 링크 매핑만 얹는다.
- `referral-program-builder` — 초대 링크의 *보상/로직*. 이 skill 은 그 링크가 앱에서 *열리고 추적되는* 배관만 담당.
- `mobile-attribution-integrator` — SDK(예: AppsFlyer/Adjust/Branch) 기반 attribution 전체. 이 skill 은 SDK 없이 도메인+파라미터 패스스루까지. SDK 필요 시 그쪽으로 넘긴다.

## 사전 진단 (먼저 묻기)

`AskUserQuestion` 으로 아래를 확정한 뒤 코드 생성. 추측 금지.

| 항목 | 왜 필요한가 |
|---|---|
| 소유 도메인 | AASA/assetlinks 를 `https://<domain>/.well-known/` 에 호스팅해야 함. 도메인 없으면 커스텀 스킴만 가능 |
| iOS Team ID + Bundle ID | AASA 의 `appID` = `<TeamID>.<BundleID>` |
| Android package + SHA-256 fingerprint | assetlinks 의 `package_name` + `sha256_cert_fingerprints` (디버그/릴리스/Play 서명 각각) |
| 라우팅할 경로 | 예: `/post/:id`, `/invite/:code` → 어느 expo-router 화면에 매핑할지 |
| deferred 필요 여부 | 미설치 → 스토어 → 설치 후 원래 링크 복원이 필요한가 (보통 초대/캠페인은 필요) |
| attribution 파라미터 | `utm_*`, `ref`, `campaign` 등 어디까지 보존·전달할지 |

## 동작 모델 (3 경로)

```
링크 클릭
├─ 앱 설치됨 + 도메인 검증됨
│    iOS: Universal Link / Android: App Link → OS가 앱 직접 오픈 → expo-router 라우팅
├─ 앱 설치됨 + 커스텀 스킴 (myapp://)
│    브라우저/타앱 → 스킴 인텐트 → 앱 오픈 (검증 불필요, 단 가로채기 위험)
└─ 앱 미설치
     도메인 링크 → 웹 폴백 페이지 → 스토어 유도 → (deferred) 설치 후 원래 경로 복원
```

원칙: **도메인 링크를 1순위**(검증되어 가로채기 안 됨), 커스텀 스킴은 폴백/내부용으로만.

## 구현 단계

### 1. expo-router linking 설정 (`app.json`)

`templates/app.json.deeplink.jsonc` 참조. 핵심은 `scheme` + iOS `associatedDomains` + Android `intentFilters`.

```jsonc
{
  "expo": {
    "scheme": "myapp",
    "ios": {
      "associatedDomains": ["applinks:app.example.com"]
    },
    "android": {
      "intentFilters": [{
        "action": "VIEW",
        "autoVerify": true,
        "data": [{ "scheme": "https", "host": "app.example.com" }],
        "category": ["BROWSABLE", "DEFAULT"]
      }]
    }
  }
}
```

expo-router 는 파일 기반 라우팅이라 `linking` config 가 대체로 자동. 커스텀 prefix/파라미터 매핑이 필요하면 `templates/linking.config.ts` 의 `getStateFromPath` 패턴 사용.

### 2. iOS Universal Links — AASA

`templates/apple-app-site-association.json` 를 채워 `https://<domain>/.well-known/apple-app-site-association` 에 호스팅.

- **확장자 없이**, `Content-Type: application/json` 로 서빙 (리다이렉트 금지)
- `appID` = `TEAMID.com.example.myapp`
- 경로는 `components`(신형) 권장. `paths`(구형)도 호환

### 3. Android App Links — assetlinks.json

`templates/assetlinks.json` 를 채워 `https://<domain>/.well-known/assetlinks.json` 에 호스팅.

- `sha256_cert_fingerprints` 에 **디버그 + 릴리스 + Play 앱 서명** 지문을 모두 배열로 넣기 (가장 흔한 실패 원인)
- Play 앱 서명 지문은 Play Console → 앱 무결성 → 앱 서명 키에서 확인

### 4. 도메인 verify

`scripts/verify-aasa.sh <domain>` / `scripts/verify-assetlinks.sh <domain> <package>` 로 호스팅 상태를 검사:

- AASA: 200 + 올바른 Content-Type + appID 포함 여부
- assetlinks: Google Digital Asset Links API 로 검증 (`digitalassetlinks.googleapis.com`)
- iOS 실기기는 Apple CDN 캐시(`app-site-association.cdn-apple.com`)를 보므로 변경 후 전파 지연 가능 → 재설치로 강제 갱신

### 5. deferred deep link

OS 기본 Universal/App Link 은 미설치 시 원래 경로를 자동 복원하지 않는다. SDK 없이 처리하려면:

- 웹 폴백 페이지에서 클릭 컨텍스트(경로+파라미터)를 단기 저장 (서버 측 클릭 ID 또는 클립보드)
- 앱 첫 실행(`onboarding/index`)에서 해당 컨텍스트를 조회해 라우팅
- 정밀 매칭이 필요하면 `mobile-attribution-integrator`(Branch/AppsFlyer OneLink) 로 위임

`templates/deferred-deeplink.ts` 에 클립보드 폴백 + 서버 클릭ID 조회 스텁 제공.

### 6. attribution 파라미터 패스스루

링크의 `utm_source`, `ref`, `campaign` 등을 라우팅 시 소실하지 않게:

- linking 파서에서 쿼리스트링 보존 → 화면 진입 시 `useLocalSearchParams()` 로 읽기
- 첫 진입 1회만 analytics 이벤트로 기록 (중복 방지 플래그)
- `analytics-integrator` 의 이벤트 분류와 키 정렬

## 검증 체크리스트 (실기기 필수)

시뮬레이터/에뮬레이터는 도메인 검증을 건너뛰는 경우가 있어 **실기기 + 릴리스 유사 빌드** 로 확인.

- [ ] `scripts/verify-aasa.sh` 200 + Content-Type 통과
- [ ] `scripts/verify-assetlinks.sh` Google API 검증 통과
- [ ] iOS: Notes/메시지에 도메인 링크 붙여넣고 탭 → 브라우저 아닌 앱이 열림
- [ ] Android: `adb shell am start -a android.intent.action.VIEW -d "https://<domain>/post/123"` → 앱 직접 오픈 (선택창 안 뜸)
- [ ] 커스텀 스킴: `myapp://post/123` → 앱 오픈
- [ ] 콜드 스타트(앱 종료 상태)와 웜 스타트(백그라운드) 양쪽에서 라우팅 동작
- [ ] 잘못된/만료된 경로 → 안전한 폴백 화면 (크래시 X)
- [ ] 미설치 → 스토어 → 설치 후 deferred 경로 복원 (해당 시)
- [ ] attribution 파라미터가 목적지 화면까지 도달 + 1회만 기록
- [ ] 로그아웃 상태에서 보호 경로 링크 → 로그인 후 원래 경로 복귀

## 흔한 실패 (측정 기반)

| 증상 | 원인 |
|---|---|
| 링크가 앱 대신 브라우저로 열림 | AASA/assetlinks 미호스팅, Content-Type 오류, 또는 SHA-256 지문 누락 |
| Android 선택창이 매번 뜸 | `autoVerify: true` 누락 또는 지문 불일치로 검증 실패 |
| iOS 변경이 반영 안 됨 | Apple CDN 캐시 → 앱 재설치로 강제 갱신 |
| 콜드 스타트 시만 라우팅 실패 | 초기 URL 처리 누락 (`Linking.getInitialURL` 경로) |
| 파라미터 소실 | 파서가 쿼리스트링 버림 / 라우팅 후 읽지 않음 |

## 외부 의존

- Expo CLI (`npx expo`), EAS Build (릴리스 유사 빌드)
- 도메인 + 정적 호스팅 (`.well-known/` 서빙 가능해야 함; Vercel/Netlify/직접 서버)
- `curl` (verify 스크립트). Android 검증은 인터넷 + Google API
- 실기기 1대 이상 (iOS/Android)

## 실패 시

- 도메인/지문/Team ID 가 없으면 커스텀 스킴까지만 배선하고, 검증 단계는 미완으로 명시 후 사용자에게 값 요청
- deferred 정밀 매칭이 필요한데 SDK 없이 한계에 부딪히면 `mobile-attribution-integrator` 로 인계

## Related Skills

- `building-native-ui` — expo-router 셋업/네비게이션 기반
- `referral-program-builder` — 초대 링크 로직/보상
- `mobile-attribution-integrator` — SDK 기반 attribution/deferred
- `analytics-integrator` — 링크 진입 이벤트 분류
- `deploy-configurator` — `.well-known/` 호스팅 배포
