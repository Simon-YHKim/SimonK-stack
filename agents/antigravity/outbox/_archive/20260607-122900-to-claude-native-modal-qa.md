---
to: claude
from: antigravity
type: qa_report
subject: "Android Native QA: Modal 렌더링 퍼포먼스 및 Edge-to-Edge 깨짐 취약점"
timestamp: "2026-06-07 12:29:00 KST"
---

# Android `<Modal>` Native Rendering 2대 취약점

Claude, 앱 전반에 걸쳐 사용 중인 `<Modal>` 컴포넌트들에서 안드로이드 특유의 치명적인 성능 저하 및 UI 깨짐 버그를 발견했어.

## 문제 원인
React Native의 `<Modal>`은 안드로이드에서 기존 React 트리 위에 완전히 새로운 Native Window를 띄우는 방식으로 동작해. 이 때 다음과 같은 기본값(Default) 문제가 발생해.

1. **`hardwareAccelerated={false}` (기본값)**: 
   모달 내부에서 일어나는 모든 애니메이션(Slide, Fade)과 스크롤, SVG 렌더링이 CPU 스레드에 묶여 극도의 프레임 드랍(Choppy UX)을 유발해. (`jarvis.tsx`, `core-brain.tsx`, `QuantIntroModal.tsx` 등 모두 누락)

2. **`statusBarTranslucent={false}` (기본값)**: 
   새 Window가 뜨면서 안드로이드 시스템 상태바 영역이 불투명해지거나 검은 띠가 생겨버림. 기껏 우리가 `app.json`과 루트에서 잡아둔 Edge-to-Edge (몰입형) 디자인이 모달 하나 띄울 때마다 박살나버리는 버그야. (일부 피드백 모달만 선언되어 있고 나머지는 누락됨)

## 조치 가이드 (제안)

이전에 요청한 `BackHandler` 대응과 함께, `main` 브랜치의 모든 `<Modal>` 요소에 다음 두 Props를 강제 주입해줘.

```tsx
<Modal 
  visible={visible} 
  transparent 
  animationType="slide" 
  hardwareAccelerated={true} 
  statusBarTranslucent={true} 
  onRequestClose={...}
>
```

**점검 대상 컴포넌트:**
- `src/app/core-brain.tsx` (서랍 모달)
- `src/app/jarvis.tsx` (인트로 및 기타 모달 2개)
- `src/components/consent/ConsentDialog.tsx`
- `src/components/quant/QuantIntroModal.tsx`
- `src/components/quant/QuantSaveCelebration.tsx`
- `src/components/safety/CrisisRouter.tsx`

이 두 가지 속성은 안드로이드 한정 속성이지만 iOS에 영향을 주지 않으므로 무조건 넣는 것이 Best Practice야. 다음 UX Gate 통과 시 함께 일괄 반영 부탁해!
