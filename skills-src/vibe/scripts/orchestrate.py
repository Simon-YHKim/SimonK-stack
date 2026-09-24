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
import stat
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from itertools import islice
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


# Bounds apply to metadata collection only; no recursive package/body imports.
MAX_SKILL_BYTES = 2 * 1024 * 1024
MAX_SKILL_ENTRIES = 10000
SKILL_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.:-]{0,127}\Z")


class _SkillCatalog(dict):
    """Normal name mapping with scan provenance for both Python and CLI plans."""


def _skill_metadata(raw):
    """Read the name/description scalar subset, not executable or arbitrary YAML."""
    lines = raw.decode("utf-8-sig").splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise ValueError("SKILL_METADATA_INVALID")
    front = lines[1:lines.index("---", 1)]
    values = {}
    for key in ("name", "description"):
        matches = [(i, re.fullmatch(key + r":[ \t]*(.*)", line)) for i, line in enumerate(front)]
        matches = [(i, m.group(1).strip()) for i, m in matches if m]
        if len(matches) != 1:
            raise ValueError("SKILL_METADATA_INVALID")
        index, value = matches[0]
        if key == "description" and value in (">", ">-", ">+", "|", "|-", "|+"):
            block = []
            for line in front[index + 1:]:
                if line and not line[0].isspace():
                    break
                block.append(line.strip())
            value = (" " if value.startswith(">") else "\n").join(block).strip()
        elif value.startswith('"'):
            value = json.loads(value)
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1].replace("''", "'")
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        if not isinstance(value, str) or not value or len(value) > 16384:
            raise ValueError("SKILL_METADATA_INVALID")
        values[key] = value
    if not SKILL_NAME.fullmatch(values["name"]):
        raise ValueError("SKILL_METADATA_INVALID")
    return values


def skill_inventory(roots, exclude_roots=(), host_skills=None):
    """Observe explicit flat roots. Preserve winners, shadows, aliases and gaps."""
    if len(roots) > 64 or len(exclude_roots) > 128:
        raise ValueError("Too many skill roots")
    excluded = [Path(p).expanduser().absolute() for p in exclude_roots]
    excluded += [p.resolve() for p in excluded]
    def is_excluded(path):
        return any(path == p or p in path.parents for p in excluded)
    records, root_rows, issues, seen = [], [], [], {}
    def issue(code, path):
        issues.append({"code": code, "path": str(path)})
    for supplied in roots:
        root = Path(supplied).expanduser().absolute()
        row = {"path": str(root), "resolved_path": None, "status": "scanned", "children_seen": 0}
        root_rows.append(row)
        try:
            if is_excluded(root) or is_excluded(root.resolve()):
                row["status"] = "excluded"
                issue("EXCLUDED", root)
                continue
            row["resolved_path"] = str(root.resolve())
            if not root.is_dir():
                row["status"] = "missing"
                issue("ROOT_MISSING", root)
                continue
            children = list(islice(root.iterdir(), MAX_SKILL_ENTRIES + 1))
            row["children_seen"] = len(children)
            if len(children) > MAX_SKILL_ENTRIES:
                row["status"] = "limited"
                issue("ROOT_LIMIT", root)
                continue
        except (OSError, RuntimeError):
            row["status"] = "unreadable"
            issue("ROOT_UNREADABLE", root)
            continue
        for child in sorted(children):
            path = child / "SKILL.md"
            try:
                if is_excluded(child) or is_excluded(path):
                    issue("EXCLUDED", child)
                    continue
                real = path.resolve()
                if is_excluded(real):
                    issue("EXCLUDED", child)
                    continue
                try:
                    info = real.stat()
                except (FileNotFoundError, NotADirectoryError):
                    continue
                if not stat.S_ISREG(info.st_mode):
                    issue("SKILL_NOT_REGULAR", path)
                    continue
                if real in seen:
                    alias = str(path)
                    if alias not in seen[real]["aliases"]:
                        seen[real]["aliases"].append(alias)
                    continue
                if len(records) >= MAX_SKILL_ENTRIES or info.st_size > MAX_SKILL_BYTES:
                    issue("SKILL_LIMIT", path)
                    continue
                with real.open("rb") as stream:
                    raw = stream.read(MAX_SKILL_BYTES + 1)
                if len(raw) > MAX_SKILL_BYTES:
                    issue("SKILL_LIMIT", path)
                    continue
                try:
                    metadata = _skill_metadata(raw)
                except UnicodeError:
                    issue("SKILL_UNREADABLE", path)
                    continue
                except (ValueError, TypeError):
                    issue("SKILL_METADATA_INVALID", path)
                    continue
                record = dict(metadata, canonical_name=metadata["name"], origin="filesystem",
                              path=str(real), resource_uri=None, root=str(root), aliases=[str(path)],
                              sha256=hashlib.sha256(raw).hexdigest())
                records.append(record)
                seen[real] = record
            except (OSError, UnicodeError, RuntimeError):
                issue("SKILL_UNREADABLE", path)
    if host_skills is not None:
        if (not isinstance(host_skills, dict) or host_skills.get("schema_version") != 1
                or not isinstance(host_skills.get("host_ref"), str) or not host_skills["host_ref"].strip()
                or not isinstance(host_skills.get("skills"), list)
                or len(host_skills["skills"]) > MAX_SKILL_ENTRIES
                or not isinstance(host_skills.get("evidence"), list) or not host_skills["evidence"]
                or any(not isinstance(e, str) or not e.strip() for e in host_skills["evidence"])):
            raise ValueError("Invalid trusted host skill snapshot")
        try:
            instant(host_skills["observed_at"])
        except (ValueError, TypeError, KeyError, AttributeError):
            raise ValueError("Invalid host observation time") from None
        manifest_digest = digest(host_skills)
        names, uris = set(), {}
        for item in host_skills["skills"]:
            if (not isinstance(item, dict)
                    or any(not isinstance(item.get(k), str) or not item[k].strip()
                           for k in ("name", "canonical_name", "description", "uri"))
                    or not SKILL_NAME.fullmatch(item["name"])
                    or not SKILL_NAME.fullmatch(item["canonical_name"])
                    or not re.fullmatch(r"[a-z][a-z0-9+.-]*://[^\s]+", item["uri"])
                    or item["name"] in names
                    or (item["uri"] in uris and uris[item["uri"]] != item["canonical_name"])):
                raise ValueError("Invalid or ambiguous host skill identity")
            names.add(item["name"])
            uris[item["uri"]] = item["canonical_name"]
            records.append({"name": item["name"], "canonical_name": item["canonical_name"],
                            "description": item["description"], "origin": "host", "path": None,
                            "resource_uri": item["uri"], "sha256": None, "host_ref": host_skills["host_ref"],
                            "observed_at": host_skills["observed_at"], "manifest_digest": manifest_digest,
                            "evidence": list(host_skills["evidence"]), "aliases": []})
    catalog = _SkillCatalog()
    for record in records:
        name = record["name"]
        if name not in catalog:
            catalog[name] = dict(record, alternatives=[])
        else:
            catalog[name]["alternatives"].append(record)
    result = {"schema_version": 1, "status": "incomplete" if issues else "complete",
              "scope": "explicit flat roots and supplied host snapshot only", "roots": root_rows,
              "host_snapshot_supplied": host_skills is not None, "records": records,
              "catalog": catalog, "issues": issues, "hash_scope": "SKILL.md bytes only",
              "package_evaluated": False, "behavior_evaluated": False}
    result["inventory_digest"] = digest(result)
    catalog.discovery = {k: result[k] for k in ("inventory_digest", "status", "roots", "issues", "scope")}
    return result


def discover_skills(roots, exclude_roots=(), host_skills=None):
    return skill_inventory(roots, exclude_roots, host_skills)["catalog"]


def candidate_inventory(exclude_roots=(), host_skills=None):
    """Bind metadata to an intact local bundle, not a split installed cache.

    The receipt is trusted local input, NOT a signature or installation grant.
    Only discovery inputs are checked here; full package verification belongs
    to plugin_bundle.verify_bundle. Explicit roots never enter this path.
    """
    suffix = ("plugins", "SimonKCore", "skills", "vibe", "scripts")
    if tuple(SCRIPT_ROOT.parts[-5:]) != suffix:
        return None
    base = SCRIPT_ROOT.parents[4]
    owners = ("SimonKCore", "SimonKAIHub", "SimonKDesign", "SimonKMarket", "SimonKStack")
    exclusions = [Path(p).expanduser().absolute() for p in exclude_roots]
    exclusions += [p.resolve() for p in exclusions]

    def local(member):
        path = base / member
        # Check every component before reading metadata (including junctions).
        for part in (path, *path.parents):
            if part == base:
                break
            if any(part == p or part.is_relative_to(p) for p in exclusions):
                raise ValueError("Candidate discovery intersects an excluded path")
            if part.is_symlink() or part.resolve() != part:
                raise ValueError("Candidate discovery does not follow links")
        return path

    def raw(member, limit):
        with local(member).open("rb") as stream:
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError("Candidate discovery input too large")
        return data

    def decode(data):
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("Duplicate candidate JSON key")
                result[key] = value
            return result
        def nonfinite(value):
            raise ValueError("Nonfinite candidate JSON value")
        return json.loads(data.decode("utf-8"), object_pairs_hook=unique, parse_constant=nonfinite)

    receipt_bytes = raw("bundle.json", 8 * 1024 * 1024)
    receipt = decode(receipt_bytes)
    scopes = {1: "five-plugin-candidate-v1", 2: "five-plugin-candidate-safety-v2"}
    if (not isinstance(receipt, dict) or type(receipt.get("schema_version")) is not int
            or receipt["schema_version"] not in scopes
            or receipt.get("scope") != scopes[receipt["schema_version"]]
            or not isinstance(receipt.get("inputs"), dict)
            or not isinstance(receipt["inputs"].get("plugins"), dict)
            or set(receipt["inputs"]["plugins"]) != set(owners)
            or not isinstance(receipt.get("owners"), dict)
            or receipt["owners"].get("vibe") != "SimonKCore"
            or not isinstance(receipt.get("files"), list)
            or not 1 <= len(receipt["files"]) <= MAX_SKILL_ENTRIES):
        raise ValueError("Invalid candidate discovery receipt")
    members = {}
    for row in receipt["files"]:
        if (not isinstance(row, dict) or not isinstance(row.get("path"), str)
                or row["path"] in members or type(row.get("size")) is not int
                or not 0 <= row["size"] <= 8 * 1024 * 1024
                or not isinstance(row.get("sha256"), str)
                or not re.fullmatch(r"[a-f0-9]{64}", row["sha256"])):
            raise ValueError("Invalid candidate discovery member")
        members[row["path"]] = row

    def checked(member):
        expected = members[member]
        data = raw(member, MAX_SKILL_BYTES)
        if len(data) != expected["size"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
            raise ValueError("Candidate discovery member drift")
        return data

    checked("plugins/SimonKCore/skills/vibe/scripts/orchestrate.py")
    expected_skills, roots = {}, []
    for name, owner in receipt["owners"].items():
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", name) or owner not in owners:
            raise ValueError("Invalid candidate skill ownership")
        member = f"plugins/{owner}/skills/{name}/SKILL.md"
        expected_skills[str(local(member))] = (name, members[member]["sha256"])
    for owner in owners:
        names = {n for n, o in receipt["owners"].items() if o == owner}
        manifest = decode(checked(f"plugins/{owner}/.claude-plugin/plugin.json"))
        if (not isinstance(manifest, dict) or not isinstance(manifest.get("skills"), list)
                or any(not isinstance(s, str) for s in manifest["skills"])
                or sorted(manifest["skills"]) != sorted(f"./skills/{n}/" for n in names)):
            raise ValueError("Candidate manifest membership mismatch")
        root = local(f"plugins/{owner}/skills")
        children = list(islice(root.iterdir(), MAX_SKILL_ENTRIES + 1))
        if len(children) > MAX_SKILL_ENTRIES or {p.name for p in children} != names:
            raise ValueError("Candidate physical skill membership mismatch")
        roots.append(root)
    inventory = skill_inventory(roots, exclude_roots, host_skills)
    actual = {r["path"]: (r["name"], r["sha256"]) for r in inventory["records"] if r["origin"] == "filesystem"}
    if inventory["status"] != "complete" or actual != expected_skills:
        raise ValueError("Candidate skill metadata differs from receipt")
    inventory["catalog"].discovery["bundle"] = {
        "path": str(base / "bundle.json"), "sha256": hashlib.sha256(receipt_bytes).hexdigest(),
        "scope": receipt["scope"], "hash_scope": "planner, plugin manifests and SKILL.md only",
        "installation_verified": False,
    }
    return inventory


def skill_coverage(source, installed, plugins=None):
    """Compare selected metadata, not behavior or scripts/assets integrity."""
    rows = []
    for name in sorted(source["catalog"]):
        expected = [r for r in source["records"] if r["name"] == name]
        selected = installed["catalog"].get(name)
        if len(expected) != 1:
            state = "ambiguous_source"
        elif selected is None:
            state = "missing"
        elif selected["origin"] == "host":
            state = "host_only"
        else:
            state = "matched" if selected["sha256"] == expected[0]["sha256"] else "drifted"
        homes = [r for r in (plugins or {}).get("records", []) if r["name"] == name]
        home_state = "not_checked" if plugins is None else ("missing" if not homes else "single" if len(homes) == 1 else "duplicate")
        rows.append({"name": name, "source_paths": [r["path"] for r in expected],
                     "selected_path": selected["path"] if selected else None, "installation": state,
                     "plugin_home": home_state, "plugin_paths": [r["path"] for r in homes],
                     "plugin_content": ("not_checked" if plugins is None else "matched" if len(expected) == 1 and len(homes) == 1
                                        and homes[0]["sha256"] == expected[0]["sha256"] else "not_matched"),
                     "modes": {mode: {"status": "not_evaluated", "quality": None, "actual_usd": None,
                                      "latency_ms": None} for mode in ("economy", "balanced", "quality")}})
    scopes = {"source": source, "installed": installed, "plugins": plugins}
    complete = all(i is None or i["status"] == "complete" for i in scopes.values())
    gaps = (not rows or not complete or any(r["installation"] != "matched" or
            (plugins is not None and (r["plugin_home"] != "single" or r["plugin_content"] != "matched")) for r in rows))
    return {"schema_version": 1, "status": "gaps" if gaps else "metadata_matched", "scope_complete": complete,
            "hash_scope": "SKILL.md bytes only", "optimization_complete": False, "package_evaluated": False,
            "behavior_evaluated": False, "inventories": scopes, "rows": rows,
            "extra_installed": sorted(set(installed["catalog"]) - set(source["catalog"])),
            "extra_plugin": sorted(set((plugins or {}).get("catalog", {})) - set(source["catalog"]))}


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
    for binding in step.get("skill_bindings", []):
        if binding.get("origin") != "host":
            continue
        if c.get("transport") != "host":
            errors.append("HOST_SKILL_REQUIRES_HOST")
        if c.get("host_ref") != binding["host_ref"]:
            errors.append("HOST_SKILL_CONTEXT_MISMATCH")
        if not fresh(binding["observed_at"], now):
            errors.append("HOST_SKILL_STALE")
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
    ancestor_names = {"vibe", *ancestors}
    ancestor_names.update(catalog[a].get("canonical_name", a) for a in list(ancestor_names) if a in catalog)
    ancestor_locations = {catalog[a].get("resource_uri") or catalog[a].get("path")
                          for a in ancestor_names if a in catalog}
    ancestor_locations.discard(None)
    for s in nodes:
        errors, rejected, choices = [], [], []
        s["route"], s["handoff"] = None, None
        s["skill_paths"] = []
        s["skill_bindings"] = []
        if s.get("kind") not in ("local", "llm", "gui") or s.get("demand", "routine") not in DEMAND_TIER:
            raise ValueError("Invalid step kind or demand")
        for name in s.get("skills", []):
            item = catalog.get(name)
            if (name in ancestor_names or (item and (item.get("canonical_name", name) in ancestor_names
                    or (item.get("resource_uri") or item.get("path")) in ancestor_locations))):
                errors.append("RECURSIVE_SKILL")
            elif name not in catalog:
                errors.append("SKILL_NOT_FOUND:" + name)
            else:
                binding = {k: copy.deepcopy(item[k]) for k in
                           ("name", "canonical_name", "origin", "path", "resource_uri", "sha256",
                            "host_ref", "observed_at", "manifest_digest", "evidence") if k in item}
                s["skill_bindings"].append(binding)
                if item["path"] is not None:
                    s["skill_paths"].append(item["path"])
                if item.get("origin") == "host" and s["kind"] != "llm":
                    errors.append("HOST_SKILL_REQUIRES_HOST")
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
                                "reuse_coordinator": any(b.get("canonical_name", b.get("name")) in ORCHESTRATORS
                                                         for b in s["skill_bindings"])}
                host_bindings = [b for b in s["skill_bindings"] if b.get("origin") == "host"]
                if host_bindings:
                    s["handoff"]["host_skills"] = copy.deepcopy(host_bindings)
                    s["route"]["valid_until"] = min([instant(s["route"]["valid_until"])] +
                        [instant(b["observed_at"]) + timedelta(seconds=DEFAULT_TTL) for b in host_bindings]).isoformat()
                if s["kind"] == "gui":
                    s["handoff"].update({"mode": "console", "bot_id": c["bot_id"],
                                         "target": s["target"], "require_nonce_result": True})
        # Identity is immutable task intent. Refreshable host observation facts
        # live in the handoff/route, which the durable Store already separates.
        for binding in s["skill_bindings"]:
            if binding.get("origin") == "host":
                for field in ("observed_at", "manifest_digest", "evidence"):
                    binding.pop(field, None)
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
    if getattr(catalog, "discovery", None) is not None:
        result["discovery"] = copy.deepcopy(catalog.discovery)
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
    parser.add_argument("command", choices=("catalog", "inventory", "coverage", "plan", "ready", "verify-bot"))
    parser.add_argument("--root", action="append", default=[])
    parser.add_argument("--source-root", action="append", default=[])
    parser.add_argument("--plugin-root", action="append", default=[])
    parser.add_argument("--exclude-root", action="append", default=[])
    parser.add_argument("--host-skills", type=Path)
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
    def read(path):
        if path is None:
            raise ValueError("Required JSON input path missing")
        return json.loads(path.read_text(encoding="utf-8-sig"))
    try:
        inventory = None
        if args.command in ("catalog", "inventory", "coverage", "plan"):
            roots = args.root
            if args.command in ("inventory", "coverage"):
                if not args.root and not args.host_skills:
                    raise ValueError("Inventory and coverage require explicit --root or --host-skills")
            host = None
            if args.host_skills:
                def unique_keys(pairs):
                    result = {}
                    for key, value in pairs:
                        if key in result:
                            raise ValueError("Duplicate host snapshot key")
                        result[key] = value
                    return result
                with args.host_skills.open("rb") as stream:
                    raw = stream.read(MAX_SKILL_BYTES + 1)
                if len(raw) > MAX_SKILL_BYTES:
                    raise ValueError("Host skill snapshot too large")
                host = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique_keys)
            if not roots and args.command in ("catalog", "plan"):
                inventory = candidate_inventory(args.exclude_root, host)
                if inventory is None:
                    roots = [SCRIPT_ROOT.parent.parent, Path.home() / ".agents" / "skills",
                             Path.home() / ".codex" / "skills", Path.home() / ".claude" / "skills",
                             Path.home() / ".codex" / "skills" / ".system"]
            if inventory is None:
                inventory = skill_inventory(roots, args.exclude_root, host)
        if args.command == "catalog":
            result = inventory["catalog"]
        elif args.command == "inventory":
            result = inventory
        elif args.command == "coverage":
            if not args.source_root:
                raise ValueError("Coverage requires explicit --source-root")
            result = skill_coverage(skill_inventory(args.source_root, args.exclude_root), inventory,
                                    skill_inventory(args.plugin_root, args.exclude_root) if args.plugin_root else None)
        elif args.command == "plan":
            result = make_plan(read(args.input), inventory["catalog"], read(args.runtime), args.now,
                               load_registry(args.registry) if args.registry else None)
        elif args.command == "ready":
            result = ready_steps(read(args.input), read(args.events) if args.events else [], args.now)
        else:
            if not all((args.bot_root, args.meta, args.result, args.nonce)):
                raise ValueError("verify-bot requires --bot-root, --meta, --result, --nonce")
            result = {"findings": verify_bot_result(args.bot_root, args.meta, args.result, args.nonce, args.evidence)}
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 2 if ((args.command == "catalog" and inventory["status"] == "incomplete") or
                     (isinstance(result, dict) and (result.get("status") in ("blocked", "incomplete", "gaps")
                                                  or result.get("findings")))) else 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
