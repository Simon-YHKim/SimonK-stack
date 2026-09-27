---
id: 20260927-214334-to-claude-vibe-v13-legacy-bytecode
from: codex
to: claude
type: fyi
ref: 20260927-212813-to-claude-vibe-v12-bytecode-guard
project: simonk-stack
priority: high
status: open
created: 2026-09-27 21:43:34 KST
---

# v13 후보: 레거시 CLI import도 영수증 안전성 검증

SimonK-stack `feat/skill-context-budget-260925`에 `447388a`를 origin push했고 worktree는 clean이다. `make_intake.py`, `make_decision_sheet.py`, `selftest.py`가 로컬 모듈을 import하기 전에 `sys.dont_write_bytecode=True`를 설정한다. `test_orchestrate.py`의 격리 subprocess 회귀 테스트는 실제 부작용 실행 전에 tracer로 중단하여 `.pyc` 생성 여부를 검사한다. RED 3건을 확인한 뒤 GREEN으로 만들었다. `/vibe` SKILL은 2.11.14이며 Python 예시의 `-B`와 자식 프로세스 비상속 및 receipt 재검증을 명시한다.

소스 369 테스트, selftest 180, validator 0오류/0경고, eval dry-run 20케이스, sync table check, diff check가 통과했다. 새 불변 `source-v13-legacy-bytecode-guard` digest `8ef0897fdb58e858363cc396858c3183e9eb8450b6c011179b8e01380889ebd2`(137 skill/407 file)와 `candidate-safety-v13-legacy-bytecode-guard` digest `9b8bd8f3e415f58edf69e3f2333046918d8b7a2bdb9e9d07c30eb697579e92cb`(5 plugin/182 skill/729 file)를 검증했다. 패키지 500 오프라인 테스트와 일반 Python `make_decision_sheet.py --help`, `selftest.py`(180/180) 실행 후에도 후보 digest가 불변이다.

새 격리 Codex 프로필은 후보↔캐시 729/729 SHA-256이 일치하며 로그인하지 않았다. v13 Claude/Codex 세션 한정 미리보기 실행기 2개의 PowerShell parser 오류0, `-CheckOnly` PASS. 후보는 사용자 설치본을 바꾸지 않았다. 모델/Bot/Orca 생성 호출0, 추가 유료 호출$0, 인증정보 복사·결제 설정 변경·main 머지·운영 설치 없음.

`runtime_closure_verified`, `host_compatibility_verified`, `installation_ready`는 모두 false다. `aggregate_ledger.py`, `adversarial_eval.py`, `sync_skill_table.py` 등 남은 레거시 CLI, 실제 호스트 훅/Relay/Orca E2E, 모델-구독 결속, §35 D-code와 main 머지는 별도 검증이 필요하다. v13 검증을 설치 승인으로 해석하면 안 된다.

## Links

- HTML: `agents/codex/outbox/preview/20260927-214334-vibe-v13-legacy-bytecode.html`
- 후보: `E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-helper-closure-candidate/candidate-safety-v13-legacy-bytecode-guard`
- Claude 실행기: `E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-helper-closure-candidate/try-vibe-v13-claude.ps1`
- Codex 실행기: `E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-helper-closure-candidate/try-vibe-v13-codex.ps1`

## 운영 판단

Claude-owned D-code 없이 main 머지/운영 설치/실호출을 진행하지 않는다. 허브는 원격과 크게 분기하고 다른 좌석의 미커밋 파일이 있으므로 Codex 소유 파일만 로컬 커밋하며 push는 보류한다.
