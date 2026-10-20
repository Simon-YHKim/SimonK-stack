# Vendored Skills

Skills derived from an upstream project. SimonK-stack owns these copies and the
runtime they call; nothing here depends on the upstream install any more.
Validation: relaxed for body length (E007) and TODO markers (E008) only — the
bodies are long procedural documents by design. Every other check, the
description quality gate and `evals/cases.json` still apply
(`.github/skill-ci/run_ci.py`).

## Source: [garrytan/gstack](https://github.com/garrytan/gstack) v1.91.9.0 (MIT)

Integrated in full on 2026-10-21 (hub D-117):

- Bodies follow upstream 1.91.9.0. Descriptions and versions are SimonK's.
- The runtime they call (bin scripts, browse/design/pdf tools, Chrome
  extension) lives in `~/.simonk/runtime`, installed by
  `scripts/windows/install-runtime.ps1` from the pin in `runtime/RUNTIME.json`.
  State lives in `~/.simonk/state`.
- Install and state paths are rewritten from the upstream home install to
  those folders. Update checks and auto-upgrade are off; SimonK-stack manages
  updates. The upstream upgrade skill is retired.
- Safety skills (`careful`, `freeze`, `guard`, `unfreeze`, `investigate`) keep
  their reviewed bytes for now: the five-plugin safety projection pins their
  hook text and the freeze state default (`$HOME/.gstack`). Moving them to
  `~/.simonk/state` is a separate safety change with its own review.
- Renamed: upstream `review` is `pr-review` (the repository already has a
  development-only `review`); upstream `open-gstack-browser` is `open-browser`.
- File-level provenance and the upstream copyright notice: repository LICENSE.

- `autoplan`
- `benchmark`
- `browse`
- `canary`
- `careful` — adapted: v1.91.9.0 + SimonK fail-closed deltas (HIGH deny,
  MEDIUM ask, internal hook failure deny; D-56). Its bin/ also vendors
  `gstack-slug` as `gstack-slug.sh`.
- `checkpoint` — earlier upstream name of `context-save`; kept for existing users.
- `codex`
- `context-restore`
- `context-save`
- `cso`
- `design-consultation`
- `design-html`
- `design-review`
- `design-shotgun`
- `deslop-shared-libs`
- `devex-review`
- `diagram`
- `document-generate`
- `document-release`
- `freeze` — adapted: v1.91.9 + SimonK Windows-path and fail-closed deltas
  ($HOME-anchored hooks, C:\ / C:/ / /c/ normalization, relative and
  unjudgeable paths deny; D-62). Its bin/ also vendors `freeze-state.sh`.
- `guard` — adapted: wiring to the SimonK `careful` and `freeze` hook scripts
  through $HOME-anchored commands (D-62).
- `health`
- `investigate` — unchanged here: still not installed from this folder (D-68).
  See the safety note below.
- `land-and-deploy`
- `learn`
- `make-pdf`
- `office-hours`
- `open-browser`
- `pair-agent`
- `plan-ceo-review`
- `plan-design-review`
- `plan-devex-review`
- `plan-eng-review`
- `pr-review`
- `qa` — adapted: SimonK QA 2.1 acceptance contract used by `/vibe`.
- `qa-only`
- `retro`
- `scrape`
- `setup-browser-cookies`
- `setup-deploy`
- `ship`
- `test-audit`
- `unfreeze` — adapted: clears the boundary through the vendored
  `freeze/bin/freeze-state.sh` (D-62).

Not carried over from upstream: `ios-*` (5, SwiftUI devices), `setup-gbrain`,
`sync-gbrain`, `plan-tune`, `skillify`, `benchmark-models`, `landing-report`,
the upstream router skill and its upgrade skill, and `spec` (the SimonK plugins
already ship their own `spec`).

**Total**: 43 vendored
