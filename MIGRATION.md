# SimonK-stack — 모놀리식 → 플러그인 전환

> **은퇴 (허브 D-87, 2026-10-05).** 이 문서가 설명하던 `scripts/install.sh` 기반 5플러그인 부트스트랩(플러그인 저장소 clone·pull 뒤 `~/.claude/skills`로 복사, `skills-src/` 오프라인 폴백, `SIMONK_SKILLS_TARGET` 테스트 모드)은 은퇴했다. 예전 본문은 git 이력에 있다.

- 루트 `skills/`(스킬 68개)와 루트 `.claude-plugin/plugin.json`(레거시 `simonk-stack` 0.1.0)은 [`_archive/legacy-root-plugin-0.1.0/`](_archive/legacy-root-plugin-0.1.0/README.md)에 보관했다.
- 옛 `install.sh`는 [`_archive/legacy-install/`](_archive/legacy-install/README.md)에 보관했다. `scripts/install.sh`에는 `--offline-package` 진입점만 남았다.

## 지금

- 사용자 설치: [README 3절](README.md#3-설치) — 마켓플레이스 다섯 플러그인(`dist` 브랜치).
- 레거시 0.1.0 사용자: [README 8절](README.md#8-예전-simonk-stack-010에서-옮기기)의 네 줄.
- 이 PC(flat 설치)와 개발: [README 11절](README.md#11-개발자-안내) — `pwsh -File scripts/windows/update-local.ps1`(미리보기, `-Apply`로 설치).
