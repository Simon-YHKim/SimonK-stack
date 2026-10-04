#!/usr/bin/env python3
"""Cohort retention diagnostics. Stdlib only — no pandas/numpy.

Three deterministic sub-commands:

  curve    Cohort retention triangle -> retained %, retention floor, cohort
           comparison at a fixed period. Marks immature (right-censored) cells NA.
             input CSV columns: cohort,period_number,cohort_size,retained
             python retention_calc.py curve --input cohorts.csv [--floor-window 2]

  rfm      Recency/Frequency/(Monetary) quintile scoring -> segment per user.
             input CSV columns: user_id,recency_days,frequency[,monetary]
             python retention_calc.py rfm --input users.csv

  drivers  Leading churn indicators: compares behavior of retained vs churned
           users, ranks each behavior by retained-association (lift + point-biserial r).
             input CSV columns: user_id,retained,<behavior_1>,<behavior_2>,...
               retained = 1 (stayed) / 0 (churned); behaviors are numeric counts.
             python retention_calc.py drivers --input behavior.csv

All math is closed-form (no RNG, no network). Lower period_number = closer to signup.
"""
import argparse
import csv
import math
import sys
from collections import defaultdict


# --------------------------------------------------------------------------
# shared CSV loading
# --------------------------------------------------------------------------
def _read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            sys.exit("ERROR: empty CSV (no header row).")
        rows = [dict(r) for r in reader]
    if not rows:
        sys.exit("ERROR: CSV has a header but no data rows.")
    return rows, reader.fieldnames


def _require(fieldnames, needed, cmd):
    missing = [c for c in needed if c not in fieldnames]
    if missing:
        sys.exit(f"ERROR ({cmd}): missing required column(s): {', '.join(missing)}\n"
                 f"       found columns: {', '.join(fieldnames)}")


# --------------------------------------------------------------------------
# curve
# --------------------------------------------------------------------------
def run_curve(args):
    rows, fns = _read_rows(args.input)
    _require(fns, ["cohort", "period_number", "cohort_size", "retained"], "curve")

    # triangle[cohort][period] = retained count ; size[cohort] = cohort_size
    triangle = defaultdict(dict)
    size = {}
    max_period = 0
    for r in rows:
        c = r["cohort"].strip()
        try:
            p = int(r["period_number"])
            n = int(r["cohort_size"])
            ret = int(r["retained"])
        except ValueError:
            sys.exit(f"ERROR (curve): non-integer value in row: {r}")
        triangle[c][p] = ret
        size[c] = n
        max_period = max(max_period, p)

    # cohorts ordered (string sort works for ISO-ish labels: 2026-05-W1 etc.)
    cohorts = sorted(triangle.keys())

    # A cell is "immature" (right-censored) if the cohort never reports any
    # period >= p. The deepest period a cohort actually reached:
    reached = {c: max(triangle[c].keys()) for c in cohorts}

    print("=== Cohort retention triangle (bracket: retained on/after period N) ===")
    header = "cohort".ljust(14) + " size  " + "".join(f"  P{p:<5}" for p in range(max_period + 1))
    print(header)
    for c in cohorts:
        line = c.ljust(14) + f"{size[c]:>5}  "
        for p in range(max_period + 1):
            if p in triangle[c]:
                pct = triangle[c][p] / size[c] if size[c] else 0.0
                line += f" {pct*100:5.1f}%"
            elif p > reached[c]:
                line += "    NA "          # immature / not yet lived this long
            else:
                line += "   0.0%"          # genuinely zero retained in a reached period
        print(line)

    # retention floor: mean retention over the last `floor-window` MATURE periods
    # per cohort, then averaged across cohorts that reached that depth.
    w = args.floor_window
    floor_vals = []
    for c in cohorts:
        deep = sorted(p for p in triangle[c] if p > 0)[-w:]
        if len(deep) < w:
            continue
        vals = [triangle[c][p] / size[c] for p in deep if size[c]]
        if vals:
            floor_vals.append(sum(vals) / len(vals))
    print()
    if floor_vals:
        floor = sum(floor_vals) / len(floor_vals)
        print(f"Retention floor (mean of last {w} mature periods, "
              f"{len(floor_vals)} cohort(s)): {floor*100:.1f}%")
        if floor < 0.10:
            print("  WARNING: floor < 10%. Curve trending toward zero -> weak/no PMF signal.")
        else:
            print("  Floor is above zero -> a retained core exists (PMF-positive signal).")
    else:
        print("Retention floor: NOT ENOUGH MATURE PERIODS to estimate. "
              "Let cohorts age, or reduce --floor-window.")

    # cohort comparison at the deepest period reached by ALL cohorts (fair compare)
    common_depth = min(reached[c] for c in cohorts) if cohorts else 0
    if common_depth >= 1:
        print(f"\n=== Cohort comparison at P{common_depth} (deepest fully-comparable period) ===")
        series = []
        for c in cohorts:
            pct = triangle[c].get(common_depth, 0) / size[c] if size[c] else 0.0
            series.append((c, pct))
            print(f"  {c.ljust(14)} {pct*100:5.1f}%  (n={size[c]})")
        first, last = series[0][1], series[-1][1]
        if first > 0:
            trend = (last - first) / first
            arrow = "improving" if trend > 0.03 else ("declining" if trend < -0.03 else "flat")
            print(f"  Trend oldest->newest cohort: {trend*100:+.1f}% ({arrow})")
    else:
        print("\nCohort comparison: cohorts too young to compare (need >= P1).")

    # immaturity / size warnings
    small = [c for c in cohorts if size[c] < args.min_cohort]
    if small:
        print(f"\nWARNING: cohort(s) below {args.min_cohort} users (noisy %): "
              f"{', '.join(small)}. Consider bucketing wider (week->month).")
    return 0


# --------------------------------------------------------------------------
# rfm
# --------------------------------------------------------------------------
def _quintile_scores(values, reverse):
    """Map each value to 1..5 by quintile. reverse=True -> smaller value scores higher
    (used for recency: fewer days since last seen = better = score 5)."""
    if not values:
        return {}
    ordered = sorted(set(values))
    # cut points at 20/40/60/80 percentiles of the sorted distinct values
    def pct_value(p):
        idx = min(len(ordered) - 1, int(p * (len(ordered) - 1) + 0.5))
        return ordered[idx]
    cuts = [pct_value(p) for p in (0.2, 0.4, 0.6, 0.8)]

    def score(v):
        s = 1
        for c in cuts:
            if v > c:
                s += 1
        return s  # 1..5, higher v -> higher score
    mapping = {v: score(v) for v in set(values)}
    if reverse:
        mapping = {v: 6 - s for v, s in mapping.items()}  # invert: lower v -> 5
    return mapping


def _segment(r_score, f_score):
    if r_score >= 4 and f_score >= 4:
        return "Champions"
    if f_score >= 4 and r_score >= 2:
        return "Loyal"
    if r_score >= 4 and f_score <= 2:
        return "New"            # recent but not yet frequent
    if r_score <= 2 and f_score >= 3:
        return "At-risk"        # was active, gone quiet
    if r_score <= 2 and f_score <= 2:
        return "Hibernating"
    return "Promising"


def run_rfm(args):
    rows, fns = _read_rows(args.input)
    _require(fns, ["user_id", "recency_days", "frequency"], "rfm")
    has_m = "monetary" in fns

    users = []
    for r in rows:
        try:
            rec = float(r["recency_days"])
            freq = float(r["frequency"])
            mon = float(r["monetary"]) if has_m and r.get("monetary", "") != "" else None
        except ValueError:
            sys.exit(f"ERROR (rfm): non-numeric value in row: {r}")
        users.append((r["user_id"], rec, freq, mon))

    r_map = _quintile_scores([u[1] for u in users], reverse=True)   # recency: lower=better
    f_map = _quintile_scores([u[2] for u in users], reverse=False)
    m_map = (_quintile_scores([u[3] for u in users if u[3] is not None], reverse=False)
             if has_m else {})

    seg_counts = defaultdict(int)
    out = []
    for uid, rec, freq, mon in users:
        rs, fs = r_map[rec], f_map[freq]
        ms = m_map.get(mon) if (has_m and mon is not None) else None
        seg = _segment(rs, fs)
        seg_counts[seg] += 1
        out.append((uid, rs, fs, ms, seg))

    print("=== RFM segments ===")
    print(f"Scored {len(users)} users  (R reversed: fewer days = higher score)"
          + ("  [+Monetary]" if has_m else "  [R/F only]"))
    total = len(users)
    order = ["Champions", "Loyal", "Promising", "New", "At-risk", "Hibernating"]
    for seg in order:
        c = seg_counts.get(seg, 0)
        if c:
            print(f"  {seg.ljust(12)} {c:>6}  ({c/total*100:4.1f}%)")
    rx = {seg: c for seg, c in seg_counts.items() if seg not in order}
    for seg, c in rx.items():
        print(f"  {seg.ljust(12)} {c:>6}  ({c/total*100:4.1f}%)")

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            wcsv = csv.writer(f)
            wcsv.writerow(["user_id", "R", "F", "M", "segment"])
            for row in out:
                wcsv.writerow([row[0], row[1], row[2],
                               "" if row[3] is None else row[3], row[4]])
        print(f"\nPer-user scores written to {args.out}")
    print("\nNOTE: segments are quantile-relative to THIS dataset. Re-score per cohort/period; "
          "do not hardcode thresholds.")
    return 0


# --------------------------------------------------------------------------
# drivers
# --------------------------------------------------------------------------
def run_drivers(args):
    rows, fns = _read_rows(args.input)
    _require(fns, ["user_id", "retained"], "drivers")
    behavior_cols = [c for c in fns if c not in ("user_id", "retained")]
    if not behavior_cols:
        sys.exit("ERROR (drivers): no behavior columns found (need at least one "
                 "numeric column besides user_id, retained).")

    retained_flags = []
    behaviors = {c: [] for c in behavior_cols}
    for r in rows:
        try:
            ret = int(float(r["retained"]))
        except ValueError:
            sys.exit(f"ERROR (drivers): retained must be 0/1, got {r['retained']!r}")
        if ret not in (0, 1):
            sys.exit(f"ERROR (drivers): retained must be 0 or 1, got {ret}")
        retained_flags.append(ret)
        for c in behavior_cols:
            try:
                behaviors[c].append(float(r[c]) if r.get(c, "") != "" else 0.0)
            except ValueError:
                sys.exit(f"ERROR (drivers): behavior '{c}' must be numeric, got {r[c]!r}")

    n = len(retained_flags)
    n_ret = sum(retained_flags)
    n_chu = n - n_ret
    if n_ret == 0 or n_chu == 0:
        sys.exit("ERROR (drivers): need both retained (1) and churned (0) users to compare.")

    print(f"=== Leading indicators: retained ({n_ret}) vs churned ({n_chu}) ===")
    print("Ranked by retained-association. Higher lift = behavior more common in retained.\n")
    print("behavior".ljust(24) + "ret_mean   chu_mean    lift   point-biserial r")

    p = n_ret / n
    sd_y = math.sqrt(p * (1 - p))  # sd of the binary outcome

    results = []
    for c in behavior_cols:
        vals = behaviors[c]
        ret_vals = [v for v, f in zip(vals, retained_flags) if f == 1]
        chu_vals = [v for v, f in zip(vals, retained_flags) if f == 0]
        m_ret = sum(ret_vals) / n_ret
        m_chu = sum(chu_vals) / n_chu
        lift = (m_ret / m_chu) if m_chu > 0 else (float("inf") if m_ret > 0 else 1.0)

        # point-biserial correlation between behavior value and retained flag
        mean_x = sum(vals) / n
        var_x = sum((v - mean_x) ** 2 for v in vals) / n
        sd_x = math.sqrt(var_x)
        if sd_x > 0 and sd_y > 0:
            cov = sum((v - mean_x) * (f - p) for v, f in zip(vals, retained_flags)) / n
            r_pb = cov / (sd_x * sd_y)
        else:
            r_pb = 0.0
        results.append((c, m_ret, m_chu, lift, r_pb))

    results.sort(key=lambda t: abs(t[4]), reverse=True)
    for c, m_ret, m_chu, lift, r_pb in results:
        lift_s = "inf" if lift == float("inf") else f"{lift:4.2f}x"
        print(f"{c[:23].ljust(24)}{m_ret:8.2f}  {m_chu:8.2f}   {lift_s:>6}   {r_pb:+.3f}")

    top = results[0]
    print(f"\nTop lever candidate: '{top[0]}' "
          f"(retained do {top[1]:.2f} vs churned {top[2]:.2f}, r={top[4]:+.3f}).")
    print("NOTE: correlation, NOT causation. Treat the top lever as an experiment "
          "HYPOTHESIS -> validate with experiment-analyzer before adopting as a goal.")
    return 0


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Cohort retention diagnostics (stdlib only)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    cv = sub.add_parser("curve", help="cohort retention triangle + floor + comparison")
    cv.add_argument("--input", required=True, help="CSV: cohort,period_number,cohort_size,retained")
    cv.add_argument("--floor-window", type=int, default=2,
                    help="# of last mature periods to average for the floor (default 2)")
    cv.add_argument("--min-cohort", type=int, default=100,
                    help="warn below this cohort size (default 100)")

    rf = sub.add_parser("rfm", help="RFM quintile segmentation")
    rf.add_argument("--input", required=True,
                    help="CSV: user_id,recency_days,frequency[,monetary]")
    rf.add_argument("--out", help="optional path to write per-user R/F/M/segment CSV")

    dr = sub.add_parser("drivers", help="leading churn indicators (retained vs churned)")
    dr.add_argument("--input", required=True,
                    help="CSV: user_id,retained,<behavior_1>,<behavior_2>,...")

    args = ap.parse_args()
    if args.cmd == "curve":
        return run_curve(args)
    if args.cmd == "rfm":
        return run_rfm(args)
    return run_drivers(args)


if __name__ == "__main__":
    raise SystemExit(main())
