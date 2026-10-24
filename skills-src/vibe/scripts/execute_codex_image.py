#!/usr/bin/env python3
"""Generate an image with Codex's built-in image_gen (hub D-121, Simon 2026-10-24).

One `codex exec` per call and never an automatic retry. Before sending, it reads
the Codex account and usage through the app-server (no model turn) and refuses
when the D-74 usage gate is closed: no ChatGPT login, unverified account, stale
usage, usage at or above 85 percent, or a reached rate limit or spend control.
The image bytes come from the session rollout, never from a path the model names.

    python execute_codex_image.py --prompt "a blue circle" --out C:/abs/circle.png
    python execute_codex_image.py --prompt-file brief.txt --out C:/abs/a.png --transparent

Exit codes: 0 image written, 2 bad arguments, 3 refused by the usage gate or by
Codex's own usage limit, 4 failed (the outcome is reported; nothing is resent).
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
from datetime import datetime, timezone

if __name__ == "__main__":
    sys.dont_write_bytecode = True
import orchestrate
import runtime_collect
from ledger import scan_secrets

# D-101: the GPT side runs gpt-6-astra at xhigh only. It drives the image_gen call.
DRIVER_MODEL = "gpt-6-astra"
DRIVER_EFFORT = "xhigh"
TIMEOUT_SECONDS = 600
MAX_PROMPT_BYTES = 32768
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# Codex's usage-limit messages as `codex exec --json` prints them (codex-rs error
# texts; list as recorded by aldegad/sprite-gen, Apache-2.0). Matched by prefix.
USAGE_LIMIT_PREFIXES = (
    "You've hit your usage limit", "You\u2019ve hit your usage limit",
    "Your workspace is out of credits.", "You hit your spend cap set",
    "Quota exceeded. Check your plan and billing details.",
    "To use Codex with your ChatGPT plan, upgrade to Plus",
)
TRANSPARENT_LINE = ("Ask image_gen for a transparent background and keep the generated "
                    "alpha channel (a PNG with real transparency, no checkerboard).")


class ImageError(Exception):
    def __init__(self, code, exit_code=4, detail=None):
        super().__init__(code)
        self.code, self.exit_code, self.detail = code, exit_code, detail


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def build_prompt(brief, transparent=False):
    lines = ["Use the built-in image_gen tool exactly once to create the image described "
             "below. Do not run shell commands and do not write files yourself. After the "
             "image is generated, reply with exactly one line: DONE", ""]
    if transparent:
        lines += [TRANSPARENT_LINE, ""]
    return "\n".join(lines + ["Image brief:", brief.strip()]) + "\n"


def build_argv(command, workdir):
    # workspace-write: image_gen is not offered in a read-only sandbox.
    return [*command, "exec", "--json", "--ignore-user-config", "--skip-git-repo-check",
            "--sandbox", "workspace-write", "-C", str(workdir), "-m", DRIVER_MODEL,
            "-c", 'model_reasoning_effort="' + DRIVER_EFFORT + '"', "-"]


def parse_stream(text):
    """Read the `codex exec --json` event stream; unknown lines are ignored."""
    result = {"thread_id": None, "completed": False, "usage": None, "errors": [], "messages": []}
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        if kind == "thread.started" and isinstance(event.get("thread_id"), str):
            result["thread_id"] = result["thread_id"] or event["thread_id"]
        elif kind == "turn.completed":
            result["completed"] = True
            usage = event.get("usage")
            result["usage"] = usage if isinstance(usage, dict) else None
        elif kind in ("error", "turn.failed"):
            message = event.get("message") or (event.get("error") or {}).get("message")
            if isinstance(message, str):
                result["errors"].append(message)
        elif kind == "item.completed" and isinstance(event.get("item"), dict):
            item = event["item"]
            if item.get("type") == "error" and isinstance(item.get("message"), str):
                result["errors"].append(item["message"])
            elif item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                result["messages"].append(item["text"])
    return result


def usage_limit_message(messages):
    for message in messages:
        text = message.strip()
        if any(text.startswith(prefix) for prefix in USAGE_LIMIT_PREFIXES):
            return text
    return None


def codex_home():
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser().resolve()


def rollout_files(sessions_root):
    root = Path(sessions_root)
    if not root.is_dir():
        return set()
    return {path.resolve() for path in root.rglob("rollout-*.jsonl") if path.is_file()}


def find_rollout(sessions_root, thread_id, preexisting):
    hits = [path for path in rollout_files(sessions_root)
            if path.name.endswith("-" + thread_id + ".jsonl") and path not in preexisting]
    if len(hits) != 1:
        raise ImageError("ROLLOUT_NOT_FOUND" if not hits else "ROLLOUT_AMBIGUOUS",
                         detail=str(sessions_root))
    return hits[0]


def extract_images(rollout):
    """Completed image_gen results, oldest first, one entry per image.

    codex 0.163 writes an `image_gen.generation` Extension item; older builds wrote
    `image_generation_call` or `image_generation_end` records with the same result.
    """
    images, seen, failures = [], set(), []
    with open(rollout, encoding="utf-8") as stream:
        for line in stream:
            if "image_gen" not in line and "image_generation" not in line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            payload = record.get("payload") if isinstance(record, dict) else None
            if not isinstance(payload, dict):
                continue
            item = payload.get("item")
            if isinstance(item, dict) and item.get("kind") == "image_gen.generation":
                source = item
            elif payload.get("type") in ("image_generation_call", "image_generation_end"):
                source = payload
            else:
                continue
            status, result = source.get("status"), source.get("result")
            if status not in (None, "completed", "generating"):
                failures.append(str(status))
                continue
            if not isinstance(result, str) or not result or result in seen:
                continue
            seen.add(result)
            prompt = source.get("revisedPrompt") or source.get("revised_prompt")
            images.append({"b64": result, "revised_prompt": prompt if isinstance(prompt, str) else None})
    return images, failures


def decode_png(b64):
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise ImageError("IMAGE_DECODE_FAILED") from None
    if not raw.startswith(PNG_SIGNATURE):
        raise ImageError("IMAGE_NOT_PNG")
    return raw


def gate(observation, now):
    """D-74 / D-121 check. Returns (reasons, tool); an empty list means open."""
    tool = runtime_collect.codex_image_tool(observation)
    if tool is None:
        return ["IMAGE_CODEX_SUBSCRIPTION_UNVERIFIED"], None
    return orchestrate.assess_image_tool(tool, {}, {}, now), tool


def collect_observation():
    now = utc_now()
    raw, profile = runtime_collect.LocalBackend().collect("codex")
    return runtime_collect.normalize("codex", raw, now, profile)


def run_codex(argv, prompt, workdir, env, timeout=TIMEOUT_SECONDS):
    """Send once inside a job object that also ends Codex's child processes."""
    data = prompt.encode("utf-8")
    with runtime_collect.Probe(argv, timeout=timeout, cwd=str(workdir), env=env) as probe:
        errors = []

        def write_input():
            try:
                probe.process.stdin.write(data)
                probe.process.stdin.flush()
            except (OSError, ValueError) as exc:
                errors.append(type(exc).__name__)
            finally:
                try:
                    probe.process.stdin.close()
                except OSError:
                    pass

        writer = threading.Thread(target=write_input, daemon=True)
        probe.writers.append(writer)
        writer.start()
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
        if errors:
            raise ImageError("CODEX_STDIN_FAILED")
    return rc, bytes(raw).decode("utf-8", errors="replace")


def check_output(out):
    path = Path(out)
    if (not path.is_absolute() or path.suffix.lower() != ".png" or not path.parent.is_dir()
            or path.exists() or receipt_path(path).exists()):
        raise ImageError("OUTPUT_PATH_INVALID", exit_code=2,
                         detail="absolute .png path in an existing folder, not already present")
    return path


def receipt_path(out):
    return out.with_name(out.stem + ".receipt.json")


def write_new(path, data):
    with open(path, "xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def generate(brief, out, transparent=False, *, collect=collect_observation, run=run_codex,
             command=None, home=None, now=None):
    """Return (exit_code, receipt). The receipt is also written beside the image."""
    started = now or utc_now()
    receipt = {"schema": "vibe-codex-image-v1", "decision": "D-121", "status": "failed",
               "started_at": started, "driver": {"model": DRIVER_MODEL, "effort": DRIVER_EFFORT},
               "images": []}
    if not isinstance(brief, str) or not brief.strip():
        raise ImageError("PROMPT_REQUIRED", exit_code=2)
    if len(brief.encode("utf-8")) > MAX_PROMPT_BYTES:
        raise ImageError("PROMPT_TOO_LARGE", exit_code=2)
    if scan_secrets(brief):
        raise ImageError("SENSITIVE_PAYLOAD", exit_code=2)
    out = check_output(out)
    prompt = build_prompt(brief, transparent)
    receipt["prompt_sha256"] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    observation = collect()
    # Judge after collecting: an observation newer than the clock is not fresh.
    reasons, tool = gate(observation, now or utc_now())
    if tool is not None:
        receipt["usage_before"] = {key: tool["quota"][key]
                                   for key in ("used_pct", "bucket", "observed_at")}
    if reasons:
        receipt.update(status="refused", reasons=reasons)
        return 3, receipt
    home = Path(home) if home else codex_home()
    sessions = home / "sessions"
    preexisting = rollout_files(sessions)
    workdir = Path(tempfile.mkdtemp(prefix="vibe-codex-image-"))
    try:
        command = command or runtime_collect.resolve_command("codex")
        env = runtime_collect.child_env(os.environ, "codex")
        try:
            rc, stdout = run(build_argv(command, workdir), prompt, workdir, env)
        except (runtime_collect.CollectorError, OSError) as exc:
            # The request may have reached Codex; report it and do not resend.
            receipt.update(status="unknown", reasons=["CODEX_SEND_OUTCOME_UNKNOWN:" + str(exc)])
            return 4, receipt
        stream = parse_stream(stdout)
        receipt["codex"] = {"exit_code": rc, "thread_id": stream["thread_id"],
                            "usage": stream["usage"]}
        limit = usage_limit_message(stream["errors"])
        if limit:
            receipt.update(status="usage_limit", reasons=["CODEX_USAGE_LIMIT"], message=limit)
            return 3, receipt
        if rc != 0 or not stream["thread_id"]:
            receipt.update(reasons=["CODEX_EXEC_FAILED"], errors=stream["errors"][-3:])
            return 4, receipt
        try:
            rollout = find_rollout(sessions, stream["thread_id"], preexisting)
            receipt["codex"]["rollout"] = str(rollout)
            images, failures = extract_images(rollout)
            if not images:
                raise ImageError("IMAGE_GEN_NOT_RUN", detail={"failures": failures,
                                                              "errors": stream["errors"][-3:]})
            for index, image in enumerate(images, start=1):
                raw = decode_png(image["b64"])
                target = out if index == 1 else out.with_name(out.stem + "-" + str(index) + ".png")
                try:
                    write_new(target, raw)
                except OSError as exc:
                    if index == 1:
                        raise ImageError("OUTPUT_WRITE_FAILED", detail=str(exc)) from None
                    receipt.setdefault("skipped", []).append(str(target))
                    continue
                receipt["images"].append({"path": str(target), "bytes": len(raw),
                                          "sha256": hashlib.sha256(raw).hexdigest(),
                                          "revised_prompt": image["revised_prompt"]})
        except ImageError as exc:
            receipt.update(reasons=[exc.code], detail=exc.detail)
            return exc.exit_code, receipt
        receipt["status"] = "succeeded"
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
    source.add_argument("--prompt", help="Image brief text")
    source.add_argument("--prompt-file", help="UTF-8 file holding the image brief")
    parser.add_argument("--out", required=True, help="Absolute path of the new .png")
    parser.add_argument("--transparent", action="store_true",
                        help="Ask for a real alpha background")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        brief = (args.prompt if args.prompt is not None
                 else Path(args.prompt_file).read_text(encoding="utf-8"))
        code, receipt = generate(brief, args.out, args.transparent)
    except ImageError as exc:
        code, receipt = exc.exit_code, {"status": "failed", "reasons": [exc.code],
                                        "detail": exc.detail}
    except (OSError, UnicodeError, runtime_collect.CollectorError) as exc:
        code, receipt = 4, {"status": "failed", "reasons": [type(exc).__name__ + ":" + str(exc)]}
    receipt.pop("b64", None)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
