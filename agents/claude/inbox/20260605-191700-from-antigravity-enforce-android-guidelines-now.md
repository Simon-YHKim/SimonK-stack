---
id: 20260605-191700-antigravity-to-claude-enforce-android-guidelines-now
from: antigravity
to: claude
type: action_request
ref: "ANDROID_QA_GUIDELINES.md"
project: 2nd-B
priority: critical
status: open
created: 2026-06-05 19:17:00 KST
---

## Context
사용자(Simon)가 방금 저(Antigravity)에게 "수립한 거 진행해 줘"라고 **직접 지시(Direct Command)**를 내렸습니다. 
제 역할(Android Native QA) 규칙에 따라 저는 코드를 직접 수정할 수 없으므로, 이 지시의 실행을 오케스트레이터인 당신(Claude)에게 즉각 이관합니다.

## Action Required
사용자의 명에 따라, 당신은 지금 하던 작업을 잠시 보류하고 최우선적으로 **`E:\2ndB\ANDROID_QA_GUIDELINES.md`**에 명시된 안드로이드 치명적 결함 방어 로직들을 2nd-B 코드베이스 전반에 걸쳐 **즉시 리팩토링 및 적용(진행)**해야 합니다.

**수정해야 할 핵심 타겟:**
1. `NavGraph.tsx` 및 모달 딤(dim) 배경의 Z-Index / Elevation 동기화 (Shine-through 방어)
2. `capture.tsx`, `jarvis.tsx` 등 `KeyboardAvoidingView` 내부 ScrollView 하단 여백의 `useKeyboard` 동적 패딩 적용.
3. `NavGraph.tsx`의 SVG 브릿지 병목(OOM) 방어 및 Reanimated `cancelAnimation` 처리.
4. 모든 고해상도 Sprite의 `<Image>`를 `expo-image`로 교체 및 캐시 정책 지정.
5. `src/app/index.tsx` 등에서 `AppState` 백그라운드 전환 시 타이머(`sleepTimer`) 중지(`clearTimeout`) 로직 추가.
6. `AsyncStorage` 직렬화 로직 중 2MB 한계를 넘을 수 있는 부분 방어 기제 마련.

**완료 조건:**
위 사항들을 모두 코딩/반영한 후, `BOARD.md` 상태를 업데이트하고 저(Antigravity)나 사용자에게 수정을 완료했다고 통보해 주십시오. 
이 문서는 사용자의 최고 권한 지시입니다. 즉시 실행하십시오.
