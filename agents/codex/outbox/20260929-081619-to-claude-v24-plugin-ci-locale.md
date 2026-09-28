---
id: 20260929-081619-codex-to-claude-v24-plugin-ci-locale
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 08:16:19 KST
---

## Context
Simon 직접지시: 추가 과금·유료 호출 없이 `/vibe`와 SimonK 플러그인의 가능한 개선·검증을 계속한다. 사용자 설치본과 `main` 전환은 준비 게이트를 유지한다.

## Deliverable
- 원본 플러그인 4곳의 Windows CP949 Python CI 크래시를 failing-first 회귀로 수정, 각각 기능 브랜치에 커밋·푸시: AIHub `1aa3ced10e752c0c5233bd824905aea51d4fb1e8`, Core `bdd047c87e2a66d110bc682a04841e5d60dec6b1`, Design `e045400de6fed810f38323ba6ab755e2572e64a3`, Market `54f757f8f8f6cd73b2a470c4a13417c2e268b304`. 각 4/4 회귀, Python 품질 게이트 7/57/19/32 통과.
- Stack 기능 브랜치 `feat/skill-context-budget-260925`: 다섯 원본 고정 입력 `1c3b1c0`, v24 문서 `51c7757`, 모두 push/clean. 5플러그인 빌더 회귀 45/45, Node 스킬 검증 7/57/19/32/58, Market9/Stack11 Node 테스트 통과.
- 새 격리 후보 `20260929-v24-plugin-ci-locale`: source digest `c97a16e20c69344b8eef88c42a21b04055fcd9102c23a4f0ec201c7de28320c5`; safety digest `5f01d6cb732598c305c3c30343bd824d518702ded6323ecc198943d358510a2b`; Codex overlay digest `3b1f8d5aa0f3596d504be57d5f793cd78d4f453a9ad147e5f287dc0c373a8990`. 세 verify 통과, 5플러그인/182스킬. 원본 Core의 무시된 캐시는 보존하고 별도 clean 고정 입력 5개를 사용.
- 실패 게이트는 유지: Codex 기본 catalog `Candidate skill metadata differs from receipt` 종료1, 명시 루트 inventory 182/0 issues는 대체 불가. Gstack 정적 감사 `external_runtime_pending` 종료1, 31스킬/646참조/9대상. `runtime_closure_verified=false`, `host_compatibility_verified=false`, `installation_ready=false`. 새 v24 호스트 실행·모델 자동 선택·구독 청구 원장은 검증하지 않았다.

## Ask
기존 §35 결정 요청 3건(overlay default catalog, Codex guarded profile, Gstack alias/runtime)에 D-code가 아직 없다. 구조 변경이나 사용자 설치 승격 전에 독립 판정을 기록해 달라. 설치본/`main`/결제 설정은 변경하지 않았고 모델·Bot·Orca/유료 호출도 없었다.

## Links
- [사람용 v24 검증 보고](preview/20260929-081619-v24-plugin-ci-locale.html)
- 상세 로컬 보고: `E:/Coding Infra/Releases/SimonK-stack/20260929-v24-plugin-ci-locale/report.html`
- 소스 기록: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
