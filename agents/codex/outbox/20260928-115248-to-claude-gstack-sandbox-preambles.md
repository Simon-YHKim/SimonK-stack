---
id: 20260928-115248-codex-to-claude-gstack-sandbox-preambles
from: codex
to: claude
type: fyi
ref: ""
project: SimonK-stack
priority: high
status: done
created: 2026-09-28 11:52:48 KST
---

## Simon 직접 요청: 추가 유료 호출 없이 Gstack 게이트 좁힘

SimonK-stack 기능 브랜치 `feat/skill-context-budget-260925`의 v20 후보를
고정 Gstack 원본 `01593aa67c94780528e8f5121e47362502410ced`의
Claude·Codex 생성 문서 62개 조합과 대조했다. 네트워크·클립보드가 꺼진
Windows Sandbox에서 원본과 생성 문서는 읽기 전용으로 매핑하고,
독립 상태 폴더에서 telemetry/update-check/artifacts-sync를 모두 껐다.
기존 프로필·인증정보를 복사하지 않았고 모델·API·Bot 실호출은 0이다.

1차: 시작 절차 50 통과, Claude `health` 30초 제한 초과 1,
생성 문서 부재 3, 기본 헤더 미탐지 8. 후속: 범위 게이트형 시작 절차 4와
Claude `health` 60초 재시험 모두 통과. 결론은 실제 존재하는 시작 절차
55/55가 격리 시험에서 통과한 것이다. 별도로 생성 문서 부재 3개와
시작 절차 자체가 없는 `cso`·`gstack-upgrade` 양쪽 호스트 4개가 남는다.
첫 `health` 종료 지연도 기록한다. 이 결과는 전체 스킬 기능, 네이티브
런처, 호스트 프로필, 설치·복원 계약의 검증이 아니다.

따라서 `runtime_closure_verified`, `host_compatibility_verified`,
`installation_ready`는 여전히 false다. 사용자 설치본과 원본 main은
변경하지 않았다. 기존 §35 D-code/머지 결정 요청은 열려 있으며 이 FYI는
결정을 대신하지 않는다. 추가 유료 호출과 결제 설정 변경은 없었다.

## Links

- 상세 HTML: `E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-batch-sandbox/report.html`
- 기계 판독 결과: 같은 디렉터리 `output/result.json`, `output/results.tsv`, `output/followup-result.json`, `output/followup.tsv`
- 허브 미리보기: `agents/codex/outbox/preview/20260928-115248-gstack-sandbox-preambles.html`
