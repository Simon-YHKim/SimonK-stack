#!/usr/bin/env python3
"""Check a pinned QA contract against scoped evidence. Never authorize a release.

Stdlib only. Reads trusted coordinator inputs and artifacts; executes no commands.
Exit 0: consistent passing evidence, 1: blocked, 2: invalid/unreadable input.
Hashes protect consistency, not truth, test completeness or reviewer identity.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys


MAX_JSON = 1024 * 1024
MAX_ARTIFACT = 64 * 1024 * 1024
HASH = re.compile(r"[a-f0-9]{64}\Z")
ID = re.compile(r"[A-Za-z0-9_.:-]{1,80}\Z")
SENSITIVE = {"authorization", "privacy", "payment", "deletion", "migration"}
RECOVERY = {"payment", "deletion", "migration"}
LEVELS = {"unit", "integration", "e2e", "visual"}
KINDS = {"positive", "negative", "boundary", "recovery", "concurrency"}


class Invalid(ValueError):
    """Input cannot be safely interpreted as the documented contract."""


def _object(value, required, optional=(), label="object"):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise Invalid(f"{label}: missing or unknown fields")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 10000 or "\0" in value:
        raise Invalid(f"{label}: expected nonempty text")
    return value


def _choice(value, choices, label):
    if not isinstance(value, str) or value not in choices:
        raise Invalid(f"{label}: unsupported value")
    return value


def _array(value, label, nonempty=True):
    if not isinstance(value, list) or (nonempty and not value) or len(value) > 2000:
        raise Invalid(f"{label}: expected bounded list" + (" with entries" if nonempty else ""))
    return value


def _identifier(value, seen, label):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise Invalid(f"{label}: invalid ID")
    if value in seen:
        raise Invalid(f"{label}: duplicate ID")
    seen.add(value)
    return value


def _hash(value, label):
    if not isinstance(value, str) or not HASH.fullmatch(value):
        raise Invalid(f"{label}: expected lowercase SHA-256")
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid("JSON: duplicate key")
        result[key] = value
    return result


def _constant(_):
    raise Invalid("JSON: non-finite number")


def _read(path):
    with Path(path).open("rb") as stream:
        data = stream.read(MAX_JSON + 1)
    if len(data) > MAX_JSON:
        raise Invalid("JSON exceeds 1 MiB")
    value = json.loads(data.decode("utf-8-sig"), object_pairs_hook=_pairs, parse_constant=_constant)
    if not isinstance(value, dict):
        raise Invalid("JSON: expected an object")
    return value, hashlib.sha256(data).hexdigest()


def _timestamp(value, label):
    _text(value, label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise Invalid(f"{label}: invalid timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise Invalid(f"{label}: timezone required")
    return parsed.astimezone(timezone.utc)


def _target(value):
    _object(value, ("revision", "environment"), label="target")
    for key in value:
        _text(value[key], f"target.{key}")
    return value


def _version(value):
    if type(value) is not int or value != 1:
        raise Invalid("schema_version must be integer 1")


def _artifacts(value, root, issues, label):
    _array(value, label, nonempty=False)
    if not value:
        issues.append(f"{label}: evidence is missing")
    for item in value:
        _object(item, ("path", "sha256"), label=label)
        name = _text(item["path"], f"{label}.path")
        digest = _hash(item["sha256"], label)
        relative = PurePosixPath(name)
        if (relative.is_absolute() or ".." in relative.parts or "\\" in name
                or ":" in name or any(ord(c) < 32 for c in name)):
            issues.append(f"{label}: unsafe artifact path")
            continue
        try:
            resolved = (root / name).resolve(strict=True)
            if not resolved.is_relative_to(root) or not resolved.is_file():
                issues.append(f"{label}: artifact outside root or not a regular file")
                continue
            with resolved.open("rb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_ARTIFACT:
                    issues.append(f"{label}: empty or oversized artifact")
                    continue
                hasher = hashlib.sha256()
                total = 0
                while chunk := stream.read(65536):
                    total += len(chunk)
                    if total > MAX_ARTIFACT:
                        break
                    hasher.update(chunk)
                if total == 0 or total > MAX_ARTIFACT or hasher.hexdigest() != digest:
                    issues.append(f"{label}: artifact hash or size mismatch")
        except (OSError, ValueError, RuntimeError):
            issues.append(f"{label}: artifact missing or unreadable")


def _observed(value, created, now, issues, label):
    observed = _timestamp(value, label)
    if observed < created or observed > now + timedelta(minutes=5):
        issues.append(f"{label}: evidence predates contract or is in the future")


def audit(*, contract_path, results_path, evidence_root, contract_sha256,
          revision, environment, approval_path=None):
    """Return (exit code, report); treat coordinator inputs as the trust boundary."""
    issues = []
    report = {"decision": "invalid", "release_authorized": False, "issues": issues,
              "scope": "Input consistency and artifact integrity only; no identity or execution attestation."}
    try:
        wanted = _target({"revision": revision, "environment": environment})
        pin = _hash(contract_sha256, "contract_sha256")
        contract, digest = _read(contract_path)
        if digest != pin:
            issues.append("contract hash does not match the independently supplied pin")
        _object(contract, ("schema_version", "created_at", "target", "requirements"), label="contract")
        _version(contract["schema_version"])
        if _target(contract["target"]) != wanted:
            issues.append("contract target differs from the trusted target")
        created = _timestamp(contract["created_at"], "created_at")
        now = datetime.now(timezone.utc)
        if created > now + timedelta(minutes=5):
            issues.append("contract created_at is in the future")
        root = Path(evidence_root).resolve(strict=True)
        if not root.is_dir():
            raise Invalid("evidence root must be a directory")
        planned, requirement_ids, check_ids = {}, set(), set()
        high_risk = False
        for req in _array(contract["requirements"], "requirements"):
            _object(req, ("id", "source_type", "source", "expected", "risk", "category",
                          "negative_testing", "checks"), ("negative_reason",), "requirement")
            rid = _identifier(req["id"], requirement_ids, "requirement")
            _choice(req["source_type"], {"user", "spec", "issue", "policy"}, f"{rid}.source_type")
            _text(req["source"], f"{rid}.source")
            _text(req["expected"], f"{rid}.expected")
            risk = _choice(req["risk"], {"low", "high"}, f"{rid}.risk")
            category = _choice(req["category"], SENSITIVE | {"functional"}, f"{rid}.category")
            high = risk == "high" or category in SENSITIVE
            high_risk |= high
            if category in SENSITIVE and risk != "high":
                issues.append(f"{rid}: sensitive category cannot be downgraded to low risk")
            negative = _choice(req["negative_testing"], {"required", "not_applicable"}, f"{rid}.negative_testing")
            if negative == "not_applicable":
                # Optional in the general shape, mandatory for this exemption.
                if "negative_reason" not in req:
                    raise Invalid(f"{rid}: negative_reason is required for not_applicable")
                _text(req["negative_reason"], f"{rid}.negative_reason")
                if high:
                    issues.append(f"{rid}: high risk cannot exempt negative checks")
            kinds, boundary_kinds = set(), set()
            for check in _array(req["checks"], f"{rid}.checks"):
                _object(check, ("id", "kind", "level", "expected"), label="planned check")
                cid = _identifier(check["id"], check_ids, "planned check")
                kind = _choice(check["kind"], KINDS, f"{cid}.kind")
                level = _choice(check["level"], LEVELS, f"{cid}.level")
                _text(check["expected"], f"{cid}.expected")
                kinds.add(kind)
                if level in {"integration", "e2e"}:
                    boundary_kinds.add(kind)
                planned[cid] = check
            if "positive" not in kinds:
                issues.append(f"{rid}: positive check missing")
            if negative == "required" and "negative" not in kinds:
                issues.append(f"{rid}: negative check missing")
            if high:
                extra = "recovery" if category in RECOVERY else "boundary"
                for kind in {"negative", extra} - boundary_kinds:
                    issues.append(f"{rid}: high risk requires {kind} integration/e2e check")

        results, _ = _read(results_path)
        _object(results, ("schema_version", "contract_sha256", "target", "checks"), label="results")
        _version(results["schema_version"])
        if _hash(results["contract_sha256"], "results contract hash") != pin:
            issues.append("results do not match the pinned contract")
        if _target(results["target"]) != wanted:
            issues.append("results target differs from the trusted target")
        seen = set()
        for check in _array(results["checks"], "results.checks", nonempty=False):
            _object(check, ("id", "status"), ("level", "mocked", "command", "exit_code",
                    "observed_at", "actual", "counts", "evidence"), "observed check")
            cid = _identifier(check["id"], seen, "observed check")
            status = _choice(check["status"], {"passed", "failed", "blocked", "not_run", "skipped"}, f"{cid}.status")
            if cid not in planned:
                issues.append(f"{cid}: unplanned check cannot replace required checks")
                continue
            if status != "passed":
                issues.append(f"{cid}: required check is {status}")
                continue
            # Failed/not-run checks may have no execution data. A passed claim
            # must provide the full shape; omission is invalid, never a pass.
            _object(check, ("id", "status", "level", "mocked", "command", "exit_code",
                    "observed_at", "actual", "counts", "evidence"), label=f"{cid}: passed check")
            _text(check.get("command"), f"{cid}.command")
            _text(check.get("actual"), f"{cid}.actual")
            if type(check.get("exit_code")) is not int or check["exit_code"] != 0:
                issues.append(f"{cid}: passed claim requires process exit code 0")
            if check.get("level") != planned[cid]["level"]:
                issues.append(f"{cid}: evidence level differs from the contract")
            if type(check.get("mocked")) is not bool:
                raise Invalid(f"{cid}: mocked must be a boolean")
            if planned[cid]["level"] in {"integration", "e2e"} and check["mocked"]:
                issues.append(f"{cid}: mocked boundary cannot prove integration/e2e acceptance")
            counts = _object(check.get("counts"), ("passed", "failed", "skipped"), label=f"{cid}.counts")
            if (any(type(n) is not int or n < 0 for n in counts.values())
                    or counts["passed"] < 1 or counts["failed"] != 0 or counts["skipped"] != 0):
                issues.append(f"{cid}: positive passed assertions and zero failed/skipped assertions required")
            _observed(check.get("observed_at"), created, now, issues, cid)
            _artifacts(check.get("evidence"), root, issues, cid)
        for cid in sorted(set(planned) - seen):
            issues.append(f"{cid}: required check not_run (missing result)")

        if high_risk and approval_path is None:
            issues.append("high-risk human review evidence is missing")
        if approval_path is not None:
            approval, _ = _read(approval_path)
            _object(approval, ("schema_version", "contract_sha256", "target", "decision",
                    "reviewer_type", "reviewer", "observed_at", "evidence"), label="approval")
            _version(approval["schema_version"])
            _text(approval["reviewer"], "reviewer")
            if approval["reviewer_type"] != "human" or approval["decision"] != "approved":
                issues.append("review must be a separately supplied human approval")
            if _hash(approval["contract_sha256"], "approval contract hash") != pin or _target(approval["target"]) != wanted:
                issues.append("review target/contract does not match")
            _observed(approval["observed_at"], created, now, issues, "review")
            _artifacts(approval["evidence"], root, issues, "review")
        report.update(decision="blocked" if issues else "pass", requirements=len(requirement_ids),
                      required_checks=len(planned), received_checks=len(seen), high_risk=high_risk)
        return (1 if issues else 0), report
    except (Invalid, OSError, ValueError, TypeError, OverflowError, RecursionError, RuntimeError):
        # Never print input values or file contents; evidence may contain sensitive data.
        error = sys.exc_info()[1]
        issues.append(str(error) if isinstance(error, Invalid) else "Unreadable or malformed input")
        return 2, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("contract", "results", "evidence-root"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("contract-sha256", "revision", "environment"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--approval", type=Path)
    args = parser.parse_args(argv)
    code, report = audit(contract_path=args.contract, results_path=args.results,
                         evidence_root=args.evidence_root, contract_sha256=args.contract_sha256,
                         revision=args.revision, environment=args.environment, approval_path=args.approval)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
