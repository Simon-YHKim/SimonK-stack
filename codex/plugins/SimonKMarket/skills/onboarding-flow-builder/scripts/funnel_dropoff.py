#!/usr/bin/env python3
"""온보딩 드롭오프 측정기 (stdlib only).

이벤트 로그(JSONL 또는 CSV)를 읽어 단계별 퍼널, skip rate,
Time-to-Aha, activation rate, 권한 opt-in 을 계산한다.

기대 이벤트 (onboarding-flow-builder 5단계에서 심음):
  onboarding_started        { user_id, ts }
  onboarding_step_viewed    { user_id, ts, step_id, step_index }
  onboarding_step_completed { user_id, ts, step_id, step_index }
  onboarding_step_skipped   { user_id, ts, step_id, step_index }
  permission_primed         { user_id, ts, permission }
  permission_granted        { user_id, ts, permission }
  aha_moment_reached        { user_id, ts }          # signup 대비 시간은 ts 차이로
  user_signed_up            { user_id, ts }          # Time-to-Aha 기준점(없으면 started 사용)

ts: epoch ms (정수) 또는 ISO8601 문자열.
필수 필드: event, user_id, ts. 나머지는 있으면 사용.

사용:
  python funnel_dropoff.py events.jsonl
  python funnel_dropoff.py events.csv --format csv
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime


def parse_ts(value):
    """epoch ms 또는 ISO8601 → epoch ms(float). 실패 시 None."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        pass
    try:
        s = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(s).timestamp() * 1000.0
    except ValueError:
        return None


def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_csv(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def median(values):
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def analyze(rows):
    # step_index -> set(user) 별 viewed/completed/skipped
    viewed = defaultdict(set)
    completed = defaultdict(set)
    skipped = defaultdict(set)
    step_label = {}

    primed = defaultdict(set)   # permission -> users
    granted = defaultdict(set)

    started_users = set()
    aha_ts = {}        # user -> earliest aha ts
    baseline_ts = {}   # user -> signup(우선) 또는 started ts

    for r in rows:
        ev = r.get("event")
        uid = r.get("user_id")
        if not ev or not uid:
            continue
        ts = parse_ts(r.get("ts"))
        idx = r.get("step_index")
        if ev == "onboarding_started":
            started_users.add(uid)
            baseline_ts.setdefault(uid, ts)
        elif ev == "user_signed_up":
            if ts is not None:
                baseline_ts[uid] = ts  # signup 이 우선 기준
        elif ev == "onboarding_step_viewed":
            viewed[idx].add(uid)
            if r.get("step_id"):
                step_label[idx] = r["step_id"]
        elif ev == "onboarding_step_completed":
            completed[idx].add(uid)
        elif ev == "onboarding_step_skipped":
            skipped[idx].add(uid)
        elif ev == "permission_primed":
            primed[r.get("permission")].add(uid)
        elif ev == "permission_granted":
            granted[r.get("permission")].add(uid)
        elif ev == "aha_moment_reached":
            if ts is not None and (uid not in aha_ts or ts < aha_ts[uid]):
                aha_ts[uid] = ts

    return {
        "viewed": viewed, "completed": completed, "skipped": skipped,
        "step_label": step_label, "primed": primed, "granted": granted,
        "started_users": started_users, "aha_ts": aha_ts, "baseline_ts": baseline_ts,
    }


def pct(num, den):
    return f"{(100.0 * num / den):.1f}%" if den else "n/a"


def report(a):
    out = []
    out.append("=== Step Funnel (viewed -> completed) ===")
    indices = sorted(
        (i for i in set(a["viewed"]) | set(a["completed"]) | set(a["skipped"]) if i is not None),
        key=lambda x: (str(x).zfill(4)),
    )
    worst = None
    for idx in indices:
        v = len(a["viewed"].get(idx, set()))
        c = len(a["completed"].get(idx, set()))
        sk = len(a["skipped"].get(idx, set()))
        label = a["step_label"].get(idx, idx)
        conv = (c / v) if v else None
        out.append(
            f"  step {idx} ({label}): viewed={v} completed={c} ({pct(c, v)}) "
            f"skipped={sk} ({pct(sk, v)})"
        )
        if v and (worst is None or conv < worst[1]):
            worst = (idx, conv, label)

    if worst:
        out.append(f"  -> 최저 전환 스텝: {worst[0]} ({worst[2]}) = {pct(worst[1] * 100, 100)}  # 개선 1순위")

    out.append("")
    out.append("=== Time-to-Aha & Activation ===")
    deltas = []
    for uid, t_aha in a["aha_ts"].items():
        base = a["baseline_ts"].get(uid)
        if base is not None and t_aha is not None:
            deltas.append(t_aha - base)
    med = median(deltas)
    out.append(f"  aha 도달 유저: {len(a['aha_ts'])}")
    out.append(f"  Time-to-Aha 중앙값: {med/1000.0:.1f}s" if med is not None else "  Time-to-Aha 중앙값: n/a (ts 누락)")
    started = len(a["started_users"]) or len(a["baseline_ts"])
    out.append(f"  Activation rate (aha / started): {pct(len(a['aha_ts']), started)}")

    out.append("")
    out.append("=== Permission Opt-in (granted / primed) ===")
    perms = set(a["primed"]) | set(a["granted"])
    if not perms:
        out.append("  (권한 이벤트 없음)")
    for p in sorted(x for x in perms if x is not None):
        pr = len(a["primed"].get(p, set()))
        gr = len(a["granted"].get(p, set()))
        out.append(f"  {p}: primed={pr} granted={gr} ({pct(gr, pr)})")

    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="온보딩 드롭오프 측정기")
    ap.add_argument("path", help="이벤트 로그 경로 (.jsonl 또는 .csv)")
    ap.add_argument("--format", choices=["jsonl", "csv"], help="미지정 시 확장자로 추론")
    args = ap.parse_args()

    fmt = args.format
    if not fmt:
        fmt = "csv" if args.path.lower().endswith(".csv") else "jsonl"

    try:
        rows = load_csv(args.path) if fmt == "csv" else load_jsonl(args.path)
    except FileNotFoundError:
        print(f"파일 없음: {args.path}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, csv.Error) as exc:
        print(f"파싱 실패: {exc}", file=sys.stderr)
        return 1

    print(report(analyze(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
