# Changelog

All notable changes to this plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Align `semantic-recall` 0.2.0 instructions with the existing FastEmbed-first
  backend and explicit `--roots`, `--out` and `--index` arguments. Explain that
  query also executes a model, cache presence is not offline proof, and scope,
  fresh output and partial-coverage checks are coordinator requirements. Expand
  bounded evaluation coverage to six cases; no embedding runtime guards or
  native-host execution are added by this documentation/evaluation change.
- Encode `semantic-recall`'s description as a YAML folded scalar so its embedded
  colon and quoted phrases parse without changing the description's text. Add
  the missing skill version and two bounded, no-model evaluation cases. This is
  a metadata/coverage repair, not a native-host or embedding-runtime validation;
  that earlier repair left the backend instructions, paths and script unchanged.

## [0.3.0] - 2026-06-16

### Changed
- **`completion-report` skill upgraded to 0.3.0** — HTML completion reports now have button toggles for **language (Korean / English)** and **explanation depth (Simple / Expert)**, where both depths always state purpose and reason. The "Simple" explanation is understandable without any coding knowledge. Stays self-contained: `<body>` class toggles + ~10 lines of inline vanilla JS (no external libraries); each item's detail is authored in 4 variants (easy/expert × ko/en). Inherited automatically by every skill that emits the HTML completion-report standard.

## [0.2.0] - 2026-06-16

### Added
- **CI quality gate** (`.github/workflows/skills-ci.yml` + vendored stdlib `skill-ci/`): per-skill lint (0 errors) + required `evals/cases.json` + cases dry-run + description score ≥ 0.6; fails the build on regression.
- **Eval coverage**: `evals/cases.json` for every skill (test coverage 0 → 100%) — 23 eval sets added across the 56 skills.
- **Runtime entry commands** under `commands/`: `/find-skill` and `/simonk` (the documented slash entry points, previously an empty dir).
- **CONTRIBUTING.md** tying skill authoring to the quality gate.
- **HTML completion-report standard**: every skill now emits a self-contained HTML report on completion — simple at-a-glance summary + intuitive inline-SVG charts/images, each item behind a `[자세히]` progressive-disclosure button.

### Changed
- Rewrote skill descriptions to lead with "Use when …" and state output (routing quality) — 9 descriptions rewritten.
- **`completion-report` skill upgraded to 0.2.0** — the HTML report engine + `[자세히]` progressive-disclosure template that powers the HTML completion-report standard across all SimonK plugins.

### Fixed
- Migrated stale-schema `evals/cases.json` to the canonical object schema — 20 migrated.

[0.3.0]: https://github.com/Simon-YHKim/SimonKCore/releases/tag/v0.3.0
[0.2.0]: https://github.com/Simon-YHKim/SimonKCore/releases/tag/v0.2.0
