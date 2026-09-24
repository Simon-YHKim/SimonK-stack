#!/usr/bin/env python3
"""Local durable dispatch intents and budget reservations; never sends tasks.

All cooperating dispatchers must use the same DB on one local filesystem.
This is not a provider billing cap, credential store or exactly-once transport.
Plans/observations/receipts come from the trusted coordinator, not raw workers.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sqlite3
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import orchestrate
import model_registry
from ledger import scan_secrets, _is_sensitive_key

SCALE = 1_000_000_000
MAX_USD = Decimal("1000000")
ACTIVE = {"intent", "running", "uncertain"}
TERMINAL = {"succeeded", "failed", "not_started", "rejected"}
SCHEMA = (
    "CREATE TABLE grant_policy (id INTEGER PRIMARY KEY CHECK(id=1), cap INTEGER NOT NULL CHECK(cap>=0), approval TEXT NOT NULL, parallel INTEGER NOT NULL)",
    "CREATE TABLE accounts (account_key TEXT PRIMARY KEY, surface TEXT NOT NULL, account_ref TEXT NOT NULL, parallel INTEGER NOT NULL)",
    "CREATE TABLE runs (run_id TEXT PRIMARY KEY, plan_digest TEXT NOT NULL, spec_digest TEXT NOT NULL, plan TEXT NOT NULL, cap INTEGER NOT NULL, prior_spent INTEGER NOT NULL, prior_held INTEGER NOT NULL, closed INTEGER NOT NULL DEFAULT 0)",
    "CREATE TABLE nodes (run_id TEXT NOT NULL REFERENCES runs, node_id TEXT NOT NULL, account_key TEXT NOT NULL REFERENCES accounts, per_attempt INTEGER NOT NULL CHECK(per_attempt>=0), remaining INTEGER NOT NULL CHECK(remaining>=0), PRIMARY KEY(run_id,node_id))",
    "CREATE TABLE attempts (dispatch_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs, node_id TEXT NOT NULL, attempt INTEGER NOT NULL, request_id TEXT NOT NULL, plan_digest TEXT NOT NULL, account_key TEXT NOT NULL REFERENCES accounts, route TEXT NOT NULL, state TEXT NOT NULL, reserved INTEGER NOT NULL CHECK(reserved>=0), actual INTEGER CHECK(actual>=0), handle TEXT, proof TEXT, verified INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, observed_at TEXT NOT NULL, UNIQUE(run_id,request_id), UNIQUE(run_id,node_id,attempt), FOREIGN KEY(run_id,node_id) REFERENCES nodes)",
    "CREATE TABLE events (seq INTEGER PRIMARY KEY, run_id TEXT, dispatch_id TEXT, kind TEXT NOT NULL, at TEXT NOT NULL, payload TEXT NOT NULL)",
)
PREPARATIONS_SCHEMA = "CREATE TABLE preparations (run_id TEXT PRIMARY KEY, draft_digest TEXT NOT NULL, draft TEXT NOT NULL, caller TEXT NOT NULL, ops TEXT NOT NULL, state TEXT NOT NULL, cap INTEGER NOT NULL CHECK(cap>=0), held INTEGER NOT NULL CHECK(held>=0), spent INTEGER NOT NULL CHECK(spent>=0), prior_unknown INTEGER NOT NULL, final_plan TEXT)"
PREPARATION_REFRESH_SCHEMA = "CREATE TABLE preparation_validations (run_id TEXT PRIMARY KEY REFERENCES preparations, plan TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0), proof TEXT NOT NULL)"


class StateError(ValueError):
    def __init__(self, code):
        super().__init__(code)  # Never echo rejected payloads or DB/provider errors.
        self.code = code


def nano(value, ceiling=True):
    if isinstance(value, bool) or value is None:
        raise StateError("INVALID_MONEY")
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or not 0 <= amount <= MAX_USD:
            raise StateError("INVALID_MONEY")
        if not amount:
            return 0
        _, digits, exponent = amount.as_tuple()
        if len(digits) > 128:
            raise StateError("INVALID_MONEY")
        # Work on the exact coefficient: Decimal's ambient precision could
        # otherwise erase a small positive fraction or underflow a tiny value.
        shift = exponent + 9
        if shift < -len(digits):
            return int(ceiling)
        coefficient = int("".join(map(str, digits)))
        if shift >= 0:
            return coefficient * 10 ** shift
        whole, fraction = divmod(coefficient, 10 ** -shift)
        return whole + int(ceiling and bool(fraction))
    except (ValueError, TypeError, InvalidOperation):
        raise StateError("INVALID_MONEY") from None


def usd(value):
    return format(Decimal(value) / SCALE, "f").rstrip("0").rstrip(".") if value % SCALE else str(value // SCALE)


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}", value):
        raise StateError("INVALID_IDENTIFIER")
    return value


def strict_loads(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise StateError("DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    def constant(_):
        raise StateError("INVALID_JSON_NUMBER")

    def number(value):
        result = float(value)
        if not math.isfinite(result):
            raise StateError("INVALID_JSON_NUMBER")
        # Monetary fields may be strings for exact decimals. Reject lossy JSON
        # numbers instead of silently turning a charge into zero or raising a cap.
        if Decimal(str(result)) != Decimal(value):
            raise StateError("LOSSY_JSON_NUMBER")
        return result

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant, parse_float=number)


def safe_json(value):
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, RecursionError):
        raise StateError("INVALID_PAYLOAD") from None
    if len(text.encode("utf-8")) > 1024 * 1024:
        raise StateError("PAYLOAD_TOO_LARGE")
    if scan_secrets(text):
        raise StateError("SENSITIVE_PAYLOAD")
    count = 0

    def inspect(item, depth=0):
        nonlocal count
        count += 1
        if depth > 16 or count > 20000:
            raise StateError("PAYLOAD_STRUCTURE_LIMIT")
        if isinstance(item, dict):
            for key, val in item.items():
                if not isinstance(key, str):
                    raise StateError("INVALID_PAYLOAD")
                if _is_sensitive_key(key):
                    raise StateError("SENSITIVE_PAYLOAD")
                inspect(val, depth + 1)
        elif isinstance(item, list):
            for val in item:
                inspect(val, depth + 1)
        elif isinstance(item, str) and item.lstrip()[:1] in {"{", "[", '"'}:
            # Embedded structured data may hide compound credential keys. Never
            # skip it because it is too large, deeply nested, or malformed.
            if len(item.encode("utf-8")) > 65536:
                raise StateError("EMBEDDED_JSON_LIMIT")
            try:
                decoded = strict_loads(item)
            except (ValueError, RecursionError):
                raise StateError("EMBEDDED_JSON_INVALID") from None
            inspect(decoded, depth + 1)
    inspect(value)
    return text


def moment(now=None):
    now = now or datetime.now(timezone.utc).isoformat()
    try:
        orchestrate.instant(now)
    except (ValueError, TypeError, AttributeError):
        raise StateError("INVALID_TIME") from None
    return now


def evidence(value):
    if not isinstance(value, list) or not value or any(not isinstance(v, str) or not v.strip() for v in value):
        raise StateError("EVIDENCE_REQUIRED")
    safe_json(value)
    return value


def spec_digest(plan):
    # Route evidence can refresh; task intent, review dependencies and policy cannot.
    nodes = [{k: v for k, v in n.items() if k not in
              {"route", "handoff", "errors", "rejected_candidates", "skill_paths"}} for n in plan["steps"]]
    return orchestrate.digest({"steps": nodes, "budget": {k: plan["budget"][k] for k in
        ("mode", "approved_usd", "spent_usd", "external_reserved_usd", "max_attempts", "max_parallel")}})


def task_spec(node):
    """The same immutable Task text is used by preparation and dispatch."""
    body = {k: v for k, v in node.items() if k not in
            {"orca", "route", "errors", "rejected_candidates"}}
    return "Vibe supervised task. Read the selected skills; obey ownership and acceptance.\n" + safe_json(body)


OBSERVABLE_PREPARATION = "observable-local-orca-preparation-v2"


def preparation_caller(caller):
    legacy = {"handle", "identity_sha256"}
    if not isinstance(caller, dict) or set(caller) not in (legacy, legacy | {"contract", "approval_ref"}):
        raise StateError("EXACT_PREPARATION_CALLER_REQUIRED")
    if "contract" in caller:
        if caller["contract"] != OBSERVABLE_PREPARATION:
            raise StateError("EXACT_PREPARATION_CALLER_REQUIRED")
        identifier(caller["approval_ref"])
    identifier(caller["handle"])
    if not isinstance(caller["identity_sha256"], str) or not re.fullmatch("[0-9a-f]{64}", caller["identity_sha256"]):
        raise StateError("EXACT_PREPARATION_CALLER_REQUIRED")
    return safe_json(caller)


def preparation_argv(plan, caller, key, native_ids):
    """Pure canonical payload projection, also used for admission sizing."""
    preparation_caller(caller)
    origin = [] if caller.get("contract") == OBSERVABLE_PREPARATION else ["--from", caller["handle"]]
    marker = "vibe-preparation:" + plan["plan_digest"]
    if key == "run":
        return ["orchestration", "run-create", "--objective", marker, *origin]
    nodes = [n for n in plan["steps"] if "task:" + n["id"] == key]
    if len(nodes) != 1:
        raise StateError("PREPARATION_OPERATION_UNKNOWN")
    node = nodes[0]
    try:
        return ["orchestration", "task-create", "--spec", task_spec(node), "--task-title", marker + ":" + node["id"],
            "--deps", safe_json([native_ids["task:" + d] for d in node["depends_on"]]),
            "--run", native_ids["run"], *origin]
    except KeyError:
        raise StateError("PREPARATION_DEPENDENCY_UNBOUND") from None


def preparation_capacity(plan, caller):
    # Admission uses worst-length IDs/escaping and one bounded proof per op;
    # native effects must not precede a deterministic journal-size failure.
    keys = ["run", *["task:" + n["id"] for n in plan["steps"]]]
    if len(keys) > 33:
        raise StateError("PREPARATION_SIZE_LIMIT")
    ids = {key: ":" * 160 for key in keys}
    safe_json(preparation_projection(plan, ids))
    largest = {}
    for key in keys:
        argv = preparation_argv(plan, caller, key, ids) + ["--retry-request", "0" * 36, "--json"]
        largest[key] = {"request_id": "0" * 36, "argv": argv, "operation_sha256": "0" * 64,
            "state": "uncertain", "native_id": ":" * 160, "proof": "p" * 4096}
    # More conservative than the 1MiB storage cap, with ample event overhead.
    if len(safe_json(largest).encode("utf-8")) > 768 * 1024:
        raise StateError("PREPARATION_SIZE_LIMIT")


def preparation_projection(plan, native_ids):
    result = json.loads(safe_json(plan))
    for node in result["steps"]:
        node["orca"].update(run_id=native_ids["run"], task_id=native_ids["task:" + node["id"]])
    result["plan_digest"] = orchestrate.digest({k: v for k, v in result.items() if k != "plan_digest"})
    return result


def preparation_proof(proof):
    if not isinstance(proof, dict) or len(safe_json(proof).encode("utf-8")) > 4096:
        raise StateError("PREPARATION_PROOF_SIZE_LIMIT")
    evidence(proof.get("evidence"))


def preparation_semantics(plan):
    """Only these existing timestamp leaves may differ; retain every other byte.

    Registry identity, numeric types, diagnostics, route selection and unknown
    extensions are intentionally frozen. This is narrower than spec_digest.
    """
    value = json.loads(safe_json(plan))
    try:
        for key in ("planned_at", "plan_digest"):
            value[key]  # Missing paths must not be added by masking.
            value[key] = None
        for node in value["steps"]:
            for key in ("runtime_observed_at", "valid_until"):
                node["route"][key]
                node["route"][key] = None
            node["route"]["quota"]["observed_at"]
            node["route"]["quota"]["observed_at"] = None
    except (KeyError, TypeError):
        raise StateError("PREPARATION_VALIDATION_SHAPE") from None
    return safe_json(value)


def validate_preparation_freshness(plan, now):
    """Bound visible evidence; omitted alias/access proofs remain host-owned."""
    validate_plan(plan, now)
    if any(n.get("handoff", {}).get("host_skills") or
           any(b.get("origin") == "host" for b in n.get("skill_bindings", [])) for n in plan["steps"]):
        # The central planner only permits host-native skills on host routes.
        # Reject unsupported hand-built combinations instead of renewing them.
        raise StateError("PREPARATION_HOST_SKILL_UNSUPPORTED")
    try:
        checked = plan["model_registry"]["checked_at"]
        registry_expiry = model_registry.timestamp(checked) + timedelta(seconds=model_registry.MAX_FACT_AGE_SECONDS)
        if not orchestrate.fresh(checked, now, model_registry.MAX_FACT_AGE_SECONDS):
            raise ValueError("Registry expired")
        for node in plan["steps"]:
            route = node["route"]
            maximum = min(registry_expiry, *[
                model_registry.timestamp(t) + timedelta(seconds=model_registry.RUNTIME_TTL_SECONDS)
                for t in (route["runtime_observed_at"], route["quota"]["observed_at"])])
            if not model_registry.timestamp(now) < model_registry.timestamp(route["valid_until"]) <= maximum:
                raise ValueError("Unbounded expiry")
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError):
        raise StateError("PREPARATION_EVIDENCE_EXPIRED") from None


def native_binding(node):
    binding = node.get("orca")
    if isinstance(binding, dict):
        return binding  # Retain historical ID ownership across route refresh.
    if node["route"].get("transport") == "orca":
        raise StateError("EXACT_ORCA_BINDING_REQUIRED")
    return {}  # Generic nodes historically allow absent/null extra metadata.


def validate_plan(plan, now):
    safe_json(plan)
    try:
        identifier(plan["run_id"])
        if plan["status"] != "ready" or plan.get("errors") or not plan["steps"]:
            raise StateError("PLAN_BLOCKED")
        if plan["plan_digest"] != orchestrate.digest({k: v for k, v in plan.items() if k != "plan_digest"}):
            raise StateError("PLAN_CHANGED")
        if not orchestrate.ready_steps(plan, [], now):
            raise StateError("PLAN_STALE_OR_BLOCKED")
        for node in plan["steps"]:
            identifier(node["id"])
            route = node["route"]
            nano(route["reserved_upper_usd"])
            if route["surface"] != "local":
                billing = route["billing"]
                if billing.get("verified") is not True:
                    raise StateError("BILLING_UNVERIFIED")
                identifier(billing["account_ref"])
        for key in ("max_attempts", "max_parallel"):
            if type(plan["budget"][key]) is not int or not 1 <= plan["budget"][key] <= 8:
                raise StateError("INVALID_POLICY")
        for key in ("approved_usd", "spent_usd", "external_reserved_usd"):
            nano(plan["budget"][key])
    except StateError:
        raise
    except (ValueError, KeyError, TypeError, AttributeError):
        raise StateError("INVALID_PLAN") from None


class Store:
    def __init__(self, path, timeout=2):
        original = Path(path).expanduser()
        if str(path) == ":memory:" or original.is_symlink():
            raise StateError("LOCAL_DURABLE_PATH_REQUIRED")
        self.path, self.timeout = original.resolve(), timeout
        if str(self.path).startswith("\\\\"):
            raise StateError("LOCAL_DURABLE_PATH_REQUIRED")
        if os.name == "nt":
            import ctypes
            if ctypes.windll.kernel32.GetDriveTypeW(str(self.path.anchor)) != 3:
                raise StateError("LOCAL_DURABLE_PATH_REQUIRED")

    @contextmanager
    def _transaction(self, new=False):
        db = None
        try:
            db = sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True,
                                 isolation_level=None, timeout=self.timeout)
            db.row_factory = sqlite3.Row
            if not new and db.execute("PRAGMA user_version").fetchone()[0] not in {1, 2, 3}:
                raise StateError("SCHEMA_UNSUPPORTED")
            if db.execute("PRAGMA journal_mode").fetchone()[0] != "delete":
                raise StateError("JOURNAL_UNSUPPORTED")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except sqlite3.Error:
            raise StateError("STATE_DB_UNAVAILABLE") from None
        finally:
            if db is not None:
                if db.in_transaction:
                    db.rollback()
                db.close()

    def initialize(self, approved_usd=0, approval_ref="user-zero-additional-budget", max_parallel=2):
        cap = nano(approved_usd, ceiling=False)
        evidence([approval_ref])
        if type(max_parallel) is not int or not 1 <= max_parallel <= 8:
            raise StateError("INVALID_POLICY")
        if cap and approval_ref == "user-zero-additional-budget":
            raise StateError("APPROVAL_REQUIRED")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            with self._transaction() as db:
                grant = self._one(db, "SELECT * FROM grant_policy WHERE id=1")
                if (grant["cap"], grant["approval"], grant["parallel"]) != (cap, approval_ref, max_parallel):
                    raise StateError("GRANT_IMMUTABLE")
            return
        os.close(fd)
        with self._transaction(new=True) as db:
            for statement in SCHEMA:
                db.execute(statement)
            db.execute("INSERT INTO grant_policy VALUES(1,?,?,?)", (cap, approval_ref, max_parallel))
            db.execute("PRAGMA user_version=1")
            self._event(db, None, None, "initialized", moment(), {"approved_usd": usd(cap)})

    def upgrade_preparations(self, approval_ref, now=None):
        """Explicit additive migration; never changes the immutable grant.

        This is not called by initialize/dispatch. Quiesce old coordinators and
        review a backup before migrating an operational DB. Old v1 code rejects
        v2 instead of ignoring preparation reservations.
        """
        evidence([approval_ref])
        with self._transaction() as db:
            if db.execute("PRAGMA user_version").fetchone()[0] in {2, 3}:
                return
            db.execute(PREPARATIONS_SCHEMA)
            db.execute("PRAGMA user_version=2")
            self._event(db, None, None, "preparation_schema_upgraded", moment(now), {"evidence": [approval_ref]})

    def upgrade_preparation_refresh(self, approval_ref, now=None):
        """Explicit v2->v3 only. Quiesce readers and review a DB backup first.

        Old v2 readers reject v3. No reservations/operations are migrated or
        released; operational migration is not an automatic recovery action.
        """
        evidence([approval_ref])
        with self._transaction() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version == 3:
                return
            if version != 2:
                raise StateError("PREPARATION_SCHEMA_REQUIRED")
            db.execute(PREPARATION_REFRESH_SCHEMA)
            db.execute("PRAGMA user_version=3")
            self._event(db, None, None, "preparation_refresh_schema_upgraded", moment(now), {"evidence": [approval_ref]})

    @staticmethod
    def _preparations(db):
        if db.execute("PRAGMA user_version").fetchone()[0] == 1:
            return []
        return [dict(r) for r in db.execute("SELECT * FROM preparations ORDER BY run_id")]

    def _preparation(self, db, run, caller=None):
        if db.execute("PRAGMA user_version").fetchone()[0] not in {2, 3}:
            raise StateError("PREPARATION_SCHEMA_REQUIRED")
        row = self._one(db, "SELECT * FROM preparations WHERE run_id=?", (identifier(run),))
        if caller is not None and preparation_caller(caller) != row["caller"]:
            raise StateError("PREPARATION_CALLER_CHANGED")
        return row, json.loads(row["draft"]), json.loads(row["ops"])

    @staticmethod
    def _preparation_validation(db, row):
        saved = (db.execute("SELECT * FROM preparation_validations WHERE run_id=?", (row["run_id"],)).fetchone()
                 if db.execute("PRAGMA user_version").fetchone()[0] == 3 else None)
        return {"plan": json.loads(saved["plan"] if saved else row["draft"]),
                "revision": saved["revision"] if saved else 0, "proof": saved["proof"] if saved else None}

    def preparation_validation(self, run, caller):
        with self._transaction() as db:
            row, _, _ = self._preparation(db, run, caller)
            validation = self._preparation_validation(db, row)
            return {k: validation[k] for k in ("plan", "revision")}

    def renew_preparation(self, run, plan, caller, proof, now=None):
        """Persist trusted planner observations, never mutate native intent/state.

        Callers must rerun the central planner with fresh runtime/quota and all
        alias/access/cost evidence. A JSON claim is not independent attestation.
        """
        now = moment(now)
        with self._transaction() as db:
            if db.execute("PRAGMA user_version").fetchone()[0] != 3:
                raise StateError("PREPARATION_REFRESH_SCHEMA_REQUIRED")
            row, draft, _ = self._preparation(db, run, caller)
            if row["state"] == "registered":
                raise StateError("PREPARATION_ALREADY_REGISTERED")
            current = self._preparation_validation(db, row)
            preparation_proof(proof)
            validate_preparation_freshness(plan, now)
            if preparation_semantics(plan) != preparation_semantics(draft):
                raise StateError("PREPARATION_INTENT_CHANGED")
            preparation_capacity(plan, caller)
            if (proof.get("verified") is not True or proof.get("runtime_revalidated") is not True or
                    proof.get("draft_digest") != row["draft_digest"] or
                    proof.get("validation_digest") != plan["plan_digest"] or
                    not orchestrate.fresh(proof.get("observed_at"), now) or
                    type(proof.get("previous_revision")) is not int):
                raise StateError("PREPARATION_REFRESH_PROOF_REQUIRED")
            self._budget_guard(db)
            # An exact retry of a committed renewal is safe and does not bump
            # revision. A different stale writer must lose the CAS below.
            if current["proof"] == safe_json(proof) and safe_json(current["plan"]) == safe_json(plan):
                return
            if (proof.get("previous_digest") != current["plan"]["plan_digest"] or
                    proof["previous_revision"] != current["revision"]):
                raise StateError("PREPARATION_VALIDATION_CHANGED")
            old = current["plan"]
            timestamps = [(old["planned_at"], plan["planned_at"])]
            for before, after in zip(old["steps"], plan["steps"]):
                timestamps.append((before["route"]["runtime_observed_at"], after["route"]["runtime_observed_at"]))
                timestamps.append((before["route"]["quota"]["observed_at"], after["route"]["quota"]["observed_at"]))
            if any(orchestrate.instant(after) < orchestrate.instant(before) for before, after in timestamps):
                raise StateError("PREPARATION_VALIDATION_DOWNGRADE")
            revision = current["revision"] + 1
            db.execute("INSERT INTO preparation_validations VALUES(?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET plan=excluded.plan,revision=excluded.revision,proof=excluded.proof",
                       (run, safe_json(plan), revision, safe_json(proof)))
            self._event(db, run, None, "preparation_renewed", now, {"draft_digest": row["draft_digest"],
                "previous_digest": old["plan_digest"], "validation_digest": plan["plan_digest"],
                "validation_revision": revision, "proof": proof})

    def _native_available(self, db, run, kind, native, node=None):
        """Conservative same-DB resource ownership, including closed history.

        Run owner=(logical run); Task owner=(logical run,node). Runtime namespaces
        are not inferred: even a cross-runtime identical native ID is fenced.
        """
        identifier(native)
        owner = (run, node if kind == "task" else None)
        for row in self._preparations(db):
            for key, op in json.loads(row["ops"]).items():
                other_kind = "run" if key == "run" else "task"
                other = (row["run_id"], key[5:] if other_kind == "task" else None)
                if other_kind == kind and op["native_id"] == native and other != owner:
                    raise StateError("NATIVE_RESOURCE_ALREADY_OWNED")
        for row in db.execute("SELECT run_id,plan FROM runs"):
            for n in json.loads(row["plan"])["steps"]:
                other = (row["run_id"], n["id"] if kind == "task" else None)
                if native_binding(n).get(kind + "_id") == native and other != owner:
                    raise StateError("NATIVE_RESOURCE_ALREADY_OWNED")

    @staticmethod
    def _bound_digest(row, ops):
        # Proof timestamps are observations, not operation identity.
        return orchestrate.digest({"draft": row["draft_digest"], "caller": json.loads(row["caller"]),
            "bindings": {k: {f: op[f] for f in ("operation_sha256", "native_id")} for k, op in ops.items()}})

    def preparation(self, run):
        with self._transaction() as db:
            row, _, ops = self._preparation(db, run)
            validation = self._preparation_validation(db, row)
            return {"run_id": row["run_id"], "draft_digest": row["draft_digest"], "state": row["state"],
                "validation_digest": validation["plan"]["plan_digest"], "validation_revision": validation["revision"],
                "held_usd": usd(row["held"]), "caller": json.loads(row["caller"]), "operations": ops,
                "bound_sha256": self._bound_digest(row, ops) if row["state"] in {"bound", "registered"} else None}

    def begin_preparation(self, plan, caller, now=None):
        """Reserve a complete unbound plan. No native access or send authority.

        Caller identity is trusted coordinator evidence of transport/runtime and
        its explicit trust contract, not authentication established by --from.
        """
        now, caller_text = moment(now), preparation_caller(caller)
        validate_plan(plan, now)
        try:
            orchestrate.ordered_steps(plan["steps"])
            if any(len(n["depends_on"]) != len(set(n["depends_on"])) for n in plan["steps"]):
                raise ValueError("Duplicate dependency")
        except (ValueError, TypeError, KeyError):
            raise StateError("INVALID_PREPARATION_DAG") from None
        shared, seen = None, set()
        pins = ("runtime_id", "app_version", "executable", "executable_sha256", "worktree_id",
                "worktree_path", "workspace_instance", "guards")
        for n in plan["steps"]:
            b = n.get("orca", {})
            if (n["id"] in seen or "run_id" in b or "task_id" in b or
                    n["route"].get("transport") != "orca" or n["route"]["surface"] not in {"claude", "codex"} or
                    any(k not in b for k in (*pins, "account_ref", "profile_ref"))):
                raise StateError("UNBOUND_ORCA_PLAN_REQUIRED")
            current = {k: b[k] for k in pins}
            if shared is not None and shared != current:
                raise StateError("PREPARATION_SCOPE_CHANGED")
            shared, seen = current, seen | {n["id"]}
        if any(d not in seen for n in plan["steps"] for d in n["depends_on"]):
            raise StateError("INVALID_PREPARATION_DAG")
        preparation_capacity(plan, caller)
        with self._transaction() as db:
            if db.execute("PRAGMA user_version").fetchone()[0] not in {2, 3}:
                raise StateError("PREPARATION_SCHEMA_REQUIRED")
            old = db.execute("SELECT * FROM preparations WHERE run_id=?", (plan["run_id"],)).fetchone()
            if old:
                if old["draft_digest"] != plan["plan_digest"] or old["caller"] != caller_text:
                    raise StateError("PREPARATION_IMMUTABLE")
                return
            if db.execute("SELECT 1 FROM runs WHERE run_id=?", (plan["run_id"],)).fetchone():
                raise StateError("RUN_ALREADY_EXISTS")
            grant = self._one(db, "SELECT * FROM grant_policy WHERE id=1")
            for other in self._preparations(db):
                previous = json.loads(other["caller"])
                if not any(previous[k] == caller[k] for k in ("handle", "identity_sha256")):
                    continue
                if (other["state"] != "registered" or
                        self._one(db, "SELECT closed FROM runs WHERE run_id=?", (other["run_id"],))["closed"] == 0):
                    raise StateError("PREPARATION_CALLER_BUSY")
            if sum(r["state"] != "registered" for r in self._preparations(db)) >= grant["parallel"]:
                raise StateError("PREPARATION_LIMIT")
            self._budget_guard(db)
            b, count = plan["budget"], plan["budget"]["max_attempts"]
            held = nano(b["external_reserved_usd"]) + sum(
                ((nano(n["route"]["reserved_upper_usd"]) + count - 1) // count) * count for n in plan["steps"])
            db.execute("INSERT INTO preparations VALUES(?,?,?,?,?,'preparing',?,?,?,?,NULL)",
                (plan["run_id"], plan["plan_digest"], safe_json(plan), caller_text, "{}",
                 nano(b["approved_usd"], ceiling=False), held, nano(b["spent_usd"]), int(bool(nano(b["external_reserved_usd"])))))
            self._budget_guard(db)
            self._event(db, plan["run_id"], None, "preparation_reserved", now, {"draft_digest": plan["plan_digest"]})

    def preparation_intent(self, run, key, caller, now=None):
        """Persist exact argv+UUID before a future adapter may send once.

        send_allowed is only a fresh journal claim, NOT native/billing/ownership
        authorization. This module never executes these arguments.
        """
        now = moment(now)
        with self._transaction() as db:
            row, plan, ops = self._preparation(db, run, caller)
            if key in ops:
                return {**ops[key], "send_allowed": False}
            if row["state"] != "preparing":
                raise StateError("PREPARATION_RECONCILIATION_REQUIRED")
            validation = self._preparation_validation(db, row)
            validate_plan(validation["plan"], now)
            if validation["revision"]:
                validate_preparation_freshness(validation["plan"], now)
            self._budget_guard(db)
            argv = preparation_argv(plan, caller, key, {k: op["native_id"] for k, op in ops.items() if op["state"] == "complete"})
            identity = orchestrate.digest({"draft": row["draft_digest"], "caller": caller, "key": key, "argv": argv})
            version = "v2" if caller.get("contract") == OBSERVABLE_PREPARATION else "v1"
            request = str(uuid.uuid5(uuid.NAMESPACE_URL, "simonk:vibe:orca:preparation:" + version + ":" + identity))
            argv += ["--retry-request", request, "--json"]
            op = {"request_id": request, "argv": argv, "operation_sha256": orchestrate.digest({
                "identity": identity, "argv": argv}), "state": "intent", "native_id": None, "proof": None}
            ops[key] = op
            db.execute("UPDATE preparations SET ops=? WHERE run_id=?", (safe_json(ops), run))
            self._event(db, run, None, "preparation_intent", now, {"key": key, "operation_sha256": op["operation_sha256"]})
            return {**op, "send_allowed": True, "validation_digest": validation["plan"]["plan_digest"],
                    "validation_revision": validation["revision"]}

    def observe_preparation(self, run, key, caller, proof, now=None):
        """Accept only coordinator-verified, exact request/resource readback.

        Raw native receipts require an adapter to check ownership, scope, spec,
        dependencies and caller fingerprint first. No such adapter ships here.
        """
        now = moment(now)
        preparation_proof(proof)
        if not orchestrate.fresh(proof.get("observed_at"), now):
            raise StateError("PREPARATION_PROOF_STALE")
        with self._transaction() as db:
            row, plan, ops = self._preparation(db, run, caller)
            if key not in ops or proof.get("operation_sha256") != ops[key]["operation_sha256"]:
                raise StateError("PREPARATION_PROOF_MISMATCH")
            op = ops[key]
            state = proof.get("state")
            if state == "complete":
                native = identifier(proof.get("native_id"))
                if (proof.get("verified") is not True or proof.get("non_generating") is not True or
                        nano(proof.get("actual_usd")) != 0):
                    raise StateError("PREPARATION_PROOF_REQUIRED")
                if op["native_id"] is not None and op["native_id"] != native:
                    raise StateError("PREPARATION_BINDING_CHANGED")
                if key != "run" and any(k != key and k != "run" and v["native_id"] == native for k, v in ops.items()):
                    raise StateError("PREPARATION_BINDING_DUPLICATE")
                self._native_available(db, run, "run" if key == "run" else "task", native,
                                       None if key == "run" else key[5:])
                op.update(state="complete", native_id=native, proof=proof)
            elif state == "unknown":
                if op["state"] != "complete":
                    op.update(state="uncertain", proof=proof)
            else:
                raise StateError("PREPARATION_PROOF_INVALID")
            if row["state"] == "registered":
                return  # Identity checked, immutable completed preparation.
            expected = {"run", *["task:" + n["id"] for n in plan["steps"]]}
            phase = ("bound" if set(ops) == expected and all(o["state"] == "complete" for o in ops.values()) else
                     "uncertain" if any(o["state"] == "uncertain" for o in ops.values()) else "preparing")
            db.execute("UPDATE preparations SET ops=?,state=? WHERE run_id=?", (safe_json(ops), phase, run))
            self._event(db, run, None, "preparation_observed", now, {"key": key, "state": state})

    def finalize_preparation(self, run, caller, proof, now=None):
        """Atomically transfer hold and project IDs into the current validation."""
        now = moment(now)
        preparation_proof(proof)
        with self._transaction() as db:
            row, plan, ops = self._preparation(db, run, caller)
            if row["state"] == "registered":
                return json.loads(row["final_plan"])
            validation = self._preparation_validation(db, row)
            if db.execute("PRAGMA user_version").fetchone()[0] == 3 and (
                    proof.get("validation_digest") != validation["plan"]["plan_digest"] or
                    type(proof.get("validation_revision")) is not int or
                    proof["validation_revision"] != validation["revision"]):
                raise StateError("PREPARATION_VALIDATION_CHANGED")
            if (row["state"] != "bound" or proof.get("bound_sha256") != self._bound_digest(row, ops) or
                    any(proof.get(k) is not True for k in ("verified", "scope_verified", "no_workers", "non_generating")) or
                    nano(proof.get("actual_usd")) != 0):
                raise StateError("PREPARATION_FINAL_PROOF_REQUIRED")
            evidence(proof.get("evidence"))
            if not orchestrate.fresh(proof.get("observed_at"), now):
                raise StateError("PREPARATION_PROOF_STALE")
            if validation["revision"]:
                validate_preparation_freshness(validation["plan"], now)
            plan = preparation_projection(validation["plan"], {key: op["native_id"] for key, op in ops.items()})
            validate_plan(plan, now)
            self._budget_guard(db)
            db.execute("UPDATE preparations SET state='registered',held=0,spent=0,prior_unknown=0,final_plan=? WHERE run_id=?",
                       (safe_json(plan), run))
            self._register(db, plan, now)
            self._event(db, run, None, "preparation_registered", now, {"proof": proof,
                "draft_digest": row["draft_digest"], "validation_digest": validation["plan"]["plan_digest"],
                "final_digest": plan["plan_digest"]})
            return plan

    @staticmethod
    def _one(db, sql, args=()):
        row = db.execute(sql, args).fetchone()
        if row is None:
            raise StateError("NOT_FOUND")
        return dict(row)

    @staticmethod
    def _event(db, run, dispatch, kind, now, payload):
        db.execute("INSERT INTO events(run_id,dispatch_id,kind,at,payload) VALUES(?,?,?,?,?)",
                   (run, dispatch, kind, now, safe_json(payload)))

    def _run(self, db, run):
        row = self._one(db, "SELECT * FROM runs WHERE run_id=?", (identifier(run),))
        if row["closed"]:
            raise StateError("RUN_CLOSED")
        return row, json.loads(row["plan"])

    def _attempts(self, db, run=None):
        rows = db.execute("SELECT * FROM attempts" + (" WHERE run_id=?" if run else "") + " ORDER BY attempt,dispatch_id",
                          (run,) if run else ())
        return [dict(row) for row in rows]

    def _totals(self, db, run=None):
        where, args = (" WHERE run_id=?", (run,)) if run else ("", ())
        held = sum(r[0] for r in db.execute("SELECT remaining FROM nodes" + where, args))
        spent, unknown, unsettled = 0, 0, 0
        for row in db.execute("SELECT prior_spent,prior_held FROM runs" + where, args):
            spent += row[0]
            held += row[1]
            unknown += bool(row[1])
        for a in self._attempts(db, run):
            if a["actual"] is None:
                held += a["reserved"]
                unknown += 1
                unsettled += a["state"] in TERMINAL
            else:
                spent += a["actual"]
        for row in self._preparations(db):
            if run is None or row["run_id"] == run:
                held += row["held"]
                spent += row["spent"]
                unknown += row["prior_unknown"]
                unknown += sum(op["state"] != "complete" for op in json.loads(row["ops"]).values())
        return spent, held, unknown, unsettled

    def _budget_guard(self, db):
        grant = self._one(db, "SELECT * FROM grant_policy WHERE id=1")
        spent, held, _, unresolved = self._totals(db)
        if spent + held > grant["cap"]:
            raise StateError("BUDGET_EXCEEDED")
        if unresolved:
            raise StateError("COST_UNRESOLVED")
        for row in db.execute("SELECT run_id,cap FROM runs"):
            s, h, _, _ = self._totals(db, row["run_id"])
            if s + h > row["cap"]:
                raise StateError("RUN_BUDGET_EXCEEDED")
        if any(r["held"] + r["spent"] > r["cap"] for r in self._preparations(db)):
            raise StateError("RUN_BUDGET_EXCEEDED")

    def _node(self, db, run, node, attempts_used=0):
        route = node["route"]
        surface = identifier(route["surface"])
        ref = "local" if surface == "local" else identifier(route["billing"]["account_ref"])
        account = orchestrate.digest([surface, ref])
        db.execute("INSERT OR IGNORE INTO accounts VALUES(?,?,?,2)", (account, surface, ref))
        count = json.loads(self._one(db, "SELECT plan FROM runs WHERE run_id=?", (run,))["plan"])["budget"]["max_attempts"]
        per = (nano(route["reserved_upper_usd"]) + count - 1) // count
        if attempts_used > count:
            raise StateError("ATTEMPT_LIMIT")
        db.execute("INSERT INTO nodes VALUES(?,?,?,?,?) ON CONFLICT(run_id,node_id) DO UPDATE SET account_key=excluded.account_key,per_attempt=excluded.per_attempt,remaining=excluded.remaining",
                   (run, node["id"], account, per, per * (count - attempts_used)))

    def register(self, plan, now=None):
        now = moment(now)
        validate_plan(plan, now)
        run = plan["run_id"]
        with self._transaction() as db:
            if any(r["run_id"] == run and r["state"] != "registered" for r in self._preparations(db)):
                raise StateError("PREPARATION_FINALIZATION_REQUIRED")
            self._register(db, plan, now)

    def _register(self, db, plan, now):
        run = plan["run_id"]
        old = db.execute("SELECT plan_digest FROM runs WHERE run_id=?", (run,)).fetchone()
        if old:
            if old[0] != plan["plan_digest"]:
                raise StateError("RUN_ALREADY_EXISTS")
            return
        self._budget_guard(db)
        tasks = set()
        for n in plan["steps"]:
            for kind in ("run", "task"):
                native = native_binding(n).get(kind + "_id")
                if native is None:
                    continue
                self._native_available(db, run, kind, native, n["id"])
                if kind == "task":
                    if native in tasks:
                        raise StateError("PREPARATION_BINDING_DUPLICATE")
                    tasks.add(native)
        b = plan["budget"]
        db.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?,0)", (run, plan["plan_digest"], spec_digest(plan),
            safe_json(plan), nano(b["approved_usd"], ceiling=False), nano(b["spent_usd"]), nano(b["external_reserved_usd"])))
        for node in plan["steps"]:
            self._node(db, run, node)
        self._budget_guard(db)
        self._event(db, run, None, "reserved", now, {"plan_digest": plan["plan_digest"]})

    def _ready(self, db, run, now):
        row, p = self._run(db, run)
        self._budget_guard(db)
        events, latest = [], {}
        for a in self._attempts(db, run):
            latest[a["node_id"]] = a
        for a in latest.values():
            if a["state"] in {"failed", "not_started", "rejected"} and a["actual"] is not None and a["plan_digest"] != p["plan_digest"] and a["attempt"] < p["budget"]["max_attempts"]:
                continue  # Explicit fresh replan, never an implicit timeout retry.
            status = "running" if a["state"] in ACTIVE else "done" if a["state"] == "succeeded" else "failed"
            events.append({"run_id": run, "plan_digest": p["plan_digest"], "id": a["node_id"],
                           "status": status, "verified": bool(a["verified"]), "evidence": [a["dispatch_id"]]})
        ready = orchestrate.ready_steps(p, events, now)
        active = [a for a in self._attempts(db) if a["state"] in ACTIVE]
        global_slots = self._one(db, "SELECT parallel FROM grant_policy WHERE id=1")["parallel"] - len(active)
        ready = [n for n in ready if sum(a["account_key"] == self._one(db,
            "SELECT account_key FROM nodes WHERE run_id=? AND node_id=?", (run, n))["account_key"] for a in active) < 2]
        return ready[:max(0, global_slots)]

    def ready(self, run, now=None):
        with self._transaction() as db:
            try:
                return self._ready(db, run, moment(now))
            except StateError as exc:
                if exc.code in {"COST_UNRESOLVED", "BUDGET_EXCEEDED", "RUN_BUDGET_EXCEEDED"}:
                    return []
                raise

    @staticmethod
    def _public_attempt(row, allowed=False):
        out = {k: row[k] for k in ("dispatch_id", "run_id", "node_id", "attempt", "request_id", "plan_digest", "account_key", "state", "created_at", "observed_at")}
        out.update(handle=json.loads(row["handle"]) if row["handle"] else None,
                   actual_usd=usd(row["actual"]) if row["actual"] is not None else None,
                   reserved_usd=usd(row["reserved"]), verified=bool(row["verified"]), dispatch_allowed=allowed,
                   route=json.loads(row["route"]), observation=json.loads(row["proof"]) if row["proof"] else None)
        return out

    def claim(self, run, node, request, plan_digest, now=None):
        now = moment(now)
        identifier(node), identifier(request)
        with self._transaction() as db:
            old = db.execute("SELECT * FROM attempts WHERE run_id=? AND request_id=?", (run, request)).fetchone()
            if old:
                if old["node_id"] != node or old["plan_digest"] != plan_digest:
                    raise StateError("IDEMPOTENCY_CONFLICT")
                return self._public_attempt(dict(old))
            _, p = self._run(db, run)
            if p["plan_digest"] != plan_digest:
                raise StateError("PLAN_CHANGED")
            if node not in self._ready(db, run, now):
                raise StateError("NODE_NOT_READY")
            n = self._one(db, "SELECT * FROM nodes WHERE run_id=? AND node_id=?", (run, node))
            attempt = 1 + db.execute("SELECT COUNT(*) FROM attempts WHERE run_id=? AND node_id=?", (run, node)).fetchone()[0]
            if attempt > p["budget"]["max_attempts"] or n["remaining"] < n["per_attempt"]:
                raise StateError("ATTEMPT_LIMIT")
            dispatch = "dispatch-" + uuid.uuid4().hex
            route = next(s["route"] for s in p["steps"] if s["id"] == node)
            db.execute("UPDATE nodes SET remaining=remaining-? WHERE run_id=? AND node_id=?", (n["per_attempt"], run, node))
            db.execute("INSERT INTO attempts VALUES(?,?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,0,?,?)",
                       (dispatch, run, node, attempt, request, plan_digest, n["account_key"], safe_json(route), "intent", n["per_attempt"], now, now))
            self._event(db, run, dispatch, "dispatch_intent", now, {"request_id": request, "plan_digest": plan_digest})
            result = self._public_attempt(self._one(db, "SELECT * FROM attempts WHERE dispatch_id=?", (dispatch,)), True)
        return result  # Commit must succeed before returning dispatch_allowed=true.

    def bind(self, dispatch, handle, now=None):
        now = moment(now)
        if not isinstance(handle, dict) or set(handle) != {"kind", "id", "identity"}:
            raise StateError("HANDLE_REQUIRED")
        for value in handle.values():
            identifier(value)
        encoded = safe_json(handle)
        with self._transaction() as db:
            a = self._one(db, "SELECT * FROM attempts WHERE dispatch_id=?", (dispatch,))
            if a["handle"]:
                if a["handle"] != encoded:
                    raise StateError("HANDLE_CONFLICT")
                return
            if a["state"] not in ACTIVE:
                raise StateError("TERMINAL_IMMUTABLE")
            db.execute("UPDATE attempts SET handle=?,state='running' WHERE dispatch_id=?", (encoded, dispatch))
            self._event(db, a["run_id"], dispatch, "handle_bound", now, handle)

    def observe(self, dispatch, observation, now=None):
        now = moment(now)
        safe_json(observation)
        if not isinstance(observation, dict) or not observation.get("observed_at"):
            raise StateError("OBSERVATION_TIME_REQUIRED")
        state = observation.get("state")
        if state not in {"unknown", "running", "succeeded", "failed", "not_started"}:
            raise StateError("INVALID_OBSERVATION")
        evidence(observation.get("evidence"))
        observed = moment(observation.get("observed_at"))
        if orchestrate.instant(observed) > orchestrate.instant(now):
            raise StateError("FUTURE_OBSERVATION")
        with self._transaction() as db:
            a = self._one(db, "SELECT * FROM attempts WHERE dispatch_id=?", (dispatch,))
            if orchestrate.instant(observed) < orchestrate.instant(a["observed_at"]):
                raise StateError("STALE_OBSERVATION")
            encoded = safe_json(observation)
            if a["state"] in TERMINAL:
                if a["proof"] == encoded:
                    return
                raise StateError("TERMINAL_IMMUTABLE")
            known = json.loads(a["handle"]) if a["handle"] else None
            if observation.get("handle") != known or (known is None and state not in {"unknown", "not_started"}):
                raise StateError("HANDLE_MISMATCH")
            if state == "not_started" and (known is not None or observation.get("proof_kind") != "transport-not-accepted"):
                raise StateError("NOT_STARTED_PROOF_REQUIRED")
            db.execute("UPDATE attempts SET state=?,proof=?,observed_at=? WHERE dispatch_id=?",
                       ("uncertain" if state == "unknown" else state, encoded, observed, dispatch))
            self._event(db, a["run_id"], dispatch, "observation", now, observation)

    @staticmethod
    def _release_verified(db, dispatch):
        a = db.execute("SELECT * FROM attempts WHERE dispatch_id=?", (dispatch,)).fetchone()
        if a["state"] == "succeeded" and a["verified"] and a["actual"] is not None:
            db.execute("UPDATE nodes SET remaining=0 WHERE run_id=? AND node_id=?", (a["run_id"], a["node_id"]))

    def settle(self, dispatch, actual_usd, receipt, now=None):
        actual, now = nano(actual_usd), moment(now)
        evidence(receipt)
        with self._transaction() as db:
            a = self._one(db, "SELECT * FROM attempts WHERE dispatch_id=?", (dispatch,))
            if a["state"] not in TERMINAL:
                raise StateError("TERMINAL_PROOF_REQUIRED")
            if a["actual"] is not None:
                if a["actual"] != actual:
                    raise StateError("RECEIPT_CONFLICT")
                return
            db.execute("UPDATE attempts SET actual=? WHERE dispatch_id=?", (actual, dispatch))
            self._release_verified(db, dispatch)
            # Persist an observed overrun. Later admission fails; never roll it back.
            self._event(db, a["run_id"], dispatch, "settled", now, {"actual_usd": usd(actual), "evidence": receipt})

    def verify(self, dispatch, acceptance_evidence, now=None):
        now = moment(now)
        evidence(acceptance_evidence)
        with self._transaction() as db:
            a = self._one(db, "SELECT * FROM attempts WHERE dispatch_id=?", (dispatch,))
            if a["state"] != "succeeded":
                raise StateError("SUCCESS_PROOF_REQUIRED")
            route, proof = json.loads(a["route"]), json.loads(a["proof"])
            if route.get("model") is not None and (proof.get("resolved_model") != (route.get("resolved_model") or route["model"])
                    or proof.get("effective_effort") != route.get("requested_effort")):
                raise StateError("EFFECTIVE_ROUTE_MISMATCH")
            db.execute("UPDATE attempts SET verified=1 WHERE dispatch_id=?", (dispatch,))
            self._release_verified(db, dispatch)
            self._event(db, a["run_id"], dispatch, "verified", now, {"evidence": acceptance_evidence})

    def reject(self, dispatch, rejection_evidence, now=None):
        evidence(rejection_evidence)
        with self._transaction() as db:
            a = self._one(db, "SELECT * FROM attempts WHERE dispatch_id=?", (dispatch,))
            if a["state"] != "succeeded" or a["verified"]:
                raise StateError("RESULT_NOT_REJECTABLE")
            db.execute("UPDATE attempts SET state='rejected' WHERE dispatch_id=?", (dispatch,))
            self._event(db, a["run_id"], dispatch, "output_rejected", moment(now), {"evidence": rejection_evidence})

    def refresh(self, plan, now=None):
        now = moment(now)
        validate_plan(plan, now)
        run = plan["run_id"]
        with self._transaction() as db:
            row, old = self._run(db, run)
            if spec_digest(plan) != row["spec_digest"]:
                raise StateError("INTENT_CHANGED")
            attempts = self._attempts(db, run)
            if any(a["state"] in ACTIVE or a["actual"] is None for a in attempts):
                raise StateError("RECONCILIATION_REQUIRED")
            self._budget_guard(db)
            db.execute("UPDATE runs SET plan=?,plan_digest=? WHERE run_id=?", (safe_json(plan), plan["plan_digest"], run))
            for node in plan["steps"]:
                history = [a for a in attempts if a["node_id"] == node["id"]]
                latest = history[-1] if history else None
                if latest and latest["state"] == "succeeded":
                    previous = json.loads(latest["route"])
                    fields = ("surface", "model", "resolved_model", "requested_effort", "vendor")
                    if any(previous.get(k) != node["route"].get(k) for k in fields) or previous.get("billing") != node["route"].get("billing"):
                        raise StateError("COMPLETED_ROUTE_CHANGED")
                    continue
                self._node(db, run, node, len(history))
            self._budget_guard(db)
            self._event(db, run, None, "replanned", now, {"plan_digest": plan["plan_digest"]})

    def cancel(self, run, reason, now=None):
        evidence(reason)
        with self._transaction() as db:
            self._run(db, run)
            if any(a["state"] in ACTIVE or a["actual"] is None for a in self._attempts(db, run)):
                raise StateError("RECONCILIATION_REQUIRED")
            db.execute("UPDATE nodes SET remaining=0 WHERE run_id=?", (run,))
            db.execute("UPDATE runs SET closed=1 WHERE run_id=?", (run,))
            self._event(db, run, None, "cancelled", moment(now), {"evidence": reason})

    def complete(self, run, acceptance_evidence, now=None):
        evidence(acceptance_evidence)
        with self._transaction() as db:
            row, plan = self._run(db, run)
            attempts = self._attempts(db, run)
            if any(a["state"] in ACTIVE or a["actual"] is None for a in attempts):
                raise StateError("RECONCILIATION_REQUIRED")
            latest = {a["node_id"]: a for a in attempts}
            if any(n["id"] not in latest or latest[n["id"]]["state"] != "succeeded" or not latest[n["id"]]["verified"] for n in plan["steps"]):
                raise StateError("ACCEPTANCE_INCOMPLETE")
            spent, held, _, _ = self._totals(db, run)
            if spent + held > row["cap"]:
                raise StateError("RUN_BUDGET_EXCEEDED")
            db.execute("UPDATE runs SET closed=2 WHERE run_id=?", (run,))
            self._event(db, run, None, "completed", moment(now), {"evidence": acceptance_evidence})

    def snapshot(self):
        with self._transaction() as db:
            grant = self._one(db, "SELECT * FROM grant_policy WHERE id=1")
            spent, held, unknown, unresolved = self._totals(db)
            halted = None
            try:
                self._budget_guard(db)
            except StateError as exc:
                halted = exc.code
            accounts = []
            for row in db.execute("SELECT * FROM accounts ORDER BY account_key"):
                account = dict(row)
                attempts = [a for a in self._attempts(db) if a["account_key"] == row["account_key"]]
                pending = sum(n[0] for n in db.execute("SELECT remaining FROM nodes WHERE account_key=?", (row["account_key"],)))
                account["active_attempts"] = sum(a["state"] in ACTIVE for a in attempts)
                account["held_usd"] = usd(pending + sum(a["reserved"] for a in attempts if a["actual"] is None))
                account["known_spent_usd"] = usd(sum(a["actual"] for a in attempts if a["actual"] is not None))
                account["actual_total_usd"] = None if any(a["actual"] is None for a in attempts) else account["known_spent_usd"]
                accounts.append(account)
            return {"schema_version": db.execute("PRAGMA user_version").fetchone()[0], "budget": {"approved_usd": usd(grant["cap"]),
                "known_spent_usd": usd(spent), "held_usd": usd(held),
                "actual_total_usd": None if unknown else usd(spent), "unknown_attempts": unknown,
                "halted": halted is not None, "halt_reason": halted, "provider_hard_cap": False},
                "runs": [dict(r, status=("active", "cancelled", "completed")[r["closed"]]) for r in db.execute("SELECT run_id,plan_digest,closed FROM runs ORDER BY run_id")],
                "preparations": [{"run_id": r["run_id"], "draft_digest": r["draft_digest"], "state": r["state"],
                    "held_usd": usd(r["held"]), "known_spent_usd": usd(r["spent"])} for r in self._preparations(db)],
                "accounts": accounts, "attempts": [self._public_attempt(a) for a in self._attempts(db)]}


def read_payload(path):
    if Path(path).stat().st_size > 1024 * 1024:
        raise StateError("PAYLOAD_TOO_LARGE")
    value = strict_loads(Path(path).read_text(encoding="utf-8"))
    safe_json(value)
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "state")))
    parser.add_argument("--db", default=str(base / "SimonK" / "vibe" / "runs.sqlite3"))
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("init")
    p.add_argument("--approved-usd", default="0")
    p.add_argument("--approval-ref", default="user-zero-additional-budget")
    sub.add_parser("upgrade-preparations").add_argument("--approval-ref", required=True)
    sub.add_parser("upgrade-preparation-refresh").add_argument("--approval-ref", required=True)
    for name in ("register", "refresh"):
        sub.add_parser(name).add_argument("--plan", required=True)
    sub.add_parser("status")
    sub.add_parser("ready").add_argument("--run", required=True)
    p = sub.add_parser("claim")
    for name in ("run", "node", "request", "plan-digest"):
        p.add_argument("--" + name, required=True)
    for name in ("bind", "observe", "settle", "verify", "reject"):
        p = sub.add_parser(name)
        p.add_argument("--dispatch", required=True)
        p.add_argument("--input", required=True)
    for name in ("cancel", "complete"):
        p = sub.add_parser(name)
        p.add_argument("--run", required=True)
        p.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    try:
        store, result = Store(args.db), None
        if args.action == "init":
            store.initialize(args.approved_usd, args.approval_ref)
        elif args.action == "upgrade-preparations":
            store.upgrade_preparations(args.approval_ref)
        elif args.action == "upgrade-preparation-refresh":
            store.upgrade_preparation_refresh(args.approval_ref)
        elif args.action in {"register", "refresh"}:
            getattr(store, args.action)(read_payload(args.plan))
        elif args.action == "claim":
            result = store.claim(args.run, args.node, args.request, args.plan_digest)
        elif args.action == "ready":
            result = store.ready(args.run)
        elif args.action in {"bind", "observe"}:
            getattr(store, args.action)(args.dispatch, read_payload(args.input))
        elif args.action == "settle":
            payload = read_payload(args.input)
            store.settle(args.dispatch, payload["actual_usd"], payload["evidence"])
        elif args.action in {"verify", "reject"}:
            getattr(store, args.action)(args.dispatch, read_payload(args.input)["evidence"])
        elif args.action in {"cancel", "complete"}:
            getattr(store, args.action)(args.run, read_payload(args.input)["evidence"])
        if result is None:
            result = store.snapshot()
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (StateError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"error": exc.code if isinstance(exc, StateError) else "STATE_COMMAND_FAILED"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
