# ATT 프리프롬프트 + Usage Description 카피

> 추적(IDFA/광고ID 수집 또는 광고·데이터 브로커 공유)이 있을 때만 사용한다.
> 추적이 없으면 ATT 자체를 적용하지 않는다 — 불필요한 추적 선언은 신뢰를 깎는다.

## 작동 순서 (RN/Expo)

1. 앱이 실제로 추적할 시점에 **프리프롬프트**(자체 설명 화면)를 먼저 띄운다.
2. 사용자가 "계속"을 누르면 그때 시스템 `requestTrackingAuthorization`를 호출한다.
3. 프리프롬프트에서 거부하면 시스템 다이얼로그를 띄우지 않는다 — iOS는 거부를 영구 저장하므로, 시스템 프롬프트는 동의 가능성이 있을 때만 노출.
4. 시스템 다이얼로그의 본문은 `NSUserTrackingUsageDescription`이 그대로 표시된다.

> `expo-tracking-transparency`의 `requestTrackingPermissionsAsync()` 사용. iOS 14.5+ 에서만 의미가 있고, Android/웹에는 ATT가 없다 — 플랫폼 분기 필수.

## 프리프롬프트 카피 (EN / KO)

과장·약속 금지. 무엇을 추적하고 무엇이 좋아지는지 솔직하게. 1문장 제목 + 1~2문장 본문.

### EN

- Title: `Allow tracking to keep <App> free`
- Body: `We use your advertising ID to show ads that fit you and to measure what works. You can change this anytime in Settings.`
- Primary: `Continue`  ·  Secondary: `Not now`

### KO

- 제목: `<앱> 무료 유지를 위해 추적을 허용해 주세요`
- 본문: `광고 식별자를 사용해 더 맞는 광고를 보여주고 효과를 측정합니다. 설정에서 언제든 바꿀 수 있어요.`
- 기본: `계속`  ·  보조: `나중에`

> 다크 패턴 금지 — "나중에"는 "계속"과 동일한 무게(크기·대비)로. 거부해도 핵심 기능은 동일하게 동작함을 본문에서 약속한 대로 지킬 것.

## NSUserTrackingUsageDescription (Info.plist / app.json)

시스템 다이얼로그 본문. 구체적으로(무엇을·왜). 빈 값·포괄 문구("타사 앱·웹사이트 추적")만 쓰면 리젝.

### EN

```
We use your advertising identifier to deliver more relevant ads and measure their performance.
```

### KO

```
더 관련 있는 광고를 제공하고 광고 효과를 측정하기 위해 광고 식별자를 사용합니다.
```

### app.json 배치

```jsonc
{
  "expo": {
    "ios": {
      "infoPlist": {
        "NSUserTrackingUsageDescription": "더 관련 있는 광고를 제공하고 광고 효과를 측정하기 위해 광고 식별자를 사용합니다."
      }
    }
  }
}
```

> 직접 수정 전 사용자 확인. 다국어 시스템 다이얼로그는 `InfoPlist.strings`(언어별)로 분리하되, 키 패리티(EN↔KO)를 맞춘다.

## 금지

- 카피에 PII·시크릿·내부 식별자 삽입 금지.
- 과장("절대 안전", "100% 익명"), 협박("거부하면 사용 불가") 금지.
- 이모지·장식 금지.
- 추적이 없는데 ATT 카피를 넣는 것 금지 (과대 선언).
