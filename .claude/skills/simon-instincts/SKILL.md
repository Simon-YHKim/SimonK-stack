---
name: simon-instincts
description: Claude 실수·패턴·한국어 컨텍스트·도구 함정을 누적 학습하는 시스템. Cumulative learning system for Claude's mistakes, project patterns, Korean context, and tool quirks. 트리거 키워드 — instincts, 학습 저장, 반복 실수 방지, 패턴 기록, Claude가 또 틀렸어, 이거 저번에도 그랬어, 같은 실수 반복, 학습.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon
---

# Simon Instincts

ECC `instincts` 개념 + Boris Cherny CLAUDE.md 철학 = Claude 가 실수할 때마다 누적 학습한다. 같은 실수를 반복하지 않는 메모리 시스템.

## When to use

- 사용자가 "이거 저번에도 그랬어", "또 틀렸어", "반복이야" 지적
- 세션 중 Claude 가 비효율적·잘못된 접근을 했을 때
- 프로젝트 고유 관용을 발견했을 때
- 새 도구·CLI 함정을 만났을 때
- `/retro` 주간 회고 시 정리

## 저장소

`~/.claude/instincts/` 아래 4개 파일:

| 파일 | 용도 |
|---|---|
| `mistakes-learned.md` | Claude 가 저지른 실수 누적 (날짜·증상·원인·예방책) |
| `project-patterns.md` | 프로젝트별 관용·제약·API·네이밍 |
| `korean-context.md` | 한국어 용어·국내 API 특이사항 (토스/네이버/카카오/부동산) |
| `tool-quirks.md` | Claude Code·CLI 도구 함정 |

## Workflow

### 1. 실수 발생 → 즉시 기록

사용자 지적 받는 즉시:

```bash
cat >> ~/.claude/instincts/mistakes-learned.md << 'EOF'

### 2026-MM-DD — <한 줄 제목>
- **증상**: 무엇이 잘못됐나
- **원인**: 근본 원인 (피상적 아님)
- **예방책**: 다음에 해야 할 것
- **출처**: <세션 / 프로젝트 / 파일>
EOF
```

또는 Edit tool 로 append.

### 2. 프로젝트 패턴 발견 → project-patterns.md

새 프로젝트 진입 시 또는 기존 프로젝트에서 새 관용 발견 시:

```md
## <project-name>
- **스택**: ...
- **도메인 용어**: ...
- **API 관용**: ...
- **금기**: ...
- **최근 업데이트**: YYYY-MM-DD
```

### 3. 한국 특이사항 → korean-context.md

- 새 국내 API 연동 (토스/카카오/네이버/PASS 등) 시 함정·제약 기록
- 한국어 UX 패턴 (본인인증, 주소 체계)
- 한국어·영어 혼용 규칙

### 4. 도구 함정 → tool-quirks.md

- Claude Code / Cursor / Codex 등 하네스 함정
- npm / pnpm / git / Supabase / Playwright 등 CLI 함정
- 두 번 이상 걸린 함정만 기록 (1회는 우연일 수 있음)

### 5. 세션 시작 시 자동 참조

`~/.claude/CLAUDE.md` 상단에 다음 블록이 있어야 한다:

```md
## Instincts (auto-loaded)
- See ~/.claude/instincts/mistakes-learned.md
- See ~/.claude/instincts/project-patterns.md
- See ~/.claude/instincts/korean-context.md
- See ~/.claude/instincts/tool-quirks.md
```

**설치 시 자동 삽입** (존재 시 skip, 없으면 신규 생성):

```bash
if ! grep -q "Instincts (auto-loaded)" ~/.claude/CLAUDE.md 2>/dev/null; then
  cat >> ~/.claude/CLAUDE.md << 'EOF'

## Instincts (auto-loaded)
- See ~/.claude/instincts/mistakes-learned.md
- See ~/.claude/instincts/project-patterns.md
- See ~/.claude/instincts/korean-context.md
- See ~/.claude/instincts/tool-quirks.md
EOF
fi
```

### 6. 주 1회 정리

`/retro` 실행 시 instincts 함께 리뷰:
- 해결된 실수는 `~~취소선~~` + 이유
- 중복 항목 병합
- 오래된 프로젝트 섹션 아카이빙

### 7. `/checkpoint` 연동

체크포인트 저장 시 instincts 파일도 스냅샷에 포함 — 롤백 시 학습 보존.

## Checklist

- [ ] `~/.claude/instincts/` 디렉토리 존재
- [ ] 4개 md 파일 초기화됨
- [ ] `~/.claude/CLAUDE.md` 에 Instincts 자동 로드 블록 존재
- [ ] 실수 지적 받으면 즉시 append
- [ ] 주 1회 리뷰 (`/retro` 와 함께)

## Anti-patterns

- ❌ 동일 실수 3회 이상 반복 — 첫 지적 시 기록 누락
- ❌ instincts 파일을 읽지 않고 새 세션 시작
- ❌ 오래된 instincts 방치 (정리 없이 무한 증가)
- ❌ 피상적 원인만 기록 ("오타 때문" → 근본: 타입 체크 안 돌림)
- ❌ instincts 를 Claude 만 관리, 사용자는 읽지 않음 → 양쪽 합의 안 됨
- ❌ 민감 정보 (토큰·비밀번호·내부 URL) 을 instincts 에 기록

## Related skills

- `/retro` — 주간 회고·리뷰
- `/checkpoint` — 스냅샷
- `/learn` — Gstack learnings (프로젝트별 학습, instincts 와 상호보완)
- `app-dev-orchestrator` — 단계 21 에서 갱신
