# 복원 스크립트 — 20260619-050016 드레인으로 삭제된 브랜치를 origin에 되살린다 (SHA가 GC 전이어야 함).
# 사용: pwsh "C:\Coding Infra\AI Infra\Communication\Output\branch-drain-restore-20260619-050016.ps1"
Set-Location "C:\2ndB"
git push origin 367454d2c140edfcea96d10476f1c84ecd2150e0:refs/heads/feat/art20-export-account   # was 155 behind / 3 ahead, 2026-06-14
git push origin c8320f1ce9b9b35e8ad10f4869847d70b66f449e:refs/heads/chore/worktrees-in-repo   # was 13 behind / 1 ahead, 2026-06-18
git push origin 7ac57e4a705fe962c7e5328a0879fd8bf9efd888:refs/heads/chore/quarantine-legacy-concept   # was 12 behind / 1 ahead, 2026-06-18
git push origin 4c7df1e24be209854536568ebda5479b793ffd39:refs/heads/claude/cyan-global-theme   # was 10 behind / 1 ahead, 2026-06-18
git push origin c3123d9bb566c8bd967f1ff1d67f99755dda9488:refs/heads/claude/cyan-phase2-entry   # was 9 behind / 1 ahead, 2026-06-18
git push origin df0de07e8c8035027546a4d0f84b3776e59caf01:refs/heads/claude/cyan-phase2-nav   # was 8 behind / 1 ahead, 2026-06-18
git push origin c7c26aecca42742b31e22c2ef5aee3219f789b36:refs/heads/claude/cyan-phase2-shape   # was 7 behind / 1 ahead, 2026-06-18
git push origin 680d6d8df3a76454e1d6b6632e1a12a78664d40a:refs/heads/claude/cyan-flat-android   # was 6 behind / 1 ahead, 2026-06-18
git push origin a3ca06d465e80cb3f02d9c737dbfba21a5a1f977:refs/heads/claude/faithful-home   # was 4 behind / 1 ahead, 2026-06-18
