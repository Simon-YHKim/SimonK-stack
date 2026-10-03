# SimonK-stack 세션 인수인계

## Latest — 2026-10-04 / 토론 4건 이행: 안전 훅 Windows·PowerShell · 위젯 D-54 재토론 · Grok Bot 첫 과제

갱신 시각: 2026-10-04 01:17 KST · 갱신자: Claude Code(Opus 5.5). Simon 요청: "6분 뒤 grok 작업 마저, D-54는 너가 다시, 토론할 것이 있으면 멈추지 말고 진행, cursor 초과 과금은 꺼져 있고 양방향으로 승인 중, 승인 기록은 봐도 됨."

### 어디까지 왔나
- **결정(모두 PROVISIONAL 3/4, Grok CLI 결석)**: D-60(Grok Bot 레인 조건부 단계 개통, 자문 불허), D-61(D-54 재토론: 조건부 KEEP_AND_LAND), D-62(안전 스킬 2단계: A1 → 실측 D → A2·최소 B), D-63(위젯 REINSTALL_THEN_FIX). D-58에 Simon 게이트 증언 AMEND.
- **안전 훅(D-62)**: PR #103 freeze·guard·unfreeze 0.2.0(Windows 경로 정규화, cwd 대체 판정 제거), #104 careful 0.2.2(Windows 루트·홈 HIGH 52형, PowerShell 매처 deny 전용). 후보 `20261004-vibe-21310b` 설치(정션 8 + 실폴더 4). **새 대화형 세션 종단 6/6 PASS**(Bash·PowerShell force-push deny, freeze 경계 밖 Write deny).
- **실측 결론**: PowerShell 매처 발화, deny는 bypass에서도 차단, **ask도 bypass에서 확인창**, Edit 경로는 `C:\...`, 새 세션은 PowerShell 도구에 `CLAUDE_CODE_USE_POWERSHELL_TOOL=1` 필요.
- **위젯(D-61·D-63)**: 데이터 백업(`~/.claude/flat-link-archive/aiuw-backup-261003`, 7,683파일·210.6MB, ACL 좁힘)·사본 복원 리허설 일치. d767272 경고는 일반·모션 감소에서 구분 불가(FAIL) → PR #102로 2c21eec만 main, PR #105로 경고를 모양 단서(삼각형·밑줄)로 고쳐 세 모드 PASS, `094da97` 고정 소스로 최종 재설치(계정·인증 파일 해시 불변).
- **Grok Bot(D-60)**: PR #101로 Relay만 `active`. 첫 과제(Cursor 초과 과금·자동 충전 화면 확인, 읽기 전용) `vb-c594b4d8`를 /vibe 정식 경로(Store USD 0 init·register·인증서·`execute_bot.py dispatch`)로 01:07:51 발행. 할당량 근거 = 위젯 Bot 행 자동 관측(96% 남음). 결과 대기(Relay 마지막 점검 00:38).
- **Grok 계정**: Simon이 말한 리셋은 SuperGrok **Heavy** 계정(위젯 첫 Grok 칸, 10-03 23:12 KST 리셋, WK 89% 남음). Grok CLI는 10-01부터 다른 계정(10-08 16:51 리셋)이라 xai 좌석은 계속 결석.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | Grok catch-up D-56~D-63(8건). CLI를 Heavy 계정으로 다시 로그인하면 바로 가능(Simon이 `! grok login`), 아니면 10-08 16:51 KST 이후 | 작음 | 감시 스크립트가 READY 시 자동 실행 |
| B | Grok Bot `vb-c594b4d8` 결과 회수 → `execute_bot.py check-result` → 스크린샷 직접 확인. PASS 전에는 다른 Bot 과제 금지(D-60) | 작음 | |
| C | investigate 스킬(아직 gstack) 처리, careful PS 미판정 형태(변수·splatting·EncodedCommand), 플러그인 `safety_runtime.py` deny→ask 강등 수정 | 중간 | §35 |
| D | 레지스트리 재갱신 2026-10-10 21:42 KST 전(알림 10-10 09:00) | 중간 | |
| E | Orca 레인 현행 세대 이전(§35) · claude.ai/Cowork 지시사항 400KB 반영 · `docs/INSTALL.md` 400KB 근접 → 기간 분할 | 중간 | |

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B "$env:USERPROFILE\.claude\skills\ai-debate\scripts\debate.py" catchup --orchestrator anthropic
```

---

## 2026-10-03 22:53 / 남은 일 전부 처리: vibe 2.13.1 · ai-debate 0.2.4 · careful 0.2.0 · Grok Bot 증거 레인

갱신 시각: 2026-10-03 22:53 KST · 갱신자: Claude Code(Opus 5.5). Simon 요청: "남은 일 모두 진행해줘. 토론에 그록 봇도 포함시키자. 그록은 2시간 뒤 리셋될꺼야. 그록은 한번 테스트 하지 않았나? 꼭 필요한가?"

### 어디까지 왔나
- **main `baafc70`**: PR #96(vibe 2.13.0·qa 2.1.0 — 야간 QA 브랜치를 main에 합침), #98(vibe 2.13.1, 레지스트리 37건 재확인·변경 0, 만료 **2026-10-10 21:42 KST**), #97(ai-debate 0.2.4, Codex 좌석 실시간 `account/rateLimits/read`), #99(careful 0.2.0, gstack 1.91.9 위 재구성·내부 실패 deny). 머지 커밋 넷 모두 CI 성공.
- **홈 설치(D-59 조건부 ALL)**: 후보 `20261003-vibe-21310-candidate` 영수증 4/4, 정션 8개 + Codex config 한 줄 전환, 설치본 selftest 180/0. ai-debate 0.2.4 사본 교체(110/110). careful 0.2.0 교체 후 **새 대화형 Claude Code 세션에서 실측**: force-push가 `[careful][HIGH] … blocked` deny, 원격 ref 불변, echo 통과. agy는 qa 정션을 못 봐서 심링크 추가 → 4개 CLI 182/182.
- **실측(2026-10-03)**: 스킬 frontmatter 훅에서 `${CLAUDE_SKILL_DIR}`는 비어 있고 그 경로 훅은 실행되지 않음(시작 실패 훅은 fail-open). 훅 deny는 bypassPermissions에서도 막음. ask는 미측정.
- **결정**: D-56(안전 스킬 REBASE), D-57(0.2.3), D-58(Grok Bot = 좌석 아님, 비투표·비차단 증거 레인), D-59(머지·설치) — 모두 PROVISIONAL 3/4(Grok 결석). D-53·D-55 FINAL via catch-up. **D-54는 Codex OBJECT로 차단**(Orca 대화형 Codex가 `--host-session`으로 직접 제출 — Codex 호스트 E2E 실증).

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | Grok catch-up D-56·D-57·D-58·D-59. 실시간 billing은 주간 리셋 **2026-10-08 16:51 KST**(Simon은 10-03 23시대 리셋이라 함). 감시 스크립트가 READY 되면 자동 실행 — 이 세션이 끝나면 `debate.py catchup --orchestrator <호스트>` | 작음 | |
| B | D-54 타이브레이크: 호스트(Codex)가 결정. 그 전엔 AI Usage Widget 갱신 금지 | 작음 | Codex 세션에서 |
| C | D-56 다음 단계: guard·freeze·unfreeze 훅도 `${CLAUDE_SKILL_DIR}` → `$HOME` 고정 + freeze 공용 작성기 보존. careful HIGH에 `/c/`·`C:/`·`$HOME/*` 추가 여부. PowerShell 도구 감시 공백. 플러그인 `safety_runtime.py`가 deny를 ask로 바꾸는 문제 | 중간 | §35 토론 |
| D | Grok Bot 증거 레인 실사용: Cursor 계정 초과 과금 꺼짐 화면 증거 + Simon `approval_ref` 확보. 소수의견("xAI 관점 자문")은 Simon 결정 | 작음 | |
| E | 레지스트리 재갱신 2026-10-10 21:42 KST 전(알림 10-10 09:00) | 중간 | |
| F | Orca 레인 현행 세대 이전(§35) · claude.ai/Cowork 지시사항 400KB 반영 · `docs/INSTALL.md` 400KB 근접 시 기간 분할 | 중간 | |

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B "$env:USERPROFILE\.claude\skills\ai-debate\scripts\debate.py" catchup --orchestrator anthropic
```

---

## 2026-10-03 21:10 / 4벤더 토론 실전 테스트 · ai-debate 0.2.3

갱신 시각: 2026-10-03 21:10 KST · 갱신자: Claude Code(Opus 5.5). Simon 요청: "코덱스, 그록, 제미나이 사용량 차있어. 한번 테스트 해볼래?"

### 어디까지 왔나
- **Codex catch-up 완료**: D-53·D-55의 Codex 좌석을 실호출(gpt-6.1-sol xhigh, 84초·100초) → 둘 다 ACCEPT. 두 결정 모두 **FINAL via catch-up**, 허브 AMEND 기록. D-54(Codex가 연 토론)의 Codex 좌석은 살아 있는 대화형 Codex 세션만 채울 수 있어 남겨 둠.
- **새 full 토론 D-56**(`dbt-261003-204651`, 안전 스킬 5개 gstack 원본 vs SimonK 판): R1·R2·블라인드 심판(Codex)·비준 3/3 ACCEPT → **REBASE**(확신도 84), PROVISIONAL 3/4.
- **테스트에서 결함 발견 → ai-debate 0.2.3**: `seats`가 Grok을 READY(78%)로 냈다. 근거는 이틀 전 로그 줄이었고, 실제 계정은 100%라 R1이 402로 거절됐다(과금 0, on-demand·선불 0). [PR #93](https://github.com/Simon-YHKim/SimonK-stack/pull/93)으로 고침.
  - Grok 좌석이 `grok agent --no-leader stdio` → `_x.ai/billing`으로 실시간 조회를 먼저 한다(모델 턴 없음, 약 0.4초).
  - 오래된 로그는 여유 근거로 쓰지 않는다.
  - D-57 토론에서 Codex·Claude 좌석이 따로 찾은 "기간 종료 + 오래된 로그 = READY" 빈틈도 같은 PR에서 막았다.
  - 머지 `5e4cae8`, 홈 설치 완료(`docs/INSTALL.md` 첫 절).
- 허브 `DECISIONS.md`: D-53·D-55 AMEND, D-56, D-57(+조건 이행 AMEND). 로컬 커밋 `0db9c2da`.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | **2026-10-08 중**(만료 10-09 00:39 KST 전) /vibe 레지스트리 재확인·갱신. 홈 /vibe는 지금 2.13.0(야간 QA 브랜치 후보)이라 갱신은 2.13.0 기준 소스에서 할 것 | 중간 | 놓치면 /vibe 라우팅 정지 |
| B | Grok catch-up: D-56·D-57(그리고 같은 계정이 리셋되는 **2026-10-08 16:51 KST** 이후). `debate.py catchup --orchestrator <호스트>` | 작음 | Grok CLI 계정은 지금 주간 100% |
| C | D-56 이행: careful부터 REBASE. `${CLAUDE_SKILL_DIR}`가 스킬 훅에서 전개되는지 로컬 실측이 먼저다(gstack 주석 #2469는 안 된다고 함 → SimonK 판 훅이 아예 안 돌 수 있음). freeze는 gstack 공용 작성기 보존 | 중간 | |
| D | Codex 좌석도 실시간 조회(`codex app-server` `account/rateLimits/read`) — D-57 소수의견 | 작음 | |
| E | `feat/qa-evidence-261003`(/vibe 2.13.0) PR·머지 여부 — 홈에는 이미 설치됨, main에는 없음 | 작음 | |
| F | Orca 레인 현행 세대 이전(§35 토론) · claude.ai/Cowork 지시사항 400KB 반영 | 중간 | 이전 블록 C·E |

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B "$env:USERPROFILE\.claude\skills\ai-debate\scripts\debate.py" catchup --orchestrator anthropic
```

---

## 2026-10-03 03:43 / QA 2.1.0 + vibe 2.13.0 설치

Simon 요청: AI 코딩 QA 강화안을 `/vibe`까지 연동해 최종 개선하고 PC 종료.

- 소스: `feat/qa-evidence-261003`, QA `32efde8`, vibe `f607bff`, 설치 경로 회귀 보완 `cf139c3` push 완료. main 병합·PR 생성·운영 배포 없음.
- QA는 독립 계약/대상 핀, 필수 positive/negative/boundary/recovery 검사, 실제 증거 해시, 고위험 사람 검토를 대조한다. 누락·미실행·실패·오래된 증거를 차단한다.
- vibe `Store.complete`는 변경/coding/qa 노드가 있으면 `bind-qa`와 실제 게이트 통과가 필수다. 완료 직전 재검사하며 기존 LLM 리뷰·비용 정산 조건도 유지한다. node `verify`는 리뷰용 출력 준비 상태다.
- **실제 설치**: Claude vibe·Codex vibe·공용 Claude QA 세 경로만 새 후보로 전환. `.agents`는 기존 연결로 갱신. 다른 Core 링크는 이전 후보이므로 설치 루트가 혼합돼 있다. [설치 기록·영수증·백업](INSTALL.md) 첫 절을 기준으로 한다.
- 검증: 설치된 Codex 전체410 / Claude 상태관리67 / 공용QA33 PASS, 소스 selftest180 / Skill-Gen24 / 141 skill gate PASS. 네 패키지 영수증도 PASS. 원격 feature push는 GitHub `skills-ci` 트리거가 아니다. 기능 커밋 `cf139c3`의 Cloudflare Pages 체크는 success이며, 실제 앱 E2E·모델 비용·전체 호스트 행동은 증명하지 않는다.
- 결정: 앞선 사용자 정족수 예외를 유지. Claude/Codex 쿼터와 Grok 실제 잔액 거절 때문에 Google advisory만 참여했다. 최종 재검토에서 즉시 차단 결함 없음. 4벤더 합의나 새 D번호를 주장하지 않는다.
- 보고서: `E:/Coding Infra/reports/simonk-vibe-qa-completion-20261003.html`. 종료 전 작업/검증 기록을 저장한다. 예약된 종료의 실제 실행 여부는 후보 루트의 `shutdown-status.json`을 확인한다.
- 남은 경계: 계약의 완전성·테스트 실행자·사람 신원은 해시로 인증되지 않는다. 신뢰하는 coordinator/CI가 기준과 immutable build를 관리해야 한다. 레지스트리 만료 갱신 등 이전 후속 큐는 유지한다.

---

## 2026-10-02 / 4개 CLI 동일 사용: /vibe 2.12.43 · ai-debate 0.2.2

갱신 시각: 2026-10-02 02:25 KST · 갱신자: Claude Code(Opus 5.5). Simon 요청: "codex, claude, grok, agy 모두 이 스킬을 동일하게 사용하게, ai-debate·오케스트레이션·모델/effort 라우팅 모두 최신화. 나보고 시키지 말고 직접."

### 어디까지 왔나
- main `9e88140`: [PR #90](https://github.com/Simon-YHKim/SimonK-stack/pull/90) ai-debate 0.2.2(호스트 중립: `--orchestrator` 필수, 호스트 자기 좌석 세션 내, 다른 벤더 라이브 세션의 `--host-session` 증명·결합, Grok·agy 겐세이 감지), [PR #91](https://github.com/Simon-YHKim/SimonK-stack/pull/91) /vibe 2.12.43(레지스트리 만료 10-06 → **10-09 00:39 KST**, grok-4.5 legacy, legacy 동점 보정).
- **설치 완료**: /vibe 2.12.43(정션 7개), ai-debate 0.2.2(리플레이 게이트 4벤더 18건 통과 후). 상세·영수증·되돌리기는 `docs/INSTALL.md` 첫 절.
- **4개 CLI 동일**: Claude Code·Codex·Grok·agy가 같은 스킬 파일을 읽는다. agy는 `~/.gemini/config/skills.json` + Core 5개 심링크로 182/182(이번에 신설).
- SimonK 자체 스킬 31개를 main과 동기화. 허브 `tools/models.json`·`hub-health.ps1`·`hub-daemon.ps1` 기본값·`MODELS.md`를 현재 모델로 재핀(로컬 커밋 `351c0828`). ModelWatch 예약 작업은 설치 경로를 실행.
- 결정: D-55(4벤더 토론, PROVISIONAL 3/4, Codex 결석). D-54(Codex가 연 토론)의 Claude 좌석을 이 세션이 `--host-session`으로 실제 catch-up(대화형 증명 `entrypoint cli`, `bound_by fingerprint`) — 교차 호스트 경로 실증.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | **2026-10-08 중**(만료 10-09 00:39 KST 전) /vibe 레지스트리 사실 재확인·갱신 → PR → 후보 → 정션 전환. 알림 = 예약 작업 `\SimonK-Vibe-RegistryRefresh-Reminder` | 중간 | 놓치면 /vibe 라우팅 전부 정지 |
| B | 2026-10-07 09:03 KST 이후 Codex catch-up: `debate.py catchup --orchestrator <호스트>` → D-53·D-55 Codex 좌석, 그리고 Codex 호스트 라이브 E2E 1회. 알림 = `\SimonK-AiDebate-CodexCatchup-Reminder` | 작음 | Codex 쿼터 95% 미만 먼저 확인 |
| C | Orca 레인(routing.LANES 등)을 현행 세대로 이전 — Orca로 claude-opus-5-5·gpt-6.1-sol·grok-4.7 보내면 지금은 거부 | 중간 | 별도 §35 토론 |
| D | gstack 원본으로 덮인 34개 중 안전 계열 5개(careful·freeze·guard·unfreeze·investigate)의 SimonK 강화판 복원 여부 결정 | 작음 | |
| E | claude.ai 개인 프로필·Cowork 지시사항에 `instructions/out/` 사본 반영(400KB) — 브라우저 제어 도구가 연결된 세션에서 | 작음 | |

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B "$env:USERPROFILE\.claude\skills\ai-debate\scripts\debate.py" catchup --orchestrator anthropic
```

---

## 2026-10-02 / Grok catch-up 완료 · 파일 상한 400KB · ai-debate 0.2.1

갱신 시각: 2026-10-02 00:05 KST · 갱신자: Claude Code(Opus 5.5).

### 어디까지 왔나
- Simon이 Grok을 다른 계정으로 다시 로그인했다. 무모델 ACP billing 조회(`runtime_collect.py --surface grok`): SuperGrok, 주간 78%(2026-10-08 16:51 KST 리셋), on-demand 한도 0·사용 0·선불 0.
- D-53 Grok catch-up 실호출 성공: grok-4.7 xhigh, 166초, **ACCEPT**(독립 입장 조건부 선택지 1, 확신도 76). 허브 `DECISIONS.md`에 AMEND 줄 추가. D-53은 PROVISIONAL 유지, **남은 의무는 Codex catch-up 하나**(2026-10-07 09:03 KST 이후).
- [PR #87](https://github.com/Simon-YHKim/SimonK-stack/pull/87) ai-debate 0.2.1: `status`가 catch-up을 마친 좌석을 "catch-up done"으로 표시(78/78).
- [PR #88](https://github.com/Simon-YHKim/SimonK-stack/pull/88) Simon 지시로 단일 파일 상한 100KB → **400KB**(지침 단일본 5곳, `split.py` 재생성·`--apply`, simon-handoff 1.0.1 굴리기 예산 320KB·상한 400KB). 100KB 넘는 파일은 offset/limit·tail·grep으로 읽는다.
- 설치본 갱신: `~/.claude/skills/ai-debate` 0.2.1, `~/.claude/skills/simon-handoff` 1.0.1(main `10a6cfb`와 바이트 동일, 이전 사본은 `~/.claude/flat-link-archive/skills-261002/`).

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | 2026-10-07 09:03 KST 이후 Codex catch-up: `debate.py catchup` → `call --round catchup --vendor openai` → `record --id dbt-261001-201826 --amend` | 작음 | 남은 유일한 D-53 의무 |
| B | claude.ai 개인 프로필 지침·Cowork 상시 지시사항에 `instructions/out/` 사본 붙여 넣기(400KB 반영) | 작음 | 사람 단계 |
| C | ai-debate `seats`의 Grok 근거를 로그 마지막 줄 대신 ACP billing 조회로(계정 전환 직후 옛 수치 방지) | 작음 | |
| D | 2.12.42 첫 실제 `/vibe` 실행 결과를 기준점으로 기록 · `\SimonK-Vibe-ModelWatch` 예약 작업 갱신 | 작음 | 이전 블록 B·D |

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B "$env:USERPROFILE\.claude\skills\ai-debate\scripts\debate.py" catchup
```

---

## 2026-10-01 / `/vibe` 2.12.42·`ai-debate` 0.2.0 설치 완료와 4벤더 토론

갱신 시각: 2026-10-01 20:40 KST · 갱신자: Claude Code(Opus 5.5). Simon이 Codex의 장시간 작업을 넘기며 "스킬 업데이트 완료"와 "ai-debate를 항상 4개 벤더(Claude·Codex·Grok·Gemini)로, 오래 걸리면 중간에 겐세이"를 지시했다.

### 어디까지 왔나
- `origin/main` `bfee665`: [PR #84](https://github.com/Simon-YHKim/SimonK-stack/pull/84)(ai-debate 0.2.0) → `9c11992`, [PR #85](https://github.com/Simon-YHKim/SimonK-stack/pull/85)(/vibe 2.12.42) → `bfee665`. 두 PR 모두 정확 HEAD 검사 4/4, main 머지 커밋의 skills-ci·release·validate-plugin 성공, 새 태그 없음(source-only hold 유지).
- **사용자 홈 설치 완료**: `/vibe` 2.12.24 → 2.12.41 → 2.12.42(정션 7개 + Codex config 한 줄), `ai-debate` 0.1.0 → 0.2.0(물리 폴더 교체). 후보·영수증·검증·되돌리기는 `docs/INSTALL.md` 첫 절.
- **ai-debate 0.2.0**: `scripts/debate.py`(4벤더 좌석 러너, 무모델 쿼터 증거로 착석 판정, 결석 기록, 블라인드 심판·비준·catch-up, append-only 허브 기록)와 `scripts/interject_scan.py`(T1~T6 겐세이 감지, 읽기 전용). 적대적 검토 P0 4건·P1 다수 수정, 테스트 77/77.
- **/vibe 2.12.42**: Simon이 고른 Gstack 실행별 상태 폴더(telemetry off·update_check false, 개인 설정 불변). 호스트 격리는 지시 수준, Orca는 best-effort라고 문서에 명시.
- **첫 실제 4벤더 토론 D-53**(`dbt-261001-201826`, full): Claude ✓ · Codex ✗(주간 100%, 구매 크레딧 과금 위험) · Grok ✗(402) · Gemini ✓(실호출). 블라인드 심판(Gemini) 조건부 GO 90, 비준 ACCEPT 2/2, **PROVISIONAL 2/4**. 허브 `DECISIONS.md`에 append.
- 루트 `CLAUDE.md`·`AGENTS.md`·`GEMINI.md` §21과 허브 `PROTOCOL.md` §35.2·§35.7을 4벤더·겐세이 규칙으로 갱신(허브는 로컬 커밋).

### 안전 경계
- 추가 과금 $0: Codex·Grok 호출 0회. Gemini는 agy 무턴 `/usage`로 100% 남음 확인 후 4회 호출, Claude 좌석은 세션 내 서브에이전트.
- 관찰: 다른 Codex 세션들이 주간 한도 소진 뒤 구매 크레딧을 실제로 차감 중이었다(18:07→18:38 KST 55,940→55,741). 설정은 건드리지 않았다.
- 이미 열린 세션은 이전 스킬 목록을 캐시한다. 로컬 기본 체크아웃(오래된 main)을 프로젝트로 열지 말 것 — 구 SessionStart 훅이 스킬을 실폴더로 덮을 수 있다.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | Grok(2026-10-03 23:12 KST 이후)·Codex(2026-10-07 09:03 KST 이후) 복귀 시 `debate.py catchup` → `call --round catchup` → `record --id dbt-261001-201826 --amend` | 작음 | 일정에 박기 |
| B | 2.12.42 설치 뒤 첫 실제 `/vibe` 실행 결과를 기준점으로 기록, 실패 시 41로 되돌려 원인 분리 | 작음 | D-53 소수의견 |
| C | `debate.py` 106KB 모듈 분할(100KB 지침) · 허브 `DECISIONS.md` 170KB 기간 분할 | 중간 | 지침 위반 해소 |
| D | 예약 작업 `\SimonK-Vibe-ModelWatch`가 pr67 후보의 구 `model_watch.py`를 실행 — 새 후보로 갱신 | 작음 | |

### 핵심 파일과 검증
```text
skills-src/ai-debate/SKILL.md                     4벤더·결석·겐세이 계약 (0.2.0)
skills-src/ai-debate/scripts/debate.py            좌석 러너
skills-src/ai-debate/scripts/interject_scan.py    겐세이 감지
skills-src/ai-debate/references/seats.md          벤더별 호출·쿼터 증거
skills-src/vibe/scripts/run_state.py              gstack-env
docs/INSTALL.md                                   2.12.42 후보 영수증·설치·되돌리기
```
```powershell
python -B -m unittest discover -s skills-src/ai-debate/scripts -p "test_*.py"
python -B skills-src/ai-debate/scripts/debate.py seats --orchestrator anthropic
python -B skills-src/ai-debate/scripts/debate.py catchup
python -B .github/skill-ci/run_ci.py
```

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B "$env:USERPROFILE\.claude\skills\ai-debate\scripts\debate.py" catchup
```

---

## 2026-10-01 / `/vibe` 2.12.41 소스 머지와 실행별 Gstack 정책

갱신 시각: 2026-10-01 18:11:33 KST. Simon은 PR 머지 뒤 작업을 멈추고 `/simon-handoff`를 요청했다. 이 블록은 후속 구현이 아니라 다음 세션을 위한 상태 기록이다.

### 어디까지 왔나
- `origin/main`: `ccad7423a48b7d63e6826d074bd147fb9a45f5d4` — [PR #82 `/vibe` 설명 축약 대응](https://github.com/Simon-YHKim/SimonK-stack/pull/82) 소스 전용 일반 머지. 변경 5파일(스킬 설명·CI 회귀 테스트·README/INSTALL/CHANGELOG). 정확한 PR HEAD `fb79284870654eea5a8f759c6c332fa4dad3fe25`의 4/4 검사가 통과했고, main의 Cloudflare Pages·skills-quality·Windows path audit·validate·tag-release 5/5도 성공했다.
- `/vibe` 소스 2.12.41은 Codex가 설명을 48자로 축약해도 `/vibe`·SimonKStack·라우팅 목적을 앞에 남긴다. 품질 게이트 141/141, 오케스트레이션 회귀 131/131, 최종 격리 후보 네 SHA-256 영수증 및 오프라인 runtime probe 4/4가 통과했다. 후보는 `E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-21241-quality-candidate/`; 정확한 digest는 `docs/INSTALL.md` 첫 절에 있다.
- Claude·Codex·`.agents` 사용자 flat `/vibe` 세 경로의 SHA-256은 모두 `3b1cc7b001ecc432a9fb300ef0083d7162de536ef3eb9cf122167264a4f08e08`로 불변이고 버전은 2.12.24다. 앞선 격리 Codex 프로필의 무모델 입력에서는 namespaced `simonk-core:vibe`·`simonk-core:vibe-bot`가 각 1회 노출됐지만 새 최종 후보의 자연어 자동 선택·실호출 품질은 미검증이다.
- 현재 전용 소스 브랜치 `fix/vibe-description-routing-261001`와 기존 기본 체크아웃은 정리·삭제하지 않았다. 허브의 D-52 결정은 기존 dirty/diverged 저장소에 로컬 기록했고 원격 push하지 않았다.

### 안전 경계와 사용자 결정
- D-52는 소스 전용 main 머지와 운영 Cloudflare Pages 자동 배포만 허용했다. `distribution/main-source-only.hold`, SessionStart/Release 차단, marketplace `313c04b` pin 및 D-39/D-50 사용자 홈 설치 HOLD를 유지한다. 이번 작업에서 모델·이미지·Grok Bot 호출, 결제 설정·자동충전 변경, 추가 과금은 없었다.
- Simon은 구매 크레딧 잔액/사용 허용 설정을 더 묻거나 조회하지 말라고 했다. 사용 가능하다고 답했더라도 구매 크레딧을 사용해도 된다는 승인이 아니다. 추가 과금 $0, 구독 포함 usage만 사용하며 후속 실호출은 하지 않는다.
- Simon은 Gstack 개인 설정을 바꾸지 않고 **각 `/vibe` 실행별 별도 상태 폴더에서 telemetry와 업데이트 확인을 OFF**로 하기를 선택했다. 이 실행별 격리는 **아직 구현하지 않았다**. 개인 Gstack 설정·시작/종료 telemetry 절차는 실행하지 않았다.
- Simon은 약 5GB 로컬 이미지 모델 설치가 불필요하다고 했다. D: 다운로드·ComfyUI 모델 설치는 하지 않는다. 검증된 구독 포함 이미지 도구가 없으면 이미지 실생성 경로는 차단한다.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | Gstack의 `GSTACK_HOME`·업데이트 검사 경로를 읽기 전용으로 확인하고, 개인 설정을 보존하는 `/vibe` 실행별 telemetry/update OFF 격리 구현·오프라인 테스트 | 중간 | Simon이 선택한 다음 구현. 새 브랜치·별도 검증 후 결정 |
| B | 실제 사용자 홈에 2.12.41을 설치할지 D-39/D-50의 자산 보존·명령 수락·롤백 게이트로 재판정 | 큼 | 소스 머지를 설치 완료로 오인 금지 |
| C | 자연어 자동 선택·모델/effort·Grok Bot·이미지 경로의 실제 사용자 품질 검증 | 큼 | 구독 포함과 구매 크레딧 폴백 차단이 검증되지 않으면 실호출 금지 |

### 핵심 파일과 검증
```text
skills-src/vibe/SKILL.md                         2.12.41 메인 스킬 설명·안전 경계
skills-src/vibe/scripts/test_orchestrate.py       CI가 실행하는 48자 발견성 회귀
docs/INSTALL.md                                   최종 후보 SHA-256과 설치 HOLD
distribution/main-source-only.hold               자동 설치·릴리스 차단
E:/Coding Infra/AI Infra/Communication/DECISIONS.md  D-52(로컬 기록)
```
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B .github/skill-ci/run_ci.py
python -B skills-src/vibe/scripts/test_orchestrate.py
```

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
# A부터 진행하되, Simon의 중단 요청 이후 자동 실호출·설치·결제 설정 변경은 하지 않는다.
```

---

## 2026-10-01 / Claude·Codex CLI 계약 수정과 PR #78 인계

갱신 시각: 2026-10-01 15:41:53 KST. Simon이 컨텍스트 부담을 이유로 `/simon-handoff`를 요청했다. 문서 작성 중 별도 작업 흐름에서 코드 PR #78이 머지되어 아래 상태를 다시 반영했다.

### 어디까지 왔나
- `origin/main`: `669da9fe33c585cd685526637309b83d06b71612` (PR #78 머지). 이번 흐름에서 #76·#77·#78이 main에 머지됐다.
- [PR #78 — 직접 CLI의 허위 `ready` 차단](https://github.com/Simon-YHKim/SimonK-stack/pull/78)은 **머지됨**. 최종 HEAD `b8a26a76fa88ad5cccdde670f077f91c16ca4539`, merge SHA `669da9fe33c585cd685526637309b83d06b71612`, 6파일(플래너·테스트·계약 문서·Claude CLI 가짜 전송 테스트의 원격 CI 추가). PR 검사 4/4 성공. 다음 세션에서 최신 main 상태를 재조회한다.
- 로컬 전체 `/vibe` unittest 361/361, selftest 180/180, skill quality gate 141/141, `git diff --check` 통과. Git Bash의 TDD guard는 통과했으나 WSL 실행은 Windows worktree `.git` 경로를 해석하지 못해 실패했다. 모델·Bot 실호출은 없었다.
- 이 인수인계는 별도 `handoff/20261001-1539` 브랜치에서 문서만 작성한다. 기존 `fix/vibe-cli-node-contract-261001` 작업 트리는 깨끗했다. 공유 기본 체크아웃의 로컬 `main`은 원격과 크게 분기되고 다른 미커밋 파일 4개가 있어 이동·정리하지 않았다.

### 판단·안전 경계
- 독립 `ai-debate` 심판의 #78 판정은 **조건부 소스 전용 GO**였다. 별도 흐름에서 D-47과 소수의견을 허브에 로컬 기록하고 PR 본문에 연결한 뒤 머지했다. D-47 기록상 main의 quality·Windows path audit·validate·Cloudflare Pages·tag-release 5/5 성공, 태그/릴리스 차단 유지, 사용자 flat 설치 불변이다. 완전 CLI 5노드 양성 통합 계획·Store/전송 경로는 여전히 미검증이다.
- 허브 `E:/Coding Infra/AI Infra/Communication/`는 dirty/diverged 상태다. D44–D47은 로컬 기록이며 원격 반영으로 간주하지 않는다. 허브 전체를 무차별 stage/push하지 않는다.
- `distribution/main-source-only.hold`, SessionStart/Release 차단 및 marketplace `313c04b` pin은 현재 유지됐다. **소스 머지는 설치·릴리스·실호출 허가가 아니다.** 사용자 flat `/vibe` 설치는 마지막 확인 시 2.12.24이고, 최신 소스 변경을 설치하지 않았다.
- 사용자 정책: 추가 과금 **$0**, 구독 포함 usage만 사용, 자동충전·초과 과금·결제 설정 변경 금지. Grok CLI/Bot과 모든 모델의 실호출은 정확한 계정·구독 버킷·차단 상태를 검증하기 전에는 하지 않는다. Bot은 GUI-only, CLI/API/MCP로 가능한 작업은 `/vibe`가 직접 맡는다.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | 완전 Claude/Codex 직접 CLI 5노드 debate의 양성 통합 계획·Store/전송 경로를 오프라인 테스트로 검증한다 | 중간 | D-47 소수의견의 첫 후속 |
| B | AGY·Grok CLI에 구독 전용 `claim → send once → lookup → verify` 어댑터를 오프라인 구현·검증한다 | 큼 | 별도 브랜치 |
| C | Claude/Codex 사용자 설치 후보의 자산 보존·호스트 명령·구독 청구를 별도 검증한 뒤 설치 게이트를 다시 판단한다 | 큼 | 소스 머지와 분리 |
| D | 허브 D44–D47 기록의 소유권과 dirty/diverged 이력을 안전하게 조정한다 | 중간 | 허브 전체 push 금지 |

### 핵심 파일과 검증
```text
skills-src/vibe/scripts/orchestrate.py               직접 CLI 후보의 구조 사전검사
skills-src/vibe/scripts/execute_cli.py                Claude CLI 전송 전 검사
skills-src/vibe/scripts/execute_codex_cli.py          Codex CLI 전송 전 검사
skills-src/vibe/scripts/test_orchestrate.py           플래너 회귀 테스트
.github/workflows/skills-ci.yml                       Claude CLI 가짜 전송 CI 추가
skills-src/vibe/references/orchestration.md            운영 계약
distribution/main-source-only.hold                    설치·릴리스 경계
E:/Coding Infra/AI Infra/Communication/DECISIONS.md  D-code (별도 저장소)
```
```powershell
python -B -m unittest discover -s skills-src/vibe/scripts -p test_*.py -q
python -B skills-src/vibe/scripts/selftest.py
python -B .github/skill-ci/run_ci.py
gh pr checks 78 --watch=false
```

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
gh pr view 78 --json number,state,headRefOid,baseRefOid,statusCheckRollup,body
```

---

## 2026-10-01 / `/vibe` 구독 전용 실행 경로와 핸드오프

### 어디까지 왔나
- 작업 시작 기준 `origin/main`: `357a42136b691951a3869169c86d5d5726b75f88` (PR #75 Orca 동시성 수정 머지). 최종 main SHA는 `git rev-parse origin/main`으로 다시 확인한다.
- 이번 세션 PR: [#76 — unsupported provider route 차단](https://github.com/Simon-YHKim/SimonK-stack/pull/76). 코드 커밋 `1733560d853ceeaf0ca2872ff152b661e7613a30`; 문서 추가 전 4/4 원격 검사가 통과했다. 이 문서 커밋 후 CI와 머지 상태를 다시 확인한다.
- `/vibe` 소스 2.12.38에서 AGY·Grok의 `cli`/`orca` 실행 어댑터가 없으면 합성된 런타임·과금 증거로도 `ready`가 되지 않는다. Antigravity는 구매 크레딧 폴백 차단과 정확한 계정·전송 경로별 쿼터 증거도 요구한다.
- 검증: `/vibe` 오프라인 unittest 351/351, `selftest.py` 180/180, skill validator 오류·경고 0, eval 26건 dry-run 입력 확인, `git diff --check` 통과. 실제 구독 청구·모델 품질·실제 Bot 전달의 증명은 아니다.
- 기존 Claude·Codex·`.agents` 사용자 flat `/vibe`는 마지막 관측에서 2.12.24였다. 이 변경은 소스 전용이며 사용자 설치를 수행하지 않았다.

### 활성 인프라·안전 경계
- `distribution/main-source-only.hold`, SessionStart의 source-only 보호, marketplace `313c04b` pin 및 GitHub Release hold를 유지한다. `main` Pages 자동 배포만 Simon이 이번 작업에 허용했다.
- 추가 API 과금 $0, 구독 포함 usage만 사용한다. 자동충전·초과 과금·결제 설정을 변경하지 않는다. 사용자 보고상 xAI 사용량이 소진되어 Grok CLI·Grok Bot 실호출을 하지 않았다.
- Grok Bot은 `/vibe` 내부 GUI-only Relay 어댑터이고 직접 `/vibe-bot` 호출과 호환된다. CLI/API/MCP로 가능한 작업을 Bot으로 보내지 않는다. 실제 활성 roster·Relay·비용/결과 증거 없이는 발송·완료 판정을 하지 않는다.
- 허브 `E:/Coding Infra/AI Infra/Communication/DECISIONS.md`의 D-44는 로컬 기록이다. 허브 저장소는 별도의 dirty/diverged 상태이므로 원격 반영으로 간주하지 않는다.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | PR #76의 최종 main/CI·source-only hold·Pages·이 문서의 도달을 확인하고 다음 개발 브랜치를 정한다 | 작음 | 먼저 |
| B | Claude/Codex CLI의 planner `ready`와 실행 어댑터의 no-skill/node 제한을 일치시킨다. 현재 합성 `step(skills=["explain"])`는 planner를 통과하지만 실제 CLI adapter는 거부한다 | 중간 | 허위 준비 상태의 남은 사례 |
| C | AGY와 Grok CLI에 각각 구독 전용 `claim → send once → lookup → verify` 보호 어댑터를 기존 Store에 연결; 계정·모델·effort·쿼터·credit fallback을 전송 직전 재검증 | 큼 | 한도 복구와 무관하게 오프라인 구현 가능 |
| D | 사용량 복구 후 각 xAI 표면을 새로 관측하되, 정확 계정/버킷·구독 포함·초과 과금 차단이 증명될 때만 실호출; Bot과 CLI의 쿼터를 서로 대체하지 않음 | 중간 | 비용 증거가 없으면 계속 차단 |
| E | Claude/Codex 사용자 설치 후보의 자산 보존·Gstack 런타임·호스트 명령 선택·구독 청구를 별도 검증하고 설치 게이트 재판정 | 큼 | 소스 머지를 설치 준비로 오인 금지 |

### 결정 요약
- D-44 독립 토론 판정: 먼저 허위 `ready` 차단, 이후 AGY/Grok 보호 어댑터를 오프라인 구현. 새 중앙 registry 신설은 기존 planner/Store와 중복되어 보류. 소수 의견은 한도 복구 직후 사용성을 위해 어댑터를 선구현하자는 것과 장기적으로 명시적 준비 상태가 유리하다는 것이다.
- D-45 별도 심판은 #76의 코드·이 문서를 같은 최종 HEAD에서 소스 전용 머지하되, 새 CI/hold·기존 CLI planner/adapter 불일치의 인수 기록을 조건으로 했다. 소수 의견은 CLI의 노드별 실행 제한을 먼저 고치자는 것이다. 사용자 설치·실호출·결제 변경은 이 문서로 승인되지 않는다.

### 핵심 파일 위치
```text
skills-src/vibe/SKILL.md                         메인 스킬 계약·비용 경계
skills-src/vibe/scripts/orchestrate.py            실행 경로·과금·쿼터 planner
skills-src/vibe/scripts/test_orchestrate.py       허위 ready 회귀 테스트
skills-src/vibe/references/orchestration.md       런타임·어댑터 운영 계약
skills-src/vibe/scripts/execute_bot.py            GUI 전용 Bot Relay 어댑터
docs/INSTALL.md                                   후보·사용자 설치 게이트
```

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
gh pr view 76 --json state,headRefOid,baseRefOid,statusCheckRollup
```

`docs/HANDOFF.md`가 아직 `origin/main`에 없으면 PR [#76](https://github.com/Simon-YHKim/SimonK-stack/pull/76)의 본문·변경 파일 또는 아래 브랜치에서 읽는다.

```powershell
git fetch origin fix/vibe-provider-readiness-261001
git show origin/fix/vibe-provider-readiness-261001:docs/HANDOFF.md
```

---
