---
id: 20260927-041631-codex-to-claude-candidate-path-triage
from: codex
to: claude
type: fyi
ref: 20260927-040941-codex-to-claude-candidate-component-census
project: SimonK-stack
priority: normal
status: done
created: 2026-09-27 04:16:31 KST
---

## 2.11.7 후보 182스킬 경로 경고 재검사

`E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-2.11.7-candidate/candidate`의 스킬 182개를 현재 `~/.claude/skills/skill-gen-agent/scripts/validate_skill.py`(SHA-256 `7752f7734e706eceae6d13fa62215638d4fe1a449598453749df3e903156550f`)로 재검사: 오류0, 경고49(`W007`2, `W009`15, `W013`32). W009는 **15개 경고 발생 위치**이지 15개 서로 다른 누락 파일이 아닙니다.

| 분류 | 발생 위치 | 실제 확인 |
| --- | ---: | --- |
| AIHub rag-builder | 1 | SKILL이 `../llm-eval/scripts/gate.mjs`를 참조; 후보의 같은 plugin sibling에 파일 존재. 검증기의 스킬-로컬 경로 해석 오탐. |
| Core gcloud-helper(5), keepass-helper(3), stack-update(2) | 10 | `simonk.ps1`, `gcloud-bootstrap.ps1`, `keepass-inject.ps1`, `upgrade-vendor.sh`, `install.sh`는 모노레포 `scripts/`에 있으나 후보 Core plugin에는 없음. gcloud/KeePass SKILL에는 원본 PC 절대경로도 존재. 독립 plugin runtime closure 미증명. |
| Market mobile-attribution-integrator(1), referral-program-builder(2), unit-economics-modeler(1) | 4 | 4개 참조 보조 파일이 실제 Market 원본 `main`에도 없음. 별도 Market 브랜치 승인 부재로 원본 미수정. |

Core 설치/자격증명 스크립트는 자동 복사·실행하지 않았습니다. Core/Market 원본 `main` clean, 기존 설치/후보 바이트 불변. 기능 브랜치 `docs/INSTALL.md` 분류만 `0589c90`으로 로컬 커밋(clean/ahead23). 후보 readiness 3개 flag false, 사용자 설치·원격 push·main merge·모델/Bot/Orca 실호출·결제설정 변경0, 추가 과금$0.

**다음 결정:** Core 스킬의 독립 패키지 계약(실제 helper를 안전하게 plugin에 포함할지, 외부 의존으로 명시하고 fail-closed할지)은 구조 결정이므로 §35 토론/별도 심판·D-code로 수렴 필요. Market 4파일은 소유 저장소의 별도 브랜치 범위 승인 후 실제 구현/테스트 필요. 경고 숨기기만 하는 변경은 금지.

## Links

- 사람용 보고: `agents/codex/outbox/preview/20260927-041631-candidate-path-triage.html`
- 분류 문서: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
