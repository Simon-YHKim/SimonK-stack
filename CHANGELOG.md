# Changelog

모든 중요한 변경은 이 파일에 기록합니다.
형식: [Keep a Changelog](https://keepachangelog.com/), 버전: [SemVer](https://semver.org/).

## [1.4.0] — 2026-05-27

Sprint D — 전체 스킬 chain audit, Wiki 정합성, 설치 ease, 100% functional perfection.

PR 머지: SimonK-stack #9 #10 #11 #12 #13 + SimonKWiki #4 + 2nd-B #18.

### Fixed — Install & hook critical
- **B1** `scripts/install.sh`: 수동 install 시 `skills-src/` 90+ 스킬 누락 (이전엔 `.claude/skills/` 만 sync). (#9)
- **B2** `scripts/install.sh` + `.claude/hooks/session-start.sh`: "existing → skip" 정책으로 글로벌 영구 stale → `git pull` 가 반영 안 되던 문제. install.sh `--force` flag. session-start.sh SHA-aware 선택적 overwrite (installed-SHA ↔ current-SHA git diff 로 changed-skill set 만 force overwrite) + `SIMON_STACK_FORCE_SYNC=1` env. (#9)
- **B2-bis** `.claude/hooks/session-start.sh`: SHA-diff sed 명령이 separator `|` 와 ERE alternation `|` 충돌 → CHANGED_SET 추출 silently fail → B2 fix 가 사실상 작동 안 함. separator `#` 으로 교체. (#10)
- **C1** `connect-chrome` 폴더가 `open-gstack-browser` 와 동일 `name:` field → Claude Code dedupe → zombie. install/hook 의 sync loop 에 명시적 skip. Gstack auto-generated SKILL.md 라 직접 수정 금지. (#13)

### Fixed — Skill chain orchestration
- 5 SKILL.md self-reference 슬래시 alias 가 frontmatter `name` 과 불일치 → 정확한 이름으로 변경: `/ohmo` → `/simon-ohmo`, `/phase4-game` → `/phase4-game-orchestrator`, `/session-export` → `/session-context-export`, `/keepass` → `/keepass-helper`, `/gcloud` → `/gcloud-helper` (`docs/CURATED-SKILLS.md` 포함). (#9)
- `simon-design-first` Step 5: 4 → 7 design skill 전체 chain 으로 확장. `/plan-design-review` + `/design-review` 가 위임 분기에서 빠져있던 문제 해결. (#11)
- `app-dev-orchestrator` 단계 3.5 (`simon-design-first` proxy) 신규 — description 이 명시한 "mandatory proxy before /design-consultation 등" 계약을 본문 chain 에 반영. (#11)
- `simon-design-first` Step 5.5: 5 시나리오 decision matrix (zero-to-one / existing refactor / live polish / variant only / external Stitch only) — chain bloat 방지 + LLM 가지치기 가능. (#12)
- `simon-research` description: orchestrator coverage 를 `app-dev-orchestrator` 에서 `dev-orchestrator` + `security-orchestrator` 까지 확장. (#13)
- `payment-integrator` Related Skills: `subscription-manager-selector` back-ref 추가 (asymmetric link graph 해소). (#13)
- `test-gen` Related skills trailer 추가 (canonical 4-skill cross-ref). (#13)
- `wiki-ingest` / `wiki-query` / `wiki-lint`: bidirectional cross-refs 추가 (3 skill 이 같은 vault 다루는데 서로 무링크였음). (#13)

### Fixed — Docs / Wiki
- `templates/CLAUDE.md`: simon-stack "13개" 표기 → "100+개" + 카테고리 재정리 (Orchestrator / 방법론 / 보안 / 그로스·수익화 / 도구·헬퍼). (#9)
- `docs/USING-IN-OTHER-REPOS.md`: stale 카운트 (24개 / 28+ / 55+ / 60+) → 100+ 통일. (#9)
- `README.md` / `README.en.md`: "0 errors / 0 warnings" → "0 errors / 56 minor warnings" (실측, description score 등 비차단). (#10)
- `docs/INSTALL.md`: 36 Gstack / 24 simon-stack → 38+ / 100+ + `~/.claude/.simon-stack-installed` marker 안내 추가. (#13 follow-up)
- **SimonKWiki PR #4**: `wiki/entities/tools/getdesign-md.md` 의 broken `[[design-consultation]]` / `[[design-shotgun]]` / `[[simon-design-first]]` → backtick (skill names, not wiki pages). `wiki/index.md`: last-updated 2026-05-25 → 2026-05-27, 페이지 카운트 메인 89→129, total 115→155.

### Fixed — Downstream (2nd-B repo, PR #18)
- `.claude/settings.json`: inline-bash hook → `templates/bootstrap-session-start.sh` 정식 위임 형식.
- `.claude/hooks/session-start.sh` (신규): bootstrap script + `SIMON_STACK_REPO` default 를 `Simon-YHKim/SimonK-stack` 로 명시 (transferred URL redirect 의존 제거).
- `CLAUDE.md`: ghost slash commands `/context-save` / `/context-restore` → `/checkpoint` + `/context-guardian`.

### Added
- `scripts/install.sh`: `--force`, `--no-backup`, `--help` flags. install 후 `~/.claude/.simon-stack-installed` 에 SHA 기록.
- `.claude/hooks/session-start.sh`: SHA-aware selective overwrite + `SIMON_STACK_FORCE_SYNC=1` env var.
- 2nd-B 같은 다운스트림 repo 의 정식 bootstrap hook 패턴 (templates/bootstrap-session-start.sh + bootstrap-settings.json) 검증·문서화.

### Verified
- 108 SKILL.md 모두 `validate_skill.py` 0 errors (56 minor warnings — W013 long ref no-TOC 33 / W009 path resolve 15 / W006/W007/W004 8 — 모두 비차단, cosmetic).
- 106 unique invocable skills (connect-chrome dedupe 후).
- 6 orchestrator chain + 7 design skill chain + 6 chain category 전수 audit (Planning / Implementation / Security / Ship & Deploy / Growth & Monetization / Korean & Helper / Wiki & Memory) — chain integrity strong.
- Wiki health: lint-report v4 후 mostly-healthy (E3→E0 after fix, W2 user-judgment 잔존).
- End-to-end: 2nd-B bootstrap hook → `~/.simon-stack-src` clone → upstream session-start.sh delegate → global `~/.claude/skills` sync 정상 동작.

### Follow-ups
- gstack upstream 99 commits behind (`~/.claude/skills/gstack/` 38 modified files) → 사용자 직접 `/gstack-upgrade` 호출 권장 (destructive 변경 위험 — 자동 처리 안 함).
- W009 false-positive 다수 (`scripts/X.ps1` 가 repo-root 기준인데 validate_skill.py 가 skill-folder 기준 resolve) → upstream Skill-Agent (`Learner-thepoorman/Skill-Agent`) PR 별도.
- W013 (reference 파일 > 400 lines + no `## Contents`) → 33 references TOC 추가 별도 작업.
- Windows-native `install.ps1` (bash 의존 제거) — 다른 머신용 nice-to-have.

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
