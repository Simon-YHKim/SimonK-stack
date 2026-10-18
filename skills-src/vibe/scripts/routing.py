# routing.py — legacy Orca policy/builders; live dispatch uses execute_orca.py.
# This is not the frontier registry. Dry output is not execution authorization.
#
# 이 파일이 레인·클래스·effort·가드의 유일한 기계 판독 정본이다.
# SKILL.md 의 표는 여기서 생성한다:  python routing.py --emit-md
# 폼(make_intake.py)과 집계(aggregate_ledger.py)는 이 모듈을 import 한다.
# 표를 두 곳에 손으로 적지 않는다 — 발주 §2.
#
# 슬러그는 2026-09-04 실측 덤프로 확정했다 (발주 §1 게이트):
#   codex : ~/.codex/models_cache.json  → sol / terra / luna 확인
#   agy   : agy models                  → gemini-3.8-flash-{high|medium|low}
#   grok  : grok models + --effort 오류 유도 → grok-4.6, {xhigh|high|medium|low}
#   claude: claude --version 2.1.259
#
# 2026-09-06 갱신 — gpt-6-astra 편입 + effort 허용목록 전수 실측 (Orca 1.4.193).
#   models_cache.json(fetched 2026-09-06T04:07Z, client 0.153.0) 에 priority 1 로
#   gpt-6-astra 가 올라왔다: "Our most capable model for complex, demanding work."
#   ~/.codex/config.toml 의 model 도 이미 gpt-6-astra 다 (sol 에서 바뀐 흔적이
#   config.toml.bak 에 남아 있다).
#   ⚠ D-28 #16 정정(2026-09-16): 위 두 줄은 09-06 시점 기록이다. 2026-09-13 실측
#   config.toml 은 model = "gpt-5.6-sol" · model_reasoning_effort = "xhigh" 이고,
#   models_cache.json(2026-09-13 수신본)에서 sol 도 priority 1 · "Latest frontier agentic
#   coding model." 이다. codex 모델 context_window 는 전부 272K(max 872K)다.
#
#   ⚠ 핵심 실측: **Orca 의 effort 허용목록은 CLI 의 정본보다 좁다.**
#   models_cache 는 astra 가 low~ultra 6단을 다 지원한다고 적지만
#   Orca worker-start 는 astra 에 max·ultra 를 거부한다 (상한 xhigh).
#   codex CLI 는 같은 모델에 ultra·max 를 실제로 받는다 (아래 CODEX_DIRECT 참조).
#   → 그래서 이 파일은 "정책(top/std)"과 "Orca 가 실제로 받는 값(orca_efforts)"을
#     분리해서 들고 있다. 표에 적을 값은 언제나 후자다.
#
#   실측 방법은 probe_orca_efforts() 에 코드로 박아뒀다 — 비용 0 이다.
#   (effort 검증이 worktree 셀렉터 검증보다 먼저 일어나므로, 존재하지 않는
#    worktree 이름을 주면 워커가 뜨지 않은 채 effort 판정만 돌려받는다.)
#
# ── 왜 astra 에 max·ultra 가 안 되는가 (2026-09-06 원인 규명, 추측 아님) ────
#   Orca 앱 번들(app.asar)과 저장소 HEAD 양쪽에서 원본을 읽어 확인했다:
#   `src/shared/agent-session-option-catalog-claude-codex.ts` 의
#   CODEX_SESSION_OPTION_CATALOG 가 **다섯 모델만 하드코딩**하고 있다 —
#       gpt-5.6-sol   → codexEffort('ultra')
#       gpt-5.6-terra → codexEffort('ultra')
#       gpt-5.6-luna  → codexEffort('max')
#       gpt-5.5       → codexEffort('xhigh')
#       gpt-5.2-codex → codexEffort('xhigh')
#   그리고 목록에 없는 모델은 전부  unknownModelOptions: [codexEffort('xhigh')].
#   gpt-6-astra 와 gpt-daybreak-blue-latest 는 **그 목록에 아예 없다.**
#   즉 두 모델은 Orca 입장에서 '모르는 모델'이고, 모르는 모델의 상한이 xhigh 다.
#   (실제로 존재하지 않는 gpt-9-nonexistent 도 정확히 같은 상한을 받는다.)
#
#   Orca 소스의 주석이 이게 의도임을 밝힌다: "Codex model access depends on auth.
#   Keep this seed short and allow unknown persisted ids to pass through instead
#   of claiming a complete list." — 즉 **버그가 아니라 설계된 폴백**이다.
#
#   따라서:
#   · Orca 를 올려도 안 풀린다. 설치본 1.4.193, 최신 1.4.197(2026-09-04) 인데
#     저장소 HEAD 의 그 파일도 여전히 같은 다섯 줄이다. astra 는 테스트 픽스처에만 있다.
#   · 푸는 길은 셋뿐이다 —
#     (a) codex CLI 직행(run_codex_exec) · (b) 목록에 있는 sol/terra 를 ultra 로 쓴다 ·
#     (c) Orca 에 astra 를 seed 에 넣어달라고 올린다(업스트림 변경).
#   · CODEX_EFFORT_CHOICES 의 0번은 'minimal' 이다 — 그래서 codex 레인은
#     minimal 도 받는다(실측 확인). 정책으로는 안 쓰지만 목록에는 사실대로 적는다.
#
# ── 2026-10-04 D-67 — 현행 세대 레인을 옛 레인 옆에 추가한다 (ADD_ALONGSIDE_KEEP_LEGACY) ──
#   허브 토론 dbt-261004-033902 (4벤더 FINAL 4/4 · 심판 Gemini · 확신도 92) 의 조건부 채택.
#   근거는 Orca 1.4.218 app.asar 검증 코드를 읽은 것이다(모델 호출·worker-start 0회):
#   · claude 카탈로그는 별칭 fable·opus·sonnet·haiku 만 안다. claude-opus-5-5 같은 정식 id 는
#     '모르는 모델'이라 low~max 를 받고 --model 을 그대로 넘긴다.
#   · codex 카탈로그는 위의 다섯 모델만 하드코딩한다. gpt-6.1-sol 은 모르는 모델이라
#     minimal~xhigh 만 받는다 — max·ultra 는 거부된다(astra 와 같은 상한).
#   · grok 은 launch-time 모델 선택을 지원하지 않아 grok-4.7 을 고정할 수 없다 → grok 레인은 그대로.
#   그래서 claude-opus-5-5(flag · low~max)와 gpt-6.1-sol(flag · minimal~xhigh)을 새 키로 넣고
#   우선순위 목록·고정 공정·코디네이터를 새 키로 옮긴다. 옛 키는 지우지 않는다 —
#   ledger.py 가 LANES 에 없는 레인의 원장 행을 거부하므로 지우면 과거 원장·스왑 분석이 깨진다.
#   ⚠ '등록'이지 '동작'이 아니다. native send 보류 · 준비 브리지 미구현 · 계정/과금 인증서 부재가
#     그대로다. 읽기 전용 canary(launch.requested ↔ launch.effective 대조)는 2026-10-04 에
#     두 레인 모두 통과했다(2.14.2, run_92ff481d8b2f). 인증서 전까지
#     registry 의 legacy_lane_migration 상태는 pending-transport-and-certificate 다.
#     $0 게이트(모델 포함·초과과금 OFF·API 폴백 OFF)와 G5·Orca 인증서는 새 레인에도 똑같이 걸린다.
#   넣지 않은 것: claude-sonnet-5-5 는 이 근거가 opus-5-5 만 직접 확인했고 registry 가
#     effort 재보정(Claude Code 기본 medium ↔ API 기본 high)을 요구해 sonnet-5 사다리를 물려받을 수 없다.
#     gpt-6-luna 는 Orca 가 6.1-sol 과 같은 폴백으로 받지만 D-67 판정의 후속 조치에 없고,
#     A 클래스 1순위를 바꾸는 별도 결정이다. gpt-6-sol 은 sol 후속을 6.1-sol 로 통일해서 뺐다.
#     → sonnet-5-5·gpt-6-luna 두 건은 2026-10-05 Simon 지시로 넣었다(바로 아래 절).
#
# ── 2026-10-05 Simon 지시 — A 클래스를 현행 세대 레인으로 옮긴다 (2.15.5) ──
#   지시 원문: "5.5로 전환해. 최신모델을써야지 왜 구모델을씀?"
#   D-67 과 같은 ADD_ALONGSIDE_KEEP_LEGACY 다: claude-sonnet-5-5 · gpt-6-luna 를 옛 키 옆에 새 키로 넣고
#   A 클래스 목록을 gpt-6-luna → claude-sonnet-5-5 → claude-opus-5-5 로 바꾼다. 옛 키 claude-sonnet-5 ·
#   gpt-5.6-luna 는 원장 호환용으로만 남긴다(우선순위 밖). 근거는 D-67 의 Orca 1.4.218 읽기다
#   (이번 변경에서 모델 호출·worker-start 0회):
#   · claude 카탈로그는 별칭만 안다 → claude-sonnet-5-5 는 '모르는 모델'이라 low~max 를 받고
#     --model·--effort 를 그대로 넘긴다.
#   · codex 카탈로그 다섯 줄에 gpt-6-luna 가 없다 → 폴백 minimal~xhigh(max·ultra 거부), 6.1-sol 과 같다.
#   · Sonnet 5.5 사다리는 sonnet-5 것을 물려받지 않고 다시 잡았다: std medium(Claude Code·앱 기본값) ·
#     top high(Artificial Analysis 가 Sonnet 5.5 의 가장 경쟁력 있는 설정으로 보는 값). xhigh·max 는
#     토큰 폭증(max 에서 작업당 출력 약 193k 토큰) 때문에 정책 사다리 밖이다 — off-ladder 로만 열린다.
#   · D-90 의 registry 보류(held-until-remeasure)는 이 레인에 한해 Simon 지시가 앞선다(D-90 소수의견:
#     레인에 대한 Simon 의 명시 지시가 우선). shadow task-fit 정책의 Sonnet 5.5 제외(D-90)는 별개의
#     비용 프런티어 결정이라 그대로다(references/task-fit-policy.json 무변경).
#   ⚠ '등록'이지 '동작'이 아니다. 읽기 전용 canary(launch.requested ↔ launch.effective)는 2026-10-05
#     두 레인 모두 통과했다(2.15.5, run_0a369252175f). Orca 런치 계정/과금 인증서 전까지
#     registry legacy_lane_migration = pending-transport-and-certificate 다.
#     $0 게이트(모델 포함·초과과금 OFF·API 폴백 OFF)와 G5·Orca 인증서는 다른 flag 레인과 똑같이 걸린다.
#
# ── 2026-10-12 D-98 — 보안 생성물 게이트를 gpt-6.1-sol @xhigh 로 옮긴다 (2.16.0) ──
#   허브 토론 dbt-261012-124530 (quick · PROVISIONAL 3/4 · 심판 Gemini · 확신도 91).
#   왜: OpenAI API 문서가 별칭 gpt-daybreak-blue-latest 를 deprecated 로 표시했다(종료일·대체 ID 미공지).
#     이 계정 Codex 카탈로그(~/.codex/models_cache.json)는 아직 그 별칭을 list · cyber 로 싣고 은퇴 표시가
#     없지만 다른 cyber 모델도 없다. registry 는 2.15.7 에서 lifecycle: deprecated 로 바꿨고 중앙 계획기는
#     그 후보를 이미 MODEL_NOT_ACTIVE 로 막는다 — 이 표만 폐기된 별칭을 가리켜 게이트 자리가 막혀 있었다.
#   지킨 것: G1(코딩 벤더 claude ≠ 게이트 벤더 codex) · G1_SEC_SAME_MODEL(생성물 게이트 gpt-6.1-sol ≠
#     인가 게이트 gpt-6-astra · 둘 다 codex) · MODEL_NOT_ACTIVE(Daybreak 는 deprecated 그대로).
#   잃은 것: cyber 전용성. 방어 루브릭과 fail-closed 규칙으로 보완하지만 동등하다고 증명된 것은 아니다.
#   규칙 정본: references/security-artifact-gate.md — 루브릭(CWE) · 출력 형식 · 빈/차단/모호 출력 = FAIL ·
#     cyber 모델이 카탈로그에 나타났을 때의 재승격 절차(자동 승격 없음) · canary 기록.
#   canary: 2026-10-12 12:53~12:55 KST · Orca run_8f7a27febc38 · ctx_ff39c4a979ba · 읽기 전용 워커 1개 · 도구 금지.
#     launch.requested == launch.effective(gpt-6.1-sol · xhigh) · rollout turn_context gpt-6.1-sol/xhigh ·
#     결함 4개를 심은 Python 생성물에 GATE: BLOCK + CWE-89·78·22·502 를 정확히 보고 · 안전한 함수 2개는 미보고.
#     워커의 자기보고 모델명은 "gpt-6" 으로 틀렸다 — 자기보고는 근거가 아니다. 심은 샘플 1건이다.
#   옛 키 gpt-daybreak-blue-latest 는 원장 호환용으로만 남긴다. 우선순위·고정 공정 밖이고,
#     새 배정은 validate_plan 이 LANE_DEPRECATED 로 막는다(DEPRECATED_LANES).
#   ⚠ 부작용: 생성물 게이트와 코디네이터(COORDINATOR)가 같은 gpt-6.1-sol 이 된다 → 코딩 라운드마다
#     coordinator_conflict() 가 참이다(경고일 뿐 디스패치를 막지 않는다). 코디네이터를 바꾸는 것은 별도 결정이다.
#
# ── 2026-10-12 D-99 — claude-haiku-5-5 를 A 클래스의 Claude 쪽 첫 폴백으로 넣는다 (2.16.0) ──
#   허브 토론 dbt-261012-124540 (quick · PROVISIONAL 3/4 · 심판 Codex · 확신도 82)의 조건부 채택.
#   조건($0 canary + 정답이 정해진 대표 A 과제)은 통과했다. D-67 과 같은 ADD_ALONGSIDE_KEEP_LEGACY 다.
#   A 클래스 = gpt-6-luna → claude-haiku-5-5 → claude-sonnet-5-5 → claude-opus-5-5.
#   · 1순위는 gpt-6-luna 그대로다(선두 승격이 아니다). Sonnet 5.5 도 그대로 남는다.
#   · Orca claude 카탈로그는 별칭만 안다 → 정식 id claude-haiku-5-5 는 '모르는 모델'이라 low~max 를 받고
#     --model·--effort 를 그대로 넘긴다(claude-sonnet-5-5 와 같다 · Claude Code 2.1.293 이상 필요).
#   · 정책 사다리 std low / top medium(제공사 기본값). high·xhigh·max 는 off-ladder 로만 열린다.
#   canary: 2026-10-12 12:53~12:54 KST · Orca run_8f7a27febc38 · ctx_cd78cf210447 · 읽기 전용 워커 1개 · @low.
#     launch.requested == launch.effective · 세션 기록 message.model claude-haiku-5-5(entrypoint cli) ·
#     정답이 스크립트로 정해진 A 과제 3개(CSV→JSON 변환 · 스키마 위반 id · 로그 레벨 집계) 전부 일치.
#   한계: 작은 과제 3개 · effort 1개다. 큰 입력 · 10만 토큰 초과 입력(API 단가 5배 구간) · 쿼터 절감은 미측정이다.
#     선두 승격이나 Sonnet 5.5 제외는 별도 비교 근거가 있어야 한다.
#   ⚠ '등록'이지 '동작'이 아니다. registry legacy_lane_migration = pending-transport-and-certificate 이고
#     $0 게이트(모델 포함·초과과금 OFF·API 폴백 OFF)와 G5·Orca 인증서는 다른 flag 레인과 똑같이 걸린다.
#
# ── 2026-10-12 D-101 — GPT 쪽은 gpt-6-astra @xhigh 만 · 생성물 게이트는 Daybreak 로 되돌린다 (2.17.0) ──
#   Simon 지시(토론 없음 · 허브 DECISIONS D-101). 원문:
#     "gpt 6.1 sol은 너무 느려서 빼기로 결정. 기획단계 gpt astra xhigh와 opus 5.5. 단순작업 sonet 5.5"
#     "gpt 쪽은 astra 말고는 쓰지마. gpt 를 넣어야한다면 astra xhigh."
#     게이트: "보안게이트는 데이브레이크로 할려했는데 그게 안돼면 opus 5.5로 하자."
#   위 D-67·10-05·D-98·D-99 절은 그 시점 기록이다. 지금 값은 이 절과 아래 표가 정본이다.
#   바뀐 것:
#   · codex 벤더 레인은 gpt-6-astra 하나만 일을 받는다. gpt-6.1-sol · gpt-6-luna · gpt-5.6-sol · gpt-5.6-terra ·
#     gpt-5.6-luna 는 WITHDRAWN_LANES 다 — 키는 원장 호환용으로 남고(ledger.py 가 LANES 밖 레인의 행을 거부한다)
#     새 계획에 넣으면 validate_plan 이 LANE_WITHDRAWN 으로 막는다. 결함 때문이 아니다: gpt-6-luna 는 D-91 canary 를,
#     gpt-6.1-sol 은 D-67·D-98 canary 를 통과했다. 소유자가 뺀 것이다(6.1-sol 은 "너무 느려서").
#   · gpt-6-astra 의 정책 사다리는 std = top = xhigh 이고 EFFORT_PINNED 로 고정한다 — allow_off_ladder 로도
#     xhigh 밖 값은 열리지 않는다(codex 직행 argv 도 같다). 반증 질문과 무관하게 항상 xhigh 라 G7('최상위는
#     반증 YES 에만')은 이 레인에서 구분이 없다. codex 쿼터를 더 쓴다 — 80% 초과 강등은 Claude 레인으로 간다
#     (B·A-verify 2순위 claude-fable-5-1). effort 를 낮추거나 철회된 GPT 레인으로 내려가는 규칙은 없다.
#   · A 클래스 = claude-haiku-5-5 → claude-sonnet-5-5 → claude-opus-5-5. 전부 claude 다 — claude 가 한도에
#     닿으면 A 작업은 codex 로 넘어가지 않고 멈춘다(pick_default 가 lane 없음을 돌려준다).
#     C-realtime = grok-4.6 → claude-opus-5-5 → gpt-6-astra · C-platform = gemini-3.8-flash → claude-opus-5-5 →
#     gpt-6-astra. B · A-verify · D · 코딩 목록은 그대로다.
#   · 코디네이터 = gpt-6-astra @xhigh. astra 는 인가 게이트이자 B·A-verify 1순위라 겸임 경고가 자주 뜬다(경고일 뿐).
#   · 생성물 게이트 = gpt-daybreak-blue-latest @xhigh 로 되돌린다(D-98 의 gpt-6.1-sol 이전을 뒤집는다).
#     제공사는 그 별칭을 여전히 deprecated 로 표시한다 — registry lifecycle: deprecated 와 중앙 계획기의
#     MODEL_NOT_ACTIVE 는 그대로다. 이 표의 LANE_DEPRECATED 만 딱 한 자리(DEPRECATED_LANE_PINS: 고정 공정
#     security-artifact-gate · 그 고정 effort)를 연다. 우선순위 목록 · 코딩 · 다른 공정 · 재시도 · 다른 effort 는 그대로 막힌다.
#     ⚠ 그래서 packaged registry 를 쓰는 중앙 계획기 경로에서는 게이트 후보가 MODEL_NOT_ACTIVE 로 계속 막힌다.
#       게이트 자리는 '고정'이지 '동작'이 아니다. 막히면 게이트는 FAIL 이고(통과가 아니다) 폴백은 Simon 판정 대기다
#       (references/security-artifact-gate.md 의 Open item). Opus 폴백은 구현하지 않았다 — G1 과 충돌한다.
#       (그 시점 기록 — 폴백은 D-102 가 gpt-6-astra @xhigh 로 정했다. 아래 절.)
#   지킨 것: G1 · G1_SEC_SAME_MODEL(생성물 게이트 Daybreak ≠ 인가 게이트 astra) · MODEL_NOT_ACTIVE · $0·G5·인증서 게이트.
#   canary(오케스트레이터 실행 · 이 변경 자체는 모델 호출 0회): 2026-10-12 15:19~15:20 KST · Orca run_b08adccb4ec8 ·
#     ctx_41243c1a0d26 · 읽기 전용 워커 1개 · 도구 금지. launch.requested == launch.effective(gpt-daybreak-blue-latest ·
#     xhigh) · rollout turn_context 같은 값 · D-98 과 같은 결함 4개 샘플에 GATE: BLOCK + CWE-89·78·22·502 정확히 ·
#     안전한 함수 2개 미보고 · 약 30초 · 자기보고 "GPT-5"(틀림). 심은 샘플 1건이고 별칭은 예고 없이 사라질 수 있다.
#   canary 를 돌리지 않은 것: 코디네이터로서의 gpt-6-astra · A 클래스 순서 변경. 근거는 앞선 것뿐이다 —
#     Haiku 5.5 는 D-99 의 정답이 정해진 A 과제 3개, Sonnet 5.5 는 D-91 canary.
#
# ── 2026-10-12 D-102 — 생성물 게이트 폴백: Daybreak 가 설 수 없을 때만 gpt-6-astra @xhigh (2.18.0) ──
#   Simon 판정(토론 없음 · 허브 DECISIONS D-102): 위 D-101 절의 "폴백은 Simon 판정 대기"가 이것으로 끝났다.
#   선택지 (가) claude-opus-5-5 + G1 완화 · (나) gpt-6-astra 가 두 보안 게이트를 겸임 + G1_SEC_SAME_MODEL 완화 중 (나).
#   Simon 의 앞선 말 "그게 안돼면 opus 5.5로 하자"는 이 판정이 대체한다 — 코딩이 claude-opus-5-5 라 (가)는
#   같은 모델이 자기 산출물을 검사한다.
#   바뀐 것:
#   · FIXED_FALLBACKS = {security-artifact-gate: (gpt-6-astra, xhigh)}. 고정 배정은 그대로 Daybreak 다 — 설 수 있으면
#     Daybreak 가 먼저다.
#   · validate_plan(..., fixed_unavailable={공정: [사유]}) — 호출자가 "고정 레인이 설 수 없다"를 사유와 함께 밝혔을 때만
#     그 공정이 폴백 레인(고정 effort)에 서도 FIXED_LANE_OVERRIDDEN 을 내지 않는다. 같은 조건에서, 그리고 인가 게이트가
#     자기 고정 레인에 있을 때만 G1_SEC_SAME_MODEL 을 면제한다. 면제는 notes 에 남는다.
#   · 사유 없이 폴백 레인에 두면 예전과 똑같이 FIXED_LANE_OVERRIDDEN + G1_SEC_SAME_MODEL 이다.
#     설 수 없다고 해 놓고 고정 레인에 배정하면 FIXED_LANE_UNAVAILABLE 이다.
#   · 중앙 계획기(orchestrate.py)는 호스트의 요청을 받지 않고, 제시받은 후보를 거부한 자기 기록으로 이 사유를 만든다: 게이트 단계에 제시된
#     Daybreak Orca 후보가 전부 가용성 사유로 거부됐을 때만 단계에 gate_fallback 을 남긴다.
#   지킨 것: G1(코딩 벤더 claude ≠ 게이트 벤더 codex) · MODEL_NOT_ACTIVE 등 계획기의 Daybreak 차단 · LANE_DEPRECATED 의
#     한 자리 예외 · $0·G5·인증서 게이트. 폴백은 '설 수 없음'에만 쓴다 — Daybreak 가 실제로 돌아 BLOCK · 빈 출력 ·
#     차단 · 모호한 판정을 낸 뒤에는 폴백하지 않는다(그건 FAIL 이다. references/security-artifact-gate.md).
#   잃은 것: 폴백 상태에서는 한 모델이 두 보안 질문에 모두 답한다 — 두 게이트가 서로 독립된 검사가 아니다.
#   canary(오케스트레이터 실행): 2026-10-12 23:26 KST · Orca run_3607f8833d7e · ctx_56f442610119 · 워커 1개 · 도구 금지.
#     launch.requested == launch.effective(gpt-6-astra · xhigh) · rollout turn_context 같은 값 · D-98·D-101 과 같은
#     결함 4개 샘플에 GATE: BLOCK + CWE-89·78·22·502 정확히 · 안전한 함수 2개 미보고 · 자기보고 "unknown". 심은 샘플 1건이다.
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

LEGACY_EXECUTION_DISABLED = "LEGACY_EXECUTION_DISABLED"
LEGACY_EXECUTION_MESSAGE = (
    LEGACY_EXECUTION_DISABLED + ": use orchestrate.py, run_state.py and the guarded "
    "execute_orca.py adapter with a fresh plan/account/cost certificate; "
    "unsupported transports stay blocked. No legacy live preflight or direct CLI fallback."
)

# Windows 콘솔 기본이 cp949 라 em-dash 하나로 스크립트가 죽는다 (실측 2026-09-04).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# ── 레인 카탈로그 (발주 §3) ──────────────────────────────────────
#  effort_style 이 세 가지인 것이 이 설계의 핵심이다:
#    flag         : CLI 플래그로 넘긴다            (codex --effort / grok --effort)
#    slug-suffix  : effort 가 모델 슬러그에 박혀 있다 (agy gemini-3.8-flash-high)
#    prompt-keyword: 프롬프트 첫 줄 키워드로 발동한다 (claude ultracode)
#  → 그래서 "슬러그"와 "effort"를 분리해 두고 slug_for() 가 조립한다.
# dispatch: 오르카 worker-start 로 실제 기동이 되는가 (2026-09-04 실측)
#   "orca"          --agent + --model + --effort 전부 사용 가능
#   "orca-no-model" --agent 만. --model 을 주면 거부된다
#   "unavailable"   오르카에 agent 가 등록돼 있지 않아 워커로 못 띄운다
#
# orca_efforts: **Orca worker-start 가 실제로 받는 값** (2026-09-06 전수 실측).
#   top/std 는 '정책'이고 orca_efforts 는 '물리적 상한'이다. 둘을 섞지 말 것 —
#   luna 의 top 이 medium 인 것은 Orca 가 못 받아서가 아니라 싼 레인에 판단을
#   맡기지 않기로 한 결정이다(그래서 max 도 받지만 정책상 안 쓴다).
#   off-ladder(정책 밖) 값은 dispatch_argv(..., allow_off_ladder=True) 로만 쓴다.
LANES = {
    "claude-opus-5-5": {
        # D-67 (2026-10-04) — claude-opus-5 의 후속. prompt-keyword(ultracode)가 아니라
        #   --effort 플래그로 전달한다: Orca claude 카탈로그는 이 id 를 모르는 모델로 보고 low~max 를 받는다.
        #   허브 핀 claude-opus-5-5@max 와 같은 상한이다.
        # ⚠ 읽기 전용 canary 는 통과했다(2026-10-04 · @high · requested == effective).
        #   native send · 계정/과금 인증서 전까지 동작 레인이 아니다
        #   (registry legacy_lane_migration = pending-transport-and-certificate).
        "cli": "claude", "vendor": "claude", "effort_style": "flag", "dispatch": "orca",
        "top": "max", "std": "high", "ctx": "canary 통과 · 인증서 전 · Orca 미등록 id → low~max",
        "orca_efforts": ("low", "medium", "high", "xhigh", "max"),
    },
    "claude-opus-5": {
        # D-67: 원장 호환용으로만 남긴다. 우선순위 목록·고정 공정에서 뺐다 —
        #   prompt-keyword 레인이라 guarded Orca(execute_orca: flag 전용)로는 실행되지 않는다.
        "cli": "claude", "vendor": "claude", "effort_style": "prompt-keyword",
        "top": "ultracode", "std": "standard", "ctx": "1M · D-67 원장 호환용(우선순위 밖)", "dispatch": "orca",
        # claude 는 effort 를 프롬프트 키워드로 받으므로 여기 값은 '정책 라벨'이고
        # 와이어로 나가는 값은 항상 --effort max 다 (dispatch_argv 참조).
        # 참고 실측: agent claude 의 와이어 허용목록은 low·medium·high·xhigh·max.
        # ultra·ultracode·standard 를 --effort 로 넘기면 invalid_argument 다.
        # 순서는 낮은 → 높은 (ceiling_for 가 마지막 원소를 상한으로 읽는다).
        "orca_efforts": ("standard", "ultracode"),
    },
    "claude-fable-5-1": {
        # 2026-09-13 22:28 Simon 결정 — fable 배정 금지 해제 (허브 DECISIONS.md RATIFY).
        #   금지 목록의 claude-fable-5 는 이전 세대라 레인으로 들이지 않고 현행 세대를 둔다.
        # Orca 1.4.200 claude 카탈로그(app.asar 원문): 별칭 fable = "Most capable for the
        #   hardest, longest-running tasks", effort 선택지 low·medium·high·xhigh·max.
        # 2026-09-13 22:33 실측(run_5f053ba46b80, 없는 worktree 로 worker-start — 워커 기동 0):
        #   low=O medium=O high=O xhigh=O max=O ultra=X. opus·sonnet 도 같은 결과.
        #   ⚠ Orca 는 --model 문자열을 검증하지 않으므로 이 측정은 '모델이 돈다'의 증거가 아니다.
        # ⚠ 쿼터는 claude 일반 weekly 가 아니라 claude.fableWeekly 버킷(Orca 가 따로 추적).
        #   두 한도가 서로 영향을 주는지는 미확인.
        # D-28 2단계(2026-09-16): M1 실워커 1회 통과 — run_c0c4a6905e26 · claude.exe --model claude-fable-5-1
        #   --effort high 로 기동 · 읽기 전용 과제 정답 3/3 · worker_done · filesModified []. 코딩·B 비코딩 2순위로 편입.
        # prompt-keyword(ultracode) 방식이 아니라 --effort 플래그로 전달한다 — Orca 카탈로그의 launchArgs 가 --effort 다.
        "cli": "claude", "vendor": "claude", "effort_style": "flag", "dispatch": "orca",
        "top": "max", "std": "high", "ctx": "1M · 쿼터 fableWeekly 별도 · API 단가 Opus 5의 2배",
        "quota_bucket": "fableWeekly",
        "orca_efforts": ("low", "medium", "high", "xhigh", "max"),
    },
    "claude-sonnet-5-5": {
        # 2026-10-05 Simon 지시("5.5로 전환해. 최신모델을써야지 왜 구모델을씀?") — claude-sonnet-5 의 후속.
        #   D-101 (2026-10-12): A 클래스 2순위 — 1순위 claude-haiku-5-5 다음이다("단순작업 sonet 5.5").
        #   (10-05 에는 codex gpt-6-luna 가 강등·금지일 때 받는 2순위였다.) --effort 플래그로 전달한다:
        #   Orca claude 카탈로그는 이 정식 id 를 모르는 모델로 보고 low~max 를 받는다(D-67 의 1.4.218 읽기).
        # effort 사다리는 다시 잡았다(sonnet-5 의 medium/xhigh 를 물려받지 않는다):
        #   std medium = Claude Code·앱 기본값 · top high = Artificial Analysis 가 Sonnet 5.5 의 가장 경쟁력 있는
        #   설정으로 보는 값. xhigh·max 는 토큰 폭증(max 에서 작업당 출력 약 193k 토큰)이라 정책 사다리에서 뺐다 —
        #   Orca 는 받으므로 allow_off_ladder 로만 열린다.
        # 쿼터는 claude 일반 weekly 다(fable 처럼 별도 버킷이 아니다).
        # ⚠ 읽기 전용 canary 는 통과했다(2026-10-05 · requested == effective · 세션 기록 모델 일치).
        #   계정/과금 인증서 전까지 동작 레인이 아니다
        #   (registry legacy_lane_migration = pending-transport-and-certificate · 게이트는 다른 flag 레인과 같다).
        "cli": "claude", "vendor": "claude", "effort_style": "flag", "dispatch": "orca",
        "top": "high", "std": "medium", "ctx": "canary 통과 · 인증서 전 · Orca 미등록 id → low~max · xhigh·max 정책 밖",
        "orca_efforts": ("low", "medium", "high", "xhigh", "max"),
    },
    "claude-sonnet-5": {
        # D-28 #2 (Simon 확정 2026-09-16) · 2단계 M1 통과 — run_c0c4a6905e26 · claude.exe --model claude-sonnet-5
        #   --effort medium 으로 기동 · 읽기 전용 과제 정답 3/3 · worker_done · filesModified [].
        # Orca 1.4.200 claude 카탈로그: 별칭 sonnet("Efficient for routine tasks", isDefault) ·
        #   effort low·medium·high·xhigh·max (2026-09-13 22:33 실측: ultra 만 거부).
        # 쿼터는 claude 일반 weekly 를 쓴다. A 클래스 2순위 — codex(luna)가 강등·금지일 때 받는다.
        # 2026-10-05 Simon 지시: 원장 호환용(우선순위 밖). A 클래스 2순위는 claude-sonnet-5-5 가 받는다.
        "cli": "claude", "vendor": "claude", "effort_style": "flag", "dispatch": "orca",
        "top": "xhigh", "std": "medium", "ctx": "1M · API 단가 Opus 5의 0.4배 · 원장 호환용(우선순위 밖)",
        "orca_efforts": ("low", "medium", "high", "xhigh", "max"),
    },
    "claude-haiku-5-5": {
        # D-99 (2026-10-12) — 새 레인(옛 레인의 후속이 아니다). 그때는 A 클래스의 Claude 쪽 첫 폴백(2순위)이었다.
        #   D-101 (같은 날 · Simon 지시): gpt-6-luna 가 철회돼 **A 클래스 1순위**다. 선두 승격의 근거는
        #   D-99 canary(작은 A 과제 3개 · @low)뿐이다 — 순서를 바꾼 뒤의 canary 는 돌리지 않았다.
        #   --effort 플래그로 전달한다: Orca claude 카탈로그는 이 정식 id 를 모르는 모델로 보고 low~max 를 받는다
        #   (claude-sonnet-5-5 와 같다 · D-67 의 1.4.218 읽기). Claude Code 2.1.293 이상이 필요하다.
        # effort 사다리: std low(canary 가 확인한 값) · top medium(제공사 API·Claude Code 기본값).
        #   high·xhigh·max 는 Orca 가 받지만 정책 밖이다 — allow_off_ladder 로만 열린다.
        #   판단이 섞인 A 작업은 여기 두지 않는다(R1: A-verify 로 승격).
        # 쿼터는 claude 일반 weekly 다(fable 처럼 별도 버킷이 아니다).
        # ⚠ 읽기 전용 canary 는 통과했다(2026-10-12 · run_8f7a27febc38 · @low · requested == effective ·
        #   세션 기록 모델 일치 · 정답이 정해진 A 과제 3/3). 계정/과금 인증서 전까지 동작 레인이 아니다
        #   (registry legacy_lane_migration = pending-transport-and-certificate · 게이트는 다른 flag 레인과 같다).
        #   작은 과제 3개·effort 1개만 봤다 — 큰 입력·10만 토큰 초과 입력(API 단가 5배 구간)·쿼터 절감은 미측정.
        "cli": "claude", "vendor": "claude", "effort_style": "flag", "dispatch": "orca",
        "top": "medium", "std": "low",
        "ctx": "canary 통과 · 인증서 전 · Orca 미등록 id → low~max · high 이상 정책 밖 · 10만 토큰 초과 입력 미측정",
        "orca_efforts": ("low", "medium", "high", "xhigh", "max"),
    },
    "gpt-6-astra": {
        # 2026-09-06 신설. models_cache priority 1 · "Our most capable model for
        # complex, demanding work." · GPT-6 세대 · ctx 272K(최대 872K).
        # ⚠ Orca 상한은 xhigh 다 — max·ultra 는 daybreak 과 똑같이 거부된다.
        #   같은 codex 벤더인 sol·terra 는 ultra 가 통과하므로 이건 모델별 목록이다.
        #   models_cache 가 "ultra 지원"이라고 적는 것과 무관하다.
        # ultra·max 가 정말 필요하면 Orca 워커가 아니라 codex CLI 직행이다
        #   (CODEX_DIRECT / run_codex_exec — 2026-09-06 실호출로 확인).
        # D-101 (2026-10-12 · Simon 지시 "gpt 를 넣어야한다면 astra xhigh"): codex 벤더에서 일을 받는 유일한 레인이고
        #   **항상 xhigh** 다. 사다리 std = top = xhigh(옛 값 std high), EFFORT_PINNED 로 고정해 allow_off_ladder 와
        #   codex 직행 argv 로도 다른 값이 열리지 않는다. 위의 'ultra·max 는 codex CLI 직행' 은 2026-09 기록이다.
        "cli": "codex", "vendor": "codex", "effort_style": "flag", "dispatch": "orca",
        "top": "xhigh", "std": "xhigh", "ctx": "272K(최대 872K) · Orca 상한 xhigh · D-101 항상 xhigh · 유일한 GPT 레인",
        "orca_efforts": ("minimal", "low", "medium", "high", "xhigh"),
    },
    "gpt-6.1-sol": {
        # D-67 (2026-10-04) — sol 의 후속(registry 의 gpt-6-sol ↔ gpt-6.1-sol 불일치는 6.1-sol 로 통일).
        #   Codex 카탈로그 priority 1. Orca codex 카탈로그에 없는 모델이라 astra 와 같은
        #   폴백(codexEffort('xhigh'))을 받는다 → minimal~xhigh 만, max·ultra 는 거부. 허브 핀 @xhigh.
        # ⚠ 읽기 전용 canary 는 통과했다(2026-10-04 · @xhigh · requested == effective, 서버측 모델 미확인).
        # ⚠ D-101 (2026-10-12): Simon 이 뺐다("gpt 6.1 sol은 너무 느려서 빼기로 결정"). 원장 호환용 키로만 남는다 —
        #   코디네이터 · 생성물 게이트(D-98) · C 클래스 2순위에서 모두 빠졌고, 계획에 넣으면 LANE_WITHDRAWN 이다.
        "cli": "codex", "vendor": "codex", "effort_style": "flag", "dispatch": "orca",
        "top": "xhigh", "std": "high", "ctx": "D-101 철회 · 원장 호환용(우선순위 밖) · Orca 상한 xhigh",
        "orca_efforts": ("minimal", "low", "medium", "high", "xhigh"),
    },
    "gpt-5.6-sol": {
        # D-67: gpt-6.1-sol 뒤 폴백으로 남겼었다(C 클래스 목록 끝). 원장 호환은 이 키로 유지한다.
        # D-101 (2026-10-12): C 클래스 끝 폴백에서도 뺐다 — 원장 호환용 키다(LANE_WITHDRAWN).
        "cli": "codex", "vendor": "codex", "effort_style": "flag", "dispatch": "orca",
        "top": "ultra", "std": "high", "ctx": "272K(최대 872K) · D-101 철회 · 원장 호환용(우선순위 밖)",   # D-28 #16: 1.5M 은 옛 값
        "orca_efforts": ("minimal", "low", "medium", "high", "xhigh", "max", "ultra"),
    },
    "gpt-5.6-terra": {
        # D-101 (2026-10-12): 어떤 목록에도 없던 키다. 원장 호환용으로 남고 계획에 넣으면 LANE_WITHDRAWN 이다.
        "cli": "codex", "vendor": "codex", "effort_style": "flag", "dispatch": "orca",
        "top": "max", "std": "medium", "ctx": "272K(최대 872K) · D-101 철회 · 원장 호환용(우선순위 밖)",   # D-28 #9 최상위 high→max(Simon 확정 09-16) · #16 ctx
        "orca_efforts": ("minimal", "low", "medium", "high", "xhigh", "max", "ultra"),
    },
    "gpt-6-luna": {
        # 2026-10-05 Simon 지시 — gpt-5.6-luna 의 후속. 그때 A 클래스 1순위였다.
        #   Orca codex 카탈로그 다섯 줄에 없는 모델이라 6.1-sol·astra 와 같은 폴백(codexEffort('xhigh'))을
        #   받는다 → minimal~xhigh 만, max·ultra 는 거부(5.6-luna 는 seed 에 있어 max 까지 받았다).
        # 정책 사다리는 gpt-5.6-luna 와 같은 low/medium 이다 — 싼 레인에 판단을 맡기지 않는다(D-28 #10 보류 유지).
        # ⚠ 읽기 전용 canary 는 통과했다(2026-10-05 · D-91 · requested == effective · 세션 기록 모델 일치).
        # ⚠ D-101 (2026-10-12): Simon 지시("gpt 쪽은 astra 말고는 쓰지마")로 A 클래스에서 뺐다. 결함 때문이 아니다 —
        #   canary 는 통과한 레인이다. 원장 호환용 키로만 남고 계획에 넣으면 LANE_WITHDRAWN 이다.
        "cli": "codex", "vendor": "codex", "effort_style": "flag", "dispatch": "orca",
        "top": "medium", "std": "low", "ctx": "D-101 철회(결함 아님 · D-91 canary 통과) · 원장 호환용(우선순위 밖) · Orca 상한 xhigh",
        "orca_efforts": ("minimal", "low", "medium", "high", "xhigh"),
    },
    "gpt-5.6-luna": {
        # 2026-10-05 Simon 지시: 원장 호환용(우선순위 밖). A 클래스 1순위는 gpt-6-luna 가 받는다.
        # D-101 (2026-10-12): gpt-6-luna 도 철회됐다. 이 키는 계획에 넣으면 LANE_WITHDRAWN 이다.
        "cli": "codex", "vendor": "codex", "effort_style": "flag", "dispatch": "orca",
        "top": "medium", "std": "low", "ctx": "272K(최대 872K) · 최저가 · 원장 호환용(우선순위 밖)",   # D-28 #10 보류(사다리 유지) · #16 ctx
        # max 까지 받지만 ultra 는 거부된다. 정책상 medium 을 넘기지 않는다.
        "orca_efforts": ("minimal", "low", "medium", "high", "xhigh", "max"),
    },
    "gpt-daybreak-blue-latest": {
        # Simon 이 codex 모델 선택지에서 찾아냈다 (2026-09-04).
        # 정본은 ~/.codex/models_cache.json — display_name "Daybreak Blue",
        # "Latest frontier agentic coding model for broad defensive cybersecurity work."
        # 보안 전용 프론티어 모델이라 생성물 안전성 게이트에 고정 배정한다.
        # ⚠ 기본 effort 가 low 다 — sol 과 같은 함정. effort 를 반드시 명시한다.
        #
        # ⚠⚠ 상한이 xhigh 다. models_cache.json 은 max·ultra 도 지원한다고 적지만
        #     Orca 는 거부한다 (2026-09-04 실기동 실측):
        #       --effort ultra → "Agent codex model gpt-daybreak-blue-latest
        #                         does not support effort ultra"
        #       --effort max   → 같은 거부 / --effort xhigh → 기동 성공
        #     같은 codex 벤더인 sol 은 ultra 가 통과한다 — 허용 목록이 **모델별**이고
        #     CLI 의 정본과도 다르다. 표의 값은 Orca 가 실제로 받는 값이어야 한다.
        #
        # 2026-09-06 재측정: **바뀐 것이 없다.** models_cache 는 여전히 ultra 를
        # 지원한다고 적고 Orca 는 여전히 max·ultra 를 거부한다(상한 xhigh).
        # 갱신된 것은 모델 실체(-latest 포인터)지 Orca 에서 쓸 수 있는 effort 가 아니다.
        #
        # ⚠ D-98 (2026-10-12 오전): OpenAI 가 이 별칭을 deprecated 로 표시해(종료일·대체 ID 미공지) 생성물 게이트를
        #   gpt-6.1-sol @xhigh 로 옮기고 이 키를 원장 호환용으로만 남겼었다. 위 설명은 2026-09 기록이다.
        # ⚠ D-101 (2026-10-12 오후 · Simon 지시 "보안게이트는 데이브레이크로"): 생성물 게이트의 고정 레인으로
        #   **되돌렸다**(references/security-artifact-gate.md). 제공사 표시는 그대로 deprecated 다 —
        #   registry lifecycle: deprecated 와 중앙 계획기의 MODEL_NOT_ACTIVE 는 건드리지 않았다.
        #   DEPRECATED_LANES 에 그대로 있고, validate_plan 은 DEPRECATED_LANE_PINS 의 한 자리
        #   (고정 공정 security-artifact-gate · 고정 effort xhigh)만 통과시킨다. 우선순위 목록·코딩·다른 공정·
        #   재시도·다른 effort 에 넣으면 여전히 LANE_DEPRECATED 다. 별칭은 예고 없이 사라질 수 있다 —
        #   실행 전마다 이 계정 Codex 카탈로그를 확인하고, 없거나 출력이 비거나 차단되면 게이트는 FAIL 이다.
        "cli": "codex", "vendor": "codex", "effort_style": "flag", "dispatch": "orca",
        "top": "xhigh", "std": "high",
        "ctx": "폐기 표시(deprecated) 별칭 · D-101 생성물 게이트 고정 전용(그 밖은 LANE_DEPRECATED) · Orca 상한 xhigh",
        "orca_efforts": ("minimal", "low", "medium", "high", "xhigh"),
    },
    "gemini-3.8-flash": {
        # ⚠ Orca 의 agent id 는 CLI 이름이 아니라 **좌석 이름**이다.
        #   --agent agy         → agent_unconfigured  (틀린 id)
        #   --agent antigravity → 인식됨              (정본)
        #   CLI 바이너리는 agy 지만 Orca 에는 antigravity 로 등록돼 있다.
        "cli": "antigravity", "cli_binary": "agy",
        "vendor": "gemini", "effort_style": "slug-suffix",
        "top": "high", "std": "medium", "ctx": "Gemini Flash 계열",
        # D-28 #12 (Simon 확정 2026-09-16): Orca 워커로는 과제가 전달되지 않는다 —
        #   재현 2/2(SKILL.md 6-2) · 원장 A 탐색 실패·시간초과 3회 · 2026-09-13 21:16 T4 exit 15.
        #   새 문자열(cli-direct 등)은 가드를 통과한 뒤 antigravity 로 기동돼 실패를 재현한다(D-28 N4 실측)
        #   → 기존 값 "unavailable" 만 쓴다. 필요하면 CLI 직행(agy --print). 해제 조건 = M6(--timeout-ms 재확인).
        #   (이전 값 "orca-no-model": --model 은 Claude·Codex·Cursor 만 받는다)
        "dispatch": "unavailable",
        # 2026-09-06 실측: --model 을 주면 "Agent antigravity does not support
        # launch-time model selection". effort 는 슬러그에 들어가므로 목록도 슬러그 기준.
        "orca_efforts": ("low", "medium", "high"),
    },
    "grok-4.6": {
        "cli": "grok", "vendor": "grok", "effort_style": "flag",
        "top": "xhigh", "std": "high", "ctx": "500K · 200K초과 2배 과금",
        # 실측: --agent grok 은 되지만 --model 을 주면 거부된다
        # (orca help: "--model supports Claude, Codex, and Cursor")
        # 2026-09-06 재확인: "Agent grok does not support launch-time model selection".
        # --model 이 안 붙으므로 --effort 도 붙이지 않는다 → 목록은 grok CLI 기준이다.
        "dispatch": "orca-no-model",
        "orca_efforts": ("low", "medium", "high", "xhigh"),
    },
}

# 배정 금지 (발주 §3) — 용도 미검증 / R&R 미확정
#   gpt-5.4-mini 는 2026-08-31 은퇴했다 (models_cache 의 upgrade.retirement_at,
#   대체 모델 gpt-5.6-luna). 은퇴 모델을 슬러그로 넘기면 Orca 는 통과시키고
#   codex 가 런타임에 400 을 낸다 — 아래 MODEL_ID_UNVALIDATED 참조.
#
#   2026-09-13 22:28 — claude-fable-5 를 금지 목록에서 뺐다 (Simon 결정, 허브 DECISIONS.md RATIFY).
#   이전 세대 claude-fable-5 는 레인으로 들이지 않고 현행 세대 claude-fable-5-1 을 LANES 에 둔다.
#   LANES 에 없는 슬러그는 validate_effort 가 unknown lane 으로 막으므로 claude-fable-5 는 여전히 배정되지 않는다.
FORBIDDEN_LANES = {"gpt-5.3-codex-spark", "gpt-reserve",
                   "codex-auto-review", "gpt-5.4-mini"}

# 제공사가 폐기 표시한 레인 (D-98 · 2026-10-12).
#   FORBIDDEN_LANES 와 다르다: 이 키는 LANES 에 남아 과거 원장 행을 읽을 수 있다(원장 호환용).
#   새 계획에 넣는 것만 validate_plan 이 LANE_DEPRECATED 로 막는다 — 중앙 계획기의
#   MODEL_NOT_ACTIVE(registry lifecycle)와 별개로, 이 표만으로도 새 일이 가지 않게 한다.
#   폐기가 풀리거나 대체 모델이 생겨도 여기서 조용히 빼지 않는다 — 별도 결정 기록이 먼저다.
DEPRECATED_LANES = {"gpt-daybreak-blue-latest"}

# 폐기 표시된 레인이 그래도 서는 단 한 자리 (D-101 · 2026-10-12 · Simon 지시 "보안게이트는 데이브레이크로").
#   {레인: 공정}. validate_plan 은 다음이 **모두** 참일 때만 LANE_DEPRECATED 를 내지 않는다:
#     ① 공정이 여기 적힌 공정이고 ② 그 공정의 고정 배정(PROCESSES)이 지금도 이 레인이며
#     ③ 명시 effort 가 없거나 고정 effort 와 같다.
#   다른 공정 · 우선순위 목록 · 코딩 · 재시도(revalidate_for_retry) · 다른 effort 는 그대로 막힌다.
#   registry 의 lifecycle: deprecated 와 중앙 계획기의 MODEL_NOT_ACTIVE 는 이 예외와 무관하게 그대로다.
#   고정 배정을 다른 레인으로 옮기면 ②가 거짓이 되어 이 예외는 저절로 닫힌다.
DEPRECATED_LANE_PINS = {"gpt-daybreak-blue-latest": "security-artifact-gate"}

# 소유자가 뺀 레인 (D-101 · 2026-10-12 · Simon 지시 "gpt 쪽은 astra 말고는 쓰지마. gpt 를 넣어야한다면 astra xhigh.").
#   FORBIDDEN_LANES(용도 미검증·은퇴 — LANES 에 없다)와도, DEPRECATED_LANES(제공사가 폐기 표시)와도 다르다:
#   제공사 쪽에서는 멀쩡한 모델이고 canary 도 통과했지만 소유자가 라우팅에서 뺐다. 키는 LANES 에 남아 과거 원장
#   행을 읽는다(ledger.py 가 LANES 밖 레인의 행을 거부한다). 새 계획에 넣으면 validate_plan 이 LANE_WITHDRAWN
#   (계획기에서는 ORCA_LANE_WITHDRAWN)으로 막고, 예외 자리는 없다. codex 직행 argv(codex_exec_argv)도 막는다.
#   불변식(테스트가 잡는다): codex 벤더 LANES 키 = {gpt-6-astra} ∪ DEPRECATED_LANES ∪ WITHDRAWN_LANES.
#   새 codex 레인을 LANES 에 넣으면서 여기에도 우선순위 목록에도 넣지 않으면 그 테스트가 실패한다.
#   되살리려면 여기서 조용히 빼지 않는다 — Simon 의 지시나 별도 결정 기록이 먼저다.
WITHDRAWN_LANES = {"gpt-6.1-sol", "gpt-6-luna", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"}

# effort 가 한 값으로 고정된 레인 (D-101). 정책 사다리(std/top)만으로는 allow_off_ladder 가 다른 값을 열 수 있어
#   따로 고정한다 — validate_effort 와 codex_exec_argv 가 이 값 밖을 전부 거부한다(off-ladder 포함).
#   원장은 영향받지 않는다: ledger_efforts 는 과거 행(astra@high·@medium)을 계속 읽는다.
EFFORT_PINNED = {"gpt-6-astra": "xhigh"}

# 고정 공정의 폴백 (D-102 · 2026-10-12 · Simon 판정). {공정: (레인, effort)}.
#   고정 배정(PROCESSES)은 바뀌지 않는다. 폴백은 호출자가 validate_plan(fixed_unavailable={공정: [사유]})으로
#   "고정 레인이 설 수 없다"를 사유와 함께 밝혔을 때만 열린다 — 사유가 없으면 예전처럼 FIXED_LANE_OVERRIDDEN 이다.
#   생성물 게이트가 폴백에 서면 두 보안 게이트가 같은 모델(gpt-6-astra)이 된다. G1_SEC_SAME_MODEL 은 그 상태 하나에서만
#   면제한다(_sec_same_model_waived). G1(코딩 벤더 ≠ 게이트 벤더)은 면제하지 않는다 — 폴백 레인도 codex 다.
#   '설 수 없음'은 가용성 문제다(계획기 거부 · 카탈로그에서 사라짐). 게이트가 돌아서 낸 판정은 폴백 사유가 아니다.
FIXED_FALLBACKS = {"security-artifact-gate": ("gpt-6-astra", "xhigh")}

# ⚠ Orca 는 --model 문자열을 검증하지 않는다 (2026-09-06 실측).
#   존재하지 않는 gpt-9-nonexistent 도 --effort high 면 effort 검증을 통과한다
#   (unknown 모델에는 기본 목록 low·medium·high·xhigh 가 적용된다).
#   즉 슬러그 오타는 Orca 단계에서 안 잡히고 워커가 뜬 뒤 codex 가 죽는다.
#   → 이 파일의 LANES 키가 사실상 유일한 오타 방어선이다. 임의 슬러그를 넣지 말 것.
MODEL_ID_UNVALIDATED = True

# codex CLI 직행에서만 닿는 effort (Orca 워커로는 못 간다) — 2026-09-06 실호출 확인.
#   echo "..." | codex exec -c model_reasoning_effort="ultra" -
#   astra·daybreak 은 Orca 에서 xhigh 가 상한이지만 CLI 에서는 ultra·max 가 돈다.
CODEX_DIRECT_EFFORTS = ("low", "medium", "high", "xhigh", "max", "ultra")

VENDORS = ["claude", "codex", "gemini", "grok"]

# ── 클래스 → 레인 우선순위 (발주 §5) ────────────────────────────
CLASS_LANES = {
    # D-28 #3 (Simon 확정 2026-09-16): gemini(과제 전달 실패)·grok(402)을 강등·탐색 목적지에서 뺀다.
    #   2026-09-20 에 grok 402 는 풀렸지만 A 목록에는 그대로 넣지 않는다 — 빼둔 이유가 가용성만이
    #   아니라 산출물 제약(CSV·카운트·분류 라벨만)이기 때문이다. grok 은 C-realtime 1순위로만 쓴다.
    #   검증 전 목록 = luna → opus. claude-sonnet-5 는 M1 실워커 1회 통과 뒤 2순위로 들어간다.
    #   2단계(2026-09-16 M1 통과): sonnet 을 2순위로 넣었다.
    # D-67 (2026-10-04): 모든 목록에서 claude-opus-5(prompt-keyword · guarded Orca 불가)를
    #   claude-opus-5-5 로 바꿨다. sol 은 gpt-6.1-sol 을 같은 자리에 두고 gpt-5.6-sol 은 목록 끝 폴백으로 남긴다 —
    #   끝에 두는 이유: 같은 codex 벤더라 쿼터 강등(pick_default)에서는 둘이 함께 건너뛰어지고,
    #   2·3순위의 벤더 교차(탐색 슬롯 · 스왑 비교 · 표의 3후보)를 바꾸지 않기 위해서다.
    # 2026-10-05 Simon 지시("5.5로 전환해. 최신모델을써야지 왜 구모델을씀?"): 1순위 gpt-5.6-luna → gpt-6-luna,
    #   2순위 claude-sonnet-5 → claude-sonnet-5-5 를 같은 자리에 둔다. 옛 두 키는 목록 끝 폴백으로도 두지 않는다
    #   (원장 호환용 · 우선순위 밖). 벤더 순서 codex → claude → claude 는 그대로다.
    # D-99 (2026-10-12 · 허브 토론 dbt-261012-124540): claude-haiku-5-5 를 2순위(Claude 쪽 첫 폴백)로 넣는다.
    #   1순위 gpt-6-luna 는 그대로이고 claude-sonnet-5-5 · claude-opus-5-5 는 한 칸씩 밀린다(빼지 않는다).
    #   2순위가 바뀌므로 A 공정의 탐색 슬롯·스왑 비교·표의 2순위 칸은 이제 haiku 를 본다(벤더는 그대로 claude).
    #   같은 claude 구독에서 haiku 실패 뒤 sonnet 을 부르면 총 쿼터가 늘 수 있다 — 절감은 미측정이다(D-99 소수의견).
    #   선두 승격이나 Sonnet 5.5 제외는 별도 비교 근거가 있어야 한다.
    # D-101 (2026-10-12 · Simon 지시 · 토론 없음): gpt-6-luna 를 목록에서 뺀다("gpt 쪽은 astra 말고는 쓰지마").
    #   A = claude-haiku-5-5 → claude-sonnet-5-5 → claude-opus-5-5. 지시 원문은 "단순작업 sonet 5.5" 이고,
    #   오케스트레이터가 Haiku 5.5 를 Sonnet 5.5 앞에 두자고 권했으며 Simon 이 반대하지 않았다.
    #   gpt-6-luna 키는 LANES 에 남는다(원장 호환용 · WITHDRAWN_LANES). 결함이 아니다 — D-91 canary 는 통과했다.
    #   ⚠ 세 레인이 전부 claude 다: claude 가 80% 를 넘으면 셋이 함께 강등되어 첫 강등 레인(haiku)을 쓰고,
    #     한도에 닿으면 A 작업은 멈춘다(codex 폴백 없음 — astra 를 A 에 두지 않는다: OUTPUT_RULES 가 대량 정형
    #     변환에 astra 배치를 금한다). 탐색 슬롯·스왑 비교의 1·2순위는 haiku·sonnet 으로 같은 벤더다.
    #   ⚠ 이 순서의 canary 는 돌리지 않았다. 근거는 D-99(Haiku · A 과제 3개)와 D-91(Sonnet canary)뿐이다.
    "A":          ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"],
    # 2026-09-06: 2순위를 sol → gpt-6-astra 로 올린다.
    #   · astra 가 codex 계열 최상위 모델이다(models_cache priority 1).
    #   · sol 을 목록에서 빼면 코디네이터 좌석과 B 워커가 **구조적으로** 겹칠 수
    #     없게 된다 — coordinator_conflict() 가 잡던 상황이 기본값에서 사라진다.
    #   · 1순위를 claude 로 두는 이유는 성능이 아니라 가용성이다(codex 주간 64%,
    #     claude 주간 23% — 2026-09-06 실측). 이 스킬의 목적은 단일 벤더 쿼터가
    #     라운드를 죽이지 않게 하는 것이다.
    # D-28 #5 (Simon 확정 2026-09-16): 이 목록은 **코딩이 아닌** B 공정(research-deep ·
    #   terminal-ci-git)용이다. 코딩은 PROCESS_LANES["coding"] 이 먼저 잡는다 — B 1순위가
    #   codex 여도 코딩은 codex 로 가지 않는다(두 보안 게이트가 codex → G1).
    #   검증 전 목록 = astra → opus. fable 은 M1 통과 뒤 2순위로 들어간다.
    #   위 09-06 주석의 "1순위 claude" 근거는 D-28 로 대체됐다(판정 원문 reports/vibe-d28-debate-260913).
    #   2단계(2026-09-16 M1 통과): fable 을 2순위로 넣었다.
    # D-101 (2026-10-12): 목록은 그대로다. 달라진 것은 둘 — astra 는 항상 xhigh 로 돌고(EFFORT_PINNED),
    #   코디네이터도 astra 가 되어 위 09-06 주석의 '구조적으로 겹칠 수 없다' 는 더는 참이 아니다(겸임 경고).
    #   codex 가 80% 를 넘으면 2순위 claude-fable-5-1 로 강등된다 — effort 를 낮추거나 다른 GPT 레인으로 가지 않는다.
    "B":          ["gpt-6-astra", "claude-fable-5-1", "claude-opus-5-5"],
    # D-28 #4 (Q-260913-08 승인 2026-09-16) — 대조·판정. 심판안 순서 그대로: astra → fable → opus.
    #   읽기 전용 클래스라 G1 과 무관하다(코딩이 아니다). 파일을 바꾸면 validate_plan 이 A_VERIFY_WRITES 로 막는다.
    "A-verify":   ["gpt-6-astra", "claude-fable-5-1", "claude-opus-5-5"],
    # D-28 #6: grok 은 새 계정 실호출 통과 전 blocked(make_intake 가 건너뛴다) → sol → opus.
    #   2026-09-20 08:33 실호출 OK(41.5초) — M3 해소. 상태는 여전히 make_intake 가 실호출로 판정한다
    #   (여기에 고정하지 않는다: G12 창이 24시간이라 하루 지나면 다시 미확인이다).
    # D-101 (2026-10-12 · Simon 지시): 2순위 gpt-6.1-sol 과 끝 폴백 gpt-5.6-sol 을 뺀다. 2순위는 claude-opus-5-5,
    #   GPT 가 필요하면 끝의 gpt-6-astra(@xhigh 고정)다. astra 는 코디네이터이기도 해서 이 폴백이 쓰이면
    #   coordinator_conflict() 가 경고한다.
    "C-realtime": ["grok-4.6", "claude-opus-5-5", "gpt-6-astra"],
    # D-28 #7: gemini 는 dispatch "unavailable" 이라 기본 채움이 건너뛴다(#12) — D-101 부터 오늘 기본은 opus 다
    #   (그 전에는 sol). opus·astra 가 BigQuery·Firebase 작업을 대신할 수 있는지는 미확인.
    "C-platform": ["gemini-3.8-flash", "claude-opus-5-5", "gpt-6-astra"],
    "D":          ["claude-opus-5-5"],            # 고정
    "N":          [],                             # 모델 미사용 — orca CLI
}

# D-28 #5·#14 (Simon 확정 2026-09-16) — 공정 단위 레인 목록. CLASS_LANES 보다 먼저 본다.
#   코딩은 claude 계열에만 둔다: 두 보안 게이트가 codex 라 코딩이 codex 로 가면 G1 이다
#   (D-28 음성대조 N1~N3 실측: S 원안·현행 강등·현행 탐색 슬롯 모두 (False, ['G1'])).
#   codex 폴백은 두지 않는다 — claude 가 막히면 코딩 없는 라운드로 줄인다(#14).
#   불변식: PROCESS_LANES["coding"] 의 벤더 ∩ 보안 게이트 벤더 = ∅ (selftest 가 잡는다).
#   fable 은 M1 실워커 1회 통과 뒤 2순위로 들어간다.
#   D-67 (2026-10-04): 1순위 opus 를 claude-opus-5 → claude-opus-5-5 로 옮겼다(옛 레인은 guarded Orca 로 못 뜬다).
#   D-103 (2026-10-18): Simon 의 "sonnet은 사용하는걸로 설정하자" 로 claude-sonnet-5-5 를 2순위에 넣었다 — 자리는
#     오케스트레이터가 정했고 같은 날 D-106 이 바로잡았다.
#   D-106 (2026-10-18 · Simon 지시 "sonnet5.5는 간단한 코딩에 써야 하는거 아니야? 복잡한 코딩은 opus5.5 xhigh가 해야지." ·
#     토론 없음): 복잡한 코딩의 기본·폴백은 opus → fable 이다(fable 은 자기 버킷 fableWeekly). sonnet 은 끝에 남긴다 —
#     기본 채움으로 오는 자리가 아니라, 단순 코딩 단계(중앙 계획기 CODE_SIMPLE)가 sonnet 을 고를 수 있게 허용 목록에 두는 것이다.
#     코딩 공정의 opus 기본 effort 는 PROCESS_EFFORTS 가 xhigh 로 정한다.
PROCESS_LANES = {
    "coding": ["claude-opus-5-5", "claude-fable-5-1", "claude-sonnet-5-5"],
}

# 공정별 기본 effort (D-106 · 2026-10-18 · Simon 지시). {공정: {레인: effort}}.
#   그 공정에서만 레인 사다리(std/top)보다 먼저다: effort_for 의 기본값이 되고, validate_effort 는 이 값을
#   정책 단으로 받는다(allow_off_ladder 없이). 다른 공정의 opus(A·C 폴백 등)는 사다리 high/max 그대로다.
#   중앙 계획기는 CODE_COMPLEX 단계의 opus 를 이 값으로만 받는다(orchestrate.OWNER_TASK_EFFORTS).
PROCESS_EFFORTS = {
    "coding": {"claude-opus-5-5": "xhigh"},
}

CLASS_LABEL = {
    "A": "기계적 — 판단 0",
    "A-verify": "대조·판정 — 기록↔사실 · 주장 확인 (읽기 전용)",
    "B": "판단 — 우열·인과·설계",
    "C-realtime": "외부 — 실시간·수집",
    "C-platform": "외부 — 플랫폼·시각",
    "D": "종합 — 다레인 산출물 조립",
    "N": "무모델 — 워크트리·run 관리",
}

# ── 공정 카탈로그 (발주 §4) ─────────────────────────────────────
#  fixed: (lane, effort) 로 고정. 탐색 슬롯·스왑 대상에서 제외한다.
PROCESSES = [
    ("bulk-transform",        "A", "대량 정형 변환 · 카운트",              None),
    ("inventory-schema",      "A", "인벤토리 · 스키마 검증",               None),
    ("disk-grep",             "A", "디스크 스캔 · grep",                   None),
    ("log-history-triage",    "A", "장문 로그 · 커밋히스토리 분류 집계",   None),
    # D-28 #4 (Q-260913-08 승인 2026-09-16) — 판정이 섞인 대조 작업. 읽기 전용이다(파일을 바꾸면 coding).
    ("claim-verify",          "A-verify", "기록↔사실 대조 · 주장 판정 (읽기 전용)", None),
    ("research-deep",         "B", "웹 리서치 — 정독 · 모순 종합",         None),
    ("coding",                "B", "코딩 — 구현 · 대규모 리팩터링",        None),
    ("terminal-ci-git",       "B", "터미널 · CI · git (판단 섞인 경우)",   None),
    # D-260904-01 옵션 ① (Simon 2026-09-04) — 인가 검사를 codex 로 옮긴다.
    #
    # 지시는 "두 게이트가 같은 codex 가 되면 생성물게이트를 claude 로 맞바꿔라" 였으나,
    # 그렇게 하면 코딩(B 1순위 = claude-opus-5)과 생성물게이트가 같은 claude 가 되어
    # 자기 산출물을 자기가 검사하는 HARD G1 이 된다 — 옮기려던 문제보다 나쁘다.
    # 판단 가능한 벤더가 claude·codex 둘뿐인데 역할은 셋(구현·생성물·인가)이라
    # 셋을 모두 다른 벤더에 두는 배치는 존재하지 않는다(비둘기집).
    #
    # 그래서 우선순위가 낮은 제약을 양보한다:
    #   지킨 것 — 코딩 ≠ 생성물게이트 · 코딩 ≠ 인가  (자기채점 0. 발주가 '불변'으로 못박은 G1)
    #   양보 -- 두 게이트가 같은 벤더가 되는 것 (발주 §5 한 줄). 대신 '다른 모델'을 강제한다:
    #            daybreak@xhigh vs terra@high — 모델도 effort 상한도 다르다.
    #
    # 2026-09-04 갱신: 생성물 게이트를 gpt-5.6-sol → gpt-daybreak-blue-latest 로 옮겼다.
    # sol 은 범용 워크호스이고 daybreak 은 "broad defensive cybersecurity work" 전용
    # 프론티어 모델이다(codex models_cache 원문). 보안 자리에 보안 모델을 놓는다.
    #   (D-28 #16 정정: 2026-09-13 models_cache 에서 sol 은 priority 1 "Latest frontier agentic coding model." — "범용 워크호스"는 09-04 시점 설명이다)
    # 벤더는 여전히 codex 라 위 양보는 그대로다 — 개선된 것은 모델 적합성뿐이다.
    #
    # 2026-09-06: 인가 게이트를 gpt-5.6-terra @high → gpt-6-astra @xhigh 로 올린다.
    #   비즈로직·인가 검사는 이 라운드에서 가장 '판단'에 가까운 자리다 —
    #   astra 설명이 정확히 그 자리를 가리킨다("complex, demanding work").
    #   [Simon 결정 2026-09-06] effort 도 같이 xhigh 로. 즉 Orca 에서 이 모델로
    #   갈 수 있는 최상단이다(그 위 max·ultra 는 Orca 가 안 받는다 — 위 원인 규명 참조).
    #   비용은 codex 주간 쿼터로 관리한다(강등 규칙이 이미 있다 — 2026-09-16 Q-05 로 80% 초과).
    #   두 게이트가 같은 codex 벤더인 것은 D-260904-01 에서 이미 양보한 부분이고,
    #   구분자는 이제 'effort 상한'이 아니라 **모델 성격**이다 —
    #   daybreak 은 model_specialty="cyber" 전용, astra 는 범용 프론티어.
    #   같은 모델이 두 축을 겸하면 G1_SEC_SAME_MODEL 이 여전히 잡는다.
    #
    # 2026-10-12 D-98 (허브 토론 dbt-261012-124530 · quick · PROVISIONAL 3/4 · 심판 확신도 91):
    #   생성물 게이트를 gpt-daybreak-blue-latest → gpt-6.1-sol @xhigh 로 옮긴다.
    #   왜 — OpenAI API 문서가 그 별칭을 deprecated 로 표시했다(종료일·대체 ID 미공지). 이 계정 Codex
    #     카탈로그(~/.codex/models_cache.json)는 아직 list · cyber 로 싣고 은퇴 표시가 없지만 다른 cyber
    #     모델도 없다. registry 는 lifecycle: deprecated 이고 중앙 계획기는 그 후보를 이미
    #     MODEL_NOT_ACTIVE 로 막는다 — 이 표만 폐기된 별칭을 가리켜 코딩 라운드의 게이트 자리가 막혀 있었다.
    #   지킨 것 — G1: 코딩 벤더(claude) ≠ 게이트 벤더(codex) — 게이트는 자기 벤더의 산출물을 채점하지 않는다.
    #     G1_SEC_SAME_MODEL: 생성물 게이트 gpt-6.1-sol ≠ 인가 게이트 gpt-6-astra (둘 다 codex —
    #     D-260904-01 의 양보 그대로). xhigh 는 6.1-sol 의 Orca 상한이고 옛 게이트와 같은 effort 다.
    #   잃은 것 — cyber 전용성. 두 게이트의 구분자는 다시 '다른 모델'뿐이다(둘 다 범용). 방어 루브릭과
    #     fail-closed 규칙(references/security-artifact-gate.md)으로 보완하지만 동등하다고 증명된 것은 아니다:
    #     canary(run_8f7a27febc38 · ctx_ff39c4a979ba)는 결함 4개를 심은 샘플 1건이다.
    #   읽는 규칙 — 빈 출력 · 제공사 차단/거절 · 첫 줄(GATE: BLOCK|PASS) 누락 · 모호한 판정은 FAIL 이다.
    #     PASS 로 읽지 않는다. 이 규칙은 게이트 출력을 읽는 쪽(호스트·코디네이터)이 적용한다 — 코드가 파싱하지 않는다.
    #   재승격 — 폐기된 별칭이 아닌 cyber 모델이 이 계정 Codex 카탈로그에 나타나면 같은 canary 를 돌리고,
    #     통과하면 1단 DECISIONS 기록과 함께 게이트를 옮긴다. 자동 승격은 없다.
    #
    # 2026-10-12 D-101 (Simon 지시 · 토론 없음 · 위 D-98 이전을 같은 날 뒤집는다):
    #   생성물 게이트를 gpt-6.1-sol → gpt-daybreak-blue-latest @xhigh 로 되돌린다.
    #   왜 — "gpt 6.1 sol은 너무 느려서 빼기로 결정", "보안게이트는 데이브레이크로 할려했는데 그게 안돼면 opus 5.5로 하자."
    #     별칭은 오늘 이 계정에서 동작한다: canary(run_b08adccb4ec8 · ctx_41243c1a0d26 · 15:19~15:20 KST)에서
    #     requested == effective(gpt-daybreak-blue-latest · xhigh) · D-98 과 같은 샘플에 GATE: BLOCK + 결함 4개 정확히.
    #   지킨 것 — G1: 코딩(claude) ≠ 게이트(codex). G1_SEC_SAME_MODEL: Daybreak ≠ 인가 게이트 gpt-6-astra.
    #     되찾은 것 — cyber 전용성(09-04 의 배치). 루브릭·출력 형식·fail-closed 규칙은 그대로 쓴다.
    #   그대로인 것 — 제공사의 deprecated 표시. registry lifecycle: deprecated · 중앙 계획기 MODEL_NOT_ACTIVE 는
    #     건드리지 않았다. 이 표의 LANE_DEPRECATED 만 DEPRECATED_LANE_PINS 의 이 한 자리를 연다.
    #     ⚠ 그래서 packaged registry 를 쓰는 중앙 계획기는 이 후보를 계속 막는다 — 게이트 자리는 고정이지 동작이 아니다.
    #   실행 전 규칙 — 코디네이터가 ~/.codex/models_cache.json 에 별칭이 은퇴·upgrade 표시 없이 남아 있는지 본다.
    #     없거나, 게이트 출력이 비거나 차단되면 게이트는 FAIL 이다(통과가 아니다).
    #   미결 — Simon 이 말한 폴백 claude-opus-5-5 는 구현하지 않았다. 코딩이 claude-opus-5-5 라 같은 모델이 자기
    #     산출물을 검사하게 되어 G1 과 충돌한다. 선택지와 판정 요청은 references/security-artifact-gate.md 의 Open item.
    #     (그 시점 기록 — 아래 D-102 가 정했다.)
    #   재승격 — 더 새로운 cyber 모델이 카탈로그에 나타나면 같은 canary 와 1단 기록 뒤에 별칭을 대체한다.
    #
    # 2026-10-12 D-102 (Simon 판정 · 토론 없음): 고정 배정은 그대로 Daybreak 다. 설 수 없을 때만
    #   FIXED_FALLBACKS 의 gpt-6-astra @xhigh 가 대신 선다(validate_plan 의 fixed_unavailable).
    #   그때는 아래 인가 게이트와 같은 모델이 되므로 G1_SEC_SAME_MODEL 을 그 상태 하나에서만 면제한다.
    ("security-artifact-gate","B", "보안 — 생성물 안전성 게이트",
     ("gpt-daybreak-blue-latest", "xhigh")),
    ("security-bizlogic-2nd", "B", "보안 — 비즈니스 로직 · 인가",          ("gpt-6-astra", "xhigh")),
    ("trend-realtime",        "C-realtime", "트렌드 · 실시간",             None),
    ("research-collect",      "C-realtime", "웹 리서치 — 수집",            None),
    ("google-platform",       "C-platform", "Google 플랫폼 (BigQuery/Firebase/Workspace)", None),
    ("ui-visual",             "C-platform", "UI 시각 검증",                None),
    # D-67 (2026-10-04): (claude-opus-5, ultracode) → (claude-opus-5-5, max).
    #   ultracode 는 프롬프트 키워드라 flag 레인이 받을 수 없고, guarded Orca 는 flag 레인만 띄운다 —
    #   옛 고정값은 그래서 실행 경로가 없었다. max 는 opus-5-5 의 Orca 상한이자 허브 핀(@max)이다.
    ("synthesis",             "D", "다레인 산출물 조립",                   ("claude-opus-5-5", "max")),
    ("worktree-run-mgmt",     "N", "워크트리 · run 관리 (orca CLI)",       None),
]

PROC_BY_ID = {p[0]: p for p in PROCESSES}

# 코디네이터 레인 (발주 §5) — 종합(D)과 벤더가 달라야 한다.
#   sol 로 유지한다. astra 로 올리지 않은 이유가 두 개다:
#   ① sol 은 이제 B 우선순위 목록에도 고정 공정에도 없다 → 겸임 충돌이 구조적으로 0.
#   ② 코디네이터는 메일·디스패치 부기가 일이지 깊은 판단이 아니다. 프론티어 좌석은
#      실제로 판단하는 워커(B·보안 인가)에 쓴다. 그리고 sol 은 Orca 에서 ultra 가
#      실제로 통과하는 몇 안 되는 레인이다(astra 는 xhigh 가 상한).
#   D-28 #8 (Simon 확정 2026-09-16): effort ultra → xhigh. ②의 이유(부기)로 ultra 는 과대다.
#   ⚠ D-28 #6 이후 sol 이 C-realtime·C-platform 2순위에 들어가 ①은 더 이상 참이 아니다 —
#     coordinator_conflict() 가 클래스와 무관하게 겸임을 경고한다.
#   이 상수는 표시·안내용이고 validate_effort 를 거치지 않는다(D-28 N7b 실측).
#   D-67 (2026-10-04): gpt-5.6-sol → gpt-6.1-sol, effort 는 xhigh 그대로.
#     · 종합(D = claude-opus-5-5)과 벤더가 달라야 하므로 codex 에 둔다.
#     · sol 의 후속이 6.1-sol 이고(허브 핀 gpt-6.1-sol@xhigh) xhigh 는 D-28 #8 의 값이자 6.1-sol 의 Orca 상한이다.
#     · 6.1-sol 이 C-realtime·C-platform 2순위라 겸임 가능성은 5.6-sol 때와 같다 — coordinator_conflict() 가 경고한다.
#   ⚠ D-98 (2026-10-12): 생성물 게이트가 gpt-6.1-sol @xhigh 로 옮겨져 코디네이터와 **같은 모델**이 됐다.
#     게이트는 코딩 라운드의 필수 공정이라 그 라운드에서는 coordinator_conflict() 가 항상 참이다
#     (경고일 뿐 디스패치를 막지 않는다 · selftest 가 이 상태를 고정한다). 위 ①은 이제 고정 공정에서도 참이 아니다.
#     G1 은 그대로다 — 코디네이터는 부기 좌석이지 구현자가 아니고, 코딩은 claude 다.
#     D-98 은 코디네이터를 바꾸지 않았다. 바꾸려면 별도 결정이 필요하다.
#   D-101 (2026-10-12 · Simon 지시 "기획단계 gpt astra xhigh와 opus 5.5" · "gpt 쪽은 astra 말고는 쓰지마"):
#     gpt-6.1-sol → gpt-6-astra, effort 는 xhigh 그대로(astra 의 고정 effort 이자 Orca 상한).
#     · 종합(D = claude-opus-5-5)과 벤더가 다르다(codex) — 발주 §5 의 조건은 그대로 지킨다.
#     · astra 는 인가 게이트(security-bizlogic-2nd 고정)이자 B·A-verify 1순위, C 클래스 끝 폴백이다 →
#       astra 가 워커로 일하는 라운드마다 coordinator_conflict() 가 참이다. 규칙은 바뀌지 않았다 — 경고일 뿐이고
#       디스패치를 막지 않는다. 위 ①(겸임 충돌이 구조적으로 0)과 ②(프론티어 좌석을 부기에 쓰지 않는다)는
#       이제 둘 다 참이 아니다. G1 은 그대로다 — 코디네이터는 구현자가 아니고 코딩은 claude 다.
#     · 코디네이터로서의 astra canary 는 돌리지 않았다.
COORDINATOR = ("gpt-6-astra", "xhigh")

# 탐색 슬롯 제외 (발주 §11)
# D-28 C2: 코딩은 공정 전용 목록 하나뿐이라 탐색할 2순위가 없다 → 제외에 넣는다.
#   2순위가 Orca 로 안 뜨거나 실호출에 실패한 공정은 explore_candidates() 가 따로 걸러낸다.
EXPLORE_EXCLUDE = {"synthesis", "security-artifact-gate", "security-bizlogic-2nd", "coding"}

# ── 레인별 산출물 제약 (발주 §6) ────────────────────────────────
OUTPUT_RULES = {
    "grok-4.6": {
        "allow": "CSV · 카운트 · 분류 라벨만",
        "deny":  "서술 결론 · 인과 추정 · 200K 초과 입력(과금 2배)",
        "why":   "사실 신뢰도가 4레인 중 최약. 합계는 D 레인이 산술 재검산한다",
    },
    "gemini-3.8-flash": {
        "allow": "발견 목록 + 탐색 드라이브 · 제외 경로 · 스캔 파일 수",
        "deny":  "범위 없는 '0건' 반환 · 무인 장기 루프 단독 배치",
        "why":   "부재 보고 오류가 직전 라운드 오류 5건 중 3건의 원인",
    },
    # D-101 (2026-10-12): 철회된 레인(WITHDRAWN_LANES)에는 규칙을 두지 않는다 — 옛 gpt-6-luna 규칙(A 클래스
    #   1순위 규율)은 새 1순위 claude-haiku-5-5 규칙으로 합쳤다. 테스트가 이 표에 철회 레인이 없음을 확인한다.
    "claude-opus-5-5": {   # D-67: 종합(D) 레인 규칙이라 종합 레인과 함께 옮겼다 (옛 키 claude-opus-5)
        "allow": "항목별 확신도 표기 필수 (강=기계검증 / 약=판단)",
        "deny":  "리포트만 내고 끝내기 — 사람이 읽는 것은 결정 시트 1장이다",
        "why":   "종합 레인이므로 사람의 결정으로 이어져야 한다",
    },
    "gpt-6-astra": {
        "allow": "판단마다 근거(파일·행·명령 출력) 첨부 · 반증 시도 1건 이상 명시 · effort 는 항상 `xhigh`(D-101) · "
                 "생성물 게이트 폴백으로 설 때(D-102)는 아래 `gpt-daybreak-blue-latest` 행의 게이트 규칙을 그대로 따른다",
        "deny":  "대량 정형 변환에 배치 (A 클래스는 claude-haiku-5-5 로 내린다) · "
                 "`xhigh` 밖 effort 로 부르기 (`ultra`/`max` 는 Orca 가 거부하고, 낮은 값은 D-101 고정이 막는다)",
        "why":   "codex 계열에서 일을 받는 유일한 좌석이다(D-101). 싼 일에 태우면 쿼터만 태우고, "
                 "고정 밖 effort 로 부르면 워커가 아예 안 뜬다",
    },
    "claude-haiku-5-5": {   # D-99 로 들어왔고 D-101 (2026-10-12)부터 A 클래스 1순위다 — 옛 luna 규칙(싼 레인 규율)을 받았다
        "allow": "정형 변환 · 카운트 · 분류 · **부재 보고에는 탐색 범위 명시**",
        "deny":  "우열 판단 (필요하면 sonnet-5-5 이상으로 올린다) · 범위 없는 '0건'",
        "why":   "A 클래스 1순위 레인(D-101) — 판단을 맡기지 않는다. "
                 "범위 요구는 Simon 결정(2026-09-04, luna03 채택)으로 A 클래스 전체에 적용된다. "
                 "canary 는 작은 과제 3개 · effort low 1회만 봤다(D-99 · 1순위로 옮긴 뒤의 canary 는 없다): "
                 "큰 입력 · 10만 토큰 초과 입력(API 단가 5배 구간) · 쿼터 절감은 미측정이다",
    },
    "gpt-daybreak-blue-latest": {   # D-101 (2026-10-12): 생성물 게이트 규칙이라 게이트와 함께 되돌렸다 (D-98 때는 gpt-6.1-sol 키)
        # 표 칸에 세로줄을 넣으면 마크다운 표가 깨진다 — 줄 형식의 원문은 참고 문서에 둔다.
        "allow": "**생성물 게이트로만 쓴다**: 첫 줄 `GATE: BLOCK` 또는 `GATE: PASS` · 이어서 발견마다 한 줄 "
                 "(CWE 번호 · 위치 · 사유) · 그 뒤에 발견별 재현 경로 · 심각도 · 최소 패치(옛 게이트 규칙 그대로) · "
                 "형식과 루브릭은 `references/security-artifact-gate.md`",
        "deny":  "빈 출력 · 차단/거절 · 첫 줄 누락 · 모호한 판정을 PASS 로 읽기 (전부 FAIL) · "
                 "방어 목적 밖의 공격 코드 생성 · 범위 없는 '취약점 0건' · 게이트 밖 공정에 배정 (`LANE_DEPRECATED`)",
        "why":   "제공사가 폐기 표시한 cyber 별칭을 Simon 지시(D-101)로 게이트에만 쓴다 — 근거 없는 통과는 게이트를 "
                 "무력화하고, 별칭은 예고 없이 사라질 수 있다. 실행 전마다 Codex 카탈로그를 확인하고, 없거나 출력이 "
                 "비거나 차단되면 FAIL 이다(canary 는 심은 샘플 1건)",
    },
}

# ── 가드 (발주 §7) ──────────────────────────────────────────────
#  auto=True 인 것만 원장 guard_violations 에 자동 기록한다.
#  나머지는 오검출이 잘못된 학습 신호가 되므로 비운다.
GUARDS = [
    ("G1", "짠 레인이 자기 코드를 보안 리뷰하지 않는다", True),
    ("G2", "자기 결론 재검증에 서브에이전트를 쓰지 않는다 — 반증은 리포트 '§X 반증 시도' 섹션", False),
    ("G3", "워커당 spawn 상한 8", True),
    ("G4", "쿼터 게이트는 디스패치 시점에만. 실행 중 중단 근거로 쓰지 않는다 — 한도 도달로 **실패·정지한** 워커만 "
           "여유 레인의 새 task 로 인수인계한다(`handoff_spec` + `revalidate_for_retry`, Q-260913-05). "
           "상시 모니터링 데몬·실행 중 선제 교체는 하지 않는다", False),
    ("G5", "쿼터는 4벤더 각각 확인한다", True),
    ("G6", "부재 보고에는 탐색 범위를 붙인다. 범위 없는 '0건'은 반환값 불인정 — "
           "gemini 뿐 아니라 **A 클래스 전체**에 적용 (Simon 결정 2026-09-04)", False),
    ("G7", "최상위 effort 는 반증질문 YES 인 태스크에만", False),
    ("G8", "쓰기 라운드 전 검증된 종료 절차가 필요하다. legacy `kill_worker.py --kill --fence`는 "
           "handle/dispatch 결속 미검증으로 사용 금지이며 raw `worker-stop`도 차단된다. "
           "별도 승인·정확한 대상 검증 없이 종료하거나 재발주하지 않는다", False),
    ("G9", "Move-Item 배치는 매니페스트 + 역방향 스크립트 선행", False),
    ("G10", "적대적 평가에서 채점자는 두 생산자와 **벤더가 달라야** 한다. "
            "벤더 3개를 못 채우면 그 문제는 건너뛴다 — 자기 벤더가 자기 답을 "
            "채점하느니 관측을 포기한다 (`adversarial_eval.py`)", False),
    ("G11", "Codex 워커 기동 전에 PATH 실행본과 인접 npm 패키지를 로컬에서 비교한다. "
            "`python -B scripts/check_tooling.py --local-codex` (종료 0만 진행, "
            "1=뒤처짐, 2=미확인). 전체 도구 보고서는 npm 원격·Orca 조회가 있어 "
            "이 게이트를 대체하지 못한다", False),
    ("G12", "쿼터·metadata는 생성 성공이나 무료 사용 증거가 아니다. legacy "
            "`adversarial_eval.py --preflight` 실호출은 차단됐다. 실측도 중앙 계획·예산 예약·"
            "fresh 계정/비용 증명 뒤에만 가능하다. 과거 Grok HOLD는 영구 금지가 아니며 "
            "복구 시에도 최신 쿼터·선택 모델의 구독 포함·초과 과금 차단을 다시 확인한다", False),
    ("G13", "재시도·대체도 중앙 planner/Store/guarded adapter를 거친다. "
            "수락 불명은 lookup-only이며 raw `worker-start --retry-of`로 우회하지 않는다", False),
    ("G14", "결정 시트(`make_decision_sheet.py`)를 만들지 않은 라운드는 **끝난 것으로 치지 않는다** — "
            "손으로 조립한 시트는 `decisions_run_*.json` 을 내지 않아 채택률이 비고 스왑 규칙이 돌지 않는다 (D-28 #15)", False),
]
AUTO_GUARDS = [g for g in GUARDS if g[2]]

SPAWN_CAP = 8            # G3
# Q-260913-05 (2026-09-16, Simon 메모 "모든 모델 100%까지 사용" + Claude 판단): 강등 60→80 · 금지 85→100(도달).
#   80% 넘은 벤더에서 비고정 레인은 여유 레인으로 가고, 옮길 수 없는 고정 게이트가 80~100% 구간을 쓴다.
QUOTA_DEMOTE = 80        # 초과 → 다음 순위로 강등
QUOTA_BLOCK = 100        # 도달(>=) → 사용 금지. 실호출(G12) 실패도 사용 금지
SWAP_MIN_OBS = 5         # §12 양쪽 관측 최소
SWAP_MIN_GAP = 0.15      # §12 채택률 15%p


# ── 조회 API ────────────────────────────────────────────────────
def lanes_for(cls):
    """클래스의 레인 우선순위 목록."""
    return list(CLASS_LANES.get(cls, []))


def lanes_for_proc(proc_id, cls=None, falsifiable=False, writes=False):
    """공정 단위 레인 목록 (D-28 #5·#11).

    우선순위: PROCESS_LANES[proc] → R1 승격 → CLASS_LANES[클래스].
    R1(#11): 반증 질문이 "예"인 A 작업은 판정이 섞였으므로 A 의 싼 레인(당시 luna · D-101 부터 haiku)에 두지 않는다.
      A-verify 클래스(2단계 · Q-260913-08)가 생기기 전까지는 B 비코딩 목록으로 임시 승격한다.
      effort 는 도착 레인의 최상위다 — effort_for(lane, True).
    """
    if writes:                            # Q-09: 파일을 바꾸는 공정은 코딩 레인만
        return list(PROCESS_LANES["coding"])
    if proc_id in PROCESS_LANES:
        return list(PROCESS_LANES[proc_id])
    p = PROC_BY_ID.get(proc_id)
    c = cls or (p[1] if p else None)
    if c == "A" and falsifiable:
        return lanes_for("A-verify")      # D-28 #11 본 규칙(2026-09-16): 임시 승격(B 비코딩)에서 A-verify 로
    return lanes_for(c)


def active_codex_lanes():
    """codex 벤더에서 새 일을 받을 수 있는 레인 (D-101 — gpt-6-astra 하나).

    철회(WITHDRAWN_LANES)·폐기 표시(DEPRECATED_LANES) 레인은 뺀다. Daybreak 는 생성물 게이트 고정 자리로만
    서므로 '일반 배정이 가능한 레인'이 아니다.
    """
    return [l for l, m in LANES.items() if m["vendor"] == "codex"
            and l not in WITHDRAWN_LANES and l not in DEPRECATED_LANES]


def gate_vendors():
    """두 보안 게이트(고정 공정)의 벤더 집합."""
    return {LANES[fixed_for(p)[0]]["vendor"]
            for p in ("security-artifact-gate", "security-bizlogic-2nd")}


def explore_candidates(live_ok_vendors=None):
    """탐색 슬롯 후보 공정 id (D-28 #12 · C2).

    2순위 레인이 있고, 그 레인이 Orca 워커로 뜨며(dispatch != unavailable),
    실호출 확인(G12)을 통과한 벤더일 때만 후보다. live_ok_vendors 가 None 이면
    실호출 조건은 보지 않는다(미확인 — 호출자가 표시할 것).
    """
    out = []
    for pid, cls, _label, fixed in PROCESSES:
        if fixed or pid in EXPLORE_EXCLUDE or cls not in ("A", "A-verify", "B"):
            continue
        lanes = lanes_for_proc(pid, cls)
        if len(lanes) < 2:
            continue
        second = LANES[lanes[1]]
        if second.get("dispatch") == "unavailable":
            continue
        if live_ok_vendors is not None and second["vendor"] not in live_ok_vendors:
            continue
        out.append(pid)
    return out


def fixed_for(proc_id):
    """고정 배정이면 (lane, effort), 아니면 None."""
    p = PROC_BY_ID.get(proc_id)
    return p[3] if p else None


def process_effort(proc, lane):
    """D-106: 그 공정에서 이 레인이 쓰는 기본 effort. 없으면 None."""
    return PROCESS_EFFORTS.get(proc, {}).get(lane) if proc else None


def effort_for(lane, falsifiable, proc=None):
    """발주 §5: effort 는 클래스가 아니라 태스크 속성(반증가능성)으로 정한다.

    D-106: proc 를 주면 PROCESS_EFFORTS 의 공정별 값이 사다리보다 먼저다(코딩의 opus 는 xhigh).
    """
    m = LANES.get(lane)
    if not m:
        raise KeyError(f"unknown lane: {lane}")
    pinned = process_effort(proc, lane)
    if pinned:
        return pinned
    return m["top"] if falsifiable else m["std"]


def orca_efforts_for(lane):
    """Orca 가 이 레인에 대해 실제로 받는 effort 목록 (2026-09-06 실측)."""
    m = LANES.get(lane)
    if not m:
        raise KeyError(f"unknown lane: {lane}")
    return tuple(m.get("orca_efforts") or (m["top"], m["std"]))


def ceiling_for(lane):
    """그 레인에서 Orca 로 갈 수 있는 가장 높은 effort."""
    return orca_efforts_for(lane)[-1]


def ladder_for(lane):
    """정책 사다리 (top/std). 기본 경로는 언제나 이 둘 중 하나다."""
    m = LANES[lane]
    return (m["std"], m["top"])


def ledger_efforts(lane):
    """원장이 받아줄 effort 집합 = 정책 두 단 ∪ Orca 실측 목록.

    off-ladder 로 올려 부른 라운드도 기록이 남아야 스왑 분석이 성립한다.
    그래도 닫힌 집합이라 아무 문자열이나 통과하지는 않는다.
    """
    m = LANES.get(lane) or {}
    return ({m.get("top"), m.get("std")} | set(m.get("orca_efforts") or ())) - {None}


def validate_effort(lane, effort, allow_off_ladder=False, proc=None):
    """effort 가 이 레인에서 쓸 수 있는 값인지 본다. 아니면 ValueError.

    기본은 정책 두 단(top/std)만 허용한다 — 발주 C3·G7 의 규율이다.
    allow_off_ladder=True 면 Orca 실측 목록까지 넓힌다(상황에 맞게 올리거나 내릴 때).
    어느 쪽이든 **Orca 가 거부하는 값은 절대 통과하지 않는다** —
    astra/daybreak 에 ultra·max 를 주면 워커가 뜨지 않고 invalid_argument 만 난다.

    D-101: EFFORT_PINNED 레인(gpt-6-astra)은 고정값만 받는다 — allow_off_ladder 로도 다른 값은 열리지 않는다.
    철회된 레인(WITHDRAWN_LANES)은 여기서 막지 않는다: 이 함수는 원장 호환 키의 argv 를 오프라인으로 조립하는
    자리이고, 새 계획을 막는 것은 validate_plan 의 LANE_WITHDRAWN 이다(LANE_DEPRECATED 와 같은 구조).
    """
    if lane in FORBIDDEN_LANES:
        raise ValueError(f"배정 금지 레인 (발주 §3): {_safe(lane)}")
    m = LANES.get(lane)
    if not m:
        raise ValueError(f"unknown lane: {_safe(lane)}")
    pinned = EFFORT_PINNED.get(lane)
    if pinned and effort != pinned:
        raise ValueError(
            f"{_safe(lane)} 는 effort {pinned} 고정이다 (D-101 · 받은 값: {_safe(effort)}). "
            f"allow_off_ladder 로도 열리지 않는다")
    physical = set(orca_efforts_for(lane))
    policy = {m["top"], m["std"]}
    if process_effort(proc, lane) in physical:
        policy.add(process_effort(proc, lane))    # D-106 — 공정별 기본값은 그 공정에서 정책 단이다
    allowed = (physical | policy) if allow_off_ladder else policy
    if effort not in allowed:
        if effort in physical and not allow_off_ladder:
            raise ValueError(
                f"{_safe(lane)} 의 정책 단은 {sorted(policy)} 다 "
                f"(받은 값: {_safe(effort)}). Orca 는 받는 값이니 의도한 상향이면 "
                f"allow_off_ladder=True 로 명시할 것 — 원장에 그대로 남는다")
        raise ValueError(
            f"{_safe(lane)} 는 {_safe(effort)} 를 쓸 수 없다. "
            f"정책 {sorted(policy)} · Orca 실측 허용 {sorted(physical)}. "
            f"상한을 넘겨 부르면 워커가 뜨지 않는다(invalid_argument)")
    return effort


def slug_for(lane, effort):
    """실제 CLI 에 넘길 모델 슬러그. agy 는 effort 가 슬러그에 박힌다."""
    m = LANES[lane]
    if m["effort_style"] == "slug-suffix":
        return f"{lane}-{effort}"
    return lane


def dispatch_argv(lane, effort, task_id, name, worktree="new-top-level",
                  allow_off_ladder=False, proc=None):
    """디스패치 커맨드를 '배열'로 만든다.

    발주 C3: effort 가 반드시 박히도록 코드에서 강제한다 (sol 기본 low 함정).
    발주 S3: shell=True 금지 · 문자열 연결 금지 — 호출자는 이 배열을 그대로 쓴다.

    allow_off_ladder=True 면 정책 두 단 밖의 값도 쓸 수 있다 —
    단 Orca 실측 허용목록 안에서만이다 (validate_effort 참조).
    """
    m = LANES.get(lane)
    if not m:
        raise ValueError(f"unknown lane: {_safe(lane)}")
    validate_effort(lane, effort, allow_off_ladder=allow_off_ladder, proc=proc)

    # 실전 검증에서 잡힘 (2026-09-04): 생성 플래그(--name/--repo/--base-branch/
    # --display-name/--comment/--setup)는 **새 워크트리에만** 허용된다.
    # current/기존 워크트리에 붙이면 invalid_argument 로 거부된다 —
    # 그런데 Orca 터미널 밖에서 통과하는 셀렉터는 current 뿐이라,
    # 무조건 붙이면 실사용 경로가 통째로 막힌다.
    creating = worktree.startswith("new-")
    argv = ["orca", "orchestration", "worker-start",
            "--task", str(task_id), "--worktree", worktree]
    if creating:
        argv += ["--name", str(name)]
    mode = m.get("dispatch", "orca")
    if mode == "unavailable":
        raise ValueError(
            f"{lane} 는 오르카 워커로 기동할 수 없다 (dispatch=unavailable — agent 미등록이거나 "
            f"과제 전달이 실측으로 실패한 레인, D-28 #12). "
            f"헤드리스 CLI 로 따로 돌리거나 다른 레인을 쓸 것")
    argv += ["--agent", m["cli"]]
    if mode == "orca":
        argv += ["--model", slug_for(lane, effort)]

    if m["effort_style"] == "flag" and mode == "orca":
        argv += ["--effort", effort]           # C3 — 절대 생략하지 않는다
    elif m["effort_style"] == "prompt-keyword" and mode == "orca":
        # claude 는 effort 플래그가 아니라 프롬프트 키워드로 발동한다.
        # 표준은 max, 최상위는 max + 프롬프트 첫 줄 'ultracode'.
        argv += ["--effort", "max"]
    # slug-suffix(agy) 는 슬러그에 이미 들어갔으므로 플래그를 붙이지 않는다

    if creating:
        argv += ["--setup", "run"]          # 생성 워크트리에만 허용
    argv += ["--json"]
    return argv


def build_spec(lane, effort, spec):
    """워커에게 줄 과제 서술. 최상위 effort 면 첫 줄에 키워드를 강제 prepend 한다.

    감사 MED (2026-09-04 재검증): claude 는 두 effort 모두 `--effort max` 라서
    argv 만으로는 최상위와 표준이 **byte-for-byte 동일**하다. 최상위는 프롬프트
    첫 줄의 `ultracode` 로만 발동하는데, prompt_prefix() 가 별도 함수로만 있고
    run_dispatch() 가 spec 을 받지도 호출하지도 않아 **조용히 표준으로 돌았다.**
    → spec 을 wrapper 가 받아서 여기서 조립한다.
    """
    prefix = prompt_prefix(lane, effort)
    body = spec or ""
    if prefix:
        return prefix + "\n" + body
    return body


def spec_digest(text):
    """dispatch·원장에 남길 spec 해시 — 무엇을 보냈는지 나중에 대조할 수 있게."""
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


def run_dispatch(lane, effort, task_id, name, worktree,
                 spec=None, timeout=600, dry=False, allow_off_ladder=False, proc=None):
    """디스패치를 '배열 그대로' 실행한다. 문자열로 합치지 않는다.

    감사 HIGH-6 (2026-09-04): dispatch_argv() 는 안전한 배열을 돌려주는데
    문서가 `print(' '.join(...))` 로 실행 문자열을 만들고 있었다.
    워커 이름이 `safe; Write-Output X` 면 배열에서는 한 인자지만
    join 결과를 셸에서 실행하면 두 명령으로 갈라진다.
    → 표시용 문자열과 실행 경로를 분리하고, 실행은 이 함수만 쓴다.

    worktree 는 **필수**다 (감사 MED): 기본값 "new-top-level" 은 이 문서 자신이
    "Orca 터미널 밖에서 selector_not_found" 라고 적어둔 값이라, 예시대로 부르면
    워커가 시작조차 안 되고 rc 만 남는다. 호출자가 환경에 맞는 값을 명시하게 한다.

    반환: (returncode, stdout, stderr, meta). meta 에 최종 spec 과 그 해시가 들어간다.
    dry=True 면 실행하지 않고 argv·spec 을 돌려준다.
    """
    if not dry:
        return 2, "", LEGACY_EXECUTION_MESSAGE, {"execution": "blocked"}
    if not worktree or not isinstance(worktree, str):
        raise ValueError("worktree 를 명시해야 한다 (외부 셸에서는 보통 'current')")
    # MED-69: claude 최상위는 프롬프트 첫 줄 키워드로만 발동한다.
    # spec 없이 부르면 meta 에만 남고 워커에는 전달되지 않아 조용히 표준으로 돈다.
    # → spec 을 요구한다. 호출자가 이 spec 을 task-create --spec 으로 넣어야 한다.
    if prompt_prefix(lane, effort) and not spec:
        raise ValueError(
            f"{lane}@{effort} 는 프롬프트 첫 줄 키워드로 발동한다 — spec 을 넘겨야 한다. "
            f"반환된 meta['spec'] 을 task-create --spec 으로 그대로 쓸 것")
    argv = dispatch_argv(lane, effort, task_id, name, worktree,
                         allow_off_ladder=allow_off_ladder, proc=proc)
    final_spec = build_spec(lane, effort, spec)
    meta = {"spec": final_spec, "spec_sha": spec_digest(final_spec),
            "prompt_prefix": prompt_prefix(lane, effort),
            "off_ladder": effort not in set(ladder_for(lane))}
    return 0, json.dumps({"argv": argv, **meta}, ensure_ascii=False), "", meta


_REDACT = [
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\."),
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{16,}"),
]


def _safe(value, limit=24):
    """감사 LOW: 예외·로그에 비신뢰 원문을 그대로 반사하지 않는다.
    길이를 자르고 자격증명 패턴을 가린 뒤, 잘린 경우 digest 를 붙인다."""
    s = str(value)
    red = _redact(s, limit)
    if len(s) > limit:
        red += f"…(len={len(s)}, sha={hashlib.sha256(s.encode()).hexdigest()[:8]})"
    return red


def _redact(text, limit=2000):
    """CLI 출력에 자격증명이 섞여 로그·transcript 로 새는 것을 막는다."""
    if not text:
        return ""
    for rx in _REDACT:
        text = rx.sub("[REDACTED]", text)
    return text[:limit]


def _legacy_read_only(args):
    """Exact small inspection grammar; unknown flags/verbs and all writes deny."""
    if not all(isinstance(arg, str) for arg in args):
        return False
    args = list(args)
    if args and args[-1] == "--json":
        args.pop()
    if tuple(args) in (("status",), ("account", "list"),
                       ("orchestration", "worker-list")):
        return True
    if len(args) == 4 and args[0] == "orchestration":
        selector = {"worker-list": "--run", "worker-show": "--dispatch",
                    "worker-read": "--dispatch", "task-list": "--run",
                    "task-show": "--task", "run-show": "--run"}.get(args[1])
        return (selector is not None and args[2] == selector and
                re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}", args[3]) is not None)
    return False


def run_orca(*args, timeout=120):
    """Legacy read-only inspection. All writes, including worker-stop, deny.

    Not the pinned/bounded dispatch transport or billing evidence. Never add
    generation or arbitrary terminal commands to this compatibility list.
    """
    if not _legacy_read_only(args):
        return 2, "", LEGACY_EXECUTION_MESSAGE
    argv = ["orca", *[str(a) for a in args]]
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=timeout)      # shell=False 가 기본
    except subprocess.TimeoutExpired:
        return 1, "", f"timeout {timeout}s"
    except Exception as e:
        return 1, "", type(e).__name__
    return p.returncode, (p.stdout or "").strip(), _redact((p.stderr or "").strip())


def run_orca_json(*args, timeout=120):
    """run_orca + --json 파싱. 반환 (ok, result_or_error)."""
    args = args if args and args[-1] == "--json" else (*args, "--json")
    rc, out, err = run_orca(*args, timeout=timeout)
    if rc != 0:
        return False, {"code": "cli_failed", "rc": rc, "stderr": err}
    try:
        d = json.loads(out)
    except Exception:
        return False, {"code": "bad_json"}
    if not d.get("ok"):
        return False, d.get("error") or {"code": "unknown"}
    return True, d.get("result")


# ── codex 직행 (Orca 워커가 아니다) ─────────────────────────────
#  Orca 는 astra·daybreak 에 xhigh 를 상한으로 건다. ultra·max 가 정말 필요하면
#  codex CLI 를 직접 부르는 길밖에 없다 (2026-09-06 실호출로 확인).
#
#  ⚠ 이건 워커가 아니다. 차이를 알고 써야 한다:
#    · 워크트리 격리 없음 — 지금 이 셸의 cwd 에서 돈다
#    · worker_done / 게이트 / worker-release 없음 — 동기 블로킹 호출이다
#    · Orca 원장의 dispatch 행이 안 생긴다 — 원장 기록은 호출자가 직접 넣는다
#    · G1(자기채점) 은 그대로 지켜야 한다. 짠 쪽을 여기로 우회시키지 말 것
#  → 쓸 자리: 워커 하나를 통째로 띄울 값어치는 없는데 최상단 추론이 필요한 단발 판정.
def codex_exec_argv(model, effort, sandbox="read-only", cwd_check=True):
    """`codex exec` argv 배열. 프롬프트는 stdin 으로 넣는다 (인자로 주지 않는다).

    프롬프트를 argv 에 넣으면 셸을 안 거쳐도 되지만, 실측에서 stdin 대기로
    행에 걸린 이력이 있어 `-` 로 명시하고 stdin 을 쓴다.
    """
    if model in FORBIDDEN_LANES:
        raise ValueError(f"배정 금지 모델: {_safe(model)}")
    # D-101 — codex 직행 argv 는 지금 일을 받는 codex 레인(active_codex_lanes: gpt-6-astra 하나)으로만 만든다.
    #   철회된 레인 · 폐기 표시된 별칭(Daybreak 는 생성물 게이트 고정 자리 하나뿐이고 그 자리는 Orca 계획 검증을
    #   거친다) · LANES 에 없는 GPT id(gpt-6-sol · gpt-5.5 · 오타)는 전부 여기서 막힌다.
    if model not in active_codex_lanes():
        raise ValueError(f"codex 직행은 {active_codex_lanes()} 만 받는다 (D-101): {_safe(model)}")
    if effort not in CODEX_DIRECT_EFFORTS:
        raise ValueError(f"codex effort 는 {list(CODEX_DIRECT_EFFORTS)} 중 하나여야 한다 "
                         f"(받은 값: {_safe(effort)})")
    pinned = EFFORT_PINNED.get(model)
    if pinned and effort != pinned:
        raise ValueError(f"{_safe(model)} 는 effort {pinned} 고정이다 (D-101 · 받은 값: {_safe(effort)})")
    argv = ["codex", "exec", "-m", str(model),
            "-c", f'model_reasoning_effort="{effort}"',
            "-c", f'sandbox_mode="{sandbox}"']
    if not cwd_check:
        argv.append("--skip-git-repo-check")
    argv.append("-")
    return argv


def resolve_bin(argv):
    """argv[0] 을 실제 실행 파일로 바꾼다. shell 은 여전히 쓰지 않는다.

    2026-09-20 실측: 이 머신에서 `codex` 는 npm 전역 셰임 `codex.CMD` 다.
    shell=False 로 부르면 CreateProcess 가 확장자 없는 이름을 못 풀어 **FileNotFoundError** 로
    죽는다 - 다른 넷(orca · claude · grok · agy)은 .EXE 라 멀쩡해서 이 경로만 조용히 막혔다.
    `adversarial_eval._resolve` 가 같은 일을 하는데 이쪽에만 없었다.
    .cmd/.bat 은 CreateProcess 가 직접 못 띄우므로 `cmd /c` 로 감싼다.
    """
    exe = shutil.which(argv[0])
    if exe and os.path.splitext(exe)[1].lower() in (".cmd", ".bat"):
        return ["cmd", "/c", exe] + list(argv[1:])
    return ([exe] + list(argv[1:])) if exe else list(argv)


def run_codex_exec(prompt, model="gpt-6-astra", effort="xhigh",
                   sandbox="read-only", cwd=None, timeout=1800, dry=False):
    """codex 직행 실행. 반환 (returncode, stdout, stderr).

    기본을 read-only 로 둔 이유: 이 경로에는 워크트리 격리가 없다.
    쓰기가 필요하면 워커로 띄우는 것이 맞다 — sandbox 를 올리기 전에 그걸 먼저 검토할 것.
    D-101: 기본 effort 를 ultra → xhigh 로 내렸다(astra 는 xhigh 고정). 실호출은 여전히 차단돼 있다.
    """
    if not dry:
        return 2, "", LEGACY_EXECUTION_MESSAGE
    argv = codex_exec_argv(model, effort, sandbox=sandbox, cwd_check=False)
    return 0, json.dumps({"argv": argv, "prompt_sha": spec_digest(prompt)},
                         ensure_ascii=False), ""


# Legacy bad-worktree probes are not metadata-only and can spawn a worker.
def probe_orca_efforts(task_id, agent, model, efforts=None,
                       bad_worktree="name:zzz-nonexistent-probe"):
    """Retired: an invalid worktree is not proof of zero execution/cost."""
    raise RuntimeError(LEGACY_EXECUTION_MESSAGE)


def prompt_prefix(lane, effort):
    """프롬프트 첫 줄에 넣어야 하는 키워드 (없으면 빈 문자열)."""
    m = LANES[lane]
    if m["effort_style"] == "prompt-keyword" and effort == m["top"]:
        return "ultracode"
    return ""


# ── 가드 자동 검출 (발주 §7 — 이 4개만) ─────────────────────────
def check_guards(assignments, quota_checked_vendors=None, spawn_counts=None, fixed_unavailable=None):
    """자동 검출 가능한 가드만 본다. 반환: 위반 코드 리스트.

    assignments: [{"proc": <proc_id>, "lane": <lane>, "explore": bool}, ...]
    quota_checked_vendors: 디스패치 전 실제로 쿼터를 읽은 벤더 집합
    spawn_counts: {worker_name: spawn 수}
    fixed_unavailable: {proc_id: [사유]} — 고정 레인이 설 수 없다고 호출자가 밝힌 공정 (D-102).
        생성물 게이트가 폴백 레인에 선 상태 하나에서만 G1_SEC_SAME_MODEL 을 면제한다.
    """
    v = []

    # G1 — 자기 코드를 자기가 보안 리뷰하지 않는다.
    #
    # ⚠ 발주 §5 는 구조적으로 과잉제약이다 (2026-09-04 자체검증에서 발견):
    #   B 클래스에 판단 가능한 벤더는 claude·codex 둘뿐인데
    #   보안 게이트 2종이 이미 그 둘을 하나씩 점유한다
    #   (생성물게이트=sol/codex 고정, 비즈로직=opus/claude 고정).
    #   따라서 코딩을 어느 B 레인에 놓아도 보안 게이트 하나와는 벤더가 겹친다.
    # → 두 게이트의 성격을 나눠서 판정한다:
    #   · 생성물 안전성 게이트 = 만든 산출물을 검사한다 → 겹치면 진짜 자기검토. HARD (G1)
    #   · 비즈니스로직·인가   = 설계·권한을 본다      → 겹침이 불가피. SOFT (G1_BIZLOGIC)
    #   Simon 이 §5 를 바꾸면 이 분기도 같이 바꾼다.
    # Q-260913-09 (Simon 2026-09-16): 계획에 writes:true 인 공정도 코딩으로 본다 — 파일을 바꾸는 쪽이
    #   자기 결과물을 검사하지 못하게 한다(공정 이름이 coding 이 아니어도).
    impl = {LANES[a["lane"]]["vendor"] for a in assignments
            if (a.get("proc") == "coding" or a.get("writes")) and a.get("lane") in LANES}
    gate = {LANES[a["lane"]]["vendor"] for a in assignments
            if a.get("proc") == "security-artifact-gate" and a.get("lane") in LANES}
    biz = {LANES[a["lane"]]["vendor"] for a in assignments
           if a.get("proc") == "security-bizlogic-2nd" and a.get("lane") in LANES}
    if impl & gate:
        v.append("G1")
    if impl & biz:
        v.append("G1")          # D-260904-01 옵션 ①: SOFT(G1_BIZLOGIC) → HARD 로 승격

    # 보안 2종은 서로 달라야 한다.
    # 발주 §5 는 '다른 벤더'를 요구했으나 판단 벤더가 2개뿐이라 G1 과 동시에 만족할 수 없다
    # (D-260904-01). G1 이 우선이므로 여기서는 '다른 모델'을 강제한다.
    # 같은 모델이 두 보안 축을 겸하면 그건 어떤 배치에서도 잘못이다.
    # D-102 (2026-10-12 · Simon 판정) — 예외는 하나다: 생성물 게이트의 고정 레인이 설 수 없어 폴백 레인에 섰을 때.
    sec_lanes = {a["proc"]: a["lane"] for a in assignments
                 if a.get("proc", "").startswith("security-")}
    if len(sec_lanes) == 2:
        if len(set(sec_lanes.values())) < 2 and not _sec_same_model_waived(assignments, fixed_unavailable):
            v.append("G1_SEC_SAME_MODEL")

    # G3 — spawn 상한
    if spawn_counts:
        if any(c > SPAWN_CAP for c in spawn_counts.values()):
            v.append("G3")

    # G5 — 생략/None 은 확인 완료가 아니다. 이 함수는 사용 벤더만 검사하고,
    # validate_plan() 은 모든 4벤더를 검사한다.
    used = {LANES[a["lane"]]["vendor"] for a in assignments if a.get("lane") in LANES}
    if used - set(quota_checked_vendors or ()):
        v.append("G5")

    # 탐색 슬롯이 D·보안·코딩에 배정 (코딩은 EXPLORE_EXCLUDE — D-28 C2)
    for a in assignments:
        if a.get("explore") and a.get("proc") in EXPLORE_EXCLUDE:
            v.append("EXPLORE_MISASSIGNED")
            break

    return sorted(set(v))


def _deprecated_pin_ok(a):
    """폐기 표시된 레인이 서도 되는 단 한 자리인가 (D-101 · DEPRECATED_LANE_PINS).

    참이려면: 레인이 핀 표에 있고 · 공정이 그 표의 공정이며 · 그 공정의 고정 배정이 지금도 이 레인이고 ·
    명시 effort 가 없거나 고정 effort 와 같다. 하나라도 어긋나면 거짓이다(= LANE_DEPRECATED).
    """
    lane, proc = a.get("lane"), a.get("proc")
    if not proc or DEPRECATED_LANE_PINS.get(lane) != proc:
        return False
    fixed = fixed_for(proc)
    if not fixed or fixed[0] != lane:
        return False
    return a.get("effort") in (None, "", fixed[1])


def fixed_fallback_for(proc_id):
    """고정 공정의 폴백이면 (lane, effort), 없으면 None (D-102 · FIXED_FALLBACKS)."""
    return FIXED_FALLBACKS.get(proc_id)


def _unavailable_reasons(fixed_unavailable, proc):
    """fixed_unavailable 에서 그 공정의 사유 목록을 꺼낸다. 비었거나 형식이 다르면 [] 다(= 폴백 닫힘)."""
    if fixed_unavailable is None:
        return []
    if not isinstance(fixed_unavailable, dict):
        raise TypeError("fixed_unavailable must be a dict of process id -> list of reasons")
    reasons = fixed_unavailable.get(proc)
    if not isinstance(reasons, (list, tuple, set, frozenset)):
        return []
    return sorted({r.strip() for r in reasons if isinstance(r, str) and r.strip()})


def _fixed_fallback_ok(a, fixed_unavailable):
    """고정 공정이 폴백 레인에 서도 되는가 (D-102).

    참이려면: 공정에 폴백이 선언돼 있고 · 레인이 그 폴백 레인이며 · 호출자가 그 공정의 고정 레인이
    설 수 없는 사유를 하나 이상 밝혔고 · 명시 effort 가 없거나 폴백 effort 와 같다.
    """
    proc = a.get("proc")
    fallback = FIXED_FALLBACKS.get(proc)
    if not fallback or a.get("lane") != fallback[0]:
        return False
    if not _unavailable_reasons(fixed_unavailable, proc):
        return False
    return a.get("effort") in (None, "", fallback[1])


def _sec_same_model_waived(assignments, fixed_unavailable):
    """두 보안 게이트가 같은 모델이어도 되는 단 한 상태인가 (D-102).

    생성물 게이트가 정확히 하나이고 폴백 조건(_fixed_fallback_ok)을 채우며, 인가 게이트도 정확히 하나이고
    자기 고정 레인에 있을 때만 참이다. 인가 게이트를 다른 레인으로 옮겨 같아진 경우는 면제하지 않는다.
    """
    gate = [a for a in assignments if a.get("proc") == "security-artifact-gate"]
    biz = [a for a in assignments if a.get("proc") == "security-bizlogic-2nd"]
    if len(gate) != 1 or len(biz) != 1:
        return False
    return (_fixed_fallback_ok(gate[0], fixed_unavailable)
            and biz[0].get("lane") == fixed_for("security-bizlogic-2nd")[0])


def validate_plan(assignments, quota_checked_vendors=None, spawn_counts=None, quota_states=None,
                  fixed_unavailable=None):
    """디스패치 전 계획 전체를 검증한다. 반환 (ok, violations, notes).

    fixed_unavailable: {proc_id: [사유]} — 고정 레인이 설 수 없다고 호출자가 사유와 함께 밝힌 공정 (D-102).
      그 공정은 FIXED_FALLBACKS 의 폴백 레인·effort 에만 설 수 있다. 사유가 비면 폴백은 열리지 않는다.

    감사 MED (재검증): check_guards() 는 list 만 돌려주고 run_dispatch() 가
    이를 요구하지 않아서, 호출자가 보안 배정을 목록에서 빼거나 아예 호출하지
    않으면 G1/G3/G5 를 전부 우회할 수 있었다. coding 1개만 주고
    quota_checked_vendors=['claude'] 로 부르면 위반이 [] 로 나왔다.
    → 필수 게이트 존재와 4벤더 전체 쿼터를 여기서 강제한다.
    """
    # Iterator 입력도 두 검증 단계에서 동일하게 보도록 한 번만 고정한다.
    checked_vendors = tuple(quota_checked_vendors or ())
    v = list(check_guards(assignments, checked_vendors, spawn_counts, fixed_unavailable))
    notes = []

    procs = {a.get("proc") for a in assignments}
    if "coding" in procs or any(a.get("writes") for a in assignments):   # Q-09: writes 도 게이트 필수
        for need in ("security-artifact-gate", "security-bizlogic-2nd"):
            if need not in procs:
                v.append("MISSING_SECURITY_GATE")
                notes.append(f"코딩이 있는 라운드에 {need} 가 없다")

        # D-28 #5 — 코딩은 PROCESS_LANES["coding"] 안에서만. codex 폴백 없음.
        for a in assignments:
            if (a.get("proc") == "coding" or a.get("writes")) and a.get("lane") not in PROCESS_LANES["coding"]:
                v.append("CODING_LANE_NOT_ALLOWED")
                notes.append(f"coding 레인 {a.get('lane')} 은 허용 목록 {PROCESS_LANES['coding']} 밖이다 (D-28 #5)")

        # D-28 #14 — 게이트 벤더가 사용 금지(한도 100% 도달·실호출 실패, Q-05)면 코딩 라운드를 띄우지 않는다.
        #   quota_states: {vendor: "ok"|"demote"|"blocked"|"unknown"} — make_intake 가 판정한 값.
        if quota_states:
            blocked = sorted(vd for vd in gate_vendors() if quota_states.get(vd) == "blocked")
            if blocked:
                v.append("GATE_VENDOR_BLOCKED")
                notes.append(f"보안 게이트 벤더 {blocked} 사용 금지 — 코딩 없는 라운드로 축소한다 (D-28 #14)")

    # D-28 #4 — A-verify 는 읽기 전용이다. 파일을 바꾸는 작업이면 coding 으로 재분류해 G1 을 받는다.
    for a in assignments:
        if a.get("class") == "A-verify" and a.get("writes"):
            v.append("A_VERIFY_WRITES")
            notes.append(f"{a.get('proc')}: A-verify 는 읽기 전용 — 파일을 바꾸면 coding 으로 재분류한다 (D-28 #4)")

    # G5 는 '4벤더 각각' 이다. 인자 생략/None 도 미확인으로 fail closed.
    missing = set(VENDORS) - set(checked_vendors)
    if missing:
        if "G5" not in v:
            v.append("G5")
        notes.append(f"쿼터 미확인 벤더: {sorted(missing)}")

    for a in assignments:
        lane = a.get("lane")
        if lane in LANES and LANES[lane].get("dispatch") == "unavailable":
            v.append("LANE_NOT_DISPATCHABLE")
            notes.append(f"{a.get('proc')} 의 레인 {lane} 은 오르카 워커로 못 띄운다")
        if lane in FORBIDDEN_LANES:
            v.append("FORBIDDEN_LANE")
            notes.append(f"{a.get('proc')} 에 배정 금지 레인 {lane}")
        # D-98 (2026-10-12) — 제공사가 폐기 표시한 레인은 새 계획에 넣지 못한다.
        # D-101 — 예외는 DEPRECATED_LANE_PINS 의 한 자리뿐이다: 그 레인이 지금도 고정 배정인 고정 공정,
        #   그리고 명시 effort 가 없거나 고정 effort 와 같을 때. 그 밖은 전부 그대로 막힌다.
        if lane in DEPRECATED_LANES and not _deprecated_pin_ok(a):
            v.append("LANE_DEPRECATED")
            notes.append(f"{a.get('proc')} 의 레인 {lane} 은 제공사가 폐기 표시했다 — "
                         f"고정 공정 {DEPRECATED_LANE_PINS.get(lane, '없음')} 의 고정 effort 로만 선다 (D-98 · D-101)")
        # D-101 (2026-10-12) — 소유자가 뺀 레인은 원장 호환용 키일 뿐이다. 예외 자리는 없다.
        if lane in WITHDRAWN_LANES:
            v.append("LANE_WITHDRAWN")
            notes.append(f"{a.get('proc')} 의 레인 {lane} 은 철회됐다 — GPT 쪽은 gpt-6-astra @xhigh 만 쓴다 (D-101)")
        # G13 보강 (2026-09-19 모의 인수인계 실측) — 위의 GATE_VENDOR_BLOCKED 는 코딩 라운드의
        #   게이트 벤더만 본다. 그래서 revalidate_for_retry 로 일반 공정을 사용 금지 레인
        #   (한도 100% 도달·실호출 실패, Q-05 — 예: grok 402)으로 넘기는 재배정이 통과했다.
        #   강등(demote)은 설계대로 허용하고, 금지(blocked)만 막는다.
        vendor = LANES.get(lane, {}).get("vendor") if lane else None
        if quota_states and vendor and quota_states.get(vendor) == "blocked":
            v.append("LANE_VENDOR_BLOCKED")
            notes.append(f"{a.get('proc')} 의 레인 {lane} 은 벤더 {vendor} 가 사용 금지 상태다 (Q-05 · G13)")
        fixed = fixed_for(a.get("proc"))
        unavailable = _unavailable_reasons(fixed_unavailable, a.get("proc"))
        if fixed and lane and lane != fixed[0]:
            # D-102 — 고정 레인이 설 수 없다고 사유와 함께 밝혀졌고 폴백 레인·effort 에 섰을 때만 통과한다.
            if _fixed_fallback_ok(a, fixed_unavailable):
                fallback = FIXED_FALLBACKS[a["proc"]]
                notes.append(f"{a.get('proc')}: 고정 레인 {fixed[0]} 가 설 수 없어({', '.join(unavailable)}) "
                             f"폴백 {fallback[0]} @{fallback[1]} 로 선다 (D-102)")
                if _sec_same_model_waived(assignments, fixed_unavailable):
                    notes.append("두 보안 게이트가 같은 모델이다 — G1_SEC_SAME_MODEL 은 이 폴백 상태에서만 면제한다 (D-102)")
            else:
                v.append("FIXED_LANE_OVERRIDDEN")
                notes.append(f"{a.get('proc')} 는 {fixed[0]} 고정인데 {lane} 로 배정됨")
        elif fixed and lane and unavailable:
            # 설 수 없다고 해 놓고 그 레인에 배정했다 — 둘 중 하나가 틀렸다. 띄우지 않는다.
            v.append("FIXED_LANE_UNAVAILABLE")
            notes.append(f"{a.get('proc')} 의 고정 레인 {fixed[0]} 는 설 수 없다고 보고됐다({', '.join(unavailable)})")

        # 명시 effort 는 여기서 미리 검증한다 — 디스패치 루프 중간에 터지면
        # 앞의 워커는 이미 떠 있고 뒤는 안 뜬 반쪽 상태가 된다.
        if lane in LANES and a.get("effort"):
            try:
                validate_effort(lane, a["effort"],
                                allow_off_ladder=bool(a.get("off_ladder")), proc=a.get("proc"))
            except ValueError as e:
                v.append("EFFORT_NOT_ALLOWED")
                notes.append(f"{a.get('proc')}: {e}")

    return (not v), sorted(set(v)), notes


def validate_and_dispatch(assignments, task_of, worktree,
                          quota_checked_vendors=None, spawn_counts=None,
                          spec_of=None, dry=False, quota_states=None, fixed_unavailable=None):
    """계획 검증을 통과해야만 디스패치한다. 위반이 있으면 아무것도 실행하지 않는다.

    task_of / spec_of: proc_id -> task_id / spec 을 주는 dict 또는 callable.
    fixed_unavailable: validate_plan 과 같다 (D-102).
    반환 (ok, results, violations, notes)
    """
    if not dry:
        return False, [], [LEGACY_EXECUTION_DISABLED], [LEGACY_EXECUTION_MESSAGE]
    ok, v, notes = validate_plan(assignments, quota_checked_vendors, spawn_counts,
                                 quota_states=quota_states, fixed_unavailable=fixed_unavailable)
    if not ok:
        return False, [], v, notes

    def _get(m, key):
        return m(key) if callable(m) else (m or {}).get(key)

    results = []
    for a in assignments:
        lane = a["lane"]
        proc = a.get("proc")
        fixed = fixed_for(proc)
        # 우선순위: 명시 effort > 고정 공정의 effort > 반증질문으로 정한 정책 단.
        # 명시 effort 는 validate_plan 에서 이미 검증됐다.
        if a.get("effort"):
            effort = a["effort"]
        elif fixed and lane != fixed[0] and _fixed_fallback_ok(a, fixed_unavailable):
            effort = FIXED_FALLBACKS[proc][1]     # D-102 — 폴백 레인에는 폴백의 고정 effort
        elif fixed:
            effort = fixed[1]
        else:
            effort = effort_for(lane, a.get("falsifiable", False), proc=proc)
        rc, out, err, meta = run_dispatch(
            lane, effort, _get(task_of, proc), a.get("name") or proc, worktree,
            spec=_get(spec_of, proc), dry=dry,
            allow_off_ladder=bool(a.get("off_ladder")), proc=proc)
        results.append({"proc": proc, "lane": lane, "effort": effort,
                        "rc": rc, "out": out, "err": err, **meta})
        if rc != 0 and not dry:
            notes.append(f"{proc} 디스패치 실패(rc={rc}) — 나머지를 중단한다")
            return False, results, v, notes
    return True, results, v, notes


def coordinator_conflict(assignments):
    """코디네이터 레인이 워커를 겸하면 경고 (발주 §5).

    D-28 #6: 클래스와 무관하게 본다 — sol 이 C-realtime·C-platform 2순위에 들어가
    B 밖에서도 겸임이 생긴다. 경고일 뿐 디스패치를 막지는 않는다.
    D-101: 코디네이터가 gpt-6-astra 가 됐다. astra 는 인가 게이트 고정이자 B·A-verify 1순위라
    코딩 라운드와 대부분의 B 라운드에서 참이다. 규칙은 그대로다(경고만).
    """
    return any(a.get("lane") == COORDINATOR[0] for a in assignments)


def revalidate_for_retry(assignments, proc, new_lane, **kw):
    """재시도·수동 재배정 전에 계획 전체를 다시 검증한다 (G13 · D-28 #14).

    assignments: 그 라운드의 원래 계획. proc 의 레인만 new_lane 으로 바꿔 validate_plan 에 넣는다.
    kw 는 validate_plan 인자(quota_checked_vendors · spawn_counts · quota_states) 그대로.
    반환 (ok, violations, notes, new_assignments) — ok 가 아니면 --retry-of 를 부르지 않는다.
    """
    new = []
    for a in assignments:
        b = dict(a)
        if b.get("proc") == proc:
            b["lane"] = new_lane
            b.pop("effort", None)     # 레인이 바뀌면 이전 effort 는 새 레인 사다리에 없을 수 있다
        new.append(b)
    ok, v, notes = validate_plan(new, **kw)
    return ok, v, notes, new


def handoff_spec(original_spec, reason, from_lane, to_lane, transcript_tail="", files_changed=None):
    """한도 도달로 실패·정지한 워커의 일을 여유 레인에 넘기는 새 task 과제 (Q-260913-05 · G4).

    트리거는 쿼터 % 가 아니라 **그 워커가 실제로 한도에 걸려 실패·정지했다는 신호**다
    (worker_done 실패 사유 · worker-read 끝부분의 한도 메시지 · 429/402). 실행 중인 워커를
    쿼터 % 로 선제 교체하지 않는다(G4). 새 task 를 띄우기 전에 revalidate_for_retry 로 계획을 다시 검증한다(G13).
    """
    files = [str(x) for x in (files_changed or [])]
    tail = (transcript_tail or "").strip()
    if len(tail) > 4000:
        tail = "…(앞부분 생략)…\n" + tail[-4000:]
    lines = [
        f"[인수인계 · {from_lane} → {to_lane} · 사유: {reason}]",
        "",
        "이전 워커가 한도에 걸려 끝내지 못한 일을 이어받는다. 이미 끝난 부분은 다시 하지 말고,",
        "아래 '바뀐 파일'과 '이전 출력 끝부분'으로 어디까지 됐는지 먼저 확인한 뒤 남은 일만 한다.",
        "이어받은 사실과 확인한 진행 지점을 worker_done 보고 첫 줄에 적는다.",
        "",
        "## 바뀐 파일 (이전 워커)",
        "\n".join(f"- {x}" for x in files) if files else "- (없음 또는 미확인 — git status 로 먼저 확인)",
        "",
        "## 이전 출력 끝부분",
        tail or "(없음)",
        "",
        "## 원래 과제",
        original_spec or "",
    ]
    return "\n".join(lines)


# ── SKILL.md 표 생성 (단일 출처 유지) ───────────────────────────
def emit_md():
    L = []
    L.append("<!-- ROUTING:BEGIN — scripts/routing.py 가 생성한다. 손으로 고치지 말 것 -->")
    L.append("")
    L.append("### 레인 카탈로그")
    L.append("")
    L.append("| 레인 | CLI | 최상위 | 표준 | Orca 실측 허용 | effort 전달 | 오르카 기동 | 정격 |")
    L.append("|---|---|---|---|---|---|---|---|")
    disp = {"orca": "✅ `--model`·`--effort` 가능",
            "orca-no-model": "⚠ `--agent` 만 — `--model` 거부",
            "unavailable": "❌ **Orca 워커 불가** (agent 미등록·과제 전달 실패 — CLI 직행만)"}
    for lane, m in LANES.items():
        style = {"flag": "`--effort`", "slug-suffix": "**슬러그 내장**",
                 "prompt-keyword": "프롬프트 키워드"}[m["effort_style"]]
        if m.get("dispatch") != "orca":
            # --effort 는 --model 을 요구하는데 이 레인은 --model 을 거부한다 →
            # Orca 경로에서 effort 지정이 아예 불가능하다. 표가 그렇게 말해야 한다.
            phys = "— **지정 불가** (그 CLI 기본값)"
        elif m["effort_style"] == "prompt-keyword":
            phys = "`standard` · `ultracode` (와이어는 항상 `--effort max`)"
        else:
            phys = " · ".join(f"`{e}`" for e in orca_efforts_for(lane))
        boot = disp[m.get('dispatch', 'orca')]
        # D-101 — 표가 '기동 가능'이라고만 말하면 철회·폐기 레인을 쓸 수 있는 것처럼 읽힌다.
        if lane in EFFORT_PINNED:
            phys += f" — 정책은 **`{EFFORT_PINNED[lane]}` 고정** (off-ladder 불가)"
        if lane in WITHDRAWN_LANES:
            boot = "⛔ **철회** (D-101) — 새 배정은 `LANE_WITHDRAWN` · 원장 호환용 키"
        elif lane in DEPRECATED_LANES:
            boot = (f"⚠ 폐기 표시 — 고정 공정 `{DEPRECATED_LANE_PINS.get(lane, '없음')}` 자리만 "
                    "(그 밖은 `LANE_DEPRECATED`)")
        L.append(f"| `{lane}` | {m['cli']} | `{m['top']}` | `{m['std']}` | {phys} | {style} "
                 f"| {boot} | {m['ctx']} |")
    L.append("")
    L.append("**과거 Orca 정책표이며 현재 실행·가격·계정 증거가 아니다.** "
             "`--probe-efforts`는 worker-start를 사용하므로 차단됐다. "
             "중앙 registry/runtime과 guarded adapter로 재검증한다. "
             "`allow_off_ladder=True`는 오프라인 argv 검증 옵션일 뿐 실행 허가가 아니다.")
    L.append("")
    L.append("**오르카 기동은 2026-09-04 실측이다.** `--model` 은 Claude·Codex·Cursor 만 받는다 "
             "(orca help) — grok·gemini 는 `--agent` 만 주고 모델은 그 CLI 의 기본값이 쓰인다. "
             "⚠ **agent id 는 CLI 이름이 아니라 좌석 이름이다**: `--agent agy` 는 "
             "`agent_unconfigured` 로 거부되고 `--agent antigravity` 가 정본이다. "
             "(CLI 바이너리는 `agy`, Orca 등록명은 `antigravity`.)")
    L.append("")
    # D-28: SKILL.md 본문 500줄 상한(SimonK-stack validate_skill E007) 때문에 새 줄을 늘리지 않고
    #   이 한 줄 끝에 붙인다. 자세한 규칙은 references/d28-routing.md.
    L.append(f"**배정 금지**: {' · '.join('`'+x+'`' for x in sorted(FORBIDDEN_LANES))} "
             "— 용도 미검증 / R&R 미확정 (발주 §3) · **D-28**: 코딩은 공정 전용 목록 `PROCESS_LANES` "
             "(claude 전용 · codex 폴백 없음 · #5 · 파일을 바꾸는 `writes` 공정도 같음 · Q-09) · "
             "fable·sonnet 은 M1 통과(2026-09-16) 뒤 2순위 편입 · A-verify = astra → fable → opus(읽기 전용 · `writes` 면 A_VERIFY_WRITES) · 반증 \"예\"인 A 작업은 A-verify 로 승격 · gemini `unavailable`(M6) "
             "→ `references/d28-routing.md`")
    L.append("")
    L.append("**D-67 (2026-10-04)**: `claude-opus-5-5`(flag · low~max)·`gpt-6.1-sol`(flag · minimal~xhigh)을 "
             "옛 레인 옆에 **등록만** 했다 — 우선순위·코딩·종합 고정·코디네이터가 새 키로 옮겨졌다. "
             "읽기 전용 canary(`launch.requested` ↔ `launch.effective` 대조)는 2026-10-04 에 두 레인 모두 "
             "통과했지만, native send 와 계정/과금 인증서 전까지는 "
             "동작 레인이 아니며 $0 게이트·G5·Orca 인증서가 똑같이 걸린다. 옛 키(`claude-opus-5` 등)는 "
             "원장 호환용으로 남고 `gpt-5.6-sol` 은 C 클래스 끝 폴백이었다. grok 은 Orca 가 모델을 고정하지 못해 그대로다. "
             "(그 시점 기록 — `gpt-6.1-sol`·`gpt-5.6-sol` 은 D-101 로 철회됐다. 아래.)")
    L.append("")
    L.append("**2026-10-05 Simon 지시 (2.15.5)**: A 클래스를 현행 세대로 옮겼다 — `gpt-6-luna`(flag · minimal~xhigh · "
             "사다리 low/medium) → `claude-sonnet-5-5`(flag · low~max · 사다리 medium/high, xhigh·max 는 토큰 폭증이라 "
             "정책 밖) → `claude-opus-5-5`. 옛 `gpt-5.6-luna`·`claude-sonnet-5` 는 원장 호환용(우선순위 밖)이다. "
             "두 새 레인은 **등록만** 됐다 — 읽기 전용 canary 와 계정/과금 인증서 전까지 동작 레인이 아니며 "
             "$0 게이트·G5·Orca 인증서가 똑같이 걸린다. (그 시점 기록 — `gpt-6-luna` 는 D-101 로 철회됐다. 아래.)")
    L.append("")
    L.append("**D-98 (2026-10-12 오전 · 2.16.0 · 같은 날 D-101 이 뒤집었다)**: 보안 생성물 게이트를 "
             "`gpt-daybreak-blue-latest` → `gpt-6.1-sol` @xhigh 로 옮겼었다. OpenAI 가 그 별칭을 deprecated 로 표시했고"
             "(종료일·대체 ID 미공지) 중앙 계획기는 `MODEL_NOT_ACTIVE` 로 막는다 — 이 두 사실은 지금도 그대로다. "
             "그때 만든 방어 루브릭과 fail-closed 규칙(빈 출력·차단·첫 줄 누락·모호한 판정 = FAIL)은 "
             "`references/security-artifact-gate.md` 에 남아 지금 게이트에도 쓴다.")
    L.append("")
    L.append("**D-99 (2026-10-12 오전 · 2.16.0)**: `claude-haiku-5-5`(flag · low~max · 사다리 low/medium, high 이상은 정책 밖)를 "
             "A 클래스의 Claude 쪽 첫 폴백(2순위)으로 넣었다. 읽기 전용 canary(run `run_8f7a27febc38` · @low · 정답이 정해진 "
             "A 과제 3/3)는 통과했지만 계정/과금 인증서 전까지 동작 레인이 아니며 $0 게이트·G5·Orca 인증서가 똑같이 걸린다. "
             "큰 입력·10만 토큰 초과 입력·쿼터 절감은 미측정이다. 같은 날 D-101 로 1순위가 됐다(아래).")
    L.append("")
    gate_lane, gate_effort = fixed_for("security-artifact-gate")
    L.append("**D-101 (2026-10-12 오후 · 2.17.0 · Simon 지시 · 토론 없음)**: \"gpt 6.1 sol은 너무 느려서 빼기로 결정. "
             "기획단계 gpt astra xhigh와 opus 5.5. 단순작업 sonet 5.5\" · \"gpt 쪽은 astra 말고는 쓰지마. gpt 를 넣어야한다면 "
             "astra xhigh.\" · \"보안게이트는 데이브레이크로 할려했는데 그게 안돼면 opus 5.5로 하자.\" "
             f"① codex 벤더에서 일을 받는 레인은 `gpt-6-astra` 하나이고 effort 는 `{EFFORT_PINNED['gpt-6-astra']}` 고정이다"
             "(사다리 std = top · off-ladder 로도 다른 값 불가). "
             f"② 철회된 레인 {' · '.join('`'+x+'`' for x in sorted(WITHDRAWN_LANES))} 는 원장 호환용 키로만 남고 새 배정은 "
             "`LANE_WITHDRAWN` 으로 막힌다 — 결함 때문이 아니다(`gpt-6-luna` 는 D-91, `gpt-6.1-sol` 은 D-67·D-98 canary 를 통과했다). "
             "③ A 클래스 = " + " → ".join(f"`{l}`" for l in CLASS_LANES["A"]) + "(전부 claude · codex 폴백 없음) · "
             "C-realtime = " + " → ".join(f"`{l}`" for l in CLASS_LANES["C-realtime"]) + " · "
             "C-platform = " + " → ".join(f"`{l}`" for l in CLASS_LANES["C-platform"]) + ". "
             f"④ 코디네이터 = `{COORDINATOR[0]}` @{COORDINATOR[1]}(인가 게이트·B 1순위와 같은 모델이라 겸임 경고가 자주 뜬다). "
             f"⑤ 생성물 게이트 = `{gate_lane}` @{gate_effort} 로 되돌렸다. 제공사의 deprecated 표시와 중앙 계획기의 "
             "`MODEL_NOT_ACTIVE` 는 그대로이고, `LANE_DEPRECATED` 는 이 고정 자리 하나만 통과시킨다(그 밖은 여전히 막힌다). "
             "그래서 packaged registry 를 쓰는 중앙 계획기 경로에서는 게이트가 계속 막힌다 — 고정이지 동작이 아니다. "
             "canary(오케스트레이터 · run `run_b08adccb4ec8` · `ctx_41243c1a0d26` · 15:19~15:20 KST): requested == effective, "
             "심은 결함 4개에 `GATE: BLOCK` 정확히, 심은 샘플 1건. 별칭은 예고 없이 사라질 수 있다 — 실행 전마다 Codex "
             "카탈로그를 확인하고, 없거나 출력이 비거나 차단되면 게이트는 FAIL 이다. "
             "**미결**: Simon 이 말한 폴백 `claude-opus-5-5` 는 G1(코딩과 같은 모델이 자기 산출물을 검사)과 충돌해 구현하지 않았다 — "
             "판정 대기(`references/security-artifact-gate.md` 의 Open item). 코디네이터로서의 astra 와 A 클래스 순서 변경은 "
             "canary 를 돌리지 않았다. (그 시점 기록 — 폴백은 D-102 가 정했다. 아래.)")
    L.append("")
    fb_lane, fb_effort = FIXED_FALLBACKS["security-artifact-gate"]
    L.append("**D-102 (2026-10-12 밤 · 2.18.0 · Simon 판정 · 토론 없음)**: 생성물 게이트의 폴백을 정했다 — "
             f"`{gate_lane}` 가 **설 수 없을 때만** `{fb_lane}` @{fb_effort} 가 대신 선다. Simon 이 먼저 말한 "
             "`claude-opus-5-5` 폴백은 이 판정이 대체한다(코딩과 같은 모델이 자기 산출물을 검사하게 된다). "
             "① 고정 배정은 그대로다 — 설 수 있으면 Daybreak 가 먼저다. "
             "② `validate_plan(fixed_unavailable={공정: [사유]})` 로 사유를 밝혔을 때만 폴백 레인이 "
             "`FIXED_LANE_OVERRIDDEN` 없이 서고, 그 상태 하나에서만 `G1_SEC_SAME_MODEL` 을 면제한다"
             "(인가 게이트와 같은 모델이 된다). 사유가 없으면 예전과 똑같이 막힌다. "
             "③ 중앙 계획기는 호스트의 요청이 아니라 제시받은 후보를 거부한 자기 기록으로 사유를 만든다 — 게이트 단계에 제시된 Daybreak "
             "Orca 후보가 전부 가용성 사유(`MODEL_NOT_ACTIVE` 등)로 거부됐을 때만 단계에 `gate_fallback` 을 남긴다. "
             "그래서 packaged registry 경로에서는 지금 이 폴백이 게이트를 맡는다. Daybreak 후보를 아예 내지 않으면 "
             "폴백은 열리지 않는다. "
             "④ `G1`(코딩 벤더 ≠ 게이트 벤더) · 계획기의 Daybreak 차단 · $0·G5·인증서 게이트는 그대로다. "
             "⑤ 폴백은 '설 수 없음'에만 쓴다 — Daybreak 가 실제로 돌아 BLOCK · 빈 출력 · 차단 · 모호한 판정을 낸 뒤에는 "
             "폴백하지 않는다(FAIL 이다). "
             "⑥ 폴백 상태에서는 한 모델이 두 보안 질문에 모두 답한다 — 두 게이트가 서로 독립된 검사가 아니다. "
             "canary(오케스트레이터 · run `run_3607f8833d7e` · `ctx_56f442610119` · 23:26 KST): requested == effective"
             f"(`{fb_lane}` · {fb_effort}), 같은 결함 4개 샘플에 `GATE: BLOCK` 정확히, 심은 샘플 1건.")
    L.append("")
    L.append("### 공정 → 클래스 → 레인")
    L.append("")
    L.append("| 공정 | 클래스 | 1순위 | 2순위 | 3후보 (이후 폴백) |")
    L.append("|---|---|---|---|---|")
    for pid, cls, label, fixed in PROCESSES:
        lanes = lanes_for_proc(pid, cls)
        if fixed:
            cells = [f"**`{fixed[0]}` @{fixed[1]} 고정**", "—", "—"]
            if pid in FIXED_FALLBACKS:     # D-102 — 고정 레인이 설 수 없을 때만 서는 폴백
                fb = FIXED_FALLBACKS[pid]
                cells[1] = f"폴백 `{fb[0]}` @{fb[1]} (고정 레인이 설 수 없을 때만 · D-102)"
        else:
            # D-67: 4번째 이후(같은 벤더 옛 세대 폴백)도 표에서 사라지지 않게 3후보 칸에 잇는다.
            cells = [f"`{l}`" for l in lanes[:2]] + ["—"] * (2 - len(lanes[:2]))
            cells.append(" → ".join(f"`{l}`" for l in lanes[2:]) or "—")
        if pid in PROCESS_LANES:
            label = f"{label} **(공정 전용 목록)**"
        L.append(f"| {label} | {cls} | {cells[0]} | {cells[1]} | {cells[2]} |")
    L.append("")
    L.append("### effort 결정 — 클래스가 아니라 태스크 속성")
    L.append("")
    L.append("> **반증 가능한 전제가 있나?** (\"X는 죽었다\"를 확인 / \"A가 B보다 낫다\"를 판정 / 원인 규명)")
    L.append("")
    L.append("| | " + " | ".join(f"`{l}`" for l in LANES) + " |")
    L.append("|---|" + "---|" * len(LANES))
    L.append("| **YES** 최상위 | " + " | ".join(f"`{m['top']}`" for m in LANES.values()) + " |")
    L.append("| **NO** 표준 | " + " | ".join(f"`{m['std']}`" for m in LANES.values()) + " |")
    # --model 을 못 주는 레인은 Orca 경로에서 effort 지정 자체가 불가능하므로
    # '상한'이라는 말이 성립하지 않는다 — 숫자를 적으면 지정된다는 오해를 만든다.
    L.append("| 사다리 밖 상한 (`allow_off_ladder`) | "
             + " | ".join(f"`{ceiling_for(l)}`" if LANES[l].get("dispatch") == "orca"
                          else "— (지정 불가)" for l in LANES) + " |")
    L.append("")
    L.append("이 사다리는 과거 transport 제약이다. 현재 모델/effort는 중앙 registry와 "
             "fresh runtime의 교집합으로 정한다. `run_codex_exec` 실호출은 차단됐으며 "
             "상한 초과를 direct CLI로 우회하지 않는다.")
    L.append("")
    L.append(f"코디네이터 레인 = **`{COORDINATOR[0]}` @{COORDINATOR[1]}** — 종합(D)과 벤더가 달라야 한다. "
             "워커 겸임은 클래스와 무관하게 경고한다(D-28 #6).")
    L.append("")
    L.append("### 레인별 산출물 제약")
    L.append("")
    L.append("| 레인 | 허용 | 금지 | 사유 |")
    L.append("|---|---|---|---|")
    for lane, r in OUTPUT_RULES.items():
        L.append(f"| `{lane}` | {r['allow']} | {r['deny']} | {r['why']} |")
    L.append("")
    L.append("### 가드")
    L.append("")
    L.append("| | 내용 | 자동 검출 |")
    L.append("|---|---|---|")
    for code, text, auto in GUARDS:
        L.append(f"| {code} | {text} | {'✅ 원장 기록' if auto else '— (오검출 방지)'} |")
    L.append("")
    L.append(f"쿼터: {QUOTA_DEMOTE}% 초과 → **모든 순위에서** 강등(ok 레인이 없으면 첫 강등 레인) · "
             f"{QUOTA_BLOCK}% 도달 → 사용 금지(Q-05) · 읽기 실패 = **미확인**(0%로 간주 금지) · "
             "실호출(G12) 실패 = 사용 금지 · 실호출 결과가 24시간 넘으면 미확인 · "
             "`quota_bucket` 이 있는 레인(fable)은 그 버킷으로 판정 (D-28 #13)")
    L.append("")
    L.append("<!-- ROUTING:END -->")
    return "\n".join(L)


def _cli_probe(argv):
    """Retired CLI entry; no argument can turn a spawn probe into metadata."""
    print(LEGACY_EXECUTION_MESSAGE)
    return 2


if __name__ == "__main__":
    if "--probe-efforts" in sys.argv:
        raise SystemExit(_cli_probe(sys.argv))
    if "--emit-md" in sys.argv:
        print(emit_md())
    elif "--json" in sys.argv:
        print(json.dumps({
            "lanes": LANES, "class_lanes": CLASS_LANES, "process_lanes": PROCESS_LANES,
            "processes": [{"id": p[0], "class": p[1], "label": p[2],
                           "fixed": list(p[3]) if p[3] else None} for p in PROCESSES],
            "coordinator": list(COORDINATOR),
            "forbidden": sorted(FORBIDDEN_LANES),
            "deprecated": sorted(DEPRECATED_LANES),
            "deprecated_pins": dict(sorted(DEPRECATED_LANE_PINS.items())),
            "withdrawn": sorted(WITHDRAWN_LANES),
            "effort_pinned": dict(sorted(EFFORT_PINNED.items())),
            "fixed_fallbacks": {p: list(f) for p, f in sorted(FIXED_FALLBACKS.items())},
            "ceilings": {l: ceiling_for(l) for l in LANES},
            "codex_direct_efforts": list(CODEX_DIRECT_EFFORTS),
        }, ensure_ascii=False, indent=2))
    else:
        print(f"레인 {len(LANES)} · 공정 {len(PROCESSES)} · 클래스 {len(CLASS_LANES)}")
        for l in LANES:
            print(f"  {l:26s} 정책 {LANES[l]['std']}/{LANES[l]['top']:9s} "
                  f"Orca 상한 {ceiling_for(l)}")
        print("--emit-md 로 SKILL.md 표를, --json 으로 기계 판독본을 낸다")
        print("--probe-efforts 는 차단됨; central runtime/guarded adapter를 사용한다")
