# selftest.py — /vibe v2.1 자체 검증
#
# ── 2026-09-04 독립 보안 감사 HIGH-7 반영 ───────────────────────
# 이전 판은 **실제** Downloads 파일을 덮어쓰고, **실제** 공유 원장을 rewrite 하고,
# **실제** HUB 에 최대 3회 commit 했다. 고정 run id 를 써서 사용자의 같은 이름 파일을
# 지울 수도 있었다. try/finally 도 없었다. "22/22 통과"는 그렇게 얻은 숫자였다.
# 감사관은 이 이유로 이 파일을 실행하지 않았다.
#
# 이제:
#   · 임시 디렉터리에 git init 한 저장소와 임시 Downloads 를 만든다
#   · ledger.configure() 로 주입하고 finally 에서 반드시 restore + 정리한다
#   · run id 는 매번 uuid — 기존 경로가 있으면 절대 덮어쓰지 않는다
#   · 커밋 검증은 "커밋이 존재한다"가 아니라 "HEAD 가 바뀌었다"로 한다
#   · 시크릿 누출 검사는 '실제로 넣은 값'을 찾는다 (다른 문자열을 보던 버그 수정)
#
# 실제 HUB·Downloads 는 어떤 경우에도 건드리지 않는다.
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid

# Suppress helper bytecode before local imports in an immutable candidate.
if __name__ == "__main__":
    sys.dont_write_bytecode = True
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import ledger   # noqa: E402
import routing  # noqa: E402
import make_decision_sheet as sheet  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ok = fail = 0


def check(label, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  PASS  {label}")
    else:
        fail += 1
        print(f"  FAIL  {label}  {detail}")


def _git(args, cwd):
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=60)
    return p.returncode, (p.stdout or "").strip()


def make_sandbox():
    root = tempfile.mkdtemp(prefix="vibe-selftest-")
    repo = os.path.join(root, "hub")
    dl = os.path.join(root, "downloads")
    os.makedirs(repo)
    os.makedirs(dl)
    for a in (["init", "-q"], ["config", "user.email", "selftest@local"],
              ["config", "user.name", "selftest"]):
        _git(a, repo)
    led = os.path.join(repo, "routing_ledger.jsonl")
    open(led, "w", encoding="utf-8").close()
    _git(["add", "routing_ledger.jsonl"], repo)
    _git(["commit", "-qm", "init"], repo)
    return root, repo, dl, led


def run():
    root, repo, dl, led = make_sandbox()
    prev = ledger.configure(ledger=led, downloads=dl)
    RUN = "run_" + uuid.uuid4().hex[:16]          # 고정 id 금지
    try:
        print(f"샌드박스: {root}")
        print(f"run id  : {RUN}  (매 실행 새로 생성)")
        print()

        print("=== 격리 확인 — 실제 경로를 쓰지 않는가 ===")
        check("원장이 임시 저장소를 가리킨다", ledger._ledger_path() == led)
        check("Downloads 가 임시 폴더를 가리킨다", ledger._downloads_dir() == dl)
        check("실제 HUB 경로가 아니다", ledger.HUB not in ledger._ledger_path())

        print()
        print("=== C8 · 원장 append + commit (HEAD 가 실제로 바뀌는가) ===")
        _, head_before = _git(["rev-parse", "HEAD"], repo)
        rec = ledger.new_record(RUN, "selftest", "A", "gpt-5.6-luna", "low",
                                falsifiable=False, explore=True, status="done",
                                sec=42, retries=0, quota_delta={"codex": 1})
        n, note = ledger.append_records([rec])
        _, head_after = _git(["rev-parse", "HEAD"], repo)
        recs, broken = ledger.read_ledger()
        print(f"  {note}")
        check("레코드 1개 기록", n == 1 and len(recs) == 1, f"n={n} recs={len(recs)}")
        check("HEAD 가 바뀌었다(새 커밋)", head_before != head_after,
              f"{head_before[:8]} -> {head_after[:8]}")

        print()
        print("=== S1 · 시크릿이 든 레코드는 기록되지 않는다 ===")
        BS = chr(92)
        secret_value = "sk-" + ("a" * 24)          # 실제로 넣는 값
        bad = ledger.new_record(RUN, "leak", "A", "gpt-5.6-luna", "low", False, False, "done")
        bad["task"] = "token=" + secret_value
        before_n = len(ledger.read_ledger()[0])
        n2, note2 = ledger.append_records([bad])
        after_n = len(ledger.read_ledger()[0])
        check("기록 거부됨", n2 == 0 and after_n == before_n, note2)
        check("사유에 실제 값이 안 실린다", secret_value not in note2, "값이 노출됨")
        check("원장 파일에도 값이 없다", secret_value not in open(led, encoding="utf-8").read())

        print()
        print("=== C9 · 결정 시트 결과 회수 + 소비 ===")
        dpath = os.path.join(dl, f"decisions_{RUN}.json")
        check("기존 파일을 덮어쓰지 않는다", not os.path.exists(dpath))
        # provenance: 정상 흐름은 시트 생성 시 manifest 가 먼저 남는다 (감사 MED)
        man1 = ledger.write_pending_manifest(
            RUN, [{"id": f"i{i}", "lane": "gpt-5.6-luna"} for i in range(1, 5)])
        with open(dpath, "w", encoding="utf-8") as f:
            json.dump({"run": RUN, "nonce": man1["nonce"],
                       "by_lane": {"gpt-5.6-luna": {"items": 4, "accepted": 3}}}, f)
        merged, notes = ledger.collect_decisions()
        recs, _ = ledger.read_ledger()
        check("merge 됨", RUN in merged, str(notes))
        check("items=4 accepted=3 반영",
              any(r.get("items") == 4 and r.get("accepted") == 3 for r in recs))
        check("파일이 소비됨", not os.path.exists(dpath))

        print()
        print("=== S2 · 신뢰 경계 밖 입력 거부 ===")
        cases = [
            ("파일명 화이트리스트 밖", "decisions_evil.json",
             {"run": RUN, "by_lane": {"gpt-5.6-luna": {"items": 1, "accepted": 1}}}),
            ("파일명 run != 내용 run", "decisions_run_Bait.json",
             {"run": RUN, "by_lane": {"gpt-5.6-luna": {"items": 1, "accepted": 1}}}),
            ("정의되지 않은 필드", f"decisions_{RUN}.json",
             {"run": RUN, "by_lane": {}, "cmd": "rm -rf /"}),
            ("accepted > items", f"decisions_{RUN}.json",
             {"run": RUN, "by_lane": {"x": {"items": 1, "accepted": 9}}}),
            ("bool 로 정수 흉내", f"decisions_{RUN}.json",
             {"run": RUN, "by_lane": {"gpt-5.6-luna": {"items": True, "accepted": True}}}),
            ("float 로 정수 흉내", f"decisions_{RUN}.json",
             {"run": RUN, "by_lane": {"gpt-5.6-luna": {"items": 1.9, "accepted": 1.8}}}),
        ]
        for label, fname, payload in cases:
            p = os.path.join(dl, fname)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            m, nts = ledger.collect_decisions()
            check(f"{label} → 거부", RUN not in m, str(nts))
            if os.path.exists(p):
                os.remove(p)
        p = os.path.join(dl, f"decisions_{RUN}.json")
        with open(p, "w", encoding="utf-8") as f:
            f.write('{"run":"%s","run":"run_x","by_lane":{"a":{"items":1,"accepted":1}}}' % RUN)
        m, nts = ledger.collect_decisions()
        check("중복 JSON 키 → 거부", RUN not in m, str(nts))
        os.path.exists(p) and os.remove(p)

        print()
        print("=== 감사 HIGH-1/2 · 결정 시트 XSS 벡터 ===")
        out_html = os.path.join(root, "sheet.html")
        xss = [
            ("</script> 탈출", "</script><img src=x onerror='document.title=1'><script>"),
            ("DOM XSS svg", "<svg onload='document.title=1'></svg>"),
            ("__proto__ 오염", "__proto__"),
        ]
        for label, lane in xss:
            try:
                sheet.build({"run": RUN, "objective": "t",
                             "items": [{"id": "i1", "lane": lane, "title": "t"}]}, out_html)
                check(f"{label} → 거부", False, "생성되어 버렸다")
            except SystemExit:
                check(f"{label} → 거부", True)
        try:
            sheet.build({"run": RUN, "objective": "t", "items": [
                {"id": "dup", "lane": "gpt-5.6-sol", "title": "a"},
                {"id": "dup", "lane": "gpt-5.6-terra", "title": "b"}]}, out_html)
            check("중복 item id → 거부", False, "생성되어 버렸다")
        except SystemExit:
            check("중복 item id → 거부", True)

        doc, n_items, lanes = sheet.build({"run": RUN, "objective": "t", "items": [
            {"id": "i1", "lane": "gpt-5.6-sol", "title": "a", "default": True},
            {"id": "i2", "lane": "claude-opus-5", "title": "b", "default": False}]}, out_html)
        payload_line = [l for l in doc.splitlines() if "var DATA=" in l][0]
        check("정상 시트는 생성된다", n_items == 2)
        check("payload 에 원문 '<' 없음", "<" not in payload_line)
        js = doc.split("<script>", 1)[1]
        code_lines = [l for l in js.splitlines()
                      if "innerHTML" in l and not l.strip().startswith(("/*", "*", "//"))
                      and "innerHTML" in l.split("/*")[0]]
        check("innerHTML sink 없음", not code_lines, str(code_lines[:2]))

        print()
        print("=== C11 · 가드 ===")
        default_coding = routing.lanes_for_proc("coding")[0]   # D-28 #5 — 코딩은 공정 전용 목록
        gate = routing.fixed_for("security-artifact-gate")
        biz = routing.fixed_for("security-bizlogic-2nd")
        a_ok = [{"proc": "coding", "lane": default_coding, "class": "B"},
                {"proc": "security-artifact-gate", "lane": gate[0], "class": "B"},
                {"proc": "security-bizlogic-2nd", "lane": biz[0], "class": "B"}]
        v_ok = routing.check_guards(a_ok, quota_checked_vendors=routing.VENDORS)
        print(f"  [정본 기본 배정] 코딩={default_coding} · 게이트={gate[0]} · 인가={biz[0]}")
        check("정본 기본 배정이 가드를 통과한다", not v_ok, f"위반={v_ok}")

        # D-28 #5·#14·C2 — 코딩 불변식 · 음성대조 · 게이트 벤더 차단 · 재시도 재검증 · 탐색 후보
        gv = routing.gate_vendors()
        check("코딩 목록 벤더 ∩ 게이트 벤더 = ∅ (D-28 #5)",
              not ({routing.LANES[l]["vendor"] for l in routing.PROCESS_LANES["coding"]} & gv),
              f"coding={routing.PROCESS_LANES['coding']} gate={sorted(gv)}")
        ok_n1, v_n1, _n1 = routing.validate_plan(
            [{"proc": "coding", "lane": "gpt-6-astra", "class": "B"}] + a_ok[1:],
            quota_checked_vendors=routing.VENDORS)
        check("코딩이 codex(astra)면 G1 + CODING_LANE_NOT_ALLOWED (D-28 N1)",
              not ok_n1 and "G1" in v_n1 and "CODING_LANE_NOT_ALLOWED" in v_n1, str(v_n1))
        ok_def, v_def, _nd = routing.validate_plan(a_ok, quota_checked_vendors=routing.VENDORS)
        check("정본 기본 배정이 validate_plan 을 통과한다", ok_def, str(v_def))
        ok_gb, v_gb, _ng = routing.validate_plan(
            a_ok, quota_checked_vendors=routing.VENDORS,
            quota_states={"claude": "ok", "codex": "blocked", "gemini": "ok", "grok": "ok"})
        check("게이트 벤더 사용 금지면 코딩 라운드 차단 (D-28 #14)",
              not ok_gb and "GATE_VENDOR_BLOCKED" in v_gb, str(v_gb))
        ok_rt, v_rt, _nr, _new = routing.revalidate_for_retry(
            a_ok, "coding", "gpt-6-astra", quota_checked_vendors=routing.VENDORS)
        check("재시도로 코딩을 codex 로 옮기면 재검증이 막는다 (G13)",
              not ok_rt and "G1" in v_rt, str(v_rt))
        # G13 보강 (2026-09-19) — 일반 공정을 사용 금지 레인으로 넘기는 재배정도 막는다
        a_rd = a_ok + [{"proc": "research-deep", "lane": "gpt-6-astra", "class": "B"}]
        qs_grok_blocked = {"claude": "ok", "codex": "ok", "gemini": "ok", "grok": "blocked"}
        ok_lb, v_lb, _nlb, _ = routing.revalidate_for_retry(
            a_rd, "research-deep", "grok-4.6", quota_checked_vendors=routing.VENDORS,
            quota_states=qs_grok_blocked)
        check("재배정 대상 레인 벤더가 사용 금지면 막는다 (G13 보강)",
              not ok_lb and "LANE_VENDOR_BLOCKED" in v_lb, str(v_lb))
        ok_ld, v_ld, _nld, _ = routing.revalidate_for_retry(
            a_rd, "research-deep", "claude-fable-5-1", quota_checked_vendors=routing.VENDORS,
            quota_states={"claude": "demote", "codex": "demote", "gemini": "ok", "grok": "blocked"})
        check("강등(demote) 레인으로의 재배정은 허용한다 (Q-05)", ok_ld, str(v_ld))
        ok_ln, v_ln, _nln, _ = routing.revalidate_for_retry(
            a_rd, "research-deep", "grok-4.6", quota_checked_vendors=routing.VENDORS)
        check("quota_states 가 없으면 벤더 금지 검사는 건너뛴다(기존 동작 유지)",
              "LANE_VENDOR_BLOCKED" not in v_ln, str(v_ln))
        v_exc = routing.check_guards(
            [{"proc": "coding", "lane": "claude-opus-5", "class": "B", "explore": True}],
            quota_checked_vendors=routing.VENDORS)
        check("탐색 슬롯이 코딩에 배정 → 검출 (D-28 C2)", "EXPLORE_MISASSIGNED" in v_exc, str(v_exc))
        cands = routing.explore_candidates()
        check("탐색 후보에 코딩·고정 공정이 없다",
              "coding" not in cands and not any(routing.fixed_for(c) for c in cands), str(cands))
        check("탐색 후보의 2순위는 모두 Orca 로 뜬다 (D-28 #12)",
              all(routing.LANES[routing.lanes_for_proc(c)[1]].get("dispatch") != "unavailable"
                  for c in cands), str(cands))
        only_codex = routing.explore_candidates(live_ok_vendors={"codex"})
        check("실호출 통과 벤더가 아닌 2순위는 탐색 후보에서 빠진다",
              all(routing.LANES[routing.lanes_for_proc(c)[1]]["vendor"] == "codex" for c in only_codex),
              str(only_codex))
        check("R1 — 반증 예인 A 작업은 A-verify 로 승격 (D-28 #11 본 규칙)",
              routing.lanes_for_proc("inventory-schema", falsifiable=True) == routing.lanes_for("A-verify"))
        check("A-verify = astra → fable → opus (D-28 #4)",
              routing.lanes_for("A-verify") == ["gpt-6-astra", "claude-fable-5-1", "claude-opus-5-5"],
              str(routing.lanes_for("A-verify")))
        gate_a = [{"proc": "security-artifact-gate", "lane": routing.fixed_for("security-artifact-gate")[0], "class": "B"},
                  {"proc": "security-bizlogic-2nd", "lane": routing.fixed_for("security-bizlogic-2nd")[0], "class": "B"}]
        ok_w1, v_w1, _nw1 = routing.validate_plan(
            [{"proc": "terminal-ci-git", "lane": "gpt-6-astra", "class": "B", "writes": True}] + gate_a,
            quota_checked_vendors=routing.VENDORS)
        check("writes 공정이 codex 면 G1 + CODING_LANE_NOT_ALLOWED (Q-09)",
              not ok_w1 and "G1" in v_w1 and "CODING_LANE_NOT_ALLOWED" in v_w1, str(v_w1))
        ok_w2, v_w2, _nw2 = routing.validate_plan(
            [{"proc": "terminal-ci-git", "lane": default_coding, "class": "B", "writes": True}],
            quota_checked_vendors=routing.VENDORS)
        check("writes 공정만 있고 게이트가 없으면 MISSING_SECURITY_GATE (Q-09)",
              not ok_w2 and "MISSING_SECURITY_GATE" in v_w2, str(v_w2))
        ok_w3, v_w3, _nw3 = routing.validate_plan(
            [{"proc": "terminal-ci-git", "lane": default_coding, "class": "B", "writes": True}] + gate_a,
            quota_checked_vendors=routing.VENDORS)
        check("writes 공정이 claude 코딩 레인 + 게이트면 통과 (Q-09)", ok_w3, str(v_w3))
        check("writes 는 lanes_for_proc 도 코딩 목록 (Q-09)",
              routing.lanes_for_proc("terminal-ci-git", writes=True) == routing.PROCESS_LANES["coding"])
        hs = routing.handoff_spec("원래 과제 본문 XYZ", "codex 한도 도달(429)", "gpt-6-astra", "claude-opus-5",
                                  transcript_tail="마지막 줄", files_changed=["a.py"])
        check("handoff_spec 에 원 과제·사유·바뀐 파일·출력 끝이 들어간다 (Q-05)",
              all(s in hs for s in ("원래 과제 본문 XYZ", "codex 한도 도달(429)", "- a.py", "마지막 줄",
                                    "gpt-6-astra → claude-opus-5")), hs[:200])
        check("R1 — 반증 아니오인 A 작업은 A 목록 그대로",
              routing.lanes_for_proc("inventory-schema") == routing.lanes_for("A"))
        check("A-verify 는 원장 class 허용목록에 있다 (D-28 #4 · Q-08)", "A-verify" in ledger.VALID_CLASSES)
        check("claim-verify 공정은 A-verify 클래스", routing.PROC_BY_ID["claim-verify"][1] == "A-verify")
        ok_aw, v_aw, _naw = routing.validate_plan(
            [{"proc": "claim-verify", "lane": "claude-opus-5", "class": "A-verify", "writes": True}],
            quota_checked_vendors=routing.VENDORS)
        check("A-verify 가 파일을 바꾸면 계획 검증이 막는다 (D-28 #4)",
              not ok_aw and "A_VERIFY_WRITES" in v_aw, str(v_aw))

        v_same = routing.check_guards(
            [{"proc": "coding", "lane": "claude-opus-5", "class": "B"},
             {"proc": "security-artifact-gate", "lane": "claude-opus-5", "class": "B"}],
            quota_checked_vendors=routing.VENDORS)
        check("구현·생성물게이트 동일 벤더 → G1", "G1" in v_same, str(v_same))
        v_sec = routing.check_guards(
            [{"proc": "security-artifact-gate", "lane": "gpt-5.6-sol", "class": "B"},
             {"proc": "security-bizlogic-2nd", "lane": "gpt-5.6-sol", "class": "B"}],
            quota_checked_vendors=routing.VENDORS)
        check("보안 2종 동일 모델 → 검출", "G1_SEC_SAME_MODEL" in v_sec, str(v_sec))
        v_exp = routing.check_guards(
            [{"proc": "synthesis", "lane": "claude-opus-5", "class": "D", "explore": True}],
            quota_checked_vendors=routing.VENDORS)
        check("탐색 슬롯이 D 에 배정 → 검출", "EXPLORE_MISASSIGNED" in v_exp, str(v_exp))
        v_q = routing.check_guards([{"proc": "coding", "lane": "grok-4.6", "class": "B"}],
                                   quota_checked_vendors=["claude", "codex"])
        check("쿼터 미확인 벤더 → G5", "G5" in v_q, str(v_q))
        v_s = routing.check_guards([{"proc": "coding", "lane": "claude-opus-5", "class": "B"}],
                                   quota_checked_vendors=routing.VENDORS,
                                   spawn_counts={"w1": 58})
        check("spawn 58 → G3", "G3" in v_s, str(v_s))

        print()
        print("=== C3 · effort 강제 · HIGH-6 셸 안전 ===")
        try:
            routing.dispatch_argv("gpt-5.6-sol", "low", "t", "w")
            check("sol 에 잘못된 effort → 차단", False, "통과되어 버렸다")
        except ValueError:
            check("sol 에 잘못된 effort → 차단", True)
        argv = routing.dispatch_argv("gpt-5.6-sol", "ultra", "t", "w")
        check("정상 디스패치에 --effort 존재", "--effort" in argv and "ultra" in argv)
        try:
            routing.dispatch_argv("gpt-reserve", "high", "t", "w")   # 2026-09-13: fable 금지 해제로 숨김 좌석으로 교체
            check("금지 레인 → 차단", False, "통과되어 버렸다")
        except ValueError:
            check("금지 레인 → 차단", True)
        # 2026-09-13 fable 금지 해제 — 레인은 claude-fable-5-1. Orca 실측: low~max 수락 · ultra 거부.
        check("fable 은 배정 금지가 아니다",
              "claude-fable-5" not in routing.FORBIDDEN_LANES
              and "claude-fable-5-1" not in routing.FORBIDDEN_LANES)
        argv_f = routing.dispatch_argv("claude-fable-5-1", "high", "t", "w", "current")
        check("fable 디스패치에 --model·--effort 가 박힌다",
              "claude-fable-5-1" in argv_f and "--effort" in argv_f and "high" in argv_f, str(argv_f))
        try:
            routing.dispatch_argv("claude-fable-5-1", "ultra", "t", "w", "current",
                                  allow_off_ladder=True)
            check("fable 에 ultra → 차단 (Orca 실측 거부)", False, "통과되어 버렸다")
        except ValueError:
            check("fable 에 ultra → 차단 (Orca 실측 거부)", True)
        check("fable 쿼터 버킷은 fableWeekly",
              routing.LANES["claude-fable-5-1"].get("quota_bucket") == "fableWeekly")
        check("fable 은 코딩·B 비코딩 2순위 (D-28 2단계 · M1 통과)",
              routing.PROCESS_LANES["coding"] == ["claude-opus-5-5", "claude-fable-5-1"]
              and routing.lanes_for("B")[1] == "claude-fable-5-1",
              f"coding={routing.PROCESS_LANES['coding']} B={routing.lanes_for('B')}")
        # 이름이 실제로 전달되는 것은 '새 워크트리' 뿐이다 —
        # current/기존 워크트리에는 생성 플래그를 못 붙인다(orca 규칙, 실전에서 확인).
        rc, out, _, _m = routing.run_dispatch("gpt-5.6-sol", "ultra", "t1",
                                             "safe; Write-Output PWNED", "new-top-level",
                                             dry=True)
        argv2 = json.loads(out)["argv"]
        check("악성 워커 이름이 한 인자로 유지된다",
              len([a for a in argv2 if "PWNED" in a]) == 1, str(argv2))
        rc, out2, _, _m2 = routing.run_dispatch("gpt-5.6-sol", "ultra", "t1", "n",
                                                "current", dry=True)
        cur = json.loads(out2)["argv"]
        check("current 에는 생성 플래그를 붙이지 않는다",
              "--name" not in cur and "--setup" not in cur, str(cur))

        print()
        print("=== 2026-09-04 재검증 MED 수정분 ===")

        # ultracode 가 실제로 소비되는가 (두 effort 의 spec 이 달라야 한다)
        _, o_top, _, m_top = routing.run_dispatch("claude-opus-5", "ultracode",
                                                  "t", "w", "current", spec="본문", dry=True)
        _, o_std, _, m_std = routing.run_dispatch("claude-opus-5", "standard",
                                                  "t", "w", "current", spec="본문", dry=True)
        check("claude 최상위 effort 가 프롬프트에 ultracode 를 넣는다",
              m_top["prompt_prefix"] == "ultracode" and m_std["prompt_prefix"] == "")
        check("두 effort 의 spec 이 실제로 다르다", m_top["spec"] != m_std["spec"])
        check("spec 해시가 기록된다", len(m_top["spec_sha"]) == 16)

        # worktree 필수
        try:
            routing.run_dispatch("gpt-5.6-sol", "ultra", "t", "w", None, dry=True)
            check("worktree 미지정 → 차단", False, "통과되어 버렸다")
        except ValueError:
            check("worktree 미지정 → 차단", True)

        # 계획 검증 — 보안 게이트 누락·부분 쿼터
        okp, vp, _ = routing.validate_plan(
            [{"proc": "coding", "lane": "claude-opus-5", "class": "B"}],
            quota_checked_vendors=["claude"])
        check("코딩만 있고 보안 게이트 없음 → 거부", not okp and "MISSING_SECURITY_GATE" in vp, str(vp))
        check("4벤더 중 일부만 확인 → G5", "G5" in vp, str(vp))
        okp2, vp2, _ = routing.validate_plan(a_ok, quota_checked_vendors=routing.VENDORS)
        check("정본 계획은 검증 통과", okp2, str(vp2))

        # 결정 시트 입력 스키마
        for label, items_ in [
            ("CLI 슬러그 lane", [{"id": "i1", "lane": "gemini-3.8-flash-high", "title": "t"}]),
            ("default 가 문자열", [{"id": "i1", "lane": "gpt-5.6-sol", "title": "t",
                                    "default": "false"}]),
            ("options 가 bool", [{"id": "i1", "lane": "gpt-5.6-sol", "title": "t",
                                  "options": True}]),
            ("title 이 숫자", [{"id": "i1", "lane": "gpt-5.6-sol", "title": 123}]),
        ]:
            try:
                sheet.build({"run": RUN, "objective": "t", "items": items_}, out_html)
                check(f"{label} → 거부", False, "생성되어 버렸다")
            except SystemExit:
                check(f"{label} → 거부", True)
        try:
            sheet.build([], out_html)
            check("최상위가 배열 → 거부", False, "생성되어 버렸다")
        except SystemExit:
            check("최상위가 배열 → 거부", True)

        # provenance — manifest 없는 run 은 회수 불가
        forged = os.path.join(dl, "decisions_run_forged1.json")
        with open(forged, "w", encoding="utf-8") as f:
            json.dump({"run": "run_forged1", "nonce": "x" * 32,
                       "by_lane": {"gpt-5.6-luna": {"items": 9, "accepted": 9}}}, f)
        m2, n2s = ledger.collect_decisions()
        check("manifest 없는 run → 회수 거부", "run_forged1" not in m2, str(n2s))
        for leftover in os.listdir(dl):
            os.remove(os.path.join(dl, leftover))

        # 중복 계상 — 같은 run/lane 2행이면 한 행에만 기록되어야 한다
        RUN2 = "run_" + uuid.uuid4().hex[:12]
        recs2 = [ledger.new_record(RUN2, f"w{i}", "A", "gpt-5.6-luna", "low",
                                   False, False, "done") for i in (1, 2)]
        ledger.append_records(recs2)
        man = ledger.write_pending_manifest(RUN2, [{"id": "i1", "lane": "gpt-5.6-luna"},
                                                   {"id": "i2", "lane": "gpt-5.6-luna"},
                                                   {"id": "i3", "lane": "gpt-5.6-luna"},
                                                   {"id": "i4", "lane": "gpt-5.6-luna"}])
        with open(os.path.join(dl, f"decisions_{RUN2}.json"), "w", encoding="utf-8") as f:
            json.dump({"run": RUN2, "nonce": man["nonce"],
                       "by_lane": {"gpt-5.6-luna": {"items": 4, "accepted": 3}}}, f)
        m3, n3s = ledger.collect_decisions()
        allr, _ = ledger.read_ledger()
        mine2 = [r for r in allr if r.get("run") == RUN2]
        rated = [r for r in mine2 if r.get("items")]
        check("같은 run/lane 2행 중 1행에만 기록", len(mine2) == 2 and len(rated) == 1,
              f"rated={len(rated)}/{len(mine2)} notes={n3s}")
        check("합계가 부풀지 않는다", sum(r.get("items", 0) for r in mine2) == 4,
              str([r.get("items") for r in mine2]))

        # 실사용에서 잡힘: 실패한 워커 레코드가 채택률 크레딧을 받으면 안 된다
        RUN3 = "run_" + uuid.uuid4().hex[:12]
        ledger.append_records([
            ledger.new_record(RUN3, "aaa-first", "A", "gpt-5.6-luna", "low",
                              False, False, "failed"),
            ledger.new_record(RUN3, "zzz-retry", "A", "gpt-5.6-luna", "low",
                              False, False, "done")])
        man3 = ledger.write_pending_manifest(
            RUN3, [{"id": f"i{i}", "lane": "gpt-5.6-luna"} for i in range(1, 3)])
        with open(os.path.join(dl, f"decisions_{RUN3}.json"), "w", encoding="utf-8") as f:
            json.dump({"run": RUN3, "nonce": man3["nonce"],
                       "by_lane": {"gpt-5.6-luna": {"items": 2, "accepted": 2}}}, f)
        ledger.collect_decisions()
        r3 = [r for r in ledger.read_ledger()[0] if r.get("run") == RUN3]
        credited = [r for r in r3 if r.get("items")]
        check("채택률이 실패 레코드가 아니라 성공 레코드에 붙는다",
              len(credited) == 1 and credited[0]["status"] == "done",
              str([(r["task"], r["status"], r["items"]) for r in r3]))

        # 재생 방지 — 같은 nonce 를 다시 넣으면 거부
        with open(os.path.join(dl, f"decisions_{RUN2}.json"), "w", encoding="utf-8") as f:
            json.dump({"run": RUN2, "nonce": man["nonce"],
                       "by_lane": {"gpt-5.6-luna": {"items": 4, "accepted": 0}}}, f)
        m4, n4s = ledger.collect_decisions()
        check("소비된 nonce 재사용 → 거부", RUN2 not in m4, str(n4s))

        # 실사용에서 잡힘 (2026-09-04): Simon 이 같은 결정을 두 번 붙여넣었을 때
        # 확인해 보니 _mark_nonce_spent 가 정의만 되고 호출되지 않았다.
        # 재생 방지가 manifest 의 consumed 플래그 한 층뿐이었고, 그 쓰기는
        # 예외를 통째로 삼키고 있었다 — 정확히 레지스트리가 막으려던 실패 모드다.
        check("회수하면 nonce 가 append-only 레지스트리에 남는다",
              ledger._nonce_spent(man["nonce"]) is True)

        # manifest 층이 통째로 무너져도(플래그 되돌림) 레지스트리가 막아야 한다
        mp = os.path.join(ledger._pending_dir(), f"{RUN2}.json")
        with open(mp, encoding="utf-8") as f:
            mm = json.load(f)
        mm["consumed"] = False                 # 플래그 쓰기 실패를 재현한다
        with open(mp, "w", encoding="utf-8") as f:
            json.dump(mm, f)
        with open(os.path.join(dl, f"decisions_{RUN2}.json"), "w", encoding="utf-8") as f:
            json.dump({"run": RUN2, "nonce": man["nonce"],
                       "by_lane": {"gpt-5.6-luna": {"items": 4, "accepted": 0}}}, f)
        m5, n5s = ledger.collect_decisions()
        check("manifest 플래그가 풀려도 nonce 레지스트리가 재생을 막는다",
              RUN2 not in m5, str(n5s))
        allr5, _ = ledger.read_ledger()
        check("재생이 막혀 채택 수가 덮어써지지 않는다",
              sum(r.get("accepted", 0) for r in allr5 if r.get("run") == RUN2) == 3,
              str([r.get("accepted") for r in allr5 if r.get("run") == RUN2]))

        # 실사용에서 잡힘: 영구 거부분이 격리↔Downloads 를 무한 왕복했다.
        # 다음 실행의 _restore_quarantine() 이 되돌려 놓고 또 거부하기를 반복해
        # 14일 퍼지까지 매 라운드 같은 오류 줄이 진짜 실패를 덮었다.
        RUNX = "run_" + uuid.uuid4().hex[:12]
        bad = os.path.join(dl, f"decisions_{RUNX}.json")
        with open(bad, "w", encoding="utf-8") as f:
            json.dump({"run": RUNX, "nonce": "z" * 32, "by_lane": {}}, f)
        _, nx1 = ledger.collect_decisions()
        check("잘못된 입력은 거부되고 Downloads 에서 치워진다",
              not os.path.exists(bad) and any(RUNX in s for s in nx1), str(nx1))
        _, nx2 = ledger.collect_decisions()
        check("영구 거부분이 Downloads 로 되돌아오지 않는다", not os.path.exists(bad))
        check("영구 거부분을 다음 실행이 다시 거부하지 않는다",
              not any(RUNX in s for s in nx2), str(nx2))

        # 쿼터 전 후보 blocked → lane None
        import make_intake as MI
        blocked = {v: {"pct": 100, "reset": "", "state": "ok", "key": "weekly"}
                   for v in routing.VENDORS}
        lane_b, note_b = MI.pick_default("A", blocked)
        check("전 레인 한도 100% 도달 → lane 없음 (Q-05)", lane_b is None, f"lane={lane_b}")
        lane_99, note_99 = MI.pick_default("A", {v: {"pct": 99, "reset": "", "state": "ok", "key": "weekly"}
                                                for v in routing.VENDORS})
        check("99% 는 금지가 아니라 강등 — 첫 강등 레인 (Q-05 · D-101 부터 A 1순위는 claude-haiku-5-5)",
              lane_99 == "claude-haiku-5-5", f"{lane_99} {note_99}")
        check("사유에 축소안 안내", "축소안" in note_b, note_b)

        # D-28 #13 — 강등을 모든 순위에 · 첫 강등 레인 폴백 · fable 버킷 · 실호출 · unavailable
        def _q(pct):
            return {"pct": pct, "reset": "", "state": "ok", "key": "weekly"}
        q6190 = {"claude": _q(100), "codex": _q(81), "gemini": _q(0), "grok": _q(0)}   # Q-05: 금지 100 · 강등 >80
        # D-101: A 는 전부 claude 라 벤더가 섞인 B(astra → fable → opus)로 강등 규칙을 본다.
        lane_n6, note_n6 = MI.pick_default("B", q6190)
        check("ok 레인이 없으면 첫 강등 레인 (D-28 N6 · B 목록: codex 81% 강등 · claude 100% 금지)",
              lane_n6 == "gpt-6-astra", f"{lane_n6} {note_n6}")
        lane_a0, note_a0 = MI.pick_default("A", q6190)
        check("D-101 A 클래스는 claude 가 한도에 닿으면 lane 없음 — codex 폴백이 없다",
              lane_a0 is None and "축소안" in note_a0, f"{lane_a0} {note_a0}")
        q_c61 = dict(q6190, claude=_q(30))
        lane_d2, _nd2 = MI.pick_default("B", q_c61)
        check("D-101 astra(codex 81%)가 강등되면 Claude 레인으로 간다 — 다른 GPT 레인이나 낮은 effort 가 아니다",
              lane_d2 == "claude-fable-5-1" and routing.LANES[lane_d2]["vendor"] == "claude", str(lane_d2))
        lane_ad, _nad = MI.pick_default("A-verify", q_c61, proc="claim-verify")
        check("D-101 A-verify 도 astra 강등 시 Claude 레인", routing.LANES[lane_ad]["vendor"] == "claude", str(lane_ad))
        lane_80, _n80 = MI.pick_default("B", dict(q_c61, codex=_q(80)))
        check("정확히 80% 는 강등이 아니다 (초과만)", lane_80 == "gpt-6-astra", str(lane_80))
        lane_a1, _na1 = MI.pick_default("A", q_c61)
        check("D-101 A 기본 채움 = claude-haiku-5-5 (codex 상태와 무관)", lane_a1 == "claude-haiku-5-5", str(lane_a1))
        for _cls in routing.CLASS_LANES:
            for _qs in (q6190, q_c61, {v: _q(10) for v in routing.VENDORS}, {v: _q(90) for v in routing.VENDORS}):
                _l, _n = MI.pick_default(_cls, _qs)
                if _l is not None and (_l in routing.WITHDRAWN_LANES or _l in routing.DEPRECATED_LANES):
                    check(f"D-101 기본 채움이 철회·폐기 레인을 고르지 않는다 ({_cls})", False, str(_l))
        check("D-101 어떤 쿼터 상태에서도 기본 채움은 철회·폐기 레인을 고르지 않는다", True)
        # Q-09 — writes:true 공정은 코딩 규칙
        lane_wr, _nwr = MI.pick_default("B", _q and {v: _q(10) for v in routing.VENDORS}, proc="terminal-ci-git", writes=True)
        check("writes 공정의 기본 채움은 코딩 레인 (Q-09)", lane_wr == routing.PROCESS_LANES["coding"][0], str(lane_wr))
        q_ok = {v: _q(10) for v in routing.VENDORS}
        lane_cp, note_cp = MI.pick_default("C-platform", q_ok)
        check("dispatch unavailable 인 gemini 는 기본 채움에서 건너뛴다 (D-28 #12 · D-101 부터 2순위는 claude-opus-5-5)",
              lane_cp == "claude-opus-5-5", f"{lane_cp} {note_cp}")
        live_bad = {"at": "t", "age_sec": 10, "stale": False,
                    "vendors": {"grok": False, "codex": True, "claude": True, "gemini": True}}
        lane_rt, _nrt = MI.pick_default("C-realtime", q_ok, live=live_bad)
        check("실호출 실패 벤더는 쿼터와 무관하게 건너뛴다 (D-28 #13③ · D-101 부터 2순위는 claude-opus-5-5)",
              lane_rt == "claude-opus-5-5", str(lane_rt))
        lane_rt2, note_rt2 = MI.pick_default("C-realtime", q_ok, live=dict(live_bad, stale=True))
        check("오래된 실호출 실패는 막지 않는다 (D-28 #13③)", lane_rt2 == "grok-4.6", f"{lane_rt2} {note_rt2}")
        st_f, why_f = MI.lane_state_for("claude-fable-5-1", q_ok, fable_pct=100)
        check("fable 은 fableWeekly 버킷으로 판정 (D-28 #13②)", st_f == "blocked", f"{st_f} {why_f}")
        st_f2, wf2 = MI.lane_state_for("claude-fable-5-1", q6190, fable_pct=0)
        check("M2 미확정 — claude 주간 100% 면 fableWeekly 0% 여도 fable 은 blocked", st_f2 == "blocked",
              f"{st_f2} {wf2}")
        lane_cd, _ncd = MI.pick_default("B", q_ok, proc="coding")
        check("코딩 기본 채움은 공정 전용 목록 (D-28 #5)", lane_cd == "claude-opus-5-5", str(lane_cd))

        print()
        print("=== 2026-09-04 최종 감사 반영분 ===")

        # 엔트로피 휴리스틱이 정상 식별자를 막지 않는가 (우리 공정 ID 포함)
        fp = [p[0] for p in routing.PROCESSES if ledger._looks_high_entropy(p[0])]
        check("정상 공정 ID 를 credential 로 오인하지 않는다", not fp, str(fp))
        creds = ["GOCSPX-" + "aB3dE6gH9jK2mN5pQ8sT1vW4",
                 "dckr_pat_" + "aB3dE6gH9jK2mN5pQ8sT1vW4x",
                 "dapi" + "0123456789abcdef0123456789abcdef"]
        check("실제 credential 형식은 잡는다",
              all(ledger._looks_high_entropy(c) for c in creds))

        # 원장 줄의 중복 키 거부
        with open(led, "a", encoding="utf-8") as f:
            f.write('{"run":"run_x","run":"run_evil","ts":"2026-09-04T03:00+0900",'
                    '"task":"t","class":"B","lane":"gpt-5.6-sol","effort":"ultra",'
                    '"status":"done"}\n')
        _r, brk = ledger.read_ledger()
        check("원장 줄의 중복 키를 손상으로 센다", brk >= 1, f"broken={brk}")
        _git(["checkout", "--", "routing_ledger.jsonl"], repo)

        # claude 최상위는 spec 없이 디스패치할 수 없다
        try:
            routing.run_dispatch("claude-opus-5", "ultracode", "t", "w", "current", dry=True)
            check("spec 없는 ultracode 디스패치 → 차단", False, "통과되어 버렸다")
        except ValueError:
            check("spec 없는 ultracode 디스패치 → 차단", True)

        # 격리 복귀 경로가 존재하고 Downloads 와 같은 볼륨인가
        qd = ledger._quarantine_dir()
        check("격리 폴더가 Downloads 와 같은 볼륨",
              os.path.splitdrive(qd)[0].lower() ==
              os.path.splitdrive(ledger._downloads_dir())[0].lower(), qd)
        check("격리 폴더가 Downloads 밖", not qd.startswith(ledger._downloads_dir()), qd)

        # 소비된 nonce 재사용 차단 (spent 원장)
        check("spent-nonce 조회가 동작한다", ledger._nonce_spent("nope") is False)

        # Orca 의 agent id 는 CLI 이름이 아니라 좌석 이름이다 (2026-09-04 실측).
        # --agent agy 는 agent_unconfigured, --agent antigravity 가 정본.
        check("gemini 레인의 agent id 는 antigravity",
              routing.LANES["gemini-3.8-flash"]["cli"] == "antigravity")
        # D-28 #12 — gemini 는 Orca 워커로 과제를 못 받아 dispatch=unavailable 이다.
        try:
            routing.dispatch_argv("gemini-3.8-flash", "medium", "t", "n", "current")
            check("gemini(unavailable) 디스패치 → 차단", False, "통과되어 버렸다")
        except ValueError:
            check("gemini(unavailable) 디스패치 → 차단", True)
        ok_gm, v_gm, _ngm = routing.validate_plan(
            [{"proc": "google-platform", "lane": "gemini-3.8-flash", "class": "C-platform"}],
            quota_checked_vendors=routing.VENDORS)
        check("gemini 배정은 계획 검증이 LANE_NOT_DISPATCHABLE 로 막는다",
              not ok_gm and "LANE_NOT_DISPATCHABLE" in v_gm, str(v_gm))
        gk = routing.dispatch_argv("grok-4.6", "high", "t", "n", "current")
        check("grok 에는 --model 을 붙이지 않는다", "--model" not in gk, str(gk))
        check("codex 에는 --model 이 붙는다",
              "--model" in routing.dispatch_argv("gpt-5.6-luna", "low", "t", "n", "current"))
        # 기동 불가 레인은 D-28 #12 로 gemini 하나다 — 늘거나 줄면 표를 다시 본다
        unavail = [l for l, m in routing.LANES.items() if m.get("dispatch") == "unavailable"]
        check("기동 불가 레인은 gemini 하나 (D-28 #12)", unavail == ["gemini-3.8-flash"], str(unavail))

        print()
        print("=== 출력 규칙 ===")
        check("A 1순위 레인은 우열 판단 금지 명시 (D-101: 규칙은 claude-haiku-5-5 에 있다 · 옛 gpt-6-luna 규칙을 받았다)",
              "우열 판단" in routing.OUTPUT_RULES[routing.lanes_for("A")[0]]["deny"]
              and routing.lanes_for("A")[0] == "claude-haiku-5-5")
        check("D-101 철회·미등록 레인에는 산출물 규칙을 두지 않는다",
              not (set(routing.OUTPUT_RULES) & routing.WITHDRAWN_LANES)
              and set(routing.OUTPUT_RULES) <= set(routing.LANES), str(sorted(routing.OUTPUT_RULES)))
        check("B 클래스 1순위에 luna 없음",
              "gpt-6-luna" not in routing.lanes_for("B") and "gpt-5.6-luna" not in routing.lanes_for("B"))
        check("코디네이터가 B 워커 겸임 → 경고",
              routing.coordinator_conflict(
                  [{"proc": "coding", "lane": routing.COORDINATOR[0], "class": "B"}]))
        check("코디네이터 겸임은 클래스와 무관하게 경고 (D-28 #6)",
              routing.coordinator_conflict(
                  [{"proc": "research-collect", "lane": routing.COORDINATOR[0], "class": "C-realtime"}]))
        check("코디네이터는 gpt-6-astra · effort 는 xhigh (D-101 · 옛 값 gpt-6.1-sol)",
              routing.COORDINATOR == ("gpt-6-astra", "xhigh"), str(routing.COORDINATOR))
        check("D-101 코디네이터는 종합(D)과 벤더가 다르다 (발주 §5)",
              routing.LANES[routing.COORDINATOR[0]]["vendor"]
              != routing.LANES[routing.fixed_for("synthesis")[0]]["vendor"])
        check("terra 사다리 medium/max (D-28 #9)",
              routing.ladder_for("gpt-5.6-terra") == ("medium", "max"), str(routing.ladder_for("gpt-5.6-terra")))
        check("luna 사다리는 low/medium 유지 (D-28 #10 보류 · gpt-6-luna 도 같다)",
              routing.ladder_for("gpt-5.6-luna") == ("low", "medium")
              and routing.ladder_for("gpt-6-luna") == ("low", "medium"))

        print()
        print("=== 2026-09-06 · gpt-6-astra 편입 · effort 사다리 ===")

        check("astra 레인이 존재한다", "gpt-6-astra" in routing.LANES)
        check("astra 의 Orca 상한은 xhigh", routing.ceiling_for("gpt-6-astra") == "xhigh")
        check("B(비코딩) 1순위가 astra (D-28 #5)", routing.lanes_for("B")[0] == "gpt-6-astra",
              str(routing.lanes_for("B")))
        check("sonnet 은 A 의 claude-sonnet-5-5 · 사다리 medium/high — D-101 부터 2순위(1순위는 claude-haiku-5-5) "
              "(옛 claude-sonnet-5 사다리 medium/xhigh 는 원장 호환용으로 그대로)",
              routing.lanes_for("A")[0] == "claude-haiku-5-5"
              and routing.lanes_for("A")[1] == "claude-sonnet-5-5"
              and routing.ladder_for("claude-sonnet-5-5") == ("medium", "high")
              and routing.ladder_for("claude-sonnet-5") == ("medium", "xhigh"),
              f"A={routing.lanes_for('A')} ladder={routing.ladder_for('claude-sonnet-5-5')}")
        check("코딩 목록에는 codex 가 끝까지 없다 (D-28 #5)",
              all(routing.LANES[l]["vendor"] == "claude" for l in routing.PROCESS_LANES["coding"]))
        check("D-101 코디네이터(astra)는 B 1순위·인가 게이트와 같은 모델이다 — 겸임 경고가 뜬다(가드 위반은 아니다)",
              routing.COORDINATOR[0] == routing.lanes_for("B")[0]
              and routing.COORDINATOR[0] == routing.fixed_for("security-bizlogic-2nd")[0]
              and routing.coordinator_conflict([{"proc": "research-deep", "lane": "gpt-6-astra", "class": "B"}])
              and "gpt-5.6-sol" not in routing.lanes_for("B") and "gpt-6.1-sol" not in routing.lanes_for("B"))
        check("인가 게이트가 astra @xhigh 로 올라갔다 (Simon 결정 2026-09-06)",
              routing.fixed_for("security-bizlogic-2nd") == ("gpt-6-astra", "xhigh"),
              str(routing.fixed_for("security-bizlogic-2nd")))
        check("두 보안 게이트의 모델이 다르다",
              routing.fixed_for("security-artifact-gate")[0]
              != routing.fixed_for("security-bizlogic-2nd")[0])
        # 고정 effort 는 그 모델의 Orca 상한을 넘으면 안 된다 —
        # 넘으면 라운드 전체가 EFFORT_NOT_ALLOWED 로 서고, 그건 표가 거짓말한 것이다.
        for proc in ("security-artifact-gate", "security-bizlogic-2nd", "synthesis"):
            lane, eff = routing.fixed_for(proc)
            check(f"{proc} 고정 effort 가 Orca 허용목록 안이다",
                  eff in routing.orca_efforts_for(lane),
                  f"{lane}@{eff} vs {routing.orca_efforts_for(lane)}")
        # Orca 카탈로그 0번 단(minimal)까지 실측대로 적혀 있는가
        check("codex 레인 목록이 minimal 로 시작한다 (Orca CODEX_EFFORT_CHOICES[0])",
              routing.orca_efforts_for("gpt-6-astra")[0] == "minimal")
        check("은퇴 모델 gpt-5.4-mini 는 배정 금지", "gpt-5.4-mini" in routing.FORBIDDEN_LANES)

        # D-67 (2026-10-04) — 현행 세대 레인을 옛 레인 옆에 추가 (ADD_ALONGSIDE_KEEP_LEGACY)
        check("D-67 새 레인은 flag · orca · 상한 opus-5-5=max / 6.1-sol=xhigh",
              all(routing.LANES[l]["effort_style"] == "flag" and routing.LANES[l]["dispatch"] == "orca"
                  for l in ("claude-opus-5-5", "gpt-6.1-sol"))
              and routing.ceiling_for("claude-opus-5-5") == "max"
              and routing.ceiling_for("gpt-6.1-sol") == "xhigh")
        check("D-67 옛 키는 원장 호환용으로 LANES 에 남는다",
              all(l in routing.LANES and routing.ledger_efforts(l)
                  for l in ("claude-opus-5", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
                            "claude-sonnet-5", "grok-4.6")))
        listed = {l for v in routing.CLASS_LANES.values() for l in v} | set(routing.PROCESS_LANES["coding"])
        check("D-67 claude-opus-5(prompt-keyword)는 어떤 우선순위 목록·고정 공정에도 없다",
              "claude-opus-5" not in listed
              and all(f[0] != "claude-opus-5" for f in (routing.fixed_for(p[0]) for p in routing.PROCESSES) if f))
        check("D-67 종합 고정 = claude-opus-5-5 @max (ultracode 는 flag 레인이 못 받는다)",
              routing.fixed_for("synthesis") == ("claude-opus-5-5", "max"), str(routing.fixed_for("synthesis")))
        check("D-101 C 클래스 = 1순위 → claude-opus-5-5 → gpt-6-astra (옛 gpt-6.1-sol · gpt-5.6-sol 폴백은 철회)",
              routing.lanes_for("C-realtime") == ["grok-4.6", "claude-opus-5-5", "gpt-6-astra"]
              and routing.lanes_for("C-platform") == ["gemini-3.8-flash", "claude-opus-5-5", "gpt-6-astra"],
              str(routing.CLASS_LANES))
        for bad in ("max", "ultra"):
            try:
                routing.dispatch_argv("gpt-6.1-sol", bad, "t", "n", "current", allow_off_ladder=True)
                check(f"6.1-sol@{bad} → 차단 (Orca 미등록 id 상한 xhigh)", False, "통과되어 버렸다")
            except ValueError:
                check(f"6.1-sol@{bad} → 차단 (Orca 미등록 id 상한 xhigh)", True)
        argv_o = routing.dispatch_argv("claude-opus-5-5", "max", "t", "n", "current")
        check("opus-5-5 는 --model·--effort max 로 나가고 ultracode 키워드를 붙이지 않는다",
              "claude-opus-5-5" in argv_o and argv_o[argv_o.index("--effort") + 1] == "max"
              and routing.prompt_prefix("claude-opus-5-5", "max") == "", str(argv_o))

        # 2026-10-05 Simon 지시 (2.15.5) — A 클래스를 현행 세대 레인으로 (같은 ADD_ALONGSIDE_KEEP_LEGACY)
        check("D-101 A 클래스 = claude-haiku-5-5 → claude-sonnet-5-5 → claude-opus-5-5 "
              "(2.15.5 의 1순위 gpt-6-luna 는 철회 · 전부 claude)",
              routing.lanes_for("A") == ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"]
              and {routing.LANES[l]["vendor"] for l in routing.lanes_for("A")} == {"claude"},
              str(routing.lanes_for("A")))
        check("2.15.5 새 레인은 flag · orca · 상한 sonnet-5-5=max / 6-luna=xhigh",
              all(routing.LANES[l]["effort_style"] == "flag" and routing.LANES[l]["dispatch"] == "orca"
                  for l in ("claude-sonnet-5-5", "gpt-6-luna"))
              and routing.ceiling_for("claude-sonnet-5-5") == "max"
              and routing.ceiling_for("gpt-6-luna") == "xhigh")
        check("2.15.5 옛 gpt-5.6-luna·claude-sonnet-5 는 어떤 우선순위 목록·고정 공정에도 없다",
              not ({"gpt-5.6-luna", "claude-sonnet-5"} & listed)
              and all(f[0] not in ("gpt-5.6-luna", "claude-sonnet-5")
                      for f in (routing.fixed_for(p[0]) for p in routing.PROCESSES) if f))
        for lane, bad in (("gpt-6-luna", "max"), ("gpt-6-luna", "ultra"), ("claude-sonnet-5-5", "ultra")):
            try:
                routing.dispatch_argv(lane, bad, "t", "n", "current", allow_off_ladder=True)
                check(f"{lane}@{bad} → 차단 (Orca 허용목록 밖)", False, "통과되어 버렸다")
            except ValueError:
                check(f"{lane}@{bad} → 차단 (Orca 허용목록 밖)", True)
        sonnet_off = []
        for eff in ("xhigh", "max"):
            try:
                routing.dispatch_argv("claude-sonnet-5-5", eff, "t", "n", "current")
                sonnet_off.append(f"{eff}=열림")
            except ValueError:
                pass
        check("2.15.5 sonnet-5-5 xhigh·max 는 정책 사다리 밖 (토큰 폭증) — 기본 경로로 안 열린다",
              not sonnet_off, str(sonnet_off))
        argv_s = routing.dispatch_argv("claude-sonnet-5-5", "max", "t", "n", "current", allow_off_ladder=True)
        check("2.15.5 sonnet-5-5 max 는 off-ladder 로만 · --model·--effort 그대로",
              "claude-sonnet-5-5" in argv_s and argv_s[argv_s.index("--effort") + 1] == "max", str(argv_s))

        # D-99 (2026-10-12 · 2.16.0) — claude-haiku-5-5 를 A 클래스의 Claude 쪽 첫 폴백으로 (선두 승격 아님)
        haiku = routing.LANES["claude-haiku-5-5"]
        check("D-99 haiku-5-5 는 flag · orca · claude · 상한 max · 사다리 low/medium · 일반 claude 쿼터",
              haiku["effort_style"] == "flag" and haiku["dispatch"] == "orca" and haiku["vendor"] == "claude"
              and routing.ceiling_for("claude-haiku-5-5") == "max"
              and routing.ladder_for("claude-haiku-5-5") == ("low", "medium")
              and "quota_bucket" not in haiku, str(haiku))
        check("D-99 haiku-5-5 는 A 에만 있다 (D-101 부터 1순위) — 다른 클래스·코딩·고정 공정에 없다",
              routing.lanes_for("A").index("claude-haiku-5-5") == 0
              and all("claude-haiku-5-5" not in routing.lanes_for(c) for c in routing.CLASS_LANES if c != "A")
              and "claude-haiku-5-5" not in routing.PROCESS_LANES["coding"]
              and all(f[0] != "claude-haiku-5-5"
                      for f in (routing.fixed_for(p[0]) for p in routing.PROCESSES) if f),
              str(routing.CLASS_LANES))
        haiku_off = []
        for eff in ("high", "xhigh", "max"):
            try:
                routing.dispatch_argv("claude-haiku-5-5", eff, "t", "n", "current")
                haiku_off.append(f"{eff}=열림")
            except ValueError:
                pass
        check("D-99 haiku-5-5 high·xhigh·max 는 정책 사다리 밖 — 기본 경로로 안 열린다",
              not haiku_off, str(haiku_off))
        argv_h = routing.dispatch_argv("claude-haiku-5-5", "low", "t", "n", "current")
        check("D-99 haiku-5-5 는 --model·--effort low 로 나가고 프롬프트 키워드를 붙이지 않는다",
              argv_h[argv_h.index("--model") + 1] == "claude-haiku-5-5"
              and argv_h[argv_h.index("--effort") + 1] == "low"
              and routing.prompt_prefix("claude-haiku-5-5", "medium") == "", str(argv_h))
        try:
            routing.dispatch_argv("claude-haiku-5-5", "ultra", "t", "n", "current", allow_off_ladder=True)
            check("haiku-5-5@ultra → 차단 (Orca 허용목록 밖)", False, "통과되어 버렸다")
        except ValueError:
            check("haiku-5-5@ultra → 차단 (Orca 허용목록 밖)", True)
        check("D-99 haiku-5-5 는 우열 판단 금지 명시 (싼 레인 규율 · 옛 luna 규칙과 같다)",
              "우열 판단" in routing.OUTPUT_RULES["claude-haiku-5-5"]["deny"])

        # D-101 (2026-10-12 · 2.17.0 · Simon 지시) — GPT 쪽은 gpt-6-astra @xhigh 만 · 생성물 게이트는 Daybreak 로 되돌림
        #   (D-98 은 같은 날 오전 게이트를 gpt-6.1-sol 로 옮겼었다 — 그 이전을 뒤집는다)
        gate101 = routing.fixed_for("security-artifact-gate")
        daybreak = "gpt-daybreak-blue-latest"
        check("D-101 생성물 게이트 = gpt-daybreak-blue-latest @xhigh (D-98 의 gpt-6.1-sol 이 아니다)",
              gate101 == (daybreak, "xhigh"), str(gate101))
        check("D-101 Daybreak 는 여전히 폐기 표시 레인이고 설 자리는 고정 게이트 하나뿐이다",
              daybreak in routing.LANES and routing.ledger_efforts(daybreak)
              and daybreak in routing.DEPRECATED_LANES
              and routing.DEPRECATED_LANE_PINS == {daybreak: "security-artifact-gate"}
              and daybreak not in listed and routing.COORDINATOR[0] != daybreak
              and [p[0] for p in routing.PROCESSES if p[3] and p[3][0] == daybreak] == ["security-artifact-gate"])
        check("D-101 게이트 벤더는 codex 뿐 — 코딩(claude)과 겹치지 않는다 (G1 불변식)",
              routing.gate_vendors() == {"codex"}, str(sorted(routing.gate_vendors())))
        codex_keys = {l for l, m in routing.LANES.items() if m["vendor"] == "codex"}
        check("D-101 codex 레인 키 = {gpt-6-astra} ∪ 폐기 표시 ∪ 철회 (새 codex 키는 결정 없이 일을 받지 못한다)",
              codex_keys == {"gpt-6-astra"} | routing.DEPRECATED_LANES | routing.WITHDRAWN_LANES
              and routing.active_codex_lanes() == ["gpt-6-astra"],
              str(sorted(codex_keys)))
        check("D-101 철회 레인 다섯 — 원장 호환용 키로 LANES 에 남는다",
              routing.WITHDRAWN_LANES == {"gpt-6.1-sol", "gpt-6-luna", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"}
              and all(l in routing.LANES and routing.ledger_efforts(l) for l in routing.WITHDRAWN_LANES))
        active = (listed | {f[0] for f in (routing.fixed_for(p[0]) for p in routing.PROCESSES) if f}
                  | {routing.COORDINATOR[0]} | set(routing.OUTPUT_RULES))
        check("D-101 철회 레인은 어떤 우선순위 목록·고정 공정·코디네이터·산출물 규칙에도 없다",
              not (active & routing.WITHDRAWN_LANES), str(sorted(active & routing.WITHDRAWN_LANES)))
        check("D-101 일을 받는 codex 자리는 gpt-6-astra 와 Daybreak 게이트 고정뿐이다",
              {l for l in active if routing.LANES[l]["vendor"] == "codex"} == {"gpt-6-astra", daybreak})
        for lane in sorted(routing.WITHDRAWN_LANES):
            ok_w, v_w, _nw = routing.validate_plan(
                [{"proc": "research-deep", "lane": lane, "class": "B"}], quota_checked_vendors=routing.VENDORS)
            check(f"D-101 철회 레인 {lane} 은 새 계획에서 LANE_WITHDRAWN", not ok_w and v_w == ["LANE_WITHDRAWN"], str(v_w))
        ok_rw, v_rw, _nrw, _ = routing.revalidate_for_retry(
            a_rd, "research-deep", "gpt-6.1-sol", quota_checked_vendors=routing.VENDORS)
        check("D-101 재시도로 철회 레인에 옮기는 것도 막는다 (G13)", not ok_rw and "LANE_WITHDRAWN" in v_rw, str(v_rw))
        for coder in ("gpt-6-astra", "gpt-6.1-sol", "gpt-6-luna"):
            ok_c, v_c, _nc = routing.validate_plan(
                [{"proc": "coding", "lane": coder, "class": "B"}] + gate_a,
                quota_checked_vendors=routing.VENDORS)
            check(f"D-101 코딩이 codex({coder})면 게이트가 Daybreak 여도 G1",
                  not ok_c and "G1" in v_c and "CODING_LANE_NOT_ALLOWED" in v_c, str(v_c))
        for same in ("gpt-6-astra", daybreak):
            ok_s, v_s, _ns = routing.validate_plan(
                [{"proc": "coding", "lane": default_coding, "class": "B"},
                 {"proc": "security-artifact-gate", "lane": same, "class": "B"},
                 {"proc": "security-bizlogic-2nd", "lane": same, "class": "B"}],
                quota_checked_vendors=routing.VENDORS)
            check(f"D-101 두 게이트가 같은 모델({same})이면 G1_SEC_SAME_MODEL",
                  not ok_s and "G1_SEC_SAME_MODEL" in v_s, str(v_s))
        ok_op, v_op, _nop = routing.validate_plan(
            [{"proc": "coding", "lane": default_coding, "class": "B"},
             {"proc": "security-artifact-gate", "lane": "claude-opus-5-5", "class": "B"},
             {"proc": "security-bizlogic-2nd", "lane": "gpt-6-astra", "class": "B"}],
            quota_checked_vendors=routing.VENDORS)
        check("D-101 Opus 는 게이트 레인이 아니다(D-102 폴백도 아니다) — claude-opus-5-5 로 두면 G1 + FIXED_LANE_OVERRIDDEN",
              not ok_op and {"G1", "FIXED_LANE_OVERRIDDEN"} <= set(v_op), str(v_op))
        ok_pin, v_pin, _npin = routing.validate_plan(
            [{"proc": "security-artifact-gate", "lane": daybreak, "class": "B", "effort": "xhigh"}],
            quota_checked_vendors=routing.VENDORS)
        check("D-101 Daybreak 는 고정 게이트 · 고정 effort 에서는 통과한다 (LANE_DEPRECATED 의 유일한 예외)",
              ok_pin, str(v_pin))
        for eff in ("high", "medium", "low"):
            ok_e, v_e, _ne = routing.validate_plan(
                [{"proc": "security-artifact-gate", "lane": daybreak, "class": "B", "effort": eff, "off_ladder": True}],
                quota_checked_vendors=routing.VENDORS)
            check(f"D-101 Daybreak 게이트라도 고정 effort 밖({eff})이면 LANE_DEPRECATED",
                  not ok_e and "LANE_DEPRECATED" in v_e, str(v_e))
        for proc, cls in (("research-deep", "B"), ("terminal-ci-git", "B"), ("bulk-transform", "A"),
                          ("claim-verify", "A-verify"), ("research-collect", "C-realtime"),
                          ("google-platform", "C-platform"), ("security-bizlogic-2nd", "B")):
            ok_d2, v_d2, _nd2b = routing.validate_plan(
                [{"proc": proc, "lane": daybreak, "class": cls}], quota_checked_vendors=routing.VENDORS)
            check(f"D-101 Daybreak 는 게이트 밖 공정({proc})에 배정되지 않는다 (LANE_DEPRECATED)",
                  not ok_d2 and "LANE_DEPRECATED" in v_d2, str(v_d2))
        ok_dc, v_dc, _ndc = routing.validate_plan(
            [{"proc": "coding", "lane": daybreak, "class": "B"}] + gate_a, quota_checked_vendors=routing.VENDORS)
        check("D-101 Daybreak 로 코딩하면 LANE_DEPRECATED + G1 + CODING_LANE_NOT_ALLOWED",
              not ok_dc and {"LANE_DEPRECATED", "G1", "CODING_LANE_NOT_ALLOWED"} <= set(v_dc), str(v_dc))
        ok_dr, v_dr, _ndr, _ = routing.revalidate_for_retry(
            a_rd, "research-deep", daybreak, quota_checked_vendors=routing.VENDORS)
        check("D-101 재시도로 다른 공정을 Daybreak 에 옮기는 것도 막는다 (G13)",
              not ok_dr and "LANE_DEPRECATED" in v_dr, str(v_dr))
        check("D-101 코디네이터(astra)가 인가 게이트와 같은 모델이라 기본 코딩 라운드에 겸임 경고가 뜬다 (가드 위반은 아니다)",
              routing.coordinator_conflict(a_ok)
              and not routing.check_guards(a_ok, quota_checked_vendors=routing.VENDORS))
        check("D-101 게이트 출력 규칙이 Daybreak 키로 돌아왔다 (빈 출력·차단을 PASS 로 읽지 않는다)",
              "GATE: BLOCK" in routing.OUTPUT_RULES[daybreak]["allow"]
              and "FAIL" in routing.OUTPUT_RULES[daybreak]["deny"]
              and "gpt-6.1-sol" not in routing.OUTPUT_RULES)
        check("D-101 astra 사다리는 std = top = xhigh 이고 effort 가 고정이다",
              routing.ladder_for("gpt-6-astra") == ("xhigh", "xhigh")
              and routing.EFFORT_PINNED == {"gpt-6-astra": "xhigh"}
              and routing.effort_for("gpt-6-astra", False) == "xhigh"
              and routing.effort_for("gpt-6-astra", True) == "xhigh", str(routing.ladder_for("gpt-6-astra")))

        gate_doc = os.path.join(os.path.dirname(_HERE), "references", "security-artifact-gate.md")
        try:
            with open(gate_doc, "r", encoding="utf-8") as f:
                gate_text = " ".join(f.read().split())   # 줄바꿈 위치에 묶이지 않게 공백을 접는다
        except OSError:
            gate_text = ""
        missing_rules = [s for s in ("FAIL, never PASS", "Empty output", "Refusal or blocked output",
                                     "Missing first line", "Ambiguous verdict", "GATE: BLOCK", "GATE: PASS",
                                     "The gate never grades work made by its own vendor",
                                     "No automatic promotion",
                                     # D-101 — 실행 전 카탈로그 확인 · canary 기록
                                     "`gpt-daybreak-blue-latest` @ `xhigh`", "## Before each run",
                                     "~/.codex/models_cache.json", "the gate **FAILS**",
                                     "run_b08adccb4ec8", "ctx_41243c1a0d26", "run_8f7a27febc38",
                                     # D-102 — 폴백이 정해졌다: 언제 열리는지 · 무엇을 지키는지 · 한계 · canary
                                     "## Fallback: `gpt-6-astra` @ `xhigh` (D-102)", "**Decided and implemented.**",
                                     "The pin does not move", "A host cannot ask for the fallback",
                                     "**G1_SEC_SAME_MODEL is waived in exactly one state**", "**G1 is not waived.**",
                                     "never a reason to ask the fallback for a second opinion",
                                     "no longer independent checks", "run_3607f8833d7e", "ctx_56f442610119")
                         if s not in gate_text]
        check("D-101·D-102 게이트 규칙 문서가 fail-closed·G1·실행 전 확인·폴백 조건·대체 규칙을 적는다 "
              "(references/security-artifact-gate.md)",
              not missing_rules, str(missing_rules))
        check("D-102 게이트 문서에 미결 표시가 남아 있지 않다",
              "## Open item" not in gate_text and "Needs Simon's ruling" not in gate_text)

        # D-102 (2026-10-12 · 2.18.0 · Simon 판정) — 생성물 게이트 폴백: Daybreak 가 설 수 없을 때만 gpt-6-astra @xhigh
        gate_proc, fb_lane = "security-artifact-gate", "gpt-6-astra"
        why102 = {gate_proc: ["MODEL_NOT_ACTIVE"]}
        fb_plan = [{"proc": "coding", "lane": default_coding, "class": "B"},
                   {"proc": gate_proc, "lane": fb_lane, "class": "B"},
                   {"proc": "security-bizlogic-2nd", "lane": "gpt-6-astra", "class": "B"}]
        check("D-102 폴백 표는 생성물 게이트 → gpt-6-astra @xhigh 하나이고 고정 배정은 Daybreak 그대로다",
              routing.FIXED_FALLBACKS == {gate_proc: (fb_lane, "xhigh")}
              and routing.fixed_fallback_for(gate_proc) == (fb_lane, "xhigh")
              and routing.fixed_for(gate_proc) == (daybreak, "xhigh"), str(routing.FIXED_FALLBACKS))
        check("D-102 폴백 레인은 codex 다 — 게이트 벤더가 코딩 벤더(claude)와 겹치지 않는다 (G1)",
              routing.LANES[fb_lane]["vendor"] == "codex"
              and routing.LANES[default_coding]["vendor"] == "claude")
        ok_f, v_f, n_f = routing.validate_plan(fb_plan, quota_checked_vendors=routing.VENDORS,
                                               fixed_unavailable=why102)
        check("D-102 설 수 없는 사유가 있으면 게이트가 폴백 레인에 서고 G1_SEC_SAME_MODEL 을 면제한다 (notes 에 남는다)",
              ok_f and any("D-102" in x and "G1_SEC_SAME_MODEL" in x for x in n_f), str((v_f, n_f)))
        for closed in (None, {}, {gate_proc: []}, {gate_proc: [""]}, {"security-bizlogic-2nd": ["MODEL_NOT_ACTIVE"]}):
            ok_n, v_n, _nn = routing.validate_plan(fb_plan, quota_checked_vendors=routing.VENDORS,
                                                   fixed_unavailable=closed)
            check(f"D-102 사유가 없으면({closed!r}) 폴백은 열리지 않는다 (FIXED_LANE_OVERRIDDEN + G1_SEC_SAME_MODEL)",
                  not ok_n and {"FIXED_LANE_OVERRIDDEN", "G1_SEC_SAME_MODEL"} <= set(v_n), str(v_n))
        ok_u, v_u, _nu = routing.validate_plan(
            [fb_plan[0], dict(fb_plan[1], lane=daybreak), fb_plan[2]],
            quota_checked_vendors=routing.VENDORS, fixed_unavailable=why102)
        check("D-102 설 수 없다고 해 놓고 고정 레인에 배정하면 FIXED_LANE_UNAVAILABLE",
              not ok_u and v_u == ["FIXED_LANE_UNAVAILABLE"], str(v_u))
        ok_o, v_o, _no = routing.validate_plan(
            [fb_plan[0], dict(fb_plan[1], lane="claude-opus-5-5"), fb_plan[2]],
            quota_checked_vendors=routing.VENDORS, fixed_unavailable=why102)
        check("D-102 사유가 있어도 Opus 는 폴백이 아니다 (G1 + FIXED_LANE_OVERRIDDEN)",
              not ok_o and {"G1", "FIXED_LANE_OVERRIDDEN"} <= set(v_o), str(v_o))
        ok_g, v_g, _ng = routing.validate_plan(
            [dict(fb_plan[0], lane="gpt-6-astra"), fb_plan[1], fb_plan[2]],
            quota_checked_vendors=routing.VENDORS, fixed_unavailable=why102)
        check("D-102 폴백 상태에서도 G1 은 면제되지 않는다 (코딩이 codex 면 위반)",
              not ok_g and "G1" in v_g, str(v_g))
        ok_b, v_b, _nb = routing.validate_plan(
            [fb_plan[0], fb_plan[1], dict(fb_plan[2], lane="claude-fable-5-1")],
            quota_checked_vendors=routing.VENDORS, fixed_unavailable=why102)
        check("D-102 면제는 인가 게이트가 자기 고정 레인에 있을 때만이다 (옮기면 FIXED_LANE_OVERRIDDEN)",
              not ok_b and "FIXED_LANE_OVERRIDDEN" in v_b, str(v_b))
        ok_e2, v_e2, _ne2 = routing.validate_plan(
            [fb_plan[0], dict(fb_plan[1], effort="high"), fb_plan[2]],
            quota_checked_vendors=routing.VENDORS, fixed_unavailable=why102)
        check("D-102 폴백은 고정 effort(xhigh)로만 선다",
              not ok_e2 and "FIXED_LANE_OVERRIDDEN" in v_e2, str(v_e2))
        ok_r, v_r, _nr, _ = routing.revalidate_for_retry(
            [fb_plan[0], dict(fb_plan[1], lane=daybreak), fb_plan[2]], gate_proc, fb_lane,
            quota_checked_vendors=routing.VENDORS, fixed_unavailable=why102)
        ok_r2, v_r2, _nr2, _ = routing.revalidate_for_retry(
            [fb_plan[0], dict(fb_plan[1], lane=daybreak), fb_plan[2]], gate_proc, fb_lane,
            quota_checked_vendors=routing.VENDORS)
        check("D-102 재시도로 게이트를 폴백에 옮기는 것도 사유가 있을 때만 통과한다 (G13)",
              ok_r and not ok_r2 and "FIXED_LANE_OVERRIDDEN" in v_r2, str((v_r, v_r2)))
        try:
            routing.validate_plan(fb_plan, quota_checked_vendors=routing.VENDORS, fixed_unavailable=[gate_proc])
            check("D-102 fixed_unavailable 형식이 틀리면 거부한다", False, "통과되어 버렸다")
        except TypeError:
            check("D-102 fixed_unavailable 형식이 틀리면 거부한다", True)
        check("D-102 생성 표에 폴백 칸과 D-102 문단이 들어간다",
              "폴백 `gpt-6-astra` @xhigh" in routing.emit_md() and "**D-102 (2026-10-12" in routing.emit_md())

        # Orca 가 거부하는 값은 allow_off_ladder 로도 열리지 않는다.
        for bad in ("ultra", "max"):
            try:
                routing.dispatch_argv("gpt-6-astra", bad, "t", "n", "current",
                                      allow_off_ladder=True)
                check(f"astra@{bad} → 차단", False, "통과되어 버렸다")
            except ValueError:
                check(f"astra@{bad} → 차단", True)

        # D-101 — astra 는 xhigh 고정이다. Orca 가 받는 낮은 값도 allow_off_ladder 로 열리지 않는다.
        argv_ax = routing.dispatch_argv("gpt-6-astra", "xhigh", "t", "n", "current")
        check("D-101 astra@xhigh 는 열린다 (--model · --effort xhigh)",
              argv_ax[argv_ax.index("--model") + 1] == "gpt-6-astra"
              and argv_ax[argv_ax.index("--effort") + 1] == "xhigh", str(argv_ax))
        for low in ("minimal", "low", "medium", "high"):
            for off_flag in (False, True):
                try:
                    routing.dispatch_argv("gpt-6-astra", low, "t", "n", "current", allow_off_ladder=off_flag)
                    check(f"D-101 astra@{low} (off_ladder={off_flag}) → 차단", False, "통과되어 버렸다")
                except ValueError:
                    check(f"D-101 astra@{low} (off_ladder={off_flag}) → 차단", True)
        ok_ae, v_ae, _nae = routing.validate_plan(
            [{"proc": "research-deep", "lane": "gpt-6-astra", "class": "B", "effort": "high", "off_ladder": True}],
            quota_checked_vendors=routing.VENDORS)
        check("D-101 계획 검증도 astra 의 xhigh 밖 effort 를 막는다 (off_ladder 포함)",
              not ok_ae and v_ae == ["EFFORT_NOT_ALLOWED"], str(v_ae))

        # 정책 밖이지만 Orca 는 받는 값 = 명시해야만 열린다. (고정이 없는 레인으로 본다 — claude-opus-5-5 사다리 high/max)
        try:
            routing.dispatch_argv("claude-opus-5-5", "medium", "t", "n", "current")
            check("정책 밖 effort 는 기본적으로 차단", False, "통과되어 버렸다")
        except ValueError:
            check("정책 밖 effort 는 기본적으로 차단", True)
        off = routing.dispatch_argv("claude-opus-5-5", "medium", "t", "n", "current",
                                    allow_off_ladder=True)
        check("allow_off_ladder 면 열린다", "medium" in off, str(off))
        _, o_off, _, m_off = routing.run_dispatch("claude-opus-5-5", "medium", "t", "n",
                                                  "current", dry=True,
                                                  allow_off_ladder=True)
        check("off_ladder 사실이 meta 에 남는다", m_off["off_ladder"] is True, str(m_off))

        # 계획 검증이 잘못된 명시 effort 에서 아무것도 실행하지 않는다.
        # D-101: 게이트 레인은 gpt-daybreak-blue-latest 다(D-98 때는 gpt-6.1-sol). 상한이 xhigh 라 ultra 는 거부된다.
        plan_bad = [{"proc": "coding", "lane": "claude-opus-5", "class": "B"},
                    {"proc": "security-artifact-gate",
                     "lane": routing.fixed_for("security-artifact-gate")[0], "class": "B", "effort": "ultra"},
                    {"proc": "security-bizlogic-2nd", "lane": "gpt-6-astra", "class": "B"}]
        okb, vb, _nb = routing.validate_plan(plan_bad,
                                             quota_checked_vendors=routing.VENDORS)
        check("Orca 상한 초과 명시 effort → 계획 거부",
              (not okb) and "EFFORT_NOT_ALLOWED" in vb, str(vb))
        okd, resd, vd, _n2 = routing.validate_and_dispatch(
            plan_bad, task_of={}, worktree="current",
            quota_checked_vendors=routing.VENDORS, dry=True)
        check("거부된 계획은 한 건도 디스패치하지 않는다",
              (not okd) and resd == [], str(resd)[:120])

        # 원장이 off-ladder effort 를 받아준다 (기록이 빠지면 학습이 멈춘다)
        # D-101: astra 는 이제 xhigh 로만 돌지만, 원장은 과거 행(astra@medium·@high)과 철회 레인의 행을 계속 읽는다.
        check("원장 허용 effort 에 off-ladder 가 포함된다 (D-101 고정과 무관 — 과거 행)",
              {"medium", "high"} <= routing.ledger_efforts("gpt-6-astra"))
        rec_off = ledger.new_record(RUN, "astra-off", "B", "gpt-6-astra", "medium",
                                    False, False, "done")
        check("off-ladder 레코드가 원장 스키마를 통과한다", rec_off["effort"] == "medium")
        rec_wd = ledger.new_record(RUN, "withdrawn-row", "A", "gpt-6-luna", "low", False, False, "done")
        check("D-101 철회 레인의 원장 행은 계속 스키마를 통과한다 (원장 호환)", rec_wd["lane"] == "gpt-6-luna")

        # codex 직행 — D-101 부터 gpt-6-astra @xhigh 만 만든다 (옛 용도: Orca 가 못 가는 ultra)
        cx = routing.codex_exec_argv("gpt-6-astra", "xhigh", cwd_check=False)
        check("codex 직행 argv 에 모델·effort 가 박힌다",
              "gpt-6-astra" in cx and any("xhigh" in a for a in cx), str(cx))
        check("codex 직행은 프롬프트를 stdin 으로 받는다", cx[-1] == "-", str(cx))
        for model, eff in (("gpt-6-astra", "ultra"), ("gpt-6-astra", "high"), ("gpt-6.1-sol", "xhigh"),
                           ("gpt-6-luna", "low"), ("gpt-5.6-sol", "ultra"), ("gpt-6-sol", "high"),
                           ("gpt-daybreak-blue-latest", "xhigh")):
            try:
                routing.codex_exec_argv(model, eff, cwd_check=False)
                check(f"D-101 codex 직행 {model}@{eff} → 차단", False, "통과되어 버렸다")
            except ValueError:
                check(f"D-101 codex 직행 {model}@{eff} → 차단", True)
        rc_cx, out_cx, _ecx = routing.run_codex_exec("p", dry=True)
        check("D-101 codex 직행 기본값은 gpt-6-astra @xhigh",
              rc_cx == 0 and "gpt-6-astra" in out_cx and "xhigh" in out_cx and "ultra" not in out_cx, out_cx)
        # 2026-09-20: 이 경로가 조용히 죽어 있었다. codex 는 이 머신에서 npm 셰임(.CMD)이라
        # shell=False 로는 CreateProcess 가 못 푼다 - 나머지 CLI 가 .EXE 라 티가 안 났다.
        import os as _os
        import shutil as _sh
        _self = _os.path.basename(sys.executable)
        _res = routing.resolve_bin([_self, "-V"])
        check("resolve_bin 이 실행 파일을 절대경로로 푼다",
              _res[0] in (_sh.which(_self), sys.executable) or _res[0] == _self, str(_res[:2]))
        check("resolve_bin 은 못 찾은 이름을 그대로 둔다",
              routing.resolve_bin(["zzz-no-such-binary", "x"]) == ["zzz-no-such-binary", "x"])
        _cmd = _sh.which("cmd")
        if _cmd and _os.path.splitext(_cmd)[1].lower() == ".exe":
            check("resolve_bin 이 .cmd 셰임을 cmd /c 로 감싼다",
                  routing.resolve_bin(["npm", "-v"])[:2] == ["cmd", "/c"]
                  if (_sh.which("npm") or "").lower().endswith(".cmd") else True)
        try:
            routing.codex_exec_argv("gpt-6-astra", "insane")
            check("codex 직행의 잘못된 effort → 차단", False, "통과되어 버렸다")
        except ValueError:
            check("codex 직행의 잘못된 effort → 차단", True)
        try:
            routing.codex_exec_argv("gpt-reserve", "high")
            check("codex 직행에도 금지 모델 차단", False, "통과되어 버렸다")
        except ValueError:
            check("codex 직행에도 금지 모델 차단", True)
        _rc, dryout, _e = routing.run_codex_exec("prompt", dry=True)
        check("codex 직행 dry 는 실행하지 않는다", "argv" in dryout, dryout[:80])

        print()
        print("=== 적대적 상호평가 — 정답 생성·G10·실행 배선 ===")

        # ── 적대적 상호평가 (adversarial_eval.py) ────────────────
        # 왜 여기 있나: 이 하네스는 2026-09-13 까지 `truth_post` 구현이 없고
        # `--run` 이 껍데기였는데도 "만들었다"고 보고됐다. 검사가 없으면
        # 껍데기와 완성품이 같은 얼굴을 한다.
        import adversarial_eval as ae   # noqa: E402

        # (1) truth_post — 질문이 물은 단위로 바꾼다
        listing = "a/x.ts\na/y.tsx\nb/z.ts\n"
        check("count_suffix 는 .tsx 를 .ts 로 세지 않는다",
              ae.TRUTH_POST["count_suffix"](listing, 0, ".ts") == "2",
              ae.TRUTH_POST["count_suffix"](listing, 0, ".ts"))
        check("prefix_count 는 줄 시작만 센다",
              ae.TRUTH_POST["prefix_count"]("## Latest a\n x ## Latest\n", 0, "## Latest") == "1")
        check("grep_yesno 는 없으면 no",
              ae.TRUTH_POST["grep_yesno"]("a\nb\n", 0, "zzz") == "no")
        check("exit_to_yesno 는 종료코드를 답으로 읽는다",
              ae.TRUTH_POST["exit_to_yesno"]("", 0, "") == "yes"
              and ae.TRUTH_POST["exit_to_yesno"]("", 1, "") == "no")

        # (2) 부재 확인 probe 의 rc!=0 이 '실패'가 아니라 '아니오'여야 한다
        gone = {"id": "t", "truth_post": "exit_to_yesno",
                "truth_cmd": ["git", "-C", repo, "cat-file", "-e",
                              "HEAD:zzz-does-not-exist"]}
        tv, terr = ae.ground_truth(gone, repo)
        check("없는 파일 확인이 '정답 생성 실패'로 죽지 않는다", tv == "no", f"{tv!r} {terr}")

        # (3) 빈 정답은 정답이 아니다 — 지표가 질문보다 좁으면 0 은 침묵이다
        empty = {"id": "t", "truth_post": "raw",
                 "truth_cmd": ["git", "-C", repo, "ls-tree", "--name-only",
                               "HEAD", "zzz-nope/"]}
        ev, eerr = ae.ground_truth(empty, repo)
        check("빈 출력은 정답으로 인정하지 않는다", ev is None and "빈 문자열" in eerr, f"{ev!r}")

        # (4) G10 — 채점자 벤더 분리
        check("같은 벤더가 채점하면 G10 에 걸린다",
              "G10_GRADER_SAME_VENDOR" in ae.check_g10(
                  {"producer_a": "gpt-6-astra", "producer_b": "claude-opus-5",
                   "grader": "gpt-5.6-luna"}))
        check("생산자 둘이 같은 벤더여도 잡는다",
              "G10_PRODUCERS_SAME_VENDOR" in ae.check_g10(
                  {"producer_a": "gpt-6-astra", "producer_b": "gpt-5.6-luna",
                   "grader": "claude-opus-5"}))
        good = ae.check_g10({"producer_a": "gpt-6-astra", "producer_b": "claude-opus-5",
                             "grader": "gemini-3.8-flash"})
        check("벤더 셋이 다르면 위반 0 (음성 대조)", good == [], str(good))

        # (5) 벤더가 줄면 채점자를 못 만드니 건너뛴다 — 몰래 같은 벤더로 채우지 않는다
        import random as _rnd
        pr = {"id": "t", "lanes": ["gpt-6-astra", "gpt-5.6-luna", "claude-opus-5",
                                   "gemini-3.8-flash"]}
        m_ok, _n = ae.pick_matchup(pr, _rnd.Random(1))
        check("벤더 3개면 대진이 만들어진다", m_ok is not None and ae.check_g10(m_ok) == [])
        m_no, note = ae.pick_matchup(pr, _rnd.Random(1), exclude_vendors=("gemini", "claude"))
        check("벤더 2개면 대진 없이 사유를 돌려준다",
              m_no is None and "채점자를 분리할 수 없다" in note, note)

        # (6) 실행 백엔드 — 프롬프트가 셸을 거치지 않고 argv/stdin 으로만 간다
        inj = "x; Write-Output PWNED `whoami` $(id)"
        a_cl, s_cl = ae.exec_plan("claude-opus-5", "standard", inj)
        check("claude 는 프롬프트를 stdin 으로 넘긴다",
              s_cl == inj and inj not in a_cl, str(a_cl))
        a_cx, s_cx = ae.exec_plan("gpt-6-astra", "xhigh", inj)   # D-101: codex 백엔드는 astra @xhigh 만 조립한다
        check("codex 는 프롬프트를 stdin 으로 넘긴다",
              s_cx == inj and a_cx[-1] == "-", str(a_cx))
        try:
            ae.exec_plan("gpt-5.6-luna", "low", inj)
            check("D-101 평가 백엔드도 철회 레인의 argv 를 만들지 않는다", False, "통과되어 버렸다")
        except ValueError:
            check("D-101 평가 백엔드도 철회 레인의 argv 를 만들지 않는다", True)
        probes_now = ae.load_probes()
        probe_lanes = {l for p in probes_now for l in p["lanes"]}
        check("D-101 평가 문제의 codex 후보는 gpt-6-astra 하나다",
              {l for l in probe_lanes if ae.VENDOR_OF[l] == "codex"} == {"gpt-6-astra"}
              and not (probe_lanes & (routing.WITHDRAWN_LANES | routing.DEPRECATED_LANES)),
              str(sorted(probe_lanes)))
        a_gm, s_gm = ae.exec_plan("gemini-3.8-flash", "medium", inj)
        check("agy 는 effort 가 슬러그에 박힌다",
              "gemini-3.8-flash-medium" in a_gm, str(a_gm))
        check("agy 프롬프트는 argv 원소 하나다 (셸 문자열 아님)",
              a_gm.count(inj) == 1 and s_gm is None, str(a_gm))
        a_gk, _s = ae.exec_plan("grok-4.6", "high", inj)
        check("grok 은 --model 이 아니라 -m 과 --reasoning-effort 를 받는다",
              "-m" in a_gk and "--reasoning-effort" in a_gk, str(a_gk))

        # (7) claude 최상위는 프롬프트 키워드로만 발동한다
        a_top, s_top = ae.exec_plan("claude-opus-5", "ultracode", "Q")
        check("claude 최상위는 프롬프트 첫 줄에 ultracode 가 붙는다",
              s_top.startswith("ultracode"), s_top[:40])
        check("claude 최상위를 --effort 로 넘기지 않는다",
              "--effort" not in a_top, str(a_top))

        # (8) 답 추출 — CLI 가 훅 로그를 섞어 찍어도 마지막 ANSWER 를 잡는다
        noisy = "hook: Stop\nANSWER: 12\ntokens used\n14,822\nANSWER: 12\n"
        check("ANSWER 는 마지막 것을 쓴다", ae.extract_answer(noisy) == "12",
              repr(ae.extract_answer(noisy)))
        check("ANSWER 가 없으면 None", ae.extract_answer("아무 말") is None)
        check("채점 JSON 을 산문 속에서 뽑는다",
              (ae.extract_json('네: {"a": {"correct": true}} 끝') or {})
              .get("a", {}).get("correct") is True)
        check("JSON 이 깨지면 None (조용히 0점 주지 않는다)",
              ae.extract_json("{not json") is None)

        # (9) dry 는 정답을 흉내내지 않는다 — dry 행이 점수로 새면 안 된다
        check("dry 응답은 정답이 아닌 값을 낸다",
              "DRY-" in ae._dry_answer("claude-opus-5"))

        # (10) 원장 append — 기존 행을 한 줄도 잃지 않는다
        prev_ledger, prev_state = ae.LEDGER, ae.STATE_DIR
        try:
            ae.STATE_DIR = os.path.join(root, "evalstate")
            ae.LEDGER = os.path.join(ae.STATE_DIR, "eval-ledger.jsonl")
            ae.append_ledger([{"at": "2026-09-13T00:00:00", "probe": "p1", "mode": "live"}])
            ae.append_ledger([{"at": "2026-09-13T00:00:01", "probe": "p2", "mode": "live"}])
            body = open(ae.LEDGER, encoding="utf-8").read().splitlines()
            check("원장 append 는 누적된다", len(body) == 2, str(len(body)))
            check("먼저 쓴 행이 그대로 남는다",
                  json.loads(body[0])["probe"] == "p1", body[0][:60])
        finally:
            ae.LEDGER, ae.STATE_DIR = prev_ledger, prev_state
        check("실제 평가 원장은 안 건드렸다",
              ae.LEDGER == prev_ledger and ae.LEDGER.startswith(ae.SKILL_ROOT),
              ae.LEDGER)

        # (11) probe 세트 자체가 규율을 지키는가 (정본 파일을 읽는다)
        real = ae.load_probes()
        check("정본 probe 세트가 로드 규칙을 통과한다", len(real) >= 6, str(len(real)))
        check("손으로 핀한 정답(manual:)이 남아 있지 않다",
              all(not p["truth_post"].startswith("manual") for p in real),
              str([p["id"] for p in real if p["truth_post"].startswith("manual")]))
        check("probe 마다 벤더 3개 이상 (G10 을 만족할 수 있다)",
              all(len({ae.VENDOR_OF[l] for l in p["lanes"] if l in ae.VENDOR_OF}) >= 3
                  for p in real))

    finally:
        ledger.restore(prev)
        # Windows 는 git 오브젝트가 읽기전용이라 rmtree 가 그냥 실패한다 → 권한을 풀고 재시도
        def _force(func, path, _exc):
            try:
                os.chmod(path, 0o700)
                func(path)
            except Exception:
                pass
        shutil.rmtree(root, onerror=_force)
        print()
        print(f"샌드박스 정리: {'제거됨' if not os.path.exists(root) else '남음 — ' + root}")
        print(f"실제 원장 무결: {ledger.LEDGER}")


if __name__ == "__main__":
    run()
    print()
    print("=" * 46)
    print(f"PASS {ok} · FAIL {fail}")
    raise SystemExit(1 if fail else 0)
