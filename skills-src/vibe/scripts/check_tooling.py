# -*- coding: utf-8 -*-
"""툴체인 최신화 점검 - /vibe 프리플라이트 0-A 단계.

왜 있는가 (2026-09-12 사고):
    워커 3개가 전부 `agent_prompt_blocked` 로 안 떴다. 프롬프트 내용 탓인 줄 알고
    스펙을 두 번 다시 썼는데 아니었다. 진짜 원인은 **codex CLI 가 업데이트 안내를
    띄워 기동 자체가 막힌 것**이었다 - 최소 프롬프트로 갈라보니 에러 문구가
    `Agent startup blocked: codex-update-prompt` 로 바뀌면서 드러났다.
    codex-cli 0.153.4 설치 / 0.154.0 최신. 올리니 세 워커가 바로 떴다.

    즉 **툴이 한 버전 뒤처지면 파이프라인이 통째로 멈추는데, 에러 문구가
    내용 문제처럼 보인다.** 그래서 디스패치 전에 여기서 먼저 본다.

무엇을 보는가:
    - codex CLI      설치본 vs npm 최신
    - --local-codex   PATH 실행본 vs 인접 npm 패키지 (네트워크·Orca 없음)
    - orca CLI       설치본 (+ 있으면 최신)
    - orca skills    목록 스냅샷 대비 추가/삭제/설명 변경
    - claude/agy/grok  버전 (있으면)

원칙:
    - **자동 설치하지 않는다.** 보고만 하고, 올릴지는 사람이 정한다
      (전역 npm 패키지는 같은 머신의 다른 세션에 영향을 준다).
    - 읽기 실패는 "미확인"이다. "최신"으로 간주하지 않는다.
      (쿼터 규칙과 같은 규율 - 구분되는 상태를 같은 신호로 보고하지 않는다.)
"""
import contextlib
import errno
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UNKNOWN = "미확인"


def _snapshot_path():
    """Keep mutable Orca state outside the versioned, receipt-verified skill."""
    base = (os.environ.get("LOCALAPPDATA") if os.name == "nt" else
            os.environ.get("XDG_STATE_HOME") or
            os.path.join(os.path.expanduser("~"), ".local", "state"))
    if not base or not os.path.isabs(base):
        raise OSError("사용자 상태 폴더를 확인할 수 없다")
    path = os.path.realpath(os.path.join(base, "SimonKStack", "vibe", "orca-skills.json"))
    skill = os.path.realpath(SKILL_ROOT)
    try:
        if os.path.commonpath((os.path.normcase(path), os.path.normcase(skill))) == os.path.normcase(skill):
            raise OSError("스킬 패키지 안에는 상태를 기록할 수 없다")
    except ValueError:  # different Windows drives cannot have a common path
        pass
    return path


def _read_snapshot(path):
    if os.path.islink(path) or os.path.getsize(path) > 65536:
        raise ValueError("스냅샷이 링크이거나 너무 크다")
    with open(path, "r", encoding="utf-8") as source:
        doc = json.load(source)
    if (not isinstance(doc, dict) or not isinstance(doc.get("skills"), dict)
            or not all(isinstance(k, str) and isinstance(v, str)
                       for k, v in doc["skills"].items())
            or not isinstance(doc.get("pending", {}), dict)):
        raise ValueError("스냅샷 형식이 잘못됐다")
    pending = doc.get("pending") or {}
    if pending and (not isinstance(pending.get("first_seen"), str)
                    or not isinstance(pending.get("seen_count"), int)
                    or ("generation" in pending and
                        (not isinstance(pending["generation"], str) or
                         not re.fullmatch(r"[a-f0-9]{32}", pending["generation"])))
                    or any(not isinstance(pending.get(key), list)
                           or not all(isinstance(item, str) for item in pending[key])
                           for key in ("added", "removed", "changed"))):
        raise ValueError("미확인 변경 형식이 잘못됐다")
    return doc


@contextlib.contextmanager
def _snapshot_lock(path):
    """Serialize report/ack across Claude and Codex without stale lock owners."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    lock_path = path + ".lock"
    if os.path.islink(lock_path):
        raise OSError("상태 잠금 파일이 링크다")
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(lock_path, flags, 0o600)
    locked = False
    try:
        deadline = time.monotonic() + 5
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
                break
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN):
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError("상태 잠금을 5초 내 얻지 못했다") from exc
                time.sleep(0.05)
        yield
    finally:
        try:
            if locked:
                if os.name == "nt":
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _pending_digest(doc):
    """Stable review token: repeat sightings alone do not invalidate review."""
    pending = doc.get("pending") or {}
    if not pending:
        return None
    if not isinstance(pending.get("generation"), str):
        raise ValueError("기존 미확인 변경은 새 보고로 확인 토큰을 받아야 한다")
    reviewed = {"skills": doc["skills"],
                "pending": {key: pending[key] for key in
                            ("generation", "first_seen", "added", "removed", "changed")}}
    payload = json.dumps(reviewed, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _resolve(argv):
    """Windows 에서 npm 전역 셔임(`codex`, `npm`)은 .cmd 다.

    shell=False 로는 CreateProcess 가 .cmd 를 못 띄운다 - 첫 판에서 codex 가
    '미확인'으로 나온 원인이 이것이었다(설치돼 있는데 못 읽었다). 셸 문자열을
    만들지 않고 argv 배열 그대로 `cmd /c <경로>` 로 감싼다.
    """
    exe = shutil.which(argv[0])
    if exe and os.path.splitext(exe)[1].lower() in (".cmd", ".bat"):
        return ["cmd", "/c", exe] + list(argv[1:])
    return ([exe] + list(argv[1:])) if exe else list(argv)


def _run(argv, timeout=60):
    """(rc, stdout, stderr). 실행 자체가 불가능하면 rc=None."""
    try:
        p = subprocess.run(_resolve(argv), capture_output=True, text=True,
                           timeout=timeout, shell=False,
                           encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except FileNotFoundError:
        return None, "", "not found"
    except subprocess.TimeoutExpired:
        return None, "", "timeout"
    except Exception as e:  # noqa: BLE001
        return None, "", str(e)


def _version(argv):
    rc, out, err = _run(argv)
    if rc != 0:
        return None, err or out
    text = out or err
    m = re.search(r"(\d+\.\d+\.\d+(?:[-.\w]+)?)", text)
    return (m.group(1) if m else None), text.splitlines()[0][:80] if text else ""


def _npm_latest(pkg):
    rc, out, err = _run(["npm", "view", pkg, "version"], timeout=90)
    if rc != 0 or not out:
        return None
    m = re.search(r"(\d+\.\d+\.\d+(?:[-.\w]+)?)", out)
    return m.group(1) if m else None


def _cmp(a, b):
    """a < b 면 -1. 비교 불가면 None."""
    if not (isinstance(a, str) and isinstance(b, str)
            and re.fullmatch(r"\d+\.\d+\.\d+", a)
            and re.fullmatch(r"\d+\.\d+\.\d+", b)):
        return None
    pa, pb = tuple(map(int, a.split("."))), tuple(map(int, b.split(".")))
    return (pa > pb) - (pa < pb)


def _local_codex_package_version():
    """Read only the npm package adjacent to the resolved PATH shim, if any."""
    shim = shutil.which("codex")
    if not shim:
        return None
    package = os.path.join(os.path.dirname(shim), "node_modules", "@openai",
                           "codex", "package.json")
    try:
        if os.path.islink(package) or os.path.getsize(package) > 65536:
            return None
        with open(package, "r", encoding="utf-8") as source:
            doc = json.load(source)
    except (OSError, UnicodeError, ValueError):
        return None
    version = (doc.get("version") if isinstance(doc, dict)
               and doc.get("name") == "@openai/codex" else None)
    if isinstance(version, str) and re.fullmatch(r"\d+\.\d+\.\d+", version):
        return version
    return None


def check_codex_local():
    """Detect a stale PATH shim without npm registry or Orca access."""
    installed, _ = _version(["codex", "--version"])
    local_package = _local_codex_package_version()
    comparison = _cmp(installed, local_package)
    state = ("뒤처짐" if comparison is not None and comparison < 0 else
             "로컬 이상" if comparison is not None else
             "설치본만 확인" if installed else UNKNOWN)
    return {"tool": "codex", "installed": installed,
            "local_package": local_package, "state": state}


def check_clis():
    rows = []

    local_codex = check_codex_local()
    cur = local_codex["installed"]
    latest = _npm_latest("@openai/codex")
    codex_row = _row("codex", cur, latest,
                     "뒤처지면 `Agent startup blocked: codex-update-prompt` 로 "
                     "**모든 codex 워커가 안 뜬다**. 2026-09-12 실사고.",
                     "npm install -g @openai/codex@latest")
    codex_row["local_package"] = local_codex["local_package"]
    if local_codex["state"] == "뒤처짐":
        codex_row["state"] = "뒤처짐"
        codex_row["fix"] = "PATH shim을 확인하고 검증된 로컬 Codex 실행 경로를 사용"
    rows.append(codex_row)

    cur, _ = _version(["orca", "--version"])
    rows.append(_row("orca", cur, None,
                     "worker-start·orchestration 의 주체. effort 허용목록이 앱에 "
                     "하드코딩돼 있어 버전이 표와 어긋날 수 있다.", None))

    for name, argv, pkg in (("claude", ["claude", "--version"], None),
                            ("agy", ["agy", "--version"], None),
                            ("grok", ["grok", "--version"], None)):
        cur, _ = _version(argv)
        rows.append(_row(name, cur, _npm_latest(pkg) if pkg else None, "", None))
    return rows


def _row(name, cur, latest, why, fix):
    if cur is None:
        state = UNKNOWN
    elif latest is None:
        state = "설치본만 확인"
    else:
        c = _cmp(cur, latest)
        state = "최신" if c is not None and c >= 0 else ("뒤처짐" if c is not None else UNKNOWN)
    return {"tool": name, "installed": cur, "latest": latest,
            "state": state, "why": why, "fix": fix}


def check_orca_skills():
    """orca skills list 를 스냅샷과 대조한다. 첫 실행이면 스냅샷만 만든다."""
    try:
        snapshot = _snapshot_path()
        with _snapshot_lock(snapshot):
            # Hold the lock during collection too: a late old listing must not
            # replace a newer listing collected by another process.
            rc, out, err = _run(["orca", "skills", "list"], timeout=120)
            if rc != 0 or not out:
                return {"state": UNKNOWN, "detail": err or "빈 출력",
                        "added": [], "removed": [], "changed": []}
            current = {}
            for line in out.splitlines():
                if ":" not in line:
                    continue
                name, desc = line.split(":", 1)
                name = name.strip()
                if name and " " not in name:
                    current[name] = desc.strip()
            if not current:
                return {"state": UNKNOWN, "detail": "파싱 결과 0건 (형식이 바뀌었을 수 있다)",
                        "added": [], "removed": [], "changed": []}
            if not os.path.lexists(snapshot):
                _write_snapshot(snapshot, current, {})
                return {"state": "스냅샷 생성",
                        "detail": "%d개 기록. 다음 실행부터 대조한다." % len(current),
                        "added": sorted(current), "removed": [], "changed": []}

            prev_doc = _read_snapshot(snapshot)
            prev = prev_doc["skills"]
            added = sorted(set(current) - set(prev))
            removed = sorted(set(prev) - set(current))
            changed = sorted(k for k in set(current) & set(prev) if current[k] != prev[k])

            # Pending survives every report until the reviewed digest is acknowledged.
            pending = prev_doc.get("pending") or {}
            if added or removed or changed:
                pending = {
                    "generation": pending.get("generation") or uuid.uuid4().hex,
                    "first_seen": pending.get("first_seen") or time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "seen_count": int(pending.get("seen_count") or 0) + 1,
                    "added": sorted(set(pending.get("added") or []) | set(added)),
                    "removed": sorted(set(pending.get("removed") or []) | set(removed)),
                    "changed": sorted(set(pending.get("changed") or []) | set(changed)),
                }
            elif pending and not pending.get("generation"):
                pending = {**pending, "generation": uuid.uuid4().hex}
            _write_snapshot(snapshot, current, pending)
            if pending:
                detail = "%d개 · 최초 감지 %s · 변경 이벤트 %d건 미확인" % (
                    len(current), pending["first_seen"], pending["seen_count"])
                return {"state": "미확인 변경", "detail": detail,
                        "added": pending["added"], "removed": pending["removed"],
                        "changed": pending["changed"], "pending": True,
                        "pending_digest": _pending_digest({"skills": current, "pending": pending})}
            return {"state": "변경 없음", "detail": "%d개" % len(current),
                    "added": [], "removed": [], "changed": [], "pending": False}
    except (OSError, ValueError, UnicodeError) as exc:
        return {"state": UNKNOWN, "detail": "상태 저장 실패: %s" % exc,
                "added": [], "removed": [], "changed": []}


def ack_skills(expected_digest):
    """Clear only the exact pending state the human reviewed."""
    snapshot = _snapshot_path()
    with _snapshot_lock(snapshot):
        if not os.path.lexists(snapshot):
            raise ValueError("스냅샷이 없다")
        doc = _read_snapshot(snapshot)
        p = doc.get("pending") or {}
        if not p:
            raise ValueError("미확인 변경이 없다")
        if not isinstance(expected_digest, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_digest):
            raise ValueError("64자리 확인 토큰이 필요하다")
        if expected_digest != _pending_digest(doc):
            raise ValueError("검토 후 미확인 변경이 달라졌다. 다시 보고 확인해야 한다")
        _write_snapshot(snapshot, doc["skills"], {})
        return "확인 처리: 추가 %d · 삭제 %d · 설명변경 %d (최초 %s)" % (
            len(p.get("added") or []), len(p.get("removed") or []),
            len(p.get("changed") or []), p.get("first_seen"))


def _write_snapshot(path, skills, pending=None):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=directory,
                                         prefix=".orca-skills-", suffix=".tmp",
                                         delete=False) as target:
            temporary = target.name
            json.dump({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                       "skills": skills, "pending": pending or {}},
                      target, ensure_ascii=False, indent=2)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def migrate_snapshot(source):
    """Explicit, one-time byte-preserving move of a legacy bundle snapshot."""
    temporary = None
    try:
        if not os.path.isfile(source) or os.path.islink(source):
            return 1
        _read_snapshot(source)
        target = _snapshot_path()
        directory = os.path.dirname(target)
        os.makedirs(directory, exist_ok=True)
        with open(source, "rb") as old:
            data = old.read(65537)
        if len(data) > 65536:
            return 1
        with tempfile.NamedTemporaryFile("wb", dir=directory, prefix=".orca-skills-",
                                         suffix=".tmp", delete=False) as staged:
            temporary = staged.name
            staged.write(data)
            staged.flush()
            os.fsync(staged.fileno())
        with _snapshot_lock(target):
            os.link(temporary, target)  # atomic create-if-absent; never a partial target
        return 0
    except (OSError, ValueError, UnicodeError):
        return 1
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def report(as_json=False):
    clis = check_clis()
    skills = check_orca_skills()
    blocking = [r for r in clis if r["state"] == "뒤처짐" and r["tool"] == "codex"]
    preflight_blocked = bool(blocking) or skills["state"] == UNKNOWN

    if as_json:
        print(json.dumps({"clis": clis, "orca_skills": skills,
                          "blocking": blocking, "preflight_blocked": preflight_blocked},
                         ensure_ascii=False, indent=2))
        return 1 if preflight_blocked else 0

    print("=== 툴체인 (프리플라이트 0-A) ===")
    for r in clis:
        mark = {"뒤처짐": "!", "최신": " ", UNKNOWN: "?"}.get(r["state"], " ")
        print(" %s %-8s 설치=%-12s 최신=%-12s %s"
              % (mark, r["tool"], r["installed"] or "-", r["latest"] or "-", r["state"]))
        if r["state"] == "뒤처짐" and r["why"]:
            print("     %s" % r["why"])
            if r["fix"]:
                print("     고치기: %s" % r["fix"])
    print()
    mark = "!! " if skills.get("pending") else ""
    print("=== %sorca 스킬 목록: %s (%s) ===" % (mark, skills["state"], skills["detail"]))
    if skills.get("pending"):
        print("  이 변경은 확인할 때까지 계속 뜬다 — 오르카의 명령 정본은 이 문서가 아니라")
        print("  `orca skills get <이름>` 이다. 바뀐 스킬을 다시 읽은 뒤")
        print("  `--ack-skills %s` 로 이 변경 묶음만 확인한다." % skills["pending_digest"])
    for k, items in (("추가", skills["added"]), ("삭제", skills["removed"]),
                     ("설명 변경", skills["changed"])):
        if items:
            print("  %s: %s" % (k, ", ".join(items)))

    if blocking:
        print("\n!! codex 가 뒤처졌다. 디스패치하면 전 워커가 "
              "`codex-update-prompt` 로 막힌다. 올리고 시작할 것.")
        print("   (전역 패키지다 - 다른 세션이 codex 를 쓰는 중인지 먼저 볼 것:")
        print("    CPU 0초로 멈춰 있으면 그것도 이 프롬프트에 걸린 워커다.)")
    if skills["state"] == UNKNOWN:
        print("\n!! Orca 스킬 목록 또는 상태가 미확인이다. 이 결과로 디스패치하지 않는다.")
    return 1 if preflight_blocked else 0


def report_local_codex():
    """A side-effect-minimal probe: no registry, Orca, snapshot or account access."""
    row = check_codex_local()
    print(json.dumps(row, ensure_ascii=True))
    if row["state"] == "뒤처짐":
        return 1
    return 0 if row["state"] == "로컬 이상" else 2


if __name__ == "__main__":
    args = sys.argv[1:]
    if args in (["--help"], ["-h"]):
        print("Usage: check_tooling.py [--local-codex | --ack-skills DIGEST | --migrate-snapshot FILE | --json | --help]")
        print("  --local-codex  Local Codex PATH/package check; no registry or Orca access")
        print("  --ack-skills DIGEST  Acknowledge only the reviewed pending state")
        print("  --migrate-snapshot FILE  Copy one legacy snapshot to external user state; never overwrite")
        print("  --json         Full report as JSON (queries registry and Orca)")
        print("  no arguments   Full report (queries registry and Orca)")
        sys.exit(0)
    if args == ["--local-codex"]:
        sys.exit(report_local_codex())
    if args and args[0] == "--ack-skills":
        if len(args) != 2:
            print("--ack-skills requires the digest from the latest report", file=sys.stderr)
            sys.exit(2)
        try:
            print(ack_skills(args[1]))
            sys.exit(0)
        except (OSError, ValueError) as exc:
            print("확인 처리 실패: %s" % exc, file=sys.stderr)
            sys.exit(1)
    if len(args) == 2 and args[0] == "--migrate-snapshot":
        result = migrate_snapshot(args[1])
        print("기존 기준선 이전 완료" if result == 0 else "기준선 이전 실패 또는 대상이 이미 존재함")
        sys.exit(result)
    if args == ["--json"]:
        sys.exit(report(as_json=True))
    if args:
        print("Unknown option(s): %s; use --help" % " ".join(args), file=sys.stderr)
        sys.exit(2)
    sys.exit(report(as_json=False))
