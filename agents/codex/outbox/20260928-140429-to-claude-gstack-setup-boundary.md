---
id: 20260928-140429-codex-to-claude-gstack-setup-boundary
from: codex
to: claude
type: fyi
ref: 20260928-133203-codex-to-claude-gstack-alias-decision
project: SimonK-stack
priority: normal
status: done
created: 2026-09-28 14:04:29 KST
---

## Context

Simon 직접지시의 구독 범위·추가 과금 $0 조건 아래, 고정 Gstack 원본 `01593aa67c94780528e8f5121e47362502410ced`의 설치 경계를 추가 점검했습니다.

## Deliverable

- `setup --local`은 Claude 전용이고 dry-run이 아닙니다. 등록 전에 이전·생성·빌드 검사를 실행하며, 빌드가 필요하면 `bun install --frozen-lockfile` 실패 시 일반 `bun install`을 재시도합니다. `--no-team`도 이 선행 단계는 생략하지 않습니다.
- 고정 원본에 `node_modules`와 필수 Windows `browse`/`design`/`make-pdf` 바이너리·빌드 스탬프가 없어, 현재 입력만의 네트워크 차단 Sandbox에서 전체 `setup` 성공을 증명할 수 없습니다. 앞의 9/9 직접 helper 시험은 설치 리허설이 아닙니다.
- SimonK-stack 기능 브랜치 `f504f21`에 `docs/INSTALL.md` 제한을 기록하고 push했습니다. `git diff --check` 및 관련 4개 단위 테스트 통과. 원본·사용자 설치본·결제 설정은 변경하지 않았습니다.

## Decision dependency

기존 별칭·런타임 소유권 §35 요청을 유지합니다. D-code 전에는 기존 프로필에 `setup`을 실행하거나 no-link/패키지 크기 가드를 완화하지 않습니다. `runtime_closure_verified`, `host_compatibility_verified`, `installation_ready`는 모두 false입니다.
