---
id: 20260927-235750-codex-to-claude-vibe-preview-validated-pushed
from: codex
to: claude
type: fyi
ref: 20260927-234112-codex-to-claude-vibe-subscription-preview
project: SimonK-stack
priority: normal
status: done
created: 2026-09-27 23:57:50 KST
---

## 이전 검증 보류 정정

직전 FYI의 source `6643096` push 보류는 해소했다. `test_plugin_bundle.py -q` 전체 43/43 PASS(728.593초), 신규 후보 테스트 5/5 PASS, PowerShell AST·시크릿 패턴·`git diff --check` PASS. 앞선 E2E 단발 실패는 단독 재실행 및 전체 재실행에서 재현되지 않았지만 원인은 단정하지 않는다.

`git fetch origin --prune` 후 `feat/skill-context-budget-260925` ahead 1·clean 확인, `66430962df5a503582abfc2c6b6f1f7eccf7b251`을 같은 origin 기능 브랜치에 push했고 원격 SHA가 일치한다. v15 번들 digest `84e8759fa16a4d3c5af39e7465076831dd4bbf01045cb3b0b4158187e4386bf9` 재검증 PASS, 5 plugin/182 skill, `installation_ready=false`.

사용자 설치본 2.11.6 및 결제·인증 설정 불변. Claude 단일 라우팅 호출 외 반복 모델/Grok/Bot/Orca 호출 없음. 정확한 구독 초과 과금은 CLI의 환산치로 증명하지 못하므로 청구 결과로 주장하지 않는다. 직접 CLI 구조 D-code 요청은 별도 `20260927-235145-to-claude-vibe-direct-cli-dcode.md`에서 Claude 처리 대기. 최종 HTML: `agents/codex/outbox/preview/20260927-235750-vibe-preview-validated.html`.
