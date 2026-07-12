---
id: 20260712-120053-antigravity-re-structured-payload-labels
from: antigravity
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-07-12 12:00:53 KST
---

커밋 08b99715 (`fix(records): localize the structured-payload grid labels`)에 대한 네이티브/에뮬레이터 검증을 완료했습니다.

레코드 상세 화면에서 4W1H 및 통화 회고 페이로드의 키가 더 이상 기계어(snake_case)로 노출되지 않으며, 사용자 로케일에 맞는 번역된 레이블(누가, 무엇을, 요지 등)로 올바르게 표시됩니다. 미등록 키 또한 정상적으로 첫 글자 대문자의 읽기 쉬운 형태로 변환되어 출력됨을 확인했습니다. 레이아웃 회귀는 없습니다.

## Links
- HTML Report: `agents/antigravity/outbox/preview/20260712-120053-structured-payload-labels-qa.html`
