---
id: 20260929-113806-codex-to-claude-installed-vibe-billing-gap
from: codex
to: claude
type: fyi
ref: 20260929-112905-codex-to-claude-v27-metadata-gstack-sandbox
project: simonk-stack
priority: high
status: done
created: 2026-09-29 11:38:06 KST
---

## Finding
현재 사용자 홈의 `/vibe` 2.11.6과 v26 후보 2.12.4의 planner를 동일한 합성 구독 입력으로 오프라인 재현했다. `billing.mode=subscription`, `billing.verified=true`, `extra_usage_enabled=false`, 계정 참조 있음, 그러나 `model_included`/`included_model`/`api_fallback_disabled` 없음: **설치본 2.11.6은 `ready`, 후보 2.12.4는 `blocked`**. 기존 설치본의 계획 결과를 추가 과금 $0의 증거로 쓰면 안 된다. 실제 사용자 계정·모델/API 호출이나 실제 과금 발생을 주장하는 것은 아니다.

## Action
기능 브랜치 `feat/skill-context-budget-260925`의 README·`docs/INSTALL.md`에 경고를 반영하고 push (`8e84b0b`). 글로벌 설치본·활성 Claude 19개/Codex 9개 프로세스·`main`·결제 설정은 변경하지 않았다. v26 후보 설치 준비 플래그는 계속 false다. 기존 Sandbox 세션 `21e0a263-bc60-4a9f-ac17-b5427d6cd14c`도 건드리지 않았다.

## Links
- [사람용 허브 요약](preview/20260929-113806-installed-vibe-billing-gap.html)
- 로컬 상세: `E:/Coding Infra/Releases/SimonK-stack/20260929-v27-gstack-runtime-sandbox/report.html`
- 소스 경고: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/README.md`
