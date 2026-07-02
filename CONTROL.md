---
owner: claude
note: "이 파일은 Claude(오케스트레이터)만 작성한다. 나머지 AI는 매 사이클 맨 앞에서 읽기만 한다."
state: running
pause_reason: "2026-06-18 Simon /goal: 데몬 정지 + 커밋 정리 + AI 가치 평가/개선. (2026-07-02 재개됨 — resume_reason 참조.)"
resume_reason: "2026-07-02 03:47 KST Simon /goal '남은 4개 진행' 승인 → 재개. 정리(INFRA-MAP 정본·13스킬 재배정 배포·SimonKStack repo 신설) + 외부지식 통합(dashboard-review·semantic-recall·model-router MoA·ROUTING-MOA §1.6 흡수) 완료. run-state=running 복원, BOARD/STATUS 정렬. 원격 오더 파이프라인 LIVE 유지."
updated: 2026-07-02 03:47 KST
---

# CONTROL.md — 런-스테이트 세마포어 (always-checked)

> **목적**: 4-AI가 무인 자율로 도는 동안 "전체 멈춤/재개"를 단일 신호로 통제한다.
> **규칙**: 모든 AI는 **자기 자율 루프의 맨 앞에서 이 파일의 `state:`를 읽는다.** Claude만 쓴다(single-writer).

## 상태 값
| state | 의미 | 각 AI 행동 |
|---|---|---|
| `running` | 정상 가동 | 자율 루프 계속 (charter 한도 내) |
| `paused` | 일시정지 | **진행 중인 사이클 1개까지만 완료** → `agents/<me>/STATUS.md`에 `state: paused` + pause-ack 기록 → 대기. 새 사이클 시작 금지 |
| `draining` | 정리 종료 | 진행 중 작업만 마무리, 신규 발의 금지, 완료 후 idle |

## 일시정지 프로토콜 (PROTOCOL §13)
1. 사용자가 Claude에게 "일시정지/멈춰/pause" → Claude가 이 파일 `state: paused` + `pause_reason` + `updated` 갱신 후 커밋·푸시.
2. 각 AI는 다음 루프 진입 시 `paused` 감지 → **현재 사이클만 마무리** → STATUS에 `state: paused` 기록 → 대기(폴링 간격 늘림).
3. 재개: Claude가 `state: running` 복원 → 각 AI 재진입.

## 현재 지시(broadcast) — Claude가 갱신
- **▶ RUNNING (2026-07-03 감사 후 정비 완료)**: 데몬 = codex 레인(+AG 레인 ConPTY 픽스 후 재기동, `AGY_USE_CONPTY=0`) · **grok은 기본레인 제외**(ROUTING §4 요청전용, directed request 시 `-Only grok` 옵트인) · HubWatchdog(10분)이 죽은 레인 오토리스타트 + ORDERS 채널 감시.
- **원격 오더 채널 (§33) — 소비자 주의**: 채널 소비자는 **살아있는 Claude /loop 디렉터 세션**이다(세션 종료=채널 정지, 06-21~07-03 12일 무소비 사고). Simon이 오더를 넣었는데 픽업이 없으면 watchdog이 `orders-unconsumed` 노트를 Claude inbox에 자동 기록한다. 디렉터 세션은 `tools/orders-poll.ps1 -Json -Heartbeat`로 폴링 + `-Ack <id>`로 픽업 기록.
- **분배 라우팅(ROUTING.md)**: Claude=오케스트레이션·코딩·통합·git, Codex=UI/UX+구현, AG=네이티브/에뮬 QA(+패치 제안), Grok=X·소비자 리서치(요청기반). 고위험 산출물은 MoA 교차검증(ROUTING-MOA §3).
- **모델 정본**: claude=`claude-fable-5`@max(07-03 재핀) · codex=gpt-5.5@medium · grok=grok-build@high · AG=gemini-3.1-pro-preview@high. 기계본 `tools/models.json`.
- 게이트(§11-5): 파괴·실비용·secrets·안전임상·법무 오더만 수행 전 Simon 확인. 그 외 dev 오더 무확인 수행.
- 상시 규칙 포인터: 별도공간→Claude 검토→결정 → **§11 #2**·§10.5.

### 운용 규칙 = PROTOCOL 헌법 참조 (레이어 분리, 2026-06-07 B-7)
> **상시 규칙은 헌법(PROTOCOL)에 산다. CONTROL은 런-스테이트 신호일 뿐.** 아래는 포인터 — 본문은 PROTOCOL을 따른다.
- **루프 5분 케이던스** → §12.1 (정본). 사이클 간 5분 대기는 폴링이지 idle 아님(내부 유휴 금지).
- **실시각 타임스탬프 `[YYYY-MM-DD / HH:MM:SS KST]`** → §27.2 (Get-Date 실행, 추정 금지).
- **적극성 의무**(수동대기 금지·가치 기준) → §27.4. **별도공간→Claude 검토→결정** → §11 #2·§10.5.
- **사용자 권한 = 4-AI 합의(§14)**, 예외 ①비용 ②파괴적 ③secrets만 Simon(§11-5·§15).
- **운용 강화 10규칙** → §27. **운영안전·인코딩** → §28. **디자인-우선·카피** → §29. **수익화 지향** → §30. **반-퇴화·성실도** → §31.
- 우선순위: 런치차단(외부의존) > P1 > P2 > P3. 온라인 git은 Claude 단독.

## 변경 로그 (append-only)
- 2026-06-06 12:30 KST | CREATE | CONTROL.md 신설, state=running, B-모델 자율운용 개시 | claude
- 2026-06-07 07:40 KST | PAUSE | Simon "하던일까지만 하고 일시정지". 최종 머지 30dc939까지 완료 후 정지. 각 AI 현재 사이클 마무리 후 대기 | claude
- 2026-06-07 07:59 KST | RESUME | Simon "허브 구동" 지시 → state=running 복원. 4-AI 재가동(activate 프롬프트 재배포) | claude
- 2026-06-08 23:24 KST | PAUSE | Simon "다른 AI 가동 중단 + 인프라 이전 준비". 회고 인터뷰 수집 후 정지. 외장하드 이전/타 랩탑 클론 예정. 재개는 새 환경에서 Claude가 경로 확인 후 | claude
- 2026-06-15 03:25 KST | RESUME | Simon "정상 가동 시키자" → state=running 복원. Claude 라이브 ScheduleWakeup 루프가 §33 ORDERS 폴러+분배자 인계(hub-daemon no PID). 원격 오더 파이프라인 LIVE. AG=agy-pty ConPTY 헤드리스 부활 | claude
- 2026-06-16 ~ KST | PAUSE | Simon "UI 완성 전까지 AI 허브 가동 중단" → state=paused. (frontmatter pause_reason 참조)
- 2026-06-17 05:21 KST | RESUME | Simon "CONTROL state running으로 수정" 지시 → state=running 복원. 2nd-B Phase 0(세계관 정본 글로사리: 북극성=Soul Core / 7 자기이해 별 / L1-L5 가치 사다리 / 두뇌 0-3 다리 모델) CONTEXT.md 락 + worldview-naming 테스트 핀 → 푸시/CI/머지 사이클 진행. 원격 오더 파이프라인 LIVE 유지. | claude
- 2026-06-18 ~ KST | PAUSE | Simon /goal: 데몬 정지 + 커밋 정리 + AI 가치 평가/개선 → state=paused. (frontmatter pause_reason — 본 로그 소급 기록 07-03) | claude
- 2026-07-02 03:47 KST | RESUME | Simon '남은 4개 진행' 승인 → state=running 복원. INFRA-MAP 정본·13스킬 재배정·SimonKStack 신설·외부지식 통합(dashboard-review·semantic-recall·MoA) 완료. (frontmatter resume_reason — 본 로그 소급 기록 07-03) | claude
- 2026-07-03 01:20 KST | AUDIT | 허브 전수 감사·정비: stale open 89건 배치클로즈, codex 브랜치 하이재킹 복구(206커밋 master ff)+브랜치 가드(commit.ps1/데몬 self-heal/watchdog), claude=fable-5 재핀, AG ConPTY 근본원인 픽스(AGY_USE_CONPTY=0, 검증 PONG), 데몬 no-op 무커밋+MoA verify 훅, grok 기본레인 제외, ORDERS 채널 12일 무소비 발견→watchdog 감시+하트비트+ack 도입, HubModelBenchmarkRefresh 재등록, 문서 4-AI 정합. 상세 Output/hub-audit-20260703.html | claude
