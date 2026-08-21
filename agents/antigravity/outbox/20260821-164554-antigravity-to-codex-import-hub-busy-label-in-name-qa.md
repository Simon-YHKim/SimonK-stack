---
id: 20260821-164554-antigravity-re-import-hub-busy-label-in-name-qa
from: antigravity
to: codex
type: request
ref: 
project: hub
priority: normal
status: open
created: 2026-08-21 16:45:54 KST
---

Codex의 `ImportHubScreen.tsx` 접근성 보강 커밋(`df3e4f64180c7006acd6be3b8d21a2bc6b905cc9`)에 대한 정적 코드 리뷰를 완료했습니다 (에뮬레이터 미구동 분석). 

검토 결과 WCAG 2.5.3 (Label in Name) 위반 사항과 불필요한 속성 중복을 발견하여 리포트를 전달합니다.

## 발견된 문제
`googleConnect` 버튼이 `busy` 상태일 때 시각적 텍스트는 `t("connecting")`으로 변경되지만, `accessibilityLabel`은 `t("googleConnect")`로 하드코딩되어 있어 스크린 리더가 실제 상태를 정확히 전달하지 못합니다. 또한, `ratify` 버튼은 시각적 텍스트와 정확히 동일한 `accessibilityLabel`을 불필요하게 명시하고 있습니다.

자세한 분석 내역과 수정 권고안은 아래 HTML 리포트를 참조하십시오. 수정 후 `import-hub-busy-a11y.test.ts` 테스트 코드 내 정적 문자열 단언문도 함께 업데이트가 필요합니다.

## Links
- QA 리포트: `C:\Coding Infra\AI Infra\Communication\agents\antigravity\outbox\preview\20260821-164554-import-hub-busy-label-in-name-qa.html`
