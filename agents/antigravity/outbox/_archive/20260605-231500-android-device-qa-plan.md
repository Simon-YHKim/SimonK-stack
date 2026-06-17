# [Device-QA Plan] 2nd-B Android Native Readiness Audit

**Agent**: Antigravity (Android device-QA)  
**Date**: 2026-06-05  
**Device/Env**: Pixel 9 Pro XL (Android 14+, API 34), Emulator/Real Device  
**Scope**: P0 UX/Layout Verification for Android Platform

## 1. 개요 (Overview)
본 계획서는 2nd-B 안드로이드 앱의 고유 UX 요소 및 레이아웃 무결성을 검증하기 위한 상세 QA 절차를 정의한다. 특히 하드웨어 뒤로가기 버튼 처리, Safe-Area 대응, 키보드 가림 현상 등 안드로이드 특화 항목에 집중한다.

## 2. 검증 항목 및 절차 (QA Items & Procedures)

| 항목 | 검증 대상 | 재현 절차 (Reproduction) | 기대 동작 (Expected Behavior) | 합격 기준 (Success Criteria) |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Empty Graph Safe-Area** | 1. 신규 계정으로 로그인 (데이터 없음)<br>2. 메인 그래프 화면(index) 진입<br>3. 하단 'Empty Graph' 카드 확인 | 하단 네비게이션 바/제스처 바와 카드 버튼 사이에 충분한 간격이 유지됨. | `paddingBottom`이 적용되어 CTA 버튼('Leave a first piece')이 가려지지 않고 온전히 클릭 가능해야 함. |
| **2** | **Onboarding Hardware Back** | 1. 온보딩 진입<br>2. 2~3단계까지 진행<br>3. 안드로이드 하드웨어 뒤로가기 버튼 클릭 | 앱이 종료되지 않고 온보딩의 이전 단계(Step)로 이동함. | 단계별 후퇴가 정상 작동하며, 0단계에서 버튼 클릭 시에만 앱 종료/백그라운드 이동이 발생해야 함. |
| **3** | **PremiumBottomSheet Back** | 1. 피드백 또는 설정 등 BottomSheet 호출<br>2. 시트가 열린 상태에서 하드웨어 뒤로가기 버튼 클릭 | 현재 열려 있는 바텀 시트만 닫힘. | 화면 뒤로가기(Navigation Back)가 발생하지 않고 시트만 성공적으로 Dismiss 되어야 함. |
| **4** | **Keyboard Avoiding (Sign-in/Capture)** | 1. 로그인 또는 캡처 화면 진입<br>2. 입력칸(Email, Title 등) 터치하여 키보드 호출 | 키보드가 올라오면서 입력칸이 키보드 위로 노출되거나 화면이 적절히 시프트됨. | 키보드가 입력 중인 텍스트 필드를 가리지 않아야 하며, `softwareKeyboardLayoutMode: "pan"` 상태에서의 시인성 확인. |
| **5** | **Edge-to-Edge Layout (Notch/Status)** | 1. 앱 실행 후 최상단 상태표시줄(StatusBar) 영역 확인<br>2. Pixel 9 Pro XL의 중앙 펀치홀(Notch) 주변 UI 확인 | 배경색/이미지가 상태표시줄 영역까지 확장(Translucent)되면서도, 텍스트나 버튼은 노치에 가려지지 않음. | `windowTranslucentStatus`가 적용되어 배경이 상단 끝까지 차오르되, 중요한 UI(닫기 버튼, 타이틀)는 Safe Area 내부에서 안전하게 렌더링되어야 함. |

## 3. 기술적 진단 메모 (Antigravity's Notes)
*   **Empty Graph**: `src/app/index.tsx`에서 `Math.max(88, insets.bottom + 64)`를 통해 동적 패딩을 부여하고 있음. 제스처 모드와 3버튼 모드 각각에서 버튼 가림 여부 정밀 확인 필요.
*   **BackHandler**: `onboarding.tsx`와 `feedback.tsx`에서 `BackHandler`를 사용해 하드웨어 이벤트를 가로채고(Consume) 있음. `return true` 로직이 누락되어 이벤트가 전파(Bubble)되지 않는지 확인.
*   **Keyboard**: `app.json`에 `softwareKeyboardLayoutMode: "pan"`으로 설정되어 있음. `adjustResize`가 아닌 `pan`을 선택한 의도가 캡처 화면의 배경 유지를 위한 것인지, 이로 인해 하단 입력칸이 가려지는 부작용은 없는지 대조군(adjustResize)과 비교 검토.

---
*본 문서는 PROTOCOL 10.5에 의거하여 진단 및 계획 용도로만 작성되었으며, 코드 수정은 포함하지 않습니다.*
