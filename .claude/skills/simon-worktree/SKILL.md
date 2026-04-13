---
name: simon-worktree
description: Sets up git worktree isolation so multiple Claude Code sessions can work on the same repo in parallel without conflicts. Use this skill whenever the user says things like "병렬 작업", "동시에 두 기능 개발", "parallel agents", "multiple Claude sessions", "worktree 만들어줘", "split work across branches", "run two tasks in parallel"—or before starting a second long-running task while another is already in progress. Prevents the classic "two sessions on the same branch" deadlock. Teaches naming convention (repo-feature dirs, feat/fix branches), .env handling (symlink or per-worktree copy), and cleanup (git worktree remove + branch delete).
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon
---

# Simon Worktree

Superpowers `using-git-worktrees` + Boris Cherny 병렬 세션 권고를 융합. 병렬 Claude 세션은 worktree 로 격리하지 않으면 동일 브랜치를 두 세션이 동시에 쓰면서 커밋 충돌·빌드 꼬임이 발생한다. 한 번이라도 겪으면 정리 비용이 격리 비용보다 훨씬 커진다.

## When to use

- 2개 이상의 기능을 동시에 개발
- Long-running 실험 branch 와 메인 작업 동시 진행
- PR 리뷰 받는 동안 다음 기능 시작
- Conductor / Claude Code web / IDE 멀티 세션
- `app-dev-orchestrator` 단계 12

## Workflow

### 1. Worktree 생성

```bash
# 메인 레포에서
git worktree add ../<repo-name>-<feature> -b feat/<feature>
cd ../<repo-name>-<feature>
```

네이밍 규칙:
- 디렉토리: `<repo>-<feature>` (예: `myapp-auth`, `myapp-billing`)
- 브랜치: `feat/<feature>` 또는 `fix/<issue>`

### 2. 독립 Claude 세션 배정

각 worktree 마다 **별도** Claude Code 세션:
- 메인 worktree → 세션 A (PR 리뷰·문서·핫픽스)
- `../myapp-auth` → 세션 B (auth 기능)
- `../myapp-billing` → 세션 C (billing 기능)

세션 간 파일 공유 금지. 각 세션은 자기 worktree 안에서만 작업.

### 3. 환경변수·의존성 처리

**`.env` 취급**:
- 실키 하드코딩 금지, 각 worktree 마다 `.env` 재복사
- 또는 심볼릭 링크: `ln -sf ../myapp/.env .env` (레포가 같은 부모 디렉토리일 때)
- `.env` 는 `.gitignore` 에 이미 들어있어야 한다 (새 worktree 에서도 재확인). 한 worktree 에만 커밋되면 전체 히스토리에 유출됨.
- 여러 worktree 에서 다른 DB 사용 시 `DATABASE_URL` 값 다르게

**`node_modules` / `dist`**:
- worktree 마다 `npm install` 재실행 (일반적)
- 또는 pnpm + `shared-workspace-lockfile` (고급)
- CI 캐시와는 별개

**DB 마이그레이션 충돌**:
- 두 worktree 가 동일 DB 에 마이그레이션 시 타임스탬프 prefix 충돌 주의
- 가능하면 worktree 마다 다른 로컬 DB 사용 (`supabase start --project-id feat-auth`)

### 4. 병렬 작업 원칙

- 메인 worktree 에는 **직접 commit 금지** (PR 만). 실수 방지
- 각 worktree 는 자기 브랜치만 커밋
- 공통 파일(예: `package.json`) 을 두 worktree 에서 동시 수정 → 머지 지옥. 한 번에 한 곳
- 세션 간 통신은 git (PR·커밋) 로만. 메신저로 직접 파일 전달 금지

### 5. 완료 후 정리

```bash
# 작업 완료·머지 후
cd /path/to/main-worktree
git worktree remove ../<repo>-<feature>
git branch -d feat/<feature>  # 로컬 정리
# 원격은 PR 머지 시 자동
```

**확인**:
```bash
git worktree list  # 고아 worktree 없는지
git worktree prune  # 수동 제거 후
```

### 6. 파괴적 작업 전 confirm

- `git worktree remove --force` → 미커밋 변경 손실. **사용자 확인 필수**
- 브랜치 삭제 전 push 여부 확인

## Checklist

- [ ] 병렬 작업 전 worktree 생성
- [ ] 각 worktree 에 독립 Claude 세션 배정
- [ ] 메인 worktree 에는 직접 커밋 안 함
- [ ] `.env` 가 모든 worktree 에서 `.gitignore` 에 있음
- [ ] 작업 완료 후 `git worktree remove` + 브랜치 정리
- [ ] `git worktree list` 로 고아 확인

## Anti-patterns

- ❌ 동일 브랜치를 두 Claude 세션에서 병렬 작업 — 커밋 충돌 지옥
- ❌ `.env` 를 worktree 마다 실키 하드코딩
- ❌ 메인 worktree 에 직접 `git commit` (PR 거치지 않음)
- ❌ `git worktree remove` 누락 — 고아 디렉토리·브랜치 축적
- ❌ worktree 간 파일 직접 복사 (git 우회) — 머지 시 충돌
- ❌ `git worktree remove --force` 확인 없이 실행 → 미커밋 변경 소실

## Related skills

- `simon-tdd` — 각 worktree 안에서 TDD 사이클
- `/ship` — PR 생성 (worktree 에서 실행)
- `/land-and-deploy` — 머지 후 worktree 정리 타이밍
- `/checkpoint` — worktree 간 상태 공유 (메모리 아닌 파일로)
