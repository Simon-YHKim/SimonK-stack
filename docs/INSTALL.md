# Install — simon-stack

이 레포는 Claude Code 를 위한 통합 skill 스택(Gstack + simon-stack + Superpowers 철학)이다.

## One-shot 설치

```bash
git clone https://github.com/Simon-YHKim/SimonK-stack.git
cd SimonK-stack
./scripts/install.sh
```

설치되는 것:
- `~/.claude/skills/gstack/` — Gstack 풀 트리 (36 skill + bin/scripts/lib + bun deps)
- `~/.claude/skills/<gstack-skill>/` — 36개 Gstack skill 개별 노출
- `~/.claude/skills/<simon-stack>/` — 24개 simon-stack skill
- `~/.claude/instincts/` — 4개 seed 파일 (mistakes·patterns·korean·quirks)
- `~/.claude/session-start-instincts.sh` — SessionStart hook 스크립트
- `~/.claude/CLAUDE.md` — 글로벌 지침 (instincts auto-load + Boris 원칙)

**기존 파일은 덮어쓰지 않음** — `cp -n` 로직. 재실행 안전.

## 사전 요구사항

- `git`
- `bun` (Gstack 런타임. 없어도 SKILL.md 만 동작하지만 헬퍼 스크립트는 실패)
- `node` ≥ 20 (Claude Code 자체)
- `claude` CLI 설치됨

## 수동 단계 (자동화 불가)

1. **SessionStart hook 등록** — `~/.claude/settings.json` 에 직접 추가:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "~/.claude/session-start-instincts.sh" }
        ]
      }
    ]
  },
  "permissions": {
    "allow": ["Skill"]
  }
}
```

2. **Claude Code 재시작** — 새 skill 로드를 위해.

3. **트리거 테스트**:
   - "새 앱 만들고 싶어" → `app-dev-orchestrator` 발동
   - "기능 구현해줘" → `dev-orchestrator`
   - "보안 점검" → `security-orchestrator`
   - "권한 시스템 설계" → `authz-designer`
   - "TDD 시작" → `simon-tdd`

## 구성

- **Gstack** (garrytan/gstack): 실행 파이프라인 36개. `/ship`, `/qa`, `/cso`, `/retro`, ...
- **simon-stack** (이 레포): 방법론·보안·학습 24개
  - Orchestrators: `app-dev-orchestrator`, `dev-orchestrator`, `security-orchestrator`
  - Security: `security-checklist`, `authz-designer`, `paid-api-guard`
  - Method: `simon-tdd`, `simon-worktree`, `simon-research`, `simon-instincts`, `agent-delegate`
  - Tools: `code-health-guard`, `simon-design-first`, `nextjs-optimizer`, `stitch-design-flow`, `project-context-md`
  - Meta: `skill-gen-agent`, `context-guardian`
  - General Dev: `commit`, `debug`, `explain`, `refactor`, `review`, `test-gen`

자세한 카테고리 맵: `.claude/skills/INDEX.md`

## 제거

```bash
rm -rf ~/.claude/skills/gstack
# 개별 simon-stack skill 은 수동 제거
# 백업에서 복구:
ls ~/.claude.bak-*  # 설치 시 자동 백업됨
```

## 참고

- [Gstack](https://github.com/garrytan/gstack) — 실행 파이프라인 원본
- [Superpowers](https://github.com/obra/superpowers) — TDD·worktree 철학 원본
- [everything-claude-code](https://github.com/affaan-m/everything-claude-code) — instincts·research-first 원본
