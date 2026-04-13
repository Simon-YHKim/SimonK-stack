---
name: project-context-md
description: Creates or updates the project-root CLAUDE.md file that Claude Code reads at session start. CLAUDE.md should list the verification tools Claude can use autonomously (dev server command, test command, browser URLs, DB access, lint/typecheck) — this realizes the Boris Cherny "verification loop" principle and is often the single most impactful file a project can add for Claude Code productivity. Use this skill whenever the user says things like "CLAUDE.md 만들어줘", "프로젝트 컨텍스트 정리", "Claude Code 설정", "검증 도구 명시", "project claude md", "bootstrap claude code for this repo", "onboard claude to this codebase"—or when entering a new repo that lacks CLAUDE.md. Also run as step 11 of app-dev-orchestrator.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon
---

# Project CLAUDE.md

프로젝트 루트에 Claude Code 가 세션 시작 시 자동 읽는 `CLAUDE.md` 를 생성한다. `simon-tdd` 의 "검증 도구 제공 원칙"(Boris Cherny) 을 실현하는 핵심 파일.

## When to use

- 새 프로젝트 시작 (`app-dev-orchestrator` 단계 11)
- 기존 프로젝트에 `CLAUDE.md` 없음
- 주요 명령어·경로·관용이 바뀌었을 때
- 새 팀원·새 Claude 세션이 막힘없이 온보딩해야 할 때

## Workflow

### 1. 기존 파일 확인

```bash
test -f CLAUDE.md && echo "EXISTS" || echo "MISSING"
```

존재 시: 섹션 단위 merge. 기존 내용을 보존해야 팀원이 써둔 컨텍스트를 날리지 않는다.
부재 시: 신규 생성

### 2. 프로젝트 컨텍스트 수집

병렬로:
- `cat package.json / pyproject.toml / go.mod / Cargo.toml`
- `ls` 로 주요 디렉토리 구조
- `grep -l` 로 주요 entry point
- `git log --oneline -10` 으로 최근 활동
- `.env.example` 있으면 필수 변수 목록

### 3. 템플릿 작성

```md
# CLAUDE.md — <project-name>

## 프로젝트 한 줄
<무엇을 하는 프로젝트인가 — 1-2 문장>

## 스택
- Language: <Node / Python / Go / Rust / ...>
- Framework: <Next.js 14 App Router / FastAPI / ...>
- DB: <Postgres via Supabase / MySQL / ...>
- Deploy: <Vercel / Fly.io / AWS / ...>
- Auth: <Supabase Auth / Clerk / ...>

## 검증 도구 (Claude 가 스스로 확인 가능)

### 개발 서버
\`\`\`
<npm run dev>  # http://localhost:<port>
\`\`\`

### 테스트
\`\`\`
<npm test>          # 전체
<npm test -- <pattern>>   # 필터
<npm run test:e2e>        # Playwright
\`\`\`

### 린트 / 타입 / 포맷
\`\`\`
<npm run lint>
<npm run typecheck>
<npm run format>
\`\`\`

### 빌드
\`\`\`
<npm run build>
\`\`\`

### DB
\`\`\`
<psql $DATABASE_URL>
<supabase db reset>
<npx prisma studio>
\`\`\`

## 주요 경로
- \`<URL>\` — <설명>
- \`/login\` — 로그인
- \`/dashboard\` — 대시보드

## 디렉토리 구조
\`\`\`
src/
  app/       — Next.js App Router 페이지
  lib/       — 공용 유틸
  components/ — UI 컴포넌트
  ...
\`\`\`

## 환경변수
`.env.example` 참조. 필수:
- \`DATABASE_URL\`
- \`NEXTAUTH_SECRET\`
- ...

## 금기 (건드리면 안 되는 곳)
- \`migrations/\` 는 기존 파일 수정 금지 (새 마이그레이션만 추가)
- \`package-lock.json\` 수동 편집 금지
- \`prod/\` 브랜치 직접 push 금지

## 관용 / 컨벤션
- 커밋: Conventional Commits (\`feat:\`, \`fix:\`, ...)
- 브랜치: \`feat/\`, \`fix/\`, \`chore/\`
- PR 머지: squash only
- 네이밍: camelCase (TS), snake_case (SQL)

## 보안
- \`.env\` 절대 커밋 금지
- API 키는 코드에 하드코딩하지 말고 env var 경유 — 레포 public 전환·실수 push 한 번이면 누출
- RLS 필수 (\`security-checklist\` 참조)
- 결제 API 는 \`paid-api-guard\` 참조

## 참고 Skills

이 프로젝트에서 유용한 skill:
- \`simon-tdd\` — TDD 사이클
- \`simon-worktree\` — 병렬 개발
- \`security-checklist\` — 감사
- \`/ship\` — 배포
- \`/qa\` — 테스트 + 자동 수정

## Global CLAUDE.md

\`~/.claude/CLAUDE.md\` 와 자동 병합됨. 글로벌 지침은 거기, 프로젝트 지침은 여기.
```

### 4. 사용자 검토 요청

템플릿 placeholder (`<...>`) 를 사용자가 채우도록 안내. 또는 Claude 가 소스 분석해 자동 채움 후 사용자 검토.

### 5. 커밋

```bash
git add CLAUDE.md
git commit -m "docs: add project CLAUDE.md with verification tools"
```

## Checklist

- [ ] 기존 파일 확인 후 충돌 처리
- [ ] 스택·검증도구·경로·환경변수 섹션 전부 채움
- [ ] 금기 항목 명시 (반복 실수 방지)
- [ ] Git 에 체크인 (Boris 원칙: 팀과 공유)
- [ ] PR 마다 필요 시 업데이트

## Anti-patterns

- ❌ 검증 도구(서버·테스트 명령) 섹션 비움 → Claude 가 스스로 확인 못 함
- ❌ `.env` 값을 CLAUDE.md 에 하드코딩
- ❌ 템플릿 placeholder 그대로 커밋 (`<TBD>` 남김)
- ❌ 프로젝트 CLAUDE.md 를 `.gitignore` 에 넣음 (팀 공유 불가)
- ❌ 한 번 만들고 업데이트 안 함 → 낡은 컨텍스트

## Related skills

- `simon-tdd` — 검증 루프의 근거 파일
- `app-dev-orchestrator` — 단계 11 에서 호출
- `/document-release` — 배포 후 업데이트
- `simon-instincts` — 프로젝트 패턴은 `project-patterns.md` 에 누적
