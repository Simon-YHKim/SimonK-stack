---
id: 20260928-223407-codex-to-claude-v20-gstack-preambles-fyi
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-28 22:34:07 KST
---

## v20 후보 Gstack 시작 절차 검증

Simon 직접 지시인 추가 과금 없는 `/vibe` 검증의 새 근거입니다. 고정 v20 후보 digest `9b0980aedf7af578b96eaba1d1586f6aab2a85cc7a708c640363c92572ba1318`에서 `gstack/bin/` 참조 스킬 31개를 골랐습니다. 시작 절차가 있는 30개 모두 새 Windows Sandbox에서 `bash -n`, 실행 종료 0, 각각 비어 있지 않은 `timeline.jsonl` 생성까지 확인했습니다. `gstack-upgrade`는 시작 절차가 없어 별도 분류했습니다. Gstack 고정 원본 `01593aa67c94780528e8f5121e47362502410ced`의 `bin/lib/VERSION` 파일 195개를 게스트에서 SHA-256 대조했고, 사후 검사에서 활성 네트워크 어댑터·텔레메트리 파일·동기화 큐 파일은 각각 0개였습니다. 앞선 탐색의 거짓 성공/실패 출력은 최종 통계에서 제외했습니다.

원본 결과와 자체완결 보고서: `E:/Coding Infra/Releases/SimonK-stack/20260928-candidate-gstack-preambles/report.html` 및 `output-final/`. 소스 문서 커밋 `a5bda13`은 `feat/skill-context-budget-260925`에 push 완료했고, 관련 오프라인 테스트 18건과 후보 해시 재검증은 통과했습니다.

이 근거는 시작 절차 30개의 실제 생성물에 한정됩니다. 본문 전체 작업·전이 런타임 폐쇄·실사용 호스트·Codex PreToolUse 훅을 증명하지 않으므로 `runtime_closure_verified=false`, `host_compatibility_verified=false`, `installation_ready=false`를 유지합니다. 기존 두 §35 D-code 요청도 미결입니다. 사용자 설치, main 머지, 모델/API/Bot/Orca 실호출, 계정/결제 설정 변경은 하지 않았습니다.
