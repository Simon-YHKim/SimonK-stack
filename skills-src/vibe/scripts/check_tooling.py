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
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

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
                    or any(not isinstance(pending.get(key), list)
                           or not all(isinstance(item, str) for item in pending[key])
                           for key in ("added", "removed", "changed"))):
        raise ValueError("미확인 변경 형식이 잘못됐다")
    return doc


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

    try:
        snapshot = _snapshot_path()
        os.makedirs(os.path.dirname(snapshot), exist_ok=True)
        if os.path.isfile(snapshot):
            prev_doc = _read_snapshot(snapshot)
        else:
            _write_snapshot(snapshot, current, {})
            prev_doc = None
    except (OSError, ValueError, UnicodeError) as exc:
        return {"state": UNKNOWN, "detail": "상태 저장 실패: %s" % exc,
                "added": [], "removed": [], "changed": []}

    if prev_doc is None:
        return {"state": "스냅샷 생성", "detail": "%d개 기록. 다음 실행부터 대조한다." % len(current),
                "added": sorted(current), "removed": [], "changed": []}

    prev = prev_doc["skills"]

    added = sorted(set(current) - set(prev))
    removed = sorted(set(prev) - set(current))
    changed = sorted(k for k in set(current) & set(prev) if current[k] != prev[k])

    # ⚠ 예전에는 여기서 무조건 스냅샷을 덮어썼다. 그러면 변경이 **딱 한 번** 보고되고
    # 사라진다. 그 한 번을 놓치면 "바뀐 적 없음"과 "바뀌었는데 아무도 안 봄"이
    # 같은 출력이 된다 — 모든 입력에 같은 답을 주는 신호는 신호가 아니다.
    # 그래서 확인(`--ack-skills`)할 때까지 남는 pending 을 둔다.
    pending = prev_doc.get("pending") or {}
    if added or removed or changed:
        pending = {
            "first_seen": pending.get("first_seen") or time.strftime("%Y-%m-%dT%H:%M:%S"),
            "seen_count": int(pending.get("seen_count") or 0) + 1,
            "added": sorted(set(pending.get("added") or []) | set(added)),
            "removed": sorted(set(pending.get("removed") or []) | set(removed)),
            "changed": sorted(set(pending.get("changed") or []) | set(changed)),
        }
    try:
        _write_snapshot(snapshot, current, pending)
    except OSError as exc:
        return {"state": UNKNOWN, "detail": "상태 저장 실패: %s" % exc,
                "added": [], "removed": [], "changed": []}

    if pending:
        state = "미확인 변경"
        detail = "%d개 · 최초 감지 %s · 변경 이벤트 %d건 미확인 (`--ack-skills` 로 확인)" % (
            len(current), pending.get("first_seen"), pending.get("seen_count", 1))
        return {"state": state, "detail": detail, "added": pending["added"],
                "removed": pending["removed"], "changed": pending["changed"],
                "pending": True}
    return {"state": "변경 없음", "detail": "%d개" % len(current),
            "added": [], "removed": [], "changed": [], "pending": False}


def ack_skills():
    """미확인 변경을 확인 처리한다. 사람이 그 스킬 문서를 다시 읽은 뒤 부른다."""
    snapshot = _snapshot_path()
    if not os.path.isfile(snapshot):
        return "스냅샷이 없다"
    doc = _read_snapshot(snapshot)
    p = doc.get("pending") or {}
    if not p:
        return "미확인 변경 없음"
    _write_snapshot(snapshot, doc.get("skills") or {}, {})
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
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def migrate_snapshot(source):
    """Explicit, one-time byte-preserving move of a legacy bundle snapshot."""
    try:
        if not os.path.isfile(source) or os.path.islink(source):
            return 1
        _read_snapshot(source)
        target = _snapshot_path()
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(source, "rb") as old:
            data = old.read(65537)
        if len(data) > 65536:
            return 1
        with open(target, "xb") as new:
            new.write(data)
        return 0
    except (OSError, ValueError, UnicodeError):
        return 1


def report(as_json=False):
    clis = check_clis()
    skills = check_orca_skills()
    blocking = [r for r in clis if r["state"] == "뒤처짐" and r["tool"] == "codex"]

    if as_json:
        print(json.dumps({"clis": clis, "orca_skills": skills,
                          "blocking": blocking}, ensure_ascii=False, indent=2))
        return 1 if blocking else 0

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
        print("  `orca skills get <이름>` 이다. 바뀐 스킬을 다시 읽은 뒤 `--ack-skills`.")
    for k, items in (("추가", skills["added"]), ("삭제", skills["removed"]),
                     ("설명 변경", skills["changed"])):
        if items:
            print("  %s: %s" % (k, ", ".join(items)))

    if blocking:
        print("\n!! codex 가 뒤처졌다. 디스패치하면 전 워커가 "
              "`codex-update-prompt` 로 막힌다. 올리고 시작할 것.")
        print("   (전역 패키지다 - 다른 세션이 codex 를 쓰는 중인지 먼저 볼 것:")
        print("    CPU 0초로 멈춰 있으면 그것도 이 프롬프트에 걸린 워커다.)")
    return 1 if blocking else 0


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
        print("Usage: check_tooling.py [--local-codex | --ack-skills | --migrate-snapshot FILE | --json | --help]")
        print("  --local-codex  Local Codex PATH/package check; no registry or Orca access")
        print("  --ack-skills   Acknowledge the existing Orca skills snapshot")
        print("  --migrate-snapshot FILE  Copy one legacy snapshot to external user state; never overwrite")
        print("  --json         Full report as JSON (queries registry and Orca)")
        print("  no arguments   Full report (queries registry and Orca)")
        sys.exit(0)
    if args == ["--local-codex"]:
        sys.exit(report_local_codex())
    if args == ["--ack-skills"]:
        print(ack_skills())
        sys.exit(0)
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
