# D-28 — 라우팅 개정 1단계 (2026-09-16)

> Simon 확정 2026-09-16 (16건 전부 심판안). 토론 원문: `E:\Coding Infra\reports\vibe-d28-debate-260913\judge-verdict.md`
> · 허브 `DECISIONS.md` 2026-09-13 23:19 D-28 · 2026-09-16 00:55 RATIFY.

## 왜

- **4벤더가 사실상 2벤더였다.** grok 402(잔액 소진) · gemini 는 Orca 워커로 과제를 못 받는다(재현 2/2 · T4 exit 15).
- **치명 결함 하나.** B 1순위를 codex(astra)로 두면 코딩도 codex 로 가고, 두 보안 게이트도 codex 라 G1 —
  `validate_plan` 이 `(False, ['G1'])` 로 코딩 라운드 전체를 막는다. 현행 배정도 claude 60% 초과 강등이나
  탐색 슬롯이 코딩을 고르면 같은 결함이 났다(음성대조 N1~N3).
- 강등이 1순위에만 걸리고, 실호출 결과·fable 버킷을 보지 않았다(N6).

## 1단계에서 바뀐 것

| # | 내용 | 코드 |
|---|---|---|
| #5 | 코딩은 `PROCESS_LANES["coding"] = [claude-opus-5]` — codex 폴백 없음. 비코딩 B = astra → opus | `routing.PROCESS_LANES` · `lanes_for_proc` · `validate_plan` `CODING_LANE_NOT_ALLOWED` |
| #14 | 게이트 벤더 사용 금지면 코딩 없는 라운드로 축소 · 재시도도 재검증 | `validate_plan(quota_states=)` `GATE_VENDOR_BLOCKED` · `revalidate_for_retry` · G13 |
| #13 | 강등을 전 순위에(ok 없으면 첫 강등 레인) · `quota_bucket`(fableWeekly) · 실호출 실패=blocked, 24h 초과=미확인 | `make_intake.lane_state_for` · `pick_default` · `read_live` |
| #12 | gemini `dispatch: "unavailable"`(새 문자열 금지) · 탐색 후보는 2순위가 뜨고 실호출 통과한 공정만 | `routing.explore_candidates` · `EXPLORE_EXCLUDE += coding` |
| #7 | C-platform = gemini → sol → opus (오늘 기본 sol) | `CLASS_LANES` |
| #6 | C-realtime = grok → sol → opus · 코디네이터 겸임 경고 클래스 무관 | `coordinator_conflict` |
| #3 | A = luna → opus (sonnet 은 M1 후) | `CLASS_LANES` |
| #11 | 반증 "예"인 A 작업 → B 비코딩 목록으로 임시 승격(A-verify 전) | `lanes_for_proc(falsifiable=True)` |
| #8 | 코디네이터 sol@ultra → sol@xhigh | `COORDINATOR` |
| #9 | terra 사다리 medium/high → medium/max | `LANES["gpt-5.6-terra"]` |
| #15 | 결정 시트 없는 라운드는 미완료 | G14 |
| #16 | 드리프트 3건(sol 설명 · ctx 272K · config 기본 sol@xhigh) | 주석·표 |
| #10 | **보류** — luna 사다리 low/medium 유지(M4 후 재심) | — |

## 2단계 — 선행 계측 뒤

| 계측 | 대상 | 완료 조건 |
|---|---|---|
| M1 실워커 1회(sonnet·fable) | #1 #2 #3 #4 #5 | 새 run·task, `--timeout-ms 300000`, `turnStart: observed` → worker_done + 산출물 회수 + 모델 확인. 저장소 범위는 Q-260913-07(fable 30일 보존) |
| M2 fableWeekly 독립성 | #13② · Q-10 | M1 전후 `orca account list` 에서 claude weekly 와 fableWeekly 가 따로 움직이는지 |
| M3 grok 새 계정 | #6 | `adversarial_eval.py --preflight` 에서 402 해소 |
| M6 gemini `--timeout-ms` | #12 해제 | 새 task 로 `turnStart: observed` + worker_done |

- 편입 순서: sonnet → A 2순위(luna → sonnet → opus) · fable → 코딩 2순위 · B 비코딩 2순위 · A-verify 2순위
- A-verify(#4)는 스키마 커밋(VALID_CLASSES·폼·탐색 후보·claim-verify·selftest)과 순위 커밋을 나눈다 — 원장 class 값은 되돌리기 어렵다(Q-260913-08)
- 되돌릴 때는 LANES 에서 지우지 말고 목록에서만 뺀다 — 지우면 원장 행이 손상 판정을 받는다

## 3단계 — 데이터 뒤

- M4 판정형 적대평가 2회차 → #10 재심 · Q-260913-10(fable 순서 상향)
- M5 결정 시트 rated 5회 이상 → 스왑 규칙 가동

## 미결 질문 (Simon)

Q-260913-01 grok 새 계정 충전 · 05 codex 60% 경계 게이트 몫 · 06 거울 배치 비상안(D-260904-01 재개) ·
07 fable 30일 보존 허용 저장소 · 08 A-verify 원장 class 영구 확장 · 09 파일 바꾸는 터미널·대조 작업의 coding 재분류 ·
10 계측 뒤 fable 순서 상향

## 2단계 진행 기록 (2026-09-16)

- **M1 통과** — `run_c0c4a6905e26`. 첫 시도 2건은 SimonK-stack 폴더가 Claude Code 신뢰 안 됨이라 신뢰 창에 과제가 먹혀 실패(→ `references/pitfalls.md`).
  신뢰된 코디네이터 폴더(`--worktree current`)에서 재기동 → `claude.exe --model claude-fable-5-1 --effort high` · `--model claude-sonnet-5 --effort medium` 확인 ·
  읽기 전용 과제(HEAD · SKILL.md version · scripts/*.py 개수) 정답 3/3 둘 다 · `worker_done` · `filesModified: []` · 자기보고 모델 일치.
- **M2 판정 불가** — 워커 2개 전후 claude weekly 62→62 · session 17→18 · fableWeekly 0→0. 정수 %가 움직이지 않아 독립 여부를 못 갈랐다.
  → fable 상태는 **fableWeekly 와 claude 일반 한도 중 더 나쁜 쪽**으로 판정한다(`make_intake.lane_state_for`). 독립이 확인되면 푼다.
- **편입** — `claude-sonnet-5` 레인 신설(사다리 medium/xhigh) · A = luna → sonnet → opus · 코딩 = opus → fable · B 비코딩 = astra → fable → opus.
- **보류** — #4 A-verify 스키마 · #11 본 규칙 (Q-260913-08). R1 임시 승격(B 비코딩 목록)은 그대로다.

## A-verify (Q-260913-08 승인 2026-09-16)

- **스키마 커밋**: `ledger.VALID_CLASSES` 에 `A-verify` · 공정 `claim-verify`(읽기 전용) · 클래스 라벨 · 폼 반복문 · 탐색 후보 클래스 ·
  `validate_plan` 에 `A_VERIFY_WRITES`(계획에 `writes: true` 면 coding 으로 재분류하라고 막는다) · selftest.
- **순위 커밋**: `CLASS_LANES["A-verify"] = astra → fable → opus` · #11 본 규칙(반증 "예"인 A 작업 → A-verify).
- 되돌릴 때는 `VALID_CLASSES` 에서 빼지 말고 `CLASS_LANES` 에서만 뺀다 — 이미 쓰인 원장 행이 손상 판정을 받는다.

## 남은 결정 회신 (2026-09-16 04:19 · 허브 DECISIONS.md)

| 질문 | 결정 | 반영 |
|---|---|---|
| Q-260913-01 grok | A — 새 계정 로그인 후 실호출 확인까지만, 충전은 402일 때 재질문 (grok usage 토 11:30경 리셋 — Simon) | 코드 변경 없음 |
| Q-260913-05 게이트 몫 | Simon 미선택 → Claude 판단: 강등 60→**80% 초과** · 금지 85→**100% 도달**·실호출 실패 · 한도로 실패·정지한 워커만 `handoff_spec` 으로 인수인계 | `QUOTA_DEMOTE/BLOCK` · `make_intake.lane_state` · `routing.handoff_spec` · G4 |
| Q-260913-06 거울 배치 | C — 모델 장애 대비 비상 절차로만 문서화(아래) | 문서 |
| Q-260913-09 파일 쓰는 작업 | A — 계획에 `writes: true` 인 공정은 전부 코딩 규칙(코딩 레인·G1·보안 게이트 필수) | `check_guards` · `validate_plan` · `lanes_for_proc(writes=)` |
| Q-260913-10 fable 순서 | A — M2 뒤 재논의(보류) | 없음 |

**Q-05 에서 채택하지 않은 것**: 상시 모니터링 데몬 · 80% 에서 실행 중 워커 선제 교체. 불변 가드 G4(쿼터로 실행 중 워커를
멈추지 않는다)와 "데몬·상시 폴링을 만들지 않는다"에 정면으로 걸린다(최고 품질 워커 오사살 · 03:00 쿼터 0% 오독 실적).
바꾸려면 Simon 의 명시 결정이 필요하다.

**인수인계 절차 (G4 안에서)**: 코디네이터의 수확 루프(`check --wait`)에서 워커가 한도 신호(worker_done 실패 사유 ·
`worker-read` 끝부분의 한도 메시지 · 429/402)로 실패·정지한 것이 보이면 → `worker-read --source auto` 끝부분과
`git status` 로 바뀐 파일을 모은다 → `routing.handoff_spec(원 과제, 사유, from, to, 끝부분, 파일)` → 여유 레인으로
`revalidate_for_retry` 통과 확인(G13) → **새 task** 로 띄운다(실패한 task 는 재디스패치가 안 된다).

## 거울 배치 — 모델 장애 대비 비상 절차 (Q-260913-06 = C)

- **무엇**: 코딩 = codex(`gpt-6-astra` 또는 `gpt-5.6-sol`) · 보안 게이트 2개 = claude 의 서로 다른 두 모델(`claude-opus-5` · `claude-fable-5-1`).
- **언제만 쓰나**: 쿼터가 아니라 **특정 모델**이 막혔을 때 — daybreak(보안 전용) 장애 · Trusted Access 해제 · astra 장애 등.
- **쿼터 대책이 아니다**: 판단 벤더가 claude·codex 둘뿐이라, 어느 벤더가 한도에 닿아도 현행이든 거울 배치든 코딩과 게이트 중 한쪽이 멈춘다.
- **비용**: daybreak 보안 전용 모델·Trusted Access 경로를 잃는다 · 종합(D)과 게이트가 같은 claude 벤더가 된다 · fable 게이트는 보안 요청에서 refusal 가능성(추정).
- **코드 기본값에는 넣지 않는다**: `PROCESS_LANES["coding"]` 은 claude 전용 그대로다. 쓰려면 그 라운드에 한해 계획을 사람이 바꾸고 `validate_plan` 을 통과시킨다(고정 게이트를 바꾸므로 `FIXED_LANE_OVERRIDDEN` 이 뜬다 — 비상 사용 사유를 원장에 남긴다).
