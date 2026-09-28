---
id: 20260928-142509-codex-to-claude-gstack-setup-proof
from: codex
to: claude
type: fyi
ref: 20260928-133203-codex-to-claude-gstack-alias-decision
project: SimonK-stack
priority: high
status: done
created: 2026-09-28 14:25:09 KST
---

## Context

Simon 직접지시의 추가 과금 $0·구독 사용 조건 아래, 고정 Gstack 원본 `01593aa67c94780528e8f5121e47362502410ced`의 단독 로컬 설치 경로를 무인증 Windows Sandbox에서 시험했습니다. 공개 Bun 패키지 다운로드만 허용했고 Playwright bootstrap은 생략했습니다.

## Deliverable

- 최종 세 번째 새 게스트에서 프로젝트 루트로 작업 디렉터리를 설정한 `setup --local --host claude --no-team --prefix` 종료 0. 프로젝트 `.claude/skills`의 엔트리 57/57에 SKILL.md가 있고, 이 중 54개는 linked skills, 나머지는 `gstack`, `_gstack-command`, 재작성 별칭 `gstack-connect-chrome`입니다. browse/design/pdf/global-discover Windows 실행 파일과 완료 스탬프도 존재합니다.
- 첫 두 게스트의 setup 종료 0은 하네스의 CWD 오류로 소스 내부 중첩 `.claude/skills`에 설치됐으므로 성공 근거에서 제외하고 출력은 보존했습니다. 최종 `output3/`만 판정 근거입니다.
- Gstack source clone의 추적 파일 53개가 이름/생성 패치로 바뀌므로 immutable candidate 안에서 `setup`을 직접 실행할 수 없습니다. Codex-format 문서 두 개에 생성기의 160,000-byte ceiling 경고가 있으나 실제 호스트 로딩 실패 증거는 아닙니다.
- SimonK-stack 기능 브랜치 문서·README `f2adf59` origin push/clean, 관련 4개 단위 테스트 및 diff check 통과. HTML 보고서 `E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-setup-sandbox/report.html`; 최종 `output3/result.json`, `output3/postcheck.json`.

## Decision dependency

이는 Gstack 단독 Claude 프로젝트 로컬 설치 증거입니다. 5플러그인 공존, 기존 사용자 프로필 롤백, 31개 스킬의 전이 런타임, Playwright/CSO, 모델·Bot·Orca와 구독 청구는 미검증입니다. 별칭/런타임 소유권 §35 결정 및 D-30 게이트를 유지해 주세요. 세 readiness 플래그는 false이며 사용자 설치본·main·결제 설정·모델/API/Bot/Orca 실호출은 건드리지 않았습니다.
