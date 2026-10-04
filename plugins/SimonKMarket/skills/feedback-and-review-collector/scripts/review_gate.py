#!/usr/bin/env python3
"""Store-review prompt gating engine. Stdlib only — no deps, no network.

Given a user's current state and a gating config, decides — deterministically —
whether to (a) request the native store review sheet, (b) wait, or (c) route the
user to a private feedback form instead. Same inputs -> same decision.

The hard rule this enforces: ONLY satisfied users who clear every frequency cap
and are not in a recently-negative state ever reach the store sheet. Everyone
else is held back or sent to feedback. Dissatisfied users are NEVER sent to the
store.

Usage:
  python review_gate.py --user user_state.json --config review-prompt-config.json

  # or feed user state on stdin (a single JSON object):
  cat user_state.json | python review_gate.py --config review-prompt-config.json

Decisions:
  REQUEST_REVIEW   all gates passed -> call StoreReview.requestReview()
  ROUTE_FEEDBACK   not satisfied -> open in-app feedback form (NOT the store)
  WAIT             satisfied but a frequency/maturity/negative gate failed
"""
import argparse
import json
import sys

# Korean Windows consoles default to cp949; force UTF-8 so EN/KO output never
# raises UnicodeEncodeError. No-op on already-UTF-8 terminals.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


REQUIRED_USER_FIELDS = {
    "days_since_install": "int — days since first install",
    "session_count": "int — total sessions",
    "days_since_last_prompt": "int — days since the last review prompt (use a "
                              "large number like 9999 if never prompted)",
    "prompts_this_version": "int — review prompts already shown on current app version",
    "prompts_this_year": "int — review prompts shown in the trailing 12 months",
    "satisfaction_signal": "bool — did a positive signal just fire "
                           "(CSAT>=top, NPS>=9, or value action completed)",
    "recent_negative_event": "bool — crash/error/payment-failure/refund in the "
                             "recent window",
}

DEFAULT_CONFIG = {
    "min_days_since_install": 3,
    "min_session_count": 5,
    "min_days_between_prompts": 90,
    "max_prompts_per_version": 1,
    "max_prompts_per_year": 3,
    "block_on_recent_negative": True,
    "feedback_form_destination": "in_app_feedback_form",
}


def _load_json(path, what):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        sys.exit(f"ERROR: {what} file not found: {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: {what} is not valid JSON ({path}): {e}")


def _coerce_bool(v, field):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("true", "1", "yes", "y"):
            return True
        if s in ("false", "0", "no", "n", ""):
            return False
    sys.exit(f"ERROR: field '{field}' must be a boolean, got {v!r}.")


def _coerce_int(v, field):
    try:
        return int(v)
    except (TypeError, ValueError):
        sys.exit(f"ERROR: field '{field}' must be an integer, got {v!r}.")


def _validate_user(user):
    missing = [f for f in REQUIRED_USER_FIELDS if f not in user]
    if missing:
        lines = "\n".join(f"  {f}: {REQUIRED_USER_FIELDS[f]}" for f in missing)
        sys.exit("ERROR: user state missing required field(s):\n" + lines)


def decide(user, config):
    """Pure decision function. Returns (decision, reasons:list[str])."""
    cfg = {**DEFAULT_CONFIG, **(config or {})}

    days_install = _coerce_int(user["days_since_install"], "days_since_install")
    sessions = _coerce_int(user["session_count"], "session_count")
    days_last = _coerce_int(user["days_since_last_prompt"], "days_since_last_prompt")
    per_version = _coerce_int(user["prompts_this_version"], "prompts_this_version")
    per_year = _coerce_int(user["prompts_this_year"], "prompts_this_year")
    satisfied = _coerce_bool(user["satisfaction_signal"], "satisfaction_signal")
    negative = _coerce_bool(user["recent_negative_event"], "recent_negative_event")

    reasons = []

    # GATE 1 — satisfaction. Failing this routes to feedback (not the store).
    if not satisfied:
        reasons.append("no satisfaction signal -> dissatisfied/neutral users must "
                       "not be sent to the store")
        return "ROUTE_FEEDBACK", reasons, cfg["feedback_form_destination"]

    # GATE 4 — recent negative event. A satisfied flag plus a fresh crash/refund
    # is contradictory; the safe move is to hold (do not store-prompt, do not
    # spam a feedback form either).
    if cfg["block_on_recent_negative"] and negative:
        reasons.append("recent negative event (crash/error/payment) -> worst "
                       "timing, hold the prompt")
        return "WAIT", reasons, None

    # GATE 2 — maturity. Has the user actually experienced the app?
    ok = True
    if days_install < cfg["min_days_since_install"]:
        reasons.append(f"too new: {days_install}d < {cfg['min_days_since_install']}d "
                       f"since install")
        ok = False
    if sessions < cfg["min_session_count"]:
        reasons.append(f"too few sessions: {sessions} < {cfg['min_session_count']}")
        ok = False

    # GATE 3 — frequency caps (OS-quota + fatigue).
    if days_last < cfg["min_days_between_prompts"]:
        reasons.append(f"cooldown: {days_last}d < {cfg['min_days_between_prompts']}d "
                       f"since last prompt")
        ok = False
    if per_version >= cfg["max_prompts_per_version"]:
        reasons.append(f"version cap reached: {per_version} >= "
                       f"{cfg['max_prompts_per_version']} this version")
        ok = False
    if per_year >= cfg["max_prompts_per_year"]:
        reasons.append(f"yearly cap reached: {per_year} >= "
                       f"{cfg['max_prompts_per_year']} this year")
        ok = False

    if ok:
        reasons.append("satisfied + mature + within all frequency caps + no recent "
                       "negative event")
        return "REQUEST_REVIEW", reasons, None
    return "WAIT", reasons, None


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Deterministic store-review prompt gating engine.")
    p.add_argument("--user", help="Path to user_state.json (omit to read stdin).")
    p.add_argument("--config", help="Path to review-prompt-config.json "
                                     "(omit to use built-in defaults).")
    p.add_argument("--json", action="store_true",
                   help="Emit the decision as a JSON object.")
    args = p.parse_args(argv)

    if args.user:
        user = _load_json(args.user, "user state")
    else:
        if sys.stdin.isatty():
            sys.exit("ERROR: no --user file and nothing on stdin.")
        try:
            user = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            sys.exit(f"ERROR: stdin is not valid JSON: {e}")
    if not isinstance(user, dict):
        sys.exit("ERROR: user state must be a single JSON object.")
    _validate_user(user)

    config = _load_json(args.config, "config") if args.config else {}

    decision, reasons, destination = decide(user, config)

    if args.json:
        out = {"decision": decision, "reasons": reasons}
        if destination:
            out["feedback_destination"] = destination
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    print(f"DECISION: {decision}")
    if destination:
        print(f"  -> feedback destination: {destination}")
    print("  why:")
    for r in reasons:
        print(f"    - {r}")
    if decision == "REQUEST_REVIEW":
        print("  NEXT: call StoreReview.requestReview() (expo-store-review) after "
              "isAvailableAsync(). The OS may still suppress the sheet; log only "
              "the ATTEMPT, never assume a review was written.")
    elif decision == "ROUTE_FEEDBACK":
        print("  NEXT: open the in-app feedback form. Do NOT show the store sheet.")
    else:
        print("  NEXT: do nothing now; re-evaluate on the next satisfaction signal.")


if __name__ == "__main__":
    main()
