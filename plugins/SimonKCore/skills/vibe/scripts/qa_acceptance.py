"""Bridge to the reviewed QA 2.1 gate; no search of home, commands or network.

The coordinator supplies an explicit installed/source qa skill root. Only the
pinned helper bytes may run. This verifies consistency, not execution identity.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import types

# LF-normalized so a Git CRLF checkout and its Linux package use the same code.
QA_GATE_SHA256 = "cb97e0680d9ad11b316da734697e670e82bc3ec86e102f91b8bd398238d946eb"
MAX_JSON = 1024 * 1024


class QaError(ValueError):
    pass


def required(plan):
    return any(n.get("writes") or n.get("proc") == "coding"
               or n.get("task_type") in {"CODE_NEW", "CODE_FIX", "CODE_SIMPLE", "CODE_COMPLEX"}
               or "qa" in n.get("skills", []) for n in plan["steps"])


def _read(path, limit=MAX_JSON):
    try:
        with Path(path).open("rb") as stream:
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise QaError("QA_INPUT_TOO_LARGE")
        return data
    except OSError:
        raise QaError("QA_INPUT_UNAVAILABLE") from None


def _helper(binding):
    try:
        path = Path(binding["qa_skill"]) / "scripts" / "qa_gate.py"
        data = _read(path).replace(b"\r\n", b"\n")
    except (QaError, KeyError, TypeError):
        raise QaError("QA_HELPER_UNAVAILABLE") from None
    if hashlib.sha256(data).hexdigest() != QA_GATE_SHA256:
        raise QaError("QA_HELPER_CHANGED")
    # Compile the exact checked bytes, never reopen a path after checking it.
    module = types.ModuleType("vibe_pinned_qa_gate")
    exec(compile(data, str(path), "exec"), module.__dict__)
    return module


def binding(value):
    keys = {"qa_skill", "contract", "results", "evidence_root",
            "contract_sha256", "revision", "environment"}
    if not isinstance(value, dict) or set(value) not in (keys, keys | {"approval"}):
        raise QaError("QA_BINDING_INVALID")
    if any(not isinstance(v, str) or not v.strip() for v in value.values()):
        raise QaError("QA_BINDING_INVALID")
    if not re.fullmatch(r"[0-9a-f]{64}", value["contract_sha256"]):
        raise QaError("QA_BINDING_INVALID")
    result = dict(value)
    for key in ("qa_skill", "contract", "results", "evidence_root", "approval"):
        if key in result:
            path = Path(result[key])
            if not path.is_absolute():
                raise QaError("QA_ABSOLUTE_PATH_REQUIRED")
            result[key] = str(path.resolve())
    return result


def validate_binding(value):
    _helper(value)
    if hashlib.sha256(_read(value["contract"])).hexdigest() != value["contract_sha256"]:
        raise QaError("QA_CONTRACT_CHANGED")


def audit(value):
    gate = _helper(value)
    code, report = gate.audit(contract_path=value["contract"], results_path=value["results"],
        evidence_root=value["evidence_root"], contract_sha256=value["contract_sha256"],
        revision=value["revision"], environment=value["environment"], approval_path=value.get("approval"))
    return code, report
