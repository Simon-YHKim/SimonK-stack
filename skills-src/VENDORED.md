# Vendored Skills

Upstream skills included as-is. Original format preserved.
Validation: relaxed (line count, description format exempt).

## Source: [garrytan/gstack](https://github.com/garrytan/gstack)

- `autoplan`
- `benchmark`
- `browse`
- `canary`
- `careful` — adapted, not as-is: gstack v1.91.9.0 + SimonK fail-closed deltas
  (HIGH deny, MEDIUM ask, internal hook failure deny; D-56, 2026-10-03). Its
  bin/ also vendors gstack `bin/gstack-slug` as `gstack-slug.sh`. File-level
  provenance and SHA-256: repository LICENSE.
- `checkpoint`
- `codex`
- `connect-chrome`
- `cso`
- `design-consultation`
- `design-html`
- `design-review`
- `design-shotgun`
- `devex-review`
- `document-release`
- `freeze` — adapted, not as-is: gstack v1.91.9 + SimonK Windows-path and
  fail-closed deltas ($HOME-anchored hooks, C:\ / C:/ / /c/ normalization,
  relative and unjudgeable paths deny; D-62, 2026-10-03). Its bin/ also vendors
  gstack `freeze/bin/freeze-state.sh` unchanged. Provenance and SHA-256:
  repository LICENSE.
- `gstack-upgrade`
- `guard` — adapted, not as-is: gstack v1.91.9 wiring to the SimonK `careful`
  and `freeze` hook scripts through $HOME-anchored commands (D-62).
- `health`
- `investigate` — 설치 대상 아님(D-68, 2026-10-04). 단일 원본은 gstack 1.91.9
  설치본 `~/.claude/skills/investigate`이며 손으로 고치지 않는다. 이 폴더는 gstack
  구판 본문(생성 배너 있음, 훅 `${CLAUDE_SKILL_DIR}`, 잠금이 상대경로 기록)이라
  설치되어 실행되면 모든 편집을 막는다. 폴더의 `.simonk-no-install` 표식 때문에
  `scripts/install.sh`, `scripts/setup-repo.sh`, `.claude/hooks/session-start.sh`는
  이 이름을 복사하지 않는다. 5플러그인 후보는 별도 릴리스 결정 전까지 안전 투영
  입력으로 그대로 포장한다. Windows 경고는 `freeze`·`guard` 본문에 있다.
  재개 조건 — 하나라도 충족되면 "E: 경로 4곳 변경 + 배너 제거만 한 고정본"으로 옮긴다.
  (1) 이 PC에서 30일 안에 실제 호출 3회. (2) investigate와 freeze·guard가 겹쳐
  모든 편집 deny 또는 경계 밖 편집 허용이 1건. (3) 설치만으로, 또는 한 번 로드된
  뒤 훅이 Edit/Write에 상주한다는 실측. 그 전에는 경로 패치, 버전 고정, 본문
  재베이스를 하지 않는다.
- `land-and-deploy`
- `learn`
- `office-hours`
- `open-gstack-browser`
- `pair-agent`
- `plan-ceo-review`
- `plan-design-review`
- `plan-devex-review`
- `plan-eng-review`
- `qa`
- `qa-only`
- `retro`
- `setup-browser-cookies`
- `setup-deploy`
- `ship`
- `unfreeze` — adapted, not as-is: gstack v1.91.9, clears the boundary through
  the vendored `freeze/bin/freeze-state.sh` (D-62).

**Total**: 36 vendored / 49 native / 85 total
