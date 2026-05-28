---
name: simonk
description: "Use when the user invokes the `simonK` keyword, `/simonK <task>` slash, or runs `simonK <task>` from PowerShell. Triggers autonomous team-based execution for any non-trivial task in Simon Kim's environment (E:\\Coding Infra). Trigger phrases: 'simonK', '/simonK', 'ultrawork', 'ulw', '한 번에 끝내줘', '팀으로 진행해', '자율로 끝까지', '스프린트 시작'. Use for tasks requiring planning + parallel subagent delegation + verification + git persistence. Produces: (1) early ambiguity score check with Socratic Q&A if score<6, (2) sprint plan written to .simonk/plan.md, (3) parallel Task-tool delegation across sub-agents, (4) test/lint verification, (5) conventional commits + auto-push under Full-Auto policy (all repos, PRs always require explicit OK), (6) structured final report with task summary + verification evidence + git status."
version: 1.0.0
---

# simonk — Unified Autonomous Team Harness

> Simon Kim의 통합 자율 팀 하네스. 단일 진입점 (`simonK` PowerShell + `/simonK` slash). 모호함 자동 catch → sprint 분해 → 병렬 실행 → 검증 → auto-push.

## 0. 운영 컨텍스트 (매 호출 시 inject)

- **Wiki vault**: `E:\Coding Infra\obsidian\SimonKWiki\` (env `$SIMON_WIKI_DIR`)
- **Stack root**: `E:\Coding Infra\Harrness Eng\SimonK-stack\`
- **External refs**: `E:\Coding Infra\Harrness Eng\external\{oh-my-claudecode, oh-my-openagent, OpenHarness, open-cowork, obsidian-skills, anthropics-skills}`
- **Locale**: Korean default · 직설적·관찰형 톤 · *italic* 강조 · 위로 과잉 금지 · 옵션 A/B/C 나열 default 금지 (첫 추천 명확)
- **Identity**: Simon Kim · 대기업 제조 IE 7년차 · AI 도메인 pivot 중 (상세 PII는 SimonKWiki PRIVATE wiki/CLAUDE.md § 4)
- **Values inject (Brain Trinity)**: 노력화폐·진정성·장인정신·솔직함·카르마 · 회로 4·5·8 주의 (본인 작품 과소평가 패턴) · 진단 수치는 PRIVATE wiki [[birkman-9-components]] 참조

## 1. Auto-push 정책 — Full Auto

- 사용자 명시 확인 없이 즉시 git commit + push **모든 repo** (private · public 동일)
- 단 **PR 생성·머지는 절대 자동 X** (글로벌 CLAUDE.md 정책)
- 단 **파괴적 작업** (`rm -rf`, `git reset --hard`, force push to main of multi-collab repo, DB drop) 은 사용자 확인 필수
- 단 **.env / credentials 수정·노출** 은 즉시 STOP

## 1.4 Doctor Check (필수 매 호출) — 2026-05-28 추가 (SenseNova pattern)

작업 진행 전 환경 health check (silent if clean, < 1 초):

| 검출 | 명령 | 처리 |
|---|---|---|
| **Git config dirty** | `git -C $REPO_DIR status -s` | dirty 면 사용자 alert (auto-push 위험) |
| **Network** | `curl -sf -m 3 https://github.com > /dev/null` | 실패 시 push/clone 작업 skip + log |
| **Disk** | `df --output=avail $HOME \| tail -1` | <500MB 면 warn (vendored clone 위험) |
| **gcloud auth** (선택) | `gcloud-helper` skill 위임 | ghost project 면 auto-fix |
| **Node/Python** (선택) | 작업 종류에 따라 `node -v` / `python3 -V` | 부재면 skill 매핑 변경 |

기존 `gcloud-helper` skill 과 통합 — Doctor 가 Phase 0 에서 silent 호출. 차용 출처: OpenSenseNova/SenseNova-Skills.

## 1.5 Boundary Check (필수 매 호출) — 2026-05-25 추가

작업 *진행 전* 다음 detection (silent if clean):

| Risk | 검출 패턴 | 처리 |
|---|---|---|
| **HIGH** | 사내 프로젝트명 (Max Capa Agent · 사내 시그니처 · 사내 양성 그룹 등) — *PUBLIC repo write 시* | STOP + 사용자 confirm |
| **HIGH** | API key 패턴 (`sk-ant-api\S{10,}` · `sk-proj-\S{10,}` · `AIza\S{30,}` · `ghp_\S{30,}`) | 즉시 STOP + 마스킹 |
| **HIGH** | `.env` / `credentials` / `*.kdbx` 수정 시도 | 즉시 STOP |
| MEDIUM | 사내 인물명 · 사내 수치 (MTBF · CapEx · 양성 인원) · 사내 라인 위치 | 마스킹 권장 + 진행 |
| MEDIUM | 본인 PII (이름·거주지·진단 결과) — *PUBLIC repo write 시* | 사용자 alert + 진행 (default 보존) |
| LOW | 일반 도메인 명칭 (Apple · Google · Tesla 등) | 진행 (log만) |

### Detection 시 흐름

```
1. write target identify (PUBLIC repo vs PRIVATE wiki vs system local)
2. content scan (위 패턴)
3. HIGH 검출 → 작업 일시 정지 + 사용자 confirm 후 진행/마스킹/SKIP
4. MEDIUM 검출 → 권장 옵션 1-2 제시, 사용자 default 보존 가능
5. LOW → 자동 진행
```

### 마스킹 매핑 reference

PUBLIC repo 작성 시 사용자 합의 generic 명칭:
- `Max Capa Agent v0/v1.0` → `closed-network signature agent`
- `사내 양성 24명` → `사내 양성 그룹` (수치 제거)
- `LG 폐쇄망` → `on-prem`
- `사내 라인 X MTBF` → `<task>` 일반화

실제 매핑 정본: SimonKWiki PRIVATE `wiki/entities/orgs/internal-projects-catalog.md`

## 2. Phase 1 — Ambiguity Score Check (필수 첫 단계)

작업 입력을 받자마자 4 차원 0-10 평가 (LLM 내부 평가, tool call 없이 fast):

| 차원 | 평가 |
|---|---|
| **Goal clarity** | 원하는 outcome 이 구체적? ("improve X" = 낮음, "rename file Y to Z" = 높음) |
| **Scope boundary** | 변경 set 이 명확? (open-ended "전체" = 낮음, 명시 파일/모듈 = 높음) |
| **Success criteria** | 완료 검증 가능? (측정 불가 = 낮음, 테스트 통과 = 높음) |
| **Risk awareness** | 민감 영역 식별됨? (public push · 외부 API · prod = 위험 ↑) |

**총합 score < 6 → Socratic Q&A 모드** (AskUserQuestion으로 3-5문항 max, simultaneously).
모호함 catch 핵심 질문 패턴:
1. "성공 기준 — 어떤 상태가 되면 끝?" (목표 명확화)
2. "범위 경계 — [관련 영역] 도 손대?" (scope)
3. "리스크 — [public repo / 외부 API / prod 데이터] 가 범위 안?" (안전)
4. "우선순위 — 시간 빠듯하면 [A] vs [B] 중 어디 먼저?" (제약)
5. "참조 — 이미 너가 적용한 패턴/스킬 (예: app-dev-orchestrator) 활용해?" (재사용)

**score >= 6 → Phase 2 직진** (질문 없이 진행).

## 3. Phase 2 — Sprint Planning

작업 규모 판단:
- **Trivial** (single edit · lookup · 1 file 수정): Phase 2 skip · 바로 Phase 3
- **Complex** (multi-file · multi-step · 병렬 가능): plan 작성

Plan 작성:
1. 작업을 ≤5개 sub-task로 분해
2. dependency 그래프 (어느 게 병렬 OK, 어느 게 순차)
3. `.simonk/plan.md` 에 frontmatter + 작업 list 박음:
   ```yaml
   sprint-id: <ISO timestamp>
   user-task: "<original user input>"
   ambiguity-score: <N/10>
   sub-tasks: <count>
   parallel-tasks: <count>
   sequential-tasks: <count>
   ```
4. plan 요약 (2-3 line per task) 사용자에게 1줄로 출력 → 명시 반대 없으면 진행 (default proceed)

## 4. Phase 3 — Parallel Execution

**Independent sub-tasks → Task tool 병렬 호출** (단일 message 내 multiple Task tool 호출 = 동시 실행):

```
agent_type 선택 가이드:
- general-purpose  → research, complex multi-step
- Explore          → read-only code/file search (가벼움)
- Plan             → architecture/design 결정
- claude           → fallback (catch-all)
```

각 Task agent에 전달:
- 명확한 단일 목표 (구체)
- 필요 file paths (절대 경로)
- 예상 output 형식
- 작업 컨텍스트 (Simon-stack root, wiki 위치)

**Sequential sub-tasks**: 이전 output → 다음 input 체이닝 · 단일 메시지에 묶지 않음.

**Git worktree 병렬** (선택, advanced): 큰 refactor면 `simon-worktree` 스킬 호출.

**Multi-terminal dispatch (v23 Phase B, 2026-05-25 추가)**: 사용자 trigger ('병렬로', '다중 터미널', 'team mode') 감지 시 또는 N>3 independent tasks 인 경우:
1. `model-router` skill 호출 → 각 task type 별 best LLM 매핑 ([[wiki/concepts/ai-model-benchmarks]] source)
2. `scripts/multi-terminal-launch.ps1 -ConfigPath dispatch.json` 으로 Windows Terminal tabs 동시 launch
3. Cost estimate 사용자 confirm (>$5 threshold) + 파괴적 keyword detect (rm -rf 등) STOP
4. 각 terminal complete 후 orchestrator merge → 사용자 1 보고
상세: [[multi-terminal-dispatcher]] skill SKILL.md + [[wiki/concepts/multi-agent-dispatch]] pattern.

## 5. Phase 4 — Verification

작업 종류별 검증:

| 작업 | 검증 명령 |
|---|---|
| Skill 수정 (SimonK-stack) | `python .claude/skills/skill-gen-agent/scripts/validate_skill.py skills-src/<name>` |
| Wiki 변경 (SimonKWiki) | wiki-lint 스킬 호출 또는 structural lint script |
| Code 변경 | repo의 test/lint 명령 (CLAUDE.md "검증 도구" 섹션) |
| Frontmatter 변경 | YAML safe_load 파싱 |
| Bash 스크립트 | `bash -n <file>` |

검증 실패 시:
- 1회 자동 재시도 (small fixes)
- 2회째 실패하면 사용자에게 보고 (block, no further push)

## 6. Phase 5 — Persistence (Full Auto)

```
1. git add -A
2. git -c commit.gpgsign=false commit -m "<conventional commit>"
   - feat(scope): for new features
   - fix(scope):  for bug fixes
   - docs(scope): for docs
   - chore(scope): for chores
   - 한국어 body OK
3. git push origin <branch>
4. wiki 변경분은 SimonK-stack Stop hook이 자동 처리 (action 불필요)
5. .simonk/log.md 에 1줄 append: `YYYY-MM-DD HH:MM | <op> | <files> | <outcome>`
```

## 7. Phase 6 — Final Report

응답 마지막은 항상 다음 포맷:

```markdown
## 완료 — <task summary>

### 작업
- <sub-task 1> → <one-line result>
- <sub-task 2> → <one-line result>

### 검증
- <test/lint command + result>

### Git
- <repo>: <commit hash> <subject> → push 0/0
- <repo>: ...

### 다음 (선택)
- <follow-up 1>
- <follow-up 2>
```

**자동 보고서 (default ON)**: Phase 6 텍스트 요약 직후 `/simonk-report` 를
자동 호출해 `.simonk/reports/<TS>.html` 생성 + `SendUserFile` 로 첨부 전송.
사용자가 모바일에서도 보고서를 받을 수 있게 함. 끄려면:
- 한 세션만: `SIMONK_REPORT=off simonK "..."`
- 영구: 프로젝트 `.envrc` 또는 shell profile 에 `SIMONK_REPORT=off`

자세한 보고서 schema 와 anti-pattern: [`skills-src/simonk-report/SKILL.md`](../simonk-report/SKILL.md)

## 8. When NOT to use simonk

- Trivial single edit / typo fix → just do it directly
- Pure info lookup ("what is X?") → Read/Grep 직접
- Conversational ("what do you think of Y?") → direct response
- Single-tool-call answer → Task delegation overkill

## 9. Integration with external/

simonk can REFERENCE (not vendor) external repos when needed:

- **OMC (`external/oh-my-claudecode/`)**: 더 강력한 multi-agent 필요 시 → 사용자에게 `/plugin marketplace add Yeachan-Heo/oh-my-claudecode` 한 줄 권장
- **OMO (`external/oh-my-openagent/`)**: model-agnostic 환경 필요 시 → reference
- **OpenHarness (`external/OpenHarness/`)**: Phase 6 폐쇄망 운영 시 → reference
- **anthropics/skills**: 공식 skill 추가 vendoring 필요 시 → cherry-pick

simonk는 위 외부 runtime 없이도 작동 (self-contained). 외부는 보강 도구.

## 10. Failure modes & recovery

| 시나리오 | 처리 |
|---|---|
| Ambiguity score 매번 < 6 | 사용자 입력이 일관되게 모호 — sprint 모드 강제 + plan.md 사용자 review 필수 |
| Task tool 호출 실패 | 1회 재시도 → 2회 실패면 fallback to sequential 단일 처리 |
| git push 실패 (네트워크/auth) | working tree commit 유지 · 1줄 보고 · 사용자에게 manual push 요청 |
| 파괴적 작업 감지 | 즉시 STOP · 명시 확인 · 백업 zip 권장 |
| 검증 실패 2회 | working tree commit X · 사용자에게 진단 보고 |

---

**호출 진입점:**
- PowerShell: `simonK <task>` (어디서든 호출 가능 · 사용자 profile에 등록됨 · case-insensitive)
- Claude Code 슬래시: `/simonK <task>` (interactive session 내)
- 둘 다 본 SKILL.md 실행
