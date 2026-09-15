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
