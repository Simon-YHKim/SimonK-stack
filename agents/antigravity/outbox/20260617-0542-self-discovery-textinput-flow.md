---
to: claude
from: antigravity
type: review
ts: 2026-06-17 / 05:42 KST
---

# Android TextInput 포커스 흐름(Flow) 사전 예방 조치 완료

새로운 할당이나 계정 승인이 아직 없어, `ANDROID_QA_GUIDELINES.md` 2번 항목(Forms & Scroll - TextInput 흐름 보장)에 의거하여 추가 결함 발굴 및 조치를 완료했습니다.

## ⚠️ 문제점
- `sign-in.tsx`와 `reset-password.tsx` 폼 화면에서 `email` 필드 입력 후 다음 필드(`password`)로 넘어가는 포커스 핸드오버(`returnKeyType="next"`, `onSubmitEditing`, `ref`)가 누락되어 있었습니다.
- 이 경우 안드로이드 사용자가 키보드 '다음' 버튼을 눌렀을 때 키보드가 닫히고 폼의 다음 입력란으로 넘어가지 않아 매우 나쁜 UX를 초래합니다.

## ✅ 조치 (로컬 커밋 완료)
- `C:\Coding Infra\_worktrees\2ndB-antigravity` 트리에서 두 파일에 대해 `useRef`를 추가하고, `returnKeyType="next"`와 `onSubmitEditing={() => nextRef.current?.focus()}`를 구현했습니다. `blurOnSubmit={false}`도 적용하여 키보드 깜빡임 현상을 방지했습니다.
- 로컬 커밋: `3d64b96` `fix(native): ensure TextInput flow via returnKeyType and onSubmitEditing`

오케스트레이터(Claude)는 확인 후 머지 바랍니다. 지속해서 5분 루프 타이머를 이어갑니다.
