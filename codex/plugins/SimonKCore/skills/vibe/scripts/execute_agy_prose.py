#!/usr/bin/env python3
"""Draft Korean prose or a read-only advisory response from an approved nonconfidential brief.
Use the model and task type in the handoff. The runner checks the exact agy catalog
slug and its included usage immediately before sending. No automatic retry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from datetime import datetime, timezone

if __name__ == "__main__":
    sys.dont_write_bytecode = True
import agy_lanes
import orchestrate
import runtime_collect
from ledger import scan_secrets

MODEL = orchestrate.AGY_PROSE_MODEL
TIMEOUT_SECONDS = 600
MAX_BRIEF_BYTES = 65536
MAX_OUTPUT_BYTES = 4 * 1024 * 1024
BRIEF_NAME = "00_BRIEF.md"
# Fixed instruction: the request itself stays in the brief file.
PROMPT = ("이 작업 폴더의 " + BRIEF_NAME + " 를 읽고 그 요청대로 한국어 글의 초안을 써라. "
          "파일을 만들거나 고치지 말고 명령도 실행하지 마라. 브리프에 없는 수치·고유명사·사실을 "
          "지어내지 마라. 답에는 완성된 초안만 마크다운으로 쓴다.")
ADVISORY_PROMPT = ("Read 00_BRIEF.md and answer the specified task from the supplied text. "
                   "Do not change files or run commands. Identify missing evidence explicitly.")
FACT_CHECK = ["numbers", "proper nouns", "claims and dates"]


class ProseError(Exception):
    def __init__(self, code, exit_code=4, detail=None):
        super().__init__(code)
        self.code, self.exit_code, self.detail = code, exit_code, detail


class SendInterrupted(Exception):
    """The send started but did not finish cleanly; `stdout` is what agy printed."""
    def __init__(self, code, stdout=b""):
        super().__init__(code)
        self.code = code
        self.stdout = stdout.decode("utf-8", errors="replace") if isinstance(stdout, bytes) else stdout


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def build_argv(command, model=MODEL, task_type="KOREAN_PROSE"):
    prompt = PROMPT if task_type == "KOREAN_PROSE" else ADVISORY_PROMPT
    return [*command, "--print", prompt, "--model", model, "--mode", "plan", "--sandbox",
            "--disable-slash-commands", "--output-format", "json",
            "--print-timeout", str(TIMEOUT_SECONDS) + "s"]


def parse_result(text):
    """Read agy's print-mode JSON; anything else is an unknown outcome."""
    try:
        data = json.loads(text)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else None
    return {"status": data.get("status"), "response": data.get("response"),
            "conversation_id": data.get("conversation_id"),
            "num_turns": data.get("num_turns"), "duration_seconds": data.get("duration_seconds"),
            "usage": usage}


def gate(observation, now, model=MODEL):
    """D-74 / D-126 check. Returns (reasons, tool); an empty list means open."""
    tool = runtime_collect.agy_prose_tool(observation, model)
    if tool is None:
        return ["PROSE_AGY_SUBSCRIPTION_UNVERIFIED"], None
    return orchestrate.assess_agy_usage(tool, now), tool


def collect_observation():
    now = utc_now()
    raw, profile = runtime_collect.LocalBackend().collect("antigravity")
    return runtime_collect.normalize("antigravity", raw, now, profile)


def run_agy(argv, workdir, env, timeout=TIMEOUT_SECONDS + 60):
    """Send once inside a job object that also ends agy's child processes."""
    with runtime_collect.Probe(argv, timeout=timeout, max_bytes=MAX_OUTPUT_BYTES,
                               cwd=str(workdir), env=env) as probe:
        try:
            probe.process.stdin.close()
        except OSError:
            pass
        raw = bytearray()
        try:
            while True:
                line = probe.line()
                if not line:
                    break
                raw.extend(line)
            rc = probe.process.wait(timeout=max(0.01, probe.deadline - runtime_collect.time.monotonic()))
        except runtime_collect.subprocess.TimeoutExpired:
            raise SendInterrupted("timeout", bytes(raw)) from None
        except runtime_collect.CollectorError as exc:
            raise SendInterrupted(exc.code, bytes(raw)) from None
    return rc, bytes(raw).decode("utf-8", errors="replace")


def check_output(out):
    path = Path(out)
    if (not path.is_absolute() or path.suffix.lower() not in (".md", ".txt") or not path.parent.is_dir()
            or path.exists() or receipt_path(path).exists()):
        raise ProseError("OUTPUT_PATH_INVALID", exit_code=2,
                         detail="absolute .md or .txt path in an existing folder, not already present")
    return path


def receipt_path(out):
    return out.with_name(out.stem + ".receipt.json")


def write_new(path, data):
    with open(path, "xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def usage_summary(tool):
    return {key: tool["quota"][key] for key in ("used_pct", "bucket", "observed_at")}


def draft(brief, out, not_confidential, *, collect=collect_observation, run=run_agy,
          command=None, now=None, model=MODEL, task_type="KOREAN_PROSE", expected_profile=None):
    """Return (exit_code, receipt). The receipt is also written beside the draft."""
    if not (model in agy_lanes.PROSE_MODELS if task_type == "KOREAN_PROSE"
            else task_type in agy_lanes.ADVISORY_MODELS.get(model, ())):
        raise ProseError("AGY_TASK_MODEL_MISMATCH", exit_code=2)
    started = now or utc_now()
    receipt = {"schema": "vibe-agy-prose-v1", "decision": "D-131", "status": "failed",
               "started_at": started, "model": model, "task_type": task_type, "fact_check_required": FACT_CHECK}
    if not_confidential is not True:
        raise ProseError("CONFIDENTIALITY_UNCONFIRMED", exit_code=2,
                         detail="pass --not-confidential after checking the brief; company-confidential material never goes to agy")
    if not isinstance(brief, str) or not brief.strip():
        raise ProseError("BRIEF_REQUIRED", exit_code=2)
    if len(brief.encode("utf-8")) > MAX_BRIEF_BYTES:
        raise ProseError("BRIEF_TOO_LARGE", exit_code=2)
    if scan_secrets(brief):
        raise ProseError("SENSITIVE_PAYLOAD", exit_code=2)
    out = check_output(out)
    receipt["brief_sha256"] = hashlib.sha256(brief.encode("utf-8")).hexdigest()
    observation = collect()
    # Judge after collecting: an observation newer than the clock is not fresh.
    reasons, tool = gate(observation, now or utc_now(), model)
    if expected_profile and observation.get("profile_ref") != expected_profile:
        reasons.append("AGY_PROFILE_CHANGED")
    if tool is not None:
        receipt["usage_before"] = usage_summary(tool)
    if reasons:
        receipt.update(status="refused", reasons=reasons)
        return 3, receipt
    workdir = Path(tempfile.mkdtemp(prefix="vibe-agy-prose-"))
    try:
        (workdir / BRIEF_NAME).write_text(brief, encoding="utf-8")
        command = command or runtime_collect.resolve_command("antigravity")
        env = runtime_collect.child_env(os.environ, "antigravity")
        try:
            rc, stdout = run(build_argv(command, model, task_type), workdir, env)
        except SendInterrupted as exc:
            # The request may have reached agy; report it and do not resend.
            receipt.update(status="unknown", reasons=["AGY_SEND_OUTCOME_UNKNOWN:" + exc.code])
            return 4, receipt
        except (runtime_collect.CollectorError, OSError) as exc:
            receipt.update(status="unknown", reasons=["AGY_SEND_OUTCOME_UNKNOWN:" + str(exc)])
            return 4, receipt
        result = parse_result(stdout)
        receipt["agy"] = {"exit_code": rc, **{k: v for k, v in (result or {}).items() if k != "response"}}
        response = (result or {}).get("response")
        if (rc != 0 or not result or result["status"] != "SUCCESS"
                or not isinstance(response, str) or not response.strip()):
            receipt.update(reasons=["AGY_PRINT_FAILED"],
                           excerpt=(response if isinstance(response, str) else stdout)[-300:])
            return 4, receipt
        text = response.strip() + "\n"
        try:
            write_new(out, text.encode("utf-8"))
        except OSError as exc:
            receipt.update(reasons=["OUTPUT_WRITE_FAILED"], detail=str(exc))
            return 4, receipt
        receipt["draft"] = {"path": str(out), "chars": len(text),
                            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
        receipt["status"] = "succeeded"
        # Usage after the send (zero-turn); used for the D-126 per-draft usage condition.
        try:
            after = runtime_collect.agy_prose_tool(collect(), model)
            receipt["usage_after"] = usage_summary(after) if after else None
        except (runtime_collect.CollectorError, OSError) as exc:
            receipt["usage_after"] = {"error": str(exc)}
        return 0, receipt
    finally:
        receipt["finished_at"] = utc_now()
        shutil.rmtree(workdir, ignore_errors=True)
        if receipt["status"] != "refused":
            try:
                write_new(receipt_path(out), json.dumps(receipt, ensure_ascii=False,
                                                        indent=2).encode("utf-8"))
            except OSError:
                pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--brief", help="Korean writing request with its source facts")
    source.add_argument("--brief-file", help="UTF-8 file holding the request and source facts")
    parser.add_argument("--out", required=True, help="Absolute path of the new .md or .txt draft")
    parser.add_argument("--not-confidential", action="store_true",
                        help="Confirm the brief holds no company-confidential material")
    parser.add_argument("--model", choices=sorted(agy_lanes.MODELS), default=MODEL)
    parser.add_argument("--task-type", default="KOREAN_PROSE")
    parser.add_argument("--expected-profile", help="Profile binding from the planned route")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        brief = (args.brief if args.brief is not None
                 else Path(args.brief_file).read_text(encoding="utf-8"))
        code, receipt = draft(brief, args.out, args.not_confidential, model=args.model,
                              task_type=args.task_type, expected_profile=args.expected_profile)
    except ProseError as exc:
        code, receipt = exc.exit_code, {"status": "failed", "reasons": [exc.code],
                                        "detail": exc.detail}
    except (OSError, UnicodeError, runtime_collect.CollectorError) as exc:
        code, receipt = 4, {"status": "failed", "reasons": [type(exc).__name__ + ":" + str(exc)]}
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
