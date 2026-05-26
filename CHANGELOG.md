# Changelog

모든 중요한 변경은 이 파일에 기록합니다.
형식: [Keep a Changelog](https://keepachangelog.com/), 버전: [SemVer](https://semver.org/).

## [Unreleased]

### Fixed — Bug-hunt sweep (2026-05-27)
- `scripts/install.sh`: 수동 install 시 `skills-src/` 90+ 스킬 누락 (이전엔 `.claude/skills/` 만 sync). **B1**
- `scripts/install.sh` + `.claude/hooks/session-start.sh`: "existing → skip" 정책으로 글로벌이 영구 stale → `git pull` 가 절대 반영 안 되던 문제. install.sh `--force` flag. session-start.sh SHA-aware 선택적 overwrite (installed-SHA ↔ current-SHA git diff 기반 changed-skill set 만 force overwrite) + `SIMON_STACK_FORCE_SYNC=1` env override. **B2**
- 5 SKILL.md self-reference 슬래시 alias 가 실재 슬래시 명령 (folder/frontmatter `name`)과 불일치 → 정확한 이름으로 변경:
  - `/ohmo` → `/simon-ohmo`
  - `/phase4-game` → `/phase4-game-orchestrator`
  - `/session-export` → `/session-context-export`
  - `/keepass` → `/keepass-helper`
  - `/gcloud` → `/gcloud-helper` (`docs/CURATED-SKILLS.md` 포함)
- `templates/CLAUDE.md`: simon-stack 섹션이 "13개"라고 표기 (실제 100+) → Orchestrator / 방법론 / 보안 / 그로스·수익화 / 도구·헬퍼 카테고리로 재정리.
- `docs/USING-IN-OTHER-REPOS.md`: stale 카운트 (24개, 28+, 55+, 60+) → 100+ 통일.

### Added
- `scripts/install.sh`: `--force`, `--no-backup`, `--help` flag 추가. install 후 `~/.claude/.simon-stack-installed` 에 SHA 기록 (session-start.sh 의 selective-update 로직 입력).

## [1.3.0] — 2026-04-16

### Changed — Token optimization + README rewrite
- **구조 분리**: `.claude/skills/` 20개 → `skills-src/` 16개 + `.claude/skills/` 4개 (commit, review, skill-gen-agent, context-guardian)
  - 매 tool call 마다 55+ skill description 이 system-reminder 로 주입되던 토큰 폭발 해결
  - `skills-src/` 는 Claude Code 가 무시 → 개발 중 토큰 사용량 극감
  - 설치 시 hook 이 양쪽 모두 `~/.claude/skills/` 로 복사 (기존 동작 유지)
- **session-start.sh** — `skills-src/` + `.claude/skills/` 양쪽에서 복사하도록 수정
- **setup-repo.sh** — vendor mode 소스 복사 + embedded hook 동일 수정
- **CLAUDE.md** — 디렉토리 구조, 검증 명령, 금기 경로 업데이트

### Docs
- **README.md** — 1,675줄 → 308줄 (81% 축소). 카탈로그 테이블 + 간결한 구조로 리라이트
- **docs/SKILL-REFERENCE.md** — (신규) 상세 skill 알고리즘 문서 (README 에서 분리)

## [1.2.0] — 2026-04-14

### Added — Meta + session management
- **`skill-gen-agent`** — vendored from `github.com/Learner-thepoorman/Skill-Agent`.
  Provides `validate_skill.py`, `test_skill.py`, `refactor_skill.py`,
  `version_log.py`, `install_skill.py` scripts + references + templates
  for creating and improving Claude Code skills from within the repo.
- **`context-guardian`** — 3-mode skill for Claude Code session health:
  - Prevention: inserts `<!-- context-guardian-rules:v1 -->` block into
    CLAUDE.md + generates `.claudeignore` (idempotent)
  - Monitoring: `context_limit_log.json` with measured-not-hardcoded
    token limits, `--load` / `--record` / `--check` subcommands,
    80% / 90% threshold warnings
  - Recovery: `SESSION_RECOVERY.md` generator with git state auto-fill,
    secret-pattern abort, ready-to-copy next-session prompt
- 3 bundled scripts: `install-rules.sh`, `create-recovery.sh`,
  `update-context-log.sh`
- `references/templates.md` documenting all 4 output artifacts
- `evals/cases.json` with 4 test cases per skill

### Validated
- All 20 skills pass `validate_skill.py` with 0 errors / 0 warnings
- Both new skills pass `test_skill.py --dry-run`
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
