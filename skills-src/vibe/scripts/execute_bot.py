#!/usr/bin/env python3
"""One-shot Bot hub publisher using the central Store; no Bot/API calls.

Trusted coordinator input: a registered GUI plan with immutable bot_delivery
pins, plus fresh account/Relay/cost and delivery authority evidence. No proof
factory, default bus, DB initialization, automatic resend or settlement.
Publishing to a watched directory IS an external-effect boundary even though
this module makes no network requests. Fixture success is not Relay acceptance.
See vibe-bot/SKILL.md for the descriptor and CLI contract.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid

import orchestrate
from run_state import Store, StateError, TERMINAL, evidence, identifier, moment, read_payload, safe_json, strict_loads, validate_plan

LIMIT = 1024 * 1024
FIELDS = {"nonce", "bot_root", "bus_root", "spec_path", "meta_path", "spec_sha256",
          "meta_sha256", "helper_sha256", "roster_sha256"}


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


def binding_digest(plan, node_id):
    return orchestrate.digest({"plan_digest": plan["plan_digest"], "node_id": node_id,
                              "delivery": selected(plan, node_id)["bot_delivery"]})


def request_id(plan, node_id):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "simonk:vibe:bot-hub:v1:" + binding_digest(plan, node_id)))


def exact_path(value):
    """No implicit home, remote drive, links/reparse parents or alternate streams.

    Cooperating single-writer directories are required. These checks are not an
    adversarial OS-user lock or a filesystem/network sandbox.
    """
    require(isinstance(value, str), "EXACT_LOCAL_PATH_REQUIRED")
    path = Path(value)
    require(path.is_absolute() and not str(path).startswith("\\\\")
            and not any(":" in p for p in path.parts[1:]), "EXACT_LOCAL_PATH_REQUIRED")
    if os.name == "nt":
        import ctypes
        require(ctypes.windll.kernel32.GetDriveTypeW(str(path.anchor)) == 3, "LOCAL_FIXED_DISK_REQUIRED")
    for item in (*reversed(path.parents), path):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400,
                "LINKED_DELIVERY_PATH")
    require(str(path.resolve()) == value, "EXACT_LOCAL_PATH_REQUIRED")
    return path


def read_bytes(path, expected=None):
    exact_path(str(path))
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= LIMIT, "DELIVERY_FILE_INVALID")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        require((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino), "DELIVERY_FILE_CHANGED")
        raw = stream.read(LIMIT + 1)
    exact_path(str(path))
    require(len(raw) <= LIMIT, "DELIVERY_FILE_INVALID")
    if expected is not None:
        require(hashlib.sha256(raw).hexdigest() == expected, "DELIVERY_FILE_CHANGED")
    return raw


def publish(path, data):
    """Complete private .tmp -> atomic no-replace hard link. Never os.replace.

    The cooperating consumer must ignore non-.md staging and metadata files.
    Filesystem atomic visibility is not Bot acceptance or power-loss durability.
    """
    exact_path(str(path))
    fd, temporary = tempfile.mkstemp(prefix=".vibe-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        exact_path(str(path))
        os.link(temporary, path)  # Atomic create; an existing name fails, never overwrites.
    finally:
        os.unlink(temporary)  # Only this call's new staging file, never user data.


def pinned_builder(root, expected):
    helper = root / "scripts/make_bot_spec.py"
    raw = read_bytes(helper, expected)
    module = importlib.util.module_from_spec(importlib.util.spec_from_file_location("vibe_bot_builder", helper))
    # No loader.exec_module: timestamp-valid bytecode is not covered by this pin.
    exec(compile(raw, str(helper), "exec"), module.__dict__)
    return module


class Adapter:
    def __init__(self, store, clock=moment):
        self.store, self.clock = store, clock

    def context(self, plan, node_id):
        node = selected(plan, node_id)
        route, handoff = node["route"], node["handoff"]
        require(node["kind"] == "gui" and route["surface"] == "grok-bot"
                and route["transport"] == handoff["kind"] == "bot"
                and route.get("model") is None and route.get("requested_effort") is None,
                "BOT_ROUTE_REQUIRED")
        require(node.get("tool_route_available") is False and node.get("gui_reason")
                and handoff["mode"] == "console" and handoff["target"] == node["target"], "GUI_SCOPE_REQUIRED")
        bot_id = handoff["bot_id"]
        require(isinstance(bot_id, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", bot_id), "BOT_ID_INVALID")
        binding = node["bot_delivery"]
        require(isinstance(binding, dict) and set(binding) == FIELDS, "BOT_DELIVERY_REQUIRED")
        require(isinstance(binding["nonce"], str) and re.fullmatch(r"vb-[0-9a-f]{8,64}", binding["nonce"]), "BOT_NONCE_INVALID")
        for key in ("spec_sha256", "meta_sha256", "helper_sha256", "roster_sha256"):
            require(isinstance(binding[key], str) and re.fullmatch(r"[a-f0-9]{64}", binding[key]), "DELIVERY_HASH_REQUIRED")
        paths = {k: exact_path(binding[k]) for k in ("bot_root", "bus_root", "spec_path", "meta_path")}
        require(paths["bot_root"].is_dir() and paths["bus_root"].is_dir(), "DELIVERY_ROOT_REQUIRED")
        require(all(not paths[k].is_relative_to(paths["bus_root"]) for k in ("bot_root", "spec_path", "meta_path")),
                "DRAFT_IN_WATCHED_BUS")
        runs = [r for r in self.store.snapshot()["runs"] if r["run_id"] == plan["run_id"]]
        require(len(runs) == 1 and runs[0]["plan_digest"] == plan["plan_digest"], "REGISTERED_PLAN_REQUIRED")
        # Pin the specialist in the plan, but deliver/collect through Relay only.
        base = paths["bus_root"] / "relay"
        paths.update(inbox=base / "inbox" / (binding["nonce"] + ".md"),
                     meta=base / "inbox" / (binding["nonce"] + ".meta.json"),
                     result=base / "outbox" / (binding["nonce"] + ".result.md"))
        for path in paths.values():
            exact_path(str(path))
        return node, binding, paths

    def payload(self, plan, node_id, attempt=None):
        node, binding, paths = self.context(plan, node_id)
        spec = read_bytes(paths["spec_path"], binding["spec_sha256"])
        meta = strict_loads(read_bytes(paths["meta_path"], binding["meta_sha256"]).decode("utf-8"))
        safe_json(meta)
        require(isinstance(meta, dict) and meta.get("mode") == "console"
                and meta.get("nonce") == binding["nonce"] and meta.get("bot") == node["handoff"]["bot_id"]
                and meta.get("target") == node["target"] and meta.get("task") == node["task"]
                and "vibe" not in meta, "BOT_METADATA_MISMATCH")
        text = spec.decode("utf-8")
        safe_json({"spec": text})  # Screen ALL draft fields, not just --task.
        require(all(value in text for value in (binding["nonce"], node["target"], node["task"], str(paths["result"]))),
                "BOT_SPEC_SCOPE_MISMATCH")
        if attempt is not None:
            meta["vibe"] = {"run_id": plan["run_id"], "node_id": node_id,
                "plan_digest": plan["plan_digest"], "dispatch_id": attempt["dispatch_id"],
                "binding_sha256": binding_digest(plan, node_id)}
        return spec, (json.dumps(meta, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

    def gate(self, plan, node_id, certificate):
        node, binding, paths = self.context(plan, node_id)
        validate_plan(plan, self.clock())
        safe_json(certificate)
        require(isinstance(certificate, dict) and all(certificate.get(k) is True for k in
                ("verified", "delivery_authorized", "relay_verified", "all_delivery_costs_included")),
                "BOT_DELIVERY_EVIDENCE_REQUIRED")
        identifier(certificate.get("approval_ref"))
        evidence(certificate.get("evidence"))
        route = node["route"]
        require(certificate.get("binding_sha256") == binding_digest(plan, node_id)
                and certificate.get("account_ref") == route["billing"]["account_ref"]
                and certificate.get("relay_account_ref") == route["billing"]["account_ref"]
                and certificate.get("billing") == route["billing"] and certificate.get("quota") == route["quota"]
                and certificate.get("bot_id") == node["handoff"]["bot_id"]
                and certificate.get("bus_root") == binding["bus_root"], "BOT_DELIVERY_EVIDENCE_MISMATCH")
        require(orchestrate.fresh(certificate.get("observed_at"), self.clock())
                and orchestrate.instant(self.clock()) < orchestrate.instant(certificate.get("valid_until")),
                "BOT_DELIVERY_EVIDENCE_STALE")
        roster = strict_loads(read_bytes(paths["bot_root"] / "bots.json", binding["roster_sha256"]).decode("utf-8"))
        safe_json(roster)
        matches = [b for b in roster["bots"] if b.get("id") == node["handoff"]["bot_id"]]
        require(len(matches) == 1 and re.match(r"^active(?:\s|$)", matches[0].get("status", ""), re.I), "BOT_NOT_ACTIVE")
        relays = [b for b in roster["bots"] if b.get("id") == "relay"]
        require(len(relays) == 1 and re.match(r"^active(?:\s|$)", relays[0].get("status", ""), re.I), "RELAY_NOT_ACTIVE")
        module = pinned_builder(paths["bot_root"], binding["helper_sha256"])
        spec, _ = self.payload(plan, node_id)
        require(not module.check_request(node["task"])["blocks"], "BOT_REQUEST_BLOCKED")
        require(not module.check_request(spec.decode("utf-8"))["blocks"], "BOT_REQUEST_BLOCKED")
        return paths

    def attempt(self, plan, node_id):
        rows = [a for a in self.store.snapshot()["attempts"] if a["run_id"] == plan["run_id"] and a["node_id"] == node_id]
        require(len(rows) <= 1, "BOT_RETRY_UNSUPPORTED")
        if rows:
            require(rows[0]["request_id"] == request_id(plan, node_id)
                    and rows[0]["plan_digest"] == plan["plan_digest"], "BOT_DISPATCH_IDENTITY_CHANGED")
            return rows[0]
        return None

    def dispatch(self, plan, node_id, certificate):
        self.context(plan, node_id)
        if self.attempt(plan, node_id):
            return self.reconcile(plan, node_id)
        paths = self.gate(plan, node_id, certificate)
        require(not any(p.exists() for p in (paths["inbox"], paths["meta"], paths["result"])), "BOT_DELIVERY_COLLISION")
        claim = self.store.claim(plan["run_id"], node_id, request_id(plan, node_id), plan["plan_digest"], now=self.clock())
        if not claim["dispatch_allowed"]:
            return self.reconcile(plan, node_id)
        try:
            paths = self.gate(plan, node_id, certificate)
            spec, meta = self.payload(plan, node_id, claim)
            paths["inbox"].parent.mkdir(parents=True, exist_ok=True)
            paths["result"].parent.mkdir(parents=True, exist_ok=True)
            publish(paths["meta"], meta)
            self.gate(plan, node_id, certificate)  # Recheck authority before visible commit marker.
            publish(paths["inbox"], spec)
        except (StateError, OSError, ValueError, TypeError, KeyError):
            pass  # Partial publication is uncertain, never permission to resend.
        return self.reconcile(plan, node_id)

    def reconcile(self, plan, node_id):
        _, binding, paths = self.context(plan, node_id)
        attempt = self.attempt(plan, node_id)
        require(attempt is not None, "BOT_INTENT_REQUIRED")
        spec, meta = self.payload(plan, node_id, attempt)
        complete = False
        try:
            complete = read_bytes(paths["inbox"]) == spec and read_bytes(paths["meta"]) == meta
        except (OSError, StateError):
            pass
        if complete and attempt["state"] not in TERMINAL:
            handle = {"kind": "bot-hub", "id": binding["nonce"], "identity": binding_digest(plan, node_id)}
            self.store.bind(attempt["dispatch_id"], handle, now=self.clock())
            if self.attempt(plan, node_id)["state"] != "uncertain":
                self.store.observe(attempt["dispatch_id"], {"state": "unknown", "handle": handle,
                    "observed_at": self.clock(), "evidence": ["Exact local publication; Bot acceptance unobserved"]}, now=self.clock())
        current = self.attempt(plan, node_id)
        return {"status": "waiting_external" if complete else "uncertain", "dispatch_id": attempt["dispatch_id"],
            "nonce": binding["nonce"], "published": complete, "bot_acceptance_verified": False,
            "actual_usd": current["actual_usd"], "store_state": current["state"],
            "meta": str(paths["meta"]), "result": str(paths["result"])}

    def check_result(self, plan, node_id, evidence_path):
        result = self.reconcile(plan, node_id)
        if not result["published"]:
            return result
        _, binding, paths = self.context(plan, node_id)
        if not paths["result"].exists():
            return result
        text = read_bytes(paths["result"]).decode("utf-8")
        safe_json({"result": text})
        findings = []
        if not text.splitlines() or text.splitlines()[0] != binding["nonce"]:
            findings.append("BOT_FIRST_LINE_NONCE_MISMATCH")
        proof_path = exact_path(str(evidence_path))
        require(proof_path.is_relative_to(paths["result"].parent), "SCREEN_EVIDENCE_OUTSIDE_RESULT")
        proof = strict_loads(read_bytes(proof_path).decode("utf-8"))
        safe_json(proof)
        require(isinstance(proof, dict) and isinstance(proof.get("images"), list)
                and 1 <= len(proof["images"]) <= 32, "SCREEN_EVIDENCE_REQUIRED")
        require(proof.get("nonce") == binding["nonce"]
                and proof.get("target") == selected(plan, node_id)["target"], "BOT_EVIDENCE_MISMATCH")
        for name in proof["images"]:
            require(isinstance(name, str), "SCREEN_EVIDENCE_REQUIRED")
            image = exact_path(str(paths["result"].parent / name))
            require(image.is_relative_to(paths["result"].parent), "SCREEN_EVIDENCE_OUTSIDE_RESULT")
            require(stat.S_ISREG(image.stat().st_mode), "BOT_SCREENSHOT_INVALID")
            with image.open("rb") as stream:
                require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "BOT_SCREENSHOT_INVALID")
                magic = stream.read(12)
            if not (magic.startswith(b"\x89PNG\r\n\x1a\n") or magic.startswith(b"\xff\xd8\xff")):
                findings.append("BOT_SCREENSHOT_INVALID")
        module = pinned_builder(paths["bot_root"], binding["helper_sha256"])
        findings.extend(module.verify_result(text, binding["nonce"], mode="console"))
        result.update(status="result_checks_failed" if findings else "result_checks_passed", findings=findings,
                      requires_screen_inspection=True)
        return result  # Never observes completion, verifies output, or settles cost.


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("dispatch", "reconcile", "check-result"))
    for key in ("plan", "node", "db"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--certificate")
    parser.add_argument("--evidence")
    args = parser.parse_args(argv)
    try:
        adapter = Adapter(Store(args.db))
        plan = read_payload(args.plan)
        if args.command == "dispatch":
            require(args.certificate is not None, "BOT_DELIVERY_EVIDENCE_REQUIRED")
            result = adapter.dispatch(plan, args.node, read_payload(args.certificate))
        elif args.command == "check-result":
            require(args.evidence is not None, "SCREEN_EVIDENCE_REQUIRED")
            result = adapter.check_result(plan, args.node, args.evidence)
        else:
            result = adapter.reconcile(plan, args.node)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["status"] in ("waiting_external", "result_checks_passed") else 2
    except (StateError, OSError, ValueError, KeyError, TypeError, AttributeError):
        print(json.dumps({"status": "blocked", "error": "BOT_DELIVERY_UNVERIFIED"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
