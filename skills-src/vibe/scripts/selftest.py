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
              routing.lanes_for("A-verify") == ["gpt-6-astra", "claude-fable-5-1", "claude-opus-5"],
              str(routing.lanes_for("A-verify")))
        gate_a = [{"proc": "security-artifact-gate", "lane": routing.fixed_for("security-artifact-gate")[0], "class": "B"},
                  {"proc": "security-bizlogic-2nd", "lane": routing.fixed_for("security-bizlogic-2nd")[0], "class": "B"}]
        ok_w1, v_w1, _nw1 = routing.validate_plan(
            [{"proc": "terminal-ci-git", "lane": "gpt-6-astra", "class": "B", "writes": True}] + gate_a,
            quota_checked_vendors=routing.VENDORS)
        check("writes 공정이 codex 면 G1 + CODING_LANE_NOT_ALLOWED (Q-09)",
              not ok_w1 and "G1" in v_w1 and "CODING_LANE_NOT_ALLOWED" in v_w1, str(v_w1))
        ok_w2, v_w2, _nw2 = routing.validate_plan(
            [{"proc": "terminal-ci-git", "lane": "claude-opus-5", "class": "B", "writes": True}],
            quota_checked_vendors=routing.VENDORS)
        check("writes 공정만 있고 게이트가 없으면 MISSING_SECURITY_GATE (Q-09)",
              not ok_w2 and "MISSING_SECURITY_GATE" in v_w2, str(v_w2))
        ok_w3, v_w3, _nw3 = routing.validate_plan(
            [{"proc": "terminal-ci-git", "lane": "claude-opus-5", "class": "B", "writes": True}] + gate_a,
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
              routing.PROCESS_LANES["coding"] == ["claude-opus-5", "claude-fable-5-1"]
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
        check("99% 는 금지가 아니라 강등 — 첫 강등 레인 (Q-05)", lane_99 == "gpt-5.6-luna", f"{lane_99} {note_99}")
        check("사유에 축소안 안내", "축소안" in note_b, note_b)

        # D-28 #13 — 강등을 모든 순위에 · 첫 강등 레인 폴백 · fable 버킷 · 실호출 · unavailable
        def _q(pct):
            return {"pct": pct, "reset": "", "state": "ok", "key": "weekly"}
        q6190 = {"claude": _q(100), "codex": _q(81), "gemini": _q(0), "grok": _q(0)}   # Q-05: 금지 100 · 강등 >80
        lane_n6, note_n6 = MI.pick_default("A", q6190)
        check("ok 레인이 없으면 첫 강등 레인 (D-28 N6)", lane_n6 == "gpt-5.6-luna", f"{lane_n6} {note_n6}")
        q_c61 = dict(q6190, claude=_q(30))
        lane_d2, _nd2 = MI.pick_default("A", q_c61)
        check("1순위 81% 면 ok 인 2순위로 강등 (Q-05 강등선 80)", lane_d2 == "claude-sonnet-5", str(lane_d2))
        lane_80, _n80 = MI.pick_default("A", dict(q_c61, codex=_q(80)))
        check("정확히 80% 는 강등이 아니다 (초과만)", lane_80 == "gpt-5.6-luna", str(lane_80))
        # Q-09 — writes:true 공정은 코딩 규칙
        lane_wr, _nwr = MI.pick_default("B", _q and {v: _q(10) for v in routing.VENDORS}, proc="terminal-ci-git", writes=True)
        check("writes 공정의 기본 채움은 코딩 레인 (Q-09)", lane_wr == routing.PROCESS_LANES["coding"][0], str(lane_wr))
        q_ok = {v: _q(10) for v in routing.VENDORS}
        lane_cp, note_cp = MI.pick_default("C-platform", q_ok)
        check("dispatch unavailable 인 gemini 는 기본 채움에서 건너뛴다 (D-28 #12)",
              lane_cp == "gpt-5.6-sol", f"{lane_cp} {note_cp}")
        live_bad = {"at": "t", "age_sec": 10, "stale": False,
                    "vendors": {"grok": False, "codex": True, "claude": True, "gemini": True}}
        lane_rt, _nrt = MI.pick_default("C-realtime", q_ok, live=live_bad)
        check("실호출 실패 벤더는 쿼터와 무관하게 건너뛴다 (D-28 #13③)", lane_rt == "gpt-5.6-sol", str(lane_rt))
        lane_rt2, note_rt2 = MI.pick_default("C-realtime", q_ok, live=dict(live_bad, stale=True))
        check("오래된 실호출 실패는 막지 않는다 (D-28 #13③)", lane_rt2 == "grok-4.6", f"{lane_rt2} {note_rt2}")
        st_f, why_f = MI.lane_state_for("claude-fable-5-1", q_ok, fable_pct=100)
        check("fable 은 fableWeekly 버킷으로 판정 (D-28 #13②)", st_f == "blocked", f"{st_f} {why_f}")
        st_f2, wf2 = MI.lane_state_for("claude-fable-5-1", q6190, fable_pct=0)
        check("M2 미확정 — claude 주간 100% 면 fableWeekly 0% 여도 fable 은 blocked", st_f2 == "blocked",
              f"{st_f2} {wf2}")
        lane_cd, _ncd = MI.pick_default("B", q_ok, proc="coding")
        check("코딩 기본 채움은 공정 전용 목록 (D-28 #5)", lane_cd == "claude-opus-5", str(lane_cd))

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
        check("luna 는 우열 판단 금지 명시",
              "우열 판단" in routing.OUTPUT_RULES["gpt-5.6-luna"]["deny"])
        check("B 클래스 1순위에 luna 없음", "gpt-5.6-luna" not in routing.lanes_for("B"))
        check("코디네이터가 B 워커 겸임 → 경고",
              routing.coordinator_conflict(
                  [{"proc": "coding", "lane": "gpt-5.6-sol", "class": "B"}]))
        check("코디네이터 겸임은 클래스와 무관하게 경고 (D-28 #6)",
              routing.coordinator_conflict(
                  [{"proc": "research-collect", "lane": routing.COORDINATOR[0], "class": "C-realtime"}]))
        check("코디네이터 effort 는 xhigh (D-28 #8)",
              routing.COORDINATOR == ("gpt-5.6-sol", "xhigh"), str(routing.COORDINATOR))
        check("terra 사다리 medium/max (D-28 #9)",
              routing.ladder_for("gpt-5.6-terra") == ("medium", "max"), str(routing.ladder_for("gpt-5.6-terra")))
        check("luna 사다리는 low/medium 유지 (D-28 #10 보류)",
              routing.ladder_for("gpt-5.6-luna") == ("low", "medium"))

        print()
        print("=== 2026-09-06 · gpt-6-astra 편입 · effort 사다리 ===")

        check("astra 레인이 존재한다", "gpt-6-astra" in routing.LANES)
        check("astra 의 Orca 상한은 xhigh", routing.ceiling_for("gpt-6-astra") == "xhigh")
        check("B(비코딩) 1순위가 astra (D-28 #5)", routing.lanes_for("B")[0] == "gpt-6-astra",
              str(routing.lanes_for("B")))
        check("sonnet 은 A 2순위 · 사다리 medium/xhigh (D-28 #2·#3 · M1 통과)",
              routing.lanes_for("A")[1] == "claude-sonnet-5"
              and routing.ladder_for("claude-sonnet-5") == ("medium", "xhigh"),
              f"A={routing.lanes_for('A')} ladder={routing.ladder_for('claude-sonnet-5')}")
        check("코딩 목록에는 codex 가 끝까지 없다 (D-28 #5)",
              all(routing.LANES[l]["vendor"] == "claude" for l in routing.PROCESS_LANES["coding"]))
        check("코디네이터(sol)가 B 목록에 없다 — 겸임이 구조적으로 불가",
              "gpt-5.6-sol" not in routing.lanes_for("B"))
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

        # Orca 가 거부하는 값은 allow_off_ladder 로도 열리지 않는다.
        for bad in ("ultra", "max"):
            try:
                routing.dispatch_argv("gpt-6-astra", bad, "t", "n", "current",
                                      allow_off_ladder=True)
                check(f"astra@{bad} → 차단", False, "통과되어 버렸다")
            except ValueError:
                check(f"astra@{bad} → 차단", True)

        # 정책 밖이지만 Orca 는 받는 값 = 명시해야만 열린다.
        try:
            routing.dispatch_argv("gpt-6-astra", "medium", "t", "n", "current")
            check("정책 밖 effort 는 기본적으로 차단", False, "통과되어 버렸다")
        except ValueError:
            check("정책 밖 effort 는 기본적으로 차단", True)
        off = routing.dispatch_argv("gpt-6-astra", "medium", "t", "n", "current",
                                    allow_off_ladder=True)
        check("allow_off_ladder 면 열린다", "medium" in off, str(off))
        _, o_off, _, m_off = routing.run_dispatch("gpt-6-astra", "medium", "t", "n",
                                                  "current", dry=True,
                                                  allow_off_ladder=True)
        check("off_ladder 사실이 meta 에 남는다", m_off["off_ladder"] is True, str(m_off))

        # 계획 검증이 잘못된 명시 effort 에서 아무것도 실행하지 않는다.
        plan_bad = [{"proc": "coding", "lane": "claude-opus-5", "class": "B"},
                    {"proc": "security-artifact-gate",
                     "lane": "gpt-daybreak-blue-latest", "class": "B", "effort": "ultra"},
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
        check("원장 허용 effort 에 off-ladder 가 포함된다",
              "medium" in routing.ledger_efforts("gpt-6-astra"))
        rec_off = ledger.new_record(RUN, "astra-off", "B", "gpt-6-astra", "medium",
                                    False, False, "done")
        check("off-ladder 레코드가 원장 스키마를 통과한다", rec_off["effort"] == "medium")

        # codex 직행 — Orca 가 못 가는 ultra 로 갈 수 있는 유일한 길
        cx = routing.codex_exec_argv("gpt-6-astra", "ultra", cwd_check=False)
        check("codex 직행 argv 에 모델·effort 가 박힌다",
              "gpt-6-astra" in cx and any("ultra" in a for a in cx), str(cx))
        check("codex 직행은 프롬프트를 stdin 으로 받는다", cx[-1] == "-", str(cx))
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
        a_cx, s_cx = ae.exec_plan("gpt-5.6-luna", "low", inj)
        check("codex 는 프롬프트를 stdin 으로 넘긴다",
              s_cx == inj and a_cx[-1] == "-", str(a_cx))
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
