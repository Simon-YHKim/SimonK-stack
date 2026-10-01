#!/usr/bin/env python3
"""One-send, tool-free Grok CLI lane; subscription-only evidence is mandatory.

No certificate is manufactured here. An ambiguous acceptance is lookup-only.
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
# Official read-only account identity, effective hook/config isolation and
# subscription usage completeness are not yet proven. Do not turn on merely
# because the CLI exists or a coordinator supplies synthetic assertions.
NATIVE_DISPATCH_ENABLED = False


def require(condition, code):
    if not condition:
        raise StateError(code)


def exact_file(value, suffix, cwd):
    require(isinstance(value, str), "EXACT_GROK_PATH_REQUIRED")
    path = Path(value)
    require(path.is_absolute() and path.suffix == suffix and str(path.resolve()) == value
            and path.parent == cwd and not path.is_symlink(), "EXACT_GROK_PATH_REQUIRED")
    return path


def binding_digest(plan, node_id):
    node = execute_cli.selected(plan, node_id)
    return orchestrate.digest({"plan_digest": plan["plan_digest"], "node_id": node_id,
                              "cli": node["cli"], "spec": execute_cli.render_spec(plan, node_id)})


def request_id(plan, node_id):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,
        "simonk:vibe:grok-cli:one-send:v1:" + binding_digest(plan, node_id)))


def execution_identity(plan, node_id, inputs_sha256):
    base = binding_digest(plan, node_id)
    return orchestrate.digest({"binding": base, "inputs_sha256": inputs_sha256}) if inputs_sha256 else base


def child_env(binding):
    env = runtime_collect.child_env(os.environ, "grok")
    env["GROK_HOME"] = binding["profile_path"]
    return env


def parse_result(raw, session_id, model):
    """Accept one OAuth model response with no client/server tool blocks."""
    require(isinstance(raw, bytes) and 0 < len(raw) <= LIMIT, "GROK_RESULT_BOUNDS")
    try:
        events = [strict_loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
    except (UnicodeError, TypeError, ValueError):
        raise StateError("GROK_RESULT_INVALID") from None
    require(3 <= len(events) <= 16 and all(isinstance(e, dict) for e in events),
            "GROK_RESULT_INVALID")
    init, result = events[0], events[-1]
    require(init.get("type") == "system" and init.get("subtype") == "init"
            and init.get("apiKeySource") == "oauth" and init.get("model") == model
            and init.get("session_id") == session_id, "GROK_INIT_UNVERIFIED")
    require(result.get("type") == "result" and result.get("subtype") == "success"
            and result.get("is_error") is False and result.get("stop_reason") == "end_turn"
            and result.get("session_id") == session_id and result.get("num_turns") == 1
            and result.get("usage_is_incomplete") is not True
            and result.get("cost_is_partial") is not True, "GROK_COMPLETION_UNVERIFIED")
    calls = result.get("modelUsage")
    require(isinstance(calls, dict) and set(calls) == {model}
            and isinstance(calls[model], dict) and calls[model].get("modelCalls") == 1,
            "GROK_MODEL_UNVERIFIED")
    usage = result.get("usage")
    require(isinstance(usage, dict)
            and all(type(usage.get(k)) is int and usage[k] >= 0 for k in ("input_tokens", "output_tokens"))
            and isinstance(usage.get("server_tool_use", {}), dict)
            and all(type(v) is int and v == 0 for v in usage.get("server_tool_use", {}).values()),
            "GROK_USAGE_UNVERIFIED")
    messages = []
    for event in events[1:-1]:
        require(event.get("type") == "assistant" and event.get("session_id") == session_id,
                "GROK_TOOL_OR_EVENT_UNVERIFIED")
        message = event.get("message")
        require(isinstance(message, dict) and message.get("model") == model
                and message.get("stop_reason") == "end_turn"
                and event.get("parent_tool_use_id") is None,
                "GROK_MODEL_OR_TOOL_UNVERIFIED")
        blocks = message.get("content")
        require(isinstance(blocks, list) and blocks
                and all(isinstance(block, dict) and block.get("type") in {"text", "thinking"}
                        for block in blocks), "GROK_TOOL_OR_EVENT_UNVERIFIED")
        messages.extend(block["text"] for block in blocks if block["type"] == "text"
                        and isinstance(block.get("text"), str))
    content = result.get("result")
    require(len(messages) == 1 and content == messages[0], "GROK_TEXT_UNVERIFIED")
    return execute_cli.checked_position(content), usage


class GrokCli(execute_cli.ClaudeCli):
    def __init__(self, executable, sha256):
        require(NATIVE_DISPATCH_ENABLED, "GROK_CLI_OPERATIONAL_HOLD")
        path = Path(executable)
        require(path.is_absolute() and path.is_file() and not path.is_symlink()
                and path.name.lower() == "grok.exe", "EXACT_GROK_EXECUTABLE_REQUIRED")
        self.executable, self.sha256 = str(path.resolve()), sha256
        self.check_binary()

    def auth(self, binding, env, now):
        self.check_binary()
        with runtime_collect.Rpc([self.executable, "agent", "--no-leader", "stdio"],
                                 cwd=binding["cwd"], env=env) as rpc:
            init = rpc.request("initialize", {"protocolVersion": 1,
                "clientCapabilities": {"fs": {"readTextFile": False, "writeTextFile": False},
                                       "terminal": False},
                "clientInfo": {"name": "vibe-grok-guard", "version": "1"}})
            require(isinstance(init, dict) and init.get("protocolVersion") == 1,
                    "GROK_PROTOCOL_UNVERIFIED")
            try:
                raw = rpc.request("_x.ai/billing", {})
            except runtime_collect.CollectorError as exc:
                if exc.rpc_code != -32601:
                    raise
                raw = rpc.request("x.ai/billing", {})
            require(isinstance(raw, dict), "GROK_BILLING_UNVERIFIED")
        socket = str(Path(binding["cwd"]) / "vibe-grok-leader.sock")
        for family in ("mcp", "plugin"):
            listing, rc = runtime_collect.run_text(
                [self.executable, "--no-auto-update", "--leader-socket", socket,
                 family, "list", "--json"], binding["cwd"], env)
            require(rc == 0, "GROK_LOCAL_TOOLS_UNVERIFIED")
            require(strict_loads(listing) in ({}, []), "GROK_LOCAL_TOOLS_PRESENT")
        models, rc = runtime_collect.run_text(
            [self.executable, "--no-auto-update", "--leader-socket", socket, "models"],
            binding["cwd"], env)
        require(rc == 0, "GROK_MODELS_UNVERIFIED")
        raw["_grok_models_text"] = models
        observed = runtime_collect.normalize("grok", raw, now, binding["profile_path"])
        observed["local_tool_config_empty"] = True
        return observed

    def send(self, argv, binding, env):
        return self._capture(argv, binding, env, 600)


class Adapter:
    def __init__(self, store, transport, clock=moment):
        self.store, self.transport, self.clock = store, transport, clock

    def context(self, plan, node_id):
        node = execute_cli.selected(plan, node_id)
        route = node["route"]
        require(node["kind"] == "llm" and node.get("writes") is False
                and not node.get("skills") and not node.get("software")
                and not node.get("verify_of") and route["surface"] == "grok"
                and route["transport"] == "cli", "READ_ONLY_GROK_CLI_ONLY")
        require("debate" in plan or not node.get("depends_on"), "DEPENDENT_NONDEBATE_UNSUPPORTED")
        execute_cli.debate_inputs(plan, node_id)
        require(not scan_secrets(node["task"]), "SENSITIVE_PAYLOAD")
        binding = node.get("cli")
        required = {"executable", "executable_sha256", "cwd", "profile_path",
                    "profile_ref", "account_ref", "prompt_path", "result_path", "content_path"}
        require(isinstance(binding, dict) and set(binding) == required,
                "EXACT_GROK_CLI_BINDING_REQUIRED")
        cwd = execute_cli.exact_directory(binding["cwd"])
        require(all(not (parent / ".git").exists() for parent in (cwd, *cwd.parents)),
                "PRIVATE_GROK_CWD_REQUIRED")
        execute_cli.exact_directory(binding["profile_path"])
        files = [exact_file(binding[k], suffix, cwd) for k, suffix in
                 (("prompt_path", ".txt"), ("result_path", ".jsonl"),
                  ("content_path", ".txt"))]
        require(len(set(files)) == 3 and binding["profile_ref"] == runtime_collect.opaque(
                    "grok", binding["profile_path"])
                and binding["account_ref"] == route["billing"]["account_ref"],
                "GROK_ACCOUNT_MISMATCH")
        require(binding["executable"] == self.transport.executable
                and binding["executable_sha256"] == self.transport.sha256,
                "GROK_EXECUTABLE_CHANGED")
        runs = [r for r in self.store.snapshot()["runs"] if r["run_id"] == plan["run_id"]]
        require(len(runs) == 1 and runs[0]["plan_digest"] == plan["plan_digest"],
                "REGISTERED_PLAN_REQUIRED")
        return node, route, binding

    def attempt(self, plan, node_id):
        rows = [r for r in self.store.snapshot()["attempts"]
                if r["run_id"] == plan["run_id"] and r["node_id"] == node_id]
        require(len(rows) <= 1, "GROK_CLI_RETRY_UNSUPPORTED")
        if rows:
            require(rows[0]["request_id"] == request_id(plan, node_id)
                    and rows[0]["plan_digest"] == plan["plan_digest"],
                    "GROK_DISPATCH_IDENTITY_CHANGED")
            return rows[0]
        return None

    @staticmethod
    def argv(plan, node_id, executable, binding):
        route = execute_cli.selected(plan, node_id)["route"]
        model = route.get("resolved_model") or route["model"]
        return [executable, "--no-auto-update", "--leader-socket",
                str(Path(binding["cwd"]) / "vibe-grok-leader.sock"),
                "--cwd", binding["cwd"],
                "--prompt-file", binding["prompt_path"], "--verbatim",
                "--output-format", "streaming-messages-json", "--session-id",
                request_id(plan, node_id), "--model", model, "--reasoning-effort",
                route["requested_effort"], "--max-turns", "1", "--no-subagents",
                "--disable-web-search", "--tools", "", "--disallowed-tools", "Agent",
                "--deny", "MCPTool", "--sandbox", "read-only"]

    def gate(self, plan, node_id, certificate):
        _, route, binding = self.context(plan, node_id)
        now = self.clock()
        validate_plan(plan, now)
        billing, quota = route["billing"], route["quota"]
        model, effort = route.get("resolved_model") or route["model"], route["requested_effort"]
        require(billing.get("mode") == "subscription" and billing.get("verified") is True
                and billing.get("extra_usage_enabled") is False
                and billing.get("api_fallback_disabled") is True
                and billing.get("paid_credit_fallback_disabled") is True
                and billing.get("model_included") is True
                and billing.get("included_model") == model
                and quota.get("surface") == "grok" and quota.get("transport") == "cli"
                and quota.get("account_ref") == binding["account_ref"]
                and quota.get("state") == "observed"
                and type(quota.get("used_pct")) in (int, float)
                and 0 <= quota["used_pct"] < 100
                and orchestrate.fresh(quota.get("observed_at"), now),
                "GROK_SUBSCRIPTION_ROUTE_UNVERIFIED")
        require(isinstance(certificate, dict) and certificate.get("verified") is True
                and certificate.get("subscription_only") is True, "GROK_CERTIFICATE_REQUIRED")
        safe_json(certificate)
        evidence(certificate.get("evidence"))
        require(certificate.get("binding_sha256") == binding_digest(plan, node_id)
                and certificate.get("account_ref") == binding["account_ref"]
                and certificate.get("profile_ref") == binding["profile_ref"]
                and certificate.get("billing") == billing and certificate.get("quota") == quota
                and certificate.get("model") == model and certificate.get("effort") == effort,
                "GROK_CERTIFICATE_MISMATCH")
        inputs, inputs_sha256 = execute_cli.resolved_inputs(plan, node_id, self.store)
        if inputs_sha256:
            require(certificate.get("inputs_sha256") == inputs_sha256
                    and certificate.get("cross_vendor_transfer_authorized") is True,
                    "GROK_INPUT_CERTIFICATE_REQUIRED")
        else:
            require("inputs_sha256" not in certificate, "GROK_INPUT_CERTIFICATE_MISMATCH")
        require(orchestrate.fresh(certificate.get("observed_at"), now)
                and orchestrate.instant(now) < orchestrate.instant(certificate["valid_until"]),
                "GROK_CERTIFICATE_STALE")
        env = child_env(binding)
        self.transport.check_binary()
        observed = self.transport.auth(binding, env, now)
        fresh_billing = observed.get("billing", {})
        require(observed.get("account_verified") is True
                and observed.get("local_tool_config_empty") is True
                and observed.get("account_ref") == binding["account_ref"]
                and observed.get("profile_ref") == binding["profile_ref"]
                and fresh_billing.get("mode") == "subscription"
                and fresh_billing.get("extra_usage_enabled") is False
                and fresh_billing.get("on_demand_cap") in ("0", "0.0")
                and fresh_billing.get("prepaid_balance") in ("0", "0.0")
                and any(item.get("model") == model for item in observed.get("models", [])),
                "GROK_AUTH_OR_COST_CHANGED")
        return binding, env, inputs, inputs_sha256

    def result(self, dispatch_id):
        row = next(a for a in self.store.snapshot()["attempts"] if a["dispatch_id"] == dispatch_id)
        if row["state"] == "succeeded":
            observed = row["observation"] or {}
            raw = Path(observed["trace_path"])
            content = Path(observed["content_path"])
            require(not raw.is_symlink() and not content.is_symlink()
                    and raw.is_file() and content.is_file()
                    and raw.stat().st_size <= LIMIT and content.stat().st_size <= 16384
                    and hashlib.sha256(raw.read_bytes()).hexdigest() == observed["trace_sha256"]
                    and hashlib.sha256(content.read_bytes()).hexdigest() == observed["content_sha256"],
                    "GROK_RESULT_CHANGED")
        return row

    def reconcile(self, plan, node_id):
        _, route, binding = self.context(plan, node_id)
        attempt = self.attempt(plan, node_id)
        require(attempt is not None, "GROK_CLI_INTENT_REQUIRED")
        recorded = (attempt["observation"] or {}).get("inputs_sha256")
        dependent = bool(execute_cli.debate_inputs(plan, node_id))
        if attempt["state"] == "succeeded":
            require((attempt["handle"] or {}).get("identity") == execution_identity(
                plan, node_id, recorded) and (not dependent or recorded)
                and (attempt["observation"] or {}).get("trace_path") == binding["result_path"]
                and (attempt["observation"] or {}).get("content_path") == binding["content_path"],
                "GROK_INPUT_CHANGED")
            return self.result(attempt["dispatch_id"])
        if attempt["state"] in {"failed", "not_started", "rejected"}:
            return self.result(attempt["dispatch_id"])
        try:
            require(not dependent or recorded, "GROK_PREDECESSOR_INPUT_NOT_BOUND")
            cwd = execute_cli.exact_directory(binding["cwd"])
            trace = exact_file(binding["result_path"], ".jsonl", cwd)
            content_path = exact_file(binding["content_path"], ".txt", cwd)
            require(trace.is_file() and trace.stat().st_size <= LIMIT, "GROK_RESULT_MISSING")
            raw = trace.read_bytes()
            require(isinstance((attempt["observation"] or {}).get("capture_sha256"), str)
                    and hashlib.sha256(raw).hexdigest() == attempt["observation"]["capture_sha256"],
                    "GROK_UNRECEIPTED_RESULT")
            model = route.get("resolved_model") or route["model"]
            content, usage = parse_result(raw, request_id(plan, node_id), model)
            encoded = content.encode("utf-8")
            if content_path.exists():
                require(content_path.read_bytes() == encoded, "GROK_CONTENT_CHANGED")
            else:
                with content_path.open("xb") as stream:
                    stream.write(encoded)
                    stream.flush()
                    os.fsync(stream.fileno())
            handle = {"kind": "grok-cli", "id": request_id(plan, node_id),
                      "identity": execution_identity(plan, node_id, recorded)}
            if attempt["handle"]:
                require(attempt["handle"] == handle, "GROK_SESSION_CHANGED")
            else:
                self.store.bind(attempt["dispatch_id"], handle, now=self.clock())
            now = self.clock()
            self.store.observe(attempt["dispatch_id"], {"state": "succeeded",
                "handle": handle, "observed_at": now,
                "evidence": ["grok-cli:stream:sha256:" + hashlib.sha256(raw).hexdigest(),
                             "CLI flags accepted; provider-internal effort and invoice not attested"],
                "resolved_model": model, "effective_effort": route["requested_effort"],
                "effort_evidence_scope": "accepted-cli-config",
                "trace_path": str(trace), "trace_sha256": hashlib.sha256(raw).hexdigest(),
                "content_path": str(content_path),
                "content_sha256": hashlib.sha256(encoded).hexdigest(),
                "content_format": "text/plain;charset=utf-8",
                "usage_units": {"input": usage["input_tokens"], "output": usage["output_tokens"]},
                "inputs_sha256": recorded}, now=now)
            return self.result(attempt["dispatch_id"])
        except (StateError, OSError, ValueError, UnicodeError, TypeError, KeyError):
            now = self.clock()
            current = next(a for a in self.store.snapshot()["attempts"]
                           if a["dispatch_id"] == attempt["dispatch_id"])
            if current["state"] in {"intent", "running", "uncertain"}:
                self.store.observe(current["dispatch_id"], {"state": "unknown",
                    "handle": current["handle"], "observed_at": now,
                    "evidence": ["GROK_RESULT_OR_ACCEPTANCE_UNCERTAIN"],
                    "inputs_sha256": recorded,
                    "capture_sha256": (current["observation"] or {}).get("capture_sha256")}, now=now)
            return self.result(attempt["dispatch_id"])

    def dispatch(self, plan, node_id, certificate):
        self.context(plan, node_id)
        if self.attempt(plan, node_id):
            return self.reconcile(plan, node_id)
        binding, _, _, first_inputs = self.gate(plan, node_id, certificate)
        cwd = execute_cli.exact_directory(binding["cwd"])
        require(all(not exact_file(binding[key], suffix, cwd).exists() for key, suffix in
                    (("prompt_path", ".txt"), ("result_path", ".jsonl"),
                     ("content_path", ".txt"))), "GROK_ARTIFACT_COLLISION")
        attempt = self.store.claim(plan["run_id"], node_id, request_id(plan, node_id),
                                   plan["plan_digest"], now=self.clock())
        if not attempt["dispatch_allowed"]:
            return self.reconcile(plan, node_id)
        try:
            binding, env, inputs, inputs_sha256 = self.gate(plan, node_id, certificate)
            require(first_inputs == inputs_sha256, "GROK_PRE_SEND_CHANGED")
            prompt = execute_cli.render_spec(plan, node_id, inputs if inputs else None)
            require(len(prompt.encode("utf-8")) <= 65536, "GROK_PROMPT_TOO_LARGE")
            with exact_file(binding["prompt_path"], ".txt", cwd).open("xb") as stream:
                stream.write(prompt.encode("utf-8"))
                stream.flush()
                os.fsync(stream.fileno())
        except (StateError, OSError, ValueError, KeyError, TypeError, runtime_collect.CollectorError):
            now = self.clock()
            self.store.observe(attempt["dispatch_id"], {"state": "not_started", "handle": None,
                "proof_kind": "transport-not-accepted", "observed_at": now,
                "evidence": ["Local pre-send gate failed; no Grok generation command invoked"]}, now=now)
            return self.result(attempt["dispatch_id"])
        now = self.clock()
        self.store.observe(attempt["dispatch_id"], {"state": "unknown", "handle": None,
            "observed_at": now, "evidence": ["Original predecessor input digest fixed before send"],
            "inputs_sha256": inputs_sha256}, now=now)
        try:
            argv = self.argv(plan, node_id, self.transport.executable, binding)
            rc, raw = self.transport.send(argv, binding, env)
            require(rc == 0 and isinstance(raw, bytes) and 0 < len(raw) <= LIMIT,
                    "GROK_RESPONSE_UNCERTAIN")
            now = self.clock()
            self.store.observe(attempt["dispatch_id"], {"state": "unknown", "handle": None,
                "observed_at": now, "evidence": ["Original Grok CLI capture hash committed"],
                "inputs_sha256": inputs_sha256,
                "capture_sha256": hashlib.sha256(raw).hexdigest()}, now=now)
            with exact_file(binding["result_path"], ".jsonl", cwd).open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        except (StateError, OSError, TimeoutError, ValueError, KeyError, TypeError,
                runtime_collect.CollectorError):
            pass  # Never turn ambiguous acceptance into another send.
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
        adapter = Adapter(Store(args.db), GrokCli(binding["executable"],
                                                  binding["executable_sha256"]))
        result = (adapter.dispatch(plan, args.node,
                  read_payload(args.certificate) if args.certificate else None)
                  if args.action == "dispatch" else adapter.reconcile(plan, args.node))
        print(safe_json(result))
        return 0 if result["state"] == "succeeded" else 2
    except (StateError, OSError, ValueError, KeyError, TypeError, AttributeError,
            runtime_collect.CollectorError):
        print(json.dumps({"error": "GROK_CLI_ADAPTER_BLOCKED"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
