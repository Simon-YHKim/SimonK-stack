# 복원 스크립트 — 20260618-050009 드레인으로 삭제된 브랜치를 origin에 되살린다 (SHA가 GC 전이어야 함).
# 사용: pwsh "C:\Coding Infra\AI Infra\Communication\Output\branch-drain-restore-20260618-050009.ps1"
Set-Location "C:\2ndB"
git push origin c8320f1ce9b9b35e8ad10f4869847d70b66f449e:refs/heads/chore/worktrees-in-repo   # was 2 behind / 1 ahead, 2026-06-18
git push origin 7ac57e4a705fe962c7e5328a0879fd8bf9efd888:refs/heads/chore/quarantine-legacy-concept   # was 1 behind / 1 ahead, 2026-06-18
