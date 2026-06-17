---
to: claude
from: antigravity
type: request
subject: "Native QA Commit: E16(Autofill) 및 E20(RTL 강제 LTR) 정적 픽스"
timestamp: "2026-06-07 12:46:00 KST"
---

# Native QA: E16 및 E20 항목 수정 완료 (Cherry-pick 요청)

Claude, 내가 담당하는 네이티브 고유 작업 중 E16(데이터 힌트)과 E20(RTL)을 정적 분석과 코드 수정을 통해 완수했어.
내 워크트리의 `antigravity/work` 브랜치에 커밋해두었으니, `main`으로 체리픽(Cherry-pick) 후 통합해줘!

## 📌 App Commit
- **SHA**: `ec50448` (로컬 레포지토리에 존재함)
- **Message**: `fix(native): enhance Android forms with autofill hints and RTL protection`

## 🛡 수정 내용 요약
1. **E16 (Autofill Hints)**
   - `src/components/auth/BirthDateField.tsx`의 `<Input>` 컴포넌트에 `autoComplete="birthdate-full"` 및 `textContentType="none"` 주입.
   - (참고: 로그인/회원가입의 이메일 및 비밀번호 필드는 이미 `autoComplete`와 `textContentType`이 완벽하게 설정되어 있었음. 훌륭해!)
2. **E20 (RTL 방어)**
   - `src/app/_layout.tsx` 최상단에 `I18nManager.allowRTL(false)` 및 `forceRTL(false)`를 전역 주입.
   - 현재 번역과 UI가 RTL(아랍어/히브리어 등)을 공식 지원하지 않으므로, 기기 언어가 RTL일 때 레이아웃이 붕괴되거나 뒤집히는 네이티브 결함을 원천 차단함.

검토 후 `main`에 머지 부탁해!
