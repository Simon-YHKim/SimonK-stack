---
id: 20260928-123103-codex-to-claude-v20-claude-init
from: codex
to: claude
type: fyi
ref: ""
project: SimonK-stack
priority: normal
status: done
created: 2026-09-28 12:31:03 KST
---

## Simon 직접 요청: 추가 과금 없이 Claude v20 초기화 검증

새 무인증·네트워크 차단 Windows Sandbox에서 Claude Code 2.1.283의
`--init-only`를 대조군과 5개 `--plugin-dir` 후보에 직접 실행했다.
두 CLI 호출 모두 게스트에서 측정한 `$LASTEXITCODE`가 0이다. 후보
디버그 로그에는 5개 플러그인, 182개 스킬(중복/사용자 소유 제외 0),
5개 명령 로딩과 `[ERROR]` 0개가 기록됐다. 번들 digest
`9b0980aedf7af578b96eaba1d1586f6aab2a85cc7a708c640363c92572ba1318`
재검증도 통과했다.

앞선 프로브의 `Start-Process -PassThru` 객체 `ExitCode`는 빈 값이었는데
검사기가 이를 실패로 오판했다. 해당 실행은 종료 판정에서 제외하고,
게스트 안에서 직접 호출한 결과만 채택했다. 시험 게스트는 닫았다.

README/INSTALL/CHANGELOG 한정 증거를 SimonK-stack 기능 브랜치
`feat/skill-context-budget-260925`의 `462680f`로 push했다. 개별 스킬
행동, Gstack 외부 런타임 폐쇄, 기존 사용자 프로필, 구독 과금과
§35 D-code는 여전히 미검증이고 `installation_ready=false`다.
사용자 설치본·원본 main·결제 설정은 변경하지 않았고 모델/API/Bot
실호출도 없었다.

## Links

- HTML 보고서: `E:/Coding Infra/Releases/SimonK-stack/20260928-v20-claude-init-probe/report.html`
- 원시 JSON: `E:/Coding Infra/Releases/SimonK-stack/20260928-v20-claude-init-probe/output-v4/result.json`
- 재현 스크립트·Sandbox 설정: 같은 폴더의 `input/run-v4.ps1`, `sandbox-direct-v4.wsb`
