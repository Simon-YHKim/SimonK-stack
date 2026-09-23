"""Host-injected preparation protocol core, NOT an operational Orca CLI.

No bridge implementation, JSON factory, subprocess runner or default fallback
ships here. A reviewed host must open an exclusive, owned local session before
using this library. Python interfaces cannot authenticate that host's assertions.
Synthetic tests prove sequencing only, never ownership, isolation or billing.
"""
from pathlib import Path
import re

import orchestrate
import routing
from execute_orca import Adapter, require
from run_state import (StateError, evidence, identifier, moment, nano,
                       preparation_argv, safe_json, strict_loads, task_spec, validate_plan)

PINS = ("runtime_id", "app_version", "executable", "executable_sha256",
        "worktree_id", "worktree_path", "workspace_instance")
FAILURES = (StateError, OSError, TimeoutError, ValueError, KeyError, TypeError, AttributeError)


class PreparationAdapter:
    def __init__(self, store, host, clock=moment):
        self.store, self.host, self.clock = store, host, clock
        self.session = self.context = self.plan = None

    def _open(self, plan):
        safe_json(plan)
        require(plan.get("plan_digest") == orchestrate.digest({k: v for k, v in plan.items()
                if k != "plan_digest"}), "PLAN_CHANGED")
        binding = plan["steps"][0]["orca"]
        require(not orchestrate._legacy_validation(plan["steps"], binding["guards"]), "ORCA_PLAN_GUARD")
        for node in plan["steps"]:
            b, r = node["orca"], node["route"]
            lane = routing.LANES.get(r["model"], {})
            require(r["transport"] == "orca" and r["surface"] in {"claude", "codex"}
                and lane.get("dispatch") == "orca" and lane.get("effort_style") == "flag"
                and lane.get("cli") == r["surface"], "ORCA_SURFACE_UNSUPPORTED")
            require(all(b[k] == binding[k] for k in (*PINS, "guards")), "PREPARATION_SCOPE_CHANGED")
            require(b["account_ref"] == r["billing"]["account_ref"], "ACCOUNT_MISMATCH")
            for key in ("runtime_id", "app_version", "workspace_instance", "account_ref", "profile_ref"):
                identifier(b[key])
            path = Path(b["worktree_path"])
            require(path.is_absolute() and path.is_dir() and str(path.resolve()) == str(path), "EXACT_WORKSPACE_REQUIRED")
            require("run_id" not in b and "task_id" not in b, "UNBOUND_ORCA_PLAN_REQUIRED")
        if self.plan is not None:
            require(self.plan["plan_digest"] == plan["plan_digest"], "PREPARATION_IMMUTABLE")
        else:
            self.plan = strict_loads(safe_json(plan))
            # open/attest are trusted, in-process capability operations. They
            # must not discover credentials or spawn native/provider processes.
            require(self.host is not None and callable(getattr(self.host, "open", None)), "OWNED_HOST_REQUIRED")
            self.session = self.host.open({"draft_digest": plan["plan_digest"],
                "binding": {k: binding[k] for k in PINS}, "contract": "owned-local-orca-preparation-v1"})
        self._guard()
        self.caller = {"handle": self.context["handle"], "identity_sha256": orchestrate.digest(self.context)}
        return binding

    def _guard(self):
        require(self.session is not None and callable(getattr(self.session, "attest", None)), "OWNED_SESSION_REQUIRED")
        proof = self.session.attest()
        safe_json(proof)
        require(isinstance(proof, dict) and proof.get("contract") == "owned-local-orca-preparation-v1"
            and proof.get("draft_digest") == self.plan["plan_digest"], "SESSION_PROOF_MISMATCH")
        require(all(proof.get(k) is True for k in ("verified", "owned", "exclusive", "startup_reviewed",
                "non_generating", "first_use_uuid")) and nano(proof.get("actual_usd")) == 0, "SESSION_PROOF_REQUIRED")
        evidence(proof.get("evidence"))
        require(orchestrate.fresh(proof.get("observed_at"), self.clock())
            and orchestrate.instant(self.clock()) < orchestrate.instant(proof.get("valid_until")), "SESSION_PROOF_STALE")
        scope = identifier(proof.get("scope_id"))
        require(scope == self.session.scope_id, "SESSION_SCOPE_CHANGED")
        context = proof["context"]
        require(context.get("target") == "local" and all(context.get(k) == self.plan["steps"][0]["orca"][k]
                for k in PINS), "SESSION_CONTEXT_MISMATCH")
        for key in ("handle", "pane_key", "process_incarnation", "transport_id"):
            identifier(context.get(key))
        require(isinstance(context.get("loaded_server_sha256"), str)
            and re.fullmatch(r"[a-f0-9]{64}", context["loaded_server_sha256"])
            and context["loaded_server_sha256"] == context.get("inspected_server_sha256"), "LOADED_SOURCE_UNVERIFIED")
        identity = proof.get("request_identity")
        require(isinstance(identity, dict)
            and identity.get("contract") == "caller-chosen-uuid-first-run-task-create-v1",
            "PREPARATION_METHOD_CONTRACT_REQUIRED")
        methods = identity.get("methods")
        require(isinstance(methods, list) and len(methods) == 3 and all(isinstance(m, str) for m in methods)
            and set(methods) == {"orchestration.runCreate", "orchestration.taskCreate", "orchestration.requestShow"}
            and identity.get("runtime_id") == context["runtime_id"]
            and identity.get("app_version") == context["app_version"]
            and identity.get("server_sha256") == context["loaded_server_sha256"], "PREPARATION_METHOD_BINDING_MISMATCH")
        evidence(identity.get("evidence"))
        if self.context is None:
            self.context, self.scope_id = strict_loads(safe_json(context)), scope
        require(context == self.context and scope == self.scope_id, "SESSION_CONTEXT_CHANGED")

    def _state(self):
        state = self.store.preparation(self.plan["run_id"])
        require(state["draft_digest"] == self.plan["plan_digest"] and state["caller"] == self.caller,
                "PREPARATION_IMMUTABLE")
        return state

    def _reply(self, wrapped):
        self._guard()
        require(wrapped.get("scope_id") == self.scope_id
            and wrapped.get("context_sha256") == orchestrate.digest(self.context), "RESPONSE_SCOPE_CHANGED")
        envelope = wrapped["envelope"]
        require(envelope.get("ok") is True and envelope.get("_meta", {}).get("runtimeId") == self.context["runtime_id"]
            and isinstance(envelope.get("result"), dict), "RESPONSE_RUNTIME_UNVERIFIED")
        safe_json(envelope["result"])
        return envelope["result"]

    def call(self, *args):
        """Sealed read transport for existing Adapter runtime/workspace checks."""
        self._guard()
        b = self.plan["steps"][0]["orca"]
        allowed = {("status",), ("worktree", "show", "--worktree", "id:" + b["worktree_id"]),
            ("orchestration", "run-current", "--from", self.caller["handle"])}
        for op in self._state()["operations"].values():
            allowed.add(("orchestration", "request-show", "--request", op["request_id"]))
        native = getattr(self, "lookup_run", None)
        if native is not None:
            for verb, flag in (("run-show", "--id"), ("task-list", "--run"), ("worker-list", "--run")):
                allowed.add(("orchestration", verb, flag, native))
        require(args in allowed, "PREPARATION_VERB_FORBIDDEN")
        return self._reply(self.session.read_exact((*args, "--json")))

    def _environment(self):
        binding = self.plan["steps"][0]["orca"]
        result = self.call("status").get("runtime", {})
        require(result.get("runtimeId") == binding["runtime_id"]
            and result.get("appVersion") == binding["app_version"] and result.get("state") == "ready",
            "ORCA_RUNTIME_CHANGED")
        # Worker launch preferences neither prove nor gate metadata preparation.
        # Exact preparation methods are covered by the separate host contract.
        adapter = Adapter(self.store, self, self.clock)
        adapter.workspace(binding)

    def _run(self, native):
        identifier(native)
        self.lookup_run = native
        shown = self.call("orchestration", "run-show", "--id", native)["run"]
        current = self.call("orchestration", "run-current", "--from", self.caller["handle"])["run"]
        for row in (shown, current):
            require(isinstance(row, dict) and row.get("id") == native
                and row.get("objective") == "vibe-preparation:" + self.plan["plan_digest"]
                and row.get("coordinator_handle") == self.caller["handle"]
                and type(row.get("legacy")) is int and row["legacy"] == 0
                and type(row.get("consumer_generation")) is int and row["consumer_generation"] == 1,
                "RUN_OWNERSHIP_MISMATCH")
        return shown

    def _tasks(self, native):
        self.lookup_run = native
        result = self.call("orchestration", "task-list", "--run", native)
        rows = result.get("tasks")
        require(result.get("runId") == native and result.get("legacyReadOnly") is False and isinstance(rows, list)
            and type(result.get("count")) is int and result["count"] == len(rows)
            and len(rows) <= 32 and len({r["id"] for r in rows}) == len(rows)
            and all(r.get("run_id") == native for r in rows), "TASK_LIST_INCOMPLETE")
        return {identifier(row["id"]): row for row in rows}

    def _task(self, key, row, run, bindings):
        node = next(n for n in self.plan["steps"] if "task:" + n["id"] == key)
        deps = [bindings["task:" + d] for d in node["depends_on"]]
        require(row.get("run_id") == run["id"] and row.get("spec") == task_spec(node)
            and row.get("task_title") == "vibe-preparation:" + self.plan["plan_digest"] + ":" + node["id"]
            and isinstance(row.get("deps"), str) and strict_loads(row["deps"]) == deps
            and "parent_id" in row and row["parent_id"] is None
            and not row.get("dispatch_id") and not row.get("assignee_handle")
            and row.get("status") == ("pending" if deps else "ready"), "TASK_INTENT_MISMATCH")
        # These nullable native fields are never synthesized. Without positive
        # provenance this restricted core leaves preparation unresolved.
        require(row.get("created_by_terminal_handle") == self.context["handle"]
            and row.get("created_by_pane_key") == self.context["pane_key"]
            and row.get("created_by_process_incarnation") == self.context["process_incarnation"]
            and type(row.get("created_by_run_generation")) is int
            and row["created_by_run_generation"] == run["consumer_generation"], "TASK_PROVENANCE_UNKNOWN")

    def _empty_workers(self, native):
        result = self.call("orchestration", "worker-list", "--run", native)
        require(result.get("scope", {}).get("run") == native and result.get("workers") == []
            and result.get("page", {}).get("hasMore") is False, "RUN_ALREADY_DISPATCHED_OR_UNKNOWN")

    def _graph(self, ignore=None):
        ops = {key: op for key, op in self._state()["operations"].items() if key != ignore}
        if "run" not in ops:
            current = self.call("orchestration", "run-current", "--from", self.caller["handle"])
            require("run" in current and current["run"] is None,
                    "UNRELATED_CURRENT_RUN")
            return
        require(all(op["state"] == "complete" for op in ops.values()), "PREPARATION_RECONCILIATION_REQUIRED")
        bindings = {key: op["native_id"] for key, op in ops.items()}
        run, rows = self._run(bindings["run"]), self._tasks(bindings["run"])
        require(set(rows) == {v for k, v in bindings.items() if k != "run"}, "UNEXPECTED_NATIVE_TASKS")
        for key, native in bindings.items():
            if key != "run":
                self._task(key, rows[native], run, bindings)
        self._empty_workers(bindings["run"])

    def begin(self, plan):
        validate_plan(plan, self.clock())
        self._open(plan)
        self.store.begin_preparation(plan, self.caller, now=self.clock())
        return self._state()

    def _result(self, status):
        return {"status": status, "preparation": self._state()}

    def _unknown(self, key):
        op = self._state()["operations"][key]
        self.store.observe_preparation(self.plan["run_id"], key, self.caller,
            {"state": "unknown", "operation_sha256": op["operation_sha256"], "observed_at": self.clock(),
             "evidence": ["PREPARATION_DUAL_READBACK_UNCERTAIN"]}, now=self.clock())
        return self._result("uncertain")

    def prepare_one(self, plan, key):
        self._open(plan)
        state = self._state()
        if state["operations"]:
            observed = self.reconcile(plan)
            # A fresh lookup failure also fences historically complete ops.
            # Store deliberately preserves completed facts; they alone cannot
            # authorize a later mutation after a pruned/ambiguous receipt.
            if (observed["status"] == "uncertain" or key in state["operations"]
                    or any(op["state"] != "complete" for op in state["operations"].values())):
                return observed  # Recovery invocation is always lookup-only.
        validate_plan(plan, self.clock())
        self._environment()
        self._graph()
        op = self.store.preparation_intent(plan["run_id"], key, self.caller, now=self.clock())
        if not op["send_allowed"]:
            return self.reconcile(plan)
        try:
            self._guard()
            self._environment()
            self._graph(ignore=key)
            self._guard()
            validate_plan(plan, self.clock())
            bindings = {k: v["native_id"] for k, v in self._state()["operations"].items() if v["state"] == "complete"}
            expected = preparation_argv(plan, self.caller, key, bindings) + ["--retry-request", op["request_id"], "--json"]
            require(op["argv"] == expected, "PREPARATION_ARGV_CHANGED")
            self._reply(self.session.mutate_exact(tuple(expected)))
        except FAILURES:
            return self._unknown(key)
        return self.reconcile(plan)

    def reconcile(self, plan):
        self._open(plan)
        state = self._state()
        require(state["state"] != "registered", "PREPARATION_ALREADY_REGISTERED")
        key = None
        try:
            self._environment()
            bindings = {}
            for key in ["run", *["task:" + n["id"] for n in orchestrate.ordered_steps(plan["steps"])]]:
                if key not in state["operations"]:
                    continue
                op = state["operations"][key]
                shown = self.call("orchestration", "request-show", "--request", op["request_id"])
                method, field = ("orchestration.runCreate", "run") if key == "run" else ("orchestration.taskCreate", "task")
                require(shown.get("requestId") == op["request_id"] and shown.get("state") == "completed"
                    and shown.get("method") == method, "REQUEST_NOT_PROVEN_COMPLETE")
                receipt = shown["receipt"]
                require(receipt["mutation"]["requestId"] == op["request_id"], "RECEIPT_MISMATCH")
                native = identifier(receipt[field]["id"])
                if key == "run":
                    run = self._run(native)
                    for name in ("id", "objective", "coordinator_handle", "consumer_generation", "legacy"):
                        require(receipt["run"].get(name) == run[name], "RECEIPT_RUN_MISMATCH")
                else:
                    run = self._run(bindings["run"])
                    row = self._tasks(bindings["run"])[native]
                    self._task(key, receipt["task"], run, bindings)
                    self._task(key, row, run, bindings)
                bindings[key] = native
                self._empty_workers(bindings["run"])
                self._guard()
                self.store.observe_preparation(plan["run_id"], key, self.caller,
                    {"state": "complete", "verified": True, "native_id": native, "actual_usd": "0",
                     "non_generating": True, "operation_sha256": op["operation_sha256"], "observed_at": self.clock(),
                     "evidence": ["owned-session:" + self.scope_id, "receipt+resource:" + op["request_id"]]}, now=self.clock())
            self._graph()
            return self._result(self._state()["state"])
        except FAILURES:
            return self._unknown(key) if key in state["operations"] else self._result("uncertain")

    def finalize(self, plan):
        self._open(plan)
        state = self._state()
        require(state["state"] == "bound", "PREPARATION_NOT_BOUND")
        require(self.reconcile(plan)["status"] == "bound", "PREPARATION_RECONCILIATION_REQUIRED")
        self._graph()
        self._guard()
        return self.store.finalize_preparation(plan["run_id"], self.caller,
            {"verified": True, "bound_sha256": self._state()["bound_sha256"], "observed_at": self.clock(),
             "scope_verified": True, "no_workers": True, "non_generating": True, "actual_usd": "0",
             "evidence": ["owned-session:" + self.scope_id, "full-receipt-resource-DAG-readback"]}, now=self.clock())
