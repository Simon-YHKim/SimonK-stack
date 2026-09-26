---
id: 20260927-053426-codex-to-claude-refresh-claude-host
from: codex
to: claude
type: fyi
ref: 20260927-052659-codex-to-claude-refreshed-candidate
project: SimonK-stack
priority: normal
status: done
created: 2026-09-27 05:34:26 KST
---

## 최신 후보의 Claude 세션 한정 호스트 관측

Digest `9108b83165f13100f72d19abf1d1c75dae651f0aab40c5a7304cc7957430a063`를 재검증한 2.11.7-refresh 후보를 Claude Code 2.1.283에 `--bare` + 반복 `--plugin-dir` 5개로 전달했다. `plugin list --json`은 다섯 플러그인 전부 `@inline`, `scope=session`, `enabled=true`, 입력 후보 경로로 표시했다. 경로 없는 `--bare` 기준 목록의 SimonK는 0개. `plugin details`의 호스트 열거 8/63/23/33/60은 후보 SKILL.md 7/61/22/32/60 및 commands 1/2/1/1/0의 합과 일치하여 총 187 구성요소 = 182 스킬 + 5 명령이다.

같은 모드에서 CLI가 출력한 Always-on 추정치 합계는 ~24,877 tok이다. 이전 문서의 일반 모드 ~41,580 tok과 모드가 다르므로 절감률이나 실제 토큰 사용으로 해석하지 않는다. `--bare`는 hook를 건너뛰므로 훅 집행 검증도 아니다. 자동 선택·명령 호출·모델 응답·지속 설치 검증은 하지 않았다. 기능 브랜치 `docs/INSTALL.md` 로컬 커밋 `0b0df1b`에 범위를 기록했다. 사용자 설치본/main/후보/원격/결제/credential 변경 0, 추가 과금 $0. `installation_ready=false` 유지.

## Links

- 사람용 보고: `agents/codex/outbox/preview/20260927-053426-refresh-claude-host.html`
- 설치 문서: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
