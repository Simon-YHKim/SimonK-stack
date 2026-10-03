#!/usr/bin/env python3
"""Four-vendor PROTOCOL 35 debate runner: seats, prompts, guarded calls, records.

Readiness never calls a model. A vendor whose subscription window is spent is
marked ABSENT and its CLI is never spawned, so purchased credits or on-demand
balances are not touched. Headless Claude draws a credit that cannot be read
locally, so it is UNKNOWN and runs only with --accept-unknown. Prompts are
text-only and capped at 24000 characters.

Any of the four CLIs can host: the host names its own vendor with
--orchestrator, answers its own seat in-session and registers it with submit.
Another vendor's live interactive session can answer that vendor's seat with
submit --host-session <id>, proven by its local transcript.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid

VENDORS = ("anthropic", "openai", "xai", "google")
DISPLAY = {"anthropic": "Claude", "openai": "Codex", "xai": "Grok", "google": "Gemini"}
AUTHOR = {"anthropic": "claude", "openai": "codex", "xai": "grok", "google": "gemini"}
LENSES = ("proponent", "skeptic", "alternative", "user-interest")
LENS_KO = {"proponent": "옹호자", "skeptic": "회의론자", "alternative": "대안 제시자",
           "user-interest": "사용자 이익 대변자"}
LENS_SHORT = {"proponent": "찬성", "skeptic": "회의", "alternative": "대안", "user-interest": "사용자 이익"}
ROUNDS = ("r1", "r2", "judge", "ratify", "catchup")
MODES = ("quick", "full", "interject")
CALLS = ("CONTINUE", "RESCOPE", "SHIP_NOW", "STOP", "ASK_USER")
DEFAULTS = {"anthropic": ("claude-opus-5-5", "max"), "openai": ("gpt-6.1-sol", "xhigh"),
            "xai": ("grok-4.7", "xhigh"), "google": ("gemini-3.1-pro-high", None)}
BINARIES = {"anthropic": "claude", "openai": "codex", "xai": "grok", "google": "agy",
            "orca": "orca"}
ARGV_SEATS = ("google", "orca")  # model-written text travels in argv for these
KST = timezone(timedelta(hours=9))
PROMPT_CAP = 24000
MIN_PROMPT_CAP = 4000
CMDLINE_CAP = 32000  # UTF-16 units; CreateProcess allows 32767
EVIDENCE_CAP = 16384
RECORD_EVIDENCE_CAP = 6000
QUESTION_CAP, ITEM_CAP, ITEM_COUNT = 2000, 300, 10
BRIDGE_FRESH = timedelta(hours=6)
CODEX_TAIL = 4 * 1024 * 1024
CODEX_FRESH = timedelta(minutes=10)  # a rollout rate-limit snapshot older than this no longer proves headroom
GROK_TAIL = 4 * 1024 * 1024
GROK_FRESH = timedelta(minutes=10)  # a logged billing line older than this no longer proves headroom
RPC_PROBE_SECONDS = 25  # live quota probes (Codex app-server, Grok ACP): the whole exchange
RPC_PROBE_LINE = 1024 * 1024
FOOTER = "도구를 쓰지 말고 파일을 수정하지 말 것. 자기 벤더·모델 정체를 밝히지 말 것. 텍스트로만 답할 것."
QUOTA_RE = re.compile(r"(?:status|HTTP)\s*(?:402|429)|402 Payment Required|\b429\b|rate[ _-]?limit"
                      r"|usage balance exhausted|usage limit|add credits|RESOURCE_EXHAUSTED|quota", re.I)
TIMEOUT_WARN_RE = re.compile(r"print[- ]?timeout|timed out|time limit|deadline exceeded"
                             r"|timeout (?:reached|expired|exceeded)", re.I)
# API keys, gateways and cloud switches would move a CLI off the subscription lane.
SCRUB_EXACT = frozenset({"GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT", "GOOGLE_API_KEY",
                         "GEMINI_API_KEY"})
SCRUB_PREFIX = ("CLAUDE_CODE_USE_", "ANTHROPIC_", "OPENAI_", "XAI_", "GROK_CODE_", "GATEWAY_",
                "GOOGLE_GENAI_USE_", "AWS_", "AZURE_OPENAI_")
SCRUB_SUFFIX = ("_API_KEY", "_AUTH_TOKEN", "_ACCESS_TOKEN", "_BASE_URL")
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
RESERVED_NAMES = frozenset(["CON", "PRN", "AUX", "NUL"] + ["COM%d" % i for i in range(1, 10)]
                           + ["LPT%d" % i for i in range(1, 10)])
CTRL_RE = re.compile("[\x00-\x1f\x7f-\x9f​-‏‪-‮⁦-⁩]")
D_HEADER_RE = re.compile(r"\| DECIDE \| \*\*D-(\d+)\b|^###\s+D-(\d+)\b", re.M)
CALL_RE = re.compile(r"(?<![A-Z_])(%s)(?![A-Z_])" % "|".join(CALLS))
SECRET_RES = tuple(re.compile(p) for p in (
    r"sk-ant-[\w-]{20,}", r"sk-[\w-]{20,}", r"gh[pousr]_\w{30,}", r"xai-[\w-]{20,}",
    r"AIza[\w-]{30,}", r"Bearer\s+\S{20,}"))
SECRET_ASSIGN_RE = re.compile(r"(?i)(api[_-]?key|token|secret|password)(\s*[=:]\s*)(?!\[REDACTED\])\S+")
PROMPT_KEYS = ("truncated", "prompt", "anon", "inputs", "positions_count", "judge_wrote_position",
               "cmdline_chars")
SCRIPT = Path(__file__).resolve()
HOST_TABLE = "Claude Code → anthropic · Codex → openai · Grok CLI → xai · agy (Antigravity) → google"
HOST_SESSION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{7,127}")
UUID_RE = re.compile(r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}")
HOST_LIVE = timedelta(minutes=30)
HOST_SKEW = timedelta(minutes=5)
HOST_SCAN_BYTES = 4 * 1024 * 1024  # Claude entrypoint / Codex session_meta are read line by line up to here
HOST_SCAN_LINES = 2000
HOST_BIND_TAIL = 16 * 1024 * 1024  # tail of the session's own transcript searched for the binding
HOST_BIND_EXTRA = 2 * 1024 * 1024  # per side file (Claude subagent transcripts, tool-results)
HOST_BIND_FILES = 64
HOST_BIND_BUDGET = 48 * 1024 * 1024
BIND_PREFIX, BIND_MIN = 200, 40
# Interactive values confirmed on this machine's real transcripts (2026-10-02, bounded reads).
CLAUDE_INTERACTIVE = ("cli", "claude-desktop")
CODEX_INTERACTIVE = ("cli", "vscode")
HOST_LAYOUT = {"anthropic": "<projects>/*/<id>.jsonl", "openai": "<sessions>/**/rollout-*-<id>.jsonl",
               "xai": "<sessions>/*/<id>/updates.jsonl",
               "google": "<brain>/<id>/.system_generated/logs/transcript.jsonl"}
# Variables a host CLI exports to the shells it spawns. Claude Code: seen in this environment.
# Codex: CODEX_THREAD_ID / CODEX_SANDBOX per a local note of a live `codex exec` env capture (0.147.0)
# and present in codex.exe 0.155.0. Grok and agy exports are unconfirmed, so their names are recorded only.
HOST_MARKERS = {"anthropic": ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT"), "openai": ("CODEX_THREAD_ID", "CODEX_SANDBOX")}
MARKER_PREFIXES = ("GROK_", "ANTIGRAVITY_", "AGY_")
MARKER_SKIP = frozenset({"GROK_HOME"})
QUOTA_GATED = ("openai", "xai")  # their spent windows bill purchased credit, even in an interactive session
UNDECLARED = "미신고"
AGY_EFFORTS = ("minimal", "low", "medium", "high", "xhigh", "max")

LENS_TEXT = {
    "proponent": "옹호자. 선택지 중 가장 유력한 하나를 골라 그것이 이기는 가장 강한 논거를 세운다. "
                 "동시에 그 선택지를 무너뜨릴 수 있는 가장 강한 반론 하나를 스스로 밝힌다.",
    "skeptic": "회의론자. 가장 유력해 보이는 선택지를 반박하는 데서 출발한다. 기본값은 의심이다. "
               "현상 유지나 다른 선택지가 왜 더 안전한지, 무엇이 검증되지 않았는지 따진다.",
    "alternative": "대안 제시자. 제시된 선택지 밖에서 아무도 제안하지 않은 경로를 하나 찾고 그것이 "
                   "기존 선택지를 이기는지 논증한다. 정말 없으면 기존 선택지의 더 나은 변형을 제안한다.",
    "user-interest": "사용자 이익 대변자. 구현 편의나 제안자의 체면은 무시하고 최종 사용자와 "
                     "의사결정자의 시간·돈·위험·되돌릴 수 있는지만으로 판단한다.",
}
INTERJECT_LENS_TEXT = {
    "proponent": "현 경로 변호인. 작업 중인 에이전트가 지금 경로를 계속해야 하는 가장 강한 이유를 "
                 "찾는다. 그래도 끊어야 할 신호가 있으면 숨기지 않는다.",
    "skeptic": "중단 검토자. 긴 턴·반복 보류·사용자 불만·쿼터 신호를 근거로 지금 멈추거나 줄여야 "
               "하는지 엄격하게 따진다.",
    "alternative": "경로 전환자. 지금 경로보다 짧은 길(범위 축소, 다른 순서, 다른 도구, 부분 납품)을 찾는다.",
    "user-interest": "사용자 대변인. 기다리고 있는 사용자의 시간과 신뢰 관점에서 지금 당장 무엇이 "
                     "필요한지 판단한다.",
}
R1_INSTR = """## 지시
위 렌즈로 이 안건에 대한 독립 입장을 쓴다. 다음 섹션을 이 순서대로 쓴다.

## 입장
한 줄: 고른 선택지 + 확신도 0-100 (예: "선택지 2 — 확신도 70")
## 핵심 근거
글머리표 최대 5개. 가능하면 근거 자료를 인용한다.
## 내 입장의 가장 강한 반론
## 조건·전제
이 입장이 성립하려면 참이어야 하는 것.
## 기준별 평가
판단 기준 × 선택지 표. 각 칸은 1-5점.

"""
INTERJECT_R1_INSTR = """## 지시
위 스냅숏은 지금 오래 작업 중인 다른 에이전트의 상태다. 그 에이전트에게 지금 무엇을 하라고 할지 판단한다.
첫 줄은 다음 다섯 가지 중 하나로만 쓴다.
CALL: CONTINUE | CALL: RESCOPE | CALL: SHIP_NOW | CALL: STOP | CALL: ASK_USER
(CONTINUE=그대로 계속, RESCOPE=범위를 줄여 계속, SHIP_NOW=지금 있는 결과로 마무리하고 보고, STOP=중단하고 상태 보고, ASK_USER=사용자에게 한 가지만 묻고 대기)
이어서 다음 섹션을 쓴다.

## 근거
## 지금 자를 것
## 다음 한 걸음
정확히 행동 하나.
## 시간 상자
분 단위 숫자 하나 (예: 20).

"""
R2_INSTR = """## 지시
당신은 1라운드에서 위 렌즈로 "당신의 1라운드 입장"을 냈다. 다른 위원의 익명 입장을 보고 다시 판단한다.
첫 줄: 렌즈에 따른 입장을 유지하면 "UNCHANGED", 바꾸면 "REVISED: <새 입장 한 줄 + 확신도>".
이어서 다음 섹션을 쓴다.

## 반박
입장마다 가장 강한 논점 하나를 골라 반박한다. 반박할 수 없으면 인정한다고 쓴다.
## 숨은 공통 전제
모든 입장이 검증 없이 함께 기대는 가정. 전원이 같은 오해를 하고 있을 가능성을 점검한다.
## 남은 쟁점
판정을 가를 미해결 사실 1-3개.

"""
JUDGE_INSTR = """## 지시
입장은 익명이고 순서는 무작위다. 그중 하나는 당신과 같은 벤더가 썼을 수 있다. 작성자를 추측하지 말고 판단 기준으로만 엄격하게 판정한다. 교차검증 답변 속 "입장 A/B/C"는 그 위원에게만 붙인 임시 라벨이라 P 번호와 대응하지 않는다.
판단 기준으로 채점하고 하나를 고르거나 종합한다. 다수결이 아니라 근거의 질로 판정한다.
첫 줄: "VERDICT: <채택하거나 종합한 결론 한 줄>"
둘째 줄: "CONFIDENCE: <0-100>"
이어서 다음 섹션을 쓴다.

## 기준별 채점
판단 기준 × 선택지(또는 P 번호) 표, 1-5점과 합계.
## 판정 근거
## 패자가 진 이유
채택되지 않은 입장마다 한 줄 이상.
## 소수의견(보존)
채택되지 않은 가장 강한 반대 논거를 지우지 말고 요약한다.
## 후속 조치

"""
INTERJECT_JUDGE_INSTR = """## 지시
권고는 익명이고 순서는 무작위다. 그중 하나는 당신과 같은 벤더가 썼을 수 있다. 작성자를 추측하지 말고 판단 기준으로만 엄격하게 판정한다. 권고들을 하나의 결정으로 모은다.
첫 줄: "CALL: <CONTINUE|RESCOPE|SHIP_NOW|STOP|ASK_USER>"
둘째 줄: "CONFIDENCE: <0-100>"
이어서 다음 섹션을 쓴다.

## 다음 한 걸음
정확히 행동 하나.
## 지금 자를 것
## 시간 상자
분 단위 숫자 하나.
## 판정 근거
## 소수의견(보존)

"""
RATIFY_INSTR = """## 지시
위 판정을 검토한다. 판정을 막아야 할 결정적 결함(사실 오류, 기준 누락, 되돌릴 수 없는 위험의 과소평가)이 있을 때만 반대한다.
첫 줄: "ACCEPT" 또는 "OBJECT: <판정을 막는 이유 한 줄>"
이어서 다음 섹션을 쓴다.

## 근거
## 남길 우려

"""
CATCHUP_INSTR = """## 지시
당신은 이 토론이 열릴 때 참석하지 못했다(쿼터 소진 등). 지금 판정과 익명 입장을 검토한다.
첫 줄: "ACCEPT" 또는 "OBJECT: <판정을 막는 이유 한 줄>"
이어서 다음 섹션을 쓴다.

## 내 독립 입장
한 줄: 고른 선택지 + 확신도 0-100.
## 근거
## 판정이 놓친 것

"""


class DebateError(Exception):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------- time, paths, io

def parse_iso(value):
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    moment = datetime.fromisoformat(text)
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def now():
    raw = os.environ.get("AI_DEBATE_NOW") if os.environ.get("AI_DEBATE_TEST") == "1" else None
    return parse_iso(raw) if raw else datetime.now(timezone.utc)


def from_epoch(value):
    try:
        return datetime.fromtimestamp(float(value), timezone.utc) if value else None
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def kst(moment):
    return moment.astimezone(KST).strftime("%Y-%m-%d %H:%M KST")


def stamp(moment):
    return moment.astimezone(KST).isoformat(timespec="seconds")


def max_used():
    try:
        value = float(os.environ.get("AI_DEBATE_MAX_USED", "95"))
    except ValueError:
        return 95.0
    if not math.isfinite(value) or value <= 0:
        return 95.0
    return min(value, 100.0)


def state_root():
    if os.environ.get("AI_DEBATE_HOME"):
        return Path(os.environ["AI_DEBATE_HOME"])
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "SimonKStack" / "ai-debate"
    if os.environ.get("XDG_STATE_HOME"):
        return Path(os.environ["XDG_STATE_HOME"]) / "SimonKStack" / "ai-debate"
    return Path.home() / ".local" / "state" / "SimonKStack" / "ai-debate"


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes((json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    os.replace(tmp, path)


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def read_text(path):
    return Path(path).read_bytes().decode("utf-8", errors="replace").lstrip("﻿")


def read_input(path, what):
    """Operator-supplied text: UTF-8 only, no NUL, missing files are usage errors."""
    path = Path(path)
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        raise DebateError("%s not found: %s" % (what, path.as_posix())) from None
    except OSError as exc:
        raise DebateError("cannot read %s %s: %s" % (what, path.as_posix(), exc.strerror or exc)) from None
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        raise DebateError("%s is UTF-16 (the PowerShell 5.1 '>' default); save it as UTF-8, e.g. "
                          "Set-Content -Encoding utf8: %s" % (what, path.as_posix()))
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DebateError("%s is not valid UTF-8 (byte %d): %s" % (what, exc.start, path.as_posix())) from None
    if "\x00" in text:
        raise DebateError("%s contains NUL characters (UTF-16 without a BOM?); save it as UTF-8: %s"
                          % (what, path.as_posix()))
    return text


def tail_lines(path, limit):
    """Last complete lines within `limit` bytes; never loads a whole large log."""
    with open(path, "rb") as stream:
        stream.seek(0, 2)
        size = stream.tell()
        start = max(0, size - limit)
        stream.seek(start)
        data = stream.read(limit)
    lines = data.split(b"\n")
    if start > 0:
        lines = lines[1:]
    return [line for line in lines if line.strip()]


def emit(obj, as_json=True):
    print(json.dumps(obj, ensure_ascii=False, indent=2) if as_json else obj)


# ---------------------------------------------------------------- binaries

def known_paths(key):
    home = Path.home()
    local = Path(os.environ.get("LOCALAPPDATA") or home / "AppData" / "Local")
    if os.name != "nt":
        return {"anthropic": [home / ".local" / "bin" / "claude"],
                "xai": [home / ".grok" / "bin" / "grok"]}.get(key, [])
    if key == "openai":
        pattern = "Programs/Codex-*/node_modules/@openai/codex/node_modules/@openai/codex-win32-*/vendor/*/bin/codex.exe"
        return sorted(local.glob(pattern))[::-1]
    return {"anthropic": [home / ".local" / "bin" / "claude.exe"],
            "xai": [home / ".grok" / "bin" / "grok.exe"],
            "google": [local / "agy" / "bin" / "agy.exe"],
            "orca": [local / "Programs" / "orca" / "resources" / "bin" / "orca.exe"]}.get(key, [])


def codex_native(shim, depth=0):
    """Follow npm .cmd shims to the vendored codex.exe (cmd quoting mangles -c values)."""
    if depth > 3:
        return None
    for candidate in (shim, shim.with_suffix(".cmd")):
        try:
            text = candidate.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for ref in re.findall(r'"([^"]+?(?:\.cmd|codex\.js))"', text, re.I):
            ref = re.sub(r"%~?dp0%?\\?", lambda _m: str(candidate.parent) + "\\", ref)
            target = Path(ref)
            if target.name.lower() == "codex.js" and target.is_file():
                root = target.parent.parent
                for base in (root / "node_modules" / "@openai", root.parent):
                    found = sorted(base.glob("codex-win32-*/vendor/*/bin/codex.exe"))
                    if found:
                        return found[-1]
            elif target.suffix.lower() == ".cmd" and target.is_file() and target != candidate:
                native = codex_native(target, depth + 1)
                if native:
                    return native
    return None


def is_shim(cmd):
    return bool(cmd) and Path(cmd[0]).suffix.lower() in (".cmd", ".bat")


def shim_native(shim, depth=0):
    """The native .exe a .cmd/.bat shim launches, so argv text never passes through cmd.exe."""
    shim = Path(shim)
    if depth > 3:
        return None
    try:
        text = shim.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    base = str(shim.parent) + os.sep
    for ref in re.findall(r'"([^"\r\n]+?\.(?:exe|cmd|bat))"', text, re.I):
        ref = re.sub(r"%~?dp0%?\\?", lambda _m: base, ref, flags=re.I)
        target = Path(ref.replace("\\", os.sep) if os.sep != "\\" else ref)
        if not target.is_file() or target.resolve() == shim.resolve():
            continue
        if target.suffix.lower() == ".exe":
            return target
        native = shim_native(target, depth + 1)
        if native:
            return native
    return None


def unshim(key, argv):
    if key in ARGV_SEATS and is_shim(argv):
        native = shim_native(argv[0])
        if native:
            return [str(native)] + argv[1:]
    return argv


def resolve_cmd(key):
    raw = os.environ.get("AI_DEBATE_CMD_" + key.upper())
    if raw is not None:
        try:
            argv = json.loads(raw)
        except ValueError:
            raise DebateError("AI_DEBATE_CMD_%s must be a JSON argv list" % key.upper()) from None
        if not isinstance(argv, list) or not all(isinstance(x, str) for x in argv):
            raise DebateError("AI_DEBATE_CMD_%s must be a JSON argv list" % key.upper())
        return unshim(key, argv) or None
    found = shutil.which(BINARIES[key])
    if found and os.name == "nt":
        suffix = Path(found).suffix.lower()
        if key == "openai" and suffix != ".exe":
            native = codex_native(Path(found))
            if native:
                return [str(native)]
        if suffix in (".exe", ".cmd", ".bat"):
            return unshim(key, [found])
        found = None
    elif found:
        return [found]
    for candidate in known_paths(key):
        if candidate.is_file():
            return [str(candidate)]
    return None


def scrubbed(name):
    upper = name.upper()
    return upper in SCRUB_EXACT or upper.startswith(SCRUB_PREFIX) or upper.endswith(SCRUB_SUFFIX)


def child_env(vendor):
    env = {k: v for k, v in os.environ.items() if not scrubbed(k)}
    env["NO_COLOR"] = "1"
    if vendor == "google":
        env["AGY_CLI_DISABLE_AUTO_UPDATE"] = "1"
    return env


def kill_tree(proc):
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    try:
        proc.kill()
    except OSError:
        pass


_KERNEL32 = None


def kernel32():
    global _KERNEL32
    if _KERNEL32 is None:
        import ctypes
        from ctypes import wintypes
        lib = ctypes.WinDLL("kernel32", use_last_error=True)
        lib.CreateJobObjectW.restype = wintypes.HANDLE
        lib.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
        lib.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
        lib.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
        lib.CloseHandle.argtypes = (wintypes.HANDLE,)
        lib.OpenProcess.restype = wintypes.HANDLE
        lib.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        lib.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        lib.GetProcessTimes.argtypes = (wintypes.HANDLE,) + (ctypes.POINTER(wintypes.FILETIME),) * 4
        _KERNEL32 = lib
    return _KERNEL32


def new_job():
    """Windows: a job with KILL_ON_JOB_CLOSE, so the child tree dies with this runner."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class Basic(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class Extended(ctypes.Structure):
            _fields_ = [("Basic", Basic), ("Io", ctypes.c_ulonglong * 6), ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        lib = kernel32()
        job = lib.CreateJobObjectW(None, None)
        if not job:
            return None
        info = Extended()
        info.Basic.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if lib.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
            return job
        lib.CloseHandle(job)
    except (OSError, AttributeError, TypeError, ValueError):
        pass
    return None


def join_job(job, proc):
    try:
        return bool(job) and bool(kernel32().AssignProcessToJobObject(job, int(proc._handle)))
    except (OSError, AttributeError, TypeError, ValueError):
        return False


def parent_death_signal():
    """Linux: SIGKILL the direct child if this runner dies (no job objects on POSIX)."""
    if not sys.platform.startswith("linux"):
        return None
    try:
        import ctypes
        prctl = ctypes.CDLL(None, use_errno=True).prctl
    except (OSError, AttributeError):
        return None
    return lambda: prctl(1, int(signal.SIGKILL))


def pid_alive(pid, started=None):
    """True while `pid` runs; on Windows a process created after `started` is a reused pid."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True
    import ctypes
    from ctypes import wintypes
    lib = kernel32()
    handle = lib.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return ctypes.get_last_error() == 5
    try:
        code = wintypes.DWORD()
        if not lib.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value != 259:
            return False
        if isinstance(started, (int, float)):
            times = [wintypes.FILETIME() for _ in range(4)]
            if lib.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
                ticks = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
                if ticks / 1e7 - 11644473600 > started + 2:
                    return False
        return True
    finally:
        lib.CloseHandle(handle)


def run_process(argv, cwd, env, timeout, out_path, err_path, stdin_path=None, on_spawn=None):
    """Run with files for stdio (no pipe deadlocks); kill the whole tree on timeout."""
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP
                                   | getattr(subprocess, "CREATE_NO_WINDOW", 0))
    else:
        kwargs["start_new_session"] = True
        death = parent_death_signal()
        if death:
            kwargs["preexec_fn"] = death
    started = time.monotonic()
    timed_out = False
    job = new_job()
    with open(out_path, "wb") as out, open(err_path, "wb") as err, \
            open(stdin_path if stdin_path else os.devnull, "rb") as fin:
        try:
            proc = subprocess.Popen(argv, stdin=fin, stdout=out, stderr=err, cwd=str(cwd),
                                    env=env, shell=False, **kwargs)
            in_job = join_job(job, proc)
            if on_spawn:
                on_spawn(proc.pid, in_job)
            try:
                rc = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                kill_tree(proc)
                try:
                    rc = proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    rc = None
        finally:
            if job:
                kernel32().CloseHandle(job)
    return rc, timed_out, round(time.monotonic() - started, 3)


# ---------------------------------------------------------------- seats (no model calls)

def seat_row(vendor, status, reason, short="", reset=None, evidence=None, cli=None, **extra):
    row = {"vendor": vendor, "display": DISPLAY[vendor], "status": status, "reason": reason,
           "short": short, "reset_kst": kst(reset) if reset else None,
           "evidence": evidence or {}, "cli": cli}
    row.update(extra)
    return row


def latest_codex_limits(root):
    files = []
    for dirpath, _dirs, names in os.walk(root):
        for name in names:
            if name.startswith("rollout-") and name.endswith(".jsonl"):
                path = Path(dirpath) / name
                try:
                    files.append((path.stat().st_mtime, path))
                except OSError:
                    continue
    best = None
    for _mtime, path in sorted(files, reverse=True)[:3]:
        try:
            lines = tail_lines(path, CODEX_TAIL)
        except OSError:
            continue
        for line in reversed(lines):
            if b'"token_count"' not in line:
                continue
            try:
                record = json.loads(line)
                payload = record.get("payload") or {}
                limits = payload.get("rate_limits")
                if payload.get("type") != "token_count" or not isinstance(limits, dict):
                    continue
                when = parse_iso(record["timestamp"])
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
            if best is None or when > best[0]:
                best = (when, limits, path)
            break
    return best


def rpc_probe(argv, vendor, label, talk):
    """Run `argv` in a throwaway folder speaking JSON-RPC lines on stdio and return talk(request, notify).
    Only what `talk` sends is sent: server notifications and requests are ignored, never answered or
    executed. ValueError on any failure or after RPC_PROBE_SECONDS. The whole tree is killed afterwards
    (an agent may start MCP servers)."""
    base = state_root() / "probe"
    base.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="%s-rpc-" % vendor, dir=str(base)))
    if os.name == "nt":
        kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    else:
        kwargs = {"start_new_session": True}
    job, proc, lines = new_job(), None, queue.Queue()
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                cwd=str(work), env=child_env(vendor), shell=False, **kwargs)
        join_job(job, proc)

        def pump():
            try:
                for raw in iter(lambda: proc.stdout.readline(RPC_PROBE_LINE), b""):
                    lines.put(raw)
            except (OSError, ValueError):
                pass
            lines.put(b"")

        threading.Thread(target=pump, daemon=True).start()
        deadline = time.monotonic() + RPC_PROBE_SECONDS

        def send(message):
            try:
                proc.stdin.write((json.dumps(message) + "\n").encode("utf-8"))
                proc.stdin.flush()
            except (OSError, ValueError):
                raise ValueError("%s closed its input before %s" % (label, message["method"])) from None

        def notify(method, params):
            send({"jsonrpc": "2.0", "method": method, "params": params})

        def request(rid, method, params):
            send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
            while True:
                left = deadline - time.monotonic()
                try:
                    raw = lines.get(timeout=left) if left > 0 else None
                except queue.Empty:
                    raw = None
                if raw is None:
                    raise ValueError("timed out waiting for %s" % method)
                if not raw:
                    raise ValueError("%s exited before answering %s" % (label, method))
                try:
                    msg = json.loads(raw)
                except ValueError:
                    continue
                if not isinstance(msg, dict) or "method" in msg or msg.get("id") != rid:
                    continue  # notifications and server requests are ignored, never executed
                if "error" in msg:
                    error = msg["error"] if isinstance(msg["error"], dict) else {}
                    raise ValueError("%s failed (code %s)" % (method, error.get("code")))
                return msg.get("result")

        return talk(request, notify)
    except OSError as exc:
        raise ValueError("could not start %s (%s)" % (label, type(exc).__name__)) from None
    finally:
        if proc is not None:
            kill_tree(proc)
            for stream in (proc.stdin, proc.stdout):
                try:
                    stream.close()
                except (OSError, ValueError):
                    pass
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
        if job:
            kernel32().CloseHandle(job)
        shutil.rmtree(work, ignore_errors=True)


def codex_live_limits(cmd):
    """Codex rate limits over the app-server protocol with no model turn: `codex app-server --stdio`,
    `initialize`, the `initialized` notification, then `account/rateLimits/read`. No thread, turn or
    prompt method is ever sent. Returns {"limits": result, "codex_home": initialize's codexHome}; the
    result carries `rateLimits` (primary/secondary `usedPercent`, `windowDurationMins`, `resetsAt`,
    `credits.hasCredits`, `planType`, `rateLimitReachedType`), `rateLimitsByLimitId` and
    `ordinaryUsageAllowed`. ValueError on any failure."""
    def talk(request, notify):
        init = request(1, "initialize", {"clientInfo": {"name": "ai-debate-seats", "version": "1"},
                                         "capabilities": {"experimentalApi": False}})
        if not isinstance(init, dict):
            raise ValueError("initialize returned no object")
        notify("initialized", {})
        result = request(2, "account/rateLimits/read", {})
        if not isinstance(result, dict) or not isinstance(result.get("rateLimits"), dict):
            raise ValueError("rate-limit reply has no rateLimits object")
        home = init.get("codexHome")
        return {"limits": result, "codex_home": home if isinstance(home, str) else None}

    return rpc_probe(cmd + ["app-server", "--stdio"], "openai", "codex app-server", talk)


def codex_live_snapshot(bucket):
    """The live `rateLimits` bucket in the rollout `token_count.rate_limits` shape."""
    credits = bucket.get("credits") if isinstance(bucket.get("credits"), dict) else {}
    snap = {"plan_type": bucket.get("planType"), "credits": {"has_credits": credits.get("hasCredits")}}
    for name in ("primary", "secondary"):
        window = bucket.get(name)
        if isinstance(window, dict):
            snap[name] = {"used_percent": window.get("usedPercent"), "resets_at": window.get("resetsAt"),
                          "window_minutes": window.get("windowDurationMins")}
    return snap


def seat_openai(cmd, probe=True):
    """Live app-server rate limits first. The rollout snapshot is only a fallback, and a stale one never
    proves headroom: rollouts record `token_count` only for this machine's own Codex turns, so usage from
    other machines or clients is invisible to them, and a spent window with credits bills purchased credit."""
    if not cmd:
        return seat_row("openai", "ABSENT", "codex CLI not found", "CLI 없음")
    current, threshold = now(), max_used()
    live_error = None if probe else "skipped (--no-probe)"
    flags = {}
    if probe:
        try:
            live = codex_live_limits(cmd)
            bucket = live["limits"]["rateLimits"]
            limits, observed = codex_live_snapshot(bucket), current
            source = "codex app-server account/rateLimits/read (live, no model turn)"
            reached = bucket.get("rateLimitReachedType")
            flags = {"codex_home": live["codex_home"],
                     "ordinary_usage_allowed": live["limits"].get("ordinaryUsageAllowed"),
                     "rate_limit_reached_type": str(reached)[:40] if reached else None}
        except ValueError as exc:
            live_error = "failed: %s" % str(exc)[:160]
    if live_error:
        home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
        root = Path(os.environ.get("AI_DEBATE_CODEX_SESSIONS") or home / "sessions")
        snap = latest_codex_limits(root) if root.is_dir() else None
        if not snap:
            return seat_row("openai", "UNKNOWN", "live rate-limit probe %s; no Codex token_count evidence "
                            "under %s" % (live_error, root.as_posix()), "쿼터 근거 없음", cli=cmd)
        observed, limits, path = snap
        source = path.as_posix()
    credits = limits.get("credits") if isinstance(limits.get("credits"), dict) else {}
    has_credits = credits.get("has_credits") is True
    windows = {}
    for name in ("primary", "secondary"):
        window = limits.get(name)
        used = window.get("used_percent") if isinstance(window, dict) else None
        if isinstance(used, (int, float)) and not isinstance(used, bool) and math.isfinite(used):
            windows[name] = (float(used), from_epoch(window.get("resets_at")), window.get("window_minutes"))
    stale = bool(live_error) and current - observed > CODEX_FRESH
    evidence = {"source": source, "observed_at": stamp(observed), "live_probe": live_error or "ok",
                "stale": stale,
                "windows": {k: {"used_percent": u, "resets_kst": kst(r) if r else None,
                                "window_minutes": m} for k, (u, r, m) in windows.items()},
                "has_credits": has_credits, "plan_type": limits.get("plan_type")}
    evidence.update(flags)
    bill = ("; further calls would bill purchased credits", ", 구매 크레딧 과금 위험") if has_credits else ("", "")
    blocking = [(u, r, k) for k, (u, r, _m) in windows.items()
                if u >= threshold and (r is None or r > current)]
    if blocking:
        used, reset, name = max(blocking, key=lambda b: b[1] or current)
        reason = "%s window %g%% used (>= %g%%)%s" % (
            name, used, threshold, " until " + kst(reset) if reset else "")
        short = "쿼터 %g%%%s" % (used, " ~" + kst(reset) if reset else "")
        return seat_row("openai", "ABSENT", reason + bill[0], short + bill[1], reset, evidence, cmd, spent=True)
    if flags.get("rate_limit_reached_type") or flags.get("ordinary_usage_allowed") is False:
        what = ("rateLimitReachedType %s" % flags["rate_limit_reached_type"]
                if flags.get("rate_limit_reached_type") else "ordinaryUsageAllowed false")
        resets = [r for _u, r, _m in windows.values() if r and r > current]
        reset = max(resets) if resets else None
        return seat_row("openai", "ABSENT", "live reply says the usage limit is reached (%s)%s" % (what, bill[0]),
                        "쿼터 소진" + bill[1], reset, evidence, cmd, spent=True)
    if not windows:
        return seat_row("openai", "UNKNOWN", "%s has no usage windows" % (
            "token_count" if live_error else "live rate-limit reply"), "쿼터 근거 없음", evidence=evidence, cli=cmd)
    if stale:  # usage from elsewhere since the snapshot is invisible to it
        passed = [(k, r) for k, (_u, r, _m) in windows.items() if r is not None and r <= current]
        if passed:
            name, reset = passed[0]
            return seat_row("openai", "UNKNOWN", "rollout snapshot's %s window reset at %s and the live probe %s; "
                            "the new window's usage is unknown" % (name, kst(reset), live_error), "쿼터 근거 오래됨",
                            evidence=evidence, cli=cmd)
        name, (used, _r, _m) = max(windows.items(), key=lambda item: item[1][0])
        return seat_row("openai", "UNKNOWN", "rollout snapshot (%s window %g%%) is %d min old and the live probe "
                        "%s; usage may have grown since" % (
                            name, used, (current - observed).total_seconds() // 60, live_error),
                        "쿼터 근거 오래됨", evidence=evidence, cli=cmd)
    if any(u >= threshold for u, _r, _m in windows.values()):
        return seat_row("openai", "READY", "window reset since snapshot", "리셋됨",
                        evidence=evidence, cli=cmd)
    name, (used, _r, _m) = max(windows.items(), key=lambda item: item[1][0])
    return seat_row("openai", "READY", "%s window %g%% used" % (name, used), "쿼터 %g%%" % used,
                    evidence=evidence, cli=cmd)


def _val(node):
    if isinstance(node, dict):
        node = node.get("val")
    try:
        return float(node or 0)
    except (TypeError, ValueError):
        return 0.0


def grok_live_billing(cmd):
    """Grok billing over ACP with no model turn: `grok agent --no-leader stdio`, `initialize`, then
    `_x.ai/billing` (older CLIs: `x.ai/billing`). No prompt is sent. Returns the result object
    ({"config": {...}, "subscription_tier": ...}); ValueError on any failure."""
    def talk(request, _notify):
        init = request(1, "initialize", {"protocolVersion": 1, "clientCapabilities": {
            "fs": {"readTextFile": False, "writeTextFile": False}, "terminal": False},
            "clientInfo": {"name": "ai-debate-seats", "version": "1"}})
        if not isinstance(init, dict) or init.get("protocolVersion") != 1:
            raise ValueError("unsupported ACP protocol version")
        try:
            result = request(2, "_x.ai/billing", {})
        except ValueError as exc:
            if "code -32601" not in str(exc):
                raise
            result = request(3, "x.ai/billing", {})
        if not isinstance(result, dict) or not isinstance(result.get("config"), dict) \
                or "creditUsagePercent" not in result["config"]:
            raise ValueError("billing reply has no config.creditUsagePercent")
        return result

    return rpc_probe(cmd + ["agent", "--no-leader", "stdio"], "xai", "grok agent", talk)


def grok_logged_billing(log):
    """The newest 'billing: fetched credits config' line Grok wrote (only at its own session starts)."""
    if not log.is_file():
        return None
    try:
        lines = tail_lines(log, GROK_TAIL)
    except OSError:
        return None
    for line in reversed(lines):
        if b"billing: fetched credits config" not in line:
            continue
        try:
            return json.loads(line)
        except ValueError:
            continue
    return None


def seat_xai(cmd, probe=True):
    """Live ACP billing first. The log line is only a fallback, and a stale one never proves headroom:
    Grok logs billing at its own session starts, so usage from elsewhere (other sessions, the web, Grok
    Bot) can spend the week while the newest line still shows room (10-03: log 78%, live 100%, then 402)."""
    if not cmd:
        return seat_row("xai", "ABSENT", "grok CLI not found", "CLI 없음")
    home = Path(os.environ.get("GROK_HOME") or Path.home() / ".grok")
    log = Path(os.environ.get("AI_DEBATE_GROK_LOG") or home / "logs" / "unified.jsonl")
    current, threshold = now(), max_used()
    live_error = None if probe else "skipped (--no-probe)"
    if probe:
        try:
            result = grok_live_billing(cmd)
            cfg, tier, on_demand = result["config"], result.get("subscription_tier"), result.get("onDemandEnabled")
            source, observed = "grok agent stdio _x.ai/billing (live, no model turn)", current
        except ValueError as exc:
            live_error = "failed: %s" % str(exc)[:160]
    if live_error:
        record = grok_logged_billing(log)
        if not record:
            return seat_row("xai", "UNKNOWN", "live billing probe %s; no 'billing: fetched credits config' "
                            "line in %s" % (live_error, log.as_posix()), "쿼터 근거 없음", cli=cmd)
        ctx = record.get("ctx") if isinstance(record.get("ctx"), dict) else {}
        cfg = ctx.get("config") if isinstance(ctx.get("config"), dict) else {}
        tier, on_demand, source = ctx.get("subscriptionTier"), ctx.get("onDemandEnabled"), log.as_posix()
        try:
            observed = parse_iso(record.get("ts"))
        except (TypeError, ValueError):
            observed = None
    try:
        pct = float(cfg.get("creditUsagePercent"))
        end_raw = (cfg.get("currentPeriod") or {}).get("end") or cfg.get("billingPeriodEnd")
        end = parse_iso(end_raw) if end_raw else None
    except (TypeError, ValueError, AttributeError):
        return seat_row("xai", "UNKNOWN", "unreadable Grok billing (%s)" % source, "쿼터 근거 없음", cli=cmd)
    paid = _val(cfg.get("onDemandCap")) > 0 or _val(cfg.get("prepaidBalance")) > 0 or on_demand is True
    stale = bool(live_error) and (observed is None or current - observed > GROK_FRESH)
    evidence = {"source": source, "observed_at": stamp(observed) if observed else None,
                "live_probe": live_error or "ok", "stale": stale,
                "credit_usage_percent": pct, "period_end_kst": kst(end) if end else None,
                "tier": tier, "on_demand_cap": _val(cfg.get("onDemandCap")),
                "prepaid_balance": _val(cfg.get("prepaidBalance"))}
    if end is not None and end <= current:
        if stale:  # a new period started after the line; nothing shows how much of it is already spent
            return seat_row("xai", "UNKNOWN", "logged billing period ended %s and the live probe %s; the new "
                            "period's usage is unknown" % (kst(end), live_error), "쿼터 근거 오래됨",
                            evidence=evidence, cli=cmd)
        return seat_row("xai", "READY", "period reset since snapshot", "리셋됨",
                        evidence=evidence, cli=cmd)
    if pct >= threshold:
        reason = "credit usage %g%% (>= %g%%); HTTP 402 expected until %s" % (
            pct, threshold, kst(end) if end else "period end")
        if paid:
            reason += "; on-demand or prepaid balance present, further calls could bill it"
        return seat_row("xai", "ABSENT", reason, "402" + (" ~" + kst(end) if end else ""),
                        end, evidence, cmd, spent=True)
    if stale:
        age = "%d min" % ((current - observed).total_seconds() // 60) if observed else "an unknown time"
        return seat_row("xai", "UNKNOWN", "logged billing (%g%%) is %s old and the live probe %s; usage may "
                        "have grown since" % (pct, age, live_error), "쿼터 근거 오래됨",
                        evidence=evidence, cli=cmd)
    note = "; on-demand or prepaid balance present" if paid else ""
    return seat_row("xai", "READY", "credit usage %g%%%s" % (pct, note), "쿼터 %g%%" % pct,
                    evidence=evidence, cli=cmd)


def parse_json_blob(text):
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object")
    return json.JSONDecoder().raw_decode(text[start:])[0]


def bucket_kind(bucket):
    window = str(bucket.get("window") or "").strip().lower()
    ident = str(bucket.get("id") or "").strip().lower()
    if window in ("weekly", "week", "7d") or (not window and ident.endswith("weekly")):
        return "weekly"
    if window in ("5h", "5-hour", "five_hour") or (not window and ident.endswith("5h")):
        return "5h"
    return window or ident or "?"


def seat_google(cmd, probe):
    if not cmd:
        return seat_row("google", "ABSENT", "agy CLI not found", "CLI 없음")
    if is_shim(cmd):
        return seat_row("google", "UNKNOWN", "shim refused: %s is a .cmd/.bat shim and the prompt would "
                        "pass through cmd.exe; point PATH or AI_DEBATE_CMD_GOOGLE at agy.exe"
                        % Path(cmd[0]).name, "shim 거부", cli=cmd, shim=True)
    if not probe:
        return seat_row("google", "UNKNOWN", "zero-turn /usage probe skipped (--no-probe)",
                        "확인 생략", cli=cmd)
    base = state_root() / "probe"
    base.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="agy-usage-", dir=str(base)))
    out, err = work / "stdout.txt", work / "stderr.txt"
    argv = cmd + ["-p", "/usage", "--output-format", "json", "--print-timeout", "40s"]
    try:
        try:
            rc, timed_out, _secs = run_process(argv, work, child_env("google"), 60, out, err)
            envelope = parse_json_blob(read_text(out))
            if rc != 0 or timed_out:
                raise ValueError("probe incomplete")
            if envelope.get("num_turns") != 0:
                raise ValueError("num_turns=%r, not a zero-turn probe" % envelope.get("num_turns"))
            groups = envelope["command"]["data"]["groups"]
            gemini = next(g for g in groups if g.get("name") == "Gemini Models")
            buckets = []
            for bucket in gemini.get("buckets") or []:
                # agy marshals remaining_fraction with omitempty, so a spent 0.0 bucket omits it.
                frac = bucket.get("remaining_fraction", 0)
                if isinstance(frac, bool) or not isinstance(frac, (int, float)) or not math.isfinite(frac):
                    raise ValueError("non-numeric remaining_fraction %r" % (frac,))
                buckets.append({"id": bucket.get("id"), "window": bucket.get("window"),
                                "kind": bucket_kind(bucket), "remaining_fraction": float(frac),
                                "field_missing": "remaining_fraction" not in bucket,
                                "reset_time": bucket.get("reset_time")})
            missing = {"weekly", "5h"} - {b["kind"] for b in buckets}
            if missing:
                raise ValueError("Gemini Models group lacks the %s bucket" % " and ".join(sorted(missing)))
        except (OSError, ValueError, KeyError, TypeError, AttributeError, StopIteration) as exc:
            detail = str(exc)[:160] if isinstance(exc, ValueError) else ""
            try:
                detail = read_text(err).strip().splitlines()[-1][:200] or detail
            except (OSError, IndexError):
                pass
            return seat_row("google", "UNKNOWN", "agy /usage probe failed (%s)%s" % (
                type(exc).__name__, ": " + detail if detail else ""), "확인 실패", cli=cmd)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    evidence = {"source": "agy -p /usage (zero-turn)", "num_turns": envelope.get("num_turns"),
                "buckets": buckets}
    lowest = min(b["remaining_fraction"] for b in buckets)
    if lowest > 0:
        return seat_row("google", "READY", "Gemini Models remaining %d%%" % round(lowest * 100),
                        "남은 쿼터 %d%%" % round(lowest * 100), evidence=evidence, cli=cmd)
    spent = [b for b in buckets if b["remaining_fraction"] <= 0]
    resets = []
    for bucket in spent:
        try:
            resets.append(parse_iso(bucket["reset_time"]))
        except (KeyError, TypeError, ValueError):
            pass
    reset = max(resets) if resets else None
    if reset is not None and len(resets) == len(spent) and reset <= now():
        return seat_row("google", "READY", "bucket reset since probe", "리셋됨",
                        evidence=evidence, cli=cmd)
    names = ", ".join(str(b.get("id") or b["kind"]) for b in spent)
    return seat_row("google", "ABSENT", "Gemini %s exhausted%s" % (
        names, " until " + kst(reset) if reset else ""),
        "쿼터 0" + (" ~" + kst(reset) if reset else ""), reset, evidence, cmd, spent=True)


def bridge_time(data, path):
    raw = data.get("capturedAt")
    if isinstance(raw, (int, float)) and not isinstance(raw, bool) and math.isfinite(raw):
        return from_epoch(raw / 1000.0)
    if isinstance(raw, str):
        try:
            return parse_iso(raw)
        except ValueError:
            pass
    try:
        return from_epoch(path.stat().st_mtime)
    except OSError:
        return None


def latest_bridge():
    local = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    folder = Path(os.environ.get("AI_DEBATE_CLAUDE_BRIDGE")
                  or Path(local) / "AIUsageWidget" / "bridge" / "claude")
    best = None
    if folder.is_dir():
        for path in folder.glob("*.json"):
            if path.name.endswith(".wrap.json") or path.name == "default-profile.json":
                continue
            data = read_json(path)
            if not isinstance(data, dict) or not isinstance(data.get("rate_limits"), dict):
                continue
            when = bridge_time(data, path)
            if when and (best is None or when > best[0]):
                best = (when, data, path)
    return best


def seat_anthropic(cmd):
    if not cmd:
        return seat_row("anthropic", "ABSENT", "claude CLI not found", "CLI 없음")
    note = "headless claude -p draws the separate headless credit, which is not verifiable locally"
    bridge = latest_bridge()
    if not bridge:
        return seat_row("anthropic", "UNKNOWN", note + "; no AI Usage Widget bridge", "헤드리스 확인 불가",
                        cli=cmd)
    captured, data, path = bridge
    current, threshold = now(), max_used()
    fresh = current - BRIDGE_FRESH <= captured <= current + timedelta(minutes=10)
    evidence = {"source": path.as_posix(), "captured_kst": kst(captured), "fresh": fresh,
                "model": (data.get("model") or {}).get("id") if isinstance(data.get("model"), dict) else None}
    spent, seen = [], []
    for window in ("five_hour", "seven_day"):
        row = data["rate_limits"].get(window) or {}
        used, end = row.get("used_percentage"), from_epoch(row.get("resets_at"))
        if isinstance(used, (int, float)) and not isinstance(used, bool) and math.isfinite(used):
            evidence[window] = {"used_percentage": used, "resets_kst": kst(end) if end else None}
            seen.append("%s %g%%" % (window, used))
            if used >= threshold and ((end and end > current) or (end is None and fresh)):
                spent.append((used, end, window))
    if spent:
        used, end, window = max(spent, key=lambda s: s[0])
        return seat_row("anthropic", "ABSENT", "%s %g%% used (>= %g%%)%s" % (
            window, used, threshold, " until " + kst(end) if end else ""),
            "쿼터 %g%%%s" % (used, " ~" + kst(end) if end else ""), end, evidence, cmd, spent=True)
    if not fresh:
        detail = "bridge captured %s is older than 6h" % kst(captured)
    elif len(seen) < 2:
        detail = "bridge lacks five_hour/seven_day usage"
    else:
        detail = "interactive windows below %g%% (%s)" % (threshold, ", ".join(seen))
    return seat_row("anthropic", "UNKNOWN", "%s; %s" % (note, detail), "헤드리스 확인 불가",
                    evidence=evidence, cli=cmd)


def quota_seat(vendor, probe=True):
    """Quota evidence for `vendor` whoever hosts and whether or not its CLI is installed (no model call)."""
    cmd = resolve_cmd(vendor)
    stand_in = cmd or [BINARIES[vendor]]
    if vendor == "openai":
        return seat_openai(stand_in, probe and bool(cmd))
    if vendor == "xai":
        return seat_xai(stand_in, probe and bool(cmd))
    if vendor == "google":
        return seat_google(stand_in, probe and bool(cmd))
    return seat_anthropic(stand_in)


def host_seat(vendor):
    """The host CLI answers its own seat in-session (nothing is spawned), but a Codex or Grok host still
    spends its own subscription: a spent window there bills purchased credit, so that seat is ABSENT."""
    row = seat_row(vendor, "READY", "in-session (host vendor); register with submit", "세션 내", in_session=True)
    if vendor not in QUOTA_GATED:
        return row
    quota = quota_seat(vendor)
    row["evidence"] = quota.get("evidence") or {}
    row["quota"] = {k: quota.get(k) for k in ("status", "reason", "short", "reset_kst")}
    if quota["status"] == "ABSENT":
        row.update(status="ABSENT", spent=True, host_over_quota=True, reset_kst=quota.get("reset_kst"),
                   short="호스트 " + (quota.get("short") or "쿼터 소진"),
                   reason="WARNING the host is over quota: this %s session itself would spend purchased credit "
                          "(%s); do not answer in-session until the reset" % (DISPLAY[vendor], quota["reason"]))
    return row


def seat_for(vendor, orchestrator, probe=True):
    if vendor == orchestrator:
        return host_seat(vendor)
    cmd = resolve_cmd(vendor)
    if vendor == "openai":
        return seat_openai(cmd, probe)
    if vendor == "xai":
        return seat_xai(cmd, probe)
    if vendor == "google":
        return seat_google(cmd, probe)
    return seat_anthropic(cmd)


def require_orchestrator(value):
    if value not in VENDORS:
        raise DebateError("--orchestrator is required: name the vendor of the CLI that runs this debate "
                          "(%s)" % HOST_TABLE)
    return value


def env_markers(env=None):
    """Host CLI variables in this shell. Confirmed markers keep their values; other vendor-prefixed names are
    recorded by name only (they may hold tokens)."""
    env = os.environ if env is None else env
    vendors, values = [], {}
    for vendor, names in HOST_MARKERS.items():
        hit = {name: condense(env[name], 80) for name in names if env.get(name)}
        if hit:
            vendors.append(vendor)
            values.update(hit)
    others = sorted(k for k in env if k.upper().startswith(MARKER_PREFIXES) and k.upper() not in MARKER_SKIP)
    return {"vendors": vendors, "values": values, "other_names": others}


def marker_vendor(markers):
    """The one vendor the markers clearly name, else None (none, or nested CLIs with inherited markers)."""
    return markers["vendors"][0] if len(markers["vendors"]) == 1 else None


def check_host(orchestrator, override):
    """--orchestrator against this shell's host markers: a clear mismatch exits 2 unless overridden."""
    markers = env_markers()
    seen = marker_vendor(markers)
    if seen and seen != orchestrator and not override:
        raise DebateError("--orchestrator %s does not match this shell: %s says the running CLI is %s. Use "
                          "--orchestrator %s, or pass --orchestrator-override if those variables were inherited "
                          "from another CLI" % (orchestrator, ", ".join("%s=%s" % kv for kv in
                                                                         sorted(markers["values"].items())),
                                                DISPLAY[seen], seen))
    return markers


def check_plain_submit(agenda, vendor):
    """A plain submit registers the stored host's own seat. A shell whose markers clearly name another CLI must
    prove a live session of that vendor instead (--host-session), unless the debate was opened overriding them."""
    seen = marker_vendor(env_markers())
    if seen and seen != vendor and not agenda.get("orchestrator_override"):
        raise DebateError("this shell's environment says the running CLI is %s, but %s is the stored host's own "
                          "seat (orchestrator %s): register it from a live %s session with --host-session <its "
                          "session id>" % (DISPLAY[seen], DISPLAY[vendor], agenda["orchestrator"], DISPLAY[vendor]))


# ---------------------------------------------------------------- host sessions (no model calls)

def host_roots():
    home = Path.home()
    claude = Path(os.environ.get("CLAUDE_CONFIG_DIR") or home / ".claude") / "projects"
    codex = Path(os.environ.get("CODEX_HOME") or home / ".codex") / "sessions"
    grok = Path(os.environ.get("GROK_HOME") or home / ".grok") / "sessions"
    agy = home / ".gemini" / "antigravity-cli" / "brain"
    return {"anthropic": Path(os.environ.get("AI_DEBATE_CLAUDE_PROJECTS") or claude),
            "openai": Path(os.environ.get("AI_DEBATE_CODEX_SESSIONS") or codex),
            "xai": Path(os.environ.get("AI_DEBATE_GROK_SESSIONS") or grok),
            "google": Path(os.environ.get("AI_DEBATE_AGY_BRAIN") or agy)}


def host_candidates(vendor, root, sid):
    if not root.is_dir():
        return []
    if vendor == "anthropic":
        return [folder / (sid + ".jsonl") for folder in root.iterdir() if folder.is_dir()]
    if vendor == "xai":
        return [folder / sid / "updates.jsonl" for folder in root.iterdir() if folder.is_dir()]
    if vendor == "google":
        return [root / sid / ".system_generated" / "logs" / "transcript.jsonl"]
    suffix = ("-" + sid + ".jsonl").lower()  # rollout-<time>-<uuid>.jsonl: the name ends with the exact id
    found = []
    for dirpath, _dirs, names in os.walk(root):
        for name in names:
            if name.startswith("rollout-") and name.lower().endswith(suffix):
                found.append(Path(dirpath) / name)
    return found


def first_entrypoint(path):
    """`entrypoint` of the first Claude record that carries one, read line by line within the scan bound."""
    budget = HOST_SCAN_BYTES
    with open(path, "rb") as stream:
        for _count in range(HOST_SCAN_LINES):
            if budget <= 0:
                break
            line = stream.readline(budget)
            if not line:
                break
            budget -= len(line)
            if b'"entrypoint"' not in line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict) and "entrypoint" in record:
                return record["entrypoint"]
    return None


def codex_session_meta(path):
    """Payload of the session_meta record that opens a rollout (its first line, within the scan bound)."""
    with open(path, "rb") as stream:
        line = stream.readline(HOST_SCAN_BYTES)
    try:
        record = json.loads(line)
    except ValueError:
        return None
    if isinstance(record, dict) and record.get("type") == "session_meta" and isinstance(record.get("payload"), dict):
        return record["payload"]
    return None


def interactive_proof(vendor, path, root, sid):
    """(proof, None) on positive evidence of an interactive session, else (None, reason): fails closed."""
    if vendor == "anthropic":
        entry = first_entrypoint(path)
        if entry in CLAUDE_INTERACTIVE:
            return "entrypoint %s" % entry, None
        if entry is None:
            return None, ("no entrypoint record in the first %d lines / %d MB"
                          % (HOST_SCAN_LINES, HOST_SCAN_BYTES >> 20))
        if isinstance(entry, str) and entry.startswith("sdk-"):
            return None, "entrypoint %s (claude -p / SDK)" % entry
        return None, "entrypoint %r is not a confirmed interactive value (%s)" % (entry, ", ".join(CLAUDE_INTERACTIVE))
    if vendor == "openai":
        payload = codex_session_meta(path)
        if payload is None:
            return None, "the rollout does not open with a readable session_meta record"
        if payload.get("thread_source") == "subagent":
            return None, "Codex thread_source subagent"
        source = payload.get("source")
        if isinstance(source, str) and source in CODEX_INTERACTIVE:
            return "source %s" % source, None
        kind = "{%s}" % ",".join(source) if isinstance(source, dict) else source
        return None, "Codex session source %s (interactive: %s)" % (kind, ", ".join(CODEX_INTERACTIVE))
    if vendor == "xai":
        summary = read_json(path.parent / "summary.json")
        if not isinstance(summary, dict):
            return None, "no readable summary.json next to updates.jsonl"
        kind = summary.get("session_kind")
        if kind is None:  # interactive Grok sessions carry no session_kind; headless runs record "headless"
            return "summary.json without session_kind", None
        if kind == "headless":
            return None, "Grok session_kind headless"
        return None, "Grok session_kind %r is not a confirmed interactive value" % (kind,)
    if agy_history_lists(root, sid):
        return "listed in history.jsonl", None
    return None, ("conversation not listed in %s (a one-shot agy --print run)"
                  % (root.parent / "history.jsonl").as_posix())


def agy_history_lists(root, sid):
    history = root.parent / "history.jsonl"
    try:
        lines = tail_lines(history, 4 * 1024 * 1024)
    except OSError:
        return False
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict) and record.get("conversationId") == sid:
            return True
    return False


def squash(text):
    return " ".join(text.split())


def leaf_strings(node, depth=0):
    """Every string in a JSON record; JSON-encoded strings (Codex arguments, agy args) are unwrapped too."""
    if isinstance(node, str):
        yield node
        inner = node.strip()
        if depth < 2 and len(inner) > 1 and inner[0] in "{[\"" and inner[-1] in "}]\"":
            try:
                value = json.loads(inner)
            except ValueError:
                return
            yield from leaf_strings(value, depth + 1)
    elif isinstance(node, dict):
        for value in node.values():
            yield from leaf_strings(value, depth)
    elif isinstance(node, list):
        for value in node:
            yield from leaf_strings(value, depth)


def binding_files(vendor, path):
    """The session's own record: its transcript, plus Claude Code's per-session subagent and tool-result files."""
    files = [(path, HOST_BIND_TAIL)]
    side = path.with_suffix("") if vendor == "anthropic" else None
    if side is not None and side.is_dir():
        extra = []
        for item in side.rglob("*"):
            if item.suffix not in (".jsonl", ".txt"):
                continue
            try:
                if item.is_file():
                    extra.append((item.stat().st_mtime, item))
            except OSError:
                continue
        files += [(item, HOST_BIND_EXTRA) for _m, item in sorted(extra, reverse=True)[:HOST_BIND_FILES]]
    return files


def session_binding(vendor, path, inputs_sha, answer_text):
    """('fingerprint' | 'answer', file) when the session's own record holds this prompt's input fingerprint or
    the answer's first 200 characters (whitespace-normalized, at least 40); (None, None) otherwise."""
    token = inputs_sha.encode("ascii") if inputs_sha else None
    needle = squash(answer_text)[:BIND_PREFIX]
    needle = needle if len(needle) >= BIND_MIN else None
    budget = HOST_BIND_BUDGET
    for item, limit in binding_files(vendor, path):
        if budget <= 0:
            break
        try:
            lines = tail_lines(item, min(limit, budget))
        except OSError:
            continue
        budget -= sum(len(line) + 1 for line in lines)
        if token and any(token in line for line in lines):
            return "fingerprint", item
        if not needle:
            continue
        if item.suffix == ".txt":
            if needle in squash(b"\n".join(lines).decode("utf-8", "replace")):
                return "answer", item
            continue
        for line in lines:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if any(needle in squash(text) for text in leaf_strings(record)):
                return "answer", item
    return None, None


def prove_host_session(vendor, sid, inputs_sha, answer_text):
    """A live interactive `vendor` session on this machine (transcript written in the last 30 min) whose own
    record is bound to this answer. Every check fails closed."""
    if not isinstance(sid, str) or not HOST_SESSION_RE.fullmatch(sid) or sid.endswith("."):
        raise DebateError("--host-session must be the live session id (8-128 of A-Z a-z 0-9 . _ -, "
                          "alphanumeric first): %r" % (sid,))
    if vendor == "openai" and not UUID_RE.fullmatch(sid):
        raise DebateError("a Codex --host-session is the rollout UUID (the 36-character id that ends "
                          "rollout-<time>-<id>.jsonl): %r" % (sid,))
    root = host_roots()[vendor]
    best = None
    for path in host_candidates(vendor, root, sid):
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        except (OSError, ValueError, OverflowError):
            continue
        if best is None or mtime > best[0]:
            best = (mtime, path)
    if best is None:
        raise DebateError("no live %s session %s on this machine: expected %s under %s"
                          % (DISPLAY[vendor], sid, HOST_LAYOUT[vendor], root.as_posix()))
    mtime, path = best
    age = now() - mtime
    if age > HOST_LIVE or age < -HOST_SKEW:
        raise DebateError("%s session %s is not live: %s was last written %s (%.0f min ago; must be within %d min)"
                          % (DISPLAY[vendor], sid, path.as_posix(), kst(mtime), age.total_seconds() / 60,
                             HOST_LIVE.total_seconds() // 60))
    try:
        proof, problem = interactive_proof(vendor, path, root, sid)
    except OSError as exc:
        proof, problem = None, "unreadable transcript: %s" % (exc.strerror or exc)
    if problem:
        raise DebateError("%s session %s is not interactive (%s); only a live interactive session can answer "
                          "a seat in-session" % (DISPLAY[vendor], sid, problem))
    bound_by, bound_in = session_binding(vendor, path, inputs_sha, answer_text)
    if not bound_by:
        raise DebateError("%s session %s is not bound to this answer: its own record holds neither this prompt's "
                          "input fingerprint (%s..., printed by prompt and written in the prompt file) nor the "
                          "answer's first %d characters; run prompt and write the answer from that session"
                          % (DISPLAY[vendor], sid, (inputs_sha or "")[:12], BIND_PREFIX))
    evidence = {"vendor": vendor, "path": path.as_posix(), "modified_at": stamp(mtime),
                "age_min": round(age.total_seconds() / 60, 1), "interactive": proof,
                "bound_by": bound_by, "bound_in": bound_in.as_posix()}
    if vendor == "google":
        evidence["history_listed"] = True
    return evidence


def session_conflict(folder, vendor, ids):
    """(vendor, round, id) when another vendor's answer in this debate already used one of `ids`."""
    for rnd in ROUNDS:
        for other in VENDORS:
            if other == vendor:
                continue
            row = meta(folder, rnd, other)
            if row.get("status") != "ok":
                continue
            hit = {row.get("host_session"), row.get("session_id")} & ids
            if hit:
                return other, rnd, sorted(hit)[0]
    return None


def compute_seats(orchestrator, probe=True):
    return {"checked_at": stamp(now()), "orchestrator": orchestrator,
            "vendors": {v: seat_for(v, orchestrator, probe) for v in VENDORS}}


def seat_summary(vendors):
    marks = {"READY": "✓", "ABSENT": "✗"}
    return " · ".join("%s %s(%s)" % (DISPLAY[v], marks.get(vendors[v]["status"], "?"),
                                     vendors[v]["short"] or vendors[v]["status"]) for v in VENDORS)


# ---------------------------------------------------------------- debate storage

def check_id(debate_id):
    text = debate_id if isinstance(debate_id, str) else ""
    if not ID_RE.fullmatch(text) or text.endswith(".") or text.split(".")[0].upper() in RESERVED_NAMES:
        raise DebateError("invalid debate id: %r (1-64 of A-Z a-z 0-9 . _ -, alphanumeric first, "
                          "no trailing dot, not a Windows device name)" % (debate_id,))
    return text


def debate_dir(debate_id):
    return state_root() / "debates" / check_id(debate_id)


def load(debate_id):
    folder = debate_dir(debate_id)
    agenda = read_json(folder / "agenda.json")
    if not isinstance(agenda, dict):
        raise DebateError("no debate %s under %s" % (debate_id, folder.as_posix()))
    return folder, agenda


def rpath(folder, rnd, vendor, suffix):
    return folder / "rounds" / rnd / (vendor + suffix)


def meta(folder, rnd, vendor):
    return read_json(rpath(folder, rnd, vendor, ".meta.json")) or {}


def answer(folder, rnd, vendor):
    if meta(folder, rnd, vendor).get("status") != "ok":
        return None
    path = rpath(folder, rnd, vendor, ".md")
    return read_text(path) if path.is_file() else None


def ok_vendors(folder, rnd):
    return [v for v in VENDORS if meta(folder, rnd, v).get("status") == "ok"
            and rpath(folder, rnd, v, ".md").is_file()]


def lenses_for(debate_id):
    offset = int(hashlib.sha256(debate_id.encode("utf-8")).hexdigest()[:8], 16) % 4
    return {v: LENSES[(i + offset) % 4] for i, v in enumerate(VENDORS)}


def order_key(*parts):
    return hashlib.sha256(":".join(parts).encode("utf-8")).hexdigest()


def judge_vendor(folder):
    picked = read_json(folder / "judge.json") or {}
    vendor = picked.get("vendor")
    if vendor in VENDORS and meta(folder, "judge", vendor).get("status") == "ok":
        return vendor
    done = ok_vendors(folder, "judge")
    return done[0] if done else (vendor if vendor in VENDORS else None)


def check_judge_seat(folder, agenda, vendor, require_pick):
    """The judge round belongs to the vendor judge-pick recorded; the interject subject never judges."""
    if vendor == agenda.get("subject_vendor"):
        raise DebateError("%s is the interject subject (the agent under review): it never judges its own case"
                          % DISPLAY[vendor])
    picked = read_json(folder / "judge.json")
    chosen = picked.get("vendor") if isinstance(picked, dict) else None
    if chosen not in VENDORS:
        if require_pick:
            raise DebateError("no judge chosen yet: run judge-pick first; only the seat it picks answers the "
                              "judge round")
        return {}
    if chosen != vendor:
        raise DebateError("judge-pick chose %s for this debate; %s cannot answer the judge round (re-run "
                          "judge-pick if that seat became unavailable)" % (DISPLAY[chosen], DISPLAY[vendor]))
    return picked


def check_round_open(folder, rnd):
    if rnd in ("r1", "r2") and ok_vendors(folder, "judge"):
        raise DebateError("%s is closed: the judge already answered; a returning vendor joins with "
                          "--round catchup" % rnd)


def fresh_workdir(debate_id, name):
    """Empty per-call cwd outside the debate folder, so no relative path reaches round files."""
    path = state_root() / "work" / debate_id / name
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    if path.exists():
        path = path.with_name(name + "-" + uuid.uuid4().hex[:8])
    path.mkdir(parents=True)
    return path


def acquire_lock(folder, rnd, vendor):
    path = rpath(folder, rnd, vendor, ".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    for _attempt in range(3):
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            held = read_json(path)
            if not isinstance(held, dict):
                try:
                    young = time.time() - path.stat().st_mtime < 10
                except OSError:
                    continue
                if young:
                    raise DebateError("%s %s is starting in another process" % (rnd, vendor)) from None
            elif pid_alive(held.get("pid"), held.get("started")):
                raise DebateError("%s %s is already running (pid %s); wait for it or let it time out"
                                  % (rnd, vendor, held.get("pid"))) from None
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"pid": os.getpid(), "started": time.time()}, stream)
        return path
    raise DebateError("could not take the %s %s lock" % (rnd, vendor))


def release_lock(path):
    held = read_json(path)
    if isinstance(held, dict) and held.get("pid") == os.getpid():
        try:
            path.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------- text helpers

def clean_line(line):
    line = re.sub(r"^[\s>#*`_]+", "", line)
    return re.sub(r"[\s*`_]+$", "", line)


def head_lines(text, count=6):
    rows = [clean_line(x) for x in (text or "").splitlines()]
    return [x for x in rows if x][:count]


def first_line(text):
    rows = head_lines(text, 1)
    return rows[0] if rows else ""


def tagged(text, tag):
    for line in head_lines(text):
        line = re.sub(r"[*`]+", "", line).strip()
        match = re.match(r"%s\s*[:：]\s*(.+)$" % tag, line, re.I)
        if match:
            return match.group(1).strip()
    return None


def section(text, name):
    out, inside = [], False
    for line in (text or "").splitlines():
        if re.match(r"^\s*#{1,6}\s*", line):
            title = re.sub(r"^\s*#{1,6}\s*", "", line).strip()
            if inside:
                break
            inside = title.startswith(name)
            continue
        if inside:
            out.append(line)
    return "\n".join(out).strip()


def condense(text, cap):
    rows = [re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", x) for x in (text or "").splitlines()]
    flat = re.sub(r"\s+", " ", " ".join(r for r in rows if r.strip()))
    flat = re.sub(r" {2,}", " ", CTRL_RE.sub("", flat)).strip()
    return flat if len(flat) <= cap else flat[:cap - 1].rstrip() + "…"


def clean_item(text):
    return " ".join(CTRL_RE.sub(" ", text or "").split())


def call_of(text):
    value = tagged(text, "CALL")
    if not value:
        return None
    value = re.sub(r"\b(SHIP|ASK)[\s_-]+(NOW|USER)\b", r"\1_\2", value.upper())
    match = CALL_RE.search(value)
    return match.group(1) if match else None


def review_kind(text):
    line = first_line(text).replace("**", "").replace("__", "").strip()
    match = re.match(r"(ACCEPT|OBJECT)\b", line, re.I)
    return (match.group(1).upper() if match else None), line


def r1_stance(text, mode):
    if mode == "interject":
        call = call_of(text)
        return "CALL: " + call if call else condense(first_line(text), 160)
    stance = section(text, "입장")
    return condense(stance.splitlines()[0] if stance else first_line(text), 160)


def format_warnings(rnd, mode, text):
    missing = []
    if rnd == "r1" and mode == "interject":
        if not call_of(text):
            missing.append("CALL: line")
        need = ["근거", "지금 자를 것", "다음 한 걸음", "시간 상자"]
    elif rnd == "r1":
        need = ["입장", "핵심 근거", "내 입장의 가장 강한 반론", "조건·전제", "기준별 평가"]
    elif rnd == "r2":
        need = []
        if not re.match(r"^(UNCHANGED|REVISED)\b", first_line(text).replace("**", ""), re.I):
            missing.append("UNCHANGED/REVISED first line")
    elif rnd == "judge":
        need = []
        if not (call_of(text) if mode == "interject" else tagged(text, "VERDICT")):
            missing.append(("CALL" if mode == "interject" else "VERDICT") + ": line")
        if not tagged(text, "CONFIDENCE"):
            missing.append("CONFIDENCE: line")
    else:
        need = []
        if not review_kind(text)[0]:
            missing.append("ACCEPT/OBJECT first line")
    for name in need:
        if not section(text, name) and not re.search(r"^\s*#{1,6}\s*" + re.escape(name), text, re.M):
            missing.append("## " + name)
    return missing


def redact(text):
    total = 0
    for pattern in SECRET_RES:
        text, count = pattern.subn("[REDACTED]", text)
        total += count
    text, count = SECRET_ASSIGN_RE.subn(lambda m: m.group(1) + m.group(2) + "[REDACTED]", text)
    return text, total + count


def clip_bytes(text, limit):
    data = text.encode("utf-8")
    if len(data) <= limit:
        return text
    return data[:max(0, limit)].decode("utf-8", "ignore").rstrip()


# ---------------------------------------------------------------- prompts

def fit(blocks, cap=PROMPT_CAP):
    """Join (name, text, truncatable) blocks under `cap` chars with explicit markers."""
    total = sum(len(text) for _n, text, _t in blocks)
    truncated = []
    texts = [text for _n, text, _t in blocks]
    if total > cap:
        flex = [i for i, (_n, text, flag) in enumerate(blocks) if flag and text]
        fixed = total - sum(len(texts[i]) for i in flex)
        if fixed + 40 * len(flex) > cap:
            raise DebateError("fixed prompt parts need %d chars (cap %d)" % (fixed, cap))
        left = cap - fixed - 40 * len(flex)
        order = sorted(flex, key=lambda i: len(texts[i]))
        for rank, i in enumerate(order):
            take = min(len(texts[i]), left // (len(order) - rank))
            left -= take
            if take < len(texts[i]):
                omitted = len(texts[i]) - take
                texts[i] = texts[i][:take].rstrip() + "\n[... %d자 생략]\n\n" % omitted
                truncated.append({"block": blocks[i][0], "omitted_chars": omitted})
    text = "".join(texts)
    if len(text) > cap:
        raise DebateError("prompt is %d chars after truncation (cap %d)" % (len(text), cap))
    return text, truncated


def fingerprint(used, seat):
    """Input fingerprint of one prompt. The seat (debate/round/vendor) salts it, so even an r1 prompt with no
    answers behind it has its own value, which binds a --host-session answer to this prompt."""
    digest = hashlib.sha256(("%s\0" % seat).encode("utf-8"))
    for rnd, vendor, text in sorted(used):
        digest.update(("%s/%s\0%s\0" % (rnd, vendor, text)).encode("utf-8"))
    return {"present": sorted({v for _r, v, _t in used}), "sha256": digest.hexdigest()}


def seat_card(agenda, label, role, inputs_sha):
    return ("# 좌석 카드\n- 토론 ID: %s\n- 모드: %s\n- 라운드: %s\n- 역할: %s\n"
            "- 원칙: 다른 위원의 정체는 가려져 있다. 근거 자료에 없는 사실을 지어내지 말고 "
            "추정은 추정이라고 표시한다.\n- 입력 지문: %s\n\n" % (agenda["id"], agenda["mode"], label, role,
                                                         inputs_sha))


def agenda_blocks(agenda, with_evidence=True):
    interject = agenda["mode"] == "interject"
    lines = ["## 상황" if interject else "## 안건", "제목: " + agenda["title"],
             "질문: " + agenda["question"], "", "선택지:"]
    if agenda["options"]:
        lines += ["- 선택지 %d: %s" % (i, o) for i, o in enumerate(agenda["options"], 1)]
    elif interject:
        lines.append("- " + " | ".join(CALLS))
    else:
        lines.append("- (명시된 선택지 없음: 필요하면 직접 정의한다)")
    lines += ["", "판단 기준:"]
    lines += ["- " + c for c in agenda["criteria"]] or ["- (명시된 기준 없음)"]
    blocks = [("agenda", "\n".join(lines) + "\n\n", False)]
    if with_evidence:
        head = "## 작업 중 에이전트 스냅숏\n" if interject else "## 근거 자료\n"
        blocks.append(("evidence_head", head, False))
        blocks.append(("evidence", (agenda.get("evidence") or "(제공된 근거 자료 없음)") + "\n\n", True))
    return blocks


def anon_positions(folder, agenda, take):
    present = ok_vendors(folder, "r1")
    ordered = sorted(present, key=lambda v: order_key(agenda["id"], "judge", v))
    blocks, mapping = [], {}
    for i, vendor in enumerate(ordered, 1):
        label = "P%d" % i
        mapping[label] = vendor
        body = "### %s\n#### 1라운드\n%s\n\n" % (label, take("r1", vendor).strip())
        second = take("r2", vendor)
        if second:
            body += "#### 교차검증\n%s\n\n" % second.strip()
        blocks.append(("position-" + label, body, True))
    return blocks, mapping


def build_prompt(folder, agenda, rnd, vendor, cap=PROMPT_CAP):
    mode, lenses = agenda["mode"], agenda["lenses"]
    lens = lenses[vendor]
    footer = ("footer", "\n" + FOOTER + "\n", False)
    extra, used = {}, []

    def card(label, role):  # filled in once the input fingerprint is known
        return (label, role)

    def take(r, v):
        text = answer(folder, r, v)
        if text is not None:
            used.append((r, v, text))
        return text

    if rnd == "r1":
        lens_text = (INTERJECT_LENS_TEXT if mode == "interject" else LENS_TEXT)[lens]
        blocks = [("card", card("r1 (독립 입장)", "패널 위원 · 렌즈: %s (%s)" % (lens, LENS_KO[lens])), False),
                  ("lens", "## 렌즈\n" + lens_text + "\n\n", False)]
        blocks += agenda_blocks(agenda)
        blocks += [("instructions", INTERJECT_R1_INSTR if mode == "interject" else R1_INSTR, False),
                   footer]
    elif rnd == "r2":
        if mode != "full":
            raise DebateError("r2 cross-examination runs only in full mode (this debate: %s)" % mode)
        others = [v for v in ok_vendors(folder, "r1") if v != vendor]
        if not others:
            raise DebateError("r2 needs at least one other r1 answer")
        others.sort(key=lambda v: order_key(agenda["id"], vendor, "r2", v))
        blocks = [("card", card("r2 (교차검증)", "패널 위원 · 렌즈: %s (%s)" % (lens, LENS_KO[lens])), False),
                  ("lens", "## 렌즈\n" + LENS_TEXT[lens] + "\n\n", False)]
        blocks += agenda_blocks(agenda)
        # A fresh-session seat cannot remember round 1, so its own stance travels in its own
        # section; it never joins the anonymized list.
        own = take("r1", vendor)
        if own is not None:
            blocks.append(("own", "## 당신의 1라운드 입장\n%s\n\n" % own.strip(), True))
        blocks.append(("positions_head", "## 다른 위원의 1라운드 입장 (익명)\n", False))
        mapping = {}
        for i, other in enumerate(others):
            label = "ABCDEFG"[i]
            mapping[label] = other
            blocks.append(("position-" + label, "### 입장 %s\n%s\n\n"
                           % (label, take("r1", other).strip()), True))
        blocks += [("instructions", R2_INSTR, False), footer]
        extra["anon"] = mapping
    elif rnd == "judge":
        positions, mapping = anon_positions(folder, agenda, take)
        if len(positions) < 2:
            raise DebateError("judge needs at least 2 r1 positions (have %d): not a debate"
                              % len(positions))
        blocks = [("card", card("judge (판정)", "심판 · 새 세션 · 블라인드"), False)]
        blocks += agenda_blocks(agenda)
        blocks.append(("positions_head", "## 입장 (익명, 순서 무작위)\n", False))
        blocks += positions
        blocks += [("instructions", INTERJECT_JUDGE_INSTR if mode == "interject" else JUDGE_INSTR,
                    False), footer]
        extra.update(anon=mapping, positions_count=len(mapping),
                     judge_wrote_position=vendor in mapping.values())
    elif rnd in ("ratify", "catchup"):
        jv = judge_vendor(folder)
        verdict = take("judge", jv) if jv else None
        if not verdict:
            raise DebateError("%s needs a completed judge answer" % rnd)
        positions, mapping = anon_positions(folder, agenda, take)
        role = "추인 위원" if rnd == "ratify" else "후속 합류 위원 (토론 당시 불참)"
        blocks = [("card", card("%s (%s)" % (rnd, "추인" if rnd == "ratify" else "후속 합류"), role), False)]
        blocks += agenda_blocks(agenda)
        blocks += [("verdict_head", "## 판정\n", False), ("verdict", verdict.strip() + "\n\n", True),
                   ("positions_head", "## 입장 (익명)\n", False)]
        blocks += positions
        blocks += [("instructions", RATIFY_INSTR if rnd == "ratify" else CATCHUP_INSTR, False), footer]
        extra["anon"] = mapping
    else:
        raise DebateError("unknown round %s" % rnd)
    extra["inputs"] = fingerprint(used, "%s/%s/%s" % (agenda["id"], rnd, vendor))
    blocks = [(name, seat_card(agenda, *text, extra["inputs"]["sha256"]) if name == "card" else text, flag)
              for name, text, flag in blocks]
    text, truncated = fit(blocks, cap)
    return text, truncated, extra


def write_prompt(folder, agenda, rnd, vendor, cap=PROMPT_CAP):
    text, truncated, extra = build_prompt(folder, agenda, rnd, vendor, cap)
    path = rpath(folder, rnd, vendor, ".prompt.md")
    write_text(path, text)
    row = meta(folder, rnd, vendor)
    for key in PROMPT_KEYS:
        row.pop(key, None)
    row.update({"vendor": vendor, "round": rnd, "truncated": truncated,
                "prompt": {"path": path.as_posix(), "chars": len(text), "built_at": stamp(now())}})
    row.update(extra)
    row.setdefault("status", "prompted")
    write_json(rpath(folder, rnd, vendor, ".meta.json"), row)
    return {"vendor": vendor, "path": path.as_posix(), "chars": len(text), "truncated": truncated,
            "inputs_sha256": extra["inputs"]["sha256"]}


def default_vendors(folder, agenda, rnd):
    r1 = ok_vendors(folder, "r1")
    if rnd == "r1":
        return list(VENDORS)
    if rnd in ("r2", "ratify"):
        return r1
    jv = judge_vendor(folder)
    if rnd == "judge":
        if not jv:
            raise DebateError("no judge chosen yet: run judge-pick or pass --vendor")
        return [jv]
    done = ok_vendors(folder, "catchup")
    return [v for v in VENDORS if v not in r1 and v not in done]


# ---------------------------------------------------------------- vendor calls

def vendor_argv(vendor, cmd, work, folder, rnd, model, effort, timeout, prompt_text):
    prompt_path = rpath(folder, rnd, vendor, ".prompt.md")
    info = {"stdin": None, "redact": None, "session_id": None, "last": None}
    if vendor == "openai":
        last = rpath(folder, rnd, vendor, ".last.txt")
        info.update(stdin=prompt_path, last=last)
        argv = cmd + ["exec", "--ephemeral", "--ignore-user-config", "--skip-git-repo-check",
                      "--sandbox", "read-only", "-C", str(work), "-m", model,
                      "-c", 'model_reasoning_effort="%s"' % effort, "-o", str(last), "-"]
    elif vendor == "xai":
        prompt_txt = rpath(folder, rnd, vendor, ".prompt.txt")
        prompt_txt.write_bytes(prompt_text.encode("utf-8"))
        info["session_id"] = str(uuid.uuid4())
        argv = cmd + ["--no-auto-update", "--cwd", str(work), "--prompt-file", str(prompt_txt),
                      "--verbatim", "--output-format", "plain", "--session-id", info["session_id"],
                      "--model", model, "--reasoning-effort", effort, "--max-turns", "1",
                      "--no-subagents", "--disable-web-search", "--tools", "",
                      "--disallowed-tools", "Agent", "--deny", "MCPTool", "--sandbox", "read-only"]
    elif vendor == "google":
        # agy has no effort flag; the effort already sits in the model name (agy_model).
        limit = max(30, int(timeout) - 30)
        argv = cmd + ["--print", prompt_text, "--model", model, "--mode", "plan", "--sandbox",
                      "--output-format", "json", "--print-timeout", "%ds" % limit]
        info["redact"] = len(cmd) + 1
    else:
        info["stdin"] = prompt_path
        argv = cmd + ["--safe-mode", "--strict-mcp-config", "--tools", "", "--permission-prompts",
                      "none", "--no-session-persistence", "--model", model, "--effort", effort,
                      "--output-format", "json", "-p",
                      "Follow only the task supplied via standard input."]
    return argv, info


def agy_model(model, effort):
    """agy takes the effort as the model-name suffix (gemini-3.1-pro-high); returns (model, effort)."""
    base, current = model, None
    for level in AGY_EFFORTS:
        if model.endswith("-" + level):
            base, current = model[:-len(level) - 1], level
            break
    if not effort:
        return model, current
    if not re.fullmatch(r"[a-z][a-z0-9]{0,15}", effort):
        raise DebateError("agy effort is a model-name suffix such as low or high, not %r" % effort)
    return base + "-" + effort, effort


def cmdline_units(argv):
    return len(subprocess.list2cmdline(argv).encode("utf-16-le")) // 2


def fit_cmdline(folder, agenda, rnd, vendor, build):
    """agy carries the prompt in argv: shrink it until the command line fits Windows."""
    cap = PROMPT_CAP
    for _attempt in range(6):
        prompt_text = read_text(rpath(folder, rnd, vendor, ".prompt.md"))
        argv, info = build(prompt_text)
        size = cmdline_units(argv)
        if size <= CMDLINE_CAP:
            return argv, info, prompt_text, size, None
        cap = min(cap, len(prompt_text)) - (size - CMDLINE_CAP) - 200
        if cap < MIN_PROMPT_CAP:
            break
        try:
            write_prompt(folder, agenda, rnd, vendor, cap)
        except DebateError as exc:
            return None, None, None, size, "prompt cannot shrink to fit the command line: %s" % exc
    return None, None, None, size, ("agy command line is %d chars (> %d) even after shrinking the prompt"
                                    % (size, CMDLINE_CAP))


def interpret(vendor, rc, timed_out, stdout, stderr, info):
    """Return (status, reason, answer_text, session_id)."""
    session = info.get("session_id")
    text, error_text, is_error = stdout, "", False
    if vendor == "openai":
        last = info.get("last")
        if last and last.is_file() and read_text(last).strip():
            text = read_text(last)
        match = re.search(r"session id:\s*([0-9A-Fa-f-]{36})", stderr + "\n" + stdout)
        session = match.group(1) if match else session
    elif vendor == "google":
        try:
            envelope = parse_json_blob(stdout)
            text = envelope.get("response") or ""
            session = envelope.get("conversation_id") or session
            is_error = envelope.get("status") not in (None, "SUCCESS")
            error_text = json.dumps(envelope.get("error") or envelope.get("status") or "",
                                    ensure_ascii=False)
        except (ValueError, AttributeError):
            text = "" if stdout.lstrip().startswith("{") else stdout
    elif vendor == "anthropic":
        try:
            envelope = parse_json_blob(stdout)
            text = envelope.get("result") or ""
            session = envelope.get("session_id") or session
            is_error = envelope.get("is_error") is True
            error_text = text if is_error else ""
        except (ValueError, AttributeError):
            text = ""
    text = text.strip()
    # Quota text inside a successful answer is content, not a failure signature.
    if rc != 0 or is_error or not text or re.match(r"\s*API error \(status 402", stdout):
        scope = "\n".join((stderr, error_text, stdout))
        match = QUOTA_RE.search(scope)
        if match:
            excerpt = scope[max(0, match.start() - 60):match.end() + 80]
            return "absent", "quota: " + condense(excerpt, 200), text, session
    if timed_out:
        return "failed", "timeout (process tree killed)", text, session
    if "AGY_ERROR" in stderr:
        line = next((x for x in stderr.splitlines() if "AGY_ERROR" in x), "AGY_ERROR")
        return "failed", condense(line, 200), text, session
    if rc != 0:
        tail = condense("\n".join(stderr.strip().splitlines()[-3:]), 200)
        return "failed", "rc=%s%s" % (rc, ": " + tail if tail else ""), text, session
    if is_error:
        return "failed", "CLI reported an error: " + condense(error_text or text, 200), text, session
    if vendor == "google" and TIMEOUT_WARN_RE.search(stderr):
        return "failed", "partial: agy --print-timeout expired", text, session
    if not text:
        return "failed", "empty answer", text, session
    return "ok", "", text, session


def git_ancestor(path):
    return next((p for p in (path, *path.parents) if (p / ".git").exists()), None)


def settle(folder, rnd, vendor, row, status, reason):
    row.update({"status": status, "reason": reason, "checked_at": stamp(now())})
    write_json(rpath(folder, rnd, vendor, ".meta.json"), row)
    emit({"vendor": vendor, "round": rnd, "status": status, "reason": reason})
    return {"ok": 0, "absent": 3}.get(status, 4)


def do_call(args):
    folder, agenda = load(args.id)
    rnd, vendor = args.round, args.vendor
    if vendor == agenda["orchestrator"]:
        raise DebateError("the %s seat is the host's own seat (orchestrator %s): answer it in-session "
                          "(a fresh subagent where the host has one) and register it with submit"
                          % (DISPLAY[vendor], vendor))
    if rnd == "judge":
        check_judge_seat(folder, agenda, vendor, require_pick=False)
    if meta(folder, rnd, vendor).get("status") == "ok":
        raise DebateError("%s %s already answered; remove its files to redo" % (rnd, vendor))
    check_round_open(folder, rnd)
    lock = acquire_lock(folder, rnd, vendor)
    try:
        return call_locked(args, folder, agenda)
    finally:
        release_lock(lock)


def call_locked(args, folder, agenda):
    rnd, vendor, orchestrator = args.round, args.vendor, agenda["orchestrator"]
    if meta(folder, rnd, vendor).get("status") == "ok":
        raise DebateError("%s %s already answered; remove its files to redo" % (rnd, vendor))
    model = args.model or DEFAULTS[vendor][0]
    effort = args.effort or DEFAULTS[vendor][1]
    if vendor == "google":
        model, effort = agy_model(model, args.effort)
    seat = seat_for(vendor, orchestrator, probe=True)
    row = meta(folder, rnd, vendor)
    row.update({"vendor": vendor, "round": rnd, "model": model, "effort": effort,
                "readiness": {k: seat.get(k) for k in ("status", "reason", "short", "reset_kst")},
                "accepted_unknown": seat["status"] == "UNKNOWN"})
    row.setdefault("truncated", [])
    if seat.get("shim"):
        return settle(folder, rnd, vendor, row, "failed", seat["reason"])
    if not (seat["status"] == "READY" or (seat["status"] == "UNKNOWN" and args.accept_unknown)):
        suffix = "" if seat["status"] == "ABSENT" else " (pass --accept-unknown to try anyway)"
        row["short"] = seat.get("short")
        return settle(folder, rnd, vendor, row, "absent",
                      "%s: %s%s" % (seat["status"], seat["reason"], suffix))
    cmd = seat.get("cli") or resolve_cmd(vendor)
    if not cmd:
        raise DebateError("%s CLI not found" % BINARIES[vendor])
    work = fresh_workdir(agenda["id"], "%s-%s" % (rnd, vendor))
    if vendor == "openai" and git_ancestor(work):
        raise DebateError("Codex workdir must have no .git ancestor: %s" % git_ancestor(work).as_posix())
    write_prompt(folder, agenda, rnd, vendor)

    def build(text):
        return vendor_argv(vendor, cmd, work, folder, rnd, model, effort, args.timeout, text)

    if vendor == "google":
        argv, info, prompt_text, size, problem = fit_cmdline(folder, agenda, rnd, vendor, build)
    else:
        prompt_text = read_text(rpath(folder, rnd, vendor, ".prompt.md"))
        (argv, info), size, problem = build(prompt_text), None, None
    fresh = meta(folder, rnd, vendor)
    for key in PROMPT_KEYS:
        row.pop(key, None)
    row.update({k: v for k, v in fresh.items() if k in PROMPT_KEYS})
    row["cmdline_chars"] = size
    if problem:
        return settle(folder, rnd, vendor, row, "failed", problem)
    redacted = list(argv)
    if info["redact"] is not None:
        redacted[info["redact"]] = "<prompt:%d chars>" % len(prompt_text)
    out, err = rpath(folder, rnd, vendor, ".stdout.txt"), rpath(folder, rnd, vendor, ".stderr.txt")
    if info["last"] is not None and info["last"].exists():
        info["last"].unlink()
    meta_path = rpath(folder, rnd, vendor, ".meta.json")
    started = now()
    row.update({"cli": Path(cmd[0]).name, "argv": redacted, "workdir": work.as_posix(),
                "status": "running", "reason": "", "pid": os.getpid(), "started": stamp(started)})
    write_json(meta_path, row)

    def spawned(pid, job):
        row.update(child_pid=pid, job_object=job)
        write_json(meta_path, row)

    try:
        rc, timed_out, seconds = run_process(argv, work, child_env(vendor), args.timeout, out, err,
                                             info["stdin"], spawned)
        stdout, stderr = read_text(out), read_text(err)
    except OSError as exc:
        rc, timed_out, seconds, stdout, stderr = None, False, 0.0, "", "spawn failed: %s" % exc
    status, reason, text, session = interpret(vendor, rc, timed_out, stdout, stderr, info)
    if text and status == "ok":
        write_text(rpath(folder, rnd, vendor, ".md"), text + "\n")
    elif text:
        write_text(rpath(folder, rnd, vendor, ".partial.md"), text + "\n")
    row.update({"rc": rc, "ended": stamp(now()), "seconds": seconds, "status": status, "reason": reason,
                "session_id": session, "stdout": out.as_posix(), "stderr": err.as_posix()})
    if status == "ok":
        row["format_warnings"] = format_warnings(rnd, agenda["mode"], text)
    if rnd == "judge":
        picked = read_json(folder / "judge.json") or {}
        row["independence"] = "independent" if vendor != orchestrator else "same-vendor"
        row["in_session"] = bool(picked.get("in_session")) and picked.get("vendor") == vendor
    write_json(meta_path, row)
    emit({"vendor": vendor, "round": rnd, "status": status, "reason": reason,
          "answer": rpath(folder, rnd, vendor, ".md").as_posix() if status == "ok" else None})
    return {"ok": 0, "absent": 3}.get(status, 4)


def do_submit(args):
    folder, agenda = load(args.id)
    rnd, vendor, orchestrator = args.round, args.vendor, agenda["orchestrator"]
    if vendor != orchestrator and not args.host_session:
        raise DebateError("submit registers the host's own seat (orchestrator %s) in-session; seat %s answers "
                          "through call, or from a live %s session with --host-session <its session id>"
                          % (orchestrator, vendor, DISPLAY[vendor]))
    if args.host_session and args.session and args.session != args.host_session:
        raise DebateError("--session and --host-session name different sessions; pass one id")
    if not args.host_session:
        check_plain_submit(agenda, vendor)
    picked = check_judge_seat(folder, agenda, vendor, require_pick=True) if rnd == "judge" else None
    if meta(folder, rnd, vendor).get("status") == "ok":
        raise DebateError("%s %s already answered; remove its files to redo" % (rnd, vendor))
    check_round_open(folder, rnd)
    row = meta(folder, rnd, vendor)
    if not row.get("inputs") or not rpath(folder, rnd, vendor, ".prompt.md").is_file():
        raise DebateError("no %s prompt for %s: run prompt first and answer that file" % (rnd, vendor))
    current = build_prompt(folder, agenda, rnd, vendor)[2]["inputs"]
    if current != row["inputs"]:
        raise DebateError("the answers behind the %s %s prompt changed since it was generated; "
                          "re-run prompt and answer the new file" % (rnd, vendor))
    text = read_input(args.file, "answer file").strip()
    if not text:
        raise DebateError("submitted answer is empty")
    session = args.host_session or args.session
    evidence = (prove_host_session(vendor, args.host_session, current["sha256"], text)
                if args.host_session else None)
    clash = session_conflict(folder, vendor, {session}) if session else None
    if clash:
        raise DebateError("session %s already answered the %s seat (%s) in this debate; one session cannot "
                          "answer for two vendors" % (clash[2], DISPLAY[clash[0]], clash[1]))
    lock = acquire_lock(folder, rnd, vendor)
    try:
        if vendor in QUOTA_GATED:  # the answering session spends this subscription: re-read its quota now
            quota = quota_seat(vendor)
            if quota["status"] == "ABSENT":
                row.update({"vendor": vendor, "round": rnd, "cli": "in-session", "short": quota.get("short"),
                            "readiness": {k: quota.get(k) for k in ("status", "reason", "short", "reset_kst")},
                            "host_session": args.host_session, "host_session_evidence": evidence})
                return settle(folder, rnd, vendor, row, "absent",
                              "quota: %s; the %s session answering in-session would spend purchased credit, so "
                              "nothing was registered" % (quota["reason"], DISPLAY[vendor]))
        write_text(rpath(folder, rnd, vendor, ".md"), text + "\n")
        moment = stamp(now())
        row.update({"vendor": vendor, "round": rnd, "cli": "in-session", "host_vendor": vendor == orchestrator,
                    "model": args.model or UNDECLARED, "model_declared": bool(args.model),
                    "effort": None, "argv": None, "rc": 0, "started": moment, "ended": moment,
                    "seconds": None, "status": "ok", "reason": "", "session_id": session,
                    "host_session": args.host_session, "host_session_evidence": evidence,
                    "source_file": Path(args.file).as_posix(), "answer_inputs": current,
                    "format_warnings": format_warnings(rnd, agenda["mode"], text)})
        row.setdefault("truncated", [])
        if rnd == "judge":  # independence is what judge-pick decided; the host's own vendor is never independent
            chosen = picked.get("independence")
            row["independence"] = ("same-vendor" if vendor == orchestrator
                                   else chosen if chosen in ("independent", "same-vendor") else "independent")
            row["in_session"] = True
        write_json(rpath(folder, rnd, vendor, ".meta.json"), row)
    finally:
        release_lock(lock)
    emit({"vendor": vendor, "round": rnd, "status": "ok", "format_warnings": row["format_warnings"]})
    return 0


# ---------------------------------------------------------------- status, record

def debate_status(folder, agenda):
    interject = agenda["mode"] == "interject"
    rounds = {}
    for rnd in ROUNDS:
        rows = {}
        for vendor in VENDORS:
            row = meta(folder, rnd, vendor)
            if row:
                rows[vendor] = {"status": row.get("status"), "reason": row.get("reason", ""),
                                "model": row.get("model"), "cli": row.get("cli")}
        rounds[rnd] = rows
    r1_ok = ok_vendors(folder, "r1")
    count = len(r1_ok)
    jv = judge_vendor(folder)
    jrow = meta(folder, "judge", jv) if jv else {}
    jtext = answer(folder, "judge", jv) if jv else None
    issues, verdict = [], None
    if jtext is not None:
        tag = "CALL" if interject else "VERDICT"
        parsed = call_of(jtext) if interject else tagged(jtext, "VERDICT")
        if not parsed:
            issues.append("judge answer has no %s: line" % tag)
        if jrow.get("positions_count") != count:
            issues.append("judge saw %s of %d positions; re-run the judge" % (jrow.get("positions_count", "?"), count))
        verdict = {"vendor": jv, "line": parsed or first_line(jtext),
                   "confidence": tagged(jtext, "CONFIDENCE"), "independence": jrow.get("independence")}
    judge_ok = jtext is not None and not issues
    seats = (read_json(folder / "seats.json") or {}).get("vendors", {})
    absent = []
    for vendor in VENDORS:
        if vendor in r1_ok:
            continue
        row = meta(folder, "r1", vendor)
        if row.get("status") in ("absent", "failed"):
            reason, short = row.get("reason", ""), row.get("short") or ""
        elif row.get("status") == "running":
            reason, short = "running (pid %s)" % row.get("pid"), "진행 중"
        else:
            seat = seats.get(vendor) or {}
            reason = "not called (seat %s: %s)" % (seat.get("status", "?"), seat.get("reason", ""))
            short = "미호출" if seat.get("status") in (None, "READY") else seat.get("short") or "미호출"
        absent.append({"vendor": vendor, "display": DISPLAY[vendor],
                       "status": row.get("status") or "not-called", "reason": reason, "short": short})
    reviews, kinds = {"ratify": {}, "catchup": {}}, {"ratify": {}, "catchup": {}}
    objections, unresolved = [], []
    for rnd in ("ratify", "catchup"):
        for vendor in ok_vendors(folder, rnd):
            kind, line = review_kind(answer(folder, rnd, vendor))
            kinds[rnd][vendor] = kind
            reviews[rnd][vendor] = line if kind else "?" + line[:60]
            item = {"vendor": vendor, "round": rnd, "text": reviews[rnd][vendor]}
            if kind == "OBJECT":
                objections.append(item)
            elif kind is None:
                unresolved.append(item)
    tiebreak = read_json(folder / "tiebreak.json")
    tiebreak = tiebreak if isinstance(tiebreak, dict) else None
    applies = bool(tiebreak) and len(objections) == 1 and tiebreak.get("objection") == {
        "vendor": objections[0]["vendor"], "round": objections[0]["round"]}
    blocked = bool(objections) and not applies
    joined = [v for v, k in kinds["catchup"].items()
              if v not in r1_ok and (k == "ACCEPT" or (applies and k == "OBJECT"))]
    via = None
    if count < 2:
        state = "INVALID"
    elif judge_ok and not blocked and not unresolved and count + len(joined) == 4:
        state, via = "FINAL", ("catch-up" if count < 4 else None)
    else:
        state = "PROVISIONAL"
    pending = [a["vendor"] for a in absent if a["vendor"] not in reviews["catchup"]]
    return {"id": agenda["id"], "title": agenda["title"], "mode": agenda["mode"],
            "orchestrator": agenda["orchestrator"], "state": state, "via": via, "attendance": count,
            "present": r1_ok, "judge": {"vendor": jv, "ok": judge_ok, "answered": jtext is not None,
                                        "issues": issues},
            "verdict": verdict, "rounds": rounds, "absent": absent,
            "catchup_pending": pending if state == "PROVISIONAL" else [],
            "ratify": reviews["ratify"], "catchup": reviews["catchup"], "objections": objections,
            "unresolved": unresolved, "tiebreak": tiebreak, "tiebreak_applies": applies,
            "blocked": blocked, "dir": folder.as_posix()}


def status_text(st):
    lines = ["%s  %s %d/4%s  (mode %s)  %s" % (st["id"], st["state"], st["attendance"],
                                                " via " + st["via"] if st["via"] else "", st["mode"],
                                                st["title"])]
    for rnd in ROUNDS:
        rows = st["rounds"][rnd]
        if rows:
            lines.append("  %-8s %s" % (rnd + ":", " · ".join(
                "%s %s" % (DISPLAY[v], rows[v]["status"]) for v in VENDORS if v in rows)))
    if st["verdict"]:
        lines.append("  verdict: %s (confidence %s, %s judge)" % (
            st["verdict"]["line"], st["verdict"]["confidence"], DISPLAY[st["verdict"]["vendor"]]))
    for issue in st["judge"]["issues"]:
        lines.append("  JUDGE INVALID: " + issue)
    for row in st["absent"]:
        if row["vendor"] in st["catchup"]:
            lines.append("  catch-up done: %s %s" % (row["display"], st["catchup"][row["vendor"]]))
        else:
            lines.append("  catch-up duty: %s (%s)" % (row["display"], row["reason"]))
    for row in st["objections"]:
        lines.append("  OBJECTION %s/%s: %s" % (row["round"], DISPLAY[row["vendor"]], row["text"]))
    for row in st["unresolved"]:
        lines.append("  UNREADABLE %s/%s: %s" % (row["round"], DISPLAY[row["vendor"]], row["text"]))
    if st["tiebreak"]:
        lines.append("  tiebreak%s: %s" % ("" if st["tiebreak_applies"] else " (stale)",
                                            st["tiebreak"].get("rationale")))
    return "\n".join(lines)


def next_d_number(path):
    numbers = [int(a or b) for a, b in D_HEADER_RE.findall(read_text(path))]
    return "D-%d" % (max(numbers) + 1 if numbers else 1)


def record_problem(st):
    if st["state"] == "INVALID":
        return "INVALID %d/4" % st["attendance"]
    if not st["judge"]["ok"]:
        return "심판 없음" if not st["judge"]["answered"] else "심판 판정 무효"
    return None


def render_record(folder, agenda, st, label, forced=None):
    mode, orchestrator = agenda["mode"], agenda["orchestrator"]
    moment = now().astimezone(KST).strftime("%Y-%m-%d %H:%M:%S KST")
    flags = ""
    if st["via"] == "catch-up":
        flags += " · catch-up 합류"
    if st["tiebreak_applies"]:
        flags += " · 타이브레이크"
    if agenda.get("reopen_of"):
        flags += " · 재개: " + agenda["reopen_of"]
    if forced:
        flags += " · ⚠ 강제 기록: " + forced
    lines = ["- %s | DECIDE | **%s %s** (§35 4벤더 토론 · %s %d/4%s) | %s" % (
        moment, label, agenda["title"], st["state"], st["attendance"], flags, AUTHOR[orchestrator])]
    question = agenda["question"]
    if agenda["options"]:
        question += " — 선택지: " + " / ".join("%d) %s" % (i, o) for i, o in enumerate(agenda["options"], 1))
    lines.append("  - **안건**: " + condense(question, 600))
    seats = []
    absent = {a["vendor"]: a for a in st["absent"]}
    for vendor in VENDORS:
        if vendor in st["present"]:
            row = meta(folder, "r1", vendor)
            detail = row.get("model") or DEFAULTS[vendor][0]
            if row.get("cli") == "in-session":
                detail += ", 세션 내"
            seats.append("%s ✓(%s)" % (DISPLAY[vendor], detail))
        else:
            row = absent[vendor]
            detail = row["short"] or condense(row["reason"], 80)
            if row["status"] == "failed":
                detail = "실패: " + condense(row["reason"], 80)
            seats.append("%s ✗(%s)" % (DISPLAY[vendor], detail))
    lines.append("  - **참석**: " + " · ".join(seats))
    stances = ["%s[%s]: %s" % (DISPLAY[v], LENS_SHORT.get(agenda["lenses"][v], agenda["lenses"][v]),
                               r1_stance(answer(folder, "r1", v), mode)) for v in st["present"]]
    lines.append("  - **입장**: " + (" · ".join(stances) if stances else "없음"))
    if mode != "full":
        cross = "%s 모드 생략" % mode
    else:
        parts = []
        for vendor in st["present"]:
            second = answer(folder, "r2", vendor)
            parts.append("%s %s" % (DISPLAY[vendor], condense(first_line(second), 120) if second else "미제출"))
        cross = " · ".join(parts) if parts else "미실행"
    lines.append("  - **교차검증**: " + cross)
    verdict = st["verdict"]
    if verdict:
        jrow = meta(folder, "judge", verdict["vendor"])
        how = ["블라인드", "새 세션"]
        if jrow.get("independence") == "same-vendor":
            how.append("동일 벤더")
        if jrow.get("cli") == "in-session":
            how.append("세션 내")
        if jrow.get("judge_wrote_position"):
            how.append("자기 벤더 입장 포함")
        tag = "CALL" if mode == "interject" else "VERDICT"
        judge = "%s (%s) — %s: %s · CONFIDENCE %s" % (
            DISPLAY[verdict["vendor"]], "·".join(how), tag, condense(verdict["line"], 200),
            condense(verdict["confidence"] or "?", 20))
        if not st["judge"]["ok"]:
            judge = "⚠ 무효(%s) " % "; ".join(st["judge"]["issues"]) + judge
        reviews = ["%s %s" % (DISPLAY[v], condense(t, 80)) for v, t in st["ratify"].items()]
        if reviews:
            judge += " · 추인: " + " · ".join(reviews)
        jtext = answer(folder, "judge", verdict["vendor"])
        minority = condense(section(jtext, "소수의견"), 300) or "없음"
        follow = condense(section(jtext, "후속") or section(jtext, "다음 한 걸음"), 300)
    else:
        judge, minority, follow = "미실행", "미실행(심판 전)", ""
    lines.append("  - **심판**: " + judge)
    if st["catchup"]:
        lines.append("  - **catch-up**: " + " · ".join(
            "%s %s" % (DISPLAY[v], condense(t, 120)) for v, t in st["catchup"].items()))
    if st["tiebreak"]:
        lines.append("  - **타이브레이크**: %s — %s%s" % (
            DISPLAY.get(st["tiebreak"].get("by"), "?"), condense(st["tiebreak"].get("rationale"), 400),
            "" if st["tiebreak_applies"] else " (반대 건수가 바뀌어 무효)"))
    lines.append("  - **소수의견**: " + minority)
    duties = []
    if st["state"] == "PROVISIONAL" and st["catchup_pending"]:
        names = "·".join(DISPLAY[v] for v in st["catchup_pending"])
        duties.append("%s 복귀 시 catchup 라운드 의무 (`debate.py catchup`)" % names)
    if st["blocked"]:
        if len(st["objections"]) == 1:
            duties.append("OBJECT 1건: 타이브레이크(`record --tiebreak`) 전 확정 금지")
        else:
            duties.append("OBJECT %d건: `new --reopen-of %s`로 재토론" % (len(st["objections"]), agenda["id"]))
    if st["unresolved"]:
        duties.append("판독 불가 응답 %d건(ACCEPT/OBJECT 아님): 다시 받기 전 확정 금지" % len(st["unresolved"]))
    if st["state"] == "INVALID":
        duties.append("참석 2벤더 미만: §35 결정 게이트로 쓸 수 없음")
    follow_text = " · ".join(x for x in [follow] + duties if x) or "없음"
    lines.append("  - **후속**: " + follow_text)
    lines.append("  - **원문**: " + folder.as_posix())
    return "\n".join(lines) + "\n"


def snapshot(st):
    return {"state": st["state"], "attendance": st["attendance"], "ratify": st["ratify"],
            "catchup": st["catchup"], "verdict": (st["verdict"] or {}).get("line"),
            "tiebreak": (st["tiebreak"] or {}).get("rationale") if st["tiebreak_applies"] else None}


def render_amend(agenda, st, label, before):
    parts = []
    if st["catchup"] and st["catchup"] != before.get("catchup"):
        parts.append("catch-up: " + " · ".join("%s %s" % (DISPLAY[v], condense(t, 120))
                                               for v, t in st["catchup"].items()))
    if st["ratify"] != before.get("ratify"):
        parts.append("추인: " + (" · ".join("%s %s" % (DISPLAY[v], condense(t, 120))
                                            for v, t in st["ratify"].items()) or "없음"))
    current = snapshot(st)
    if current["tiebreak"] and current["tiebreak"] != before.get("tiebreak"):
        parts.append("타이브레이크(%s): %s" % (DISPLAY.get(st["tiebreak"].get("by"), "?"),
                                          condense(current["tiebreak"], 300)))
    if current["verdict"] != before.get("verdict"):
        parts.append("판정: %s" % condense(current["verdict"] or "없음", 200))
    state = "상태 %s %d/4" % (st["state"], st["attendance"])
    if st["via"]:
        state += " (%s)" % st["via"]
    if st["blocked"]:
        state += " · 차단(OBJECT %d건)" % len(st["objections"])
    if st["unresolved"]:
        state += " · 판독 불가 %d건" % len(st["unresolved"])
    parts.append(state)
    moment = now().astimezone(KST).strftime("%Y-%m-%d %H:%M:%S KST")
    return "- %s | AMEND | **%s %s** — %s | %s\n" % (moment, label, agenda["title"],
                                                     condense(" · ".join(parts), 900),
                                                     AUTHOR[agenda["orchestrator"]])


def append_entry(target, entry):
    before = target.read_bytes()
    newline = b"\r\n" if b"\r\n" in before else b"\n"
    prefix = b""
    if before and not before.endswith(b"\n"):
        prefix += newline
    if before and not (before + prefix).endswith(newline + newline):
        prefix += newline
    payload = prefix + entry.encode("utf-8").replace(b"\n", newline)
    with open(target, "ab") as stream:
        stream.write(payload)
    if not target.read_bytes().startswith(before):
        raise DebateError("append verification failed: existing bytes changed", 4)


def set_tiebreak(folder, agenda, rationale):
    rationale = condense(rationale, 600)
    if not rationale:
        raise DebateError("--tiebreak needs a written rationale")
    if (folder / "tiebreak.json").exists():
        raise DebateError("a tiebreak is already recorded for %s" % agenda["id"])
    st = debate_status(folder, agenda)
    if len(st["objections"]) != 1:
        raise DebateError("a tiebreak resolves exactly one OBJECT (have %d); with 2 or more, reopen with "
                          "new --reopen-of %s" % (len(st["objections"]), agenda["id"]))
    target = st["objections"][0]
    write_json(folder / "tiebreak.json", {"rationale": rationale, "by": agenda["orchestrator"],
                                          "at": stamp(now()),
                                          "objection": {"vendor": target["vendor"], "round": target["round"]}})


def do_record(args):
    folder, agenda = load(args.id)
    problem = record_problem(debate_status(folder, agenda))
    if problem and not args.force:
        raise DebateError("record refuses a debate with %s; pass --force to record it marked as forced"
                          % problem)
    if args.tiebreak is not None:
        set_tiebreak(folder, agenda, args.tiebreak)
    st = debate_status(folder, agenda)
    problem = record_problem(st)
    saved = read_json(folder / "record.json")
    saved = saved if isinstance(saved, dict) and saved.get("label") else None
    if args.amend:
        return amend_record(args, folder, agenda, st, saved)
    target = Path(args.decisions) if args.decisions else None
    if target:
        if not target.is_file():
            raise DebateError("decisions file not found: %s" % target.as_posix())
    elif args.append:
        raise DebateError("--append needs --decisions PATH")
    if args.append and saved:
        raise DebateError("%s is already recorded as %s in %s; use --amend to append an AMEND line"
                          % (agenda["id"], saved["label"], saved.get("decisions_path")))
    label = saved["label"] if saved else (next_d_number(target) if target else "D-??")
    entry = render_record(folder, agenda, st, label, problem)
    write_text(folder / "record.md", entry)
    if args.append:
        append_entry(target, entry)
        write_json(folder / "record.json", {"label": label, "decisions_path": target.resolve().as_posix(),
                                            "appended_at": stamp(now()), "forced": problem,
                                            "snapshot": snapshot(st), "amends": []})
    print(entry, end="")
    if args.append:
        print("(appended %s to %s)" % (label, target.as_posix()))
    return 0


def amend_record(args, folder, agenda, st, saved):
    if not saved:
        raise DebateError("nothing recorded for %s yet: run record --decisions PATH --append first"
                          % agenda["id"])
    target = Path(saved["decisions_path"])
    if args.decisions and Path(args.decisions).resolve() != target.resolve():
        raise DebateError("%s was recorded in %s, not %s" % (saved["label"], target.as_posix(),
                                                             Path(args.decisions).as_posix()))
    if not target.is_file():
        raise DebateError("decisions file not found: %s" % target.as_posix())
    current = snapshot(st)
    if current == saved.get("snapshot"):
        raise DebateError("nothing changed since %s was last recorded" % saved["label"])
    line = render_amend(agenda, st, saved["label"], saved.get("snapshot") or {})
    append_entry(target, line)
    saved["snapshot"] = current
    saved.setdefault("amends", []).append({"appended_at": stamp(now()), "line": line.strip()})
    write_json(folder / "record.json", saved)
    print(line, end="")
    print("(appended AMEND for %s to %s)" % (saved["label"], target.as_posix()))
    return 0


# ---------------------------------------------------------------- commands

def do_seats(args):
    require_orchestrator(args.orchestrator)
    seats = compute_seats(args.orchestrator, probe=not args.no_probe)
    seats["summary"] = seat_summary(seats["vendors"])
    if args.json:
        emit(seats)
        return 0
    print("seats checked %s (orchestrator %s)" % (seats["checked_at"], DISPLAY[args.orchestrator]))
    for vendor in VENDORS:
        row = seats["vendors"][vendor]
        print("  %-7s %-8s %s" % (row["display"], row["status"], row["reason"]))
    print(seats["summary"])
    return 0


def record_evidence(evidence, record):
    """Prior evidence plus the prior record, condensed to the evidence cap."""
    block = "\n\n## 이전 토론 기록\n" + clip_bytes(record, RECORD_EVIDENCE_CAP)
    room = EVIDENCE_CAP - len(block.encode("utf-8"))
    if len(evidence.encode("utf-8")) > room:
        marker = "\n[... 근거 자료 일부 생략]"
        evidence = clip_bytes(evidence, room - len(marker.encode("utf-8"))) + marker
    return (evidence + block).strip()


def do_new(args):
    require_orchestrator(args.orchestrator)
    markers = check_host(args.orchestrator, args.orchestrator_override)
    prior = None
    if args.reopen_of:
        prior = load(args.reopen_of)
    base = prior[1] if prior else {}
    title = clean_item(args.title if args.title is not None else base.get("title"))
    if not title or len(title) > 200:
        raise DebateError("--title must be one line of 1-200 characters")
    raw_question = args.question if args.question is not None else base.get("question") or ""
    question = "\n".join(clean_item(x) for x in raw_question.splitlines()).strip()
    if not question:
        raise DebateError("--question is required")
    if len(question) > QUESTION_CAP:
        raise DebateError("--question is %d characters (> %d); move detail into --evidence-file"
                          % (len(question), QUESTION_CAP))
    options = [clean_item(o) for o in (args.option if args.option else base.get("options") or [])]
    criteria = [clean_item(c) for c in (args.criterion if args.criterion else base.get("criteria") or [])]
    options, criteria = [o for o in options if o], [c for c in criteria if c]
    for flag, items in (("--option", options), ("--criterion", criteria)):
        if len(items) > ITEM_COUNT:
            raise DebateError("at most %d %s values (got %d)" % (ITEM_COUNT, flag, len(items)))
        for item in items:
            if len(item) > ITEM_CAP:
                raise DebateError("%s is %d characters (> %d): %s…" % (flag, len(item), ITEM_CAP, item[:40]))
    mode = args.mode or base.get("mode") or "quick"
    subject = args.subject_vendor or (base.get("subject_vendor") if prior else None)
    if subject and mode != "interject":
        raise DebateError("--subject-vendor applies to --mode interject only")
    evidence, evidence_file = "", None
    if args.evidence_file:
        evidence = read_input(args.evidence_file, "evidence file").strip()
        evidence_file = Path(args.evidence_file).resolve().as_posix()
    elif prior:
        evidence = base.get("evidence") or ""
    evidence, redacted = redact(evidence)
    if prior:
        pfolder, pagenda = prior
        saved = read_json(pfolder / "record.json") or {}
        record, more = redact(render_record(pfolder, pagenda, debate_status(pfolder, pagenda),
                                            saved.get("label") or "D-??"))
        evidence, redacted = record_evidence(evidence, record), redacted + more
    size = len(evidence.encode("utf-8"))
    if size > EVIDENCE_CAP:
        raise DebateError("evidence is %d UTF-8 bytes (> %d); condense it first" % (size, EVIDENCE_CAP))
    debate_id = check_id(args.id if args.id is not None
                         else "dbt-" + now().astimezone(KST).strftime("%y%m%d-%H%M%S"))
    folder = debate_dir(debate_id)
    if (folder / "agenda.json").exists():
        raise DebateError("debate %s already exists" % debate_id)
    lenses = lenses_for(debate_id)
    agenda = {"id": debate_id, "title": title, "question": question, "options": options,
              "criteria": criteria, "evidence": evidence, "evidence_file": evidence_file,
              "redacted": redacted, "mode": mode, "orchestrator": args.orchestrator,
              "subject_vendor": subject, "reopen_of": prior[1]["id"] if prior else None,
              "created_at": stamp(now()), "lenses": lenses, "host_env": markers,
              "orchestrator_override": bool(args.orchestrator_override)}
    (folder / "rounds").mkdir(parents=True, exist_ok=True)
    write_json(folder / "agenda.json", agenda)
    seats = compute_seats(args.orchestrator, probe=not args.no_probe)
    write_json(folder / "seats.json", seats)
    emit({"id": debate_id, "dir": folder.as_posix(), "mode": mode, "lenses": lenses, "redacted": redacted,
          "seats": {v: {k: r.get(k) for k in ("status", "reason", "short", "reset_kst")}
                    for v, r in seats["vendors"].items()},
          "summary": seat_summary(seats["vendors"])})
    return 0


def do_prompt(args):
    folder, agenda = load(args.id)
    targets = [args.vendor] if args.vendor else default_vendors(folder, agenda, args.round)
    written, skipped = [], []
    for vendor in targets:
        if meta(folder, args.round, vendor).get("status") == "ok":
            if args.vendor:
                raise DebateError("%s %s already answered" % (args.round, vendor))
            skipped.append({"vendor": vendor, "reason": "already answered"})
            continue
        written.append(write_prompt(folder, agenda, args.round, vendor))
    emit({"id": agenda["id"], "round": args.round, "prompts": written, "skipped": skipped})
    return 0


def do_judge_pick(args):
    folder, agenda = load(args.id)
    orchestrator, subject = agenda["orchestrator"], agenda.get("subject_vendor")
    seats = compute_seats(orchestrator, probe=not args.no_probe)["vendors"]
    offset = int(order_key(agenda["id"], "judge")[:8], 16) % 4
    order = [VENDORS[(i + offset) % 4] for i in range(4)]
    spent = {v for v in VENDORS for rnd in ROUNDS if meta(folder, rnd, v).get("status") == "absent"
             and not str(meta(folder, rnd, v).get("reason", "")).startswith("UNKNOWN:")}
    eligible = [v for v in order if v not in (orchestrator, subject) and v not in spent
                and not seats[v].get("shim")]
    candidates = [v for v in eligible if seats[v]["status"] == "READY"]
    if args.accept_unknown:
        candidates += [v for v in eligible if seats[v]["status"] == "UNKNOWN"]
    if candidates:
        vendor, independence, in_session = candidates[0], "independent", False
    else:  # the host's own vendor judges in-session, in a fresh subagent where the host has one
        vendor, independence, in_session = orchestrator, "same-vendor", True
    result = {"vendor": vendor, "independence": independence, "in_session": in_session}
    write_json(folder / "judge.json", dict(result, picked_at=stamp(now()), order=order,
                                           candidates=candidates, subject_vendor=subject,
                                           accept_unknown=bool(args.accept_unknown),
                                           seats={v: seats[v]["status"] for v in VENDORS}))
    emit(result)
    return 0


def do_status(args):
    folder, agenda = load(args.id)
    st = debate_status(folder, agenda)
    if args.json:
        emit(st)
    else:
        print(status_text(st))
    return 0


def all_debates():
    root = state_root() / "debates"
    if not root.is_dir():
        return []
    rows = []
    for folder in sorted(root.iterdir()):
        agenda = read_json(folder / "agenda.json")
        if isinstance(agenda, dict) and agenda.get("id") == folder.name:
            rows.append((folder, agenda))
    return rows


def do_catchup(args):
    """Returned seats of PROVISIONAL debates, judged from the CLI running catchup now (--orchestrator).

    A plain submit is offered only when this CLI is that vendor and the debate's own host. Any other seat is
    reached by `call` (when the stored host can spawn it) or by a live session of that vendor proving itself
    with --host-session, and never when that vendor's quota evidence says it is spent."""
    host = require_orchestrator(args.orchestrator)
    check_host(host, args.orchestrator_override)
    seats, quotas, ready, waiting = {}, {}, [], []
    script = 'python -B "%s"' % SCRIPT.as_posix()
    probe = not args.no_probe
    for folder, agenda in all_debates():
        st = debate_status(folder, agenda)
        if st["state"] != "PROVISIONAL" or not st["catchup_pending"]:
            continue
        stored = agenda["orchestrator"]
        for vendor in st["catchup_pending"]:
            key = (vendor, stored)
            if key not in seats:
                seats[key] = seat_for(vendor, stored, probe=probe)
            seat = seats[key]
            if vendor not in quotas:  # reuse a CLI seat's own quota reading; else read the evidence directly
                quotas[vendor] = seat if vendor != stored and seat.get("cli") else quota_seat(vendor, probe)
            quota = quotas[vendor]
            own = vendor == host == stored
            item = {"id": agenda["id"], "title": agenda["title"], "vendor": vendor,
                    "display": DISPLAY[vendor], "readiness": seat["status"], "reason": seat["reason"],
                    "judge_ok": st["judge"]["ok"], "debate_orchestrator": stored, "current_host": host}
            if vendor == stored and not own:
                item["readiness"] = "ABSENT" if quota["status"] == "ABSENT" else "HOST_SESSION"
                item["reason"] = (quota["reason"] if quota["status"] == "ABSENT" else
                                  "the debate host's own seat (orchestrator %s) and the current host is %s: only "
                                  "a live %s session can answer it (--host-session)"
                                  % (stored, host, DISPLAY[vendor]))
            base = "%s %%s --id %s --round catchup --vendor %s" % (script, agenda["id"], vendor)
            if (folder / "record.json").is_file():
                item["then"] = "%s record --id %s --amend" % (script, agenda["id"])
            if not st["judge"]["ok"]:
                item["note"] = "judge pending: run judge-pick and the judge round first"
                waiting.append(item)
                continue
            if not own and quota["status"] != "ABSENT":
                item["host_session_commands"] = [
                    base % "prompt",
                    base % "submit" + " --host-session <that live %s session's id> --file <answer .md>"
                    % DISPLAY[vendor]]
            if own and seat["status"] == "READY":
                item["commands"] = [base % "prompt", base % "submit" + " --file <in-session answer .md>"]
                ready.append(item)
            elif vendor != stored and seat["status"] == "READY":
                item["commands"] = [base % "prompt", base % "call"]
                ready.append(item)
            else:
                waiting.append(item)
    result = {"checked_at": stamp(now()), "host": host, "ready": ready, "waiting": waiting}
    if args.json:
        emit(result)
        return 0
    if not ready:
        print("no PROVISIONAL debate has a returned vendor yet (%d waiting)" % len(waiting))
    for item in ready:
        print("%s  %s is READY for catch-up (%s)" % (item["id"], item["display"], item["reason"]))
        for command in item["commands"] + ([item["then"]] if item.get("then") else []):
            print("    " + command)
    for item in waiting:
        if item.get("host_session_commands"):
            who = ("this %s session (its own session id)" % item["display"] if item["vendor"] == host
                   else "a live %s session" % item["display"])
            print("%s  %s seat is %s; %s can catch up in-session:" % (
                item["id"], item["display"], item["readiness"], who))
            for command in item["host_session_commands"] + ([item["then"]] if item.get("then") else []):
                print("    " + command)
    return 0


def do_deliver(args):
    folder, agenda = load(args.id)
    if agenda["mode"] != "interject":
        raise DebateError("deliver works on interject debates only")
    terminal = args.orca_terminal
    if terminal is not None and (not terminal.strip() or CTRL_RE.search(terminal)):
        raise DebateError("--orca-terminal must be a plain handle")
    if args.send and not terminal:
        raise DebateError("--send needs --orca-terminal HANDLE")
    st = debate_status(folder, agenda)
    jv = st["judge"]["vendor"]
    text = answer(folder, "judge", jv) if st["judge"]["ok"] else None
    if not text:
        raise DebateError("no completed interject judge answer to deliver")
    call = call_of(text) or "?"
    confidence = condense(tagged(text, "CONFIDENCE") or "?", 20)
    step = condense(section(text, "다음 한 걸음"), 220) or "?"
    cut = condense(section(text, "지금 자를 것"), 220) or "없음"
    box = condense(section(text, "시간 상자"), 40) or "?"
    if re.fullmatch(r"\d+", box):
        box += "분"
    calls = {v: call_of(answer(folder, "r1", v)) for v in st["present"]}
    stops = sum(1 for c in calls.values() if c == "STOP")
    seats = " · ".join("%s %s" % (DISPLAY[v], "✓" if v in st["present"] else "✗") for v in VENDORS)
    votes = " · ".join("%s %s" % (DISPLAY[v], calls[v] or "?") for v in st["present"])
    card = ["# 겐세이 %s" % agenda["id"], "CALL: %s (확신도 %s)" % (call, confidence)]
    if stops >= 3:
        card.append("⚠ STOP %d/%d — Simon에게 일시정지 권고" % (stops, len(st["present"])))
    card += ["위원 권고: " + (votes or "-"),
             "다음 한 걸음: " + step,
             "자를 것: " + cut,
             "시간 상자: " + box,
             "참석: %s (%s %d/4)" % (seats, st["state"], st["attendance"]),
             "심판: %s (%s)" % (DISPLAY[jv], meta(folder, "judge", jv).get("independence") or "?"),
             "근거: " + (condense(section(text, "판정 근거"), 220) or "-"),
             "전문: " + rpath(folder, "judge", jv, ".md").as_posix()]
    card = [CTRL_RE.sub("", line) for line in card]
    card_path = folder / "card.md"
    write_text(card_path, "\n".join(card) + "\n")
    message = condense("[겐세이 %s] %s: %s — 전문: %s" % (agenda["id"], call, step, card_path.as_posix()), 500)
    orca = resolve_cmd("orca")
    argv = (orca or ["orca"]) + ["terminal", "send", "--terminal", terminal or "<HANDLE>",
                                 "--text", message, "--enter", "--json"]
    refused = None
    if orca and is_shim(orca):
        refused = ("shim refused: %s is a .cmd/.bat shim and cmd.exe would re-parse the card text; "
                   "point PATH or AI_DEBATE_CMD_ORCA at orca.exe" % Path(orca[0]).name)
    if not args.send:
        result = {"dry_run": True, "card": card_path.as_posix(), "lines": len(card), "argv": argv}
        if refused:
            result["refused"] = refused
        emit(result)
        return 0
    if not orca:
        raise DebateError("orca CLI not found")
    if refused:
        write_json(folder / "deliver.json", {"sent_at": None, "status": "failed", "reason": refused,
                                             "terminal": terminal, "card": card_path.as_posix()})
        emit({"status": "failed", "reason": refused, "card": card_path.as_posix()})
        return 4
    out, err = folder / "deliver.stdout.txt", folder / "deliver.stderr.txt"
    work = fresh_workdir(agenda["id"], "deliver")
    rc, timed_out, seconds = run_process(argv, work, child_env("orca"), 60, out, err)
    result = {"sent_at": stamp(now()), "status": "ok" if rc == 0 and not timed_out else "failed",
              "terminal": terminal, "argv": argv, "rc": rc, "timed_out": timed_out, "seconds": seconds,
              "stdout": read_text(out)[:4000], "stderr": read_text(err)[:2000], "card": card_path.as_posix()}
    write_json(folder / "deliver.json", result)
    emit({k: result[k] for k in ("sent_at", "terminal", "rc", "timed_out", "card")})
    return 0 if rc == 0 and not timed_out else 4


def parser():
    top = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = top.add_subparsers(dest="command", required=True)
    host_help = "required: the vendor of the CLI running this debate (%s)" % HOST_TABLE
    override_help = ("accept --orchestrator although this shell's host variables name another CLI "
                     "(they were inherited); recorded in agenda.json")
    p = sub.add_parser("seats", help="vendor readiness without model calls")
    p.add_argument("--json", action="store_true")
    p.add_argument("--orchestrator", choices=VENDORS, help=host_help)
    p.add_argument("--no-probe", action="store_true")
    p = sub.add_parser("new", help="open a debate")
    p.add_argument("--title", help="required unless --reopen-of")
    p.add_argument("--question", help="required unless --reopen-of")
    p.add_argument("--option", action="append")
    p.add_argument("--criterion", action="append")
    p.add_argument("--evidence-file")
    p.add_argument("--orchestrator", choices=VENDORS, help=host_help)
    p.add_argument("--orchestrator-override", action="store_true", help=override_help)
    p.add_argument("--mode", choices=MODES, help="default quick (or the reopened debate's mode)")
    p.add_argument("--subject-vendor", choices=VENDORS, help="interject: the stuck agent's vendor")
    p.add_argument("--reopen-of", metavar="ID", help="copy that debate's agenda and attach its record")
    p.add_argument("--id")
    p.add_argument("--no-probe", action="store_true")
    p = sub.add_parser("prompt", help="write prompt files for a round")
    p.add_argument("--id", required=True)
    p.add_argument("--round", choices=ROUNDS, required=True)
    p.add_argument("--vendor", choices=VENDORS)
    p = sub.add_parser("judge-pick", help="choose the judge vendor")
    p.add_argument("--id", required=True)
    p.add_argument("--no-probe", action="store_true")
    p.add_argument("--accept-unknown", action="store_true")
    p = sub.add_parser("call", help="run one vendor CLI for one round")
    p.add_argument("--id", required=True)
    p.add_argument("--round", choices=ROUNDS, required=True)
    p.add_argument("--vendor", choices=VENDORS, required=True)
    p.add_argument("--model")
    p.add_argument("--effort")
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--accept-unknown", action="store_true")
    p = sub.add_parser("submit", help="register an in-session answer (the host's seat, or --host-session)")
    p.add_argument("--id", required=True)
    p.add_argument("--round", choices=ROUNDS, required=True)
    p.add_argument("--vendor", choices=VENDORS, required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--model")
    p.add_argument("--session", help="label of the answering session (not verified)")
    p.add_argument("--host-session", metavar="ID",
                   help="id of a live interactive session of --vendor on this machine; required when --vendor "
                        "is not the orchestrator, verified from its local transcript")
    p = sub.add_parser("status", help="attendance and debate state")
    p.add_argument("--id", required=True)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("record", help="render or append the hub DECISIONS.md entry")
    p.add_argument("--id", required=True)
    p.add_argument("--decisions")
    p.add_argument("--append", action="store_true")
    p.add_argument("--amend", action="store_true", help="append one AMEND line after catch-up or tiebreak")
    p.add_argument("--tiebreak", metavar="RATIONALE", help="resolve a single OBJECT with a written rationale")
    p.add_argument("--force", action="store_true", help="record an INVALID or judge-less debate, marked")
    p = sub.add_parser("catchup", help="PROVISIONAL debates whose absent vendor is back")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-probe", action="store_true")
    p.add_argument("--orchestrator", choices=VENDORS, help="required: the vendor of the CLI running catchup "
                                                            "now (%s)" % HOST_TABLE)
    p.add_argument("--orchestrator-override", action="store_true", help=override_help)
    p = sub.add_parser("deliver", help="hand the interject card to the running agent")
    p.add_argument("--id", required=True)
    p.add_argument("--orca-terminal")
    p.add_argument("--send", action="store_true")
    return top


HANDLERS = {"seats": do_seats, "new": do_new, "prompt": do_prompt, "judge-pick": do_judge_pick,
            "call": do_call, "submit": do_submit, "status": do_status, "record": do_record,
            "catchup": do_catchup, "deliver": do_deliver}


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        return HANDLERS[args.command](args)
    except DebateError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
