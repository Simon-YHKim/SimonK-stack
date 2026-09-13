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
import time

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_DIR = os.path.join(SKILL_ROOT, "state")
SNAPSHOT = os.path.join(STATE_DIR, "orca-skills.json")

UNKNOWN = "미확인"


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
    if rc is None:
        return None, err
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
    def parts(v):
        return [int(x) for x in re.findall(r"\d+", v or "")][:4]
    pa, pb = parts(a), parts(b)
    if not pa or not pb:
        return None
    pa += [0] * (4 - len(pa))
    pb += [0] * (4 - len(pb))
    return (pa > pb) - (pa < pb)


def check_clis():
    rows = []

    cur, _ = _version(["codex", "--version"])
    latest = _npm_latest("@openai/codex")
    rows.append(_row("codex", cur, latest,
                     "뒤처지면 `Agent startup blocked: codex-update-prompt` 로 "
                     "**모든 codex 워커가 안 뜬다**. 2026-09-12 실사고.",
                     "npm install -g @openai/codex@latest"))

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

    os.makedirs(STATE_DIR, exist_ok=True)
    if not os.path.isfile(SNAPSHOT):
        _write_snapshot(current, {})
        return {"state": "스냅샷 생성", "detail": "%d개 기록. 다음 실행부터 대조한다." % len(current),
                "added": sorted(current), "removed": [], "changed": []}

    try:
        prev = json.load(open(SNAPSHOT, encoding="utf-8")).get("skills", {})
    except Exception:  # noqa: BLE001
        prev = {}

    added = sorted(set(current) - set(prev))
    removed = sorted(set(prev) - set(current))
    changed = sorted(k for k in set(current) & set(prev) if current[k] != prev[k])

    # ⚠ 예전에는 여기서 무조건 스냅샷을 덮어썼다. 그러면 변경이 **딱 한 번** 보고되고
    # 사라진다. 그 한 번을 놓치면 "바뀐 적 없음"과 "바뀌었는데 아무도 안 봄"이
    # 같은 출력이 된다 — 모든 입력에 같은 답을 주는 신호는 신호가 아니다.
    # 그래서 확인(`--ack-skills`)할 때까지 남는 pending 을 둔다.
    try:
        prev_doc = json.load(open(SNAPSHOT, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        prev_doc = {}
    pending = prev_doc.get("pending") or {}
    if added or removed or changed:
        pending = {
            "first_seen": pending.get("first_seen") or time.strftime("%Y-%m-%dT%H:%M:%S"),
            "seen_count": int(pending.get("seen_count") or 0) + 1,
            "added": sorted(set(pending.get("added") or []) | set(added)),
            "removed": sorted(set(pending.get("removed") or []) | set(removed)),
            "changed": sorted(set(pending.get("changed") or []) | set(changed)),
        }
    _write_snapshot(current, pending)

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
    if not os.path.isfile(SNAPSHOT):
        return "스냅샷이 없다"
    doc = json.load(open(SNAPSHOT, encoding="utf-8"))
    p = doc.get("pending") or {}
    if not p:
        return "미확인 변경 없음"
    _write_snapshot(doc.get("skills") or {}, {})
    return "확인 처리: 추가 %d · 삭제 %d · 설명변경 %d (최초 %s)" % (
        len(p.get("added") or []), len(p.get("removed") or []),
        len(p.get("changed") or []), p.get("first_seen"))


def _write_snapshot(skills, pending=None):
    json.dump({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "skills": skills, "pending": pending or {}},
              open(SNAPSHOT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


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


if __name__ == "__main__":
    if "--ack-skills" in sys.argv:
        print(ack_skills())
        sys.exit(0)
    sys.exit(report(as_json="--json" in sys.argv))
