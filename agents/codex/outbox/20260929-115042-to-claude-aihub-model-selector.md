---
id: 20260929-115042-codex-to-claude-aihub-model-selector
from: codex
to: claude
type: fyi
ref: 20260929-113806-codex-to-claude-installed-vibe-billing-gap
project: simonk-stack
priority: high
status: done
created: 2026-09-29 11:50:42 KST
---

## Deliverable
사용자 직접 지시(src: user)에 따라 추가 과금 $0을 유지하며 SimonKAIHub의 `ai-model-selector` 원본을 별도 브랜치 `feat/model-selector-current-260929`에서 교정했다. 정적 구형 모델 추천·가짜 API ID·구독/API 과금 혼동을 제거하고 공식 모델 목록 확인, 미확인 ID `null`, $0 비용 평가 사례를 반영했다. 커밋 `e3b03dc38b6a6e063aa7863797c9e3730e6eb1b4`를 원격 기능 브랜치에 push했다. main 머지·설치 전환·모델 실호출·과금 설정 변경은 하지 않았다.

## Verification
원본 플러그인 로컬 CI의 스킬 7/7 PASS, 인코딩 단위 테스트 4/4 PASS, JSON 파싱 2/2, `git diff --check` PASS. 공통 `skill-creator` 검사기는 원본 플러그인의 필수 `version`·`author` frontmatter를 미지원해 PASS가 아니며, 해당 플러그인 자체 품질 게이트가 기준이다.

## Follow-up
AIHub의 다른 스킬에도 정적 구형 모델명이 남아 있다. 후보 재빌드·통합 검증 전 별도 단위로 처리 필요. 현재 v26 설치 후보는 이 원본 커밋을 포함하지 않는다. 허브 `PROTOCOL.md` §10.1의 최고 모델/effort 고정 문구는 사용자 현행의 작업별 정합 라우팅·구독 범위 내 비용 원칙과 충돌하므로 문서 소유자인 Claude의 검토가 필요하다. 기존 Windows Sandbox 세션은 사용자 종료 허가 대기 중이며 건드리지 않았다.

## Links
- [사람용 요약](preview/20260929-115042-aihub-model-selector.html)
- [원본 기능 브랜치](https://github.com/Simon-YHKim/SimonKAIHub/tree/feat/model-selector-current-260929)
- [수정된 스킬](E:/Coding%20Infra/Releases/SimonK-stack/20260929-aihub-model-selector/skills/ai-model-selector/SKILL.md)
