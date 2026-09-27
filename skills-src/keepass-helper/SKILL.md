---
name: keepass-helper
description: >
  Use when asked "KeePassXC 상태", "vault 키" or "keepass-inject".
  Produces vault/CLI presence status and a safe next step; never unlocks
  a vault, reveals keys, or injects secrets automatically.
allowed-tools: Read, Bash
version: 2.0.0
author: simon-stack
---

# keepass-helper

This skill checks whether a KeePassXC workflow is available. It does not read the vault or move credentials into an agent, model prompt, log, or child process.

## Default: metadata-only check

1. Check whether keepassxc-cli is installed. Do not install it automatically.
2. Use only a vault path supplied by the user or the SIMONK_KEEPASS_VAULT environment setting. If neither exists, report vault location as unknown. Never assume a fixed drive or filename.
3. Test path existence and file type without opening the vault. Report only present/missing/unknown and a masked path if needed.
4. For an environment variable needed by the current task, report set/missing by name only. Never print a value, length, prefix, suffix, checksum or token shape.

Do not ask the user to paste a master password or API key into chat. Do not run keepassxc-cli against a vault by default. Do not auto-inject any key when simonK or vibe starts.

## Credential-use boundary

The previous monorepo helper is **not** bundled with this plugin. Its output exposed key fragments, and its fixed vault path was machine-specific. Do not dot-source it from a guessed external location. Vault unlock, key retrieval and process environment injection are unsupported in this version until a separate reviewed adapter exists.

If the user asks for credential use, identify the target service, required variable name, recipient process, lifetime and whether an existing authenticated integration can avoid exposing the value. Pause for an exact, security-sensitive authorization before any vault read or injection. Keep the master password inside the user's trusted KeePassXC interface or an audited, non-logging local adapter; never pass it through an agent prompt, command argument or persistent environment.

## Result contract

Return CLI availability, vault-path presence (not contents), required variable names with set/missing state, and the blocked or user-controlled next step. A status check is not proof that the credential is valid or that a provider request is included in a subscription.

## Validation

- No vault path, missing CLI, unreadable path and ambiguous variable state must fail closed.
- A completed default check must contain no credential bytes or fragments.
- An injection request cannot be marked done without a separately approved and verified adapter.
