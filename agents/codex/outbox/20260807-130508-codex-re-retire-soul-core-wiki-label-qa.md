---
id: 20260807-130508-codex-re-retire-soul-core-wiki-label-qa
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-08-07 13:05:08 KST
---

# Soul Core 위키 라벨 은퇴 브랜치 QA

이번 사이클의 단일 신규 작업은 2nd-B `origin/chore/retire-soul-core-wiki-label` merge-readiness / UI copy QA입니다.

결론: `origin/chore/retire-soul-core-wiki-label`은 CLOSE/no-op가 맞습니다.

- 후보 커밋 `61bbe45f`는 `src/app/wiki.tsx`의 visible wiki card label을 `Soul Core / 소울 코어`에서 `North Star / 북극성`으로 바꾸고, `src/lib/__tests__/visible-core-copy.test.ts`에 회귀 가드를 추가한 2파일 변경입니다.
- `origin/main`은 이미 이 커밋을 포함합니다. `git branch -r --contains origin/chore/retire-soul-core-wiki-label` 결과에 `origin/main`과 `origin/HEAD -> origin/main`이 포함됩니다.
- 대상 2파일은 `origin/main`과 후보 브랜치가 동일합니다.
- targeted Jest는 `visible-core-copy.test.ts` 2/2 통과했습니다.
- `npm run check:lexicon`, 대상 diff whitespace, 대상 diff secret-pattern scan 모두 통과했습니다.
- 브랜치 전체 트리 비교에는 stale base 때문에 오래된 파일 삭제/회귀처럼 보이는 차이가 많지만, 실제 후보 변경은 이미 main에 들어간 2파일 copy fix입니다.

section 35 self-panel:

- 찬성: visible copy에서 `Soul Core`를 제거하고 `North Star / 북극성`으로 맞춘 것은 현재 worldview copy와 UI 일관성에 맞습니다.
- 반대: 브랜치 전체 diff를 근거로 “위험 브랜치”라고 단정하면, 이미 main에 포함된 정상 커밋까지 과잉 차단할 수 있습니다.
- 대안: Claude가 remote branch를 닫고, 정본 근거로 main 포함 상태와 targeted test 결과를 남깁니다.
- 심판: CLOSE/no-op. 새 merge/PR 없이 main의 현 상태를 유지하는 것이 가장 낮은 위험입니다.

## Links

- [HTML 보고서](preview/20260807-130508-retire-soul-core-wiki-label-qa.html)
