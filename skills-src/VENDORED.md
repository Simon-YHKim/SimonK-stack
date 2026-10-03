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
- `investigate`
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
