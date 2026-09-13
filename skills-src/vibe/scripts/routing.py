# routing.py — /vibe v2.1 라우팅 정본 (단일 출처)
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
import hashlib
import json
import re
import subprocess
import sys

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
    "claude-opus-5": {
        "cli": "claude", "vendor": "claude", "effort_style": "prompt-keyword",
        "top": "ultracode", "std": "standard", "ctx": "1M", "dispatch": "orca",
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
        # 클래스·순위 배치는 D-28 §35 토론 판정 전까지 CLASS_LANES 에 넣지 않는다.
        # prompt-keyword(ultracode) 방식이 아니라 --effort 플래그로 전달한다 — Orca 카탈로그의 launchArgs 가 --effort 다.
        "cli": "claude", "vendor": "claude", "effort_style": "flag", "dispatch": "orca",
        "top": "max", "std": "high", "ctx": "1M · 쿼터 fableWeekly 별도 · API 단가 Opus 5의 2배",
        "quota_bucket": "fableWeekly",
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
        "cli": "codex", "vendor": "codex", "effort_style": "flag", "dispatch": "orca",
        "top": "xhigh", "std": "high", "ctx": "272K(최대 872K) · Orca 상한 xhigh",
        "orca_efforts": ("minimal", "low", "medium", "high", "xhigh"),
    },
    "gpt-5.6-sol": {
        "cli": "codex", "vendor": "codex", "effort_style": "flag", "dispatch": "orca",
        "top": "ultra", "std": "high", "ctx": "1.5M",
        "orca_efforts": ("minimal", "low", "medium", "high", "xhigh", "max", "ultra"),
    },
    "gpt-5.6-terra": {
        "cli": "codex", "vendor": "codex", "effort_style": "flag", "dispatch": "orca",
        "top": "high", "std": "medium", "ctx": "1.5M",
        "orca_efforts": ("minimal", "low", "medium", "high", "xhigh", "max", "ultra"),
    },
    "gpt-5.6-luna": {
        "cli": "codex", "vendor": "codex", "effort_style": "flag", "dispatch": "orca",
        "top": "medium", "std": "low", "ctx": "1.5M · 최저가",
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
        "cli": "codex", "vendor": "codex", "effort_style": "flag", "dispatch": "orca",
        "top": "xhigh", "std": "high", "ctx": "보안 전용 · 기본 low · Orca 상한 xhigh",
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
        "dispatch": "orca-no-model",   # --model 은 Claude·Codex·Cursor 만 받는다
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
    "A":          ["gpt-5.6-luna", "gemini-3.8-flash", "grok-4.6"],
    # 2026-09-06: 2순위를 sol → gpt-6-astra 로 올린다.
    #   · astra 가 codex 계열 최상위 모델이다(models_cache priority 1).
    #   · sol 을 목록에서 빼면 코디네이터 좌석과 B 워커가 **구조적으로** 겹칠 수
    #     없게 된다 — coordinator_conflict() 가 잡던 상황이 기본값에서 사라진다.
    #   · 1순위를 claude 로 두는 이유는 성능이 아니라 가용성이다(codex 주간 64%,
    #     claude 주간 23% — 2026-09-06 실측). 이 스킬의 목적은 단일 벤더 쿼터가
    #     라운드를 죽이지 않게 하는 것이다.
    "B":          ["claude-opus-5", "gpt-6-astra", "gpt-5.6-terra"],
    "C-realtime": ["grok-4.6", "gemini-3.8-flash"],
    "C-platform": ["gemini-3.8-flash"],           # 대체 불가
    "D":          ["claude-opus-5"],              # 고정
    "N":          [],                             # 모델 미사용 — orca CLI
}

CLASS_LABEL = {
    "A": "기계적 — 판단 0",
    "B": "판단 — 우열·인과·설계",
    "C-realtime": "외부 — 실시간·수집",
    "C-platform": "외부 — 플랫폼·시각 (후보 1개)",
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
    # 벤더는 여전히 codex 라 위 양보는 그대로다 — 개선된 것은 모델 적합성뿐이다.
    #
    # 2026-09-06: 인가 게이트를 gpt-5.6-terra @high → gpt-6-astra @xhigh 로 올린다.
    #   비즈로직·인가 검사는 이 라운드에서 가장 '판단'에 가까운 자리다 —
    #   astra 설명이 정확히 그 자리를 가리킨다("complex, demanding work").
    #   [Simon 결정 2026-09-06] effort 도 같이 xhigh 로. 즉 Orca 에서 이 모델로
    #   갈 수 있는 최상단이다(그 위 max·ultra 는 Orca 가 안 받는다 — 위 원인 규명 참조).
    #   비용은 codex 주간 쿼터로 관리한다(60% 초과 시 강등 규칙이 이미 있다).
    #   두 게이트가 같은 codex 벤더인 것은 D-260904-01 에서 이미 양보한 부분이고,
    #   구분자는 이제 'effort 상한'이 아니라 **모델 성격**이다 —
    #   daybreak 은 model_specialty="cyber" 전용, astra 는 범용 프론티어.
    #   같은 모델이 두 축을 겸하면 G1_SEC_SAME_MODEL 이 여전히 잡는다.
    ("security-artifact-gate","B", "보안 — 생성물 안전성 게이트",
     ("gpt-daybreak-blue-latest", "xhigh")),
    ("security-bizlogic-2nd", "B", "보안 — 비즈니스 로직 · 인가",          ("gpt-6-astra", "xhigh")),
    ("trend-realtime",        "C-realtime", "트렌드 · 실시간",             None),
    ("research-collect",      "C-realtime", "웹 리서치 — 수집",            None),
    ("google-platform",       "C-platform", "Google 플랫폼 (BigQuery/Firebase/Workspace)", None),
    ("ui-visual",             "C-platform", "UI 시각 검증",                None),
    ("synthesis",             "D", "다레인 산출물 조립",                   ("claude-opus-5", "ultracode")),
    ("worktree-run-mgmt",     "N", "워크트리 · run 관리 (orca CLI)",       None),
]

PROC_BY_ID = {p[0]: p for p in PROCESSES}

# 코디네이터 레인 (발주 §5) — 종합(D)과 벤더가 달라야 한다.
#   sol 로 유지한다. astra 로 올리지 않은 이유가 두 개다:
#   ① sol 은 이제 B 우선순위 목록에도 고정 공정에도 없다 → 겸임 충돌이 구조적으로 0.
#   ② 코디네이터는 메일·디스패치 부기가 일이지 깊은 판단이 아니다. 프론티어 좌석은
#      실제로 판단하는 워커(B·보안 인가)에 쓴다. 그리고 sol 은 Orca 에서 ultra 가
#      실제로 통과하는 몇 안 되는 레인이다(astra 는 xhigh 가 상한).
COORDINATOR = ("gpt-5.6-sol", "ultra")

# 탐색 슬롯 제외 (발주 §11)
EXPLORE_EXCLUDE = {"synthesis", "security-artifact-gate", "security-bizlogic-2nd"}

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
    "gpt-5.6-luna": {
        "allow": "정형 변환 · 카운트 · 분류 · **부재 보고에는 탐색 범위 명시**",
        "deny":  "우열 판단 (필요하면 terra 이상으로 올린다) · 범위 없는 '0건'",
        "why":   "최저가 레인 — 판단을 맡기면 싼 값에 틀린다. "
                 "범위 요구는 Simon 결정(2026-09-04, luna03 채택)으로 A 클래스 전체에 적용된다",
    },
    "claude-opus-5": {
        "allow": "항목별 확신도 표기 필수 (강=기계검증 / 약=판단)",
        "deny":  "리포트만 내고 끝내기 — 사람이 읽는 것은 결정 시트 1장이다",
        "why":   "종합 레인이므로 사람의 결정으로 이어져야 한다",
    },
    "gpt-6-astra": {
        "allow": "판단마다 근거(파일·행·명령 출력) 첨부 · 반증 시도 1건 이상 명시",
        "deny":  "대량 정형 변환에 배치 (A 클래스는 luna 로 내린다) · "
                 "`ultra`/`max` 로 Orca 디스패치 (거부된다 — 상한 xhigh)",
        "why":   "codex 계열 최상위 좌석이다. 싼 일에 태우면 쿼터만 태우고, "
                 "정책 밖 effort 로 부르면 워커가 아예 안 뜬다",
    },
    "gpt-daybreak-blue-latest": {
        "allow": "취약점 발견마다 file:line · 재현 경로 · 심각도 · 최소 패치",
        "deny":  "방어 목적 밖의 공격 코드 생성 · 범위 없는 '취약점 0건'",
        "why":   "보안 전용 레인 — 근거 없는 발견은 게이트를 무력화한다. "
                 "출력이 차단되면 Trusted Access 미승인이므로 terminal read 로 확인한다",
    },
}

# ── 가드 (발주 §7) ──────────────────────────────────────────────
#  auto=True 인 것만 원장 guard_violations 에 자동 기록한다.
#  나머지는 오검출이 잘못된 학습 신호가 되므로 비운다.
GUARDS = [
    ("G1", "짠 레인이 자기 코드를 보안 리뷰하지 않는다", True),
    ("G2", "자기 결론 재검증에 서브에이전트를 쓰지 않는다 — 반증은 리포트 '§X 반증 시도' 섹션", False),
    ("G3", "워커당 spawn 상한 8", True),
    ("G4", "쿼터 게이트는 디스패치 시점에만. 실행 중 중단 근거로 쓰지 않는다", False),
    ("G5", "쿼터는 4벤더 각각 확인한다", True),
    ("G6", "부재 보고에는 탐색 범위를 붙인다. 범위 없는 '0건'은 반환값 불인정 — "
           "gemini 뿐 아니라 **A 클래스 전체**에 적용 (Simon 결정 2026-09-04)", False),
    ("G7", "최상위 effort 는 반증질문 YES 인 태스크에만", False),
    ("G8", "쓰기 라운드는 **워커 강제종료 절차가 선 상태에서만** 띄운다 — "
           "`python scripts/kill_worker.py --dispatch <ctx_…>` (기본은 목록만, "
           "`--kill --fence` 로 트리 종료 → 재스캔 0 확인 → worker-stop). "
           "worker-stop 은 프로세스 사망을 약속하지 않는다. "
           "원래 문구 '문서화 전까지 착수 금지'는 2026-09-13 문서화·실측 1회로 충족 — "
           "SKILL.md '워커 강제종료 (G8)'", False),
    ("G9", "Move-Item 배치는 매니페스트 + 역방향 스크립트 선행", False),
    ("G10", "적대적 평가에서 채점자는 두 생산자와 **벤더가 달라야** 한다. "
            "벤더 3개를 못 채우면 그 문제는 건너뛴다 — 자기 벤더가 자기 답을 "
            "채점하느니 관측을 포기한다 (`adversarial_eval.py`)", False),
    ("G11", "디스패치 전에 툴체인 최신화를 확인한다 — codex 가 한 버전만 뒤처져도 "
            "`Agent startup blocked: codex-update-prompt` 로 **전 워커가 안 뜨는데 "
            "에러가 프롬프트 문제처럼 보인다** (2026-09-12 실사고). "
            "`python scripts/check_tooling.py`", False),
    ("G12", "**벤더 가용성은 쿼터로 판정하지 않는다 — 실호출로 확인한다.** "
            "2026-09-13 실측: grok 은 402(잔액 소진), gemini 단독 CLI 는 "
            "IneligibleTierError 였는데 **쿼터 %로는 둘 다 여유 있어 보였다** — "
            "못 쓰는 이유가 쿼터가 아니었기 때문이다. 쿼터 게이트(G5)는 "
            "'얼마나 썼나'를 보고, 이건 '지금 답이 나오나'를 본다. 다른 질문이다. "
            "`python scripts/adversarial_eval.py --preflight`", False),
]
AUTO_GUARDS = [g for g in GUARDS if g[2]]

SPAWN_CAP = 8            # G3
QUOTA_DEMOTE = 60        # §8 초과 → 2순위 강등
QUOTA_BLOCK = 85         # §8 초과 → 사용 금지
SWAP_MIN_OBS = 5         # §12 양쪽 관측 최소
SWAP_MIN_GAP = 0.15      # §12 채택률 15%p


# ── 조회 API ────────────────────────────────────────────────────
def lanes_for(cls):
    """클래스의 레인 우선순위 목록."""
    return list(CLASS_LANES.get(cls, []))


def fixed_for(proc_id):
    """고정 배정이면 (lane, effort), 아니면 None."""
    p = PROC_BY_ID.get(proc_id)
    return p[3] if p else None


def effort_for(lane, falsifiable):
    """발주 §5: effort 는 클래스가 아니라 태스크 속성(반증가능성)으로 정한다."""
    m = LANES.get(lane)
    if not m:
        raise KeyError(f"unknown lane: {lane}")
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


def validate_effort(lane, effort, allow_off_ladder=False):
    """effort 가 이 레인에서 쓸 수 있는 값인지 본다. 아니면 ValueError.

    기본은 정책 두 단(top/std)만 허용한다 — 발주 C3·G7 의 규율이다.
    allow_off_ladder=True 면 Orca 실측 목록까지 넓힌다(상황에 맞게 올리거나 내릴 때).
    어느 쪽이든 **Orca 가 거부하는 값은 절대 통과하지 않는다** —
    astra/daybreak 에 ultra·max 를 주면 워커가 뜨지 않고 invalid_argument 만 난다.
    """
    if lane in FORBIDDEN_LANES:
        raise ValueError(f"배정 금지 레인 (발주 §3): {_safe(lane)}")
    m = LANES.get(lane)
    if not m:
        raise ValueError(f"unknown lane: {_safe(lane)}")
    physical = set(orca_efforts_for(lane))
    policy = {m["top"], m["std"]}
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
                  allow_off_ladder=False):
    """디스패치 커맨드를 '배열'로 만든다.

    발주 C3: effort 가 반드시 박히도록 코드에서 강제한다 (sol 기본 low 함정).
    발주 S3: shell=True 금지 · 문자열 연결 금지 — 호출자는 이 배열을 그대로 쓴다.

    allow_off_ladder=True 면 정책 두 단 밖의 값도 쓸 수 있다 —
    단 Orca 실측 허용목록 안에서만이다 (validate_effort 참조).
    """
    m = LANES.get(lane)
    if not m:
        raise ValueError(f"unknown lane: {_safe(lane)}")
    validate_effort(lane, effort, allow_off_ladder=allow_off_ladder)

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
            f"{lane} 는 오르카 워커로 기동할 수 없다 (agent 미등록, 2026-09-04 실측). "
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
                 spec=None, timeout=600, dry=False, allow_off_ladder=False):
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
                         allow_off_ladder=allow_off_ladder)
    final_spec = build_spec(lane, effort, spec)
    meta = {"spec": final_spec, "spec_sha": spec_digest(final_spec),
            "prompt_prefix": prompt_prefix(lane, effort),
            "off_ladder": effort not in set(ladder_for(lane))}
    if dry:
        return 0, json.dumps({"argv": argv, **meta}, ensure_ascii=False), "", meta
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=timeout)          # shell=False 가 기본이다
        return p.returncode, (p.stdout or "").strip(), _redact((p.stderr or "").strip()), meta
    except subprocess.TimeoutExpired:
        return 1, "", f"timeout {timeout}s", meta
    except Exception as e:
        return 1, "", type(e).__name__, meta


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


def run_orca(*args, timeout=120):
    """orca 호출의 **유일한 실행 경로**.

    감사 HIGH-C (2026-09-04 재검증): dispatch wrapper 만 고쳤더니
    run-create/task-create/gate-create/worktree set 예시가 여전히 자유 문자열을
    셸 큰따옴표에 넣고 있었다. `$(...)`·`;`·백틱이 orca 보다 먼저 실행된다.
    builder 만 주면 호출자가 다시 문자열로 합치므로, 실행·timeout·returncode·
    redaction 까지 여기서 강제한다.

    objective·spec·comment·question 같은 자유 문자열을 그냥 인자로 넘기면 된다.
    셸을 거치지 않으므로 인용이 필요 없다.

    반환: (returncode, stdout, stderr) — stderr 는 redact 된다.
    """
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
    rc, out, err = run_orca(*args, "--json", timeout=timeout)
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
    if effort not in CODEX_DIRECT_EFFORTS:
        raise ValueError(f"codex effort 는 {list(CODEX_DIRECT_EFFORTS)} 중 하나여야 한다 "
                         f"(받은 값: {_safe(effort)})")
    argv = ["codex", "exec", "-m", str(model),
            "-c", f'model_reasoning_effort="{effort}"',
            "-c", f'sandbox_mode="{sandbox}"']
    if not cwd_check:
        argv.append("--skip-git-repo-check")
    argv.append("-")
    return argv


def run_codex_exec(prompt, model="gpt-6-astra", effort="ultra",
                   sandbox="read-only", cwd=None, timeout=1800, dry=False):
    """codex 직행 실행. 반환 (returncode, stdout, stderr).

    기본을 read-only 로 둔 이유: 이 경로에는 워크트리 격리가 없다.
    쓰기가 필요하면 워커로 띄우는 것이 맞다 — sandbox 를 올리기 전에 그걸 먼저 검토할 것.
    """
    argv = codex_exec_argv(model, effort, sandbox=sandbox, cwd_check=False)
    if dry:
        return 0, json.dumps({"argv": argv, "prompt_sha": spec_digest(prompt)},
                             ensure_ascii=False), ""
    try:
        p = subprocess.run(argv, input=prompt or "", capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           cwd=cwd, timeout=timeout)      # shell=False
    except subprocess.TimeoutExpired:
        return 1, "", f"timeout {timeout}s"
    except Exception as e:
        return 1, "", type(e).__name__
    return p.returncode, (p.stdout or "").strip(), _redact((p.stderr or "").strip())


# ── Orca effort 허용목록 실측 (비용 0) ──────────────────────────
def probe_orca_efforts(task_id, agent, model, efforts=None,
                       bad_worktree="name:zzz-nonexistent-probe"):
    """워커를 띄우지 않고 Orca 의 effort 허용목록을 읽는다.

    원리(2026-09-06 실측): worker-start 의 검증 순서가
      consumer fence → task 존재 → **effort** → worktree 셀렉터 → 실제 기동
    이다. 그래서 '존재하지 않는 worktree 이름'을 같이 주면
      · effort 가 거부되면  invalid_argument "does not support effort X"
      · effort 가 통과하면  selector_not_found
    로 갈린다. 어느 쪽이든 워커는 뜨지 않으므로 **비용이 0** 이다.

    task_id 는 실재하는 태스크여야 한다(없으면 task_not_found 로 먼저 잘린다).

    ⚠ 모델 슬러그 자체는 Orca 가 검증하지 않는다(MODEL_ID_UNVALIDATED).
      오타 난 슬러그도 low·medium·high·xhigh 는 '통과'로 나온다.
      이 함수는 effort 만 재는 자다 — 모델 존재 확인에 쓰지 말 것.

    반환: {effort: True(허용) | False(거부) | None(판정 불가)}
    """
    if efforts is None:
        efforts = ["low", "medium", "high", "xhigh", "max", "ultra"]
    out = {}
    for ef in efforts:
        args = ["orchestration", "worker-start", "--task", str(task_id),
                "--worktree", bad_worktree, "--agent", str(agent)]
        if model:
            args += ["--model", str(model)]
        args += ["--effort", str(ef)]
        rc, so, se = run_orca(*args, "--json", timeout=120)
        try:
            d = json.loads(so)
        except Exception:
            out[ef] = None
            continue
        err = d.get("error") or {}
        msg = err.get("message", "")
        if "does not support effort" in msg:
            out[ef] = False
        elif err.get("code") == "selector_not_found":
            out[ef] = True
        elif d.get("ok"):
            # 여기 오면 안 된다 — bad_worktree 가 실재하는 이름이라는 뜻이다.
            out[ef] = "SPAWNED"
        else:
            out[ef] = None
    return out


def prompt_prefix(lane, effort):
    """프롬프트 첫 줄에 넣어야 하는 키워드 (없으면 빈 문자열)."""
    m = LANES[lane]
    if m["effort_style"] == "prompt-keyword" and effort == m["top"]:
        return "ultracode"
    return ""


# ── 가드 자동 검출 (발주 §7 — 이 4개만) ─────────────────────────
def check_guards(assignments, quota_checked_vendors=None, spawn_counts=None):
    """자동 검출 가능한 가드만 본다. 반환: 위반 코드 리스트.

    assignments: [{"proc": <proc_id>, "lane": <lane>, "explore": bool}, ...]
    quota_checked_vendors: 디스패치 전 실제로 쿼터를 읽은 벤더 집합
    spawn_counts: {worker_name: spawn 수}
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
    impl = {LANES[a["lane"]]["vendor"] for a in assignments
            if a.get("proc") == "coding" and a.get("lane") in LANES}
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
    sec_lanes = {a["proc"]: a["lane"] for a in assignments
                 if a.get("proc", "").startswith("security-")}
    if len(sec_lanes) == 2:
        if len(set(sec_lanes.values())) < 2:
            v.append("G1_SEC_SAME_MODEL")

    # G3 — spawn 상한
    if spawn_counts:
        if any(c > SPAWN_CAP for c in spawn_counts.values()):
            v.append("G3")

    # G5 — 4벤더 쿼터 미확인 상태로 디스패치
    if quota_checked_vendors is not None:
        used = {LANES[a["lane"]]["vendor"] for a in assignments if a.get("lane") in LANES}
        if used - set(quota_checked_vendors):
            v.append("G5")

    # 탐색 슬롯이 D·보안에 배정
    for a in assignments:
        if a.get("explore") and a.get("proc") in EXPLORE_EXCLUDE:
            v.append("EXPLORE_MISASSIGNED")
            break

    return sorted(set(v))


def validate_plan(assignments, quota_checked_vendors=None, spawn_counts=None):
    """디스패치 전 계획 전체를 검증한다. 반환 (ok, violations, notes).

    감사 MED (재검증): check_guards() 는 list 만 돌려주고 run_dispatch() 가
    이를 요구하지 않아서, 호출자가 보안 배정을 목록에서 빼거나 아예 호출하지
    않으면 G1/G3/G5 를 전부 우회할 수 있었다. coding 1개만 주고
    quota_checked_vendors=['claude'] 로 부르면 위반이 [] 로 나왔다.
    → 필수 게이트 존재와 4벤더 전체 쿼터를 여기서 강제한다.
    """
    v = list(check_guards(assignments, quota_checked_vendors, spawn_counts))
    notes = []

    procs = {a.get("proc") for a in assignments}
    if "coding" in procs:
        for need in ("security-artifact-gate", "security-bizlogic-2nd"):
            if need not in procs:
                v.append("MISSING_SECURITY_GATE")
                notes.append(f"코딩이 있는 라운드에 {need} 가 없다")

    # G5 는 '4벤더 각각' 이다 — 쓰는 벤더만 확인하는 것으로는 부족하다
    if quota_checked_vendors is not None:
        missing = set(VENDORS) - set(quota_checked_vendors)
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
        fixed = fixed_for(a.get("proc"))
        if fixed and lane and lane != fixed[0]:
            v.append("FIXED_LANE_OVERRIDDEN")
            notes.append(f"{a.get('proc')} 는 {fixed[0]} 고정인데 {lane} 로 배정됨")

        # 명시 effort 는 여기서 미리 검증한다 — 디스패치 루프 중간에 터지면
        # 앞의 워커는 이미 떠 있고 뒤는 안 뜬 반쪽 상태가 된다.
        if lane in LANES and a.get("effort"):
            try:
                validate_effort(lane, a["effort"],
                                allow_off_ladder=bool(a.get("off_ladder")))
            except ValueError as e:
                v.append("EFFORT_NOT_ALLOWED")
                notes.append(f"{a.get('proc')}: {e}")

    return (not v), sorted(set(v)), notes


def validate_and_dispatch(assignments, task_of, worktree,
                          quota_checked_vendors=None, spawn_counts=None,
                          spec_of=None, dry=False):
    """계획 검증을 통과해야만 디스패치한다. 위반이 있으면 아무것도 실행하지 않는다.

    task_of / spec_of: proc_id -> task_id / spec 을 주는 dict 또는 callable.
    반환 (ok, results, violations, notes)
    """
    ok, v, notes = validate_plan(assignments, quota_checked_vendors, spawn_counts)
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
        elif fixed:
            effort = fixed[1]
        else:
            effort = effort_for(lane, a.get("falsifiable", False))
        rc, out, err, meta = run_dispatch(
            lane, effort, _get(task_of, proc), a.get("name") or proc, worktree,
            spec=_get(spec_of, proc), dry=dry,
            allow_off_ladder=bool(a.get("off_ladder")))
        results.append({"proc": proc, "lane": lane, "effort": effort,
                        "rc": rc, "out": out, "err": err, **meta})
        if rc != 0 and not dry:
            notes.append(f"{proc} 디스패치 실패(rc={rc}) — 나머지를 중단한다")
            return False, results, v, notes
    return True, results, v, notes


def coordinator_conflict(assignments):
    """코디네이터(sol)가 B 워커를 겸하면 경고 (발주 §5)."""
    return any(a.get("lane") == COORDINATOR[0] and a.get("class") == "B"
               for a in assignments)


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
            "unavailable": "❌ **agent 미등록 — 워커 불가**"}
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
        L.append(f"| `{lane}` | {m['cli']} | `{m['top']}` | `{m['std']}` | {phys} | {style} "
                 f"| {disp[m.get('dispatch', 'orca')]} | {m['ctx']} |")
    L.append("")
    L.append("**「Orca 실측 허용」은 2026-09-06 에 전수 측정한 값이다** — `python scripts/routing.py "
             "--probe-efforts --task <실재 task_id>` 로 언제든 다시 잰다(워커가 안 뜨므로 비용 0). "
             "`models_cache.json` 이 지원한다고 적는 값과 **다르다**: astra·daybreak 은 CLI 에서는 "
             "`ultra`·`max` 가 돌지만 Orca 워커로는 `xhigh` 가 상한이다. "
             "정책 두 단(최상위/표준) 밖의 값을 쓰려면 `allow_off_ladder=True` 를 명시한다.")
    L.append("")
    L.append("⚠ **Orca 는 `--model` 문자열을 검증하지 않는다** — 존재하지 않는 슬러그도 "
             "`high`·`xhigh` 면 통과하고, 워커가 뜬 뒤 codex 가 죽는다. "
             "이 표의 레인 키가 사실상 유일한 오타 방어선이다.")
    L.append("")
    L.append("**오르카 기동은 2026-09-04 실측이다.** `--model` 은 Claude·Codex·Cursor 만 받는다 "
             "(orca help) — grok·gemini 는 `--agent` 만 주고 모델은 그 CLI 의 기본값이 쓰인다. "
             "⚠ **agent id 는 CLI 이름이 아니라 좌석 이름이다**: `--agent agy` 는 "
             "`agent_unconfigured` 로 거부되고 `--agent antigravity` 가 정본이다. "
             "(CLI 바이너리는 `agy`, Orca 등록명은 `antigravity`.)")
    L.append("")
    L.append(f"**배정 금지**: {' · '.join('`'+x+'`' for x in sorted(FORBIDDEN_LANES))} "
             "— 용도 미검증 / R&R 미확정 (발주 §3)")
    L.append("")
    L.append("### 공정 → 클래스 → 레인")
    L.append("")
    L.append("| 공정 | 클래스 | 1순위 | 2순위 | 3후보 |")
    L.append("|---|---|---|---|---|")
    for pid, cls, label, fixed in PROCESSES:
        lanes = lanes_for(cls)
        if fixed:
            cells = [f"**`{fixed[0]}` @{fixed[1]} 고정**", "—", "—"]
        else:
            cells = [f"`{l}`" for l in lanes[:3]] + ["—"] * (3 - len(lanes[:3]))
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
    L.append("셋째 줄이 **물리적 상한**이다. 둘째 줄까지가 기본 경로고, 셋째 줄까지는 "
             "`allow_off_ladder=True` 를 명시해야 열린다 — 원장에 `off_ladder` 로 남는다. "
             "그 위(`ultra`·`max` on astra/daybreak)는 Orca 가 거부하므로 **없는 값**이다. "
             "거기가 정말 필요하면 워커가 아니라 codex 직행이다 (`run_codex_exec`).")
    L.append("")
    L.append(f"코디네이터 레인 = **`{COORDINATOR[0]}` @{COORDINATOR[1]}** — 종합(D)과 벤더가 달라야 한다.")
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
    L.append(f"쿼터: {QUOTA_DEMOTE}% 초과 → 2순위 강등 · {QUOTA_BLOCK}% 초과 → 사용 금지 · "
             "읽기 실패 = **미확인**(0%로 간주 금지)")
    L.append("")
    L.append("<!-- ROUTING:END -->")
    return "\n".join(L)


def _cli_probe(argv):
    """--probe-efforts --task <task_id> [--lane <lane>] — Orca 허용목록 재측정."""
    if "--task" not in argv:
        print("사용법: routing.py --probe-efforts --task <실재 task_id> [--lane <lane>]")
        print("  · task 는 이 터미널에 바인딩된 Run 의 실재 태스크여야 한다")
        print("    (orca orchestration run-create → task-create 로 하나 만들면 된다)")
        print("  · 워커는 뜨지 않는다. 비용 0.")
        return 2
    task = argv[argv.index("--task") + 1]
    only = argv[argv.index("--lane") + 1] if "--lane" in argv else None
    targets = [only] if only else list(LANES)
    print(f"task={task} · 워커를 띄우지 않고 effort 허용목록만 읽는다\n")
    for lane in targets:
        m = LANES[lane]
        if m.get("dispatch") != "orca":
            # --effort 는 --model 을 요구하는데 이 레인들은 --model 자체를 거부한다.
            # 즉 Orca 로는 effort 를 지정할 방법이 없다 — 그 CLI 의 기본값이 쓰인다.
            print(f"{lane:26s} N/A — Orca 가 --model 을 거부하는 레인(효력 있는 effort 지정 불가)")
            continue
        model = slug_for(lane, m["std"])
        res = probe_orca_efforts(task, m["cli"], model)
        cells = " ".join(f"{k}={'O' if v is True else 'X' if v is False else str(v)}"
                         for k, v in res.items())
        measured = {k for k, v in res.items() if v is True}
        if m["effort_style"] == "prompt-keyword":
            # claude 의 top/std 는 프롬프트 키워드 라벨이고 와이어 값은 항상 max 다.
            # 비교 대상은 표가 아니라 '와이어 값이 아직 살아 있는가' 하나뿐이다.
            mark = "와이어 max 유효" if "max" in measured else "⚠ 와이어 max 가 거부된다"
        else:
            declared = set(orca_efforts_for(lane))
            mark = ("일치" if declared == measured
                    else f"⚠ 불일치 표={sorted(declared)} 실측={sorted(measured)}")
        print(f"{lane:26s} {cells}   [{mark}]")
    return 0


if __name__ == "__main__":
    if "--probe-efforts" in sys.argv:
        raise SystemExit(_cli_probe(sys.argv))
    if "--emit-md" in sys.argv:
        print(emit_md())
    elif "--json" in sys.argv:
        print(json.dumps({
            "lanes": LANES, "class_lanes": CLASS_LANES,
            "processes": [{"id": p[0], "class": p[1], "label": p[2],
                           "fixed": list(p[3]) if p[3] else None} for p in PROCESSES],
            "coordinator": list(COORDINATOR),
            "forbidden": sorted(FORBIDDEN_LANES),
            "ceilings": {l: ceiling_for(l) for l in LANES},
            "codex_direct_efforts": list(CODEX_DIRECT_EFFORTS),
        }, ensure_ascii=False, indent=2))
    else:
        print(f"레인 {len(LANES)} · 공정 {len(PROCESSES)} · 클래스 {len(CLASS_LANES)}")
        for l in LANES:
            print(f"  {l:26s} 정책 {LANES[l]['std']}/{LANES[l]['top']:9s} "
                  f"Orca 상한 {ceiling_for(l)}")
        print("--emit-md 로 SKILL.md 표를, --json 으로 기계 판독본을 낸다")
        print("--probe-efforts --task <id> 로 Orca 허용목록을 다시 잰다 (비용 0)")
