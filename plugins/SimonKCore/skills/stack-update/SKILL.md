---
name: stack-update
description: >
  Use when asked "SimonK stack 최신화", "update the stack", or
  /stack-update (not gstack alone). Produces a per-repository fast-forward
  update report and separate installation gate; never force-installs or
  changes credentials.
version: 2.0.0
allowed-tools:
  - Bash
  - Read
---

# stack-update

Refresh the SimonK-stack ecosystem without hiding unrelated writes behind one command. This skill works from the repositories actually present in the user's workspace; it does not require a monorepo helper or a fixed home layout.

## 1. Inventory and plan

For SimonK-stack, SimonKWiki and each requested vendored stack, record: resolved repository root, remote/upstream, current branch and commit, dirty files, ahead/behind counts, and whether a fast-forward is possible. Include only repositories the user placed in scope and whose origin is verified. Never infer a missing repository from its folder name or clone a new one automatically.

A request for status stops after the plan. A request to update authorizes safe repository refresh, but not profile installation, forced checkout, credential access, production deployment, or an unrelated vendor upgrade.

## 2. Safe apply

For each selected repository independently:

- Fetch its configured upstream only after verifying the target and remote.
- Pull with fast-forward-only only if the branch is known, the worktree is clean, and the upstream is a descendant of HEAD.
- If dirty, detached, diverged, protected, or missing an upstream, skip it and report the exact reason. Do not stash, reset, force, switch branches, remove files, or overwrite another agent's work.
- Check the resulting commit and status. A zero exit code without the expected commit is not a verified update.

External upgrade scripts are not bundled here. Do not search the user's home for a same-named script or execute a guessed copy. If a vendor needs its own updater, use that vendor's reviewed skill and authorization separately.

## 3. Installation is a distinct gate

Repository refresh does not install or activate skills. Do not run a force or no-backup installer against a user profile. A plugin candidate can be installed only after its receipt, dependencies, host behavior, conflicts and rollback path are checked. Preserve the prior installation and switch only exact validated targets under the user's installation approval.

## Final report

For each component give before/after commit, branch, operation, verification and any skipped reason. Summarize profile changes separately; normally there are none. State whether main merge, remote push or installed-skill activation was outside the update.

## Compatibility note

The former v1 procedure auto-chained wiki/vendor updates and a force/no-backup global reinstall. That procedure is retired because it could overwrite user profiles and hid several external dependencies. Existing projects can still request each update explicitly under the safe per-repository contract above.
