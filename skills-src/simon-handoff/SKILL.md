---
name: simon-handoff
description: >
  Use when the user wants to hand off the current session so a fresh session
  can resume — triggers "/simon-handoff", "/handoff", "핸드오프 해줘",
  "인수인계", "다음 세션 준비", "이 작업 인수인계", "session handoff".
  Produces a git-persistent, main-merged docs/HANDOFF.md plus the exact
  shell command the next session should paste to wake up at full context.
  Different from /checkpoint and /context-save (those are ephemeral in
  ~/.gstack/...) and from /document-release (README/CHANGELOG, not handoff).
  Two invariants the skill MUST satisfy: (1) file lives in the repo on
  disk (no /root, /tmp, ~/.gstack paths), (2) it gets merged to main
  (commit+push alone is not enough — the next session's `git pull origin
  main` won't see it until merge). Includes fallback URLs (PR URL, raw
  URL, branch checkout) for the case where merge can't complete.
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# /simon-handoff

Create a git-persistent, main-merged session handoff so a fresh session
can resume with full context from `docs/HANDOFF.md`.

## Why this skill exists

Most session-save tools (`/checkpoint`, `/context-save`) write to
`~/.gstack/projects/.../checkpoints/<file>.md` — that path is ephemeral
in containerized Claude Code environments and the next session never
sees it. Commit-and-push alone also fails: the next session's
`git pull origin main` won't pick up an unmerged branch.

This skill closes both gaps by enforcing two invariants.

## The two invariants (non-negotiable)

1. **세션 간 영속** — the handoff lives at `docs/HANDOFF.md` inside the
   git repo. Never `/root/.gstack/...`, never `/tmp/...`, never browser
   localStorage.
2. **다른 세션에서 즉시 접근** — the commit reaches `origin/main`. PR
   creation + push to a feature branch is not enough.

If either fails, the handoff is useless.

## ⛔ 실행 전 게이트 — 생략하지 않는다

**이 스킬은 코드까지 main 에 머지한다.** 그래서 `/ship` 의 정지 조건을 우회할 수 있다.
호출 전에 셋을 점검하고, 하나라도 걸리면 **실행하지 않고** HANDOFF 최신 블록만 출력한다.

```bash
git status --porcelain | head -40          # ① 지금 무엇이 변경돼 있나
gh pr checks --watch=false 2>/dev/null     # ② CI 초록인가
```

③ 정지 조건 해당 여부를 눈으로 판정한다 — **시크릿 · DB 마이그레이션 · 스키마 변경 ·
파일 삭제 · 대량 리네임 · 롤백 미확인 배포 · 과금 트리거.**

통과했으면 **머지 범위를 먼저 보고**하고 진행한다. 이 게이트는 권한 모드와 무관하다
(`bypassPermissions` 여도 내가 지킨다 — Simon 지침 §3).

## ⚠ 워크트리가 공유일 수 있다 — `git checkout -b` 를 함부로 쓰지 않는다

2ndB 같은 저장소에서는 **한 워크트리를 여러 세션이 동시에 쓴다.** 그 자리에서
`git checkout -b` 하면 남의 미커밋 작업을 통째로 끌고 브랜치를 갈아탄다.
먼저 공유 여부를 본다:

```bash
git rev-parse --git-common-dir            # .git 이 아니라 ../../.git 이면 워크트리다
git status --porcelain | wc -l            # 내가 만들지 않은 변경이 잔뜩이면 공유다
```

공유면 **전용 워크트리를 새로 만들어** 거기서 작업한다. 저장소 루트 기준:

```bash
git -C <repo-root> worktree add .worktrees/handoff-<YYYYMMDD> \
    -b handoff/<YYYYMMDD-HHMM> origin/main
```

- 워크트리는 **반드시** `.worktrees/` 아래에 만든다(형제 폴더 금지).
- `git worktree remove --force` 를 쓰지 않는다 — 정션을 따라가 공유
  `node_modules` 를 지운다. 정션을 먼저 끊는다.
- 공유 워크트리에서는 `git add -A` · 맨 `stash`/`pop` · `checkout` · `restore` ·
  `reset` 을 쓰지 않는다. **경로를 지정한 `add` 만** 쓴다.

## Execution sequence

### Step 1 — Collect session state

```bash
git fetch --quiet origin main
CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo HEAD)
MAIN_SHA=$(git rev-parse origin/main)
BEHIND=$(git rev-list HEAD..origin/main --count 2>/dev/null || echo 0)
AHEAD=$(git rev-list origin/main..HEAD --count 2>/dev/null || echo 0)
DIRTY=$(git status --porcelain | wc -l | tr -d ' ')
LATEST_COMMITS=$(git log origin/main --oneline -5)
```

Also collect, from the conversation context:

- PRs merged during this session (titles + numbers).
- Files changed (rolled up by area, not raw paths).
- Active infrastructure state (Supabase project ID, deployed edge function
  version, env vars location — wherever applies).
- Next-work queue: anything in the last PR's "follow-up" section + items
  the user explicitly deferred.
- Permanent policies the user articulated this session (e.g. "always
  branch from main, never rebase", "auto-merge after green CI", "wiki
  append on session end").

### Step 2 — Prepend to docs/HANDOFF.md

If the file exists, **prepend** the new "Latest" block at the top — never
delete prior sections. **Before prepending, demote the previous top block's
`## Latest — <date>` heading to a plain `## <date>` header** (strip the
`Latest — ` prefix only — leave the block's body untouched). Exactly one
section — the newest — ever carries the `## Latest` marker. Skip this and the
marker accumulates one-per-session until the log's "newest on top" rule
silently breaks (real defect found 2026-07-03: 31 `## Latest` markers, recency
inverted). If absent, create with just the new block.

⚠ **기간 분할 뒤에는 "맨 위"가 첫 H2 가 아니다.** 파일 머리에 기간 파일 색인 절
(`## 이 로그는 기간으로 쪼개져 있다`)이 있고, 그건 파일 **지도**라 계속 맨 위여야 한다.
첫 H2 앞에 끼우면 색인이 새 블록 밑으로 밀린다(2026-09-13 에 실제로 그렇게 됐고 되돌렸다).
새 블록은 **첫 `## <날짜>` 블록 앞**에 넣는다. 최종 순서:

```
# 제목 + 머리말
## 이 로그는 기간으로 쪼개져 있다      ← 색인. 항상 맨 위
## Latest — <오늘>                     ← 새 블록
## <직전 날짜>                          ← 강등된 것
```

Template:

```markdown
## Latest — YYYY-MM-DD / <one-line summary>

### 어디까지 왔나
- main HEAD: `<sha>`
- 이번 세션 머지된 PR: #<n> <title>, #<n> <title>
- 테스트 상태: <X/Y green> or "no CI configured"
- working tree: clean / dirty (N files)

### 활성 인프라
- <external service ID + version + where env vars live>

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | <first> | small/medium/large | ⭐ <why recommended> |
| B | <second> | ... | ... |

### 적용 중인 정책 (영구)
1. <CI auto-merge etc — user-explicit policies>
2. <branch reset patterns, anti-mistakes>

### 핵심 파일 위치
```
<path>    <role>
```

### 검증
```bash
<actual project verification command — npm run verify, pytest, etc>
```

### 다음 세션 시작하는 법
```bash
git fetch origin main && git pull
cat docs/HANDOFF.md
# A 작업부터 시작
```

---
```

The trailing `---` separates this block from prior blocks.

### Step 2-B — 100KB 를 넘으면 **굴린다**. 요약하지 않는다

`docs/HANDOFF.md` 는 **활성 창**이고, 밀려난 블록은 기간 파일에 원문 그대로 남는다.
Simon 지침 §0-1: *"100KB 에 닿으면 요약하지 않고 기간으로 쪼갠다. 압축은 선택지가 아니다."*

```
docs/HANDOFF.md                      활성 창 (예산 80KB · 상한 100KB)
docs/handoff/HANDOFF-YYYY-MM.md      월 보관
docs/handoff/HANDOFF-YYYY-MM-pN.md   월이 넘칠 때의 부분. **p1 이 가장 오래된 쪽**
```

⚠ **왜 반기(`YYYYHn`)가 아닌가.** 2026-09-13 실측에서 2026-07·08·09 가 각각
226KB·307KB·110KB 였다. 반기로 묶으면 한 파일이 640KB 가 되어 **상한을 지키라는 규칙을
지키려다 상한을 어긴다.** 상한을 만족하는 가장 굵은 기간을 쓴다 — 지금은 월, 월도
넘치면 부분. 예시가 아니라 목적을 따른다.

⚠ **부분 번호는 오래된 쪽이 1.** 굴러 들어오는 블록은 보관된 어떤 블록보다도 새로우니
**번호가 가장 큰 부분의 맨 위**로 들어간다. 최신 쪽부터 번호를 매기면 굴릴 때마다
전부 개명해야 한다.

**절차** — prepend 후 활성 파일이 100KB 를 넘으면:

1. 가장 오래된 H2 블록부터, 활성 파일이 **80KB 아래**로 내려갈 때까지 떼어낸다.
2. 뗀 블록을 그 달의 보관 파일(부분이 있으면 번호가 가장 큰 것) **맨 위**에 얹는다.
   그 파일이 90KB 를 넘으면 번호 하나 큰 새 부분을 만든다.
3. 활성 파일 머리의 색인 표(기간·파일·블록 수·크기)를 갱신한다.
4. **아래 Step 2-C 검사를 돌린다.** 블록 수가 보존되지 않으면 되돌린다.

**한 글자도 요약하지 않는다.** 블록을 합치지도, 지우지도, 재정렬하지도 않는다 —
이 로그에는 날짜 역순이 아닌 자리가 실제로 있고 그것도 기록이다.

### Step 2-C — 검사. 규칙만 적어두면 안 지켜진다

2026-09-06 부터 `## Latest` 마커가 **최신이 아닌 블록**에 붙어 있었다. 그 위에
2026-09-13 블록이 네 개 있었는데 아무도 못 봤다. 강등 규칙은 처음부터 적혀 있었다 —
**없던 것은 검사였다.**

```bash
# ① Latest 마커는 활성 파일에 정확히 1개, 보관본에 0개
grep -c '^## Latest' docs/HANDOFF.md                       # 1 이어야 한다
grep -rc '^## Latest' docs/handoff/HANDOFF-20*.md          # 전부 0

# ② 그 1개가 정말 맨 위 블록인가
grep -n '^## ' docs/HANDOFF.md | head -2

# ③ 모든 파일이 상한 아래인가
find docs/HANDOFF.md docs/handoff -name 'HANDOFF-*.md' -size +100k

# ④ 굴림 전후로 블록 수가 보존됐나 (굴렸을 때만)
git show HEAD:docs/HANDOFF.md | grep -c '^## '             # before
cat docs/HANDOFF.md docs/handoff/HANDOFF-20*.md | grep -c '^## '   # after (색인 H2 +1)
```

④ 는 **개수 보존**을 본다. 유일성으로 검사하지 말 것 — 이 파일에는 원본부터 완전히
같은 본문이 두 번 있는 블록이 있어서, 유일성 검사는 원본의 사실을 결함으로 읽는다.

⑤ **색인이 여전히 맨 위인가** — `grep -n '^## ' docs/HANDOFF.md | head -3` 의 첫 줄이
색인 절이어야 하고 둘째가 `## Latest` 여야 한다.

⚠ **검사 결과를 파이프 뒤 명령의 종료코드로 읽지 말 것.** `cmd | head -3 && echo OK` 는
`head` 가 성공하면 언제나 OK 를 찍는다 — 실패가 초록으로 보인다(2026-09-13 에 밟았다).
종료코드가 필요하면 파이프 없이 따로 받는다.

### Step 3 — Merge it all the way through

Commit + push + PR + auto-merge in a single uninterrupted sequence. The
PR description embeds the new "Latest" block inline so the handoff is
readable from the PR URL even before merge completes (fallback path).

```bash
HANDOFF_BRANCH="handoff/$(date +%Y%m%d-%H%M)"

# 공유 워크트리면 checkout 하지 말고 전용 워크트리를 만든다 (위 ⚠ 절 참조)
git -C <repo-root> worktree add .worktrees/handoff-$(date +%Y%m%d) \
    -b "$HANDOFF_BRANCH" origin/main
cd <repo-root>/.worktrees/handoff-$(date +%Y%m%d)

# 경로를 지정해 add 한다. `git add -A` 금지 — 남의 변경을 빨아들인다
git add docs/HANDOFF.md docs/handoff/HANDOFF-20*.md
git commit -m "docs: handoff — <one-line summary>"
git push -u origin "$HANDOFF_BRANCH"
```

전용 체크아웃이고 내가 유일한 사용자임을 **확인했을 때만** `git checkout -b` 를 써도 된다.

Then create the PR. Two environment paths:

**Path A — local CLI with `gh` available**
```bash
gh pr create \
  --base main --head "$HANDOFF_BRANCH" \
  --title "docs: handoff $(date +%Y-%m-%d)" \
  --body-file /tmp/handoff_pr_body.md   # copy of the Latest block

gh pr merge --squash --auto             # waits for CI then merges
```

**Path B — remote Claude Code (no `gh`, use GitHub MCP)**
- `mcp__github__create_pull_request` with `base: main`, `head: $HANDOFF_BRANCH`, body = the Latest block.
- `mcp__github__pull_request_read` method=`get_status` to check CI. If
  `total_count: 0` (no CI workflows) or all checks pass, proceed.
- `mcp__github__merge_pull_request` with `merge_method: squash`.

In both paths: **wait for the merge to actually complete** before Step 4.
The user's pasted command in Step 4 only works once the merge lands on
`main`.

### Step 4 — Report the resume command to the user

Only after the merge SHA is on `origin/main`, send the user a single
copy-pasteable block:

```bash
git fetch origin main && git pull origin main && cat docs/HANDOFF.md
```

Plus the fallback URLs in case the next session can't `git pull` (e.g.,
fresh container without this repo cloned yet):

```
PR URL:  https://github.com/<owner>/<repo>/pull/<N>
Raw URL: https://raw.githubusercontent.com/<owner>/<repo>/<merge-sha>/docs/HANDOFF.md
Branch:  git fetch origin <branch> && git show origin/<branch>:docs/HANDOFF.md
```

### Step 5 — Fallback when merge cannot complete

Reasons merge may fail: branch protection blocks auto-merge, CI red, user
explicitly declines merge, or PR pre-conditions unmet. In any of those
cases the skill still has a valid handoff via two routes:

1. **PR body** — the Latest block is inlined in the PR description, so
   `mcp__github__pull_request_read` or `gh pr view` recovers it.
2. **Raw URL** — once any commit is pushed,
   `https://raw.githubusercontent.com/<owner>/<repo>/<sha>/docs/HANDOFF.md`
   is permanent and immutable.

Surface these to the user in priority order (PR URL → Raw URL → branch
checkout command), and clearly state the merge did not complete and why.

## Success criteria

The skill is only complete when **all four** are true:

1. `git show origin/main:docs/HANDOFF.md` first H2 starts with today's date.
2. CI on that commit is green (or repo has no CI workflows configured).
3. The copy-paste command shown to the user works in a fresh container.
4. At least two fallback routes (PR URL, raw URL, branch checkout)
   accompany the resume command.
5. **실행 전 게이트 3개를 실제로 돌렸고 머지 범위를 보고했다.**
6. **`## Latest` 가 활성 파일에 정확히 1개이고 그것이 맨 위 블록이다.**
7. **`docs/HANDOFF.md` 와 모든 `docs/handoff/HANDOFF-*.md` 가 100KB 미만이다.**
8. **굴렸다면 블록 수가 보존됐다**(Step 2-C ④). 요약·병합·삭제 0건.

If any of these is false, do not declare success.

## Anti-patterns (do NOT do)

- ❌ Writing to `/root/.gstack/projects/.../checkpoints/<file>.md` — ephemeral path.
- ❌ Writing to `/tmp/handoff.md` — ephemeral path.
- ❌ Updating `HANDOFF.md` but not committing — disappears with the container.
- ❌ Committing + pushing to a feature branch but not merging to main —
  next session's `git pull origin main` won't see it.
- ❌ Creating the PR and giving the user the resume command before merge
  lands — paste produces stale content.
- ❌ Using browser session/localStorage — different container has no access.
- ❌ **파일이 커졌다고 요약·압축하기.** §0-1 은 이 경우를 명시적으로 금지한다.
  기간으로 쪼개는 것만이 허용된 처분이다.
- ❌ **공유 워크트리에서 `git checkout -b` / `git add -A` / 맨 `git stash`.**
  다른 세션의 미커밋 작업을 끌고 가거나 삼킨다.
- ❌ **`## Latest` 를 강등하지 않고 prepend 하기.** 마커가 누적되거나(2026-07-03: 31개)
  최신이 아닌 블록에 남는다(2026-09-06 ~ 09-13). 규칙이 아니라 **검사**가 이걸 막는다.

## Related skills (explicit boundaries)

- `/checkpoint` (gstack): in-session temporary save, ephemeral OK. **Not a
  cross-session handoff.**
- `/context-save` (gstack): same as `/checkpoint`.
- `/document-release` (gstack): updates README / CHANGELOG / ARCHITECTURE
  post-ship. Different concern from handoff.
- `/session-context-export`, `/session-context-tracker`: in-session
  context tracking, not git-persistent.

This skill's exclusive responsibility: **git-persistent cross-session
handoff with merged main as the success gate**.

## Trigger phrases (matched by description block above)

- `/simon-handoff`, `/handoff`
- "핸드오프 해줘", "인수인계 해줘"
- "다음 세션 준비", "이 작업 인수인계"
- "session handoff", "prepare next session"

## Operational notes

- The handoff PR title pattern `docs: handoff YYYY-MM-DD` makes it easy
  to find prior handoffs via `gh pr list --search "docs: handoff"` or
  `mcp__github__list_pull_requests`.
- If the repo lacks `docs/`, create it. Don't reroute to a different
  path — `docs/HANDOFF.md` is the canonical, predictable location every
  future session can probe.
- Prior handoff blocks are valuable history — keep their bodies intact, but
  they carry a plain `## <date>` heading, **not** `## Latest`; only the single
  newest block is `## Latest` (it is demoted on each prepend — Step 2).
  Renaming the oldest to `## Sprint 0 (historic)` after ~10 sessions keeps the
  file scannable while preserving accumulation.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
