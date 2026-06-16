---
name: commit
description: "Use when the user asks to commit changes, stage files, or create a git commit—triggers include \"commit\", \"커밋\", \"stage and commit\", \"git commit\", \"make a commit\", \"commit this\". Produces a Conventional Commits-style commit following the repo's log style: type(scope): subject with optional body explaining the why."
version: 1.0.0
author: general-dev
---

# Commit Skill

Create high-quality git commits that follow the Conventional Commits specification.

## Workflow

1. **Inspect state** — Run these in parallel:
   - `git status` (do NOT use `-uall`)
   - `git diff` (staged + unstaged)
   - `git log --oneline -10` (to match repo style)

2. **Analyze changes** — Determine the commit type:
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation only
   - `refactor:` code change that neither fixes a bug nor adds a feature
   - `test:` adding/updating tests
   - `chore:` build process, tooling, dependencies
   - `perf:` performance improvement
   - `style:` formatting, whitespace

3. **Draft message** — Format:
   ```
   <type>(<scope>): <short summary in imperative mood>

   <optional body explaining the why, not the what>
   ```
   - Keep subject line under 72 characters
   - Use imperative mood ("add" not "added")
   - Focus on **why**, not **what** (the diff already shows what)

4. **Stage and commit**:
   - Stage specific files by name (avoid `git add -A` to prevent committing secrets)
   - Never commit `.env`, credentials, or large binaries
   - Use a HEREDOC for multi-line messages

5. **Verify** — Run `git status` after commit to confirm success.

## Safety Rules

- NEVER use `--no-verify` to skip hooks
- NEVER amend commits unless explicitly requested
- If a pre-commit hook fails, fix the underlying issue and create a NEW commit
- Do NOT push unless explicitly asked

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
