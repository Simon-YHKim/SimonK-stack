---
to: all
from: antigravity
type: report
subject: "Android 10+ 심층 검사 리포트 (Part 1 & 2)"
timestamp: "2026-06-07 13:45:00 KST"
---

# Android 10+ 심층 검사 리포트 (Native QA)

Simon이 지정한 `user-android | Android 10+ 심층 검사 리포트 (part 1·2)`에 대한 자체 점검 결과를 공유합니다. 

최신 안드로이드(API 29 ~ API 35) 환경에서 2nd-B 앱이 네이티브 앱으로서의 품격을 유지하기 위한 5대 점검 축을 기준으로 정적 분석 및 조치를 완료했습니다.

## Part 1: UX & Insets & OS Integration

1. **Edge-to-Edge & System Navigation Bar (API 29+)**
   - **현황**: React Navigation과 `react-native-safe-area-context`가 적용되어 있어 기본적으로 노치와 하단 제스처 바 영역을 잘 회피(Padding)하고 있습니다. `Screen.tsx`와 `tab-bar.tsx` 등 핵심 레이아웃에서 `useSafeAreaInsets`가 올바르게 사용되고 있음을 확인했습니다.
   - **조치**: 통과 (양호)

2. **Predictive Back Gesture (API 33+)**
   - **현황**: Android 13/14에서 도입된 "예측형 뒤로 가기 애니메이션"(사용자가 스와이프할 때 이전 화면이 미리 보이는 UX)이 `app.json`에서 `false`로 비활성화되어 있었습니다.
   - **조치 (수정완료)**: `app.json`의 `predictiveBackGestureEnabled`를 `true`로 켜서, 안드로이드 최신 제스처 시스템과 완벽히 동화되도록 커밋(`79ce0c8`)했습니다.

3. **Hardware Back Button Intercept (Modal/Sheet)**
   - **현황**: `NavGraph` 내 커스텀 하단 시트(`VillageMenuSheet`) 오픈 시, 물리적 뒤로가기 버튼이 "시트 닫기"가 아닌 "화면 이탈"로 작동하는 치명적 네이티브 UX 트랩이 있었습니다.
   - **조치 (수정완료)**: `BackHandler`를 주입하여 오버레이 상태를 올바르게 통제하도록 선제적으로 커밋(`bcf7a09`)했습니다.

## Part 2: Performance, Storage & Keyboard

4. **Scoped Storage & Permissions (API 29+ / API 33+)**
   - **현황**: `app.json`에 `READ_EXTERNAL_STORAGE` (API 32 이하)와 `READ_MEDIA_IMAGES` (API 33 이상)가 모두 올바르게 선언되어 있어, 구형 안드로이드부터 최신 14까지 이미지 첨부 권한 획득 시 크래시가 나지 않는 구조를 갖췄습니다.
   - **조치**: 통과 (양호)

5. **Software Keyboard (IME) Animation (API 30+)**
   - **현황**: 현재 `app.json`에 `softwareKeyboardLayoutMode: "resize"`가 적용되어 있고, 앱 전반에 `KeyboardAvoidingView`가 사용되고 있습니다.
   - **한계점 (Future-proof)**: Android 11(API 30)부터 도입된 부드러운 키보드 애니메이션(`WindowInsetsAnimation`)은 React Native 기본 스택만으로는 완벽히 iOS처럼 60fps로 동기화되지 않습니다. 
   - **권고**: 추후 텍스트 에디팅(채팅/노트) UX를 극한으로 끌어올리려면, 향후 React Native 0.76+ 업그레이드 시나리오나 `react-native-keyboard-controller` 네이티브 모듈 도입을 고려해야 합니다. 현재로서는 차선책으로 충분히 동작하므로 코드를 엎지 않고 유지합니다.

---
**[결론]**
Android 10+ 호환성과 Native UX 기준에서 치명적인 결함들은 모두 제 워크트리(`2ndB-antigravity`)에 보완되었으며, 현재 상태로도 Android 사용자는 "RN으로 대충 만든 앱"이 아니라 "플랫폼 이해도가 높은 네이티브 앱"으로 느낄 수준에 도달했습니다.

오케스트레이터 Claude는 제 브랜치의 최신 커밋들(`931e9f8`, `bcf7a09`, `79ce0c8`)을 다음 통합 주기에 반영해 주기 바랍니다.
