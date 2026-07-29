---
id: 20260722-001002-codex-re-rc2-emu-dispatch-review
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-07-22 00:10:02 KST
verify: requested
---

# 안드로이드 에뮬레이터 빌드 분기 검토

이번 사이클의 단일 작업으로 `origin/release/v0.1.0-rc2-emu` 커밋 `105fad8a`를 `origin/main` `c87bff24` 기준으로 검토했습니다.

판정: 차단 이슈 없음. 변경은 `.github/workflows/eas-preview-build.yml`에서 수동 dispatch 프로필 선택지와 shell allowlist에 `preview-emulator`를 추가하는 범위입니다. `eas.json` 기준 `preview-emulator`는 `preview`와 ABI 필터만 다르고 둘 다 APK 빌드입니다.

검증:
- `git diff --check origin/main..origin/release/v0.1.0-rc2-emu` 통과.
- `origin/main`은 대상 브랜치의 조상이며 merge-tree 충돌 출력 없음.
- Node 기반 `eas.json` 비교: `sameExceptAbi=true`, `preview=arm64-v8a`, `preview-emulator=arm64-v8a,x86_64`.
- 워크플로우 정적 확인: 수동 실행 전용, `contents: read`, production만 AAB로 표기, 나머지는 APK.
- `actionlint`는 로컬에 없어 실행하지 못했습니다.

제약 준수:
- 실제 EAS 빌드, GitHub dispatch, push, PR, merge, 배포, 브라우저 오픈, 파괴적 작업, 비용 작업, secrets 작업 없음.
- 허브에서는 `agents/codex/` 아래에만 작성.
- 네이티브 빌드 dispatch 설정 변경이므로 Antigravity에 MoA 교차 검증 요청을 별도 outbox로 남겼습니다.

## Links

- HTML 보고서: `agents/codex/outbox/preview/20260722-001002-rc2-emu-dispatch-review.html`

