#!/usr/bin/env python3
"""One-send Codex CLI read-only lane; requires fresh subscription-only proof.

This is an integration point, not a billing certificate factory. No account
setting or payment method is changed. An ambiguous send is lookup-only.
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
import execute_cli
import orchestrate
import runtime_collect
from run_state import Store, StateError, evidence, moment, read_payload, safe_json, scan_secrets, strict_loads, validate_plan

LIMIT = 1024 * 1024


def require(condition, code):
    if not condition:
        raise StateError(code)


def artifact_path(value, suffix):
    require(isinstance(value, str), "EXACT_CODEX_RESULT_PATH_REQUIRED")
    path = Path(value)
    require(path.is_absolute() and path.suffix == suffix and str(path.resolve()) == value
            and not path.is_symlink(), "EXACT_CODEX_RESULT_PATH_REQUIRED")
    execute_cli.exact_directory(str(path.parent))
    return path


def binding_digest(plan, node_id):
    node = execute_cli.selected(plan, node_id)
    return orchestrate.digest({"plan_digest": plan["plan_digest"], "node_id": node_id,
                              "cli": node["cli"], "spec": execute_cli.render_spec(plan, node_id)})


def request_id(plan, node_id):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,
        "simonk:vibe:codex-cli:one-send:v1:" + binding_digest(plan, node_id)))


def execution_identity(plan, node_id, inputs_sha256):
    base = binding_digest(plan, node_id)
    return orchestrate.digest({"binding": base, "inputs_sha256": inputs_sha256}) if inputs_sha256 else base


def child_env(binding):
    env = runtime_collect.child_env(os.environ, "codex")
    env["CODEX_HOME"] = binding["profile_path"]
    return env


def parse_result(raw):
    """Accept exactly one successful, tool-free Codex JSONL turn."""
    require(isinstance(raw, bytes) and 0 < len(raw) <= LIMIT, "CODEX_RESULT_BOUNDS")
    try:
        lines = raw.decode("utf-8-sig").splitlines()
        events = [strict_loads(line) for line in lines if line.strip()]
    except (UnicodeError, ValueError, TypeError):
        raise StateError("CODEX_RESULT_INVALID") from None
    require(3 <= len(events) <= 1000, "CODEX_RESULT_INVALID")
    thread, starts, finishes, messages = None, 0, 0, []
    for event in events:
        require(isinstance(event, dict), "CODEX_EVENT_INVALID")
        kind = event.get("type")
        if kind == "thread.started":
            require(thread is None and starts == 0 and finishes == 0
                    and isinstance(event.get("thread_id"), str)
                    and 0 < len(event["thread_id"]) <= 128, "CODEX_THREAD_INVALID")
            thread = event["thread_id"]
        elif kind == "turn.started":
            require(thread and starts == 0 and finishes == 0, "CODEX_TURN_INVALID")
            starts = 1
        elif kind in {"item.started", "item.updated", "item.completed"}:
            item = event.get("item")
            require(starts == 1 and finishes == 0 and isinstance(item, dict)
                    and item.get("type") in {"reasoning", "agent_message"},
                    "CODEX_TOOL_OR_EVENT_UNVERIFIED")
            if kind == "item.completed" and item["type"] == "agent_message":
                messages.append(execute_cli.checked_position(item.get("text")))
        elif kind == "turn.completed":
            usage = event.get("usage")
            require(starts == 1 and finishes == 0 and messages
                    and isinstance(usage, dict)
                    and all(type(usage.get(key)) is int and usage[key] >= 0
                            for key in ("input_tokens", "output_tokens")),
                    "CODEX_COMPLETION_UNVERIFIED")
            finishes = 1
        else:
            raise StateError("CODEX_TOOL_OR_EVENT_UNVERIFIED")
    require(thread and starts == 1 and finishes == 1, "CODEX_COMPLETION_UNVERIFIED")
    return thread, messages[-1], events[-1]["usage"]


class CodexCli(execute_cli.ClaudeCli):
    def __init__(self, executable, sha256):
        path = Path(executable)
        require(path.is_absolute() and path.is_file() and not path.is_symlink()
                and path.name.lower() == "codex.exe", "EXACT_CODEX_EXECUTABLE_REQUIRED")
        self.executable, self.sha256 = str(path.resolve()), sha256
        self.check_binary()

    def auth(self, binding, env, now):
        self.check_binary()
        with runtime_collect.Rpc([self.executable, "app-server", "--stdio"],
                                 cwd=binding["cwd"], env=env) as rpc:
            init = rpc.request("initialize", {"clientInfo": {"name": "vibe-codex-cli", "version": "1"},
                                              "capabilities": {"experimentalApi": False}})
            require(isinstance(init, dict)
                    and os.path.normcase(os.path.normpath(init.get("codexHome", ""))) ==
                    os.path.normcase(os.path.normpath(binding["profile_path"])),
                    "CODEX_PROFILE_CHANGED")
            rpc.send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
            account = rpc.request("account/read", {"refreshToken": False})
            models = rpc.request("model/list", {"includeHidden": False})
            limits = rpc.request("account/rateLimits/read", {})
            require(account == rpc.request("account/read", {"refreshToken": False}),
                    "CODEX_ACCOUNT_CHANGED")
        return runtime_collect.normalize("codex", {"initialize": init, "account": account,
                                                   "models": models, "limits": limits},
                                         now, binding["profile_path"])

    def send(self, argv, binding, env, prompt):
        require(isinstance(prompt, str) and len(prompt.encode("utf-8")) <= 65536,
                "CODEX_PROMPT_TOO_LARGE")
        return self._capture(argv, binding, env, 600, stdin=prompt.encode("utf-8"))


class Adapter:
    def __init__(self, store, transport, clock=moment):
        self.store, self.transport, self.clock = store, transport, clock

    def context(self, plan, node_id):
        node = execute_cli.selected(plan, node_id)
        route = node["route"]
        require(node["kind"] == "llm" and node.get("writes") is False
                and not node.get("skills") and not node.get("software")
                and not node.get("verify_of") and route["surface"] == "codex"
                and route["transport"] == "cli", "READ_ONLY_CODEX_CLI_ONLY")
        require("debate" in plan or not node.get("depends_on"), "DEPENDENT_NONDEBATE_UNSUPPORTED")
        execute_cli.debate_inputs(plan, node_id)
        require(not scan_secrets(node["task"]), "SENSITIVE_PAYLOAD")
        binding = node.get("cli")
        required = {"executable", "executable_sha256", "cwd", "profile_path",
                    "profile_ref", "account_ref", "result_path", "content_path"}
        require(isinstance(binding, dict) and set(binding) == required,
                "EXACT_CODEX_CLI_BINDING_REQUIRED")
        cwd = execute_cli.exact_directory(binding["cwd"])
        require(all(not (parent / ".git").exists() for parent in (cwd, *cwd.parents)),
                "PRIVATE_CODEX_CWD_REQUIRED")
        execute_cli.exact_directory(binding["profile_path"])
        result = artifact_path(binding["result_path"], ".jsonl")
        content = artifact_path(binding["content_path"], ".txt")
        require(result.parent == cwd and content.parent == cwd,
                "PRIVATE_CODEX_RESULTS_REQUIRED")
        require(result != content and binding["profile_ref"] == runtime_collect.opaque(
                    "codex", binding["profile_path"])
                and binding["account_ref"] == route["billing"]["account_ref"],
                "CODEX_ACCOUNT_MISMATCH")
        require(binding["executable"] == self.transport.executable
                and binding["executable_sha256"] == self.transport.sha256,
                "CODEX_EXECUTABLE_CHANGED")
        runs = [row for row in self.store.snapshot()["runs"] if row["run_id"] == plan["run_id"]]
        require(len(runs) == 1 and runs[0]["plan_digest"] == plan["plan_digest"],
                "REGISTERED_PLAN_REQUIRED")
        return node, route, binding

    def attempt(self, plan, node_id):
        rows = [row for row in self.store.snapshot()["attempts"]
                if row["run_id"] == plan["run_id"] and row["node_id"] == node_id]
        require(len(rows) <= 1, "CODEX_CLI_RETRY_UNSUPPORTED")
        if rows:
            require(rows[0]["request_id"] == request_id(plan, node_id)
                    and rows[0]["plan_digest"] == plan["plan_digest"],
                    "CODEX_DISPATCH_IDENTITY_CHANGED")
            return rows[0]
        return None

    @staticmethod
    def argv(plan, node_id, executable, cwd):
        route = execute_cli.selected(plan, node_id)["route"]
        model = route.get("resolved_model") or route["model"]
        return [executable, "exec", "--json", "--ephemeral", "--ignore-user-config",
                "--skip-git-repo-check", "--sandbox", "read-only", "-C", cwd,
                "-m", model, "-c", 'model_reasoning_effort="' +
                route["requested_effort"] + '"', "-"]

    def gate(self, plan, node_id, certificate):
        _, route, binding = self.context(plan, node_id)
        now = self.clock()
        validate_plan(plan, now)
        billing, quota = route["billing"], route["quota"]
        model, effort = route.get("resolved_model") or route["model"], route["requested_effort"]
        require(billing["mode"] == "subscription" and billing["verified"] is True
                and billing.get("extra_usage_enabled") is False
                and billing.get("api_fallback_disabled") is True
                and billing.get("paid_credit_fallback_disabled") is True
                and billing.get("model_included") is True
                and billing.get("included_model") == model
                and type(quota.get("used_pct")) in (int, float)
                and 0 <= quota["used_pct"] < 100
                and orchestrate.fresh(quota.get("observed_at"), now),
                "CODEX_SUBSCRIPTION_ROUTE_UNVERIFIED")
        require(isinstance(certificate, dict) and certificate.get("verified") is True
                and certificate.get("subscription_only") is True,
                "CODEX_CERTIFICATE_REQUIRED")
        safe_json(certificate)
        evidence(certificate.get("evidence"))
        require(certificate.get("binding_sha256") == binding_digest(plan, node_id)
                and certificate.get("account_ref") == binding["account_ref"]
                and certificate.get("profile_ref") == binding["profile_ref"]
                and certificate.get("billing") == billing and certificate.get("quota") == quota
                and certificate.get("model") == model and certificate.get("effort") == effort,
                "CODEX_CERTIFICATE_MISMATCH")
        inputs, inputs_sha256 = execute_cli.resolved_inputs(plan, node_id, self.store)
        if inputs_sha256:
            require(certificate.get("inputs_sha256") == inputs_sha256
                    and certificate.get("cross_vendor_transfer_authorized") is True,
                    "CODEX_INPUT_CERTIFICATE_REQUIRED")
        else:
            require("inputs_sha256" not in certificate, "CODEX_INPUT_CERTIFICATE_MISMATCH")
        require(orchestrate.fresh(certificate.get("observed_at"), now)
                and orchestrate.instant(now) < orchestrate.instant(certificate["valid_until"]),
                "CODEX_CERTIFICATE_STALE")
        env = child_env(binding)
        self.transport.check_binary()
        observed = self.transport.auth(binding, env, now)
        require(observed.get("account_verified") is True
                and observed.get("account_ref") == binding["account_ref"]
                and observed.get("profile_ref") == binding["profile_ref"]
                and observed.get("billing", {}).get("mode") == "subscription"
                and observed.get("auth", {}).get("method") == "chatgpt"
                and any(item.get("model") == model and effort in item.get("transport_efforts", [])
                        for item in observed.get("models", [])), "CODEX_AUTH_OR_MODEL_CHANGED")
        return binding, env, inputs, inputs_sha256

    def _unknown(self, attempt, reason):
        current = next(row for row in self.store.snapshot()["attempts"]
                       if row["dispatch_id"] == attempt["dispatch_id"])
        if current["state"] in {"intent", "running", "uncertain"}:
            now = self.clock()
            self.store.observe(current["dispatch_id"], {"state": "unknown",
                "handle": current["handle"], "observed_at": now, "evidence": [reason],
                "inputs_sha256": (current["observation"] or {}).get("inputs_sha256")}, now=now)
        return self.result(attempt["dispatch_id"])

    def result(self, dispatch_id):
        row = next(a for a in self.store.snapshot()["attempts"] if a["dispatch_id"] == dispatch_id)
        if row["state"] == "succeeded":
            observed = row["observation"] or {}
            raw_path = artifact_path(observed.get("output_path"), ".jsonl")
            text_path = artifact_path(observed.get("content_path"), ".txt")
            require(raw_path.is_file() and text_path.is_file()
                    and raw_path.stat().st_size <= LIMIT and text_path.stat().st_size <= 16384
                    and hashlib.sha256(raw_path.read_bytes()).hexdigest() == observed.get("output_sha256")
                    and hashlib.sha256(text_path.read_bytes()).hexdigest() == observed.get("content_sha256"),
                    "CODEX_RESULT_CHANGED")
        return row

    def reconcile(self, plan, node_id):
        _, route, binding = self.context(plan, node_id)
        attempt = self.attempt(plan, node_id)
        require(attempt is not None, "CODEX_CLI_INTENT_REQUIRED")
        recorded = (attempt["observation"] or {}).get("inputs_sha256")
        dependent = bool(execute_cli.debate_inputs(plan, node_id))
        if attempt["state"] == "succeeded":
            require((attempt["handle"] or {}).get("identity") == execution_identity(
                plan, node_id, recorded) and (not dependent or recorded),
                "CODEX_INPUT_CHANGED")
            return self.result(attempt["dispatch_id"])
        if attempt["state"] in {"failed", "not_started", "rejected"}:
            return self.result(attempt["dispatch_id"])
        if dependent and not recorded:
            return self._unknown(attempt, "CODEX_PREDECESSOR_INPUT_NOT_BOUND")
        try:
            raw_path = artifact_path(binding["result_path"], ".jsonl")
            text_path = artifact_path(binding["content_path"], ".txt")
            require(raw_path.is_file() and raw_path.stat().st_size <= LIMIT,
                    "CODEX_RESULT_MISSING")
            raw = raw_path.read_bytes()
            thread_id, content, usage = parse_result(raw)
            encoded = content.encode("utf-8")
            if text_path.exists():
                require(text_path.is_file() and text_path.read_bytes() == encoded,
                        "CODEX_CONTENT_CHANGED")
            else:
                with text_path.open("xb") as stream:
                    stream.write(encoded)
                    stream.flush()
                    os.fsync(stream.fileno())
            handle = {"kind": "codex-cli", "id": thread_id,
                      "identity": execution_identity(plan, node_id, recorded)}
            if attempt["handle"]:
                require(attempt["handle"] == handle, "CODEX_THREAD_CHANGED")
            else:
                self.store.bind(attempt["dispatch_id"], handle, now=self.clock())
            now = self.clock()
            self.store.observe(attempt["dispatch_id"], {"state": "succeeded",
                "handle": handle, "observed_at": now,
                "evidence": ["codex-cli:jsonl:sha256:" + hashlib.sha256(raw).hexdigest(),
                             "CLI accepted model/effort flags; provider-internal model/effort not attested"],
                "resolved_model": route.get("resolved_model") or route["model"],
                "effective_effort": route["requested_effort"],
                "effort_evidence_scope": "accepted-cli-config", "thread_id": thread_id,
                "output_path": str(raw_path), "output_sha256": hashlib.sha256(raw).hexdigest(),
                "content_path": str(text_path), "content_sha256": hashlib.sha256(encoded).hexdigest(),
                "content_format": "text/plain;charset=utf-8",
                "usage_units": {"input": usage["input_tokens"],
                                "output": usage["output_tokens"]},
                "inputs_sha256": recorded}, now=now)
            return self.result(attempt["dispatch_id"])
        except (StateError, OSError, ValueError, UnicodeError, TypeError, KeyError):
            return self._unknown(attempt, "CODEX_RESULT_OR_ACCEPTANCE_UNCERTAIN")

    def dispatch(self, plan, node_id, certificate):
        self.context(plan, node_id)
        if self.attempt(plan, node_id):
            return self.reconcile(plan, node_id)
        binding, _, _, first_inputs_sha256 = self.gate(plan, node_id, certificate)
        require(not artifact_path(binding["result_path"], ".jsonl").exists()
                and not artifact_path(binding["content_path"], ".txt").exists(),
                "CODEX_RESULT_COLLISION")
        attempt = self.store.claim(plan["run_id"], node_id, request_id(plan, node_id),
                                   plan["plan_digest"], now=self.clock())
        if not attempt["dispatch_allowed"]:
            return self.reconcile(plan, node_id)
        try:
            binding, env, inputs, inputs_sha256 = self.gate(plan, node_id, certificate)
            require(inputs_sha256 == first_inputs_sha256
                    and not artifact_path(binding["result_path"], ".jsonl").exists()
                    and not artifact_path(binding["content_path"], ".txt").exists(),
                    "CODEX_PRE_SEND_CHANGED")
        except (StateError, OSError, ValueError, KeyError, TypeError,
                runtime_collect.CollectorError):
            now = self.clock()
            self.store.observe(attempt["dispatch_id"], {"state": "not_started", "handle": None,
                "proof_kind": "transport-not-accepted", "observed_at": now,
                "evidence": ["Local pre-send gate failed; no Codex generation command was invoked"]},
                now=now)
            return self.result(attempt["dispatch_id"])
        now = self.clock()
        self.store.observe(attempt["dispatch_id"], {"state": "unknown", "handle": None,
            "observed_at": now, "evidence": ["Original predecessor input digest fixed before send"],
            "inputs_sha256": inputs_sha256}, now=now)
        try:
            prompt = execute_cli.render_spec(plan, node_id, inputs if inputs else None)
            argv = self.argv(plan, node_id, self.transport.executable, binding["cwd"])
            rc, raw = self.transport.send(argv, binding, env, prompt)
            require(rc == 0 and isinstance(raw, bytes) and 0 < len(raw) <= LIMIT,
                    "CODEX_RESPONSE_UNCERTAIN")
            path = artifact_path(binding["result_path"], ".jsonl")
            with path.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        except (StateError, OSError, TimeoutError, ValueError, KeyError, TypeError,
                runtime_collect.CollectorError):
            pass  # Unknown acceptance never authorizes a second send.
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
        node = execute_cli.selected(plan, args.node)
        if args.action == "spec":
            require(not execute_cli.debate_inputs(plan, args.node), "DEPENDENT_SPEC_PRIVATE")
            print(execute_cli.render_spec(plan, args.node))
            return 0
        require(args.db is not None, "SHARED_DB_REQUIRED")
        binding = node["cli"]
        adapter = Adapter(Store(args.db), CodexCli(binding["executable"],
                                                  binding["executable_sha256"]))
        result = (adapter.dispatch(plan, args.node,
                  read_payload(args.certificate) if args.certificate else None)
                  if args.action == "dispatch" else adapter.reconcile(plan, args.node))
        print(safe_json(result))
        return 0 if result["state"] == "succeeded" else 2
    except (StateError, OSError, ValueError, KeyError, TypeError, AttributeError,
            runtime_collect.CollectorError):
        print(json.dumps({"error": "CODEX_CLI_ADAPTER_BLOCKED"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
