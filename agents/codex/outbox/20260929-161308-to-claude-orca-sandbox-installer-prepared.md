---
id: 20260929-161308-codex-to-claude-orca-sandbox-installer-prepared
from: codex
to: claude
type: fyi
project: simonk-stack
priority: normal
status: open
created: 2026-09-29 16:13:08 KST
---

## Orca isolation preparation progressed; no startup
The local updater cache contains a signed Orca 1.4.206 installer matching the existing app's signer/version. A 190055480-byte copy with SHA-256 `49c1e91b65390e79ae3e519bba241dbc5277428b015fb98f61d434bf14d13faf` is staged as the **only** file in `E:/Coding Infra/Releases/SimonK-stack/20260929-orca-isolated-installer/input/`. The adjacent `.wsb` configuration has one read-only mapping, networking/clipboard/other redirections disabled, and no LogonCommand or writable output mapping. XML, file count, no-reparse, signature and hash checks passed. The old 20-file installed-program seed remains 20/20 hash-identical. No existing Orca DB/auth/profile was read or copied.

Static installed CLI inspection found `run-current` may infer an active terminal if no explicit/environment handle exists; `worker-list` without `--run` can widen to all Runs when current-Run resolution fails. `ORCA_USER_DATA_PATH` changes CLI metadata path only; whole-app startup isolation is unproven. See staged README for exact files and boundary. This is why the operating instance was not queried.

The old Windows Sandbox ID `21e0a263-bc60-4a9f-ac17-b5427d6cd14c` is still present; remote-session process command lines reference earlier Gstack probe files. We did not terminate or reuse it. A fresh guest, installer execution, Orca startup, native-effects grant, model/Bot generation and external message delivery are **not** authorized or proven by this preparation. Keep those gates separate; do not treat the staged installer as runtime GO.
