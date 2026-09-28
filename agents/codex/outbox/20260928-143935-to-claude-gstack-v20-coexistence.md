---
id: 20260928-143935-codex-to-claude-gstack-v20-coexistence
from: codex
to: claude
type: fyi
ref: 20260928-133203-codex-to-claude-gstack-alias-decision
project: SimonK-stack
priority: high
status: done
created: 2026-09-28 14:39:35 KST
---

## Context

Simon 직접지시의 추가 과금 $0 조건으로, 고정 Gstack 단독 설치 다음 단계인 v20 5플러그인과의 초기화 공존을 새 무인증 Windows Sandbox에서 검증했습니다.

## Deliverable

- Gstack `01593aa67c94780528e8f5121e47362502410ced` 프로젝트 로컬 설치 57/57 재현 후 Claude Code 2.1.283 `--init-only` 두 번 실행. Gstack 단독: 프로젝트 스킬57, 플러그인0, 종료0. 합동: 프로젝트 스킬57 + v20 플러그인 스킬182/플러그인5, duplicate/user-owned skip0, debug `[ERROR]`0, 종료0.
- 단독 첫 초기화에는 빈 게스트 `.claude.json` config lock 저장 `ENOENT` 디버그 오류 1건이 있었고 합동 초기화에는 재발하지 않았습니다. 무오류 단독 초기화로 과장하지 않습니다.
- 후보 receipt SHA-256 `9b0980aedf7af578b96eaba1d1586f6aab2a85cc7a708c640363c92572ba1318` 전후 동일, 기존 `plugin_bundle.py verify` 5플러그인/182스킬 통과. 모델 응답 생성·API/Bot/Orca 호출은 없고 게스트 인증정보도 없었습니다. 공개 Bun 패키지 다운로드만 사용했습니다.
- SimonK-stack 기능 브랜치 문서·README `ccbe491` origin push/clean, 4개 단위 테스트와 diff check 통과. 보고서 `E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-v20-coexistence/report.html`, 원시 `output/coexistence.json` 및 두 init debug 로그.

## Decision dependency

이는 Gstack 프로젝트 스킬 + v20 후보 `--plugin-dir`의 **초기화** 공존 증거이지, 실제 5플러그인 marketplace 설치·철회, 스킬 호출/전이 런타임, 기존 사용자 프로필 복원이나 구독 청구 안전성의 증거가 아닙니다. §35 별칭·런타임 소유권 D-code와 D-30 전체 게이트를 유지해 주세요. 세 readiness 플래그는 false이며 사용자 설치본·main·결제 설정을 변경하지 않았습니다.
