---
id: 20260928-235511-codex-to-claude-v21-candidate-fyi
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-28 23:55:11 KST
---

## Deliverable

Simon의 추가 과금 $0·구독 범위 조건 아래, 최신 G5 및 페르소나 근거 검사를 포함한 v21 격리 후보를 새 경로에 만들었습니다. 기존 v20·사용자 설치본은 보존했습니다. 입력 플러그인 5개는 고정 HEAD와 clean 상태였고 별도 LF 로컬 복제본으로 빌드했습니다. source digest `d3056d93e76cc44a9c0c43ad7ebf6c8460c83dc052c9a0935fe595575a3c756c`, candidate digest `4e726c41e3c23029923f1bd44b439da18c71d2a7cf5ad5268f25ada052df5486`, Codex overlay digest `483d5147184e1838f920f69db033cd03ff5af2b25488202bdbbc654f44cb3d05`입니다. README·INSTALL 기록은 소스 기능 브랜치 `188d867`로 push/clean입니다.

## Acceptance

- 후보 5플러그인·182스킬·736파일, source-v21 137스킬·411파일. 변경 핵심 4파일은 소스·후보·오버레이 SHA-256 일치; v20과 v21 영수증 모두 재검증.
- 후보 `/vibe` 단위220/220·자체180/180, 일회용 복사본 스모크4/4, 관련 패키징·페르소나119/119, Codex manifest5/5, 기본 후보 catalog182 통과.
- 새 네트워크·클립보드 차단, 무인증 Windows Sandbox에서 Claude Code2.1.283 `--init-only` 대조군/후보 모두 rc0, 플러그인5·스킬182·명령5, 디버그 오류0, 전후 활성 네트워크 어댑터0. 이번 Sandbox 세션만 종료함.
- 정적 경로 감사의 미해결0이지만 Gstack 외부 런타임31스킬/646직접참조/9대상으로 `external_runtime_pending` 종료1. Codex overlay 기본 catalog는 `zoom-out` 투영과 원본 영수증 불일치로 종료2; 별도 manifest 검증은 이 실패의 대체 증거가 아님. 세 readiness 플래그 false 유지.
- PR #54 HTML 규칙, Claude 소유 §35 오버레이 결정, 기존 사용자 프로필·Gstack 전이·실제 Bot/Orca·구독 과금 증거가 남음. 사용자 설치·main 머지·모델/API/Bot/Orca 실호출·결제 설정 변경은 없었음.

## Links

- HTML 보고서: `E:/Coding Infra/Releases/SimonK-stack/20260928-v21-g5-persona/report.html`
- Sandbox 재현 입력·결과: `E:/Coding Infra/Releases/SimonK-stack/20260928-v21-g5-persona/sandbox-init-v21/`
- 소스: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925`
