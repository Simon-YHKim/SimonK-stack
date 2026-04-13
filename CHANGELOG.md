# Changelog

모든 중요한 변경은 이 파일에 기록합니다.
형식: [Keep a Changelog](https://keepachangelog.com/), 버전: [SemVer](https://semver.org/).

## [1.1.0] — 2026-04-13

### Added — Repo hygiene + cross-repo distribution
- `.gitignore` — `.claude/settings.local.json`, `.bak`, OS artifacts, editor files, node/bun
- `LICENSE` — MIT + upstream credits (Gstack, Superpowers, ECC)
- `CHANGELOG.md` — this file
- `scripts/setup-repo.sh` — 다른 레포에 simon-stack 설치 (vendor / bootstrap 모드)
- `templates/bootstrap-session-start.sh` — 얇은 drop-in hook
- `templates/bootstrap-settings.json` — settings.json 템플릿
- `docs/USING-IN-OTHER-REPOS.md` — 4-시나리오 결정 트리 가이드

### Fixed
- `scripts/session-start-instincts.sh` — `grep -c` dual-output 버그 (`0\n0` 줄바꿈) + 템플릿 placeholder 가 "최근 실수"에 끼어드는 문제 해결

### Docs
- README 에 cross-repo 섹션 링크 추가
- `.claude/skills/README.md` 를 INDEX.md 포인터로 갱신

## [1.0.0] — 2026-04-12

### Added — simon-stack 통합 스택
- **Orchestrators**: `app-dev-orchestrator` (21단계 마스터 파이프라인),
  `security-orchestrator` (5단계 보안 감사 메타)
- **Security**: `security-checklist` (RLS/구독/RateLimit/예산),
  `authz-designer` (RBAC/ABAC/ReBAC + IDOR 감사),
  `paid-api-guard` (유료 API 6층 방어 + API 설계)
- **Method (simon-\*)**: `simon-tdd` (RED-GREEN-REFACTOR),
  `simon-worktree` (병렬 세션 격리), `simon-research` (리서치 우선),
  `simon-instincts` (누적 학습)
- **Tools**: `nextjs-optimizer` (Next.js 5대 최적화),
  `stitch-design-flow` (Stitch 프롬프트 생성기),
  `project-context-md` (프로젝트별 CLAUDE.md 템플릿)
- **Instincts**: 4 seed 파일 (`mistakes-learned`, `project-patterns`,
  `korean-context`, `tool-quirks`)
- **Templates**: `templates/CLAUDE.md` (글로벌 CLAUDE.md, Boris 원칙 + skill 맵)
- **Scripts**:
  - `scripts/install.sh` — 로컬 데스크탑 설치
  - `scripts/session-start-instincts.sh` — user-level instincts 요약 hook
- **Hook**: `.claude/hooks/session-start.sh` — Claude Code 웹 매 세션 bootstrap
- **Config**: `.claude/settings.json` — SessionStart hook + Skill permission
- **Docs**: `README.md`, `docs/INSTALL.md`, `docs/MORNING-START.md`

### Infra
- Gstack 풀 런타임 (36 skills + bin/scripts/lib + bun install)
- 매 세션 idempotent 재설치 (marker 파일 기반)

## [0.1.0] — 2026-04-12

### Added — Base
- `commit`, `review`, `debug`, `refactor`, `test-gen`, `explain` —
  6 일반 개발 skill
- `.claude/skills/README.md` — 최초 skill 안내
