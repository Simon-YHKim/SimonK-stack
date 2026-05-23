# CLAUDE.md — Gstack-Ultraplan-Superpowers (simon-stack)

Claude Code reads this file at session start. This is a **skill development repo** — the 20+ skills here are shipped to downstream projects via the SessionStart hook. You are not building an app; you are curating a skill library.

## 🎯 작업 맥락

이 레포의 주 작업:
- **Skill 작성·수정·검증** (`skills-src/<name>/SKILL.md` 또는 `.claude/skills/<name>/SKILL.md`)
- **Hook·script 개선** (`.claude/hooks/`, `scripts/`)
- **README·docs 유지보수**
- **Instincts seed 갱신** (`.claude/instincts/`)

실제 앱 코드는 없습니다. 대신 *다른 프로젝트가 이 레포를 import 해서* 55+ skill 을 자동 장착하게 만드는 것이 목표.

## 🔧 검증 도구 (Claude 가 스스로 확인 가능)

Skill 수정 후 **반드시** 아래를 실행:

```bash
# 단일 skill 검증 (skills-src/ 또는 .claude/skills/ 경로)
python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py skills-src/<name>

# 전체 repo 검증 (skills-src/ + .claude/skills/ 모두)
for d in skills-src/*/ .claude/skills/*/; do
  [ -f "${d}SKILL.md" ] || continue
  python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py "${d%/}" 2>&1 | grep Result
done

# JSON cases dry-run
python3 .claude/skills/skill-gen-agent/scripts/test_skill.py \
  skills-src/<name> --cases skills-src/<name>/evals/cases.json --dry-run

# Skill-Agent 통합 테스트 (24 checks)
python3 .claude/skills/skill-gen-agent/scripts/tests/run_all.py

# SessionStart hook 수동 실행 (idempotent)
CLAUDE_PROJECT_DIR=$PWD CLAUDE_CODE_REMOTE=true bash .claude/hooks/session-start.sh

# Bash 스크립트 문법 체크
for f in scripts/*.sh .claude/hooks/*.sh .claude/skills/*/scripts/*.sh skills-src/*/scripts/*.sh; do
  [ -f "$f" ] || continue; bash -n "$f" && echo "OK: $f"
done

# YAML frontmatter 파싱 (skills-src/ + .claude/skills/)
python3 -c "
import yaml, pathlib
for base in ['skills-src', '.claude/skills']:
  for p in pathlib.Path(base).rglob('SKILL.md'):
    yaml.safe_load(open(p).read().split('---')[1])
print('YAML OK')
"
```

**원칙**: Claude 가 눈으로 확인할 수 없으면 = 검증 실패. 사용자에게 "확인해 주세요" 라고 말하지 말고 위 명령을 실행하세요.

## 📂 디렉토리 구조

```
skills-src/                    ← 배포용 skill 소스 (16개, Claude Code 미로딩)
├── app-dev-orchestrator/
├── simon-tdd/
├── ... (배포 대상 skill)

.claude/
├── hooks/session-start.sh   ← 매 세션 bootstrap (self-healing)
├── settings.json             ← Hook + Skill permission
├── instincts/                ← 4 seed md (학습 누적)
└── skills/                   ← 개발용 skill (4개만, Claude Code 로딩)
    ├── commit/               ← 커밋 워크플로
    ├── review/               ← 코드 리뷰
    ├── skill-gen-agent/      ← validator + test harness (vendored)
    └── context-guardian/     ← 세션 보호

docs/                          ← INSTALL / MORNING-START / USING-IN-OTHER-REPOS
scripts/                       ← install.sh, setup-repo.sh
templates/                     ← CLAUDE.md (global), bootstrap-*.sh
README.md
CHANGELOG.md                   ← Keep a Changelog
LICENSE                        ← MIT + upstream credits
```

> **왜 분리?** `.claude/skills/` 에 skill 이 많으면 매 tool call 마다 모든 description 이
> system-reminder 로 주입되어 토큰이 폭발한다. `skills-src/` 는 Claude Code 가 무시하므로
> 개발 중 토큰 사용량이 극적으로 줄어든다. 설치 시 hook 이 양쪽 모두 복사.

## 🚫 금기 (건드리면 안 되는 곳)

- **`.claude/skills/gstack/`** — upstream (garrytan/gstack) 에서 clone. 약 12 MB / 450 파일. **절대 직접 수정하거나 Read 로 스캔 금지.** `.claudeignore` 로 차단됨.
- **`.claude/skills/gstack/node_modules/`** — bun 이 관리
- **`.claude.bak-*/`** — 설치 전 백업. 읽기 금지.
- **기존 base commit 6 파일** (`commit`, `debug`, `explain`, `refactor`, `review`, `test-gen` SKILL.md): description 과 version 은 개선됐지만 본문은 원저자 존중. 본문 재작성 전 사용자 승인 필수. (4개는 `.claude/skills/`, 나머지는 `skills-src/` 에 위치)

## 💡 관용 / 컨벤션

- **Skill 수정 후 필수**: `validate_skill.py` 실행 + 0 errors / 0 warnings 확인
- **새 skill 작성 시**: `evals/cases.json` 에 최소 2 개 test case 포함
- **새 skill 작성은 반드시 `skill-gen-agent` 경유**: 7단계 검증 파이프라인을 스킵하면 description 점수·네이밍·길이 한도 위반이 누락됨. 직접 SKILL.md 작성 금지.
- **Description 작성**:
  - `"Use when..."` 으로 시작
  - 한국어 + 영어 트리거 문구 병기
  - 구체 사용자 구문 포함 ("새 앱 만들자", "debug this" 등)
  - 400-900 자 사이, state the output
- **Commit**: Conventional Commits (`feat(skills):`, `fix(hook):`, `docs(readme):`, `chore:`, `test:`)
- **Skill 이름**: kebab-case, ≤ 64 자, `claude`/`anthropic` 예약어 금지
- **SKILL.md 본문**: < 500 줄 (400 에서 warning). 넘으면 `references/*.md` 로 분리 + TOC

<!-- context-guardian-rules:v1 -->
## Context Guardian Rules (auto-maintained)

SessionStart hook 이 매 세션 시작 시 이 블록 존재를 확인하고, 없으면 자동 재삽입합니다 (self-healing).

### 작업 범위 제한
- 한 세션에서 수정 파일 **최대 5 개**
- 한 번에 하나의 skill / hook / 문서 단위로만 작업
- 작업 완료 즉시 `git commit` 후 세션 종료 권고

### 파일 읽기 제한
- **`.claude/skills/gstack/` 읽기 금지** (12 MB, 450 files — `.claudeignore` 로 차단됨)
- `.claude.bak-*/`, `/tmp/simon-stack-*.log` 읽기 금지
- 1000 줄+ 파일은 Read offset+limit 으로 부분 읽기
- `node_modules/`, `.next/`, `dist/`, `.git/` 목적 없는 스캔 금지

### 작업 요청 방식
- 광범위 요청 ("전체 skill 개선") → 작은 단위로 분해 후 사용자 확인
- Plan 모드로 먼저 계획 수립 → 승인 후 실행
- **이 레포 특이 사항**: tool call 마다 55+ skill description 이 system-reminder 로 반복되어 컨텍스트가 빠르게 쌓임. 따라서:
  - Bash 호출 **최소화** — 여러 작업을 하나의 Bash 로 배치
  - `python3 <<PY ... PY` heredoc 으로 여러 파일 생성 batch 처리
  - Write tool 이 Bash 보다 reminder 가 적음 — 복잡 content 는 Write 선호
  - 불필요한 Read 금지 (특히 대용량 파일)

### 컨텍스트 보호
- 80 % 도달 시 `SESSION_RECOVERY.md` 생성 + 새 세션 전환 권고
- 90 % 도달 시 즉시 작업 마무리 + 새 세션 강제

### 복구 사이클
- 세션 끊기 전: `bash .claude/skills/context-guardian/scripts/create-recovery.sh`
- 새 세션 첫 메시지: "SESSION_RECOVERY.md 읽고 이어해줘"

## 📚 이 레포에서 특히 자주 쓰는 skill

- **`skill-gen-agent`** — 모든 skill 수정의 검증 표준
- **`context-guardian`** — 이 파일이 관리하는 규칙의 source. 세션 시작 시 auto-heal
- **`commit`** — Conventional Commits 준수
- **`review`** — PR 사전 리뷰
- **`simon-tdd`** — 새 script/feature 추가 시 RED-GREEN-REFACTOR
- **`/ship`** (Gstack) — VERSION + CHANGELOG + push + PR

## 🧠 Instincts (auto-loaded)

`~/.claude/instincts/` 4 개 파일 참조:
- `mistakes-learned.md` — Claude 실수 누적 (grep -c exit 1, Plan 파일 시크릿 substring 등)
- `project-patterns.md` — 프로젝트별 관용
- `korean-context.md` — 한국 API 특이사항
- `tool-quirks.md` — CLI·하네스 함정

실수 지적 받으면 즉시 `simon-instincts` 로 append.

## 📖 Wiki 참고 (필수)

**SimonK Stack 의 모든 작업은 SimonKWiki 를 _먼저_ 참고합니다.**

> **2026-05-23 통합 메모**: 로컬 vault 경로 = `SimonKWiki` (단일 정본). GitHub repo 이름은 그대로 [`Simon-YHKim/Simon-LLM-Wiki`](https://github.com/Simon-YHKim/Simon-LLM-Wiki) **(PRIVATE)**. 훅 3개 (`session-start.sh`/`user-prompt-submit.sh`/`stop.sh`)가 SimonKWiki·Simon-LLM-Wiki 둘 다 자동 감지. 본 섹션 이하의 'Simon-LLM-Wiki' 참조는 GitHub repo 식별자로 해석. wiki/ 콘텐츠는 `SimonKWiki/wiki/protocols/llm-wiki/` 하위에 위치.

이는 instincts 와 보완 관계:
- `instincts` = 코딩 도메인 (mistakes, patterns, korean API, tool quirks)
- `SimonKWiki` (repo: Simon-LLM-Wiki) = 사용자 메타 인지 도메인 (작업 성향, 의사결정 패턴, 누적 결론)

### 세션 시작 시 (자동 권장)

```bash
[ -d ~/.claude/wiki/Simon-LLM-Wiki ] && (
  cd ~/.claude/wiki/Simon-LLM-Wiki && git pull --quiet 2>/dev/null
  cat LESSONS_LEARNED.md
  echo "--- recent log ---"
  grep "^## \[" wiki/log.md 2>/dev/null | tail -10
) || echo "[wiki] not cloned yet — bash scripts/wiki-init.sh"
```

### 작업 단위로 참고할 핵심 페이지

경로 prefix: `SimonKWiki/wiki/protocols/llm-wiki/` (또는 환경변수 `$SIMON_WIKI_DIR` 가리키는 vault root).

| 작업 | wiki 페이지 |
|---|---|
| 새 프로젝트 시작 | `entities/simon-yhkim.md § Tech Preferences` |
| 의사결정 / 추천 | `LESSONS_LEARNED.md § T-001..T-N` |
| 어투 검사 | `concepts/anti-llm-voice.md` |
| SEO / 런칭 | `concepts/seo-essentials.md` |
| 같은 실수 반복 의심 | `concepts/recurring-mistakes.md § M-001..M-N` |

### 세션 종료 시 (필수)

새 mistake / 결론 / 사용자 패턴 발견 시 wiki append:
```bash
cd ~/.claude/wiki/Simon-LLM-Wiki
bash ~/eject-button/.claude/skills/llm-wiki-builder/scripts/log-append.sh \
  refactor "<요약>" "- Updated: <pages>"
git add . && git commit -m "session: <요약>" && git push
```

자세한 절차: wiki 의 `concepts/session-meta-analysis.md`.

## 🔄 Stack 자체 업데이트 체크 (사용 전)

SimonK Stack 사용 _전_ 에 origin 에 새 커밋이 있는지 확인:

```bash
# Wiki (SimonKWiki canonical, Simon-LLM-Wiki legacy) — auto-detect
for d in ~/.claude/wiki/SimonKWiki ~/.claude/wiki/Simon-LLM-Wiki; do
  [ -d "$d/.git" ] || continue
  ( cd "$d" && git fetch --quiet origin && \
    [ "$(git rev-list HEAD..origin/main --count 2>/dev/null)" -gt 0 ] && \
    echo "[wiki:$(basename "$d")] origin has new commits — git pull 권장" )
  break
done

cd ~/SimonK-stack 2>/dev/null
[ -d .git ] && git fetch --quiet origin && \
  [ "$(git rev-list HEAD..origin/main --count 2>/dev/null)" -gt 0 ] && \
  echo "[simonk-stack] origin has new commits — /gstack-upgrade 권장"
```

`session-start.sh` 가 이 체크를 매 세션 시작에 1회 실행 권장 (옵션 — 후속 작업).

## 🔁 Hook 자동화 매트릭스

세 종류의 hook 이 사용자 명시 없이 wiki 누적·반영을 _자동_ 으로 처리합니다.

| Hook | 시점 | 동작 |
|---|---|---|
| **SessionStart** | 세션 시작 | bootstrap (skills 설치, instincts seed) + update 감지 (SimonK / gstack / wiki) + auto-pull (clean+main+ff) + `~/.claude/.update-pending` fallback |
| **UserPromptSubmit** | 매 사용자 발화 전 | wiki 의 5초 인덱스 + 최근 3 log + M/T totals 를 _system context_ 에 inject. LLM 자발성 보강 — _사용자가 언급 안 해도_ wiki 인지 상태 |
| **Stop** | LLM 응답 종료 시 | wiki/instincts repo 가 dirty 면 자동 commit + push (branch=main + md/json 변경 위주 필터). LLM 이 _수정만 하면 영속화_ 자동 |

**효과**: A (Stop hook) 가 _영속화 누락_ 을 막고, C (UserPromptSubmit hook) 가 _LLM 의 wiki 인지_ 를 매 발화 강제. 사용자 발화에 "wiki", "오답노트" 같은 키워드가 없어도 _LLM 이 스스로_ M-xxx / T-xxx append 할 가능성 ↑.

**비용**:
- UserPromptSubmit: 매 발화 ~300-500 토큰 (인덱스 + 최근 log 만 inject — 컴팩트하게 유지)
- Stop: 0 토큰 (bash 만)

**Opt-out**: `.claude/settings.json` 에서 해당 hook 블록 제거.

## 🚀 세션 시작 정책 (필수)

**SimonK Stack 을 사용하는 모든 세션의 첫 동작은 업데이트 확인.**

`.claude/hooks/session-start.sh` 가 세션 시작 직후 SimonK-stack / gstack 업스트림 / Simon-LLM-Wiki 의 origin 에 새 커밋이 있는지 fetch + ahead-count 체크합니다.

### 세션 시작 시 — LLM 의 **첫 번째 동작** (예외 없음)

세션 시작 시 SessionStart hook 출력이 LLM 컨텍스트에 안 들어오는 환경 (Claude Code 의 일부 모드, 또는 hook stdout 이 system message 로 안 가는 경우) 도 대비해 **file-based fallback** 을 운영합니다.

**LLM 은 첫 응답 _전_ 다음 한 줄을 실행해야 합니다**:

```bash
[ -f ~/.claude/.update-pending ] && cat ~/.claude/.update-pending && rm ~/.claude/.update-pending
```

파일이 비어 있으면 silent — 정상. 파일이 있으면 그 내용을 보고 아래 정책대로 처리.

### 자동 처리 vs 수동 처리

`session-start.sh` 가 다음을 _자동_ 으로 합니다 (안전 조건 = clean tree + on main):
- **SimonK-stack auto-pull** — origin/main ahead 이고 안전하면 `git pull --ff-only` 즉시 실행
- **Simon-LLM-Wiki auto-pull** — 같음

LLM 이 직접 처리할 것:
- **gstack upstream 업데이트** → `/gstack-upgrade` 호출 (gstack 의 _자체 upgrade_ 스킬)
  - install type 자동 감지 (global-git / local-git / vendored)
  - gstack 본체 + 로컬 vendored gstack 카피 sync
  - ⚠️ **이 스킬은 SimonK-stack 자체는 pull 안 함** (gstack 의 책임 도메인이 아님). SimonK-stack pull 은 위의 session-start.sh auto-pull 이 담당.
  - `GSTACK_AUTO_UPGRADE=1` 또는 `gstack-config set auto_upgrade true` 면 사용자 확인 없이 진행

### `[UPGRADE_AVAILABLE]` 가 출력되면 — LLM 의 첫 동작

박스 내용을 _읽고_ 다음을 수행:
1. **`auto-pulled ✓` 표시가 있는 항목** — 이미 처리됨. 단, Simon-LLM-Wiki auto-pull 시 LESSONS_LEARNED.md 재독.
2. **gstack 항목이 있으면** → `/gstack-upgrade` 호출.
3. **`auto-pull skipped` / `failed` 항목이 있으면** → 사용자에게 1줄 보고 (dirty / 다른 브랜치 / ff 불가 사유 안내).

이후 원래 사용자 요청 처리.

### `[UPGRADE_AVAILABLE]` 가 없으면

별다른 보고 없이 사용자 요청 즉시 처리. 매번 "최신입니다" 같은 narration 금지 (T-003 — 토큰 효율).

### 정책 예외

- 사용자가 _명시적으로_ "업데이트 하지 마", "그대로 가자" 라고 한 세션: skip
- working tree dirty / non-main branch: `git pull --ff-only` 가 자동 실패 → 사용자에게 한 줄 보고 후 수동 처리 요청
- `/gstack-upgrade` "Never ask again" 상태: 스킬 자체가 update check 비활성화

**이 정책의 의도**: vendoring 이 안정성을 위한 _명시적 sync 게이트_ 라는 설계를 살리되, 게이트가 자동으로 _트리거_ 되도록 해서 stale 상태를 방지.

---

## 🤖 simonk 통합 자율 하네스 (2026-05-23 추가)

`simonk` 는 OMC·OMO·OpenHarness 3 철학을 종합한 **단일 자율 실행 진입점**. Claude Code Task tool 기반 self-contained (외부 plugin 의존 X).

### 사용

```powershell
# PowerShell (어디서든)
simonK "task description"            # non-interactive, /simonK 호출 자동
simonK                                # interactive, claude 열림

# Claude Code 슬래시 (interactive session)
/simonK <task>
```

대소문자 무관 (alias `simonk`, `SimonK` 모두 작동).

### 6-Phase 실행 흐름

```
Phase 1: Ambiguity Score (4 차원 0-10) — score<6 면 Socratic Q&A 3-5문항
Phase 2: Sprint Plan (.simonk/plan.md, trivial 작업은 skip)
Phase 3: Parallel Task tool delegation (general-purpose / Explore / Plan)
Phase 4: Verification (validate_skill.py, wiki-lint, bash -n, 등 작업별)
Phase 5: Persistence (commit + push, Full Auto 모든 repo, PR 자동 X)
Phase 6: Final Report (구조화된 요약)
```

전체 protocol: `skills-src/simonk/SKILL.md` + `skills-src/simonk/references/orchestration-protocol.md`.

### Auto-push 정책: **Full Auto**

사용자 명시 확인 없이 모든 repo (private + public) 자동 push. 단 (1) PR 생성·머지 자동 X, (2) 파괴적 작업 (`rm -rf`, force push, DB drop) STOP, (3) .env / credentials 노출 STOP.

### Entry point 영속화

`scripts/install-simonk-profile.ps1` 가 PowerShell profile 에 `simonk.ps1` dot-source 박음 (idempotent). `SIMONK_PROJECT_DIR=E:\Coding Infra` 환경변수 user-scope 영속 설정.

### 통합 외부 reference

- **OMC (`external/oh-my-claudecode/`)**: 정식 Claude Code plugin install 시 (`/plugin marketplace add Yeachan-Heo/oh-my-claudecode`) Team Mode + 19 agents + 32 skills 활성. simonk 가 더 강력한 multi-agent 필요시 권장.
- **OMO (`external/oh-my-openagent/`)**: model-agnostic 작업 시 reference (OpenCode 환경 위주, Claude Code 호환).
- **OpenHarness (`external/OpenHarness/`)**: Phase 6 폐쇄망 운영 시 (Python 표준 라이브러리, `pip install openharness-ai` 또는 `omc` npm CLI 이미 설치됨 - v4.14.1).
- **anthropics/skills**: 공식 카탈로그, cherry-pick vendoring 가능.

### Claude Code Native Team Mode 활성

`~/.claude/settings.json` 에 `"env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" }` 자동 박힘 (`scripts/install-simonk-profile.ps1` 의 사이드 효과). OMC 정식 install 후 `/team N:role "task"` 사용 가능.

### Windows 제약

- `omc team` CLI mode (tmux 워커) 는 `winget install psmux` 필요 (선택사항).
- `simonK <task>` 본체는 tmux 없이 작동.
