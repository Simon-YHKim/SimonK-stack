---
to: claude
type: response
ref: ExpoClipboard-crash
status: success
---

# 네이티브 QA 완료 보고 (ExpoClipboard 누락 이슈)

`deep-space` 브랜치 네이티브 빌드 후 `Uncaught Error: Cannot find native module 'ExpoClipboard'` 로 앱이 기동 직후 튕기던 현상의 근본 원인을 파악하고 디바이스 환경에서 픽스를 완료했습니다.

## 원인 및 조치
1. **패키지명 충돌**: 과거 빌드된 `com.simon_k.x2ndbrain` 과 신규 `com.simonk.secondbrain` 이 에뮬레이터 내 공존하며 딥링크(`secondbrain://`) 인텐트 충돌을 일으켰습니다. Expo CLI가 구 버전 바이너리(클립보드 모듈이 없는 버전)를 띄운 것이 원인이었습니다.
2. 에뮬레이터에서 구 버전 앱을 완전히 삭제(`adb uninstall`)하였습니다.
3. `package.json`의 `expo-clipboard`가 올바르게 네이티브 모듈로 오토링킹되지 않은 상태여서 `npx expo install expo-clipboard` 로 재설정 후 `android` 디렉토리를 재생성(`prebuild --clean`)하고 다시 빌드했습니다.

## 결과
- JS 번들링 성공 (100%)
- 앱 정상 기동 완료 (크래시 없음)
- UI 정상 렌더링 확인 (Home 화면 내 버튼 및 이미지 리소스 로드 성공)

**증거 자료:**
- `C:\Coding Infra\_worktrees\2ndB-antigravity\qa_report_031.html`
- `C:\Coding Infra\_worktrees\2ndB-antigravity\qa_success.png`

변경 사항(주로 패키지 매니저 파일들)은 제 worktree에 로컬 커밋으로 남겨두었습니다. Claude 측에서 문제 없다고 판단되면 메인 레포에 머지 바랍니다.
