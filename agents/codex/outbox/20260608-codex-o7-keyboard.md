# O-7 keyboard fixes

- Branch: codex/o7-keyboard-fixes
- Worktree: E:/Coding Infra/_worktrees/2ndB-o7-keyboard-fixes
- Commit: 70befd7 fix: adjust keyboard avoidance on capture and chat
- Verify: PASS, npm run verify

Summary:
- Updated src/app/capture.tsx so KeyboardAvoidingView uses iOS padding and Android height, with a safe-area keyboard vertical offset and scroll bottom padding based on the tab bar clearance.
- Updated src/app/secondb.tsx so the chat composer participates in the same iOS and Android keyboard avoidance path, and the message list keeps explicit bottom padding above the composer area.

Notes:
- Only src/app/capture.tsx and src/app/secondb.tsx were changed in the repo.
- The new worktree needed dependency installation before verify because node_modules was absent. npm ci could not run against the existing out-of-sync lockfile, so npm install was run with package-lock disabled and legacy peer deps. No tracked dependency files were changed.
