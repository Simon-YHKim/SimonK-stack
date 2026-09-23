#!/usr/bin/env python3
"""Offline /vibe orchestration planner. Outputs handoffs, never launches a worker.

The host reads the selected skills, supplies observed runtime facts, executes only
ready nodes, and verifies results. Prices/model IDs are inputs, not hidden defaults.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

SURFACES = {"claude": "anthropic", "codex": "openai", "antigravity": "google",
            "grok": "xai", "grok-bot": "xai"}
DEMAND_TIER = {"routine": 1, "reasoning": 2, "critical": 3}
# Task semantics only. Models, scoring, effort and money stay in central policy.
# model-router documents this contract; offline tests bind the mirror to it.
TASK_TYPE_MAP = {
    "CODE_NEW": {"kind": "llm", "needs": ["code"], "demand": "reasoning", "proc": "coding", "class": "B"},
    "CODE_FIX": {"kind": "llm", "needs": ["code"], "demand": "reasoning", "proc": "coding", "class": "B"},
    "CODE_REVIEW": {"kind": "llm", "needs": ["code", "reasoning"], "demand": "reasoning", "proc": "claim-verify", "class": "A-verify"},
    "RESEARCH": {"kind": "llm", "needs": ["research", "reasoning"], "demand": "reasoning", "proc": "research-deep", "class": "B"},
    "AGENTIC": {"kind": "llm", "needs": ["reasoning"], "demand": "reasoning", "proc": "terminal-ci-git", "class": "B"},
    "COMPUTER_USE": {"kind": "gui", "needs": ["gui"], "demand": "reasoning", "proc": "ui-visual", "class": "C-platform"},
    "DESIGN_UI": {"kind": "llm", "needs": ["vision", "reasoning"], "demand": "reasoning", "proc": "ui-visual", "class": "C-platform"},
    "KOREAN_DOC": {"kind": "llm", "needs": ["reasoning"], "demand": "reasoning", "proc": "research-deep", "class": "B"},
    "BULK_LIGHT": {"kind": "llm", "needs": ["reasoning"], "demand": "routine", "proc": "bulk-transform", "class": "A"},
    "REASONING_ABSTRACT": {"kind": "llm", "needs": ["reasoning"], "demand": "critical", "proc": "research-deep", "class": "B"},
    "VISION": {"kind": "llm", "needs": ["vision"], "demand": "reasoning", "proc": "ui-visual", "class": "C-platform"},
}
ORCHESTRATORS = {"vibe", "simonk", "app-dev-orchestrator", "dev-orchestrator"}
SCRIPT_ROOT = Path(__file__).resolve().parent
DEFAULT_TTL = 900  # Refresh availability, price quotes and quota before dispatch.
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))
from model_registry import constrain_runtime, load_registry


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def money(value):
    if isinstance(value, bool):
        raise ValueError("Money must be a finite nonnegative number")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("Money must be a finite nonnegative number") from None
    if not amount.is_finite() or amount < 0:
        raise ValueError("Money must be a finite nonnegative number")
    return amount


def instant(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamps must have a timezone")
    return result


def fresh(observed, now, ttl=DEFAULT_TTL):
    try:
        return 0 <= (instant(now) - instant(observed)).total_seconds() <= ttl
    except (TypeError, ValueError, AttributeError):
        return False


def discover_skills(roots):
    """First root wins by declared skill name; read metadata only, no imports."""
    result, seen = {}, set()
    for root in roots:
        root = Path(root).expanduser()
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*/SKILL.md")):
            real = path.resolve()
            if real in seen:
                continue
            seen.add(real)
            text = path.read_text(encoding="utf-8-sig")
            parts = text.split("---", 2)
            front = parts[1] if text.startswith("---") and len(parts) == 3 else ""
            # Metadata preview, not a YAML interpreter. Folded descriptions are
            # exposed verbatim; the host reads the full skill before using it.
            def field(key, fallback):
                match = re.search(r"^" + key + r":\s*(.+)$", front, re.MULTILINE)
                return match.group(1).strip().strip('\"\'') if match else fallback
            name = field("name", path.parent.name)
            result.setdefault(name, {"name": name, "path": str(real),
                                    "description": field("description", ""),
                                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()})
    return result


def compile_task_type(node):
    """Compile optional typed steps on the real plan path, without new routing.

    A type grants no authority to write, open a GUI or spend. Stronger needs and
    demand survive; conflicting fields fail closed. Untyped requests still work.
    """
    result = copy.deepcopy(node)
    if "task_type" not in result:
        return result
    name = result["task_type"]
    if not isinstance(name, str) or name not in TASK_TYPE_MAP:
        raise ValueError("Unknown task_type")
    if type(result.get("writes")) is not bool:
        raise ValueError("Typed steps require explicit boolean writes scope")
    if name == "CODE_REVIEW" and result["writes"]:
        raise ValueError("CODE_REVIEW is read-only; put repairs in a separate CODE_FIX step")
    contract = TASK_TYPE_MAP[name]
    for field in ("kind", "proc", "class"):
        if field in result and result[field] != contract[field]:
            raise ValueError("task_type conflicts with " + field)
        result[field] = contract[field]
    demand = result.get("demand", contract["demand"])
    if (not isinstance(demand, str) or demand not in DEMAND_TIER
            or DEMAND_TIER[demand] < DEMAND_TIER[contract["demand"]]):
        raise ValueError("task_type demand floor cannot be weakened")
    result["demand"] = demand
    needs = result.get("needs", contract["needs"])
    if (not isinstance(needs, list) or any(not isinstance(n, str) or not n for n in needs)
            or not set(contract["needs"]) <= set(needs)):
        raise ValueError("task_type capability requirements cannot be weakened")
    result["needs"] = copy.deepcopy(needs)
    return result


def ordered_steps(steps):
    ids = [s.get("id") for s in steps]
    if not steps or any(not isinstance(i, str) or not re.fullmatch(r"[\w.-]{1,80}", i) for i in ids):
        raise ValueError("Steps require nonempty unique IDs")
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate step IDs")
    for s in steps:
        deps = s.get("depends_on", [])
        if not isinstance(deps, list) or any(d not in ids for d in deps):
            raise ValueError("Unknown dependency")
        if s.get("verify_of") and s["verify_of"] not in deps:
            raise ValueError("A verifier must depend on the step it verifies")
    remaining, ordered, done = list(steps), [], set()
    while remaining:
        wave = [s for s in remaining if set(s.get("depends_on", [])) <= done]
        if not wave:
            raise ValueError("Dependency cycle")
        ordered.extend(wave)
        done.update(s["id"] for s in wave)
        remaining = [s for s in remaining if s["id"] not in done]
    return ordered


def assess_candidate(c, step, policy, now, producer_vendor=None):
    errors = list(c.get("registry_errors", []))
    surface = c.get("surface")
    demand = step.get("demand", "routine")
    effort = c.get("effort_by_demand", {}).get(demand)
    if surface not in SURFACES:
        errors.append("UNKNOWN_SURFACE")
    if step.get("surface") and step["surface"] != surface:
        errors.append("SURFACE_MISMATCH")
    if c.get("available") is not True or c.get("lifecycle") != "active":
        errors.append("MODEL_UNAVAILABLE")
    if not fresh(c.get("observed_at"), now) or not c.get("evidence"):
        errors.append("RUNTIME_STALE")
    if not set(step.get("needs", [])) <= set(c.get("capabilities", [])):
        errors.append("CAPABILITY_MISMATCH")
    floor = max(DEMAND_TIER[demand], 2 if policy["mode"] == "quality" else 1)
    tier, rank = c.get("quality_tier"), c.get("resource_rank")
    if type(tier) is not int or not 1 <= tier <= 3 or tier < floor:
        errors.append("QUALITY_FLOOR")
    if type(rank) is not int or rank < 0:
        errors.append("RESOURCE_RANK_INVALID")
    if producer_vendor and SURFACES.get(surface) == producer_vendor:
        errors.append("SAME_VENDOR_REVIEW")
    if step["kind"] == "gui":
        if surface != "grok-bot" or c.get("transport") != "bot":
            errors.append("GUI_REQUIRES_BOT")
        if not re.match(r"^active(?:\s|$)", c.get("bot_status", ""), re.IGNORECASE) or not c.get("bot_id"):
            errors.append("BOT_INACTIVE")
        effort = None  # Grok Bot has no verified model/effort control surface.
    else:
        if surface == "grok-bot" or c.get("transport") not in ("host", "cli", "orca"):
            errors.append("TRANSPORT_MISMATCH")
        if not c.get("model"):
            errors.append("MODEL_UNRESOLVED")
        if (not effort or effort not in c.get("provider_efforts", [])
                or effort not in c.get("transport_efforts", [])):
            errors.append("EFFORT_UNSUPPORTED")
        if c.get("transport") == "host" and c.get("effective_effort") != effort:
            errors.append("HOST_EFFORT_MISMATCH")
    billing = c.get("billing", {})
    account_ref = billing.get("account_ref")
    if not isinstance(account_ref, str) or not account_ref.strip():
        errors.append("ACCOUNT_UNVERIFIED")
    upper = None
    if billing.get("verified") is not True:
        errors.append("BILLING_UNVERIFIED")
    elif billing.get("mode") == "subscription":
        if billing.get("extra_usage_enabled") is not False:
            errors.append("OVERAGE_UNVERIFIED")
        else:
            upper = Decimal(0)  # Incremental bill only; subscription usage is separate.
    elif billing.get("mode") in ("api", "metered"):
        try:
            upper = money(c.get("upper_usd_per_attempt"))
        except ValueError:
            errors.append("COST_UNKNOWN")
    else:
        errors.append("BILLING_UNVERIFIED")
    quota = c.get("quota", {})
    used = quota.get("used_pct")
    if isinstance(used, bool) or not isinstance(used, (int, float)) or not 0 <= used <= 100:
        errors.append("QUOTA_UNKNOWN")
    elif used >= 100:
        errors.append("QUOTA_EXHAUSTED")
    if not fresh(quota.get("observed_at"), now):
        errors.append("QUOTA_STALE")
    reserved = upper * policy["max_attempts"] if upper is not None else None
    if reserved is not None and reserved > money(policy["approved_usd"]):
        errors.append("PAID_BUDGET_EXCEEDED")
    return errors, effort, reserved


def _legacy_validation(nodes, runtime):
    """Retain the full Orca guard. This is preflight, never worker-start."""
    orca_nodes = [s for s in nodes if (s.get("route") or {}).get("transport") == "orca"]
    if not orca_nodes:
        return []
    if str(SCRIPT_ROOT) not in sys.path:
        sys.path.insert(0, str(SCRIPT_ROOT))
    import routing
    assignments = []
    for s in orca_nodes:
        r = s["route"]
        a = {"proc": s.get("proc"), "class": s.get("class"), "lane": r["model"],
             "effort": r["requested_effort"], "writes": s.get("writes", False),
             "off_ladder": s.get("off_ladder", False), "falsifiable": s.get("falsifiable", False)}
        if a["proc"] not in routing.PROC_BY_ID or a["lane"] not in routing.LANES:
            return ["ORCA_UNREGISTERED_PROCESS_OR_MODEL"]
        try:
            routing.dispatch_argv(a["lane"], a["effort"], "dry-task", s["id"],
                                  worktree="current", allow_off_ladder=a["off_ladder"])
        except ValueError:
            return ["ORCA_DISPATCH_UNSUPPORTED"]
        assignments.append(a)
    # G5 counts the four original provider seats, not five execution surfaces.
    ok, violations, _ = routing.validate_plan(
        assignments, quota_checked_vendors=runtime.get("quota_checked_vendors", []),
        quota_states=runtime.get("quota_states", {}))
    return [] if ok else ["ORCA_" + v for v in violations]


def make_plan(request, catalog, runtime, now=None, registry=None):
    now = now or datetime.now(timezone.utc).isoformat()
    instant(now)
    runtime = constrain_runtime(runtime, registry if registry is not None else load_registry(), now)
    budget = request.get("budget", {})
    policy = {"mode": budget.get("mode", "balanced"),
              "approved_usd": str(money(budget.get("approved_usd", 0))),
              "spent_usd": str(money(budget.get("spent_usd", 0))),
              "external_reserved_usd": str(money(budget.get("external_reserved_usd", 0))),
              "max_attempts": budget.get("max_attempts", 2),
              "max_parallel": budget.get("max_parallel", 2)}
    if policy["mode"] not in ("economy", "balanced", "quality"):
        raise ValueError("Unknown cost mode")
    for field in ("max_attempts", "max_parallel"):
        if type(policy[field]) is not int or not 1 <= policy[field] <= 8:
            raise ValueError(field + " must be an integer from 1 to 8")
    ancestors = request.get("ancestor_skills", [])
    if (not isinstance(ancestors, list)
            or any(not isinstance(name, str) or not name.strip() for name in ancestors)):
        raise ValueError("ancestor_skills must be a list of nonempty skill names")
    nodes = ordered_steps([compile_task_type(s) for s in request.get("steps", [])])
    candidates = runtime.get("candidates", [])
    candidate_ids = [c.get("id") for c in candidates]
    if len(set(candidate_ids)) != len(candidate_ids) or any(not i for i in candidate_ids):
        raise ValueError("Candidate IDs must be nonempty and unique")
    by_id, reserved = {}, Decimal(0)
    for s in nodes:
        errors, rejected, choices = [], [], []
        s["route"], s["handoff"] = None, None
        s["skill_paths"] = []
        if s.get("kind") not in ("local", "llm", "gui") or s.get("demand", "routine") not in DEMAND_TIER:
            raise ValueError("Invalid step kind or demand")
        for name in s.get("skills", []):
            if name == "vibe" or name in ancestors:
                errors.append("RECURSIVE_SKILL")
            elif name not in catalog:
                errors.append("SKILL_NOT_FOUND:" + name)
            else:
                s["skill_paths"].append(catalog[name]["path"])
        tools = set(s.get("software", []))
        if tools and (not fresh(runtime.get("observed_at"), now) or not tools <= set(runtime.get("tools", []))):
            errors.append("SOFTWARE_UNAVAILABLE")
        if s["kind"] == "gui":
            if s.get("tool_route_available") is not False or not s.get("gui_reason"):
                errors.append("PREFER_TOOL_ROUTE")
            if not s.get("target"):
                errors.append("GUI_TARGET_REQUIRED")
            if "vibe-bot" not in s.get("skills", []):
                errors.append("BOT_SKILL_REQUIRED")
        parent = by_id.get(s.get("verify_of"))
        vendor = (parent.get("route") or {}).get("vendor") if parent else None
        if parent and not parent.get("route"):
            errors.append("PRODUCER_UNROUTED")
        if s.get("writes") and not any(n.get("verify_of") == s["id"] and n.get("kind") == "llm" for n in nodes):
            errors.append("MISSING_REVIEW")
        if s["kind"] == "local":
            argv = s.get("argv")
            local_upper = None
            if not isinstance(argv, list) or not argv or any(not isinstance(a, str) for a in argv):
                errors.append("LOCAL_ARGV_REQUIRED")
            elif argv[0] not in tools:
                errors.append("LOCAL_TOOL_NOT_DECLARED")
            else:
                binary = re.split(r"[/\\]", argv[0])[-1].lower().removesuffix(".exe").removesuffix(".cmd")
                if binary in ("claude", "codex", "grok", "agy") or (binary == "orca" and "worker-start" in argv):
                    errors.append("LLM_CLI_AS_LOCAL")
                quote = next((q for q in runtime.get("tool_costs", []) if q.get("argv_sha256") == digest(argv)), {})
                if quote.get("verified") is not True or not quote.get("evidence") or not fresh(quote.get("observed_at"), now):
                    errors.append("LOCAL_COST_UNVERIFIED")
                else:
                    try:
                        local_upper = money(quote.get("upper_usd_per_attempt")) * policy["max_attempts"]
                    except ValueError:
                        errors.append("LOCAL_COST_UNVERIFIED")
            if not errors:
                reserved += local_upper
                s["route"] = {"surface": "local", "transport": "tool", "model": None,
                              "vendor": None, "requested_effort": None, "effective_effort": None,
                              "reserved_upper_usd": float(local_upper), "actual_usd": None}
                s["handoff"] = {"kind": "tool", "argv": argv, "shell": False}
        elif not errors:
            for c in candidates:
                reasons, effort, amount = assess_candidate(c, s, policy, now, vendor)
                if reasons:
                    rejected.append({"candidate_id": c["id"], "reasons": reasons})
                    continue
                # Monetary bounds first. Within a subscription, prefer low quota
                # pressure and the declared resource rank, not fabricated prices.
                score = (amount, c["quota"]["used_pct"] > 80,
                         c.get("resource_rank", 100), c["quota"]["used_pct"], c["id"])
                choices.append((score, c, effort, amount))
            if not choices:
                errors.append("NO_ELIGIBLE_ROUTE")
            else:
                _, c, effort, amount = min(choices, key=lambda v: v[0])
                reserved += amount
                s["route"] = {"candidate_id": c["id"], "surface": c["surface"],
                              "vendor": SURFACES[c["surface"]], "transport": c["transport"],
                              "model": c.get("model"), "requested_model": c.get("requested_model"),
                              "resolved_model": c.get("resolved_model"), "requested_effort": effort,
                              "effective_effort": c.get("effective_effort") if c["transport"] == "host" else None,
                              "billing": copy.deepcopy(c["billing"]), "quota": copy.deepcopy(c["quota"]),
                              "reserved_upper_usd": float(amount), "actual_usd": None,
                              "valid_until": c["valid_until"],
                              "runtime_observed_at": c["observed_at"]}
                s["handoff"] = {"kind": c["transport"], "read_skills": s["skill_paths"],
                                "reuse_coordinator": any(k in ORCHESTRATORS for k in s.get("skills", []))}
                if s["kind"] == "gui":
                    s["handoff"].update({"mode": "console", "bot_id": c["bot_id"],
                                         "target": s["target"], "require_nonce_result": True})
        s["errors"], s["rejected_candidates"] = sorted(set(errors)), rejected
        by_id[s["id"]] = s
    total = reserved + money(policy["spent_usd"]) + money(policy["external_reserved_usd"])
    global_errors = _legacy_validation(nodes, runtime)
    if total > money(policy["approved_usd"]):
        global_errors.append("RUN_BUDGET_EXCEEDED")
    policy.update({"reserved_upper_usd": float(reserved), "committed_upper_usd": float(total),
                   "estimate_is_provider_hard_cap": False})
    if not isinstance(request.get("run_id"), str) or not request["run_id"].strip():
        raise ValueError("A unique run_id is required")
    result = {"schema_version": 1, "run_id": request["run_id"], "ancestor_skills": copy.deepcopy(ancestors),
            "planned_at": now, "status": "blocked" if global_errors or any(s["errors"] for s in nodes) else "ready",
            "errors": global_errors, "budget": policy, "steps": nodes,
            "model_registry": runtime["model_registry"]}
    result["plan_digest"] = digest(result)
    return result


def ready_steps(plan, events, now=None):
    """No implicit retries. Done requires accepted evidence, not a transport rc."""
    if plan.get("status") != "ready" or plan.get("errors"):
        return []
    now = now or datetime.now(timezone.utc).isoformat()
    if not fresh(plan.get("planned_at"), now):
        return []
    for node in plan["steps"]:
        route = node.get("route") or {}
        if route.get("surface") != "local":
            try:
                valid = instant(now) <= instant(route.get("valid_until"))
            except (TypeError, ValueError, AttributeError):
                valid = False
            if (not valid or not fresh(route.get("runtime_observed_at"), now)
                    or not fresh(route.get("quota", {}).get("observed_at"), now)):
                return []
    if plan.get("plan_digest") != digest({k: v for k, v in plan.items() if k != "plan_digest"}):
        raise ValueError("Plan changed after validation")
    ids = {s["id"] for s in plan["steps"]}
    latest = {}
    for event in events:
        if event.get("run_id") != plan["run_id"] or event.get("plan_digest") != plan["plan_digest"]:
            raise ValueError("Result belongs to another run or plan")
        if event.get("id") not in ids:
            raise ValueError("Result for unknown step")
        latest[event["id"]] = event
    done = {key for key, e in latest.items() if e.get("status") == "done"
            and e.get("verified") is True and isinstance(e.get("evidence"), list) and e["evidence"]}
    running = sum(e.get("status") in ("running", "waiting_external") for e in latest.values())
    slots = max(0, plan["budget"]["max_parallel"] - running)
    by_id = {s["id"]: s for s in plan["steps"]}
    ancestor_cache = {}

    def ancestors(node):
        if node["id"] not in ancestor_cache:
            result = set(node.get("depends_on", []))
            for dependency in node.get("depends_on", []):
                result.update(ancestors(by_id[dependency]))
            ancestor_cache[node["id"]] = result
        return ancestor_cache[node["id"]]

    def reviewed_dependencies(node):
        if not set(node.get("depends_on", [])) <= done:
            return False
        for dependency in ancestors(node):
            if not by_id[dependency].get("writes") or node.get("verify_of") == dependency:
                continue  # Reviewers need the producer's output before approval.
            reviewers = {s["id"] for s in plan["steps"]
                         if s.get("kind") == "llm" and s.get("verify_of") == dependency}
            if not reviewers <= done:
                return False
        return True

    return [s["id"] for s in plan["steps"] if s["id"] not in latest and not s["errors"]
            and reviewed_dependencies(s)][:slots]


def verify_bot_result(skill_root, meta_path, result_path, expected_nonce, evidence_path=None):
    """Validate console mode from the expected metadata, never collect's exit code."""
    if not expected_nonce:
        return ["BOT_NONCE_REQUIRED"]
    try:
        meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
        text = Path(result_path).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return ["BOT_RESULT_OR_META_MISSING"]
    if meta.get("nonce") != expected_nonce or meta.get("mode") != "console":
        return ["BOT_META_MISMATCH"]
    try:
        evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    except (TypeError, OSError, ValueError):
        return ["BOT_SCREENSHOT_EVIDENCE_MISSING"]
    if (evidence.get("nonce") != expected_nonce or not meta.get("target")
            or evidence.get("target") != meta["target"] or not evidence.get("images")):
        return ["BOT_EVIDENCE_MISMATCH"]
    result_root = Path(result_path).resolve().parent
    for item in evidence["images"]:
        try:
            path = (result_root / item).resolve()
            path.relative_to(result_root)
            with path.open("rb") as stream:
                magic = stream.read(12)
            if not (magic.startswith(b"\x89PNG\r\n\x1a\n") or magic.startswith(b"\xff\xd8\xff")):
                return ["BOT_SCREENSHOT_INVALID"]
        except (OSError, ValueError, TypeError):
            return ["BOT_SCREENSHOT_MISSING_OR_OUTSIDE_RUN"]
    source = Path(skill_root) / "scripts" / "make_bot_spec.py"
    spec = importlib.util.spec_from_file_location("vibe_bot_adapter", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify_result(text, expected_nonce, mode="console")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("catalog", "plan", "ready", "verify-bot"))
    parser.add_argument("--root", action="append", default=[])
    parser.add_argument("--input", type=Path)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--registry", type=Path, help="Override the packaged central model registry")
    parser.add_argument("--events", type=Path)
    parser.add_argument("--now")
    parser.add_argument("--bot-root", type=Path)
    parser.add_argument("--meta", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--nonce")
    args = parser.parse_args(argv)
    roots = args.root or [SCRIPT_ROOT.parent.parent, Path.home() / ".agents" / "skills",
                         Path.home() / ".codex" / "skills", Path.home() / ".claude" / "skills"]
    def read(path):
        if path is None:
            raise ValueError("Required JSON input path missing")
        return json.loads(path.read_text(encoding="utf-8-sig"))
    try:
        if args.command == "catalog":
            result = discover_skills(roots)
        elif args.command == "plan":
            result = make_plan(read(args.input), discover_skills(roots), read(args.runtime), args.now,
                               load_registry(args.registry) if args.registry else None)
        elif args.command == "ready":
            result = ready_steps(read(args.input), read(args.events) if args.events else [], args.now)
        else:
            if not all((args.bot_root, args.meta, args.result, args.nonce)):
                raise ValueError("verify-bot requires --bot-root, --meta, --result, --nonce")
            result = {"findings": verify_bot_result(args.bot_root, args.meta, args.result, args.nonce, args.evidence)}
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 2 if isinstance(result, dict) and (result.get("status") == "blocked" or result.get("findings")) else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
