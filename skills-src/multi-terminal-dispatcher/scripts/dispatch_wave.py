#!/usr/bin/env python3
"""One bounded ready wave using sibling /vibe state and Orca adapter.

Exactly one coordinator must serialize invocations for a run. Individual claims
are atomic; the wave is not a transaction or a cross-process uncertain fence.
No initialization, retries, refill, settlement, verification or worker cleanup.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

CORE = Path(__file__).resolve().parents[2] / "vibe" / "scripts"
if not (CORE / "execute_orca.py").is_file():
    raise SystemExit('Sibling /vibe adapter is required; no installed fallback.')
sys.path.insert(0, str(CORE))
import execute_orca
import orchestrate
from run_state import ACTIVE, TERMINAL, Store, StateError, moment, read_payload, safe_json

require = execute_orca.require
ERRORS = (StateError, OSError, ValueError, KeyError, TypeError, AttributeError)
RESULT_KEYS = ("dispatch_id", "run_id", "node_id", "request_id", "state", "handle",
               "actual_usd", "reserved_usd", "verified", "reason", "output")


def current_attempts(plan, snapshot):
    rows = [a for a in snapshot["attempts"] if a["run_id"] == plan["run_id"]
            and a["plan_digest"] == plan["plan_digest"]]
    for row in rows:
        node = execute_orca.selected(plan, row["node_id"])
        if node["route"]["transport"] == "orca":
            require(row["request_id"] == execute_orca.request_id(plan, row["node_id"]),
                    "FOREIGN_DISPATCH_IDENTITY")
    return rows


def unresolved(row):
    require(row["state"] in ACTIVE | TERMINAL, "UNKNOWN_ATTEMPT_STATE")
    return not (row["state"] == "succeeded" and row["verified"] and row["actual_usd"] is not None)


def summary(row):
    return {k: row[k] for k in RESULT_KEYS if k in row}


def run_wave(action, plan, store, certificates, node_ids=None,
             transport_factory=execute_orca.Orca, clock=moment):
    result = {"status": "blocked", "ready": [], "results": [], "new_dispatches": [], "deferred": [],
              "admission_unknown": [], "state_available": None, "budget_halted": None, "halt_reason": None}
    initial_ids, adapters, chosen = set(), {}, []
    registered = False
    sending = None
    try:
        require(action in {"preview", "dispatch", "reconcile"}, "INVALID_ACTION")
        safe_json(plan)
        require(plan["plan_digest"] == orchestrate.digest({k: v for k, v in plan.items() if k != "plan_digest"}),
                "PLAN_CHANGED")
        snapshot = store.snapshot()
        result["state_available"] = True
        runs = [r for r in snapshot["runs"] if r["run_id"] == plan["run_id"]]
        require(len(runs) == 1 and runs[0]["plan_digest"] == plan["plan_digest"], "REGISTERED_PLAN_REQUIRED")
        registered = True
        result.update(run_id=plan["run_id"], plan_digest=plan["plan_digest"])
        known = [n["id"] for n in plan["steps"]]
        if node_ids is not None:
            require(isinstance(node_ids, list) and node_ids and all(isinstance(n, str) for n in node_ids)
                    and len(set(node_ids)) == len(node_ids) and all(n in known for n in node_ids), "INVALID_SELECTION")
        rows = current_attempts(plan, snapshot)
        initial_ids = {a["dispatch_id"] for a in rows}
        pending = [a for a in rows if unresolved(a)]
        ready = store.ready(plan["run_id"], now=clock())
        result["ready"] = ready
        result["budget_halted"] = snapshot["budget"]["halted"]
        result["halt_reason"] = snapshot["budget"]["halt_reason"]
        if action == "preview":
            result.update(status="preview", selected=list(node_ids if node_ids is not None else ready),
                          unresolved=[summary(a) for a in pending], next_action="reconcile" if pending else "dispatch")
            return result

        def adapter(node_id):
            if node_id not in adapters:
                node = execute_orca.selected(plan, node_id)
                require(node["route"]["transport"] == "orca" and node["route"]["surface"] in {"claude", "codex"},
                        "ORCA_SURFACE_UNSUPPORTED")
                binding = node["orca"]
                adapters[node_id] = execute_orca.Adapter(store,
                    transport_factory(binding["executable"], binding["executable_sha256"]), clock=clock)
            return adapters[node_id]

        # This decision is immutable for the entire invocation, even if lookup
        # resolves everything. Explicit selection cannot hide a pending sibling.
        if pending or action == "reconcile":
            result["deferred"] = [n for n in (node_ids if node_ids is not None else ready)
                                  if n not in {a["node_id"] for a in pending}]
            result["unsupported_nodes"] = [a["node_id"] for a in pending
                if execute_orca.selected(plan, a["node_id"])["route"]["transport"] != "orca"]
            require(not result["unsupported_nodes"], "OTHER_TRANSPORT_RECONCILIATION_REQUIRED")
            for row in pending:
                result["results"].append(summary(adapter(row["node_id"]).reconcile(plan, row["node_id"])))
            after = store.snapshot()
            bad = any(a["state"] in {"intent", "uncertain", "failed", "not_started", "rejected"}
                      for a in result["results"])
            result.update(status="blocked" if bad or after["budget"]["halted"] else
                          "reconciled" if pending else "waiting", budget_halted=after["budget"]["halted"],
                          halt_reason=after["budget"]["halt_reason"])
            return result

        require(not snapshot["budget"]["halted"], "SHARED_BUDGET_HALTED")
        chosen = list(node_ids if node_ids is not None else ready)
        require(all(n in ready for n in chosen), "NODE_NOT_READY")
        result["deferred"] = chosen.copy()
        if not chosen:
            result["status"] = "waiting"  # An empty frontier is not proof of completion.
            return result
        require(isinstance(certificates, dict), "CERTIFICATES_REQUIRED")
        require(all(isinstance(certificates.get(n), dict) for n in chosen), "CERTIFICATES_REQUIRED")
        # Preflight the entire fixed set; native read failures cannot cause a
        # partially started wave. This is not cached authority for later sends.
        for node_id in chosen:
            adapter(node_id).preflight(plan, node_id, certificates[node_id])
        owned = set()
        for node_id in chosen:
            fresh = store.snapshot()
            require(not fresh["budget"]["halted"], "SHARED_BUDGET_HALTED")
            pending_now = [a for a in current_attempts(plan, fresh) if unresolved(a)]
            require(all(a["dispatch_id"] in owned and a["state"] == "running" for a in pending_now),
                    "RECONCILIATION_REQUIRED")
            require(node_id in store.ready(plan["run_id"], now=clock()), "NODE_NOT_READY")
            sending = node_id  # Claim/send may occur before a returned observation.
            row = adapter(node_id).dispatch(plan, node_id, certificates[node_id])
            result["results"].append(summary(row))
            owned.add(row["dispatch_id"])
            if row["dispatch_id"] not in initial_ids:
                result["new_dispatches"].append(node_id)
            result["deferred"].remove(node_id)
            sending = None
            require(row["state"] == "running", "DISPATCH_REQUIRES_RECONCILIATION")
            require(not store.snapshot()["budget"]["halted"], "SHARED_BUDGET_HALTED")
        result["status"] = "dispatched"
    except ERRORS:
        # Do not echo exception strings, plan, certificates, executable paths,
        # worker prose or other accounts. Keep any committed intents/handles.
        if registered:
            try:
                after = store.snapshot()
                result.update(budget_halted=after["budget"]["halted"], halt_reason=after["budget"]["halt_reason"])
                for row in current_attempts(plan, after):
                    if row["dispatch_id"] not in initial_ids and row["node_id"] in chosen:
                        if row["node_id"] not in result["new_dispatches"]:
                            result["new_dispatches"].append(row["node_id"])
                        if row["dispatch_id"] not in {r["dispatch_id"] for r in result["results"]}:
                            result["results"].append(summary(row))
                        if row["node_id"] in result["deferred"]:
                            result["deferred"].remove(row["node_id"])
            except ERRORS:
                # Neither the claim nor its absence can be proven. Do not call
                # this node unstarted or invent a new_dispatches entry.
                result.update(state_available=False, budget_halted=None, halt_reason="STATE_UNAVAILABLE")
                if sending is not None:
                    result["admission_unknown"].append(sending)
                    if sending in result["deferred"]:
                        result["deferred"].remove(sending)
        result.update(status="partial" if result["new_dispatches"] or result["admission_unknown"] else "blocked",
                      error="WAVE_BLOCKED")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["preview", "dispatch", "reconcile"], nargs="?", default="preview")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--certificates")
    parser.add_argument("--node", action="append")
    args = parser.parse_args()
    try:
        result = run_wave(args.action, read_payload(args.plan), Store(args.db),
                          read_payload(args.certificates) if args.certificates else {}, args.node)
        print(safe_json(result))
        return 2 if result["status"] in {"blocked", "partial"} else 0
    except ERRORS:
        print(json.dumps({"status": "blocked", "error": "WAVE_INPUT_BLOCKED"}))
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
