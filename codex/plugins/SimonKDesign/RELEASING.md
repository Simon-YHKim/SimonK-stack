# Releasing

This plugin is consumed via the Claude Code marketplace, which pulls directly from
this repository. A "release" is therefore a versioned, merged commit on `main` plus a
matching git tag.

## Steps

1. **Bump the version** in both manifests (keep them in sync):
   - `.claude-plugin/plugin.json` → `"version"`
   - `.claude-plugin/marketplace.json` → top-level `"version"` **and** the per-plugin entry `"version"`
2. **Update `CHANGELOG.md`** following [Keep a Changelog](https://keepachangelog.com):
   add a new `## [<version>] - <YYYY-MM-DD>` section grouped under Added / Changed / Fixed.
3. **Open a PR** against `main` with the version bump + changelog. Ensure the
   **CI quality gate** (`.github/workflows/skills-ci.yml`) is green.
4. **Merge the PR to `main`.** Release artifacts are prepared on the feature branch,
   but the release is only real once it lands on `main`.
5. **Tag `v<version>` on `main`** (e.g. `v0.2.0`) — tags are cut on `main` *after* merge,
   **never** on the feature branch.
6. **(Optional) Publish a GitHub Release** from that tag with the changelog section as notes.

Marketplace consumers pull from the repo, so no separate publish step is required.
