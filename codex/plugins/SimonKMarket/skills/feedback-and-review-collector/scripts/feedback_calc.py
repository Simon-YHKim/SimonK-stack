#!/usr/bin/env python3
"""In-app feedback score calculator. Stdlib only — no pandas/numpy.

Four deterministic sub-commands. All math is closed-form (no RNG, no network,
no LLM). Same input -> same output.

  nps      Net Promoter Score from 0-10 responses.
             %Promoter(9-10) - %Detractor(0-6). Passive(7-8) excluded.
             input CSV columns: respondent_id,score[,verbatim,segment]
             python feedback_calc.py nps --input nps.csv

  csat     Customer Satisfaction = top-box ratio (NOT the mean).
             scale 1-5 -> top box = {4,5} ; scale 1-7 -> top box = {6,7}.
             input CSV columns: respondent_id,score[,verbatim,segment]
             python feedback_calc.py csat --input csat.csv --scale 5

  ces      Customer Effort Score on a 1-7 scale (1=very hard, 7=very easy).
             reports mean + "easy" ratio (5-7). Higher = lower effort = better.
             input CSV columns: respondent_id,score[,verbatim,segment]
             python feedback_calc.py ces --input ces.csv

  themes   Verbatim theme clustering: deterministic keyword + sentiment match.
             buckets free-text into known themes, ranks by frequency & sentiment.
             input CSV columns: respondent_id,verbatim[,score,segment]
             python feedback_calc.py themes --input nps.csv

Sample-size guard: any metric with n < 100 is flagged low-confidence; an
approximate 95% margin of error is printed so a swing is not over-read.
"""
import argparse
import csv
import math
import sys
from collections import defaultdict

# Korean Windows consoles default to cp949; force UTF-8 so EN/KO output and the
# em-dash never raise UnicodeEncodeError. No-op on already-UTF-8 terminals.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


# --------------------------------------------------------------------------
# shared CSV loading
# --------------------------------------------------------------------------
def _read_rows(path):
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                sys.exit("ERROR: empty CSV (no header row).")
            rows = [dict(r) for r in reader]
    except FileNotFoundError:
        sys.exit(f"ERROR: file not found: {path}")
    if not rows:
        sys.exit("ERROR: CSV has a header but no data rows.")
    return rows, [c.strip() for c in reader.fieldnames]


def _require(fieldnames, needed, cmd):
    missing = [c for c in needed if c not in fieldnames]
    if missing:
        sys.exit(f"ERROR ({cmd}): missing required column(s): {', '.join(missing)}\n"
                 f"       found columns: {', '.join(fieldnames)}")


def _parse_scores(rows, lo, hi, cmd):
    """Parse integer scores, dropping blanks; bail on out-of-range/non-numeric."""
    scores = []
    for i, r in enumerate(rows, start=2):  # row 1 is the header
        raw = (r.get("score") or "").strip()
        if raw == "":
            continue
        try:
            s = int(float(raw))
        except ValueError:
            sys.exit(f"ERROR ({cmd}): non-numeric score {raw!r} at CSV row {i}.")
        if not (lo <= s <= hi):
            sys.exit(f"ERROR ({cmd}): score {s} at CSV row {i} outside "
                     f"expected range {lo}-{hi}.")
        scores.append(s)
    if not scores:
        sys.exit(f"ERROR ({cmd}): no usable score values found.")
    return scores


def _pct(part, whole):
    return 0.0 if whole == 0 else 100.0 * part / whole


def _moe_proportion(p_fraction, n):
    """Approximate 95% margin of error for a proportion (Wald), in pct points."""
    if n == 0:
        return 0.0
    return 100.0 * 1.96 * math.sqrt(max(p_fraction * (1 - p_fraction), 0.0) / n)


def _sample_warning(n):
    if n < 100:
        print(f"  [WARN] n={n} < 100 — low confidence. Read as a trend, not a "
              f"precise number.")
    elif n < 300:
        print(f"  [note] n={n} — moderate sample; margins still meaningful.")


# --------------------------------------------------------------------------
# nps
# --------------------------------------------------------------------------
def run_nps(args):
    rows, fns = _read_rows(args.input)
    _require(fns, ["score"], "nps")
    scores = _parse_scores(rows, 0, 10, "nps")
    n = len(scores)

    promoters = sum(1 for s in scores if s >= 9)
    passives = sum(1 for s in scores if 7 <= s <= 8)
    detractors = sum(1 for s in scores if s <= 6)

    p_pct = _pct(promoters, n)
    d_pct = _pct(detractors, n)
    nps = p_pct - d_pct
    # NPS = difference of two proportions; combine their variances.
    se = 100.0 * math.sqrt(
        ((promoters / n) * (1 - promoters / n)
         + (detractors / n) * (1 - detractors / n)) / n
    )
    moe = 1.96 * se

    print("== NPS ==")
    print(f"  responses (n)   : {n}")
    print(f"  Promoters (9-10): {promoters:>5}  ({p_pct:5.1f}%)")
    print(f"  Passives  (7-8) : {passives:>5}  ({_pct(passives, n):5.1f}%)")
    print(f"  Detractors(0-6) : {detractors:>5}  ({d_pct:5.1f}%)")
    print(f"  NPS             : {nps:+.1f}   (range -100..+100, not a percentage)")
    print(f"  95% MoE         : +/- {moe:.1f}")
    _sample_warning(n)
    print("  NOTE: NPS is a score, not a %. Detractors should route to a private "
          "feedback form, never to the store review sheet.")


# --------------------------------------------------------------------------
# csat
# --------------------------------------------------------------------------
def run_csat(args):
    rows, fns = _read_rows(args.input)
    _require(fns, ["score"], "csat")
    scale = args.scale
    if scale not in (5, 7):
        sys.exit("ERROR (csat): --scale must be 5 or 7.")
    scores = _parse_scores(rows, 1, scale, "csat")
    n = len(scores)

    top_box = {5: {4, 5}, 7: {6, 7}}[scale]
    bottom_box = {5: {1, 2}, 7: {1, 2}}[scale]
    satisfied = sum(1 for s in scores if s in top_box)
    dissatisfied = sum(1 for s in scores if s in bottom_box)

    sat_pct = _pct(satisfied, n)
    moe = _moe_proportion(satisfied / n, n)

    print(f"== CSAT (scale 1-{scale}) ==")
    print(f"  responses (n)        : {n}")
    print(f"  top-box {sorted(top_box)} satisfied : {satisfied}  ({sat_pct:.1f}%)")
    print(f"  bottom-box {sorted(bottom_box)} unhappy  : {dissatisfied}  "
          f"({_pct(dissatisfied, n):.1f}%)")
    print(f"  CSAT (top-box ratio) : {sat_pct:.1f}%   95% MoE +/- {moe:.1f}")
    _sample_warning(n)
    print("  NOTE: report the top-box ratio, NOT the mean (the mean hides the "
          "distribution).")


# --------------------------------------------------------------------------
# ces
# --------------------------------------------------------------------------
def run_ces(args):
    rows, fns = _read_rows(args.input)
    _require(fns, ["score"], "ces")
    scores = _parse_scores(rows, 1, 7, "ces")
    n = len(scores)
    mean = sum(scores) / n
    easy = sum(1 for s in scores if s >= 5)       # 5-7 = low effort
    hard = sum(1 for s in scores if s <= 3)        # 1-3 = high effort
    easy_pct = _pct(easy, n)

    print("== CES (scale 1-7, 7 = very easy) ==")
    print(f"  responses (n)   : {n}")
    print(f"  mean effort     : {mean:.2f}  (higher = easier = better)")
    print(f"  easy (5-7)      : {easy}  ({easy_pct:.1f}%)")
    print(f"  hard (1-3)      : {hard}  ({_pct(hard, n):.1f}%)")
    _sample_warning(n)
    print("  NOTE: high-effort (1-3) clusters mark friction worth a CES drill-down "
          "or a CES verbatim theme pass.")


# --------------------------------------------------------------------------
# themes — deterministic keyword/sentiment clustering of verbatims
# --------------------------------------------------------------------------
# Theme -> keyword stems (EN + KO). Pure substring match, lowercased.
THEME_KEYWORDS = {
    "performance/speed": ["slow", "lag", "freeze", "crash", "load", "느리", "버벅",
                          "멈춰", "튕", "로딩", "끊"],
    "usability/ux":      ["confus", "complic", "hard to", "where is", "복잡", "어렵",
                          "헷갈", "못찾", "불편"],
    "pricing/value":     ["expensive", "price", "cost", "pay", "worth", "비싸",
                          "가격", "요금", "결제", "환불"],
    "bugs/errors":       ["bug", "error", "broken", "doesn't work", "wont", "버그",
                          "오류", "에러", "안돼", "안 돼", "작동"],
    "missing-feature":   ["wish", "should add", "feature", "need", "would love",
                          "있으면", "추가", "기능", "없어"],
    "content/quality":   ["inaccur", "wrong", "quality", "outdated", "정확", "틀린",
                          "품질", "오래된"],
    "praise":            ["love", "great", "awesome", "amazing", "perfect", "best",
                          "최고", "좋아", "훌륭", "만족", "편리"],
}
POSITIVE_WORDS = ["love", "great", "awesome", "amazing", "perfect", "best", "good",
                  "nice", "최고", "좋", "훌륭", "만족", "편리", "추천"]
NEGATIVE_WORDS = ["hate", "bad", "worst", "terrible", "awful", "annoying", "slow",
                  "crash", "bug", "error", "싫", "별로", "최악", "느리", "불편",
                  "버그", "오류", "안돼"]


def _sentiment(text):
    t = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)
    if pos > neg:
        return "+"
    if neg > pos:
        return "-"
    return "0"


def run_themes(args):
    rows, fns = _read_rows(args.input)
    _require(fns, ["verbatim"], "themes")

    counts = defaultdict(int)
    sentiments = defaultdict(lambda: {"+": 0, "-": 0, "0": 0})
    total_with_text = 0
    uncategorized = 0

    for r in rows:
        text = (r.get("verbatim") or "").strip()
        if not text:
            continue
        total_with_text += 1
        low = text.lower()
        matched = False
        senti = _sentiment(text)
        for theme, kws in THEME_KEYWORDS.items():
            if any(kw in low for kw in kws):
                counts[theme] += 1
                sentiments[theme][senti] += 1
                matched = True
        if not matched:
            uncategorized += 1

    if total_with_text == 0:
        sys.exit("ERROR (themes): no non-empty verbatim text found.")

    print("== Verbatim themes (deterministic keyword + sentiment) ==")
    print(f"  verbatims with text : {total_with_text}")
    print(f"  uncategorized       : {uncategorized}  "
          f"({_pct(uncategorized, total_with_text):.1f}%)")
    print("  (a verbatim can hit multiple themes)\n")

    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    if not ranked:
        print("  no known themes matched — review verbatims manually.")
    print(f"  {'theme':<20} {'hits':>5} {'share':>7}   sentiment(+/0/-)")
    print(f"  {'-'*20} {'-'*5} {'-'*7}   {'-'*16}")
    for theme, c in ranked:
        s = sentiments[theme]
        print(f"  {theme:<20} {c:>5} {_pct(c, total_with_text):>6.1f}%   "
              f"{s['+']:>3} / {s['0']:>2} / {s['-']:>3}")

    print("\n  HYPOTHESIS HINTS (not conclusions — verify via experiment-analyzer):")
    for theme, c in ranked[:3]:
        s = sentiments[theme]
        if theme == "praise":
            print(f"   - '{theme}' ({c}) — candidate for review-prompt timing "
                  f"(these are your satisfied users).")
        elif s["-"] >= s["+"]:
            print(f"   - Reducing '{theme}' friction (neg-leaning, {c} hits) may "
                  f"lift CSAT — frame as a testable hypothesis.")


# --------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(
        description="In-app feedback score calculator (NPS/CSAT/CES/themes). "
                    "Stdlib only, deterministic.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("nps", help="Net Promoter Score (0-10).")
    sp.add_argument("--input", required=True)
    sp.set_defaults(func=run_nps)

    sp = sub.add_parser("csat", help="CSAT top-box ratio.")
    sp.add_argument("--input", required=True)
    sp.add_argument("--scale", type=int, default=5, help="5 or 7 (default 5).")
    sp.set_defaults(func=run_csat)

    sp = sub.add_parser("ces", help="Customer Effort Score (1-7).")
    sp.add_argument("--input", required=True)
    sp.set_defaults(func=run_ces)

    sp = sub.add_parser("themes", help="Verbatim theme clustering.")
    sp.add_argument("--input", required=True)
    sp.set_defaults(func=run_themes)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
