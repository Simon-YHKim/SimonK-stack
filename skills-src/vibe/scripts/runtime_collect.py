#!/usr/bin/env python3
"""One-shot official CLI metadata collection. No tasks, login or paid probes.

Prints a redacted, planner-compatible snapshot; metadata alone never authorizes
generation. Missing identity, billing, model inclusion and quota stay unknown.
Protocols follow the repository's AI Usage Widget adapters, but preserve billing
fields and bucket IDs which its display-only DTO intentionally drops.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))
from model_registry import load_registry

SURFACES = ("codex", "claude", "antigravity", "grok")
MAX_BYTES = 1024 * 1024  # Catalogs fit well below 1 MiB; stop unsolicited floods.
RPC_METHODS = {"initialize", "model/list", "account/read", "account/rateLimits/read",
               "_x.ai/billing", "x.ai/billing"}
TOKEN_FIELDS = {"input_tokens", "output_tokens", "thinking_tokens", "cache_read_tokens", "total_tokens"}
AGY_USAGE_VERSIONS = {"1.2.6", "1.2.7", "1.2.9"}  # Zero-turn command contract measured locally.
BASE_ENV = {"SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATH", "PATHEXT", "TEMP", "TMP", "TMPDIR",
            "HOME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA",
            "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "COMMONPROGRAMFILES", "COMMONPROGRAMFILES(X86)",
            "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "OS", "USERNAME", "USERDOMAIN", "COMPUTERNAME",
            "LANG", "LC_ALL", "CLAUDE_CODE_GIT_BASH_PATH"}


class CollectorError(Exception):
    def __init__(self, code, rpc_code=None):
        super().__init__(code)  # Never put provider text, argv or credentials here.
        self.code, self.rpc_code = code, rpc_code


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def obj(value):
    return value if isinstance(value, dict) else {}


def identifier(value):
    return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}", value) else None


def opaque(*parts):
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode("utf-8")).hexdigest()[:24]


def amount(value, depth=0):
    if isinstance(value, dict) and depth < 2:
        return amount(value.get("val", value.get("value")), depth + 1)
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = Decimal(str(value))
        return str(result) if result.is_finite() and result >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def percent(value):
    parsed = amount(value)
    return float(parsed) if parsed is not None and Decimal(parsed) <= 100 else None


def stamp(value):
    try:
        if isinstance(value, dict):
            value = value.get("seconds")
        if isinstance(value, bool) or value is None:
            return None
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdecimal()):
            number = float(value)
            if number > 1e12:
                number /= 1000
            if not math.isfinite(number) or number < 1e9:
                return None
            return datetime.fromtimestamp(number, timezone.utc).isoformat()
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result.isoformat() if result.tzinfo is not None else None
    except (TypeError, ValueError, OverflowError, AttributeError, OSError):
        return None


def window(bucket, slot, used, reset, now, **extra):
    end = stamp(reset)
    expired = end is not None and datetime.fromisoformat(end) <= datetime.fromisoformat(now)
    return {"bucket": identifier(bucket), "slot": identifier(slot),
            "used_pct": None if expired else percent(used), "resets_at": end,
            "observed_at": now, "state": "reset-unobserved" if expired else "observed", **extra}


def codex_billing(bucket):
    credits = obj(bucket.get("credits"))
    return {"credits": ({"has_credits": credits["hasCredits"], "unlimited": credits["unlimited"],
                          "balance": amount(credits.get("balance"))}
            if type(credits.get("hasCredits")) is bool and type(credits.get("unlimited")) is bool else None),
            "spend_control_reached": bucket.get("spendControlReached")
            if type(bucket.get("spendControlReached")) is bool else None,
            "rate_limit_reached_type": identifier(bucket.get("rateLimitReachedType"))}


def normalize(surface, raw, now, profile):
    if surface not in SURFACES or not isinstance(raw, dict) or stamp(now) is None:
        raise CollectorError("invalid-observation")
    result = {"surface": surface, "source": {"codex": "codex-app-server", "claude": "claude-auth-status",
              "grok": "grok-acp-billing", "antigravity": "agy-usage-command"}[surface],
              "state": "ok", "observed_at": now, "profile_ref": opaque(surface, profile),
              "account_ref": None, "account_verified": False, "generation_verified": False,
              "models": [], "quota_windows": [], "auth": {},
              "billing": {"mode": "unknown", "verified": False, "extra_usage_enabled": None,
                          "model_included": None, "api_fallback_disabled": None,
                          "provider_hard_cap": None, "actual_cost_usd": None},
              "collection": {"generation_requested": False, "zero_token_verified": None}}
    identity = None
    if surface == "codex":
        account = obj(obj(raw.get("account")).get("account"))
        kind, plan = identifier(account.get("type")), identifier(account.get("planType"))
        result["auth"] = {"logged_in": bool(account), "method": kind, "plan": plan}
        identity = account.get("email") if kind == "chatgpt" else None
        result["billing"]["mode"] = "subscription" if kind == "chatgpt" else "unknown"
        for model in obj(raw.get("models")).get("data", []):
            model = obj(model)
            key = identifier(model.get("model"))
            if key:
                efforts = [identifier(obj(e).get("reasoningEffort"))
                           for e in model.get("supportedReasoningEfforts", [])]
                result["models"].append({"model": key, "transport_efforts": sorted(set(filter(None, efforts)))})
        limits = obj(raw.get("limits"))
        legacy = obj(limits.get("rateLimits"))
        buckets = dict(obj(limits.get("rateLimitsByLimitId")))
        if legacy:
            # Keep an unnamed bucket separate; do not guess its model membership.
            buckets.setdefault(identifier(legacy.get("limitId")) or "unnamed", legacy)
        result["billing"]["buckets"] = {}
        for name, bucket in buckets.items():
            if not identifier(name) or not isinstance(bucket, dict):
                continue
            result["billing"]["buckets"][name] = codex_billing(bucket)
            for slot in ("primary", "secondary"):
                w = obj(bucket.get(slot))
                if w:
                    result["quota_windows"].append(window(name, slot, w.get("usedPercent"), w.get("resetsAt"), now,
                        window_minutes=w.get("windowDurationMins") if type(w.get("windowDurationMins")) is int else None))
        result["billing"].update(codex_billing(legacy))
    elif surface == "grok":
        roots = [raw] if "currentPeriod" in raw or "creditUsagePercent" in raw else [
            v for v in raw.values() if isinstance(v, dict) and ("currentPeriod" in v or "creditUsagePercent" in v)]
        if len(roots) != 1:
            raise CollectorError("billing-shape-unknown")
        root, period = roots[0], obj(roots[0].get("currentPeriod"))
        identity = raw.get("accountId")  # May be absent: a profile is not an identity.
        tier = identifier(raw.get("subscriptionTier", raw.get("subscription_tier")))
        result["auth"] = {"logged_in": True, "plan": tier}
        result["billing"]["mode"] = "subscription" if tier else "unknown"
        result["quota_windows"].append(window("grok-credits", identifier(period.get("type")) or "unknown",
            root.get("creditUsagePercent"), period.get("end"), now))
        for source, target in (("onDemandCap", "on_demand_cap"), ("onDemandUsed", "on_demand_used"),
                               ("prepaidBalance", "prepaid_balance")):
            result["billing"][target] = amount(root.get(source))
        enabled = root.get("onDemandEnabled", root.get("on_demand_enabled"))
        result["billing"]["extra_usage_enabled"] = enabled if type(enabled) is bool else None
    elif surface == "claude":
        if type(raw.get("loggedIn")) is not bool:
            raise CollectorError("auth-shape-unknown")
        logged = raw["loggedIn"]
        method, provider = identifier(raw.get("authMethod")), identifier(raw.get("apiProvider"))
        result["auth"] = {"logged_in": logged, "method": method, "provider": provider,
                          "plan": identifier(raw.get("subscriptionType"))}
        identity = raw.get("email") if logged else None
        if logged and method == "claude.ai" and provider == "firstParty":
            result["billing"]["mode"] = "subscription"
    else:
        usage, command = obj(raw.get("usage")), obj(raw.get("command"))
        if (raw.get("status") != "SUCCESS" or type(raw.get("num_turns")) is not int or raw["num_turns"] != 0
                or command.get("name") != "usage" or not TOKEN_FIELDS <= usage.keys()
                or any(type(v) not in (int, float) or v != 0 for k, v in usage.items() if k.endswith("tokens"))):
            raise CollectorError("unsafe-usage-response")
        groups = obj(command.get("data")).get("groups")
        if not isinstance(groups, list):
            raise CollectorError("quota-shape-unknown")
        result["collection"]["zero_token_verified"] = True
        result["auth"] = {"logged_in": True, "plan": None}
        for group in groups:
            for bucket in obj(group).get("buckets", []):
                bucket = obj(bucket)
                remaining = bucket.get("remaining_fraction")
                used = ((1 - remaining) * 100 if type(remaining) in (int, float)
                        and math.isfinite(remaining) and 0 <= remaining <= 1 else None)
                result["quota_windows"].append(window(bucket.get("id"), bucket.get("window"), used,
                                                     bucket.get("reset_time"), now))
    if isinstance(identity, str) and identity.strip():
        result["account_ref"] = opaque(surface, result["profile_ref"], identity.strip())
        result["account_verified"] = True
    return result


def strict_json(text):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise CollectorError("invalid-json")
            result[k] = v
        return result
    try:
        return json.loads(text, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(CollectorError("invalid-json")))
    except (ValueError, UnicodeError):
        raise CollectorError("invalid-json") from None


class WindowsJob:
    """Contain a suspended probe before it can spawn descendants (Windows 8+).

    Uses documented Job Objects, Toolhelp thread enumeration and ResumeThread.
    https://learn.microsoft.com/windows/win32/procthread/job-objects
    No breakaway flags: closing our unnamed job kills only its own process tree.
    """
    def __init__(self):
        import ctypes as c
        from ctypes import wintypes as w
        self.c, self.k = c, c.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([c.c_void_p, w.LPCWSTR], w.HANDLE),
            "SetInformationJobObject": ([w.HANDLE, c.c_int, c.c_void_p, w.DWORD], w.BOOL),
            "AssignProcessToJobObject": ([w.HANDLE, w.HANDLE], w.BOOL),
            "CloseHandle": ([w.HANDLE], w.BOOL),
            "CreateToolhelp32Snapshot": ([w.DWORD, w.DWORD], w.HANDLE),
            "Thread32First": ([w.HANDLE, c.c_void_p], w.BOOL),
            "Thread32Next": ([w.HANDLE, c.c_void_p], w.BOOL),
            "OpenThread": ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            "ResumeThread": ([w.HANDLE], w.DWORD),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.k, name)
            fn.argtypes, fn.restype = args, result
        class Basic(c.Structure):
            _fields_ = [("process_time", c.c_int64), ("job_time", c.c_int64), ("flags", w.DWORD),
                        ("min_ws", c.c_size_t), ("max_ws", c.c_size_t), ("active", w.DWORD),
                        ("affinity", c.c_size_t), ("priority", w.DWORD), ("scheduling", w.DWORD)]
        class Extended(c.Structure):
            _fields_ = [("basic", Basic), ("io", c.c_uint64 * 6), ("memory", c.c_size_t * 4)]
        self.handle = self.k.CreateJobObjectW(None, None)
        if not self.handle:
            raise CollectorError("process-containment-failed")
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.k.SetInformationJobObject(self.handle, 9, c.byref(limits), c.sizeof(limits)):
            self.close()
            raise CollectorError("process-containment-failed")

    def contain_and_resume(self, process):
        c, k = self.c, self.k
        from ctypes import wintypes as w
        if not k.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise CollectorError("process-containment-failed")
        class Thread(c.Structure):
            _fields_ = [("size", w.DWORD), ("usage", w.DWORD), ("id", w.DWORD), ("pid", w.DWORD),
                        ("base", w.LONG), ("delta", w.LONG), ("flags", w.DWORD)]
        snapshot = k.CreateToolhelp32Snapshot(4, 0)  # TH32CS_SNAPTHREAD
        if snapshot == c.c_void_p(-1).value:
            raise CollectorError("process-containment-failed")
        try:
            entry = Thread()
            entry.size = c.sizeof(entry)
            found = k.Thread32First(snapshot, c.byref(entry))
            while found:
                if entry.pid == process.pid:
                    thread = k.OpenThread(0x0002, False, entry.id)  # THREAD_SUSPEND_RESUME
                    if not thread:
                        break
                    try:
                        if k.ResumeThread(thread) != 1:
                            break
                        return
                    finally:
                        k.CloseHandle(thread)
                entry.size = c.sizeof(entry)
                found = k.Thread32Next(snapshot, c.byref(entry))
            raise CollectorError("process-containment-failed")
        finally:
            k.CloseHandle(snapshot)

    def close(self):
        if self.handle:
            self.k.CloseHandle(self.handle)
            self.handle = None


class Probe:
    """Bounded stdout, discarded stderr, finite lifetime; owns only this child."""
    def __init__(self, argv, timeout=30, max_bytes=MAX_BYTES, cwd=None, env=None):
        self.deadline = time.monotonic() + timeout
        self.max_bytes, self.read_bytes = max_bytes, 0
        self.messages, self.stop = queue.Queue(maxsize=32), threading.Event()
        self.writers, self.written = [], 0
        self.job = WindowsJob() if os.name == "nt" else None
        kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP | 0x4} if self.job else {"start_new_session": True}
        try:
            self.process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                            bufsize=0, shell=False, cwd=cwd, env=env, **kwargs)
            if self.job:
                self.job.contain_and_resume(self.process)
        except Exception:
            if self.job:
                self.job.close()
            if getattr(self, "process", None):
                self.process.kill()
                self.process.wait(timeout=5)
                self.process.stdin.close()
                self.process.stdout.close()
            raise
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        while not self.stop.is_set():
            line = self.process.stdout.readline(self.max_bytes + 1)
            while not self.stop.is_set():
                try:
                    self.messages.put(line, timeout=0.1)
                    break
                except queue.Full:
                    pass
            if not line or len(line) > self.max_bytes:
                break

    def line(self):
        if time.monotonic() >= self.deadline:
            raise CollectorError("timeout")
        try:
            line = self.messages.get(timeout=max(0, self.deadline - time.monotonic()))
        except queue.Empty:
            raise CollectorError("timeout") from None
        self.read_bytes += len(line)
        if self.read_bytes > self.max_bytes:
            raise CollectorError("output-limit")
        return line

    def close(self):
        self.stop.set()
        if self.job:
            self.job.close()  # Also kills descendants after the root has exited.
        else:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.process.wait(timeout=5)
        self.reader.join(timeout=1)
        for writer in self.writers:
            writer.join(timeout=1)
        self.process.stdin.close()
        self.process.stdout.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class Rpc(Probe):
    def send(self, message):
        if time.monotonic() >= self.deadline:
            raise CollectorError("timeout")
        payload = (json.dumps(message) + "\n").encode("utf-8")
        self.written += len(payload)
        if len(payload) > 4096 or self.written > 16384:
            raise CollectorError("write-limit")
        outcome = queue.Queue(maxsize=1)
        def write():
            try:
                view = memoryview(payload)
                while view:
                    size = self.process.stdin.write(view)
                    if not size:
                        raise OSError()
                    view = view[size:]
                outcome.put(True)
            except (OSError, ValueError):
                outcome.put(False)
        writer = threading.Thread(target=write, daemon=True)
        self.writers.append(writer)
        writer.start()
        try:
            if not outcome.get(timeout=max(0, self.deadline - time.monotonic())):
                raise CollectorError("protocol-closed")
        except queue.Empty:
            raise CollectorError("timeout") from None

    def request(self, method, params):
        if method not in RPC_METHODS:
            raise CollectorError("method-forbidden")
        self.serial = getattr(self, "serial", 0) + 1
        request_id = self.serial
        self.send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        while True:
            line = self.line()
            if not line:
                raise CollectorError("protocol-closed")
            response = obj(strict_json(line))
            if "method" in response:
                if "id" in response:
                    # This client cannot satisfy fs/tool/auth requests. Do not
                    # echo unbounded or sensitive server-supplied identifiers.
                    raise CollectorError("server-request-forbidden")
                continue  # Never execute a server-originated fs/tool/auth request.
            if type(response.get("id")) is not int or response["id"] != request_id:
                continue
            if "error" in response:
                raise CollectorError("rpc-error", obj(response["error"]).get("code"))
            if "result" not in response:
                raise CollectorError("protocol-error")
            return response["result"]


def run_text(argv, cwd, env):
    with Probe(argv, cwd=cwd, env=env) as probe:
        output = bytearray()
        while True:
            line = probe.line()
            if not line:
                break
            output.extend(line)
        try:
            rc = probe.process.wait(timeout=max(0.01, probe.deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            raise CollectorError("timeout") from None
        # Claude logged-out auth status is a valid diagnostic with exit code 1.
        if rc not in (0, 1):
            raise CollectorError("cli-failed")
        try:
            return output.decode("utf-8-sig"), rc
        except UnicodeError:
            raise CollectorError("invalid-encoding") from None


def resolve_command(surface):
    name = "agy" if surface == "antigravity" else surface
    path = shutil.which(name)
    if not path:
        raise CollectorError("cli-not-found")
    binary = Path(path).resolve()
    if binary.suffix.lower() in (".cmd", ".bat", ".ps1"):
        # Known npm installation only: do not evaluate arbitrary wrapper text.
        entry = binary.parent / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
        node = shutil.which("node")
        if surface != "codex" or not entry.is_file() or not node:
            raise CollectorError("cli-wrapper-unsupported")
        return [str(Path(node).resolve()), str(entry)]
    return [str(binary)]


def child_env(parent, surface):
    profile_key = {"codex": "CODEX_HOME", "claude": "CLAUDE_CONFIG_DIR", "grok": "GROK_HOME"}.get(surface)
    allowed = BASE_ENV | ({profile_key} if profile_key else set())
    result = {k: v for k, v in parent.items() if k.upper() in allowed}
    result.update(AGY_CLI_DISABLE_AUTO_UPDATE="1", NO_COLOR="1")
    return result


class LocalBackend:
    def collect(self, surface):
        command = resolve_command(surface)
        env = child_env(os.environ, surface)
        profile_key = {"codex": "CODEX_HOME", "claude": "CLAUDE_CONFIG_DIR", "grok": "GROK_HOME"}.get(surface)
        profile = str(Path(os.environ.get(profile_key, str(Path.home() / ("." + surface))))
                      .expanduser().resolve()) if profile_key else "host-agy-session"
        with tempfile.TemporaryDirectory(prefix="vibe-metadata-") as cwd:
            if surface == "codex":
                with Rpc([*command, "app-server", "--stdio"], cwd=cwd, env=env) as rpc:
                    init = rpc.request("initialize", {"clientInfo": {"name": "vibe-metadata", "version": "1"},
                                                       "capabilities": {"experimentalApi": False}})
                    if os.path.normcase(os.path.normpath(obj(init).get("codexHome", ""))) != os.path.normcase(os.path.normpath(profile)):
                        raise CollectorError("profile-mismatch")
                    rpc.send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
                    raw = {"initialize": init, "account": rpc.request("account/read", {"refreshToken": False}),
                           "models": rpc.request("model/list", {"includeHidden": False}),
                           "limits": rpc.request("account/rateLimits/read", {})}
                    # Account switches during one collection invalidate the combined snapshot.
                    if raw["account"] != rpc.request("account/read", {"refreshToken": False}):
                        raise CollectorError("account-changed")
            elif surface == "grok":
                with Rpc([*command, "agent", "--no-leader", "stdio"], cwd=cwd, env=env) as rpc:
                    init = rpc.request("initialize", {"protocolVersion": 1,
                        "clientCapabilities": {"fs": {"readTextFile": False, "writeTextFile": False}, "terminal": False},
                        "clientInfo": {"name": "vibe-metadata", "version": "1"}})
                    if obj(init).get("protocolVersion") != 1:
                        raise CollectorError("protocol-version-unsupported")
                    try:
                        raw = rpc.request("_x.ai/billing", {})
                    except CollectorError as exc:
                        if exc.rpc_code != -32601:
                            raise
                        raw = rpc.request("x.ai/billing", {})
            elif surface == "claude":
                text, _ = run_text([*command, "auth", "status", "--json"], cwd, env)
                raw = strict_json(text)
            else:
                version, rc = run_text([*command, "--version"], cwd, env)
                match = re.search(r"\b(\d+\.\d+\.\d+)\b", version)
                if rc != 0 or not match or match[1] not in AGY_USAGE_VERSIONS:
                    raise CollectorError("usage-contract-unverified")
                text, rc = run_text([*command, "-p", "/usage", "--output-format", "json", "--print-timeout", "30s"], cwd, env)
                if rc != 0:
                    raise CollectorError("cli-failed")
                raw = strict_json(text)
        return raw, profile


def snapshot(observations, now, registry=None):
    registry = registry if registry is not None else load_registry()
    facts = {m["id"]: m for m in registry["models"]}
    candidates = []
    for observation in observations:
        for model in observation.get("models", []):
            fact = facts.get(model["model"])
            if not fact or fact["surface"] != observation["surface"]:
                continue
            candidates.append({"id": observation["surface"] + ":" + model["model"],
                "surface": observation["surface"], "transport": "cli", "model": model["model"],
                "lifecycle": fact["lifecycle"], "available": False, "observed_at": observation["observed_at"],
                "evidence": observation["source"], "effective_effort": None, "resolved_model": None,
                "provider_efforts": list(fact["api_efforts"] or []), "transport_efforts": model["transport_efforts"],
                "billing": {**copy.deepcopy(observation["billing"]), "account_ref": observation["account_ref"]},
                "quota": {"used_pct": None, "observed_at": observation["observed_at"], "bucket": None},
                "pending_evidence": ["generation-probe", "model-billing", "model-quota-binding", "task-policy"]})
    return {"schema_version": 1, "observed_at": now, "candidates": candidates,
            "tools": [], "observations": observations, "metadata_only": True}


def collect_all(surfaces, backend=None, now=None):
    backend = backend or LocalBackend()
    observations = []
    for surface in surfaces:
        observed = now or utc_now()  # Per-provider start, never refresh an older measurement.
        try:
            raw, profile = backend.collect(surface)
            observations.append(normalize(surface, raw, observed, profile))
        except (CollectorError, OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
            observations.append({"surface": surface, "observed_at": observed, "state": "error",
                                 "error_code": exc.code if isinstance(exc, CollectorError) else "collector-failed"})
    return snapshot(observations, now or utc_now())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", choices=SURFACES, action="append", required=True,
                        help="Explicit metadata-only surface; repeat to collect more than one")
    args = parser.parse_args(argv)
    result = collect_all(list(dict.fromkeys(args.surface)))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 2 if any(o["state"] != "ok" for o in result["observations"]) else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
