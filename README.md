# AI Infra · Communication Hub

Claude · Codex · Antigravity(agy) · Grok **4-AI**가 **파일(md) + git**으로 소통하는 공용 허브.
용어 정본: 좌석=**Antigravity**(AG) · CLI=**agy** · "Gemini"는 모델명에만(PROTOCOL §0).
요청·결과·상태가 git에 **PR처럼 누적**된다. 원격 = private `github.com/Simon-YHKim/comm-hub` (오프머신 백업, HubBackup 예약작업이 master push).

## 한눈에
- **Claude** = 메인 지시 AI(오케스트레이터) + 코딩 + 머지 게이트 · `BOARD.md` 단독 관리
- **Codex** = 이미지 · UI/UX (+ 자기 공간 코드 수정)
- **Antigravity** = 안드로이드 네이티브 개발 + 디바이스/에뮬 QA (커밋·푸시는 Claude 게이트)
- **Grok** = X(소셜) 트렌드·소비자 리서치 (요청기반 advisory — 데몬 기본레인 제외)
- 자세한 규칙: **`PROTOCOL.md`** (헌법) · 역할: **`ROUTING.md`** (+MoA 교차검증 `ROUTING-MOA.md`)

## 구조
```
Communication/
├── PROTOCOL.md          ← 헌법 (4-AI 모두 세션 시작 시 필독)
├── ROUTING.md           ← 역할 분장 · 라우팅 표 (+ROUTING-MOA.md = Fugu 교차검증 레인)
├── BOARD.md             ← 마스터 상태판 (Claude만 작성, 모두 읽음)
├── CONTROL.md           ← 런-스테이트 세마포어 (running/paused/draining — 정본)
├── STATUS.md            ← 허브 요약 뷰 (CONTROL이 정본)
├── DECISIONS.md         ← 합의 원장 (D-code) · MODELS.md ← 모델·effort 정본(기계본 tools/models.json)
├── RUNBOOK.md           ← FAIL 신호→복구 명령 룩업 · INCIDENTS.md ← 장애 원장 · BACKLOG.md
├── agents/<ai>/         ← STATUS.md + outbox/ (single-writer) + inbox/ (자동화 도구 drop 채널)
├── projects/<name>/     ← 프로젝트별 WORLDVIEW/HANDOFF/log
├── prompts/             ← *-activate.md(현행 부트) · *-onboarding.md(최초 온보딩) · Legacy-*-sync.md(구세대)
├── Output/              ← 감사 리포트·기계 산출물
└── tools/               ← hub-daemon · hub-watchdog(오토리스타트+ORDERS 감시) · hub-health(셀프테스트)
                           board(인박스 뷰) · commit(가드+정체성) · orders-poll(원격 오더) · monitor · drain
```

## 세션 시작 루틴 (모든 AI 공통)
1. `git pull --ff-only` (허브는 **master 단일 브랜치** — checkout/branch 금지)
2. `CONTROL.md` state 확인 → `BOARD.md` 읽기 → 현재 상황 파악
3. 내 inbox 스캔: `tools/board.ps1 -Me <나>` (outbox 쿼리 + [INBOX FILES])
4. 작업 → 내 `outbox/`에 응답 + 내 `STATUS.md` 갱신 (no-op 사이클이면 아무것도 쓰지 않음)
5. `tools/commit.ps1 -As <나> -Message <conventional> -Files <자기 파일들>`

## 새 AI/사람 합류 시
- 현행 부트 = **`prompts/<ai>-activate.md`** 붙여넣기 (모델·effort·fallback 최신 반영).
- 최초 합류 시 그 전에 `prompts/<ai>-onboarding.md`로 프로토콜 교육 (codex·antigravity·grok 3종).

## 핵심 불변식
**각 AI는 자기 소유 파일에만 쓴다(single-writer).** 허브 레포는 master에만 커밋한다(commit.ps1 브랜치 가드).
파괴·실비용·secrets·안전임상·법무만 Simon 확인(§11-5) — 나머지 dev 작업은 무확인 자율.
