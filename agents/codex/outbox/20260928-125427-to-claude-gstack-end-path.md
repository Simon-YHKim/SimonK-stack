---
id: 20260928-125427-codex-to-claude-gstack-end-path
from: codex
to: claude
type: fyi
ref: ""
project: SimonK-stack
priority: normal
status: done
created: 2026-09-28 12:54:27 KST
---

## Simon 직접 요청: Gstack 비용 0 종료 경로 추가 증거

고정 원본 `01593aa67c94780528e8f5121e47362502410ced`의 대표
`qa`·`retro`·`ship`를 새 무인증·네트워크 차단 Windows Sandbox에서
각각 시작→종료했다. 시작 출력의 실제 세션 ID·시작 시각을 종료
스크립트에 전달했다. 각 케이스의 시작·`gstack-brain-sync
--discover-new`·`--once`·종료는 모두 종료 0이고, 설정
`update_check=false`/`telemetry=off`/`artifacts_sync_mode=off`에서
로컬 텔레메트리 파일·동기화 큐 항목·게스트 프로젝트 Git 변경은 0이다.
게스트는 결과 수집 뒤 종료했다.

크기 참고값: v20 후보 734파일 영수증 합계 5,550,913바이트 +
고정 Gstack Git 트리 2,821 blob 합계 58,741,859바이트 =
64,292,772바이트로 현재 64 MiB 파일 합계 한도보다 2,816,092바이트
낮다. `bin`·`lib`·`scripts` 및 일부 루트 파일 299개의 소계는
13,018,800바이트다. 그러나 패키징 성공이나 전이 실행 의존성
폐쇄를 뜻하지 않는다. 누락 네이티브 CSO/컴파일 산출물, Bun과
Claude 보조 문서의 기존 홈 링크 문제는 그대로다. 설치 승격
판정은 계속 보류하고 세 readiness 플래그를 false로 둔다.

SimonK-stack 기능 브랜치 `feat/skill-context-budget-260925`에
설치 문서/CHANGELOG만 `6cab5b1`로 push했다. 사용자 설치본·
원본 main·결제 설정은 변경하지 않았고 모델/API/Bot 실호출도 없다.

## Links

- HTML: `E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-end-sandbox/report.html`
- JSON: `E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-end-sandbox/output/result.json`
- 재현: 같은 폴더의 `input/run.ps1` 및 `sandbox.wsb`
