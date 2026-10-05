# workingstyle.md — {{PROJECT_NAME}}

> 이 프로젝트에서의 작업 패턴. 글로벌 `~/.claude/instincts/` 와 보완 관계.

## Branch & commit

- 브랜치 전략: {{BRANCH_STRATEGY}}
- 머지 방식: {{MERGE_METHOD}}
- 커밋 메시지: {{COMMIT_STYLE}}

## Test strategy

- TDD 강도: {{TDD_LEVEL}}
- 전체 테스트 명령: `{{TEST_COMMAND}}`
- 빠른 smoke 명령: `{{SMOKE_COMMAND}}`
- 수동 QA URL / 경로: {{MANUAL_QA}}

## Dev loop

- 개발 서버 시작: `{{DEV_SERVER}}`
- 헬스 체크 / 로그: `{{HEALTH_CHECK}}`
- 빌드 명령: `{{BUILD_COMMAND}}`

## Anti-patterns (이 프로젝트 한정)

Claude 가 이 프로젝트에서 자주 저지르는 실수 — 다음 세션부터 명시적으로 금지:

1. ❌ {{ANTI_1}}
2. ❌ {{ANTI_2}}
3. ❌ {{ANTI_3}}

> 다른 프로젝트에도 통용되는 cross-project 실수는 `~/.claude/instincts/mistakes-learned.md` 에 `simon-instincts` skill 로 append.

## Verified workflows (이미 검증된 것)

- ✅ {{WORKING_1}}
- ✅ {{WORKING_2}}

다음 세션에서 이 워크플로는 재발견 시간 낭비 없이 바로 사용.

---

> Imported from: {{IMPORT_SOURCE}} ({{IMPORT_DATE}})
