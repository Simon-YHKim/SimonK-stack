---
name: session-context-tracker
description: "Use when a Claude Code session is getting long, slow, or near its context limit, or when deciding how to continue after a response — triggers \"세션 관리\", \"컨텍스트 정리\", \"세션 끊을 때\", \"rewind 할까\", \"compact 해줘\", \"session management\", \"context running out\", \"clear or compact\". Produces a 5-option decision (continue / rewind / clear / compact / subagent) with the matching tactic, a proactive-compact hint, and a subagent delegation check. Use proactively whenever a session crosses a context threshold so context rot never sets in."
allowed-tools: Read, Grep, Glob
version: 1.0.0
author: simon-stack
---

# session-context-tracker

매 응답 후 세션을 어떻게 이어갈지 5선택지로 자가 점검하는 메타 skill. context rot 가 누적되기 전에 선제 대응한다.

근거 출처: Anthropic 공식 세션 관리 가이드 (Simon-LLM-Wiki `concepts/session-management-tactics.md`).

## 왜 필요한가

- Claude 는 매 메시지마다 컨텍스트를 처음부터 다시 읽는다 — 토큰 비용이 곱셈으로 증가.
- 컨텍스트 검색 정확도는 창이 커질수록 떨어진다 (256K 92% → 1M 78%, context rot).
- auto-compaction 은 95% 에서 발동 = 이미 늦음. 모델이 가장 산만할 때 요약시키는 꼴.
- 세션 한도 도달의 주원인은 창 크기가 아니라 5선택지 중 continue 만 쓰는 습관.

## 5선택지 자가 점검

매 응답 후, 또는 세션이 무거워질 때 아래 표로 판단한다.

| 선택지 | 트리거 상황 | 행동 |
|---|---|---|
| **continue** | 직전까지의 컨텍스트가 _전부_ 필요할 때만 | 다음 메시지 이어서 |
| **`/rewind`** | Claude 가 잘못된 경로로 갔을 때 | 실패 지점 직전으로 되돌리고 흔적 삭제 |
| **`/clear`** | 완전히 다른 작업으로 전환 | 세션 통째로 비우고 새 시작 |
| **`/compact`** | 맞게 가다가 컨텍스트가 무거워졌을 때 | 힌트 동반 수동 압축 |
| **subagent** | 중간 과정 불필요, 결론만 필요 | 별도 컨텍스트에 위임 |

기본값(continue) 을 의심하는 것이 이 skill 의 핵심. "정말 직전 컨텍스트가 전부 필요한가?" 를 먼저 묻는다.

## Rewind 우선 원칙

실패 후 "그거 안 됐어, 이거 해봐" 라고 _이어서_ 답하면 실패 시도·틀린 코드·오추론이 컨텍스트에 영구히 남아 매 응답마다 다시 읽힌다 (지수 누적).

올바른 패턴:

1. 파일을 읽기 _직전_ 지점으로 `/rewind` (더블 ESC)
2. 새 프롬프트에 _배운 것만_ 주입 — 예: "접근법 A 는 쓰지마, foo 모듈이 그걸 노출하지 않으니까"
3. 결과물은 같고 컨텍스트는 깨끗 → 세션 수명 2~3배

팁: rewind 메뉴의 "summarize from here" 로 인수인계 메시지를 자동 생성한다. 실패에서 배운 건 남기고 흔적은 지운다.

## Proactive compact 힌트

auto-compaction 을 기다리지 않고, 다음 작업이 예상 가능한 지점에서 직접 친다.

- **힌트 필수**: `/compact OAuth 리팩토링에 집중, 테스트 디버깅 내용은 제외` — 무엇을 남기고 버릴지 지정.
- 모델이 _아직 맑을 때_ 친다. 같은 `/compact` 라도 타이밍이 결과 품질을 가른다.
- 실무 기준값: 1M 모델 기준 약 12% (~120K) 에서 큰 작업 전 한 번 정리.

이 skill 이 힌트 문장을 생성할 때는 직전 N 개 메시지의 주제를 요약해 "집중 / 제외" 두 줄로 제시한다.

## Subagent 위임 판정

위임 여부는 질문 하나로 판단한다:

> **"이 작업의 중간 출력물을 나중에 또 볼 일이 있나?"**

- "아니, 결론만 알면 돼" → subagent (스펙 검증, 타 레포 요약, 문서 생성)
- "응, 과정을 다 봐야 해" → 메인에서 직접 (지금 보는 코드 리팩토링)

상세 위임 설계는 `agent-delegate` skill 로 이어진다.

## Workflow

1. **현재 세션 상태 추정** — 대화 길이, 읽은 파일 수, 작업 전환 여부를 본다.
2. **5선택지 매핑** — 위 표로 현재 상황에 맞는 선택지를 고른다.
3. **선택지별 행동 제시**:
   - rewind → 되돌릴 지점 + 재주입할 "배운 것" 한 줄
   - compact → "집중 / 제외" 힌트 두 줄
   - subagent → 위임 판정 질문 적용 결과 + `agent-delegate` 연결
   - clear → 새 세션 시작 프롬프트
4. **경고 임계치 안내** — 70% 선제 compact 권장, 80% 이상이면 `context-guardian` 으로 인계.

## context-guardian 와의 관계

| | session-context-tracker | context-guardian |
|---|---|---|
| 초점 | 매 응답 후 5선택지 판단 | 컨텍스트 고갈 예방·모니터링·복구 |
| 산출 | 선택지 + 힌트 (조언) | CLAUDE.md 규칙, 복구 파일 (파일) |
| 시점 | 응답마다 | 세션 시작 / 위험 시 / 끊긴 후 |

두 skill 은 상호보완적. 이 skill 이 _판단_, context-guardian 이 _예방·복구 인프라_.

## 피해야 할 함정

- continue 를 기본으로 두고 5선택지를 점검하지 않음 — 한도 조기 도달의 주원인.
- 잘못된 경로에서 rewind 대신 이어서 교정 — 실패 흔적이 컨텍스트에 누적.
- 힌트 없는 `/compact` — auto 가 중요한 걸 버리는 사고와 동일.
- 중간 과정이 안 중요한 작업을 메인에서 직접 — subagent 로 위임해야 메인이 가벼움.

## Related skills

- `context-guardian` — 컨텍스트 고갈 예방·모니터링·복구 인프라
- `agent-delegate` — subagent 위임 결정 시 위임 설계로 연결
- `simon-worktree` — 병렬 세션 분리 (각 worktree 가 독립 컨텍스트)
- `simon-instincts` — 같은 컨텍스트 실수가 반복되면 instincts 에 기록
