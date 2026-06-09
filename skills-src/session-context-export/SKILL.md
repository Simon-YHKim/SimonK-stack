---
name: session-context-export
description: "Use when the user invokes \"세션 종료\", \"hand-off\", \"context export\", \"다음 세션 준비\", \"세션 저장\", \"/session-context-export\", or 컨텍스트 80%+ 도달 시. Produces (1) sprint state snapshot (.simonk/session-<timestamp>.md), (2) recent commits 양쪽 repo (git log --oneline -10), (3) pending tasks list (사용자 본인 영역 + 자율 가능), (4) re-entry prompt (다음 세션 첫 메시지 template). Context-guardian와 짝. simonK 자율 하네스 완료 후 자동 권장 가능."
allowed-tools: Read, Bash, Write
version: 0.1.0
author: simon-stack
---

# session-context-export

세션 종료 시 *다음 세션 hand-off* 자동 생성. context-guardian과 짝 — 둘 다 *세션 보호* 도구.

## 발동 조건

- `세션 종료`, `hand-off`, `context export`
- `다음 세션 준비`, `세션 저장`
- `/session-context-export`
- 컨텍스트 사용량 80%+ 도달 시 (자동 권장)

## 산출물

### 1. Sprint state snapshot

`.simonk/session-<timestamp>.md`:

```yaml
---
session-id: <claude session UUID>
sprint-version: v<N>
ended-at: <ISO timestamp>
phases-progress:
  phase-1: 95%
  phase-2: 90%
  # ... (system-blueprint.md 참조)
---

# Session <date> Snapshot

## 이번 세션 핵심 sprint
- v<N>: <title> — <commits>

## 양쪽 repo 최근 commits (git log --oneline -10)
### SimonK-stack
<commits>

### SimonKWiki
<commits>

## Pending — 사용자 본인 영역
- [ ] <시간순>

## Pending — 자율 진행 가능 (다음 세션)
- [ ] <항목>

## Re-entry prompt (다음 세션 첫 메시지)
> simonK "<continue context: <link to this snapshot>>"
```

### 2. 양쪽 repo 최근 commits

```bash
cd "C:/Coding/Harrness Eng/SimonK-stack"
git log --oneline -10

cd "C:/Coding/obsidian/SimonKWiki"
git log --oneline -10
```

### 3. Pending tasks (분류)

- **사용자 본인 영역** (시뮬레이션 X): 회고 일정 · 면접 · 출시 등
- **자율 진행 가능** (다음 세션 simonK가 픽업): 시스템 구축 잔여

### 4. Re-entry prompt (template)

```
simonK "<이전 세션 .simonk/session-<timestamp>.md 읽고 이어 진행. Phase 진행률 + pending 자율 작업 확인 후 적합한 sprint 시작.>"
```

→ 새 세션 첫 메시지로 복붙 → simonK 6-phase 진입 + Boundary Check + 자동 hand-off.

## context-guardian과의 짝

| skill | 역할 |
|---|---|
| `context-guardian` | *예방* (CLAUDE.md 룰 + .claudeignore + 사전 SESSION_RECOVERY.md) |
| `session-context-export` | *마무리* (snapshot + 다음 세션 entry prompt) |

→ 같이 호출 시: context-guardian이 *예방·모니터*, session-context-export가 *최종 hand-off*.

## simonK 자율 하네스 통합 (옵션)

simonK 6-Phase 완료 후 *자동 권장*:

```
Phase 6 Final Report 후:
→ "다음 세션 hand-off 자동 export 할까? (y/n)"
→ y → session-context-export 자동 호출
→ .simonk/session-<timestamp>.md 생성 + commit
```

현재 manual 호출만. 추후 simonK SKILL.md에 통합 옵션.

## 보안

- session UUID + 최근 작업 path만 (개인 정보 X)
- API key / credentials 절대 export X
- *PRIVATE repo 권장* (사내 작업 reference)

## 교차참조

- `context-guardian` skill (예방·모니터)
- `simonk` skill (6-Phase 자율 하네스)
- `SimonK-stack/.simonk/log.md` (sprint append-only log)

---

*v0.1.0 placeholder 2026-05-25. v1.0: 첫 실제 hand-off 시도 후 본격 작성.*
