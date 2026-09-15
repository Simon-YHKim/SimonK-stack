# make_intake.py — /vibe v2.1 인테이크 폼 생성기
#
# v2.0 대비 바뀐 것:
#   C4 · 4벤더(claude/codex/gemini/grok) 쿼터를 각각 읽고 "미확인"을 0%와 구분한다
#   C5 · 클래스별 기본 레인이 미리 채워지고, 미선택 시 그대로 진행된다
#   C6 · 반증질문(예/아니오)과 탐색 슬롯 표시가 폼에 있다
#   §10· 실행 때마다 decisions_run_*.json 을 자동 회수하고, 미회수 3건 이상이면 경고한다
#   D-28 · 강등을 전 순위에 · quota_bucket(fable) · 실호출(G12) 반영 · unavailable 건너뛰기 · 코딩 전용 행 (2026-09-16)
#
# 라우팅 표는 scripts/routing.py 가 정본이다 — 여기서 다시 적지 않는다 (발주 §2).
# 사용: python make_intake.py [출력경로]
import datetime
import json
import os
import subprocess
import time
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import routing   # noqa: E402
import ledger    # noqa: E402
import ui        # noqa: E402

# Windows 콘솔 기본이 cp949 라 em-dash 하나로 스크립트가 죽는다 (실측 2026-09-04).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


DEFAULT_OUT = r"E:\Coding Infra\reports\vibe-intake.html"
esc = ui.esc


ORCA_ERR = {}          # 마지막 오류 종류를 보존한다 (감사 MED: fail-open 근거 표시)


def orca(args):
    """S3 — 인자 배열. 실패하면 None. 실패 '종류' 는 ORCA_ERR 에 남긴다."""
    key = " ".join(args)
    try:
        p = subprocess.run(["orca", *args, "--json"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=90)
        if p.returncode != 0:
            ORCA_ERR[key] = f"rc={p.returncode}"      # stderr 원문은 남기지 않는다(S1)
            return None
        return json.loads(p.stdout).get("result")
    except subprocess.TimeoutExpired:
        ORCA_ERR[key] = "timeout"
        return None
    except Exception as e:
        ORCA_ERR[key] = type(e).__name__
        return None


# ── 쿼터: 4벤더 각각 (C4) ───────────────────────────────────────
# orca account list 가 claude/codex/gemini/grok 를 모두 낸다 —
# agy·grok CLI 에는 비대화형 쿼터 명령이 없다(grok usage 는 TUI 를 띄운다).
# 벤더별로 구속력 있는 키가 다르다: gemini 는 weekly 가 비고 session/buckets 만 온다.
VENDOR_KEYS = {
    "claude": ["weekly", "session"],
    "codex":  ["weekly", "session"],
    "gemini": ["session", "buckets", "weekly"],
    "grok":   ["weekly", "session"],
}
VENDOR_LABEL = {"claude": "Claude", "codex": "Codex", "gemini": "Gemini (agy)", "grok": "Grok"}


def read_quota():
    """벤더별 {pct, reset, state}. 읽기 실패는 state='unknown' — 0%로 간주하지 않는다(§8).

    S1 — CLI 실패 메시지를 원문 그대로 남기지 않는다. 상태만 기록한다.
    """
    acc = orca(["account", "list"])
    rl = (acc or {}).get("rateLimits", {}) if acc else {}
    out = {}
    for v in routing.VENDORS:
        node = rl.get(v) or {}
        best, key = None, None
        for k in VENDOR_KEYS[v]:
            d = node.get(k)
            if isinstance(d, dict) and d.get("usedPercent") is not None:
                p = d["usedPercent"]
                if best is None or p > best:      # 가장 구속력 있는 값을 택한다
                    best, key = p, k
        if best is None:
            out[v] = {"pct": None, "reset": "", "state": "unknown", "key": ""}
        else:
            d = node.get(key) or {}
            out[v] = {"pct": int(best), "reset": d.get("resetDescription") or "",
                      "state": "ok", "key": key}
    # Fable 은 별도 표시 (claude 워커가 fable 로 떨어지는 것을 막기 위한 신호)
    fw = ((rl.get("claude") or {}).get("fableWeekly") or {}).get("usedPercent")
    return out, (int(fw) if fw is not None else None)


LIVE_PATH = os.path.join(os.path.dirname(_HERE), "state", "eval-vendors.json")
LIVE_STALE_SEC = 24 * 3600      # D-28 #13③ — 실호출 결과가 이보다 오래되면 미확인


def read_live(now=None):
    """G12 실호출 결과(adversarial_eval.py --preflight 가 쓴 state/eval-vendors.json).

    반환 {"at", "age_sec", "stale", "vendors": {vendor: True|False}}.
    파일이 없거나 깨지면 vendors 가 비고 stale=True — 막지 않고 '미확인'으로 표시한다.
    """
    now = time.time() if now is None else now
    try:
        with open(LIVE_PATH, encoding="utf-8") as fh:
            d = json.load(fh)
        age = now - float(d.get("at_epoch") or 0)
        vendors = {k: bool((v or {}).get("ok")) for k, v in (d.get("vendors") or {}).items()}
        return {"at": d.get("at"), "age_sec": age, "stale": age > LIVE_STALE_SEC, "vendors": vendors}
    except Exception:
        return {"at": None, "age_sec": None, "stale": True, "vendors": {}}


def lane_state(vendor, quota):
    """§8 — 80% 초과 강등 · 한도 100% 도달 금지(Q-05) · 미확인은 순위 유지."""
    q = quota.get(vendor) or {}
    if q.get("state") != "ok":
        return "unknown"
    p = q["pct"]
    if p >= routing.QUOTA_BLOCK:          # Q-05: 도달이 금지다(100%)
        return "blocked"
    if p > routing.QUOTA_DEMOTE:
        return "demote"
    return "ok"


def lane_state_for(lane, quota, fable_pct=None, live=None):
    """레인 단위 상태 (D-28 #12·#13). 반환 (state, 사유).

    ② quota_bucket 이 있는 레인(fable)은 벤더 주간값이 아니라 그 버킷으로 판정한다.
    ③ 실호출 실패는 쿼터와 무관하게 blocked. 결과가 오래됐으면 막지 않고 사유에 '미확인'.
    #12 dispatch == "unavailable" 은 기본 채움에서 건너뛴다(blocked).
    """
    m = routing.LANES[lane]
    if m.get("dispatch") == "unavailable":
        return "blocked", "Orca 워커 불가(dispatch=unavailable)"
    vendor = m["vendor"]
    if m.get("quota_bucket") == "fableWeekly":
        if fable_pct is None:
            st = "unknown"
        elif fable_pct >= routing.QUOTA_BLOCK:
            st = "blocked"
        elif fable_pct > routing.QUOTA_DEMOTE:
            st = "demote"
        else:
            st = "ok"
        why = f"fableWeekly {fable_pct}%" if fable_pct is not None else "fableWeekly 미확인"
        # D-28 M2 미확정(2026-09-16: 워커 2개로는 claude weekly 62→62 · fableWeekly 0→0 으로 정수 %가
        #   움직이지 않았다) — fableWeekly 가 claude 일반 한도와 독립인지 모르므로 둘 중 더 나쁜 상태로 판정한다.
        #   독립이 확인되면(M2) 이 블록을 지운다.
        vst = lane_state(vendor, quota)
        order = {"ok": 0, "unknown": 1, "demote": 2, "blocked": 3}
        if order.get(vst, 1) > order.get(st, 1):
            st = vst
            q = quota.get(vendor) or {}
            why += f" · {vendor} {q.get('pct')}% (M2 미확정 — 더 나쁜 쪽)"
    else:
        st = lane_state(vendor, quota)
        q = quota.get(vendor) or {}
        why = f"{vendor} {q['pct']}%" if q.get("state") == "ok" else f"{vendor} 쿼터 미확인"
    if live is not None:
        seen = live.get("vendors", {})
        if seen.get(vendor) is False:
            if not live.get("stale"):
                return "blocked", f"{vendor} 실호출 실패({live.get('at')})"
            why += f" · 실호출 실패 기록이 오래됨({live.get('at')}) — 미확인"
    return st, why


def pick_default(cls, quota, fable_pct=None, live=None, proc=None, falsifiable=False, writes=False):
    """C5 — 기본 레인. 반환 (lane, 메모).

    D-28 #13①: 강등(80% 초과, Q-05)을 **모든 순위**에 적용한다 — ok(또는 미확인) 레인이 있으면 그중 첫째,
    없으면 첫 강등 레인. 이전 판은 1순위만 건너뛰어 61% 인 2순위가 그대로 뽑혔고,
    전 레인이 강등·금지로 섞이면 None 을 돌려주는 버그가 있었다(D-28 N6).
    proc 을 주면 공정 단위 목록(PROCESS_LANES · R1 승격)을 쓴다.
    """
    lanes = (routing.lanes_for_proc(proc, cls, falsifiable, writes) if (proc or writes)
             else routing.lanes_for(cls))
    if not lanes:
        return None, ("모델 미사용 (orca CLI)" if cls == "N" else "레인 미정")
    first_demote = None
    skipped = []
    for lane in lanes:
        st, why = lane_state_for(lane, quota, fable_pct, live)
        if st in ("ok", "unknown"):
            note = "" if st == "ok" else "쿼터 미확인 — 순위 유지"
            if skipped:
                note = (note + " · " if note else "") + "건너뜀: " + ", ".join(skipped)
            return lane, note
        if st == "demote" and first_demote is None:
            first_demote = (lane, why)
        skipped.append(f"{lane}({why})")
    if first_demote:
        return first_demote[0], f"전 레인 강등선({routing.QUOTA_DEMOTE}%) 초과 — 첫 강등 레인 사용({first_demote[1]})"
    # 감사 MED: 전 후보가 blocked 인데 마지막 금지 lane 을 prefill 하면
    # 문서의 "사용 금지, 후보 없으면 축소안 승인" 과 정반대다. lane 을 주지 않는다.
    return None, "전 레인이 한도 도달·실호출 실패 — 실행 불가. 축소안 승인 필요"


def main(out_path=None, argv=None):
    """감사 MED: 이전 판은 실행부가 module top-level 에 있어서 **import 만으로**
    ledger.collect_decisions()(실제 Downloads 소비·Git commit)와
    open(sys.argv[1], "w")(임의 경로 truncate)가 일어났다.
    테스트가 함수 하나 import 하는 것만으로 실제 상태가 파괴될 수 있었다.
    → 모든 I/O 를 여기 안으로 넣고 출력 경로를 인자로 받는다.
    """
    argv = sys.argv if argv is None else argv
    OUT = out_path or (argv[1] if len(argv) > 1 else DEFAULT_OUT)
    if os.path.exists(OUT) and not OUT.lower().endswith(".html"):
        raise SystemExit("출력 경로가 .html 이 아니다 — 덮어쓰지 않는다")

    # ── 실행 때마다: 결정 시트 결과 회수 (§10) ──────────────────────
    merged_runs, merge_notes = ledger.collect_decisions()
    unmerged = ledger.unmerged_runs()

    quota, fable_pct = read_quota()
    repos = []
    rp = orca(["repo", "list"])
    if rp:
        prefer = ("2ndB", "SimonK-stack", "Communication", "SimonKWiki")
        seen = [(r.get("displayName", "?"), r.get("path", "")) for r in rp.get("repos", [])]
        repos = [x for x in seen if x[0] in prefer] + [x for x in seen if x[0] not in prefer]
        repos = repos[:12]
    if not repos:
        repos = [("2ndB", "E:/2ndB")]

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── 의도 축 ─────────────────────────────────────────────────────
    AXES = [
        {"id": "type", "label": "무엇을 만드나", "multi": True,
         "note": "복수 선택 — 고른 유형의 단계를 합쳐서 돈다",
         "opts": [("화면·UI", "새 화면이나 기존 화면 변경"),
                  ("백엔드·데이터", "API·DB·로직"),
                  ("버그 수정", "증상이 특정됨"),
                  ("전수 감사·조사", "코드 안 바꿈 — 병렬 조사 후 종합")]},
        {"id": "repo", "label": "어디에", "multi": True, "note": "복수 선택 가능",
         "opts": [(p, n) for n, p in repos], "swap": True},
        {"id": "depth", "label": "얼마나 깊게", "multi": False,
         "note": "하나만 — 워커 수 = 비용",
         "opts": [("가볍게", "워커 3개 내외"),
                  ("표준", "워커 5~6개"),
                  ("철저히", "워커 8개+ · 교차검증 다중")]},
        {"id": "falsify", "label": "반증할 전제가 있나", "multi": False,
         "note": "이 답이 effort 를 정한다 — 미응답은 아니오",
         "opts": [("예 — 무엇이 참인지 판정해야 한다",
                   "'X는 죽었다' 확인 · 'A가 B보다 낫다' 판정 · 원인 규명 → 최상위 effort"),
                  ("아니오 — 만들거나 모으면 된다", "표준 effort")]},
        {"id": "confirm", "label": "화면 확인", "multi": False, "note": "하나만",
         "opts": [("로컬호스트에서 내가 컨펌", "앱을 띄운 채 넘겨 오르카 탭에서 확인"),
                  ("불필요", "UI를 건드리지 않는 작업")]},
        {"id": "done", "label": "어디까지", "multi": False,
         "note": "하나만 — 머지는 언제나 Simon이 한다",
         "opts": [("로컬 확인만", "커밋 안 함"),
                  ("브랜치까지", "커밋·푸시, PR 없음"),
                  ("PR까지", "PR 생성, 머지는 안 함")]},
    ]

    OPTIONS = [
        ("dry", "먼저 계획만 보여줘 (비용 0)"),
        ("test", "테스트 필수"),
        ("design-system", "기존 디자인 시스템 엄격히 따를 것"),
        ("i18n", "i18n 키 누락 검사 포함"),
        ("no-newdep", "새 의존성 추가 금지"),
        ("no-explore", "탐색 슬롯 끄기 (이번 라운드는 학습보다 결과)"),
    ]

    MULTI_IDS = [a["id"] for a in AXES if a["multi"]]

    axes_html = []
    for ax in AXES:
        m = ax["multi"]
        state = 'aria-pressed="false"' if m else 'role="radio" aria-checked="false"'
        chips = []
        for a, b in ax["opts"]:
            val, big, small = (a, b, a) if ax.get("swap") else (a, a, b)
            chips.append(
                f'<button type="button" class="chip{" multi" if m else ""}" data-axis="{esc(ax["id"])}" '
                f'data-val="{esc(val)}" {state}><b>{esc(big)}</b>'
                f'{f"<i>{esc(small)}</i>" if small else ""}</button>')
        chips.append(
            f'<button type="button" class="chip dunno{" multi" if m else ""}" data-axis="{esc(ax["id"])}" '
            f'data-val="__auto__" {state}><b>모르겠음 — 네가 골라줘</b></button>')
        grp = 'role="group"' if m else 'role="radiogroup"'
        axes_html.append(
            f'<fieldset class="axis"><legend>{esc(ax["label"])} <span class="note">{esc(ax["note"])}</span></legend>'
            f'<div class="chips" {grp} aria-label="{esc(ax["label"])}">{"".join(chips)}</div></fieldset>')

    opts_html = "".join(
        f'<button type="button" class="chip multi" data-opt="{esc(k)}" aria-pressed="false">'
        f'<b>{esc(v)}</b></button>' for k, v in OPTIONS)

    # ── 쿼터 패널 (4벤더 · 미확인 구분) ─────────────────────────────
    qrows, qwarn = [], []
    for v in routing.VENDORS:
        q = quota[v]
        st = lane_state(v, quota)
        if q["state"] == "unknown":
            qrows.append(f'<div class="qrow"><span>{esc(VENDOR_LABEL[v])}</span>'
                         f'<div class="bar"></div><span class="qn">미확인</span></div>')
        else:
            tone = {"blocked": "사용 금지", "demote": "2순위 강등", "ok": ""}[st]
            qrows.append(
                f'<div class="qrow"><span>{esc(VENDOR_LABEL[v])}</span>'
                f'<div class="bar"><i style="width:{min(q["pct"],100)}%"></i></div>'
                f'<span class="qn">{q["pct"]}%{(" · " + esc(q["reset"])) if q["reset"] else ""}'
                f'{(" · " + tone) if tone else ""}</span></div>')
            if st == "blocked":
                qwarn.append(f"{VENDOR_LABEL[v]} {q['pct']}% — 사용 금지")
            elif st == "demote":
                qwarn.append(f"{VENDOR_LABEL[v]} {q['pct']}% — 2순위 강등")

    unknowns = [VENDOR_LABEL[v] for v in routing.VENDORS if quota[v]["state"] == "unknown"]
    if unknowns:
        qwarn.append("미확인: " + ", ".join(unknowns) + " (0%로 간주하지 않고 1순위 유지)")
    if fable_pct is not None and fable_pct >= 100:
        qwarn.append(f"Claude Fable 주간 {fable_pct}% — fable 을 워커로 쓰지 않는다")

    warn_html = (f'<p class="warn">⚠ {esc(" · ".join(qwarn))}</p>') if qwarn else ""
    quota_html = (f'<section class="quota"><h2>4벤더 쿼터 '
                  f'<span class="note">{esc(now)} 기준 · orca account list</span></h2>'
                  f'{"".join(qrows)}{warn_html}</section>')

    # ── 기본 레인 패널 (C5) ─────────────────────────────────────────
    defaults = {}
    drows = []
    live = read_live()
    for cls in ["A", "A-verify", "B", "C-realtime", "C-platform", "D"]:
        lane, note = pick_default(cls, quota, fable_pct, live)
        defaults[cls] = lane
        lanes = routing.lanes_for(cls)
        alt = " → ".join(f"<code>{esc(l)}</code>" for l in lanes) if lanes else "—"
        drows.append(
            f"<tr><td><b>{esc(cls)}</b><br><span class='note'>{esc(routing.CLASS_LABEL[cls])}</span></td>"
            f"<td><span class='tag lane'>{esc(lane or '—')}</span>"
            f"{f'<br><span class=\"note\">{esc(note)}</span>' if note else ''}</td>"
            f"<td class='note'>{alt}</td></tr>")

    # D-28 #5·#14 — 코딩은 공정 전용 목록. 게이트 벤더가 사용 금지면 코딩 라운드 불가.
    c_lane, c_note = pick_default("B", quota, fable_pct, live, proc="coding")
    gate_blocked = sorted(vd for vd in routing.gate_vendors()
                          if lane_state(vd, quota) == "blocked"
                          or (not live["stale"] and live["vendors"].get(vd) is False))
    if gate_blocked:
        c_note = (c_note + " · " if c_note else "") + \
            f"보안 게이트 벤더 {', '.join(gate_blocked)} 사용 금지 — 코딩 없는 라운드로 축소"
        c_lane = None
    defaults["coding"] = c_lane
    c_alt = " → ".join(f"<code>{esc(l)}</code>" for l in routing.lanes_for_proc("coding"))
    drows.append(
        "<tr><td><b>coding</b><br><span class='note'>공정 전용 목록 (D-28 #5)</span></td>"
        f"<td><span class='tag lane'>{esc(c_lane or '—')}</span>"
        + (f"<br><span class='note'>{esc(c_note)}</span>" if c_note else "")
        + f"</td><td class='note'>{c_alt} · codex 폴백 없음</td></tr>")
    live_note = ("실호출 결과 없음 — adversarial_eval.py --preflight 먼저" if live["at"] is None
                 else f"실호출 {live['at']}" + (" · 24시간 초과 — 미확인" if live["stale"] else ""))

    fixed_rows = "".join(
        f"<tr><td>{esc(p[2])}</td><td><span class='tag lane'>{esc(p[3][0])}</span> "
        f"<span class='tag'>@{esc(p[3][1])}</span></td><td class='note'>고정 · 탐색·스왑 제외</td></tr>"
        for p in routing.PROCESSES if p[3])

    default_html = (
        '<section class="quota"><h2>클래스별 기본 레인 '
        f'<span class="note">안 건드리면 이대로 간다 — 정본은 scripts/routing.py · {esc(live_note)}</span></h2>'
        '<table class="sum"><tr><th>클래스</th><th>기본</th><th>우선순위</th></tr>'
        + "".join(drows) + "</table>"
        '<h2 style="margin-top:14px">고정 배정 <span class="note">바뀌지 않는다</span></h2>'
        '<table class="sum"><tr><th>공정</th><th>레인</th><th></th></tr>' + fixed_rows + "</table>"
        f'<p class="note" style="margin-top:10px">코디네이터 = <code>{esc(routing.COORDINATOR[0])}</code> '
        f'@{esc(routing.COORDINATOR[1])} — 종합(D)과 벤더가 다르다.</p>'
        "</section>")

    # ── 탐색 슬롯 · 학습 상태 (C6 · §10) ────────────────────────────
    # D-28 #12·C2 — 2순위가 Orca 로 뜨고 실호출을 통과한 공정만 후보
    live_ok = None if live["stale"] else {vd for vd, ok in live["vendors"].items() if ok}
    explore_pool = [routing.PROC_BY_ID[pid][2] for pid in routing.explore_candidates(live_ok)]
    learn_warn = ""
    if len(unmerged) >= 3:
        learn_warn = (f'<p class="warn">⚠ 최근 {len(unmerged)}개 라운드의 채택률이 비어 있다 — '
                      f'학습 정지 상태. 결정 시트에서 [결과 저장]을 눌러야 한다.</p>')
    merged_note = (f'<p class="note">이번 실행에서 {len(merged_runs)}개 run 의 채택률을 회수했다: '
                   f'{esc(", ".join(merged_runs))}</p>') if merged_runs else ""

    explore_html = (
        '<section class="quota"><h2>탐색 슬롯 '
        '<span class="note">라운드당 1개를 2순위 레인으로 돌려 학습을 쌓는다</span></h2>'
        f'<p class="note">대상 후보(A 우선 · 고정·종합·보안·코딩 제외 · 2순위가 Orca 로 뜨고 실호출 통과한 공정만 — D-28 #12): {esc(" · ".join(explore_pool[:6]))}'
        f'{" 외" if len(explore_pool) > 6 else ""}<br>'
        '실제 선택은 후보 중 <b>무작위</b>다 — 항상 첫 태스크를 고르면 난이도 편향이 생긴다. '
        '끄려면 아래 추가 조건에서 "탐색 슬롯 끄기".</p>'
        f'<p class="note">원장 레코드 {len(ledger.read_ledger()[0])}개 · 채택률 미회수 run {len(unmerged)}개</p>'
        f"{merged_note}{learn_warn}</section>")

    body = (
        "<h1>/vibe — 무엇을 어떻게 만들까</h1>"
        '<p class="sub">고르면 아래에 프롬프트가 만들어진다. <strong>복사해서 Claude Code에 붙여넣으면</strong> '
        "그대로 실행된다. 체크박스 모양 칩은 <strong>여러 개 고를 수 있다.</strong> "
        "안 고른 축은 내가 판단하고 이유를 밝힌다.</p>"
        f"{quota_html}{default_html}{explore_html}"
        '<form id="f" onsubmit="return false">'
        f"{''.join(axes_html)}"
        '<fieldset class="axis"><legend>추가 조건 <span class="note">복수 선택</span></legend>'
        f'<div class="chips" role="group" aria-label="추가 조건">{opts_html}</div></fieldset>'
        '<fieldset class="axis"><legend>과제 <span class="note">한두 문장이면 충분하다</span></legend>'
        '<textarea id="task" placeholder="예) 설정 화면에 알림 토글 섹션을 추가하고, 값은 서버에 저장되게 해줘"></textarea>'
        "</fieldset></form>"
        '<section class="out"><h2>붙여넣을 프롬프트</h2>'
        '<pre id="prompt">과제를 적으면 여기에 만들어진다.</pre>'
        '<div class="row"><button class="act" id="copy">복사</button>'
        '<button class="act ghost" id="reset">초기화</button>'
        '<span class="status" id="st"></span></div>'
        '<div id="fb"><div class="status">클립보드가 막혀 있다. 아래를 직접 복사할 것.</div>'
        '<textarea id="fbt" readonly></textarea></div></section>')

    JS = """
    (function(){
    'use strict';
    var MULTI=__MULTI__;
    var LABEL={type:'유형',repo:'저장소',depth:'깊이',falsify:'반증 전제',confirm:'화면 확인',done:'완료 기준'};
    var ORDER=['type','repo','depth','falsify','confirm','done'];
    var OPTLABEL=__OPTLABEL__;
    var DEFAULTS=__DEFAULTS__;
    var QUOTA=__QUOTA__;
    var sel={},opts={};
    function all(s){return Array.prototype.slice.call(document.querySelectorAll(s));}
    function paint(a){
      var cur=sel[a];
      all('.chip[data-axis="'+a+'"]').forEach(function(o){
        var v=o.getAttribute('data-val'),on;
        if(MULTI[a]){on=(cur||[]).indexOf(v)>=0;o.setAttribute('aria-pressed',on?'true':'false');}
        else{on=(cur===v);o.setAttribute('aria-checked',on?'true':'false');}
      });
    }
    all('.chip[data-axis]').forEach(function(c){
      c.addEventListener('click',function(){
        var a=c.getAttribute('data-axis'),v=c.getAttribute('data-val');
        if(MULTI[a]){
          var arr=sel[a]||[];
          if(v==='__auto__'){arr=(arr.indexOf('__auto__')>=0)?[]:['__auto__'];}
          else{arr=arr.filter(function(x){return x!=='__auto__';});
            var i=arr.indexOf(v);if(i>=0){arr.splice(i,1);}else{arr.push(v);}}
          sel[a]=arr;
        }else{sel[a]=(sel[a]===v)?undefined:v;}
        paint(a);build();
      });
    });
    all('.chip[data-opt]').forEach(function(c){
      c.addEventListener('click',function(){
        var k=c.getAttribute('data-opt');opts[k]=!opts[k];
        c.setAttribute('aria-pressed',opts[k]?'true':'false');build();
      });
    });
    document.getElementById('task').addEventListener('input',build);
    function build(){
      var task=document.getElementById('task').value.trim();
      var L=['/vibe 실행',''];
      L.push('과제: '+(task||'(아직 안 적음)'));
      var auto=[];
      ORDER.forEach(function(k){
        var v=sel[k];
        if(MULTI[k]){
          var arr=(v||[]).filter(function(x){return x!=='__auto__';});
          if(!arr.length){auto.push(LABEL[k]);return;}
          L.push(LABEL[k]+': '+arr.join(' + '));
        }else{
          if(!v||v==='__auto__'){auto.push(LABEL[k]);return;}
          L.push(LABEL[k]+': '+v);
        }
      });
      var on=Object.keys(opts).filter(function(k){return opts[k];});
      if(on.length){L.push('추가 조건: '+on.map(function(k){return OPTLABEL[k];}).join(' · '));}
      if(auto.length){L.push('');L.push('안 고른 축('+auto.join(', ')+')은 네가 판단하고 이유를 밝혀줘.');}
      L.push('');
      L.push('── 라우팅 (v2.2 · 정본 = scripts/routing.py) ──');
      L.push('기본 레인: '+Object.keys(DEFAULTS).map(function(c){return c+'='+DEFAULTS[c];}).join(' · '));
      L.push('쿼터: '+QUOTA);
      L.push('');
      L.push('vibe 스킬대로 진행할 것:');
      L.push('1) 프리플라이트 — 4벤더 쿼터 각각 확인(미확인은 0%로 간주 금지)');
      L.push('2) 공정을 클래스(A/A-verify/B/C/D/N)로 분류하고 클래스별 레인을 배정 — 판정이 섞인 대조는 A-verify(읽기 전용)');
      L.push('3) 태스크마다 반증질문 예/아니오를 정하고 그에 따라 effort 를 고른다(미응답=아니오)');
      L.push('4) 디스패치는 routing.validate_and_dispatch() 로만 — 계획 검증을 통과해야 실행된다');
  L.push('   (effort 누락·금지 레인·필수 게이트 부재·4벤더 쿼터 미확인을 코드가 막는다)');
      L.push('   재시도(--retry-of)·수동 재배정 전에는 routing.revalidate_for_retry() 로 다시 검증(G13)');
      L.push('5) 탐색 슬롯 1개를 routing.explore_candidates() 후보 중 무작위로 2순위 레인에 배정(explore:true)');
      L.push('6) 보안 2종은 서로 다른 모델(__SECFIXED__ — D-260904-01)');
      L.push('   코딩은 PROCESS_LANES["coding"](claude 전용)만 — 게이트 벤더가 사용 금지면 코딩을 빼고 축소안(D-28 #5·#14)');
      L.push('   effort 는 Orca 실측 허용목록 안에서만 — astra·daybreak 은 xhigh 가 상한이고');
      L.push('   ultra/max 는 codex 직행(run_codex_exec)으로만 닿는다. 정책 밖 값은 off_ladder 명시');
      L.push('7) worker_done 수확·release → 보드 갱신');
      L.push('8) 결정 시트 생성(make_decision_sheet.py) → Simon 이 [결과 저장] — 이 단계 없이 라운드 종료 금지(G14)');
      L.push('9) 마지막에 원장 append+commit(ledger.py) — 데몬 만들지 말 것');
      L.push('착수 전 분류 결과·예상 워커 수·탐색 슬롯이 뭔지 한 줄로 알릴 것.');
      document.getElementById('prompt').textContent=L.join('\\n');
    }
    function fallback(t){document.getElementById('fb').style.display='block';
      var e=document.getElementById('fbt');e.value=t;e.focus();e.select();}
    function legacy(t){try{var a=document.createElement('textarea');a.value=t;a.style.position='fixed';
      a.style.opacity='0';document.body.appendChild(a);a.select();var ok=document.execCommand('copy');
      document.body.removeChild(a);return ok;}catch(e){return false;}}
    document.getElementById('copy').addEventListener('click',function(){
      var t=document.getElementById('prompt').textContent;
      var done=function(){document.getElementById('st').textContent='복사됨 — Claude Code에 붙여넣으면 시작한다';};
      if(navigator.clipboard&&navigator.clipboard.writeText){
        navigator.clipboard.writeText(t).then(done).catch(function(){if(legacy(t)){done();}else{fallback(t);}});
      }else if(legacy(t)){done();}else{fallback(t);}
    });
    document.getElementById('reset').addEventListener('click',function(){
      sel={};opts={};
      all('.chip').forEach(function(c){
        if(c.hasAttribute('aria-pressed')){c.setAttribute('aria-pressed','false');}
        if(c.hasAttribute('aria-checked')){c.setAttribute('aria-checked','false');}
      });
      document.getElementById('task').value='';
      document.getElementById('st').textContent='';document.getElementById('fb').style.display='none';
      build();
    });
    build();
    })();
    """

    qsummary = " · ".join(
        f"{VENDOR_LABEL[v]} " + ("미확인" if quota[v]["state"] == "unknown" else f"{quota[v]['pct']}%")
        for v in routing.VENDORS)

    # 보안 2종 고정 배정은 routing 정본에서 읽는다 — 여기 손으로 적으면 곧 어긋난다
    # (실제로 어긋나 있었다: 표는 daybreak@xhigh 인데 이 줄은 sol@ultra 였다).
    _sec = " / ".join(
        f"{routing.fixed_for(p)[0]}@{routing.fixed_for(p)[1]}"
        for p in ("security-artifact-gate", "security-bizlogic-2nd"))
    _sec_vendors = sorted({routing.LANES[routing.fixed_for(p)[0]]["vendor"]
                           for p in ("security-artifact-gate", "security-bizlogic-2nd")})
    secfixed = f"{_sec}, 벤더 {'·'.join(_sec_vendors)}"

    JS = (JS.replace("__SECFIXED__", secfixed)
            .replace("__MULTI__", json.dumps({k: True for k in MULTI_IDS}, ensure_ascii=False))
            .replace("__OPTLABEL__", json.dumps(dict(OPTIONS), ensure_ascii=False))
            .replace("__DEFAULTS__", json.dumps(defaults, ensure_ascii=False))
            .replace("__QUOTA__", json.dumps(qsummary, ensure_ascii=False)))

    DOC = ui.page("/vibe — 무엇을 어떻게 만들까", body, JS)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(DOC)

    print(OUT)
    print(f"쿼터 {qsummary}")
    print(f"기본 레인 {defaults}")
    print(f"저장소 {len(repos)}개 · 원장 {len(ledger.read_ledger()[0])}레코드 · "
          f"미회수 run {len(unmerged)} · {round(len(DOC.encode('utf-8'))/1024,1)}KB")
    for n in merge_notes:
        print("  회수:", n)
    if qwarn:
        print("WARN: " + " · ".join(qwarn))


if __name__ == "__main__":
    main()
