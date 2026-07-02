# 복원 스크립트 — 20260620-165936 드레인으로 삭제된 브랜치를 origin에 되살린다 (SHA가 GC 전이어야 함).
# 사용: pwsh "C:\Coding Infra\AI Infra\Communication\Output\branch-drain-restore-20260620-165936.ps1"
Set-Location "C:\2ndB"
git push origin 367454d2c140edfcea96d10476f1c84ecd2150e0:refs/heads/feat/art20-export-account   # was 197 behind / 3 ahead, 2026-06-14
git push origin 083df8cb08585a7ab0536b14e21683ad065b6e3f:refs/heads/wip/deep-space-20260616   # was 154 behind / 2 ahead, 2026-06-16
git push origin c8320f1ce9b9b35e8ad10f4869847d70b66f449e:refs/heads/chore/worktrees-in-repo   # was 55 behind / 1 ahead, 2026-06-18
git push origin 7ac57e4a705fe962c7e5328a0879fd8bf9efd888:refs/heads/chore/quarantine-legacy-concept   # was 54 behind / 1 ahead, 2026-06-18
git push origin 4c7df1e24be209854536568ebda5479b793ffd39:refs/heads/claude/cyan-global-theme   # was 52 behind / 1 ahead, 2026-06-18
git push origin c3123d9bb566c8bd967f1ff1d67f99755dda9488:refs/heads/claude/cyan-phase2-entry   # was 51 behind / 1 ahead, 2026-06-18
git push origin df0de07e8c8035027546a4d0f84b3776e59caf01:refs/heads/claude/cyan-phase2-nav   # was 50 behind / 1 ahead, 2026-06-18
git push origin c7c26aecca42742b31e22c2ef5aee3219f789b36:refs/heads/claude/cyan-phase2-shape   # was 49 behind / 1 ahead, 2026-06-18
git push origin 680d6d8df3a76454e1d6b6632e1a12a78664d40a:refs/heads/claude/cyan-flat-android   # was 48 behind / 1 ahead, 2026-06-18
git push origin a3ca06d465e80cb3f02d9c737dbfba21a5a1f977:refs/heads/claude/faithful-home   # was 46 behind / 1 ahead, 2026-06-18
git push origin 80169e671dfc5d138f7a6f203507bae30cd265a4:refs/heads/claude/github-livelink-screenshot-access-nny76s   # was 40 behind / 1 ahead, 2026-06-19
git push origin 719d82f3ee8dbf81281be90c55822d3e2e5e7859:refs/heads/claude/native-deepspace-82evat   # was 22 behind / 1 ahead, 2026-06-19
git push origin a1a9a5f7494ece70e2f703d18e8f325dd676e2f0:refs/heads/claude/import-manual-82evat   # was 22 behind / 1 ahead, 2026-06-19
git push origin 6320f52bd2d82543c1ef190637138690fdb682fd:refs/heads/claude/health-slice1-82evat   # was 19 behind / 2 ahead, 2026-06-19
git push origin 5b573ff6a3d99858966053a322c944e0d1925db6:refs/heads/claude/ops-routines-82evat   # was 19 behind / 1 ahead, 2026-06-19
git push origin 99dcdc9022f1a2c7f0f05c8f5aa5de1a8d8963ef:refs/heads/claude/health-slice1-clean-82evat   # was 18 behind / 1 ahead, 2026-06-19
git push origin d2ed9273a923877cc38f3bbcbe78aa2b827a0b83:refs/heads/claude/auth-rebased-82evat   # was 17 behind / 1 ahead, 2026-06-19
git push origin 0cdf7e8c83351718a584e2cdd943915cb12a18ff:refs/heads/claude/pomodoro-focus-82evat   # was 16 behind / 1 ahead, 2026-06-19
git push origin ca510d8f8d9f35e7bd142786b532caef0c35df4d:refs/heads/claude/assistant-roadmap-82evat   # was 16 behind / 1 ahead, 2026-06-19
git push origin df648162dda3ba7c9c30c9f15b2fdbae9b3a07c7:refs/heads/claude/language-srs-82evat   # was 14 behind / 1 ahead, 2026-06-19
git push origin 349c9508068a826727dec9c34378c618d1aac70c:refs/heads/claude/ops-meal-plan   # was 11 behind / 1 ahead, 2026-06-20
git push origin 4a6c54fb09773fa3d90d03d0e68bebadaf5aecdc:refs/heads/claude/ops-ia   # was 11 behind / 1 ahead, 2026-06-20
git push origin c81f7f1bca22002172531829429ffaa5f582c38d:refs/heads/claude/ops-remaining-surfaces   # was 9 behind / 1 ahead, 2026-06-20
git push origin 7a15b72b2f2b8f4b0296833a91aa253f94ed03c7:refs/heads/claude/ops-grounding   # was 8 behind / 1 ahead, 2026-06-20
git push origin c3023c33a2b51dbc3adedf14ca73eb7204eef146:refs/heads/claude/personal-data-import   # was 7 behind / 1 ahead, 2026-06-20
git push origin 12a4b67feac41bb2bac1080c08824704619901a9:refs/heads/claude/import-parsers-2   # was 6 behind / 1 ahead, 2026-06-20
git push origin 7982f591df131a1bac3ef988a276618650f2b22b:refs/heads/claude/import-dispatch   # was 5 behind / 1 ahead, 2026-06-20
git push origin 17479055a91ed76568dc46bc5b5d902a70b94312:refs/heads/claude/import-spec   # was 4 behind / 1 ahead, 2026-06-20
git push origin f8442455cd4f905164c3ca95fd3c533b72ecd3cd:refs/heads/claude/import-hub   # was 3 behind / 1 ahead, 2026-06-20
git push origin c6c4ed581dbeecd8cbceefdc62f41c0640565b20:refs/heads/claude/import-revoke   # was 2 behind / 1 ahead, 2026-06-20
git push origin 362e6fc0c601628e2ea08c5c8c022f5ba9367fe9:refs/heads/claude/gate-runbook   # was 1 behind / 1 ahead, 2026-06-20
