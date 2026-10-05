"""In-process, one-send image handoff for a trusted host-owned atomic tool.

No default host or CLI is provided. In particular the currently exposed
``image_gen__imagegen`` tool does not expose the subscription-only hard cap or
idempotent lookup required by this contract, so it must not be wrapped here.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

import orchestrate
import run_state


class ImageDispatchError(ValueError):
    pass


def request_identity(plan, node_id):
    return "image-" + orchestrate.digest([plan["run_id"], plan["plan_digest"], node_id])[:40]


def _node(plan, node_id, now, fresh_plan=True):
    if fresh_plan:
        run_state.validate_plan(plan, now)
    else:
        run_state.safe_json(plan)
        if plan.get("plan_digest") != orchestrate.digest(
                {key: value for key, value in plan.items() if key != "plan_digest"}):
            raise ImageDispatchError("IMAGE_PLAN_CHANGED")
    node = next((item for item in plan["steps"] if item["id"] == node_id), None)
    if (node is None or node.get("kind") != "image"
            or (node.get("route") or {}).get("transport") != "host-image"
            or (node.get("handoff") or {}).get("kind") != "host-image"
            or node["handoff"].get("atomic_subscription_only") is not True
            or node["handoff"].get("idempotent_lookup_required") is not True):
        raise ImageDispatchError("IMAGE_HOST_ROUTE_REQUIRED")
    return node


def _live_host(host, route, node, now):
    if not all(callable(getattr(host, name, None)) for name in
               ("observe_image_tool", "generate_once", "lookup_by_request")):
        raise ImageDispatchError("IMAGE_HOST_ATOMIC_ADAPTER_UNAVAILABLE")
    observation = host.observe_image_tool()
    if not isinstance(observation, dict):
        raise ImageDispatchError("IMAGE_HOST_OBSERVATION_INVALID")
    runtime = {"host_ref": route["host_ref"], "interaction_ref": route["interaction_ref"]}
    reasons = orchestrate.assess_image_tool(observation, runtime, node, now)
    if (reasons or observation.get("id") != route.get("candidate_id")
            or observation.get("surface") != route.get("surface")
            or observation.get("tool_ref") != route.get("tool_ref")
            or observation.get("billing", {}).get("account_ref") != route["billing"]["account_ref"]):
        raise ImageDispatchError("IMAGE_HOST_REVALIDATION_FAILED:" + ",".join(reasons))


def _lookup_host(host, route, now):
    """Reentry needs exact lookup identity, not remaining generation quota."""
    if not callable(getattr(host, "observe_image_tool", None)) or not callable(
            getattr(host, "lookup_by_request", None)):
        raise ImageDispatchError("IMAGE_HOST_LOOKUP_UNAVAILABLE")
    observed = host.observe_image_tool()
    if (not isinstance(observed, dict) or observed.get("id") != route.get("candidate_id")
            or observed.get("surface") != route.get("surface")
            or observed.get("tool_ref") != route.get("tool_ref")
            or observed.get("host_ref") != route.get("host_ref")
            or observed.get("interaction_ref") != route.get("interaction_ref")
            or not isinstance(observed.get("billing"), dict)
            or observed["billing"].get("account_ref") != route["billing"]["account_ref"]
            or not orchestrate.fresh(observed.get("observed_at"), now)
            or not observed.get("evidence")):
        raise ImageDispatchError("IMAGE_HOST_LOOKUP_IDENTITY_CHANGED")


def _record(store, dispatch_id, receipt, request_id, now):
    if receipt is None:
        return {"status": "uncertain", "dispatch_id": dispatch_id,
                "reason": "IMAGE_ACCEPTANCE_UNKNOWN"}
    if not isinstance(receipt, dict) or receipt.get("request_id") != request_id:
        raise ImageDispatchError("IMAGE_REQUEST_ID_MISMATCH")
    handle = receipt.get("handle")
    if (not isinstance(handle, dict) or set(handle) != {"kind", "id", "identity"}
            or handle["kind"] != "host-image" or handle["identity"] != request_id):
        raise ImageDispatchError("IMAGE_HANDLE_UNVERIFIED")
    state = receipt.get("state")
    if state not in {"running", "unknown", "succeeded", "failed"}:
        raise ImageDispatchError("IMAGE_STATE_UNVERIFIED")
    if state == "succeeded" and not re.fullmatch(r"[0-9a-f]{64}", receipt.get("result_sha256", "")):
        raise ImageDispatchError("IMAGE_RESULT_DIGEST_REQUIRED")
    observed_at = receipt.get("observed_at")
    if not orchestrate.fresh(observed_at, now):
        raise ImageDispatchError("IMAGE_RECEIPT_STALE")
    evidence = receipt.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ImageDispatchError("IMAGE_RECEIPT_EVIDENCE_REQUIRED")
    store.bind(dispatch_id, handle, now)
    proof = {"state": state, "observed_at": observed_at, "handle": handle,
             "evidence": evidence, "result_sha256": receipt.get("result_sha256")}
    store.observe(dispatch_id, proof, now)
    # Image bytes, acceptance and actual additional charge are checked later.
    return {"status": state, "dispatch_id": dispatch_id,
            "result_sha256": receipt.get("result_sha256"), "verified": False,
            "actual_usd": None}


def dispatch(plan, node_id, store, host, now=None):
    """Claim once, reobserve, then call an atomic provider-enforced $0 tool.

    Reentry performs lookup only. An ambiguous send never gets a new request ID
    or an automatic retry, and the Store keeps its cost reservation unresolved.
    """
    now = now or datetime.now(timezone.utc).isoformat()
    node = _node(plan, node_id, now, fresh_plan=False)
    request_id = request_identity(plan, node_id)
    if any(attempt["run_id"] == plan["run_id"] and attempt["node_id"] == node_id
           and attempt["plan_digest"] == plan["plan_digest"]
           and attempt["request_id"] == request_id
           for attempt in store.snapshot()["attempts"]):
        return reconcile(plan, node_id, store, host, now)
    run_state.validate_plan(plan, now)
    route = node["route"]
    _live_host(host, route, node, now)
    claim = store.claim(plan["run_id"], node_id, request_id, plan["plan_digest"], now)
    dispatch_id = claim["dispatch_id"]
    if not claim["dispatch_allowed"]:
        return reconcile(plan, node_id, store, host, now)
    # An account/tool change after claim leaves an unresolved intent, not a send.
    _live_host(host, route, node, now)
    try:
        receipt = host.generate_once(request_id=request_id, tool_ref=route["tool_ref"],
                                     account_ref=route["billing"]["account_ref"],
                                     prompt=node["task"], subscription_only=True,
                                     provider_hard_cap_usd=0)
    except Exception:
        return {"status": "uncertain", "dispatch_id": dispatch_id,
                "reason": "IMAGE_SEND_OUTCOME_UNKNOWN"}
    return _record(store, dispatch_id, receipt, request_id, now)


def reconcile(plan, node_id, store, host, now=None):
    """Look up the original request even after quota/cap or plan freshness changes."""
    now = now or datetime.now(timezone.utc).isoformat()
    node = _node(plan, node_id, now, fresh_plan=False)
    route = node["route"]
    request_id = request_identity(plan, node_id)
    attempts = [attempt for attempt in store.snapshot()["attempts"]
                if attempt["run_id"] == plan["run_id"]
                and attempt["node_id"] == node_id
                and attempt["plan_digest"] == plan["plan_digest"]
                and attempt["request_id"] == request_id]
    if len(attempts) != 1 or attempts[0]["route"] != route:
        raise ImageDispatchError("IMAGE_ORIGINAL_INTENT_NOT_FOUND")
    _lookup_host(host, route, now)
    receipt = host.lookup_by_request(request_id)
    attempt = attempts[0]
    if attempt["state"] in {"succeeded", "failed", "rejected"}:
        proof = attempt["observation"] or {}
        receipt_state = "succeeded" if attempt["state"] == "rejected" else attempt["state"]
        if (not isinstance(receipt, dict) or receipt.get("request_id") != request_id
                or receipt.get("handle") != attempt["handle"]
                or proof.get("state") != receipt_state
                or receipt.get("state") != receipt_state
                or receipt.get("result_sha256") != proof.get("result_sha256")
                or not orchestrate.fresh(receipt.get("observed_at"), now)
                or not isinstance(receipt.get("evidence"), list)
                or not receipt["evidence"]):
            raise ImageDispatchError("IMAGE_TERMINAL_RECEIPT_CHANGED")
        # Store proof is immutable after completion; a fresher lookup is not a new observation.
        return {"status": attempt["state"], "dispatch_id": attempt["dispatch_id"],
                "result_sha256": proof.get("result_sha256"),
                "verified": attempt["verified"], "actual_usd": attempt["actual_usd"]}
    return _record(store, attempt["dispatch_id"], receipt, request_id, now)
