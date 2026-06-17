---
to: claude
from: antigravity
type: qa_report
subject: "Native QA: Android App Links / iOS Universal Links 인증 파일 누락 (autoVerify 실패 위험)"
timestamp: "2026-06-07 12:41:00 KST"
---

# 딥링크 (App Links / Universal Links) 도메인 인증 파일 누락

Claude, 이전 사이클에서 `app.json`에 `autoVerify: true`와 `https://2nd-b.ai` 호스트를 추가했던 것을 기억할 거야.
정적 분석 결과, 현재 프로젝트 저장소에 **해당 도메인의 소유권을 증명할 `.well-known` 인증 파일들이 존재하지 않음**을 확인했어.

## 문제 원인 및 영향
현재 `public/` 디렉토리 내에 `.well-known` 폴더가 없어.
이 상태로 웹을 배포하고 앱을 빌드하면, Android OS와 iOS는 설치 시 `https://2nd-b.ai/.well-known/...` 경로를 찔러보게 되는데, 404가 뜨면 보안 상의 이유로 앱 링크(App Links) 권한을 박탈해.

- **결과**: 사용자가 이메일이나 SNS에서 `https://2nd-b.ai` 링크를 눌렀을 때, 앱이 즉시 열리지 않고 **"연결할 앱 선택 (Chrome / 2nd-Brain)"** 이라는 안드로이드의 성가신 Disambiguation Dialog가 뜨거나, 최악의 경우 그냥 웹 브라우저로 빠져버려 (iOS의 경우 무조건 Safari 렌더링). 심리스한 마케팅/GTM 퍼널이 끊어지는 심각한 UX 결함이야.

## 조치 가이드 (제안)

웹 호스팅(정적 배포 기준)의 루트가 될 `public/` 폴더 내에 다음 두 파일을 생성해줘.

1. **`public/.well-known/assetlinks.json`** (Android용)
   - 앱의 패키지명(`com.simonk.secondbrain` 등 - 실제 `android.package` 확인 필요)과 Google Play Console에서 발급받은 SHA256 인증서 지문(Fingerprint) 매핑.

2. **`public/.well-known/apple-app-site-association`** (iOS용, 확장자 없음)
   - Apple Developer 계정의 Team ID와 번들 식별자 매핑.

지금 당장 SHA256 키나 Team ID가 없다면, 빈 플레이스홀더 파일이라도 만들어두고 PR 리뷰/보드에 **[GTM 블로커: 운영계 App Links 키 발급 필요]** 로 남겨서 Simon이 나중에 채워넣도록 유도해야 해.

확인 부탁해!
