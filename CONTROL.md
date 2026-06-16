---
owner: claude
note: "이 파일은 Claude(오케스트레이터)만 작성한다. 나머지 AI는 매 사이클 맨 앞에서 읽기만 한다."
state: running
pause_reason: "2026-06-16 Simon 지시: UI 완성 전까지 AI 허브 가동 중단, 잠시 휴식. Claude 디렉터 /loop 정지, 3 데몬(codex/grok/AG) 종료. watchdog는 paused라 자동재시작 안 함(§auto-restart는 running일 때만). 재개는 Simon이 UI 작업 후 'running' 복원 + 디렉터 루프 재가동."
resume_reason: "2026-06-17 Simon 지시: state running 복원. UI 작업 사이클 재개. 2nd-B 세계관 정본(북극성/7별/L1-L5/두뇌 0-3) Phase 0 글로사리 락 푸시/CI/머지 진행. 원격 오더 파이프라인 LIVE 유지. Simon 직접 재확인 2026-06-17 05:36 KST: state=running 명시 유지."
updated: 2026-06-17 05:36 KST
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
- **▶ RUNNING (2026-06-15)**: Simon "정상 가동" 지시로 재개. 각 AI는 자율 루프 재개(5분 §12.1, charter 한도 내). pause-ack 중이던 좌석은 다음 틱에 running 감지 후 작업 복귀.
- **원격 오더 채널 LIVE (§33)**: Simon이 모바일로 2nd-B `ORDERS.md`의 `## OPEN`에 오더 push → **Claude 라이브 루프가 매 사이클 git fetch 후 읽고, 담당 AI에 분배·수행 후 `## DONE`에 피드백 + commit/push**. hub-daemon이 죽어 Claude 인터랙티브 루프가 §33 폴러를 인계한다.
- **분배 라우팅(ROUTING.md)**: Claude=오케스트레이션·코딩·통합·git, Codex=UI/UX+구현, AG(agy-pty 헤드리스 부활)=네이티브/에뮬 QA, Grok=X·소비자 리서치. Claude가 오더 분해→담당 헤드리스 spawn→통합 보고.
- 게이트(§11-5): 파괴·실비용·secrets·안전임상·법무 오더만 수행 전 Simon 확인. 그 외 dev 오더 무확인 수행.

### 운용 규칙 = PROTOCOL 헌법 참조 (레이어 분리, 2026-06-07 B-7)
> **상시 규칙은 헌법(PROTOCOL)에 산다. CONTROL은 런-스테이트 신호일 뿐.** 아래는 포인터 — 본문은 PROTOCOL을 따른다.
- **루프 5분 케이던스** → §12.1 (정본). 사이클 간 5분 대기는 폴링이지 idle 아님(내부 유휴 금지).
- **실시각 타임스탬프 `[YYYY-MM-DD / HH:MM:SS KST]`** → §27.2 (Get-Date 실행, 추정 금지).
- **적극성 의무**(수동대기 금지·가치 기준) → §27.4. **별도공간→Claude 검토→결정** → §11.2·§10.5.
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
