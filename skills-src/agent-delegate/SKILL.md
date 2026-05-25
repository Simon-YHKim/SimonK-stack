---
name: agent-delegate
description: "Use when the user asks to delegate work to sub-agents, parallelize tasks, save tokens via agent splitting—triggers \"에이전트 위임\", \"sub-task\", \"delegate to agent\", \"parallel agents\", \"작업 분할\", \"token 절약\", \"멀티 에이전트\", \"agent 병렬화\". Produces a delegation plan with task decomposition, context envelope (file paths only, no content), output contracts (exact return format), and pattern selection (Fan-out / Pipeline / Supervisor). Minimizes round-trips and per-agent context. Used by app-dev-orchestrator, simon-worktree, and any multi-step work that benefits from parallelization."
allowed-tools: Read, Write, Edit, Grep, Glob
version: 1.1.0
author: simon-stack
---

# agent-delegate

Sub-agent 위임으로 작업을 쪼개고 토큰을 절약하는 메타 skill.

## 핵심 원칙

1. **작업 분해는 atomic하게** — 각 sub-task는 독립적으로 완료 가능해야 함
2. **Context envelope 최소화** — file path 전달, file content는 sub-agent가 읽음
3. **Output contract 명시** — sub-agent가 어떤 포맷으로 반환할지 사전 정의
4. **No round-trips** — sub-agent가 추가 질문 없이 끝낼 수 있게 specification 충분히

## Step 0. 위임 판정 (먼저 한 줄로 거른다)

분해·envelope·contract 를 설계하기 _전에_, 이 작업을 애초에 위임할지부터 한 질문으로 판정한다:

> **"이 작업의 중간 출력물을 나중에 또 볼 일이 있나?"**

- "아니, 결론만 알면 돼" → **위임 (subagent)**. 중간 과정이 메인 컨텍스트에 남을 이유 없음.
  - 예: 스펙 검증(통과/실패만), 타 레포 읽고 요약, 깃허브 보고 문서 작성
- "응, 과정을 다 봐야 해" → **메인에서 직접**. 위임하면 오히려 손해.
  - 예: 지금 보고 있는 코드 리팩토링

이 한 줄을 매 작업마다 던지는 습관이 메인 세션 컨텍스트를 가볍게 유지한다. (출처: Anthropic 세션 관리 가이드 — `session-context-tracker` skill 과 공유.)

판정 결과가 "위임" 이면 아래 4단계로 진행한다.

## Delegation Protocol (4단계)

### Step 1. Task decomposition

큰 작업을 atomic, context-independent 단위로 쪼갠다.

좋은 분해:
- "X 파일들 읽고 사용 안 하는 export 찾기" — 독립적, 명확한 input/output
- "Y 디렉토리에서 함수명 패턴 검색" — 단일 책임

나쁜 분해:
- "코드베이스 이해하고 좋게 만들기" — vague, 무한정 확장
- "Step A 하고, 결과 보면서 Step B 결정" — 의존성, 라운드트립 발생

### Step 2. Context envelope

각 sub-agent에 **필요한 최소 context만** 전달.

✅ Good:
```
Read src/auth/middleware.ts (lines 40-80) and report:
- All function signatures
- Any uses of process.env
Output as JSON: { signatures: [...], envVars: [...] }
```

❌ Bad:
```
Here is the entire codebase: <10000 lines pasted>
Find env vars used in auth.
```

### Step 3. Output contract

Sub-agent의 반환 형식을 사전에 못 박는다.

```
Respond with ONLY a JSON array, no prose:
[
  { "file": "...", "line": 0, "issue": "..." }
]
```

이유: prose가 섞이면 parsing 실패, agent들 간 chaining 어려움.

### Step 4. No round-trips

Sub-agent가 추가 질문해야 하면 spec이 부족한 것.

체크리스트:
- [ ] 모든 input 명시됨 (파일 경로, 옵션, 제약)
- [ ] Output 형식 명시됨 (JSON schema, markdown 템플릿 등)
- [ ] Edge case 처리 명시됨 (파일 없을 때, 빈 결과일 때)
- [ ] Time/scope 한도 명시됨 (under 200 words, max 3 files)

## Token Minimization 기법

| 기법 | Bad | Good |
|---|---|---|
| File 전달 | 전체 내용 paste | path만 전달, agent가 Read |
| 응답 길이 | "explain in detail" | "respond in under 200 words" |
| 중복 context | 매 agent에 같은 background | 한 번 정의, 모두 참조 |
| Format | 자유 prose | 구조화된 JSON/markdown |
| Verbosity | "let me think... actually..." | "Final answer: ..." |

## 위임 패턴

### Pattern 1. Fan-out (병렬 독립)

여러 독립 task를 동시에 실행. 결과 모아서 사용.

```
사용자 요청: "이 3개 모듈의 보안 점검"
  ↓
Agent A: auth 모듈 점검    } 동시 실행
Agent B: payment 모듈 점검  }
Agent C: storage 모듈 점검  }
  ↓
결과 합쳐서 사용자에게 리포트
```

언제 쓰나: 작업들 사이 의존성 없음, 결과가 독립적

### Pattern 2. Pipeline (순차 의존)

이전 agent 결과가 다음 agent input.

```
Agent A: 코드베이스 스캔 → 큰 파일 목록 (JSON)
  ↓
Agent B: 각 파일 분석 → 분리 추천 (markdown)
  ↓
Agent C: 분리 코드 생성 → diff (patch format)
```

언제 쓰나: 단계별 작업, 각 단계가 다음 input

### Pattern 3. Supervisor (라우팅 전문가)

상위 agent가 작업 분류 → 적절한 specialist에게 라우팅.

```
사용자 요청
  ↓
Supervisor Agent: 요청 분류
  ├── 보안 관련? → Security Specialist
  ├── 디자인 관련? → Design Specialist
  └── 코드 관련? → Code Specialist
```

언제 쓰나: 다양한 도메인의 요청, 각 도메인 전문 agent 존재

## Anti-patterns

- ❌ 전체 codebase를 sub-agent에 paste
- ❌ Sub-agent가 "더 정보 필요해요" 라고 묻는 task spec
- ❌ Agent 간에 같은 background 반복 전달
- ❌ "잘 해줘" 같은 vague 명령
- ❌ Sequential 작업을 fan-out으로 (의존성 무시)
- ❌ 결과 합치는 로직 없이 fan-out (parallel agents 결과 버림)

## Integration

- `app-dev-orchestrator` — 21단계의 각 stage가 다른 skill에 위임
- `simon-worktree` — 병렬 Claude 세션 (worktree 분리 = agent 분리)
- `context-guardian` — 각 agent 세션이 독립적으로 context 한도를 가짐

## Related skills

- `session-context-tracker` — 5선택지 중 subagent 가 맞는지 판단. 이 skill 의 Step 0 판정 질문과 동일 출처
- `simon-worktree` — git worktree로 sessions 분리
- `context-guardian` — 각 agent의 context 보호
- `simon-research` — 리서치 작업을 fan-out으로 병렬화 가능
