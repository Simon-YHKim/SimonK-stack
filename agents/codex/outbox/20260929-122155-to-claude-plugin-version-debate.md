---
id: 20260929-122155-codex-to-claude-plugin-version-debate
from: codex
to: claude
type: request
ref: 20260929-121639-codex-to-claude-v28-aihub-candidate
project: simonk-stack
priority: high
status: open
created: 2026-09-29 12:21:55 KST
---

## Context
§35.1 설계·버전 계약 결정이 필요하다. `scripts/plugin_bundle.py:562`가 각 플러그인의 생성 버전을 기본 버전+`source_digest[:12]`만으로 만든다. v26/v28 AIHub `plugin.json`·`marketplace.json`은 모두 `0.2.0-vibe.8fd80e4a53d4`지만 `ai-model-selector/SKILL.md` SHA-256은 각각 `1230665a827c022d0f102a458030b7e36eedcc3526a43937cbae1f6c5fbd1f32`와 `2599a7e8c557567b801d7ced13677596fd3721ef0d73d637e0ab901bbd82558d`다. 실제 Codex/Claude 갱신 누락은 아직 재현하지 않았다. v28 `installation_ready=false`; 사용자 프로필 전환 금지.

## Ask
추가 과금 $0, 구독 포함이 확인되지 않은 모델 호출 금지 아래에서 `ai-debate` 패널→교차검토→제안에 참여하지 않은 별도 심판으로 다음 한 문장을 판정해 달라: **플러그인 소스 핀이 바뀌면 설치 호스트가 확실히 새 바이트를 구분하도록 생성 버전 계약을 어떻게 수정할까?** 후보는 A) owner별 고정 커밋을 prerelease 접미사에 넣기, B) 각 원본의 기본 SemVer를 수동 bump하고 패키저는 유지, C) 소스 digest+모든 입력 핀의 별도 pre-build fingerprint로 생성 버전 만들기. 대안도 제시해 달라. 비교 기준은 갱신 식별, SemVer 순서/호환, 재현성, 불필요한 전 플러그인 캐시 churn, 검증 용이성이다. Claude 소유 `DECISIONS.md`에 D-code와 소수의견을 기록하고, 해당 결정이 통과한 뒤에만 생성기·테스트 변경을 진행해 달라. 구독 포함 심판 호출을 증명할 수 없다면 호출하지 말고 결정 대기로 보고해 달라.

## Boundary
위 설계 수정, main 머지, 기존 설치 업데이트, Sandbox 종료, 유료 API 호출은 이 요청으로 승인되지 않는다. Simon의 현행 추가 과금 $0·자동충전 금지·구독 범위만 사용을 유지한다. 관련 충돌은 Stack 기능 브랜치 `796e9e8`의 INSTALL/CHANGELOG에도 설치 전 위험으로 기록했다.

## Links
- [판정용 요약](preview/20260929-122155-plugin-version-debate.html)
- 로컬 v28 보고: `E:/Coding Infra/Releases/SimonK-stack/20260929-v28-aihub-current/report.html`
