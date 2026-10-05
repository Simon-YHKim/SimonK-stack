# CLAUDE.md — Gstack-Ultraplan-Superpowers (simon-stack)

Claude Code reads this file at session start. This is a **skill development repo** — this branch has 137 `skills-src/` skills plus 4 development skills (141 source/development skills). The separately assembled five-plugin v23 candidate has 182 skills; neither count proves what is installed in a user profile. You are not building an app; you are curating a skill library.

## 🎯 작업 맥락

이 레포의 주 작업:
- **Skill 작성·수정·검증** (`skills-src/<name>/SKILL.md` 또는 `.claude/skills/<name>/SKILL.md`)
- **Hook·script 개선** (`.claude/hooks/`, `scripts/`)
- **README·docs 유지보수**
- **Instincts seed 갱신** (`.claude/instincts/`)

앱 코드는 한 군데뿐입니다 — `apps/ai-usage-widget/`(2026-09-20 통합, 아래 "apps/" 절). 그 밖에는 141개 소스·개발 스킬과 별도 5플러그인 후보를 관리하며, 다른 프로젝트에는 검증된 배포 절차로 스킬을 공급하는 것이 목표입니다.

## 📦 apps/ — 이 레포에 같이 사는 앱

- `apps/ai-usage-widget/` = Windows 작업 표시줄 AI 사용량 위젯(Electron). **자체 규칙이 우선**: 그 폴더의 `CLAUDE.md` 고정 읽기 목록(`CLAUDE.md` → `DECISIONS.md` → `STATE.md` → `docs/HANDOFF.md`)을 먼저 읽고, 검증은 그 폴더에서 `pnpm verify`(typecheck + lint + test) 종료코드로 판정한다. 아래 skill 검증 도구는 이 폴더에 적용되지 않는다.
- 설치·갱신·제거는 `skills-src/ai-usage-widget-install`이 한다(소스에서 빌드, 검증 통과가 설치 조건).
- 이력은 `git subtree`로 들어왔다. 이 폴더의 커밋은 이 레포에서 바로 한다(별도 원격 없음).
- 타사 로고는 MIT 범위 밖이다 — `NOTICE`의 Trademarks 절.

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

# SessionStart hook 수동 실행 (D-87 이후 읽기 전용: 안내 한 줄만 출력, 쓰기·git·네트워크 없음)
CLAUDE_PROJECT_DIR=$PWD bash .claude/hooks/session-start.sh

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
skills-src/                    ← 배포용 skill 소스 (128개, Claude Code 미로딩)
├── app-dev-orchestrator/
├── simon-tdd/
├── ... (배포 대상 skill)

.claude/
├── hooks/session-start.sh   ← 읽기 전용 안내 (D-87, 아무것도 쓰지 않음)
├── settings.json             ← Hook + Skill permission
├── instincts/                ← 4 seed md (학습 누적)
└── skills/                   ← 개발용 skill (4개만, Claude Code 로딩)
    ├── commit/               ← 커밋 워크플로
    ├── review/               ← 코드 리뷰
    ├── skill-gen-agent/      ← validator + test harness (vendored)
    └── context-guardian/     ← 세션 보호

docs/                          ← INSTALL(설치·배포 기록) / HANDOFF / 은퇴 안내(MORNING-START, USING-IN-OTHER-REPOS)
scripts/                       ← 빌드·검증 도구, windows/update-local.ps1, install.sh(--offline-package 전용)
templates/                     ← CLAUDE.md (global 템플릿)
_archive/                      ← 은퇴 경로 보관 (D-87): 레거시 루트 플러그인 0.1.0, 옛 git clone 설치 스크립트
README.md
CHANGELOG.md                   ← Keep a Changelog
LICENSE                        ← MIT + upstream credits
```

> **왜 분리?** `.claude/skills/` 에 skill 이 많으면 매 tool call 마다 모든 description 이
> system-reminder 로 주입되어 토큰이 폭발한다. `skills-src/` 는 Claude Code 가 무시하므로
> 개발 중 토큰 사용량이 극적으로 줄어든다. 배포는 `skills-src/` 를 입력으로 한 다섯 플러그인 빌드가,
> 이 PC flat 설치는 `scripts/windows/update-local.ps1` 이 맡는다 (D-87 이후 hook 은 아무것도 복사하지 않음).

## 🚫 금기 (건드리면 안 되는 곳)

- **`~/.claude/skills/gstack/` (홈 설치본)** — upstream (garrytan/gstack) 에서 clone. 약 12 MB / 450 파일. **절대 직접 수정하거나 Read 로 스캔 금지.** (레포 내 `.claude/skills/gstack/` 은 존재하지 않음 — 홈 설치본 기준)
- **`~/.claude/skills/gstack/node_modules/`** — bun 이 관리
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
  - 보통 160-280 자를 목표로 하되 필요한 선택 경계는 보존한다. 최소 글자 수를 채우려고 늘리지 않는다.
  - 첫 문장에 고유 목적·트리거, 이어서 산출물과 중요한 제외 조건을 둔다. 절차·예시·모델 목록은 본문으로 유지한다.
  - 설명 축약은 본문·권한·비용 가드 변경이 아니다. 중복 노출은 동일 패키지 확인 후 경로별 비활성화하고 파일은 보존한다.
- **Commit**: Conventional Commits (`feat(skills):`, `fix(hook):`, `docs(readme):`, `chore:`, `test:`)
- **Skill 이름**: kebab-case, ≤ 64 자, `claude`/`anthropic` 예약어 금지
- **SKILL.md 본문**: < 500 줄 (400 에서 warning). 넘으면 `references/*.md` 로 분리 + TOC

<!-- context-guardian-rules:v1 -->
## Context Guardian Rules (auto-maintained)

SessionStart hook 은 D-87(2026-10-05)부터 이 블록을 확인하거나 재삽입하지 않습니다. 블록을 고치거나 되살릴 때는 이 파일을 직접 편집합니다.

### 작업 범위 제한
- 한 세션에서 수정 파일 **최대 5 개**
- 한 번에 하나의 skill / hook / 문서 단위로만 작업
- 작업 완료 즉시 `git commit` 후 세션 종료 권고

### 파일 읽기 제한
- **`~/.claude/skills/gstack/` (홈 설치본) 읽기 금지** (12 MB, 450 files)
- `.claude.bak-*/`, `/tmp/simon-stack-*.log` 읽기 금지
- 1000 줄+ 파일은 Read offset+limit 으로 부분 읽기
- `node_modules/`, `.next/`, `dist/`, `.git/` 목적 없는 스캔 금지

### 작업 요청 방식
- 광범위 요청 ("전체 skill 개선") → 작은 단위로 분해 후 사용자 확인
- Plan 모드로 먼저 계획 수립 → 승인 후 실행
- **이 레포 특이 사항**: 활성화된 스킬 description 이 컨텍스트에 많이 노출되면 빠르게 쌓일 수 있음. 초기 목록 축약은 본문 손실과 다르며, 설치 수는 현재 호스트에서 확인한다. 따라서:
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
- **`context-guardian`** — 이 파일의 Context Guardian 블록 규칙의 source (D-87 이후 세션 시작 자동 복구 없음)
- **`commit`** — Conventional Commits 준수
- **`review`** — PR 사전 리뷰
- **`simon-tdd`** — 새 script/feature 추가 시 RED-GREEN-REFACTOR
- **`/ship`** (Gstack) — VERSION + CHANGELOG + push + PR
- **`simon-handoff`** — 세션 끝 핸드오프 (docs/HANDOFF.md prepend + PR auto-merge to main). 다음 세션이 `git pull` 한 번에 복원
- **`perspectives`** — 세션 blind-spot 감사 (Core 5 stakeholder + 세션 특화). perspectives.md 누적, SessionStart hook 이 다음 세션에 자동 알림

## 🧠 Instincts (auto-loaded)

`~/.claude/instincts/` 4 개 파일 참조:
- `mistakes-learned.md` — Claude 실수 누적 (grep -c exit 1, Plan 파일 시크릿 substring 등)
- `project-patterns.md` — 프로젝트별 관용
- `korean-context.md` — 한국 API 특이사항
- `tool-quirks.md` — CLI·하네스 함정

실수 지적 받으면 즉시 `simon-instincts` 로 append.

## 📖 Wiki 참고 (필수)

**SimonK Stack 의 모든 작업은 SimonKWiki 를 _먼저_ 참고합니다.**

> **2026-05-23 통합 메모**: 로컬 vault 경로 = `SimonKWiki` (단일 정본). GitHub repo 도 [`Simon-YHKim/SimonKWiki`](https://github.com/Simon-YHKim/SimonKWiki) **(PRIVATE, renamed from Simon-LLM-Wiki)** 로 이름 일치. 훅 3개 (`session-start.sh`/`user-prompt-submit.sh`/`stop.sh`)가 SimonKWiki·Simon-LLM-Wiki(legacy) 둘 다 자동 감지. wiki/ 콘텐츠는 `SimonKWiki/wiki/protocols/llm-wiki/` 하위에 위치.

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
bash skills-src/llm-wiki-builder/scripts/log-append.sh \
  refactor "<요약>" "- Updated: <pages>"
git add . && git commit -m "session: <요약>" && git push
```

자세한 절차: wiki 의 `concepts/session-meta-analysis.md`.

## 🔄 Stack 자체 업데이트

SessionStart hook 은 D-87(2026-10-05)부터 읽기 전용입니다. 업데이트 감지·auto-pull 을 하지 않습니다.
- **사용자**: 마켓플레이스 다섯 플러그인 — `claude plugin marketplace update simonk-stack` 뒤 `claude plugin update <id>@simonk-stack` (README 7절)
- **이 PC (flat 설치)**: `pwsh -File scripts/windows/update-local.ps1` (미리보기, `-Apply` 로 설치)

## 🔁 Hook 자동화 매트릭스

UserPromptSubmit·Stop hook 이 사용자 명시 없이 wiki 누적·반영을 _자동_ 으로 처리합니다. SessionStart 는 D-87 이후 읽기 전용 안내만 합니다.

| Hook | 시점 | 동작 |
|---|---|---|
| **SessionStart** | 세션 시작 | 읽기 전용 안내 (D-87): `perspectives.md` 가 있으면 알림 + 설치·업데이트 경로 한 줄. git·네트워크·파일 쓰기 없음 |
| **UserPromptSubmit** | 매 사용자 발화 전 | wiki 의 5초 인덱스 + 최근 3 log + M/T totals 를 _system context_ 에 inject. LLM 자발성 보강 — _사용자가 언급 안 해도_ wiki 인지 상태 |
| **Stop** | LLM 응답 종료 시 | wiki/instincts repo 가 dirty 면 자동 commit + push (branch=main + md/json 변경 위주 필터). LLM 이 _수정만 하면 영속화_ 자동 |

**효과**: A (Stop hook) 가 _영속화 누락_ 을 막고, C (UserPromptSubmit hook) 가 _LLM 의 wiki 인지_ 를 매 발화 강제. 사용자 발화에 "wiki", "오답노트" 같은 키워드가 없어도 _LLM 이 스스로_ M-xxx / T-xxx append 할 가능성 ↑.

**비용**:
- UserPromptSubmit: 매 발화 ~300-500 토큰 (인덱스 + 최근 log 만 inject — 컴팩트하게 유지)
- Stop: 0 토큰 (bash 만)

**Opt-out**: `.claude/settings.json` 에서 해당 hook 블록 제거.

## 🚀 세션 시작 정책

**SessionStart hook 은 D-87(2026-10-05)부터 읽기 전용입니다.** `.claude/hooks/session-start.sh` 는 git·네트워크 명령을 실행하지 않고 아무것도 쓰지 않습니다. `perspectives.md` 가 있으면 알리고, 설치 경로를 한 줄로 안내할 뿐입니다. 예전의 bootstrap(스킬 복사·instincts seed·CLAUDE.md 생성), SimonK-stack·wiki auto-pull, `[UPGRADE_AVAILABLE]` 박스, `~/.claude/.update-pending` fallback 은 모두 없어졌으므로 세션 첫 동작으로 업데이트 확인을 실행하지 않습니다. 업데이트 경로는 위 "Stack 자체 업데이트" 절(사용자: 마켓플레이스, 이 PC: `update-local.ps1`)입니다.

### 사용자가 업데이트를 요청하면

LLM 이 직접 처리할 것:
- **사용자가 "최신화" / "stack update" 같은 holistic 요청** → `/stack-update` 호출
  - SimonK-stack 본체 + Wiki + gstack + 5 vendored stacks + skill 재설치를 한 번에 처리
  - 각 단계는 단일 entry point 의 sibling skill (예: `/gstack-upgrade`, `/omc-upgrade`) 위임
- **gstack 만** 업데이트 명시 요청 → `/gstack-upgrade` (gstack 단독)
  - install type 자동 감지 (global-git / local-git / vendored)
  - gstack 본체 + 로컬 vendored gstack 카피 sync
  - ⚠️ **이 스킬은 SimonK-stack 자체는 pull 안 함** (gstack 의 책임 도메인이 아님). D-87 이후 SessionStart auto-pull 도 없다.
  - `GSTACK_AUTO_UPGRADE=1` 또는 `gstack-config set auto_upgrade true` 면 사용자 확인 없이 진행
- **특정 외부 stack** 만 업데이트 요청 → 해당 sibling skill 호출
  - `/omc-upgrade` (oh-my-claudecode), `/omo-upgrade` (oh-my-openagent)
  - `/openharness-upgrade`, `/opencowork-upgrade`, `/designmd-upgrade`

업데이트 요청이 없으면 별다른 보고 없이 사용자 요청을 바로 처리한다. 매번 "최신입니다" 같은 narration 금지 (T-003 — 토큰 효율).

---

## /vibe main entry and simonk compatibility

/vibe owns skill discovery, model/effort routing, account/quota evidence, budget,
the registered DAG and execution state. simonk contributes a six-phase sprint
procedure in that same host, not a second coordinator.

### Entry points

```text
/vibe <outcome>     # Main entry in an existing LLM session
/simonK <task>      # Sprint procedure under the same /vibe contract
```

The case-insensitive PowerShell command is different: it accepts prepared JSON
for **offline planning only**, never a text prompt or an interactive LLM launch.

```powershell
$ErrorActionPreference = 'Stop'  # Batch callers must also catch binding errors.
simonK -RequestPath request.json -RuntimePath runtime.json
exit $LASTEXITCODE              # Batch scripts only, not interactive shells.
```

Use the schemas and execution gates in
`skills-src/vibe/references/orchestration.md`. A plan is neither a reservation
nor proof of dispatch. Reuse the parent's run, grant, DB, ancestry and reviews.
Additional spending defaults to $0; unknown billing/quota is not free.
GUI-only work uses vibe-bot through the same owner; Bot is no quota workaround.

### Six phases and Git boundary

Clarify consequential gaps → one dependency/review plan → authorized ready work
→ evidence-based verification/recovery → scoped persistence → honest report.
See `skills-src/simonk/SKILL.md` and its orchestration protocol for the details.

Do not fan out raw Task/terminal/provider calls, stage all changes, disable
signing/hooks or push unrelated repositories. Commit only the intended changes
after tests/review; push only the confirmed repository/branch within the user's
authorization. PR, merge, deployment, destructive, credential and spending gates
remain in force. Installed parity and live model tests are separate evidence.

### Optional PowerShell profile migration

Use PowerShell 7 and an explicitly chosen persistent **ordinary clone** whose
entry script and central planner match this reviewed source. A linked worktree,
old primary checkout or automatic fallback is not an installation target.

```powershell
# Default: preview only. No directory, profile, backup or environment writes.
pwsh -NoProfile -NonInteractive -File scripts/install-simonk-profile.ps1 -RepoRoot 'E:/persistent/SimonK-stack'

# After inspecting the target and preview, explicitly apply:
pwsh -NoProfile -NonInteractive -File scripts/install-simonk-profile.ps1 -RepoRoot 'E:/persistent/SimonK-stack' -Apply
```

An optional absolute `-ProfilePath` selects a specific .ps1 profile; otherwise
the current PowerShell's CurrentUserAllHosts path is used. The installer only
replaces one exact owned v1/v2 block, preserves surrounding bytes and supported
UTF-8/UTF-16 encoding, and returns a unique byte-preserving backup on replacement.
Malformed/edited/duplicate markers or unmanaged simonk.ps1 references fail closed.
The marker and statement must be actual top-level code, not a here-string,
block comment or nested function that merely contains an installer example.

A v2 profile holds a read-only file handle (no write/delete sharing) from hash
verification through dot-source, and loads the function-definition wrapper only
when its pinned SHA-256 matches. Missing/changed/unreadable files give a warning, not
startup execution. The installer does not dot-source anything itself, change
SIMONK_PROJECT_DIR, authenticate gcloud, enable Team Mode or alter settings.
Existing environment values are left intact; removing unrelated bootstrap
consumers belongs to a separate migration.

Close other editors/installers during apply. The final hash recheck and atomic
replacement preserve a backup but are not a universal cross-editor lock.
For rollback, inspect the returned backup and current profile first, then restore
only with the applicable overwrite authorization; no automatic rollback occurs.
Startup pinning is not full planner-package integrity or a guarantee for already
open sessions. Full release/installation checksum parity remains a separate gate.

Offline validation:
```text
python -B -m unittest discover -s scripts/tests -p test_install_simonk_profile.py
python -B -m unittest discover -s scripts/tests -p test_simonk_entrypoint.py
```

### 통합 외부 reference (Sprint v22-EXT: vendored, 2026-05-25)

3 외부 repo 가 **`external/` 안 vendor 됨** (shallow clone + `.git` 제거). SimonK-stack clone 시 즉시 사용 가능, upstream sync 는 수동 (별도 sprint). `.claudeignore` 로 토큰 보호 (110 MB / 8500 files).

- **OMC (`external/oh-my-claudecode/`, 49 MB)** — upstream: [Yeachan-Heo/oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode). Team Mode + 19 agents + 32 skills. simonk 가 더 강력한 multi-agent 필요시 trigger. Vendored 후에도 정식 plugin install 권장 (`/plugin marketplace add Yeachan-Heo/oh-my-claudecode`) — vendor 는 reference + offline fallback.
- **OMO (`external/oh-my-openagent/`, 48 MB)** — upstream: [code-yeongyu/oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) (formerly oh-my-opencode). Model-agnostic agent orchestrator (Claude/GPT/Kimi/GLM/Gemini/Minimax 단일 interface). OpenCode 환경 위주, Claude Code 호환 일부.
- **OpenHarness (`external/OpenHarness/`, 13 MB)** — upstream: [HKUDS/OpenHarness](https://github.com/HKUDS/OpenHarness). Open Agent Harness + 내장 personal agent (Ohmo). Tool-use, skills, memory, multi-agent coordination 핵심 인프라. Phase 6 폐쇄망 운영 또는 simon-ohmo skill 통합 시 활용. `pip install openharness-ai` 보조.
- **anthropics/skills**: 공식 카탈로그, cherry-pick vendoring 가능 (별도).

**Wiki 연동**: [[wiki/entities/tools/omc]] · [[wiki/entities/tools/omo]] · [[wiki/entities/tools/openharness]] (SimonKWiki PRIVATE) 에 활성화·사용법·simonK 통합 시나리오 명시.

### Claude Code Native Team Mode 활성

The profile installer does not enable experimental teams or edit Claude settings.
External team tooling is a separately authorized setup; availability and supported
controls must be checked before use, not inferred from a vendored directory.

### Windows 제약

- `omc team` CLI mode (tmux 워커) 는 `winget install psmux` 필요 (선택사항).
- The offline PowerShell planning entry does not require tmux or a provider CLI.

## graphify

지식 그래프가 `graphify-out/`에 생성돼 있다 (2026-06-11 재생성, graphify 0.8.36, gitignored).

- **코드베이스/문서 구조 질문** → grep 전에 `graphify query "<질문>"` 먼저 (scoped subgraph, 토큰 절감).
- **광역 아키텍처 맥락** → `graphify-out/GRAPH_REPORT.md` (god nodes + communities).
- **파일 변경 후** → `graphify update .` (AST 기반, LLM/토큰 비용 0).
- 시각화: `graphify-out/graph.html` (D3 force-directed).
- 제외 규칙: `.graphifyignore` (external/ vendored 레포·site/ 제외).
- PreToolUse hook(`.claude/settings.json`)이 grep류 명령 시 graphify 사용을 자동 권장 — `graphify-out/graph.json` 존재 시에만 발화.
