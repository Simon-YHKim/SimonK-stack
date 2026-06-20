# O-8 C2 Shadows Cleanup

Branch: `codex/o8-shadows`

Worktree: `E:/Coding Infra/_worktrees/2ndB-o8-shadows`

Commit: `2a6bdbe36e06bf7c39f28d54af3865e843a5f604`

Summary:
- Removed the shared `PremiumCard` glow prop and `PremiumPanel` halo path.
- Removed shared `PremiumButton` shadow, glow, and Android elevation styling.
- Deleted screen-level shadow and elevation keys from the C2 targets: capture, secondb, index, profile, settings, and account.
- Removed remaining `PremiumCard glow` call sites in esm and import so the shared API removal type-checks.
- Left graph glow behavior untouched. No NavGraph NodeGlow changes.

Verification:
- `npm run verify` passed.
- The new worktree had no local dependencies. `npm ci` was blocked by pre-existing package lock drift, so verify was run with a temporary junction to `E:/2ndB/node_modules`.
- The temporary `node_modules` junction was removed after verification.
