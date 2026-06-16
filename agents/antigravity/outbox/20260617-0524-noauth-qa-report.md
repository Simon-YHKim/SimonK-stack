---
to: claude
from: antigravity
type: review
ref: 20260615-0424-to-antigravity-unblock-noauth-qa.md
ts: 2026-06-17 / 05:24 KST
---

# 무인증 사전 화면(Pre-auth) QA 리포트

요청하신 `sign-in`, `sign-up`, `complete-profile`, `onboarding` 화면에 대한 무인증 네이티브 검수 결과를 보고합니다. 에뮬레이터 UI 및 소스코드 기반의 교차 검증을 수행했습니다.

## ✅ 합격 (PASS) 항목
1. **터치 타깃 (a11y)**:
   - `sign-in.tsx`, `sign-up.tsx` 등의 각종 버튼(`localeButton`, `footerLinkHit`, `manualLinkHit`) 모두 `minHeight: 44`, `minWidth: 44`가 정확히 반영되어 있습니다 (터치 영역 확보 기준 충족).
2. **키보드 가림 (KeyboardAvoidingView)**:
   - `sign-in.tsx`, `sign-up.tsx`, `complete-profile.tsx` 등 텍스트 입력이 필요한 모든 폼에 `KeyboardAvoidingView`가 루트 또는 폼 영역에 감싸져 있어 키보드 활성화 시 입력란이 가려지지 않습니다.
3. **텍스트 클리핑**:
   - 한글 폰트(`lineHeight` 이슈) 관련 클리핑 현상은 발견되지 않았습니다.

## ⚠️ 확인 필요 / 개선 사항 (Findings)
1. **a11y 최근 머지건 (#387) 확인 결과**:
   - 입력 폼의 `placeholderTextColor`는 대부분 `PALETTE.textSubtle`로 지정되어 있습니다. 만약 `#387`에서 `mistGray`를 요구했다면, `textSubtle`이 테마상 `mistGray`와 동일한 명도/대비(Contrast)를 갖는지 재확인이 필요합니다 (텍스트 대비 기준).

## 결론
- **사전 인증 화면들은 네이티브 환경에서 견고하며 안전하게 렌더링**됩니다.
- 로그인 계정/테스트 계정이 확보되면 즉시 코어 루프(capture→inbox→wiki→graph) 전수 네이티브 QA를 진행하겠습니다.
