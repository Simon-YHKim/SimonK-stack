#!/usr/bin/env python3
"""Guarded, one-send Claude subscription CLI lane for tool-free independent work.

This is not a billing proof factory or scheduler. A trusted coordinator supplies
the registered plan and fresh exact-account subscription certificate. Missing
evidence blocks before generation; reentry only inspects the original result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

if __name__ == "__main__":
    sys.dont_write_bytecode = True
import orchestrate
import runtime_collect
from run_state import Store, StateError, evidence, moment, read_payload, safe_json, strict_loads, validate_plan

LIMIT = 1024 * 1024


def require(condition, code):
    if not condition:
        raise StateError(code)


def selected(plan, node_id):
    safe_json(plan)
    require(plan.get("plan_digest") == orchestrate.digest({k: v for k, v in plan.items()
            if k != "plan_digest"}), "PLAN_CHANGED")
    nodes = [n for n in plan["steps"] if n["id"] == node_id]
    require(len(nodes) == 1, "NODE_NOT_FOUND")
    return nodes[0]


def render_spec(plan, node_id):
    node = selected(plan, node_id)
    task = node.get("task")
    require(isinstance(task, str) and 0 < len(task.encode("utf-8")) <= 24000,
            "BOUNDED_TASK_REQUIRED")
    role = next((key for key in ("proposer", "challenger")
                 if (plan.get("debate") or {}).get(key) == node_id), None)
    return ("Independent read-only /vibe node. Do not claim to have used tools or "
            "other models. State uncertainty and evidence.\n"
            + safe_json({"role": role, "task": task,
                         "acceptance": node.get("acceptance", [])}))


def binding_digest(plan, node_id):
    node = selected(plan, node_id)
    return orchestrate.digest({"plan_digest": plan["plan_digest"], "node_id": node_id,
                              "cli": node["cli"], "spec": render_spec(plan, node_id)})


def request_id(plan, node_id):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,
        "simonk:vibe:claude-cli:one-send:v1:" + binding_digest(plan, node_id)))


def exact_directory(value):
    require(isinstance(value, str), "EXACT_LOCAL_PATH_REQUIRED")
    path = Path(value)
    require(path.is_absolute() and not str(path).startswith("\\\\") and path.is_dir()
            and str(path.resolve()) == value, "EXACT_LOCAL_PATH_REQUIRED")
    for parent in (path, *path.parents):
        if parent.is_symlink() or getattr(parent.stat(), "st_file_attributes", 0) & 0x400:
            raise StateError("LINKED_CLI_PATH")
    return path


def output_path(value):
    require(isinstance(value, str), "EXACT_OUTPUT_PATH_REQUIRED")
    path = Path(value)
    require(path.is_absolute() and path.suffix == ".json"
            and str(path.resolve()) == value, "EXACT_OUTPUT_PATH_REQUIRED")
    exact_directory(str(path.parent))
    require(not path.is_symlink(), "LINKED_CLI_PATH")
    return path


def child_env(binding):
    env = runtime_collect.child_env(os.environ, "claude")
    env["CLAUDE_CONFIG_DIR"] = binding["profile_path"]
    env["DISABLE_AUTOUPDATER"] = "1"
    return env


class ClaudeCli:
    def __init__(self, executable, sha256):
        path = Path(executable)
        require(path.is_absolute() and path.is_file() and not path.is_symlink()
                and (os.name != "nt" or path.suffix.lower() == ".exe"),
                "EXACT_CLAUDE_EXECUTABLE_REQUIRED")
        self.executable, self.sha256 = str(path.resolve()), sha256
        self.check_binary()

    def check_binary(self):
        with open(self.executable, "rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        require(actual == self.sha256, "CLI_EXECUTABLE_CHANGED")

    def _capture(self, argv, binding, env, timeout):
        self.check_binary()
        with runtime_collect.Probe(argv, timeout=timeout, max_bytes=LIMIT,
                                   cwd=binding["cwd"], env=env) as probe:
            raw = bytearray()
            while True:
                line = probe.line()
                if not line:
                    break
                raw.extend(line)
            try:
                rc = probe.process.wait(timeout=max(0.01, probe.deadline - runtime_collect.time.monotonic()))
            except runtime_collect.subprocess.TimeoutExpired:
                raise runtime_collect.CollectorError("timeout") from None
        return rc, bytes(raw)

    def auth(self, binding, env, now):
        rc, raw = self._capture([self.executable, "--safe-mode", "auth", "status", "--json"],
                                binding, env, 30)
        require(rc == 0, "CLAUDE_AUTH_UNVERIFIED")
        observed = runtime_collect.normalize("claude", strict_loads(raw.decode("utf-8-sig")),
                                             now, binding["profile_path"])
        require(observed["account_verified"] and observed["billing"]["mode"] == "subscription"
                and observed["auth"]["method"] == "claude.ai"
                and observed["auth"]["provider"] == "firstParty", "CLAUDE_AUTH_UNVERIFIED")
        return observed

    def send(self, argv, binding, env):
        return self._capture(argv, binding, env, 600)


class Adapter:
    def __init__(self, store, transport, clock=moment):
        self.store, self.transport, self.clock = store, transport, clock

    def context(self, plan, node_id):
        node = selected(plan, node_id)
        route = node["route"]
        require(node["kind"] == "llm" and node.get("writes") is False
                and not node.get("skills") and not node.get("software")
                and not node.get("depends_on") and not node.get("verify_of")
                and route["surface"] == "claude" and route["transport"] == "cli",
                "TOOL_FREE_INDEPENDENT_CLAUDE_ONLY")
        if "debate" in plan:
            require(node_id in {plan["debate"]["proposer"], plan["debate"]["challenger"]},
                    "DEBATE_OPENING_ONLY")
        binding = node.get("cli")
        required = {"executable", "executable_sha256", "cwd", "profile_path",
                    "profile_ref", "account_ref", "result_path"}
        require(isinstance(binding, dict) and set(binding) == required, "EXACT_CLI_BINDING_REQUIRED")
        exact_directory(binding["cwd"])
        exact_directory(binding["profile_path"])
        output_path(binding["result_path"])
        require(binding["profile_ref"] == runtime_collect.opaque("claude", binding["profile_path"])
                and binding["account_ref"] == route["billing"]["account_ref"], "CLI_ACCOUNT_MISMATCH")
        require(binding["executable"] == self.transport.executable
                and binding["executable_sha256"] == self.transport.sha256,
                "CLI_EXECUTABLE_CHANGED")
        runs = [r for r in self.store.snapshot()["runs"] if r["run_id"] == plan["run_id"]]
        require(len(runs) == 1 and runs[0]["plan_digest"] == plan["plan_digest"],
                "REGISTERED_PLAN_REQUIRED")
        return node, route, binding

    def attempt(self, plan, node_id):
        rows = [a for a in self.store.snapshot()["attempts"]
                if a["run_id"] == plan["run_id"] and a["node_id"] == node_id]
        require(len(rows) <= 1, "CLI_RETRY_UNSUPPORTED")
        if rows:
            require(rows[0]["request_id"] == request_id(plan, node_id)
                    and rows[0]["plan_digest"] == plan["plan_digest"],
                    "CLI_DISPATCH_IDENTITY_CHANGED")
            return rows[0]
        return None

    def gate(self, plan, node_id, certificate):
        node, route, binding = self.context(plan, node_id)
        now = self.clock()
        validate_plan(plan, now)
        billing, quota = route["billing"], route["quota"]
        model = route.get("resolved_model") or route["model"]
        require(billing["mode"] == "subscription" and billing["verified"] is True
                and billing.get("extra_usage_enabled") is False
                and billing.get("api_fallback_disabled") is True
                and billing.get("model_included") is True
                and billing.get("included_model") == model
                and type(quota.get("used_pct")) in (int, float)
                and 0 <= quota["used_pct"] < 100
                and orchestrate.fresh(quota.get("observed_at"), now),
                "SUBSCRIPTION_ROUTE_UNVERIFIED")
        require(isinstance(certificate, dict) and certificate.get("verified") is True
                and certificate.get("subscription_only") is True, "CLI_CERTIFICATE_REQUIRED")
        safe_json(certificate)
        evidence(certificate.get("evidence"))
        require(certificate.get("binding_sha256") == binding_digest(plan, node_id)
                and certificate.get("account_ref") == binding["account_ref"]
                and certificate.get("profile_ref") == binding["profile_ref"]
                and certificate.get("billing") == billing and certificate.get("quota") == quota
                and certificate.get("model") == model
                and certificate.get("effort") == route["requested_effort"],
                "CLI_CERTIFICATE_MISMATCH")
        require(orchestrate.fresh(certificate.get("observed_at"), now)
                and orchestrate.instant(now) < orchestrate.instant(certificate["valid_until"]),
                "CLI_CERTIFICATE_STALE")
        env = child_env(binding)
        self.transport.check_binary()
        observed = self.transport.auth(binding, env, now)
        require(observed.get("account_ref") == binding["account_ref"]
                and observed.get("profile_ref") == binding["profile_ref"]
                and observed.get("billing", {}).get("mode") == "subscription"
                and observed.get("auth", {}).get("method") == "claude.ai"
                and observed.get("auth", {}).get("provider") == "firstParty",
                "CLI_AUTH_CHANGED")
        return node, route, binding, env

    @staticmethod
    def argv(plan, node_id, executable, session_id):
        route = selected(plan, node_id)["route"]
        model = route.get("resolved_model") or route["model"]
        return [executable, "--safe-mode", "--strict-mcp-config", "--tools", "",
                "--permission-prompts", "none", "--no-session-persistence",
                "--model", model, "--effort", route["requested_effort"],
                "--session-id", session_id, "--output-format", "json",
                "-p", render_spec(plan, node_id)]

    def _unknown(self, attempt, reason):
        current = next(a for a in self.store.snapshot()["attempts"]
                       if a["dispatch_id"] == attempt["dispatch_id"])
        if current["state"] in {"intent", "running", "uncertain"}:
            now = self.clock()
            self.store.observe(current["dispatch_id"], {"state": "unknown", "handle": current["handle"],
                "observed_at": now, "evidence": [reason]}, now=now)
        return self.result(attempt["dispatch_id"])

    def result(self, dispatch_id):
        row = next(a for a in self.store.snapshot()["attempts"] if a["dispatch_id"] == dispatch_id)
        if row["state"] == "succeeded":
            observed = row["observation"] or {}
            path = output_path(observed.get("output_path"))
            require(path.is_file() and path.stat().st_size <= LIMIT
                    and hashlib.sha256(path.read_bytes()).hexdigest() == observed.get("output_sha256"),
                    "CLI_RESULT_CHANGED")
        return {**row, "output_path": row["observation"].get("output_path") if row["observation"] else None,
                "output_sha256": row["observation"].get("output_sha256") if row["observation"] else None}

    def reconcile(self, plan, node_id):
        _, route, binding = self.context(plan, node_id)
        attempt = self.attempt(plan, node_id)
        require(attempt is not None, "CLI_INTENT_REQUIRED")
        if attempt["state"] in {"succeeded", "failed", "not_started", "rejected"}:
            return self.result(attempt["dispatch_id"])
        handle = attempt["handle"]
        if not handle or handle.get("kind") != "claude-cli" or handle.get("identity") != binding_digest(plan, node_id):
            return self._unknown(attempt, "CLI_SEND_NOT_ATTESTED")
        try:
            path = output_path(binding["result_path"])
            require(path.is_file() and path.stat().st_size <= LIMIT, "CLI_RESULT_MISSING")
            raw = path.read_bytes()
            require(len(raw) <= LIMIT, "CLI_RESULT_TOO_LARGE")
            data = strict_loads(raw.decode("utf-8-sig"))
            model = route.get("resolved_model") or route["model"]
            require(isinstance(data, dict) and data.get("type") == "result"
                    and data.get("is_error") is False
                    and data.get("session_id") == handle["id"]
                    and isinstance(data.get("result"), str) and data["result"].strip()
                    and isinstance(data.get("modelUsage"), dict)
                    and set(data["modelUsage"]) == {model}, "CLI_RESULT_IDENTITY_UNVERIFIED")
            now = self.clock()
            self.store.observe(attempt["dispatch_id"], {"state": "succeeded", "handle": handle,
                "observed_at": now, "evidence": ["claude-cli:result:sha256:" + hashlib.sha256(raw).hexdigest(),
                    "Pinned CLI accepted --model/--effort; provider-internal effort is not attested"],
                "resolved_model": model, "effective_effort": route["requested_effort"],
                "effort_evidence_scope": "accepted-cli-flag", "output_path": str(path),
                "output_sha256": hashlib.sha256(raw).hexdigest()}, now=now)
            return self.result(attempt["dispatch_id"])
        except (StateError, OSError, ValueError, UnicodeError, TypeError, KeyError):
            return self._unknown(attempt, "CLI_RESULT_OR_ACCEPTANCE_UNCERTAIN")

    def dispatch(self, plan, node_id, certificate):
        self.context(plan, node_id)
        if self.attempt(plan, node_id):
            return self.reconcile(plan, node_id)
        _, _, binding, _ = self.gate(plan, node_id, certificate)
        require(not output_path(binding["result_path"]).exists(), "CLI_RESULT_COLLISION")
        attempt = self.store.claim(plan["run_id"], node_id, request_id(plan, node_id),
                                   plan["plan_digest"], now=self.clock())
        if not attempt["dispatch_allowed"]:
            return self.reconcile(plan, node_id)
        try:
            _, _, binding, env = self.gate(plan, node_id, certificate)
            require(not output_path(binding["result_path"]).exists(), "CLI_RESULT_COLLISION")
        except (StateError, OSError, ValueError, KeyError, TypeError,
                runtime_collect.CollectorError):
            now = self.clock()
            self.store.observe(attempt["dispatch_id"], {"state": "not_started", "handle": None,
                "proof_kind": "transport-not-accepted", "observed_at": now,
                "evidence": ["Local pre-send gate failed; no generation command was invoked"]}, now=now)
            return self.result(attempt["dispatch_id"])
        handle = {"kind": "claude-cli", "id": str(uuid.uuid4()),
                  "identity": binding_digest(plan, node_id)}
        self.store.bind(attempt["dispatch_id"], handle, now=self.clock())
        try:
            argv = self.argv(plan, node_id, self.transport.executable, handle["id"])
            rc, raw = self.transport.send(argv, binding, env)
            require(rc == 0 and isinstance(raw, bytes) and 0 < len(raw) <= LIMIT,
                    "CLI_RESPONSE_UNCERTAIN")
            path = output_path(binding["result_path"])
            with path.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        except (StateError, OSError, TimeoutError, ValueError, KeyError, TypeError,
                runtime_collect.CollectorError):
            pass  # A failed client response is never proof that generation did not occur.
        return self.reconcile(plan, node_id)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("spec", "dispatch", "reconcile"))
    parser.add_argument("--plan", required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument("--db")
    parser.add_argument("--certificate")
    args = parser.parse_args(argv)
    try:
        plan = read_payload(args.plan)
        node = selected(plan, args.node)
        if args.action == "spec":
            print(render_spec(plan, args.node))
            return 0
        require(args.db is not None, "SHARED_DB_REQUIRED")
        binding = node["cli"]
        adapter = Adapter(Store(args.db), ClaudeCli(binding["executable"], binding["executable_sha256"]))
        if args.action == "dispatch":
            certificate = read_payload(args.certificate) if args.certificate else None
            result = adapter.dispatch(plan, args.node, certificate)
        else:
            result = adapter.reconcile(plan, args.node)
        print(safe_json(result))
        return 0 if result["state"] == "succeeded" else 2
    except (StateError, OSError, ValueError, KeyError, TypeError, AttributeError,
            runtime_collect.CollectorError):
        print(json.dumps({"error": "CLI_ADAPTER_BLOCKED"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
