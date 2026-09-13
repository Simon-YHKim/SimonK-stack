# -*- coding: utf-8 -*-
"""G8 — Orca 워커 강제종료 절차 (실행 가능한 문서).

dispatch id → 그 워커의 터미널 handle → 환경변수 ORCA_TERMINAL_HANDLE 이 같은 프로세스와
그 자손 전부 → 트리째 종료 → 재스캔 0 확인 → (선택) worker-stop 으로 Orca 상태 fence.

왜 이 경로인가 (2026-09-13 실측, Orca 1.4.200 · Windows):
- worker-stop 은 "Dispatch 를 fence 하고 터미널을 멈춘다"만 약속하고 프로세스 사망은 약속하지 않는다.
  worker-abandon 은 프로세스에 손대지 않는다. worker-release 는 끝난 워커의 터미널만 닫는다(help 원문).
- terminal show 는 PID 를 내주지 않는다(ptyId · incarnationId 만).
- 대신 워커 셸(pwsh)과 에이전트(claude.exe · agy.exe · codex)가 모두 환경변수
  ORCA_TERMINAL_HANDLE=<handle> 을 갖는다. 코디네이터 세션은 다른 handle 을 갖는다.
  구조: Orca.exe(터미널 호스트) → pwsh(터미널마다) → 에이전트 → 도구 하위 프로세스.

기본은 목록만 출력한다. --kill 을 줘야 죽인다.
자기 자신 · 자기 조상 프로세스가 대상에 섞이면 아무것도 하지 않고 종료코드 3.
"""
import argparse
import json
import os
import sys
import time

import psutil

sys.path.insert(0, os.path.expanduser("~/.claude/skills/vibe/scripts"))
import routing  # noqa: E402


def kst(ts):
    return time.strftime("%H:%M:%S", time.gmtime(ts + 9 * 3600))


def handle_for(dispatch):
    ok, d = routing.run_orca_json("orchestration", "worker-list", "--json")
    res = (d or {}).get("result", d) if isinstance(d, dict) else {}
    for w in (res or {}).get("workers", []):
        if w.get("dispatchId") == dispatch:
            return w.get("agentTerminalHandle"), w
    return None, None


def procs_with_handle(handle):
    out = []
    for p in psutil.process_iter(["pid", "name", "create_time"]):
        try:
            if p.environ().get("ORCA_TERMINAL_HANDLE") == handle:
                out.append(p)
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess, OSError):
            continue
    return out


def describe(p, with_env):
    try:
        return {"pid": p.pid, "name": p.name(), "started_kst": kst(p.create_time()), "env_match": with_env}
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return {"pid": p.pid, "name": "?", "started_kst": "?", "env_match": with_env}


def main():
    ap = argparse.ArgumentParser(description="Orca 워커 강제종료 (G8)")
    ap.add_argument("--dispatch", help="ctx_… dispatch id")
    ap.add_argument("--handle", help="term_… 터미널 handle (dispatch 대신)")
    ap.add_argument("--kill", action="store_true", help="실제로 종료한다. 없으면 목록만")
    ap.add_argument("--fence", action="store_true", help="종료 확인 뒤 worker-stop 으로 Orca 상태를 닫는다")
    args = ap.parse_args()

    handle = args.handle
    if not handle and args.dispatch:
        handle, _w = handle_for(args.dispatch)
    if not handle:
        print(json.dumps({"ok": False, "error": "handle 을 찾지 못했다", "dispatch": args.dispatch}, ensure_ascii=False))
        return 2

    me = os.environ.get("ORCA_TERMINAL_HANDLE")
    protected = {os.getpid()} | {p.pid for p in psutil.Process().parents()}
    if me and me == handle:
        print(json.dumps({"ok": False, "error": "자기 자신의 터미널이다 — 거부", "handle": handle}, ensure_ascii=False))
        return 3

    roots = procs_with_handle(handle)
    targets = {}
    for r in roots:
        targets[r.pid] = (r, True)
        try:
            for c in r.children(recursive=True):
                targets.setdefault(c.pid, (c, False))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    clash = sorted(pid for pid in targets if pid in protected)
    if clash:
        print(json.dumps({"ok": False, "error": "대상에 이 스크립트의 조상 프로세스가 있다 — 거부",
                          "pids": clash, "handle": handle}, ensure_ascii=False))
        return 3

    listing = [describe(p, env) for p, env in targets.values()]
    summary = {"handle": handle, "dispatch": args.dispatch, "targets": listing, "count": len(listing),
               "measured_kst": kst(time.time())}
    if not args.kill:
        summary["mode"] = "dry"
        print(json.dumps(summary, ensure_ascii=False, indent=1))
        return 0

    procs = [p for p, _env in targets.values()]
    for p in procs:
        try:
            p.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    _gone, alive = psutil.wait_procs(procs, timeout=8)
    for p in alive:
        try:
            p.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    _gone2, alive2 = psutil.wait_procs(alive, timeout=5)

    left = procs_with_handle(handle)
    left_pids = sorted({p.pid for p in left} | {p.pid for p in alive2})
    summary.update(mode="kill", terminated_then_killed=len(alive), left_after=left_pids,
                   verified=not left_pids, verified_kst=kst(time.time()))
    if args.fence and args.dispatch and summary["verified"]:
        ok, d = routing.run_orca_json("orchestration", "worker-stop", "--dispatch", args.dispatch, "--json")
        summary["worker_stop_ok"] = ok
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0 if summary["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
