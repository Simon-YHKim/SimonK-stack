# Coding-root migration (moving C:\Coding -> "C:\Coding Infra" or a new laptop)

Most of the environment travels with git. Three classes of **machine-specific**
references do **not**, so a drive/folder move silently breaks the session
bootstrap until they are repointed:

| What | Why it breaks | Fixed by |
|---|---|---|
| User env vars `SIMON_STACK_DIR`, `SIMONK_PROJECT_DIR`, `SIMON_WIKI_DIR` | stored in the Windows registry, not git; the SessionStart bootstrap reads `SIMON_STACK_DIR` to find this repo | `heal-coding-paths.ps1` |
| `SimonK-*` Scheduled Tasks (e.g. `SimonK-MemoryGuard` every 5 min) | the task's `-File` path is absolute; after a move it points at a deleted file and the launcher flashes/fails | `heal-coding-paths.ps1` |
| `~/.claude/**` (global CLAUDE.md, instincts, memory) | lives in the user home, not on the moved drive | copy by hand / `install.sh` reseeds |

## One-shot fix

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\heal-coding-paths.ps1
# preview first:  ... -File scripts\heal-coding-paths.ps1 -DryRun
```

`heal-coding-paths.ps1` derives the **current** coding root from its own
location (`<root>\Harrness Eng\SimonK-stack\scripts\`) and repoints the three
env vars + the known `SimonK-*` tasks to it. It is **idempotent** — a no-op once
everything already matches — and needs no admin (only the current user's env and
tasks). Scheduled tasks are rewired through `<root>\tools\run-hidden.vbs` so
their periodic runs never flash a console window.

## Automatic detection

- **On install:** `scripts/install.sh` runs the healer automatically on Windows
  (best-effort, non-fatal). So `git pull && ./scripts/install.sh --force` after a
  move is enough.
- **Every session:** the SessionStart hook compares the three env vars against
  where this repo actually lives and prints a `[PATHS_STALE]` banner (with the
  one-shot command) if any still point at an old root.

## Full move checklist

See `MIGRATION.md` at the coding-root for the complete drive-move / re-clone
guide (Node/Git/CLI installs, `.env` re-creation, `암호.kdbx`, hub resume). This
doc covers only the path-reference healing that the move tends to miss.
