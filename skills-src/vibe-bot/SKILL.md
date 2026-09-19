---
name: vibe-bot
description: "Use when a task should run on Grok Bot's xAI/Cursor cloud computer, and for all console or GUI work (Play Console, App Store Connect, cloud consoles, desktop apps) - triggers \"/vibe-bot\", \"그록 봇으로 돌려\", \"봇한테 시켜\", \"콘솔 작업\", \"GUI 작업\", \"run this on Grok Bot\", \"console task\". Produces a task sheet with a run nonce (console: target, goal, scope, forbidden buttons, stop points, screen evidence, result format), routes it to the owning bot from an 11-bot roster and drops it in that bot's hub inbox, gates secrets, repo writes, merges, deploys and payments, and collects results from the hub outboxes with a check that rejects a missing nonce, a scope-less absence, a returned credential or console output without screen evidence, and escalates any reported irreversible click. NOT for local repo work (use vibe)."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 0.5.0
author: simon-stack
---

# vibe-bot - Grok Bot (xAI 클라우드 컴퓨터)로 일 보내기

`/vibe`는 이 PC의 Orca 워커에 일을 뿌린다. `vibe-bot`은 **남의 클라우드 컴퓨터에서 도는
Grok Bot**에 일을 맡긴다. 브라우저를 직접 몰아야 하거나, 노트북을 닫아도 계속 돌아야 하거나,
API가 없는 사이트를 다뤄야 할 때 쓴다. **콘솔 · GUI 작업은 항상 이 스킬로 간다**(아래 절).

```
/vibe-bot <요청>                                   → 과제서 생성 + 담당 봇 배정 + 안전 게이트
/vibe-bot --mode console --target "<콘솔 · 앱 ID>" <목표> → 콘솔 과제서(누르지 말 것 · 멈춤 지점 · 화면 증거)
/vibe-bot ... --deliver hub                        → 담당 봇의 허브 과제함에 넣고, 봇에게 보낼 한 줄만 준다
/vibe-bot --collect [--nonce vb-…]                 → 모든 봇 결과함을 한 번 훑어 검사
/vibe-bot --verify <결과파일> [--mode console]      → 결과 하나를 규칙으로 검사
```

## 지금 어디까지 되나 (2026-09-19)

| 단계 | 상태 |
|---|---|
| 과제서 조립 · 안전 게이트 · 결과 검사 | **동작한다.** 구독도 로그인도 필요 없다 |
| 전달 - 수동 붙여넣기 | **실측 1회 통과**(2026-09-19, `vb-f66af738`). 이후 fable 교차검증으로 금액 6/6 일치 |
| 콘솔 모드 | 과제서 · 검사(C1 · C2) 동작(2026-09-19). 콘솔 과제 실측은 아직 |
| 봇 명단 · 허브 과제함/결과함 · `--collect` | 동작(0.4.0). 봇이 허브 파일을 읽고 쓰는 실측은 아직 |
| 전달 - 웹훅 · GitHub 이벤트 | **미검증.** 실측을 한 번 통과해야 열린다 |
| /vibe 원장 편입 | 아직. 관측이 쌓인 뒤 별도 PR |

**공식 문서에 Grok Bot 과제 전송 API는 없다.** 웹훅 트리거는 외부 보도에만 있다. 그래서 기본
전달은 **사람이 한 줄을 보내는 것**이고, 나머지는 실측 뒤에만 켠다.

## 사실 근거 (공식 문서에서 확인한 것만)

- 봇은 **사람의 권한을 넘길 수 없고**, 모든 행동은 그 사람 이름으로 기록된다.
- 격리 단위는 **사람**이다. 한 사람의 봇들은 **같은 컴퓨터 · 파일 · 브라우저 세션 · 앱 로그인**을 쓴다.
  공식 문서 문장: 봇을 보안 경계로 쓰지 말 것.
- 로그인 · 2차 인증 · 결제 입력은 봇이 타이핑하지 않고 **사람에게 화면을 넘긴다.**
- 커넥터 토큰은 백엔드에 남고 클라우드 컴퓨터에 저장되지 않는다.
- 외부에서 읽은 내용은 **신뢰할 수 없는 데이터**로 표시되지만 "위험을 줄일 뿐 없애지 못한다".
- 학습 제외는 Privacy Mode 설정을 따른다. 감사 로그 · 행동 기록 · 네트워크 정책은 기업 플랜 기능이다.
- 루틴은 일정과 계정 이벤트(예: GitHub 알림)로 시작할 수 있다. **기존 봇이 새 봇을 만들 수 있다.**
- 앱은 **별도 데스크톱 앱**이고 로그인은 **Cursor 계정**이다. grok CLI 의 xAI 로그인과 계정이 다르다.

## 앱 화면에서 확인한 것 (2026-09-19, Grok Bot 0.56.1)

- **설정 → 컴퓨터**의 "이 컴퓨터에서 실행" · "트래픽 라우팅"이 켜져 있으면 클라우드 봇이 **이 PC의
  파일 · 명령 · 네트워크**에 닿는다(Simon 선택: 허용 — 허브 과제함 방식이 이걸 쓴다).
- **자동 검토 규칙**의 기본값은 **"자동으로 허용"**이다. 막을 규칙은 "먼저 묻기"로, 필요 없는 규칙은 삭제.
- 첫 화면 카드는 계정 연결을 부른다. 필요한 연결만 커넥터로 한다.

## 게이트 - 코드가 막는다

| | 규칙 | 근거 |
|---|---|---|
| B1 | 요청·과제서에 키 · 토큰 · 비밀번호 · 계정 문자열이 있으면 **중단** | 전역 지침 §3-4 |
| B2 | 레포 쓰기 · 머지 · 배포 · force push · 삭제 · 결제 · 권한 변경은 **봇에게 위임하지 않는다** | 파괴·비용 게이트 |
| B3 | 회사 기밀(설비·LOT·공정 수치·단가·고객사)은 **보내지 않는다** | 프로젝트 지침 §1 |
| B4 | 봇 산출물은 grok 레인과 같은 등급이다. 수치·목록은 받되 **결론은 재검증** | vibe 레인별 산출물 제약 |
| B5 | 요청마다 nonce를 박고, 결과에 그 nonce가 없으면 **버린다** | 웹훅은 보낸 쪽을 검증하지 않는다 |
| B6 | 봇 쪽 승인 규칙은 전송 · 게시 · 삭제 · 구매 · 운영 변경 = 먼저 묻기로 둔다 | 공식 Auto Review |
| B7 | 상시 폴링 · 감시 데몬을 만들지 않는다. 회수는 `--collect` 한 번 훑기뿐 | vibe 규율(허브가 그 SPOF로 죽었다) |

## 쓰는 법

### 1. 과제서 만들기

```bash
SKILL_ROOT="$HOME/.claude/skills/vibe-bot"
python "$SKILL_ROOT/scripts/make_bot_spec.py" --task "경쟁 툴 5곳 가격 페이지를 열어 요금제와 변경일을 표로 정리"
```

통과하면 과제서와 `.meta.json`(nonce · 담당 봇)이 리포트 폴더에 생긴다. 막히면 이유가 출력된다.
일반 과제서는 다섯 칸(**Outcome · Sources · Constraints · Deliverable · Review point**)이고, 부재
보고에는 찾은 범위를, 판단에는 근거를 붙이라는 규율이 항상 따라붙는다.

### 2. 전달

| 경로 | 명령 | 조건 |
|---|---|---|
| 허브(권장) | `--deliver hub` | 담당 봇 과제함에 넣고 봇에게 **한 줄**만 보낸다. 봇이 이 PC 파일을 읽을 수 있어야 한다 |
| 수동 | 과제서를 봇 대화창에 붙여넣기 | 항상 가능 · 2026-09-19 실측 통과 |
| 웹훅 | `--deliver webhook --send` | 환경변수 두 개 + 실측 1회 통과 |
| GitHub 이벤트 | `--deliver github` | 전용 비공개 레포 이슈 + 루틴(실측 전) |

웹훅 값은 환경변수에서 읽는다(`GROK_BOT_WEBHOOK_URL`, `GROK_BOT_WEBHOOK_KEY`). 키를 명령줄에 쓰지 않는다.

### 3. 회수와 검사

```bash
python "$SKILL_ROOT/scripts/make_bot_spec.py" --collect                 # 모든 결과함 한 번 훑기
python "$SKILL_ROOT/scripts/make_bot_spec.py" --verify 결과.md --nonce vb-1a2b3c4d
```

걸리는 것: nonce 없음 · 범위 없는 "0건" · 근거 없는 결론 · 결과에 섞여 돌아온 자격증명(+ 콘솔이면
C1 · C2). 하나라도 걸리면 그 결과는 **쓰지 않는다**. 부재 보고의 범위는 결과 어딘가의 범위 문장이나
**부재를 적은 줄마다 붙은 출처**로 인정한다.

## 콘솔 · GUI 작업 (Simon 원칙 2026-09-19)

웹 콘솔과 데스크톱 GUI 조작은 **이 스킬로 Grok Bot에 맡긴다.** Claude는 과제서를 쓰고 결과를 검사하고,
사람은 로그인 · 2단계 인증 · 결제 · 되돌릴 수 없는 버튼 승인만 한다. 콘솔 · GUI 작업에 한해 전역 지침
§7 의 브라우저 순서보다 이 원칙이 우선한다. **레포 코드 · CLI 로 끝나는 일은 기존 `/vibe` 레인**이다.

```bash
python "$SKILL_ROOT/scripts/make_bot_spec.py" --mode console --deliver hub \
  --target "Google Play Console · com.simonk.secondbrain" --url "https://play.google.com/console" \
  --task "출시 트랙별 최신 버전 · 상태 · 검토 메시지를 읽어 표로 정리"
```

| 칸 | 내용 |
|---|---|
| 대상 | 콘솔 · 앱 이름, 앱/패키지 ID, 시작 URL (`--target` 필수 · `--url`) |
| 목표 | 확인하거나 바꿀 것 한 문장 (`--task`) |
| 범위 | 기본 **읽기 전용**. 바꿔야 하면 `--allow-change "항목과 값"` - 그래도 저장 · 제출 직전에는 멈춘다 |
| 누르지 말 것 | 제출 · 게시 · 출시 · 검토 요청 · Reply · Resubmit · 삭제 · 결제 · 권한 변경 · 허용 밖 저장 (+ `--forbid`) |
| 멈춤 지점 | 로그인 · 2단계 인증 · 결제 화면, 금지 버튼이 필요한 순간, 지시와 다른 화면 |
| 증거 | 화면마다 메뉴 경로 · 읽은 값 · 스크린샷 1장 |
| 결과 형식 | 첫 줄 nonce → 표(항목 · 값 · 화면 경로 · 스크린샷) → 한 일 / 안 한 일 → 다음 행동은 제안만 |

**C1** 메뉴 경로나 스크린샷이 없으면 불합격. **C2** "제출했다 · 답변 보냈다 · Resubmit 눌렀다" 같은
보고는 불합격 처리하고 사람이 콘솔에서 바로 확인한다(상태 라벨을 읽은 것도 걸릴 수 있다 - 안전한 쪽).

## 봇 명단과 연동 (0.4.0)

정본은 `bots.json` 이다. 대상 · 과제 문구의 키워드로 담당 봇을 고르고(`--bot` 으로 지정 가능),
아무것도 안 맞으면 **Grok Bot**(접수 · 분배)이 받는다.

| id | 앱 이름 | 맡는 일 |
|---|---|---|
| `play-console` | Play Console | 트랙 · 출시 · 스토어 등록정보 · 앱 콘텐츠 · 정책 기한 |
| `apple-dev` | Apple Dev | App Store Connect · 심사 · TestFlight · 인증서 |
| `store-reviews` | Store Reviews | 스토어 리뷰 분류 · 답글 초안(게시 직전 멈춤) |
| `eas` | EAS Bot | EAS 빌드 · 제출 상태(유료 빌드 시작 · 제출은 승인) |
| `dev-infra` | Dev Infra | GitHub · Supabase · GA4 · Firebase · AdMob · Clarity 대시보드 |
| `keys` | 2ndB Keys | 비밀값 이름 · 존재 · 회전 점검(값은 보지 않음, 운영 변경은 Simon + 레포 게이트 문서) |
| `web-qa` | Web QA | 라이브 웹 · 랜딩 스모크 · 회귀, 화면별 스크린샷 |
| `public-mail` | Public Mail | 공개 메일 분류 · 삭제 요청 기한 · 답장 초안(받은편지함 연결 보류) |
| `marketing` | Marketing | 콘텐츠 · SNS 초안(게시 승인, 레포 파일은 브랜치 + PR 로만) |
| `research` | Research Bot | 출처 달린 사실 조사 |
| `grok-bot` | Grok Bot | 접수 · 분배, 일회성 일 |

**허브 버스** - `AI Infra/Communication/bots/<id>/inbox` 에 과제서(`vb-….md` + `.meta.json`)가 들어가고,
봇은 결과를 `outbox/vb-….result.md` 로 남긴다. 누가 보냈든(Claude · codex · 다른 세션) 같은 폴더를
쓰므로 세션이 바뀌어도 과제와 결과가 이어진다. 회수는 `--collect` 한 번이고, 합격한 결과만 결정에 쓴다.
봇끼리 넘길 때도 상대 봇 과제함에 과제서를 두고 그 봇 이름을 결과에 적는다.

**프로젝트 버스 (0.5.0)** - 프로젝트에 속한 봇(`bots.json` 의 `project`)은 그 프로젝트 작업 폴더 안의 버스를 쓴다.
2nd-B 봇 9개는 Simon 의 작업 워크트리 `TTL-Work_rev2`(`projects.2nd-b.root`)의 `.bots/<id>/` 를 쓰고, 과제서에는
`프로젝트 루트` 줄이 붙는다. 메인 작업 트리 `E:\2ndB` 에는 쓰지 않는다(`_sync/` 만 거기 있다 - 읽기만).
`.bots/` 와 `marketing/` 은 `E:\2ndB\.git\info\exclude` 로 로컬 제외라 Simon 의 브랜치 상태를 바꾸지 않는다.
워크트리 이름이 바뀌면 `projects.2nd-b.root` 한 곳만 고친다. `--hub` 를 명시하면 모든 봇이 그 경로를 쓴다(시험용).
`--collect` 는 허브와 프로젝트 버스를 함께 훑는다.

## 실측 절차 (PC 앞에서)

1. 앱 설치: `cursor.com/download/bot` (winget 없음). 서명이 **Anysphere, Inc.** 인지 확인
2. **Cursor 계정** 로그인. 요금제 · 결제 화면이 나오면 **멈추고 Simon에게 묻는다**
3. 설정: 자동 검토 켜기 + 규칙 "먼저 묻기" · 컴퓨터 탭 결정 · 추가 사용량 확인
4. 계정 연결은 필요한 커넥터만. **토큰을 채팅에 붙여넣지 않는다**
5. 과제서 1장을 수동으로 넣고 `--verify` 통과 (2026-09-19 완료)
6. 허브 과제함 1회(`--deliver hub` → 한 줄 → `--collect`) 실측 뒤 이 표를 고친다

각 단계 결과는 허브 `DECISIONS.md`에 한 줄로 남긴다.

## 이 스킬을 쓰지 않는 경우

- 레포 코드를 고치는 일 → `/vibe`(Orca 워커, 워크트리 격리, 보안 게이트)
- 한 세션에서 끝나는 작은 수정 → `dev-orchestrator`
- 되돌리기 어려운 일, 돈이 나가는 일, 자격증명이 필요한 일 → 사람이 한다

## 관련 스킬

`vibe`(4벤더 로컬 파이프라인) · `ai-debate`(결정 지점) · `simon-worktree`(격리 규칙)
