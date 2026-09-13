# aggregate_ledger.py — /vibe v2.1 원장 집계 · 스왑 제안
#
# 발주 §12 : 산술만 한다. 판단 로직을 넣지 않는다.
#            집계 키는 반드시 (class, lane, effort). task 로 집계하지 않는다.
#            제안은 출력만. 표를 자동 수정하지 않는다 (발주 §14).
#            관측이 부족하면 "관측 부족(n=N, 필요 5)"을 명시 출력한다. 침묵 금지.
# 사용: python aggregate_ledger.py [--json]
import json
import os
import statistics
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import routing            # noqa: E402
import ledger             # noqa: E402

# Windows 콘솔 기본이 cp949 라 em-dash 하나로 스크립트가 죽는다 (실측 2026-09-04).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass



def aggregate(records):
    """(class, lane, effort) → 지표. explore 관측은 분리 집계한다."""
    buckets = {}
    for r in records:
        key = (r.get("class"), r.get("lane"), r.get("effort"))
        if None in key:
            continue
        b = buckets.setdefault(key, {
            "n": 0, "n_explore": 0, "items": 0, "accepted": 0,
            "items_x": 0, "accepted_x": 0,
            "secs": [], "fail": 0, "retries": 0, "rated": 0,
        })
        exp = bool(r.get("explore"))
        b["n"] += 1
        if exp:
            b["n_explore"] += 1
        it, ac = int(r.get("items") or 0), int(r.get("accepted") or 0)
        if it > 0:
            b["rated"] += 1
            if exp:
                b["items_x"] += it
                b["accepted_x"] += ac
            else:
                b["items"] += it
                b["accepted"] += ac
        if r.get("status") not in ("done", "ok", "success"):
            b["fail"] += 1
        b["retries"] += int(r.get("retries") or 0)
        if r.get("sec"):
            b["secs"].append(int(r["sec"]))
    return buckets


def _rate(acc, items):
    return (acc / items) if items else None


def rows(buckets):
    out = []
    for (cls, lane, eff), b in sorted(buckets.items()):
        out.append({
            "class": cls, "lane": lane, "effort": eff,
            "n": b["n"], "n_explore": b["n_explore"],
            "accept": _rate(b["accepted"], b["items"]),
            "accept_explore": _rate(b["accepted_x"], b["items_x"]),
            "rated": b["rated"],
            "median_sec": int(statistics.median(b["secs"])) if b["secs"] else None,
            "fail_rate": b["fail"] / b["n"] if b["n"] else None,
            "retry_rate": b["retries"] / b["n"] if b["n"] else None,
        })
    return out


def swap_proposals(buckets):
    """§12 — 같은 클래스에서 2순위 채택률이 1순위보다 15%p 이상 높고
    양쪽 관측이 각 5회 이상이면 '제안'한다. 자동 반영은 하지 않는다."""
    props, shortfalls = [], []
    for cls, lanes in routing.CLASS_LANES.items():
        if len(lanes) < 2:
            continue
        first, second = lanes[0], lanes[1]

        def gather(lane):
            """감사 MED: 표본 수를 전체 n 으로 세면 items=0 인 미평가 행만 늘려도
            n>=5 스왑 게이트를 넘길 수 있다. **평가된 행(rated)** 만 센다."""
            rated = items = acc = 0
            for (c, l, _e), b in buckets.items():
                if c == cls and l == lane:
                    rated += b["rated"]
                    items += b["items"] + b["items_x"]
                    acc += b["accepted"] + b["accepted_x"]
            return rated, items, acc

        n1, i1, a1 = gather(first)
        n2, i2, a2 = gather(second)
        r1, r2 = _rate(a1, i1), _rate(a2, i2)

        if n1 < routing.SWAP_MIN_OBS or n2 < routing.SWAP_MIN_OBS:
            shortfalls.append(
                f"{cls}: 관측 부족(1순위 {first} rated={n1}, 2순위 {second} rated={n2}, "
                f"필요 {routing.SWAP_MIN_OBS}) — 채택률이 회수된 라운드만 센다")
            continue
        if r1 is None or r2 is None:
            shortfalls.append(
                f"{cls}: 채택률 미회수(items=0) — 결정 시트 [결과 저장]이 안 돌아왔다")
            continue
        if r2 - r1 >= routing.SWAP_MIN_GAP:
            props.append({
                "class": cls, "from": first, "to": second,
                "rate_first": round(r1, 3), "rate_second": round(r2, 3),
                "gap_pp": round((r2 - r1) * 100, 1), "n_first": n1, "n_second": n2,
            })
    return props, shortfalls


def main():
    recs, broken = ledger.read_ledger()
    buckets = aggregate(recs)
    table = rows(buckets)
    props, shortfalls = swap_proposals(buckets)
    unmerged = ledger.unmerged_runs()

    if "--json" in sys.argv:
        print(json.dumps({"rows": table, "proposals": props,
                          "shortfalls": shortfalls, "unmerged_runs": unmerged,
                          "recovery_state": ledger.run_recovery_state(),
                          "records": len(recs), "broken_lines": broken},
                         ensure_ascii=False, indent=2))
        return

    print(f"원장: {ledger.LEDGER}")
    print(f"레코드 {len(recs)}개" + (f" · 깨진 줄 {broken}" if broken else ""))
    print()

    if not table:
        # C10 — 빈 원장에서 에러 없이 돌고 침묵하지 않는다
        print("관측 없음 — 집계할 레코드가 하나도 없다.")
        print(f"관측 부족(n=0, 필요 {routing.SWAP_MIN_OBS}) — 스왑 판정 불가.")
        print("라운드를 돌리면 /vibe 실행 마지막 단계에서 자동으로 쌓인다.")
        return

    hdr = f"{'클래스':<12}{'레인':<20}{'effort':<10}{'n':>4}{'탐색':>5}{'채택률':>8}{'탐색채택':>9}{'중위초':>7}{'실패율':>7}{'재시도':>7}"
    print(hdr)
    print("-" * len(hdr))
    for r in table:
        def pct(x):
            return f"{x*100:.0f}%" if x is not None else "  —"
        print(f"{r['class']:<12}{r['lane']:<20}{r['effort']:<10}{r['n']:>4}{r['n_explore']:>5}"
              f"{pct(r['accept']):>8}{pct(r['accept_explore']):>9}"
              f"{(r['median_sec'] if r['median_sec'] is not None else '—'):>7}"
              f"{pct(r['fail_rate']):>7}{r['retry_rate']:>7.2f}")
    print()

    # 상태를 가른다 — "라운드가 실패했다"와 "내가 절차를 건너뛰었다"는 처방이 다르다.
    states = ledger.run_recovery_state()
    groups = {}
    for run, (st, why) in states.items():
        if st != "recovered":
            groups.setdefault(st, []).append((run, why))
    LABEL = {
        "no-sheet": ("⛔ 시트를 안 만든 run", "진짜 학습 정지다. "
                     "make_decision_sheet.py 로 만들어야 decisions_run_*.json 이 나온다 — "
                     "손으로 조립한 시트는 회수 경로가 없다"),
        "sheet-pending": ("⚠ 회수 대기 run", "시트는 있다. [결과 저장] 한 번이면 다음 /vibe 가 집는다"),
        "no-output": ("· 산출물 0건 run", "워커가 죽은 라운드다. 채택할 항목이 없으니 "
                      "학습 정지가 아니다 — 고칠 곳은 디스패치·타임아웃 쪽"),
    }
    for st in ("no-sheet", "sheet-pending", "no-output"):
        if st not in groups:
            continue
        head, tip = LABEL[st]
        print(f"{head} {len(groups[st])}개: {[r for r, _w in groups[st]][:5]}")
        print(f"  {tip}")
        for run, why in groups[st][:5]:
            print(f"    {run}  {why}")
        print()

    # MED-59: effort 별 채택률은 어느 행이 크레딧을 받았는지에 좌우된다.
    # 시트는 (run, lane) 총계만 알므로 lane 수준 집계를 함께 보여준다.
    by_lane = {}
    for r in table:
        k = (r["class"], r["lane"])
        b = by_lane.setdefault(k, {"n": 0, "rated": 0, "acc": 0, "items": 0})
        b["n"] += r["n"]
        b["rated"] += r["rated"]
    for (cls, lane), b in sorted(by_lane.items()):
        pass
    print("── 레인 수준 채택률 (effort 귀속과 무관한 값) ──")
    agg = {}
    for (c, l, _e), bb in buckets.items():
        k = (c, l)
        a = agg.setdefault(k, {"items": 0, "acc": 0, "rated": 0, "n": 0})
        a["items"] += bb["items"] + bb["items_x"]
        a["acc"] += bb["accepted"] + bb["accepted_x"]
        a["rated"] += bb["rated"]
        a["n"] += bb["n"]
    for (c, l), a in sorted(agg.items()):
        rate = f"{a['acc'] / a['items'] * 100:.0f}%" if a["items"] else "  —"
        print(f"  {c:<12}{l:<20} n={a['n']:<3} rated={a['rated']:<3} 채택률={rate}")
    print()

    print("── 스왑 제안 (제안만 한다. 표는 Simon 이 폼에서 승인한다) ──")
    if props:
        for p in props:
            print(f"  {p['class']}: {p['from']} → {p['to']} "
                  f"(채택률 {p['rate_first']:.0%} → {p['rate_second']:.0%}, "
                  f"+{p['gap_pp']}%p, n={p['n_first']}/{p['n_second']})")
    else:
        print("  제안 없음")
    for s in shortfalls:
        print(f"  · {s}")


if __name__ == "__main__":
    main()
