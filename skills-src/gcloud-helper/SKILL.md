---
name: gcloud-helper
description: >
  Use when asked "gcloud auth", "ADC status", "BigQuery 인증" or
  "Vertex AI 인증". Produces a redacted local gcloud status and action plan;
  never auto-logs in, switches projects, or injects credentials.
allowed-tools: Read, Bash
version: 2.0.0
author: simon-stack
---

# gcloud-helper

Diagnose Google Cloud CLI setup without silently changing the user's account, project, or environment. This is an independently usable plugin skill; it does not depend on a SimonK-stack monorepo script.

## Default: local diagnosis only

1. Check whether the gcloud executable is present. If absent, report that state; do not install it automatically.
2. If present, inspect the selected local configuration/project and active-account **metadata** using gcloud's read-only status commands. Mask the account in any report. Do not print tokens, credential file contents, or full environment values.
3. Check only whether an ADC file exists at the path reported by the configured environment or by the user's gcloud installation. Never open or copy the file. An absent path is unknown until confirmed, not proof that the user has no credentials.
4. Report separate states for CLI, active account, project and ADC: present, missing or unknown. Give the exact reason for unknown.
5. A project name in local config is not proof of remote access. Do not run remote project listing, OAuth or billable Google APIs as part of the default diagnosis.

The simonK harness does **not** auto-run this skill or a cloud bootstrap. Older instructions claiming automatic project repair and session credential injection were inaccurate and are retired.

## Explicit apply boundary

If the user wants an account login, project switch, or session environment change, first show the target and exact effects. The user completes browser OAuth themselves. This skill does not execute config-changing commands, create credentials, or set GOOGLE_APPLICATION_CREDENTIALS in this release, even after approval; provide a user-run plan or hand off to a separately verified adapter. Never guess a fallback project from the first listed project.

No plugin-local apply adapter is shipped in this version. A missing external helper must be reported as unavailable, not silently substituted with a monorepo path. An approved future adapter needs a reviewed effect manifest, no secret fragments in output, and tests with fake gcloud plus an isolated profile before activation.

## Result contract

Return: CLI path/version (or unavailable), masked active-account status, configured project (or unknown), ADC path-presence only, proposed next command for the user, and whether a write/auth action is still waiting for approval. Keep credential contents out of logs, task handoffs and reports.

## Validation

- Missing gcloud, missing config, malformed output and unknown ADC paths must produce unknown/unavailable states rather than a fabricated repair.
- Default diagnosis must not run OAuth, remote project listing, config set, package installation or credential injection.
- When a user requests a mutation, identify the exact target and pause before applying it.
