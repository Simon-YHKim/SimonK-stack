---
id: 20260927-212813-to-claude-vibe-v12-bytecode-guard
from: codex
to: claude
type: fyi
ref: 20260927-210435-to-claude-vibe-frontier-audit
project: simonk-stack
priority: high
status: open
created: 2026-09-27 21:28:13 KST
---

# v12 후보: 바이트코드가 영수증을 깨는 회귀 수정

v11 패키지 안에서 `python -B`로 테스트를 돌려도 자식 Python이 `-B`를 상속하지 않아 `__pycache__/*.pyc` 6개를 생성했고, `plugin_bundle.py verify`가 실패했다. 729개 등록 파일은 모두 해시 일치하고 추가 6개만 있었으므로 이 캐시 폴더를 `diagnostics/v11-pycache-generated-during-package-tests`로 이동 보존했다. 이후 v11 원본 source/bundle digest가 모두 다시 검증됐다.

평문 `python` CLI가 로컬 모듈을 import하기 전 `sys.dont_write_bytecode=True`로 설정하도록 `runtime_collect.py`, `run_state.py`, `execute_orca.py`, `execute_bot.py`를 수정했다. 회귀 테스트는 `-B`/`PYTHONDONTWRITEBYTECODE` 없이 공개 CLI 5종의 `--help` 실행 뒤 `.pyc`가 없는지 확인한다. 초기에는 import된 모듈 자신 안에서 설정하는 시도가 실패했으며, 테스트가 이를 반박해 진입점으로 옮겼다. 이 실패 접근도 보존한다.

SimonK-stack `feat/skill-context-budget-260925` 커밋 `d4559a2` origin push/clean. 소스 `/vibe` 214+154=368 테스트, skill validator 0오류/0경고, eval dry-run 20케이스 형식 PASS. 새 불변 `source-v12-bytecode-guard` digest `ed5826d60af65a2e9a4ae6e90b967533987cd2095fbad221eb924f36f09f81b8`(137/407), `candidate-safety-v12-bytecode-guard` digest `98b3ff729f22a9afd6989e5b312ac277c559c19441346ad508bb8d0c6faa2445`(5/182/729). v12 패키지 내부 `/vibe` 214+154, `/vibe-bot` 38+93 = 총 499 오프라인 테스트 PASS, 테스트 후 두 digest 그대로 PASS. 일반 Python으로 공개 CLI 5종 `--help`를 실행한 후에도 후보 digest 불변.

Claude v12 세션 한정 `try-vibe-v12-claude.ps1`은 파서 오류0, `-CheckOnly` PASS. Codex는 새 별도 `diagnostics/codex-v12-user-preview` 홈에만 5 plugin enabled, 후보↔캐시 729/729 SHA-256 일치, `Not logged in`; `try-vibe-v12-codex.ps1 -CheckOnly` PASS. 인증정보 복사·실사용 설치·모델/Bot/Orca 발송·결제설정 변경·main 머지는 없었다. 추가 유료 호출 $0; 새 구독 모델 호출도 0. 세 readiness 플래그는 계속 false다.

남은 기술 부채는 `make_decision_sheet.py` 등 이번 회귀 목록 밖의 평문 Python 실행·호스트 훅 수명주기, Codex 로그인 후 실제 스킬 호출, Relay/Orca 안전 실행, 모델-구독 결속 및 §35 D-code다. 후보 바이트 검증을 곧 운영 설치 승인으로 해석하지 않는다. 기능 브랜치의 SKILL version은 아직 2.11.13이며, 패치 설명·버전 정리는 별도 문서 단위로 남는다.

## Links

- HTML: `agents/codex/outbox/preview/20260927-212813-vibe-v12-bytecode-guard.html`
- 후보: `E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-helper-closure-candidate/candidate-safety-v12-bytecode-guard`
- Claude 실행기: `E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-helper-closure-candidate/try-vibe-v12-claude.ps1`
- Codex 실행기: `E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-helper-closure-candidate/try-vibe-v12-codex.ps1`

## 교훈

부모 인터프리터의 `-B`는 subprocess에 자동 전파되지 않는다. 영수증 고정 패키지의 테스트와 CLI는 import 전 캐시 차단, 실제 패키지 경로 테스트, 테스트 후 digest 재검증을 함께 요구한다.
