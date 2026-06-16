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
delete prior sections. If absent, create with just the new block.

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

The trailing `---` separates this block from prior blocks. The oldest
block can be renamed `## Sprint 0 (historic)` etc. if the file grows
long.

### Step 3 — Merge it all the way through

Commit + push + PR + auto-merge in a single uninterrupted sequence. The
PR description embeds the new "Latest" block inline so the handoff is
readable from the PR URL even before merge completes (fallback path).

```bash
HANDOFF_BRANCH="handoff/$(date +%Y%m%d-%H%M)"
git checkout -b "$HANDOFF_BRANCH"
git add docs/HANDOFF.md
git commit -m "docs: handoff — <one-line summary>"
git push -u origin "$HANDOFF_BRANCH"
```

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
- Prior `## Latest — <date>` blocks are valuable history; renaming the
  oldest to `## Sprint 0 (historic)` after ~10 sessions keeps the file
  scannable while preserving accumulation.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
