#!/usr/bin/env python3
"""One-shot, guarded local Orca adapter. No billing discovery or automatic retry.

The trusted coordinator supplies an already registered plan and a separately
verified account/transport certificate. Raw worker prose never drives state.
Only a fresh, internal Store.claim may send. Recovery is always lookup-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import orchestrate
import routing
from run_state import Store, StateError, evidence, identifier, moment, read_payload, safe_json, strict_loads, validate_plan

LIMIT = 1024 * 1024


def require(condition, code):
    if not condition:
        raise StateError(code)


def selected(plan, node_id):
    require(plan.get("plan_digest") == orchestrate.digest({k: v for k, v in plan.items() if k != "plan_digest"}), "PLAN_CHANGED")
    nodes = [n for n in plan["steps"] if n["id"] == node_id]
    require(len(nodes) == 1, "NODE_NOT_FOUND")
    return nodes[0]


def render_spec(node):
    """Create this exact native Task spec before registering its immutable plan.

    Includes the node's complete intent and selected skill paths; excludes only
    planner diagnostics and the transport manifest. Never accepts a second,
    unrelated free-form prompt at dispatch time.
    """
    body = {k: v for k, v in node.items() if k not in
            {"orca", "route", "errors", "rejected_candidates"}}
    return "Vibe supervised task. Read the selected skills; obey ownership and acceptance.\n" + safe_json(body)


def binding_digest(plan, node_id):
    node = selected(plan, node_id)
    return orchestrate.digest({"plan_digest": plan["plan_digest"], "node_id": node_id,
                              "orca": node["orca"], "spec": render_spec(node)})


def request_id(plan, node_id):
    return "vibe-orca-" + binding_digest(plan, node_id)


def _client(argv, timeout=45, max_bytes=LIMIT):
    """Bounded nonblocking pipe; terminate only our CLI, never its worker tree."""
    process = subprocess.Popen(argv, shell=False, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    deadline, raw = time.monotonic() + timeout, bytearray()
    try:
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes
            import msvcrt
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.PeekNamedPipe.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                                            ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
            kernel.PeekNamedPipe.restype = wintypes.BOOL
            handle = msvcrt.get_osfhandle(process.stdout.fileno())
        else:
            os.set_blocking(process.stdout.fileno(), False)
        while True:
            require(time.monotonic() < deadline, "ORCA_RESPONSE_TIMEOUT")
            chunk = None
            if os.name == "nt":
                available = wintypes.DWORD()
                if not kernel.PeekNamedPipe(handle, None, 0, None, ctypes.byref(available), None):
                    require(ctypes.get_last_error() == 109, "ORCA_RESPONSE_PIPE_FAILED")
                    chunk = b""
                elif available.value:
                    chunk = os.read(process.stdout.fileno(), min(65536, available.value, max_bytes + 1 - len(raw)))
            else:
                try:
                    chunk = os.read(process.stdout.fileno(), min(65536, max_bytes + 1 - len(raw)))
                except BlockingIOError:
                    pass
            if chunk:
                raw.extend(chunk)
                require(len(raw) <= max_bytes, "ORCA_RESPONSE_TOO_LARGE")
            elif process.poll() is not None:
                return process.returncode, bytes(raw)
            else:
                time.sleep(0.01)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        process.stdout.close()


class Orca:
    """Pinned native executable, argv only, bounded returned data and no raw errors.

    Unlike legacy routing.run_orca this pins the executable and bounds live I/O.
    A nonzero response triggers lookup, not replay. A timeout stops only our CLI client,
    not the Orca-owned worker. It proves neither cancellation nor non-acceptance.
    """
    def __init__(self, executable, sha256):
        path = Path(executable)
        require(path.is_absolute() and path.is_file() and not path.is_symlink(), "EXACT_ORCA_EXECUTABLE_REQUIRED")
        require(os.name != "nt" or path.suffix.lower() == ".exe", "NATIVE_ORCA_EXECUTABLE_REQUIRED")
        self.executable, self.sha256 = str(path.resolve()), sha256
        self.check_binary()

    def check_binary(self):
        with open(self.executable, "rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        require(actual == self.sha256, "ORCA_EXECUTABLE_CHANGED")

    def call(self, *args):
        self.check_binary()
        # Only the fixed read verbs or task-ID start below reach this boundary.
        try:
            rc, raw = _client([self.executable, *args, "--json"])
        except (OSError, subprocess.TimeoutExpired):
            raise StateError("ORCA_RESPONSE_UNKNOWN") from None
        try:
            envelope = strict_loads(raw.decode("utf-8"))
        except (ValueError, UnicodeError, RecursionError):
            raise StateError("ORCA_RESPONSE_INVALID") from None
        require(isinstance(envelope, dict) and envelope.get("ok") is True and rc == 0,
                "ORCA_RESPONSE_UNKNOWN")
        require(isinstance(envelope.get("result"), dict), "ORCA_RESPONSE_INVALID")
        return envelope["result"]


class Adapter:
    def __init__(self, store, transport, clock=moment):
        self.store, self.transport, self.clock = store, transport, clock

    def context(self, plan, node_id):
        safe_json(plan)
        node = selected(plan, node_id)
        r, b = node["route"], node["orca"]
        require(r["transport"] == "orca" and r["surface"] in {"claude", "codex"}, "ORCA_SURFACE_UNSUPPORTED")
        lane = routing.LANES.get(r["model"], {})
        require(lane.get("dispatch") == "orca" and lane.get("effort_style") == "flag", "ORCA_EFFORT_UNSUPPORTED")
        require(lane.get("cli") == r["surface"], "ORCA_AGENT_MISMATCH")
        for key in ("run_id", "task_id", "runtime_id", "account_ref", "profile_ref", "app_version", "workspace_instance"):
            identifier(b[key])
        require(isinstance(b["worktree_id"], str) and 0 < len(b["worktree_id"]) < 2048
                and not any(ord(c) < 32 for c in b["worktree_id"]), "EXACT_WORKSPACE_REQUIRED")
        path = Path(b["worktree_path"])
        require(path.is_absolute() and path.is_dir() and str(path.resolve()) == b["worktree_path"], "EXACT_WORKSPACE_REQUIRED")
        require(b["executable"] == self.transport.executable and b["executable_sha256"] == self.transport.sha256,
                "ORCA_EXECUTABLE_CHANGED")
        require(b["account_ref"] == r["billing"]["account_ref"], "ACCOUNT_MISMATCH")
        runs = [v for v in self.store.snapshot()["runs"] if v["run_id"] == plan["run_id"]]
        require(len(runs) == 1 and runs[0]["plan_digest"] == plan["plan_digest"], "REGISTERED_PLAN_REQUIRED")
        return node, r, b

    def attempt(self, plan, node_id):
        return next((a for a in self.store.snapshot()["attempts"] if a["run_id"] == plan["run_id"]
                     and a["request_id"] == request_id(plan, node_id)), None)

    def runtime(self, binding):
        result = self.transport.call("status").get("runtime", {})
        require(result.get("runtimeId") == binding["runtime_id"] and result.get("appVersion") == binding["app_version"]
                and result.get("state") == "ready", "ORCA_RUNTIME_CHANGED")
        require("orchestration.worker-launch-preferences.v1" in result.get("capabilities", []), "LAUNCH_CAPABILITY_REQUIRED")

    def task(self, binding, spec):
        result = self.transport.call("orchestration", "task-list", "--run", binding["run_id"])
        require(result.get("runId") == binding["run_id"] and isinstance(result.get("tasks"), list), "TASK_LOOKUP_SCOPE")
        matches = [t for t in result["tasks"] if t.get("id") == binding["task_id"]]
        require(len(matches) == 1, "TASK_LOOKUP_AMBIGUOUS")
        task = matches[0]
        require(task.get("run_id") == binding["run_id"] and task.get("spec") == spec, "TASK_SPEC_MISMATCH")
        return task

    def workspace(self, binding):
        data = self.transport.call("worktree", "show", "--worktree", "id:" + binding["worktree_id"])["worktree"]
        require(data.get("id") == binding["worktree_id"] and data.get("hostId") == "local"
                and data.get("instanceId") == binding["workspace_instance"]
                and data.get("identity", {}).get("executionHostId") == "local"
                and Path(data["path"]).is_absolute()
                and Path(data["path"]).resolve() == Path(binding["worktree_path"]), "WORKSPACE_BINDING_MISMATCH")

    def workers(self, binding):
        result, cursor, seen = [], None, set()
        for _ in range(20):
            args = ["orchestration", "worker-list", "--run", binding["run_id"]]
            if cursor:
                args += ["--cursor", cursor]
            page = self.transport.call(*args)
            require(page.get("scope", {}).get("run") == binding["run_id"] and isinstance(page.get("workers"), list),
                    "WORKER_LOOKUP_SCOPE")
            for row in page["workers"]:
                if row.get("taskId") == binding["task_id"]:
                    require(row.get("runId") == binding["run_id"], "WORKER_LOOKUP_SCOPE")
                    result.append(row)
            pagination = page.get("page", {})
            if pagination.get("hasMore") is False:
                return result
            cursor = pagination.get("nextCursor")
            require(isinstance(cursor, str) and cursor and cursor not in seen, "WORKER_LOOKUP_INCOMPLETE")
            seen.add(cursor)
        raise StateError("WORKER_LOOKUP_INCOMPLETE")

    def gate(self, plan, node_id, certificate):
        node, route, binding = self.context(plan, node_id)
        now = self.clock()
        validate_plan(plan, now)
        require(not orchestrate._legacy_validation(plan["steps"], binding["guards"]), "ORCA_PLAN_GUARD")
        require(isinstance(certificate, dict) and certificate.get("verified") is True, "TRANSPORT_ACCOUNT_UNVERIFIED")
        safe_json(certificate)
        evidence(certificate.get("evidence"))
        require(certificate.get("binding_sha256") == binding_digest(plan, node_id)
                and certificate.get("account_ref") == binding["account_ref"]
                and certificate.get("profile_ref") == binding["profile_ref"]
                and certificate.get("billing") == route["billing"], "TRANSPORT_ACCOUNT_MISMATCH")
        require(orchestrate.fresh(certificate.get("observed_at"), now)
                and orchestrate.instant(now) < orchestrate.instant(certificate["valid_until"]), "TRANSPORT_ACCOUNT_STALE")
        return node, route, binding

    def preflight(self, plan, node_id, certificate):
        node, route, binding = self.gate(plan, node_id, certificate)
        self.runtime(binding)
        self.workspace(binding)
        require(self.task(binding, render_spec(node)).get("status") == "ready", "TASK_NOT_READY")
        require(not self.workers(binding), "TASK_ALREADY_DISPATCHED")
        self.transport.check_binary()
        # Repeat clock-dependent gates after the read-only calls, before send.
        self.gate(plan, node_id, certificate)
        return node, route, binding

    def dispatch(self, plan, node_id, certificate):
        self.context(plan, node_id)
        if self.attempt(plan, node_id):
            return self.reconcile(plan, node_id)
        node, route, binding = self.preflight(plan, node_id, certificate)
        claim = self.store.claim(plan["run_id"], node_id, request_id(plan, node_id), plan["plan_digest"], now=self.clock())
        if not claim["dispatch_allowed"]:
            return self.reconcile(plan, node_id)
        try:
            self.preflight(plan, node_id, certificate)
            argv = routing.dispatch_argv(route["model"], route["requested_effort"], binding["task_id"], node_id,
                worktree="id:" + binding["worktree_id"], allow_off_ladder=node.get("off_ladder", False))
            # One call only. Orca retry identity is additional deduplication, not
            # permission to replay an absent/pending request or claim exactly-once.
            self.transport.call(*argv[1:-1], "--run", binding["run_id"], "--retry-request", request_id(plan, node_id))
        except (StateError, OSError, TimeoutError, ValueError, KeyError, TypeError):
            pass  # A failed CLI response is not proof the worker did not start.
        return self.reconcile(plan, node_id)

    def _unknown(self, attempt, reason):
        current = next(a for a in self.store.snapshot()["attempts"] if a["dispatch_id"] == attempt["dispatch_id"])
        if current["state"] in {"intent", "running", "uncertain"}:
            now = self.clock()
            self.store.observe(current["dispatch_id"], {"state": "unknown", "handle": current["handle"],
                "observed_at": now, "evidence": [reason]}, now=now)
        return self.result(current["dispatch_id"], reason=reason)

    def result(self, dispatch_id, **extra):
        row = next(a for a in self.store.snapshot()["attempts"] if a["dispatch_id"] == dispatch_id)
        return {**row, **extra}

    def reconcile(self, plan, node_id):
        node, route, binding = self.context(plan, node_id)
        attempt = self.attempt(plan, node_id)
        require(attempt is not None, "NO_EXISTING_INTENT")
        if attempt["state"] in {"succeeded", "failed", "not_started", "rejected"}:
            return self.result(attempt["dispatch_id"])
        try:
            self.runtime(binding)
            self.workspace(binding)
            self.task(binding, render_spec(node))
            workers = self.workers(binding)
            require(len(workers) == 1, "WORKER_LOOKUP_AMBIGUOUS")
            native_id = identifier(workers[0]["dispatchId"])
            shown = self.transport.call("orchestration", "worker-show", "--dispatch", native_id)
            d, w, projection = shown["dispatch"], shown["worker"], shown["projection"]
            require(d["id"] == native_id and d["taskId"] == binding["task_id"] and d["runId"] == binding["run_id"]
                and w["dispatchId"] == native_id and w["worktreeId"] == binding["worktree_id"]
                and projection["dispatchId"] == native_id and projection["taskId"] == binding["task_id"]
                and projection["runId"] == binding["run_id"], "WORKER_IDENTITY_MISMATCH")
            options = w["startOptions"]
            require(options["agent"] == route["surface"] and options["worktree"] == "id:" + binding["worktree_id"]
                and options["resolvedWorktreeId"] == binding["worktree_id"], "WORKER_PLACEMENT_MISMATCH")
            requested = {"agent": route["surface"], "model": routing.slug_for(route["model"], route["requested_effort"]),
                         "effort": route["requested_effort"]}
            launch = options.get("launch") or {}
            require(launch.get("requested") == requested, "WORKER_LAUNCH_MISMATCH")
            handle = {"kind": "orca", "id": native_id, "identity": orchestrate.digest({
                "binding": binding_digest(plan, node_id), "epoch": identifier(w["runtimeEpoch"]), "dispatch": native_id})}
            self.store.bind(attempt["dispatch_id"], handle, now=self.clock())
            effective = launch.get("effective") or {}
            require(effective == requested, "EFFECTIVE_ROUTE_UNVERIFIED")
            state = "unknown"
            if d.get("status") == "completed" and w.get("state") == "succeeded" and projection.get("outcome") == "succeeded":
                state = "succeeded"
            elif d.get("status") == "failed" and w.get("state") == "failed" and projection.get("outcome") == "failed":
                state = "failed"
            elif projection.get("liveness", {}).get("verdict") == "live":
                state = "running"
            output = self.output(native_id)
            now = self.clock()
            self.store.observe(attempt["dispatch_id"], {"state": state, "handle": handle, "observed_at": now,
                "evidence": ["orca:worker-show:" + native_id, "orca:worker-read:sha256:" + output["sha256"]],
                "resolved_model": effective["model"], "effective_effort": effective["effort"]}, now=now)
            return self.result(attempt["dispatch_id"], output=output)
        except (StateError, OSError, TimeoutError, ValueError, KeyError, TypeError, AttributeError):
            return self._unknown(attempt, "ORCA_RECONCILIATION_UNCERTAIN")

    def output(self, native_id):
        data = self.transport.call("orchestration", "worker-read", "--dispatch", native_id, "--limit", "50")
        require(data.get("dispatchId") == native_id, "OUTPUT_IDENTITY_MISMATCH")
        text = []
        if data.get("source") == "transcript" and data.get("sourceExact") is True:
            for message in data.get("transcript", {}).get("messages", []):
                if message.get("role") == "assistant":
                    text += [b["text"] for b in message.get("blocks", []) if b.get("type") == "text" and isinstance(b.get("text"), str)]
        joined = "\n".join(text)
        require(data.get("source") in {"transcript", "terminal"}, "OUTPUT_SOURCE_UNKNOWN")
        result = {"sha256": orchestrate.digest(data), "source": data["source"],
            "source_identity_sha256": orchestrate.digest(data.get("sourceIdentity")), "has_cursor": bool(data.get("cursor")),
            "content_complete": data.get("contentComplete") is True and not data.get("clipping") and len(joined) <= 16384,
            "warning_count": len(data.get("warnings", [])), "untrusted": True,
            "assistant_text_bytes": len(joined.encode("utf-8")), "text_omitted": True,
            "read_argv": ["orchestration", "worker-read", "--dispatch", native_id, "--limit", "50", "--json"]}
        # Text can contain arbitrary credentials (not only known token shapes).
        # Inspect it separately through the authorized native reader; never copy
        # raw prose, cursor, tool input or provider errors into run-state/logs.
        safe_json(result)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["spec", "dispatch", "reconcile"])
    parser.add_argument("--plan", required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument("--db")
    parser.add_argument("--certificate")
    args = parser.parse_args()
    try:
        plan = read_payload(args.plan)
        node = selected(plan, args.node)
        if args.action == "spec":
            print(render_spec(node))
            return 0
        require(args.db is not None, "SHARED_DB_REQUIRED")
        binding = node["orca"]
        adapter = Adapter(Store(args.db), Orca(binding["executable"], binding["executable_sha256"]))
        if args.action == "dispatch":
            certificate = read_payload(args.certificate) if args.certificate else None
            result = adapter.dispatch(plan, args.node, certificate)
        else:
            result = adapter.reconcile(plan, args.node)
        print(safe_json(result))
        return 2 if result["state"] in {"uncertain", "failed", "rejected"} else 0
    except (StateError, OSError, ValueError, KeyError, TypeError, AttributeError):
        print(json.dumps({"error": "ORCA_ADAPTER_BLOCKED"}))
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
