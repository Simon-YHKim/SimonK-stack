---
name: context-guardian
description: Use when the user wants to prevent Claude Code session disconnects, save recovery state, or manage context limits — triggers include "context-guardian", "컨텍스트 저장", "세션 복구", "recovery 만들어줘", "어디까지 했지", "새 세션 준비해", "context 위험해", "compact 할 때", "prevent context overflow", "session recovery". Has 4 independent modes (prevention / monitoring / proactive-compact / recovery) that run separately or together. Produces CLAUDE.md rule block, .claudeignore, SESSION_RECOVERY.md, context_limit_log.json, and a proactive /compact hint. Different from /checkpoint which unconditionally saves state — this skill focuses on PREVENTING context exhaustion and recovering gracefully after disconnects.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.1.0
author: simon
---

# Context Guardian

Claude Code 세션이 context window 한도에 도달해 응답이 느려지거나 끊기는 문제를 3 단계로 대응합니다:

1. **Prevention** — 컨텍스트가 쌓일 구조 자체를 제거 (CLAUDE.md 규칙 + `.claudeignore`)
2. **Monitoring** — 실측 기반 한도 추적 (`context_limit_log.json`) + 80/90 % 경고
3. **Proactive Compact** — auto-compaction(95%) 전에 70/80 % 에서 선제 압축 + 도메인 힌트 생성
4. **Recovery** — 세션 간 연속성 보장 (`SESSION_RECOVERY.md`)

## Relationship to `/checkpoint`

Gstack `/checkpoint` 는 작업 상태를 조건 없이 스냅샷 저장/재개합니다. Context Guardian 은 다른 문제를 해결합니다:

| | `/checkpoint` | `context-guardian` |
|---|---|---|
| 목적 | 일반 작업 스냅샷 | 컨텍스트 고갈 *예방* + *복구* |
| 트리거 | 명시적 저장 요청 | 80% 임박 · 세션 끊긴 후 |
| 산출물 | Git + 결정 로그 | CLAUDE.md 규칙 + `.claudeignore` + `SESSION_RECOVERY.md` + `context_limit_log.json` |
| 실행 시점 | 작업 중간중간 | 세션 시작 (prevention) / 위험 시 (monitoring) / 끊긴 후 (recovery) |

두 skill 은 **상호보완적**. `/checkpoint` 로 중간 저장하고, `context-guardian` 으로 고갈 방지 + 세션 연속성 유지.

## Workflow

3 mode 중 하나를 선택하거나 `all` 로 통합 실행. 모든 스크립트는 **프로젝트 루트에서 실행**한다고 가정합니다.

### Mode 1: Prevention

프로젝트에 보호 규칙을 설치합니다. 세션마다 한 번이면 충분 (idempotent).

```bash
bash .claude/skills/context-guardian/scripts/install-rules.sh
```

동작:
1. **CLAUDE.md Rule Block 삽입** — 프로젝트 루트 `CLAUDE.md` 에 아래 내용이 없으면 append. 마커 `<!-- context-guardian-rules:v1 -->` 로 중복 삽입 방지.
   - 작업 범위 제한 (세션당 파일 ≤ 5 개, 한 번에 하나의 기능)
   - 파일 읽기 제한 (`node_modules`/`.next`/`dist`/`.git` 차단, 1000 줄+ 파일 부분 읽기)
   - 광범위 요청 작은 단위로 분해 후 사용자 확인
   - 80%/90% 컨텍스트 경고 규칙
2. **`.claudeignore` 생성** — 없을 때만. `node_modules`, `.next`, `dist`, `.git`, `*.lock`, `build`, `coverage`, `.cache`, `.turbo`, `.vercel`, `.parcel-cache`, `*.min.js`, `*.min.css`.
3. **`.gitignore` 확인 안내** — `SESSION_RECOVERY.md` 와 `context_limit_log.json` 은 per-session state 이므로 보통 커밋 대상이 아님. 사용자에게 확인 요청.

### Mode 2: Monitoring

실측 기반 동적 한도 관리. **한도 하드코딩 금지** — 모델이 업데이트되면 자동으로 갱신돼야 하므로 측정값으로만 작동.

```bash
# 세션 시작 시 현재 한도 확인
bash .claude/skills/context-guardian/scripts/update-context-log.sh --load

# 끊김 발생 후 수동 기록
bash .claude/skills/context-guardian/scripts/update-context-log.sh \
  --record --model claude-opus-4-6 --measured 195000

# 현재 사용량 체크 (수동)
bash .claude/skills/context-guardian/scripts/update-context-log.sh --check 140000
```

**`context_limit_log.json` 스키마**:
```json
{
  "model": "claude-opus-4-6",
  "measured_limit": 200000,
  "safety_margin": 0.8,
  "effective_limit": 160000,
  "last_disconnect": "2026-04-14T12:34:56Z",
  "history": [
    { "date": "2026-04-12T10:00:00Z", "measured_limit": 200000, "model": "claude-opus-4-6" }
  ]
}
```

- `effective_limit` = `measured_limit × safety_margin` (기본 0.8)
- `history` 배열로 모델 변경 이력 추적
- 파일 없으면 보수적 기본값 100,000 (effective 80,000) 사용

**경고 임계치**:
- **80 %** (128K of 160K): `⚠️ 컨텍스트 80% 도달. SESSION_RECOVERY.md 생성 후 새 세션 준비 권장`
- **90 %** (144K of 160K): `🚨 컨텍스트 위험 수위. 즉시 작업 마무리 + 새 세션 전환`

**주의**: Claude Code 는 skill 에 실시간 토큰 카운터를 노출하지 않습니다. 이 skill 의 Monitoring 은 (a) 문서화된 한도 기준 + (b) 사용자 수동 기록 + (c) 세션 시작 시 로그 자동 읽기로 구성됩니다. 실시간 자동 감지는 Claude Code 내장 기능에 의존.

### Mode 3: Recovery

세션이 끊긴 후 손실 없이 이어갈 수 있도록 상태를 포착.

```bash
bash .claude/skills/context-guardian/scripts/create-recovery.sh
```

동작:
1. **git 상태 수집** — 레포명, 브랜치, 마지막 커밋, `git status --short`, `git diff --stat`
2. **`.env.example` 파싱** — env var 이름만 추출 (값 절대 ❌)
3. **`SESSION_RECOVERY.md` 작성** — 프로젝트 루트에 생성:
   - 자동 필드: 타임스탬프, 레포, 브랜치, 커밋, 변경 파일 목록
   - 수동 필드 (템플릿만): 완료/미완료 작업, 핵심 변경 요약
   - 다음 세션 시작 프롬프트 (복사용)
4. **보안 스캔** — 출력 파일에 `sk-`, `sk_live_`, `pk_live_`, `AKIA`, `ghp_`, `xox[bps]-` 패턴이 있으면 abort + 경고

**새 세션 시작 시 자동 복원 (manual convention)**:
새 세션 첫 메시지에 "SESSION_RECOVERY.md 읽고 이어해줘" 라고 말하거나, 생성된 파일 하단의 "다음 세션 시작 프롬프트" 를 복사해서 붙여넣으면 됩니다. Claude 는 해당 파일을 먼저 읽고 첫 미완료 작업부터 시작합니다.

### Mode 3.5: Proactive Compact

auto-compaction 은 컨텍스트 95% 에서 발동합니다 — 이미 context rot 가 심한 구간이고, 모델이 가장 산만한 상태에서 요약을 시키는 꼴입니다. Proactive Compact 모드는 그 _전에_ 친다.

**임계치 (Monitoring 의 80/90 보다 보수적)**:

- **70 %** (112K of 160K): `💡 컨텍스트 70% — 다음 작업 단위 전에 proactive /compact 권장`
- **80 %** (128K of 160K): `⚠️ 컨텍스트 80% — 지금 /compact 또는 SESSION_RECOVERY.md 생성`

70/80 을 쓰는 이유: auto(95%) 와 disconnect-recovery(80/90) 사이에 _아직 모델이 맑은_ 구간을 확보하기 위함.

**도메인 힌트 생성기**: 단순 `/compact` 가 아니라 무엇을 남기고 버릴지 지정하는 힌트를 동반해야 한다. 이 모드는 직전 작업 맥락에서 힌트 두 줄을 생성한다:

```
/compact <현재 주력 작업>에 집중. <부수적으로 끝난 작업>은 제외.
```

예: `/compact OAuth 리팩토링에 집중. 테스트 디버깅 내용은 제외.`

힌트 생성 절차:

1. 직전 N 개 메시지에서 _주력 작업_ 1개와 _이미 끝난 부수 작업_ 을 식별
2. "집중 / 제외" 두 항목으로 압축
3. `/compact <집중>. <제외>.` 형태로 사용자에게 제시

**session-context-tracker 와의 분담**: `session-context-tracker` 가 5선택지 중 compact 가 맞는지 _판단_ 하고, 이 모드가 임계치 감지 + 힌트 _생성_ 을 담당. 두 skill 은 같은 출처(세션 관리 가이드)를 공유.

### Mode: all (통합 실행)

```bash
SKILL=.claude/skills/context-guardian/scripts
bash $SKILL/install-rules.sh                  # Prevention
bash $SKILL/update-context-log.sh --load      # Monitoring (load only)
bash $SKILL/create-recovery.sh                # Recovery (optional)
```

Proactive Compact 모드는 스크립트가 아닌 _판단 모드_ 이므로 통합 실행에 포함되지 않습니다. 세션 진행 중 70/80 % 감지 시 수동 적용합니다.

## 보안

- `SESSION_RECOVERY.md` 에 **API 키·토큰·패스워드 절대 기록 금지**. 환경변수는 이름만.
- `create-recovery.sh` 는 자동으로 시크릿 패턴을 grep 하고 발견 시 abort 합니다.
- `git status` / `git diff` 에 민감 정보가 포함돼 있을 수 있으므로 생성 후 수동 검토를 권장.
- `SESSION_RECOVERY.md` 와 `context_limit_log.json` 은 `.gitignore` 에 추가하는 것이 일반적.

## Checklist

**Prevention**:
- [ ] `CLAUDE.md` 에 `<!-- context-guardian-rules:v1 -->` 마커 존재
- [ ] `.claudeignore` 존재 + `node_modules`/`.next`/`.git` 차단
- [ ] 사용자에게 `.gitignore` 업데이트 여부 확인

**Monitoring**:
- [ ] `context_limit_log.json` 존재 + 유효 JSON
- [ ] `safety_margin` ≥ 0.8
- [ ] `history` 에 최소 1 개 entry

**Proactive Compact**:
- [ ] 70 % 도달 시 다음 작업 단위 전 compact 권장
- [ ] `/compact` 에 "집중 / 제외" 도메인 힌트 동반
- [ ] auto-compaction(95%) 을 기다리지 않음

**Recovery**:
- [ ] `SESSION_RECOVERY.md` 에 시크릿 없음 (grep 통과)
- [ ] 환경변수는 이름만 (값 ❌)
- [ ] 다음 세션 시작 프롬프트 포함
- [ ] git 자동 필드 populated (브랜치, 커밋, status)

## 피해야 할 함정

- **한 세션에서 10+ 파일 수정** — 범위가 너무 넓음. prevention 규칙대로 5 개 이하로 분해해서 세션을 나누세요.
- **`SESSION_RECOVERY.md` 에 `.env` 값 붙여넣기** — create-recovery.sh 가 abort 하지만, 수동 편집으로 들어갈 수 있으니 커밋 전 검토 필수.
- **`context_limit_log.json` 을 하드코딩** — 모델 업데이트 시 stale. 반드시 `--record` 명령으로 실측값 누적.
- **`CLAUDE.md` 기존 블록 덮어쓰기** — install-rules.sh 는 append + 마커 기반 skip. 수동 편집 금지.
- **`/checkpoint` 와 중복 사용 시도** — 둘은 다른 문제를 해결. context-guardian 은 *예방* 이고 /checkpoint 는 *일반 스냅샷*. 동시 사용 OK, 중복 저장 불필요.
- **`node_modules/` 를 통째로 grep** — .claudeignore 가 막는 이유. 필요 시 특정 패키지 경로만 명시.

## Related skills

- **`session-context-tracker`** — 매 응답 후 5선택지(continue/rewind/clear/compact/subagent) 판단. Proactive Compact 모드와 같은 출처(세션 관리 가이드)를 공유하며, 판단은 tracker, 임계치+힌트 생성은 이 skill 이 담당.
- **`/checkpoint`** (Gstack) — 상호보완. 일반 작업 상태 저장·재개. context-guardian 은 고갈 예방·복구에 특화.
- **`simon-instincts`** — context 고갈 원인이 반복되면 `~/.claude/instincts/mistakes-learned.md` 에 기록해서 재발 방지.
- **`simon-worktree`** — 병렬 세션 사용 시 각 worktree 에서 context-guardian 독립 관리 (worktree 마다 자기 `SESSION_RECOVERY.md`).
- **`/retro`** (Gstack) — 주간 회고 시 `context_limit_log.json` history 리뷰로 패턴 파악.
- **`app-dev-orchestrator`** — 21 단계 파이프라인 실행 시 각 단계 사이에 prevention 모드 자동 실행 권장.
