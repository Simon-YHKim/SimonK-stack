---
id: 20260929-130352-codex-to-claude-core-obsidian-bases
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 13:03:52 KST
---

SimonKCore 원본 플러그인의 승인된 기능 브랜치 `fix/core-helper-closure-260927`에 `obsidian-bases` 스킬 문맥 경량화 커밋 `6eca5c214599431f38ca4432bf4e1c3d51efcde9`를 push했다. 세 완성 예제를 내용 변경 없이 `references/EXAMPLES.md`로 옮기고 필요할 때만 읽는 링크를 본문에 남겼다. `FUNCTIONS_REFERENCE.md`와 새 예제 참조에는 목차를 넣었다. 본문 500→388줄, 대상 스킬 W007/W013 경고 2개 해소.

검증: 이동 전후 예제 블록 문자 동일, 대상 validator 0오류·0경고, 링크 2개 실제 파일 확인, 저장소 전체 `run_ci.py` 57/57 PASS, 인코딩 테스트 4/4 PASS, Claude strict manifest 오류·경고 0, 커밋 diff 시크릿 패턴 0. 시스템 범용 `quick_validate`는 이 플러그인의 필수 `version` frontmatter를 거부하므로 저장소 전용 품질 게이트를 정본으로 사용했다. 모델·API·Bot 호출이나 설치·결제 설정 변경은 없다.

중요: SimonK-stack `distribution/plugin-inputs.v1.json`은 아직 Core 이전 커밋 `bdd047c8…`을 고정한다. v28 후보의 34개 비차단 경고와 영수증은 **변하지 않았다**. 버전 충돌 D-code 이전에 새 후보 설치·기존 프로필 갱신은 하지 않는다.

[HTML 미리보기](preview/20260929-130352-core-obsidian-bases.html)
