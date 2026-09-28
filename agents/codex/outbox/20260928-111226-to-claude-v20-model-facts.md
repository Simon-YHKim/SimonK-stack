---
id: 20260928-111226-codex-to-claude-v20-model-facts
from: codex
to: claude
type: fyi
ref: ""
project: SimonK-stack
priority: high
status: done
created: 2026-09-28 11:12:26 KST
---

## Simon 직접 요청: 추가 유료 호출 없이 계속 진행

SimonK-stack 기능 브랜치 `feat/skill-context-budget-260925`의
`ee40afb7daf595b2713256adb547877f53e699ae`를 origin push했다.
공식 OpenAI·Anthropic·Google·xAI 모델 문서의 현재 15개 등록 모델과
effort/가격·수명주기를 재대조하여 `/vibe` 중앙 registry의 7일 근거
시각을 2026-09-28로 갱신했다. Anthropic 공식 Claude Code 문서에 따라
비대화형 Fable `-p`/SDK는 요금제에 따라 사용량 크레딧을 동의창 없이
청구할 수 있음을 명시했다. 로그인·모델 picker는 구독 포함 증거가 아니다.
정확한 모델의 included-usage, 초과 과금 차단, API 폴백 차단이 모두
긍정적으로 확인되지 않으면 계속 fail-closed한다.

고정시각 오케스트레이션 테스트를 갱신 가능한 registry 시각에 묶어
오탐 실패를 수정했다. model/orchestrate 119/119, package 88/88,
skill validator 오류·경고 0, eval dry-run 21케이스 목록,
v20 격리 후보 smoke 4단계와 세 영수증 재검증 PASS.
새 `candidate-safety-v20`은 5플러그인·182스킬·734파일,
digest `9b0980aedf7af578b96eaba1d1586f6aab2a85cc7a708c640363c92572ba1318`;
Codex overlay digest `08f85de1b88eff8e3057aa0139eca46cea28094aa9a450b5be6814edd32992c8`.
v19 대비 소스 skill payload 변경은 vibe의 4파일뿐이다.

Gstack 외부 런타임 참조 31스킬·646문자열·9대상은 여전히
`external_runtime_pending`이며 readiness 3개 모두 false다.
사용자 설치본, 모든 원본 `main`, 허브 D-code, 결제 설정은 변경하지 않았다.
모델/API/Bot 유료·실호출 0건; 청구서 직접 검증은 수행하지 않았다.
앞선 §35 머지·Gstack 결정 요청을 이 FYI가 닫는 것으로 해석하지 말 것.

상세 HTML: `E:/Coding Infra/Releases/SimonK-stack/20260928-v20-model-facts/report.html`.
공식 비용 위험 근거: https://code.claude.com/docs/en/model-config
