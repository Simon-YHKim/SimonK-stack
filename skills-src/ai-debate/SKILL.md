---
name: ai-debate
description: Use when a decision is important, contested or irreversible, or when an agent has been handling one task too long and needs a mid-course challenge — triggers "토론 붙여", "다관점으로 결정", "이거 합의 보자", "찬반 검토", "AI들끼리 토론", "겐세이", "중간 점검", "너무 오래 걸려", "debate this", "interject", or /ai-debate. MANDATORY for PROTOCOL §35.1 triggers. Always seats all four vendors — Claude, Codex (OpenAI), Grok (xAI) and Gemini (Google, via the Antigravity agy CLI) — through scripts/debate.py at $0 extra cost; an unreachable seat is recorded as absent with evidence and must catch up later, never simulated by another vendor. Runs positions, cross-examination, a blind separate judge and ratification, then Produces a D-code entry in the hub DECISIONS.md; interject mode Produces a 겐세이 card.md for the running agent.
version: 0.2.1
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Agent
compatibility:
  - claude-code
---

# AI Debate — 4개 벤더 구조적 토론 + 겐세이

중요하거나 엇갈리거나 되돌릴 수 없는 결정을 혼자 내리지 않고, **Claude·Codex·Grok·Gemini 네 벤더가 실제로 참여한 토론**으로 내린다. 또 한 에이전트가 같은 일을 너무 오래 붙잡고 있으면 다른 벤더들이 중간에 끼어들어(겐세이) 경로를 바로잡는다. PROTOCOL **§35(구조적 토론 게이트)** 의 실행형이며 §14(합의)·§34.4(별도 심판)를 묶는다.

## 불변 규칙

1. **4개 벤더 전원 착석.** 좌석은 Claude(Anthropic) · Codex(OpenAI) · Grok(xAI) · Gemini(Google, Antigravity `agy`) 넷이다. 한 벤더가 다른 벤더 좌석을 흉내 내면 토론이 아니다. "Codex 내부 패널", "Claude 서브에이전트 4명"은 토론 기록으로 인정하지 않는다. `submit`은 오케스트레이터 벤더의 세션 내 답만 받는다. 다른 좌석은 반드시 `call`로 실제 CLI를 부른다.
2. **추가 과금 $0.** 구독 포함 사용량만 쓴다. `debate.py`가 좌석 호출 직전에 쿼터 증거를 다시 읽고, 소진됐거나 구매 크레딧이 청구될 상황이면 호출하지 않고 결석으로 기록한다. 헤드리스 `claude -p`는 별도 헤드리스 크레딧을 쓰고 로컬에서 확인할 수 없으므로 기본 UNKNOWN이다. Simon이 그 과금을 허락한 경우에만 `--accept-unknown`으로 부른다. 결제·자동충전 설정은 건드리지 않는다.
3. **결석은 기록하고, 나중에 합류시킨다.** 착석 4/4 = `FINAL`. 2~3개 = `PROVISIONAL`: 되돌릴 수 있는 일만 진행하고, 결석 벤더가 돌아오면 catch-up 표결이 의무다. 출석 + catch-up ACCEPT가 4가 되면 `FINAL`(via catch-up)로 올라간다. 1개 이하 = `INVALID`: §35 게이트로 쓸 수 없다(기다리거나 Simon에게).
4. **심판은 블라인드·별도 호출.** 입장은 P1..Pn으로 익명화하고, 안건을 올린 오케스트레이터와 **다른 벤더**가 새 세션에서 판정한다. 심판 벤더의 R1 입장도 익명 입장 안에 들어갈 수 있다. 프롬프트가 이를 밝히고 작성자 추측을 금하며, `meta.json`에 `judge_wrote_position`이 남는다. 다른 벤더가 없으면 오케스트레이터 벤더가 새 세션에서 판정하고 `same-vendor`로 표시한다.
5. **안전 레일은 토론이 정하지 않는다.** §11-5(파괴·비용·시크릿·임상·법무)는 토론이 근거를 만들고 Simon이 결정한다.

## 언제 쓰나 (필수 트리거)

| 트리거 | 예 |
|---|---|
| ① 설계·아키텍처·네이밍 | UI 방향, 스택/DB 선택, 앱·기능 명명, 정보위계 |
| ② AI·에이전트 충돌 | findings/verdict가 엇갈림, 공유-전제 위양성 의심 |
| ③ 중요·비가역 | main 머지, 스키마, 수익화/가격, 권한 모델, 대량 삭제, 라이브 배포·사용자 홈 설치 |
| ④ 저신뢰·고영향 | 불확실 + 영향 큼 (보안·법무·임상 표현 — 최종은 Simon) |
| ⑤ 겐세이 | 한 에이전트가 45분 넘게 사용자에게 보이는 결과 없이 같은 목표를 붙잡음, HOLD·보류 반복, 사용자가 "왜 이렇게 오래 걸려"라고 함 |

사소하거나 되돌리기 쉬운 일, 답이 하나뿐인 일에는 쓰지 않는다.

## 좌석

| 좌석 | 호출 | 착석 전 증거 (모델 호출 없음) |
|---|---|---|
| Claude | Claude Code가 오케스트레이터면 **세션 안 서브에이전트**(Agent/Workflow)로 답을 받아 `submit`. 다른 호스트면 `claude -p` (safe-mode, 도구 끔). 기본 UNKNOWN, `--accept-unknown`일 때만 | AI Usage Widget 브리지의 5시간·7일 사용률(6시간 안 기록). 사용률이 기준 이상이면 ABSENT |
| Codex | `codex exec --sandbox read-only --ignore-user-config`, 프롬프트는 stdin | 최신 rollout의 `token_count.rate_limits` (used_percent, resets_at, credits) |
| Grok | `grok --prompt-file ... --sandbox read-only --tools ""` | `~/.grok/logs/unified.jsonl`의 billing 기록 (creditUsagePercent, 주기 종료) |
| Gemini | `agy --print ... --mode plan --sandbox --output-format json` | 무턴 `/usage` 조회의 Gemini 그룹 주간·5시간 버킷 remaining_fraction |

호출 형식·실패 문구·결석 처리·환경변수 제거 목록은 `references/seats.md`. 쿼터가 리셋되면 같은 명령이 자동으로 착석시킨다(통로는 항상 열어 둔다).

## 결정 토론 절차

아래 `<skill>`은 이 스킬 폴더, `<id>`는 `new`가 돌려준 토론 ID다. 모든 명령은 `python -B <skill>/scripts/debate.py ...`로 실행한다. 종료 코드는 0 성공 · 2 사용 오류·거부 · 3 결석(쿼터·준비 안 됨) · 4 실패다.

1. **좌석 확인.** `debate.py seats --orchestrator anthropic` 결과를 사용자에게 한 줄로 보여 준다(예: `Claude ✓ · Codex ✗(쿼터 100%, 10-07 09:03 리셋) · Grok ✗(402) · Gemini ✓`).
2. **안건 세우기.** 질문 하나(2000자 이하) + 선택지(각 300자 이하, 10개까지) + 판정 기준(같은 제한) + 실제 증거(UTF-8 파일, 16KB 이하)를 만든다. 증거 없이 논쟁시키지 않는다. 증거 속 키·토큰 모양 문자열은 저장 전에 가려진다(`redacted` 개수).
   `debate.py new --title "<제목>" --question "<질문>" --option "<A>" --option "<B>" --criterion "<기준>" --evidence-file <증거.md>`
   `--mode`의 기본값은 `quick`이다. ③ 비가역 결정은 `--mode full`. 벤더마다 렌즈(찬성·회의·대안·사용자 이익)가 토론 ID 기준으로 돌아가며 배정된다.
3. **R1 입장.** `debate.py prompt --id <id> --round r1` 후, 착석 가능한 외부 좌석마다 `debate.py call --id <id> --round r1 --vendor openai|xai|google` 를 **병렬**(백그라운드)로 실행한다. `call`은 항상 현재 입력으로 프롬프트를 다시 만든다. 같은 좌석의 `call`이 이미 돌고 있으면 두 번째는 종료 코드 2로 거부된다. Claude 좌석은 `rounds/r1/anthropic.prompt.md`를 서브에이전트에게 그대로 주고, 답을 파일로 저장해 `debate.py submit --id <id> --round r1 --vendor anthropic --file <답.md>`.
4. **R2 교차검증** (`full` 모드). R1이 모두 끝난 뒤 `--round r2`로 같은 방식을 쓴다. 각 좌석은 다른 입장의 가장 강한 논점을 반박하고 `UNCHANGED` 또는 `REVISED`를 밝히며, 공유된 숨은 전제를 드러낸다. 프롬프트를 만든 뒤 다른 입장이 새로 들어오면 `submit`이 "re-run prompt"로 거부한다. 그때는 `prompt`를 다시 돌리고 새 파일로 답한다.
5. **블라인드 심판.** `debate.py judge-pick --id <id>`는 ID로 정한 순번에서 오케스트레이터(겐세이면 대상 벤더도)를 빼고 첫 READY 벤더를 고른다. UNKNOWN 좌석은 `--accept-unknown`을 줄 때만 후보가 된다.
   - 고른 벤더가 외부 좌석이면 `debate.py call --id <id> --round judge --vendor <벤더>`.
   - `same-vendor`로 오케스트레이터가 뽑히면 `debate.py prompt --id <id> --round judge --vendor anthropic` 후 **새** 서브에이전트에게 맡기고 `submit --round judge`.
   - 심판 답의 첫 줄은 `VERDICT:`, 둘째 줄은 `CONFIDENCE:`이고, 패자가 진 이유와 보존할 소수의견을 쓴다.
   - `VERDICT:`가 없거나 심판이 본 입장 수가 출석 수와 다르면 판정이 무효다(`status`의 `judge.issues`). 심판이 답한 뒤에는 `r1`·`r2`가 닫힌다. 늦게 돌아온 벤더는 catch-up으로 합류한다.
6. **비준** (`full` 모드, ③ 비가역). `debate.py prompt --id <id> --round ratify`는 심판 벤더를 포함해 착석한 모든 좌석의 프롬프트를 만든다. 각 좌석은 `call`(Claude는 `submit`)로 첫 줄에 `ACCEPT` 또는 `OBJECT: <차단 사유>`를 낸다.
   - 첫 줄이 ACCEPT/OBJECT로 시작하지 않는 답은 "판독 불가"로 남고 FINAL을 막는다. 그 좌석에 다시 받는다(`.md`·`.meta.json`을 지우고 재호출).
   - **OBJECT 1건**: Claude가 근거를 적어 타이브레이크한다. `debate.py record --id <id> --tiebreak "<근거>"`. 근거는 `tiebreak.json`과 기록에 남는다. 이미 7단계로 기록했다면 `debate.py record --id <id> --amend`로 덧붙인다.
   - **OBJECT 2건 이상**: 새 토론으로 다시 연다. `debate.py new --reopen-of <id> --evidence-file <새 증거.md>`(증거 파일은 선택)는 안건을 복사하고 이전 기록을 증거에 붙인다. 16KB를 넘으면 이전 증거부터 줄인다. 새 토론에서 3단계부터 다시 한다.
   - 안전 레일 사안은 Simon이 정한다.
7. **기록.** `debate.py status --id <id>`로 FINAL/PROVISIONAL/INVALID와 `blocked`·`unresolved`를 확인한다. 그다음 `debate.py record --id <id> --decisions "E:/Coding Infra/AI Infra/Communication/DECISIONS.md" --append`.
   - D-code는 `| DECIDE | **D-n` 또는 `### D-n` 머리 줄만 세어 정한다. 지정된 D-code와 경로는 `record.json`에 남는다.
   - 같은 토론의 두 번째 `--append`는 거부된다.
   - INVALID이거나 유효한 심판 판정이 없는 토론은 거부된다. 정말 남겨야 하면 `--force`를 주며, 기록에 `⚠ 강제 기록`이 붙는다.
   - 이 D-code를 PR·머지·스펙에 링크한다.
8. **catch-up.** 세션을 시작할 때와 PROVISIONAL 판정 위에서 머지하기 전에 `debate.py catchup`을 돌린다.
   - 돌아온 벤더마다 출력된 명령 `debate.py prompt --id <id> --round catchup --vendor <벤더>`와 `debate.py call --id <id> --round catchup --vendor <벤더>`를 실행한다. 오케스트레이터 벤더면 `call` 대신 `submit`이다.
   - 그다음 `debate.py record --id <id> --amend`로 같은 D-code에 AMEND 줄 하나를 덧붙인다(기존 줄은 고치지 않는다).
   - catch-up OBJECT는 6단계와 같은 규칙(1건 타이브레이크, 2건 이상 재토론)을 따른다.

모드: `quick`(R1+심판, 최대 5회 호출)이 기본값이며 되돌릴 수 있는 결정에 쓴다. `full`(R1+R2+심판+비준, 최대 13회)은 ③ 비가역 결정에 쓴다.

## 겐세이 모드 (중간 개입)

오래 걸리는 작업은 대개 같은 게이트를 맴돈다. 네 좌석이 짧게 끼어들어 "계속·범위 축소·지금 내보내기·중단·사용자에게 묻기" 중 하나를 고르게 한다. 작업 중인 에이전트의 벤더도 **새 세션**으로 앉지만 심판은 맡지 않는다.

**감지 신호** (모두 턴이 열려 있을 때만) — `T1` 열린 턴이 45분 이상 · `T2` 최근 60분 안에 HOLD/NO-GO/보류/재판정 메시지 3번 이상 · `T3` 최근 사용자 메시지에 "오래 걸려", "왜 이렇게", "답답" 등 · `T4` 사용자가 "멈춰/그만해"라고 한 지 5분이 지났는데 턴이 계속 돎 · `T5` 작업 중인 벤더의 쿼터 100% · `T6` 같은 목표가 120분 넘게 진행 중. 이미 닫힌 턴이나 30분 넘게 기록이 없는 턴(`stale`)에는 권고하지 않는다. 사용자가 멈추라고 해서 끝난 세션에 다시 입력하지 않는다.

1. **감지.** `python -B <skill>/scripts/interject_scan.py scan --hours 12 --threshold-min 45` (Codex rollout과 Claude Code 기록을 읽기만 한다). 주기 점검이면 `--fail-on-trigger`로 종료 코드 10을 받는다.
2. **스냅샷.** `interject_scan.py snapshot --file <세션.jsonl> --out <증거.md>` — 목표, 경과 시간, 쿼터, 최근 사용자·에이전트 메시지를 6000자 안으로 줄인다.
3. **토론.** 다음 명령으로 연다(대상 벤더는 anthropic, openai, xai, google 중 하나). 그다음 네 좌석 R1과 블라인드 심판을 결정 토론 3·5단계처럼 진행한다. `judge-pick`이 대상 벤더를 건너뛴다.
   `debate.py new --mode interject --subject-vendor <작업 중인 벤더> --title "겐세이: <에이전트> <목표>" --question "지금 경로를 계속할 것인가?" --option CONTINUE --option RESCOPE --option SHIP_NOW --option STOP --option ASK_USER --criterion "사용자 목표까지 최단 경로" --criterion "추가 과금 0" --evidence-file <증거.md>`
   각 답의 첫 줄은 `CALL:`이다(`**CALL**:`·`SHIP NOW`·`ASK USER` 표기도 읽는다). 이어서 "지금 자를 것", "다음 한 걸음(행동 하나)", "시간 상자"를 쓴다.
4. **전달.** `debate.py deliver --id <id>`가 `card.md`(12줄 이하, 제어·양방향 문자 제거)를 만든다.
   - 실행 중인 Orca 터미널에 한 줄로 넣으려면 `--orca-terminal <핸들> --send`. orca가 `.cmd`/`.bat` 래퍼로만 잡히면 전송을 거부한다.
   - 카드는 항상 Simon에게도 보여 준다. 에이전트를 강제로 끊거나 죽이지 않는다.
   - 착석한 벤더 셋 이상이 `STOP`이면 카드에 `⚠ STOP n/m — Simon에게 일시정지 권고` 줄이 붙는다. 그대로 Simon에게 일시정지를 권한다.

**자기 자신에게도 적용한다.** 오케스트레이터가 같은 목표에서 45분 넘게 사용자에게 보이는 결과를 못 냈다면 스스로 겐세이를 요청한다.

## DECISIONS.md 기록 형식 (허브 실제 형식)

```
- 2026-10-01 20:15:00 KST | DECIDE | **D-53 <제목>** (§35 4벤더 토론 · PROVISIONAL 2/4) | claude
  - **안건**: <질문 + 선택지>
  - **참석**: Claude ✓(claude-opus-5-5, 세션 내) · Codex ✗(쿼터 100% ~10-07 09:03 KST) · Grok ✗(402 ~10-03 23:12 KST) · Gemini ✓(gemini-3.1-pro-high)
  - **입장**: Claude[회의]: ... · Gemini[찬성]: ...
  - **교차검증**: <UNCHANGED/REVISED 요약 또는 quick 모드 생략>
  - **심판**: Gemini (블라인드·새 세션·자기 벤더 입장 포함) — VERDICT: ... · CONFIDENCE ...
  - **소수의견**: <지우지 않는다>
  - **후속**: <조치 + 결석 벤더 catch-up 의무>
  - **원문**: <토론 폴더>
- 2026-10-03 09:10:00 KST | AMEND | **D-53 <제목>** — catch-up: Codex ACCEPT · 상태 PROVISIONAL 2/4 | claude
```

- 끝의 `| claude`는 오케스트레이터 벤더(claude·codex·grok·gemini)다.
- catch-up 결과와 타이브레이크가 있으면 본문에 `**catch-up**:`·`**타이브레이크**:` 줄이 더해진다.
- `record --append`·`--amend`는 기존 바이트를 다시 쓰지 않고 끝에만 붙이며, 파일의 줄바꿈 형식을 따른다.

## 검증 — "끝났다"의 조건

- `status`가 k/4를 보여 주고, 착석한 좌석마다 `meta.json`에 실제 호출 증거(CLI, 모델, 종료 코드, 시각, 작업 폴더)가 있다. `submit`된 답은 오케스트레이터 벤더 하나뿐이다.
- 심판 벤더와 독립성(`independent`/`same-vendor`), `judge_wrote_position`, `positions_count`가 기록돼 있고 `judge.issues`가 비어 있다.
- `blocked`와 `unresolved`가 비어 있다. 아니면 타이브레이크나 재토론 기록이 있다.
- DECISIONS.md에 참석 줄과 소수의견이 있는 D-code가 있고, PROVISIONAL이면 catch-up 대상이 적혀 있다. catch-up 뒤에는 AMEND 줄이 있다.
- 결석한 좌석을 4/4로 보고하지 않는다.

## 금지 패턴

- 한 벤더의 페르소나 여러 개를 "4벤더 토론"이라고 부르기. 다른 벤더의 답을 `submit`으로 대신 등록하기.
- 쿼터가 소진된 좌석을 "한 번만" 호출하기 — 구매 크레딧이 조용히 청구된다. UNKNOWN 좌석을 Simon 허락 없이 `--accept-unknown`으로 부르기.
- 심판에게 벤더 이름을 보여 주기, 오케스트레이터 벤더가 표시 없이 심판 하기.
- HOLD를 반복하며 시간을 쓰기 — 겐세이를 부를 신호다.
- 사소하고 되돌리기 쉬운 결정에 토론 쓰기.
- 구조화 출력 실패로 생긴 "반대 0건"을 합의로 읽기 — 판독 불가 답은 `unresolved`로 남고 FINAL을 막는다.

## 완료 보고 (HTML) — 표준

작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG). 참석 4좌석 표를 반드시 넣는다.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다.
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
