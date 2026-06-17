# 복원 스크립트 — 20260617-214827 드레인으로 삭제된 브랜치를 origin에 되살린다 (SHA가 GC 전이어야 함).
# 사용: pwsh "C:\Coding Infra\AI Infra\Communication\Output\branch-drain-restore-20260617-214827.ps1"
Set-Location "C:\2ndB"
git push origin 21a73efb2db48460bd32a832e29e314a3301376a:refs/heads/feat/o21-landing-live   # was 102 behind / 1 ahead, 2026-06-15
git push origin f96be28edd9a7bb1325d01f9a948c0345f6674bb:refs/heads/claude/iden-ui   # was 45 behind / 1 ahead, 2026-06-16
git push origin 9a42c4f0e417a6b7ec2fa9483b8ea16384765d1e:refs/heads/handoff/20260616-1850   # was 44 behind / 1 ahead, 2026-06-16
git push origin d9abe64b93b2c19311fa6ea96fb264f0d0ba33fe:refs/heads/feat/deep-space-nav-stage2   # was 5 behind / 1 ahead, 2026-06-17
