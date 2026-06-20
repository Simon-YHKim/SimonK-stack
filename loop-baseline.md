---
title: 측정 기반 루프 — 운영 베이스라인 / 골든셋 / 실패 원장
created: 2026-06-13
last-updated: 2026-06-13
owner: claude (orchestrator)
related: PROTOCOL.md §12.1a, §18.0
---

# 측정 기반 루프 — 운영 베이스라인

> PROTOCOL §12.1a "측정 기반 루프 규칙"을 **실행 가능한 형태**로 내린 운영 문서.
> 자율 루프 재개 시 0단계 = 여기 골든셋으로 baseline 먼저 측정 → 한 번에 하나 변경 → 같은 골든셋 재측정 → 점수 상승/무회귀일 때만 채택. "측정 없는 진화는 금지."

## 1. 골든셋 (고정 시험지 — 바꾸면 점수 비교 무효)

| 시스템 | 베이스라인 명령 | 무엇을 잰다 |
|---|---|---|
| **2nd-B** (`E:\2ndB`) | `npm run verify` | lint + typecheck + jest (suites/tests/통과) |
| 2nd-B (UI/회귀) | `npm run web` + 스크린샷 / `npx expo run:android`(에뮬) + CDP `scrollWidth` | 가로스크롤·렌더·E2E 흐름 (정적 green ≠ E2E 통과) |
| 2nd-B (제약) | constraints / i18n / lexicon 스캔 | 금지어·번역누락·하드코딩 |
| 2nd-B (페르소나 UX §27.9) | `persona-cluster-sim` 워크플로 (12 페르소나, scriptPath 재실행) | 막힘/이탈/불신/오해 빈도·심각 — 개선 후 재실행해 감소 측정 |
| **SimonKWiki** (`E:\Coding Infra\obsidian\SimonKWiki`) | `wiki_lint.py` + `raw_isolation.py` | 깨진 링크·frontmatter·index 정합성 / raw 격리 |
| **Hub** (`E:\Coding Infra\AI Infra\Communication`) | `tools\board.ps1 -Me claude` | 메시지 frontmatter·status·cycle counter 정합성 |
| **Grok 리서치** (lane golden set §34.2) | `agents/grok/golden-set.md` 고정 질문셋 Q1–Q7 + 고정 소스 2-pass | 신호 재현성(2회 동일 결론)·유효 인사이트 N=5 채택 카운트·실패 lead는 §4 원장 |
| **Skill Stack** (`~/.claude/skills`) | `validate_skill.py` 전수 (`PYTHONIOENCODING=utf-8`) | simon-stack 0-error / Gstack는 E007 긴-doc 포맷 제외 |

## 2. 현재 베이스라인 (2026-06-13 측정, Codex 세션)

- **2nd-B `npm run verify`**: 129 suites / **1125 tests PASS**. lint = 0 errors / 4 existing unused-eslint-disable warnings. HEAD `f769d1d` (#367) == origin/main.
- **SimonKWiki `wiki_lint.py`**: Error=0 (E1=0, E2=0, W2/W3/W4/FM=0). `raw_isolation.py`: isolated=0/26. HEAD `53043ed`.
- **Hub**: CONTROL `state=paused` (의도), 1216 commits, dirty=0.

- **페르소나 UX baseline (2026-06-13, wf persona-cluster-sim, 12 페르소나)**: P1 막힘/이탈 테마 4종 = ① 가입 게이트 과중(9/12) ② 핵심 효용 불명확·은유 과잉(12/12) ③ 접근성 픽셀-다크 기본(6/12) ④ 첫 journal 게이트(4/12). 개선 머지 후 동일 워크플로 재실행 → 이 빈도가 감소해야 개선 인정. 큐: `agents/claude/PROPOSAL_QUEUE.md` E1~E8. 리포트: `E:\Coding Infra\2ndB-페르소나시뮬-findings.html`.

- **Skill Stack baseline (2026-06-13)**: 153 설치 스킬 중 simon-stack 전부 통과(`wiki-query` E013=YAML 콜론-공백 수정 후). 검증기 `validate_skill.py`의 cp949 크래시 + E008 "Todo-list" 오탐 수정 → SimonK-stack `4aacecd` 푸시. 잔여 51 = Gstack/벤더드(E007 긴-doc 포맷 41 + 벤더드 실결함·검증기 false-pos 10, 수정금지 영역). 재측정: `for d in ...; validate_skill.py $d`.

> 다음 루프 변경 전 이 표를 갱신 측정해 baseline으로 삼는다. 점수가 이보다 내려가면 그 변경은 회귀 → 반려.

## 3. 루프 규율 (요약 — 정본은 PROTOCOL §12.1a)

1. **baseline first** — 위 골든셋으로 현재 점수 먼저 기록.
2. **one change** — 한 사이클에 의미 있는 변경 1개. 여러 개면 독립 커밋/근거로 분리.
3. **same test** — 동일 골든셋으로 재측정.
4. **merge on measured gain** — 상승 또는 무회귀, 또는 명확한 위험감소가 증명될 때만 채택. "좋아 보임"은 근거 아님.
5. **separate judge** — 제안자 ≠ 채점자. 자기 산출 자기 채점만으로 done 금지(불가 시 같은 기준표+원시로그 outbox에).
6. **E2E human-on-loop** — 정적 green이어도 실사용 흐름 QA는 별도 증거 필요. AI가 직접 못 돌린 표면은 "검증됨" 아닌 **proof gap**으로 기록.

## 4. 실패 원장 (오답노트 — 같은 실패 재시도 방지)

> 점수가 안 오른/회귀한 변경은 버리지 말고 여기 1줄 남긴다. 재제안하려면 **새 baseline·새 증거**가 필요.
> 경량 연동: 반복실수는 `~/.claude/instincts/mistakes-learned.md`, 위키 교훈은 `concepts/recurring-mistakes.md`(M-코드)·`protocols/llm-wiki/LESSONS_LEARNED.md`(T-코드)로도 환류(§18.1).

| 날짜 | 시도한 변경 | baseline | 결과 | 채택? | 이유/재시도 조건 |
|---|---|---|---|---|---|
| _(시드)_ | — | — | — | — | 실패 시도를 여기 기록 |

## 5. Subtractive cycle 추적

- 추가형 개선 **3회마다 1회**는 삭제형 개선 검토(오래된 규칙·중복 게이트·효과 없는 체크 제거 → 점수 안 떨어지면 제거 확정).
- 추가 카운터: `0 / 3` (다음 subtractive 검토까지)
