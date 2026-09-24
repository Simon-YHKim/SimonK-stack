#!/usr/bin/env python3
"""vibe-bot selftest - gates, spec shape, result check, transport refusal."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_bot_spec as m  # noqa: E402

PASS = FAIL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"FAIL {name} {detail}")


def main() -> int:
    # B1 secrets
    for bad in ("키는 sk-abcdefghijklmnopqrstuvwx 로 써",
                "password: hunter2 로 로그인해",
                "github token ghp_abcdefghijklmnopqrstuvwxyz12 사용"):
        check("B1 blocks secret", any("B1" in b for b in m.check_request(bad)["blocks"]), bad)

    # B2 write verbs
    for bad in ("PR 만들고 머지해줘", "프로덕션에 올려", "rm -rf build 하고 정리해",
                "요금제 결제해줘", "레포 권한을 바꾸고 공개로 전환해"):
        check("B2 blocks write", any("B2" in b for b in m.check_request(bad)["blocks"]), bad)

    # safe request passes
    ok_task = "경쟁 툴 5곳 가격 페이지를 열어 요금제와 최근 변경일을 표로 정리"
    g = m.check_request(ok_task)
    check("safe request passes", g["blocks"] == [], str(g))

    # B3 warns but does not block
    g3 = m.check_request("고객사명 기준으로 단가표를 정리")
    check("B3 warns only", g3["blocks"] == [] and any("B3" in w for w in g3["warns"]), str(g3))

    # spec shape
    nonce = m.make_nonce()
    spec = m.build_spec(ok_task, nonce)
    for sec in m.SPEC_SECTIONS:
        check(f"spec has {sec}", f"## {sec}" in spec)
    check("spec carries nonce", nonce in spec)
    check("spec demands scope", "범위 없는 '0건'" in spec)
    check("nonce shape", nonce.startswith("vb-") and len(nonce) == 11, nonce)

    # result verification
    good = f"{nonce}\n검색 범위: 5개 사이트 가격 페이지\n| 툴 | 요금 |\nhttps://example.com 근거"
    check("good result passes", m.verify_result(good, nonce) == [],
          str(m.verify_result(good, nonce)))
    check("missing nonce fails", any("B5" in f for f in m.verify_result(good, "vb-deadbeef")))
    scopeless = f"{nonce}\n결과: 해당 항목 0건"
    check("scope-less absence fails", any("G6" in f for f in m.verify_result(scopeless, nonce)))
    concl = f"{nonce}\n검색 범위: 3곳\n결론: 가격이 올랐기 때문이다"
    check("evidence-free conclusion fails", any("B4" in f for f in m.verify_result(concl, nonce)))
    leaked = f"{nonce}\n검색 범위: 3곳\n토큰: ghp_abcdefghijklmnopqrstuvwxyz12"
    check("leaked credential fails", any("B1" in f for f in m.verify_result(leaked, nonce)))

    # 2026-09-19 pilot: each absence row carries its own source column
    pilot = (f"{nonce}\n| 도구 | 최근 변경일 | 출처 |\n"
             "| Claude Code | 페이지에 변경일 없음 | claude.com/pricing |\n"
             "| Cursor | 페이지에 변경일 없음 | cursor.com/pricing |")
    check("row-level source scopes absence", m.verify_result(pilot, nonce) == [],
          str(m.verify_result(pilot, nonce)))
    unsourced = pilot + "\n| Gemini CLI | 페이지에 변경일 없음 | |"
    check("absence row without source still fails",
          any("G6" in f for f in m.verify_result(unsourced, nonce)))
    counted = f"{nonce}\n5곳 모두 공개 가격 페이지에서 확인했고 변경일은 없었습니다"
    check("counted places scope absence", m.verify_result(counted, nonce) == [],
          str(m.verify_result(counted, nonce)))
    header_scope = f"{nonce}\n검색 범위: 가격 페이지 5곳\n결과: 변경일 0건"
    check("scope on another line still passes", m.verify_result(header_scope, nonce) == [],
          str(m.verify_result(header_scope, nonce)))
    # 0.7.0 - measured on the rly-d16843d2 probe: a status line about the bot's own action
    # not failing is not a finding-absence.
    own_status = (f"{nonce}\n- 봇 이름: Relay\n- 도구: PowerShell Set-Content\n"
                  "- 쓰기 실패 여부: (작성 시점에는 실패 없음)")
    check("own-action status line is not a scope-less absence",
          m.verify_result(own_status, nonce) == [], str(m.verify_result(own_status, nonce)))
    mixed = own_status + "\n- 취약점 0건"
    check("a real finding-absence still fails next to a status line",
          any("G6" in f for f in m.verify_result(mixed, nonce)))
    # 0.7.0 - measured on vb-78dadec4: this bus is files, so a local path scopes a line
    # exactly the way a URL does.
    path_scoped = (f"{nonce}\n- E:\\2ndB\\.bots\\relay\\inbox\\ - 읽힘 "
                   "(직전 실행에서 폴더 없음이었던 경로가 이번 턴에 존재)")
    check("a local path scopes an absence line",
          m.verify_result(path_scoped, nonce) == [], str(m.verify_result(path_scoped, nonce)))
    posix_scoped = f"{nonce}\n- src/app/index.tsx 에서 그 호출은 없음"
    check("a posix path scopes an absence line too",
          m.verify_result(posix_scoped, nonce) == [], str(m.verify_result(posix_scoped, nonce)))
    bare = f"{nonce}\n- 해당 설정 없음"
    check("an absence with neither path nor source still fails",
          any("G6" in f for f in m.verify_result(bare, nonce)))
    # 0.7.0 - the sheet template's own section: every line under it is self-conduct.
    did_not = f"{nonce}\n## 안 한 일\n- 봇 답 대필/날조 없음\n- inbox 원본 삭제 없음"
    check("lines under 안 한 일 are conduct, not findings",
          m.verify_result(did_not, nonce) == [], str(m.verify_result(did_not, nonce)))
    finding_section = f"{nonce}\n## 안 한 일\n- 삭제 없음\n## 발견\n- 취약점 0건"
    check("a finding section after it is still checked",
          any("G6" in f for f in m.verify_result(finding_section, nonce)))
    # 0.7.0 - the sheet template asks for 막힌 것, so "막힘: 없음" is our own vocabulary
    # reporting a clear run. Measured on vb-acda474d.
    blocked_none = f"{nonce}\n⑤ 막힘: 없음. 루틴 패널에서 읽어 기록했다"
    check("막힘 없음 is a run status, not a finding-absence",
          m.verify_result(blocked_none, nonce) == [], str(m.verify_result(blocked_none, nonce)))
    # One wake is this system's unit of observation, so naming it is naming a scope.
    turn_scope = f"{nonce}\n이번 프롬프트에 webhook_event 블록 없음 (웹훅 기동이면 포함된다)"
    check("이번 턴/프롬프트 counts as a scope",
          m.verify_result(turn_scope, nonce) == [], str(m.verify_result(turn_scope, nonce)))
    still = f"{nonce}\n결과: 해당 항목 0건"
    check("a bare absence is still caught after those two",
          any("G6" in f for f in m.verify_result(still, nonce)))
    domain_conclusion = f"{nonce}\n결론: 가격이 올랐다 (cursor.com/pricing)"
    check("domain counts as evidence for a conclusion",
          m.verify_result(domain_conclusion, nonce) == [],
          str(m.verify_result(domain_conclusion, nonce)))

    # transport stays shut until measured
    ok, note = m.send_webhook({"nonce": nonce})
    check("legacy webhook cannot bypass the central gate", ok is False and "LEGACY_BOT_DELIVERY_DISABLED" in note, note)
    argv = m.webhook_argv("https://example.invalid/hook")
    check("key never inlined in argv", all("crsr_" not in x for x in argv)
          and any(m.WEBHOOK_KEY_ENV in x for x in argv), str(argv))

    # console mode (2026-09-19, Simon): explicit sheet + screen evidence + irreversible escalation
    cspec = m.build_console_spec("출시 트랙별 최신 버전과 상태를 읽는다", nonce,
                                 target="Google Play Console · com.simonk.secondbrain",
                                 url="https://play.google.com/console")
    for sec in m.CONSOLE_SECTIONS:
        check(f"console spec has {sec}", f"## {sec}" in cspec)
    check("console spec is read-only by default", "읽기 전용" in cspec)
    check("console spec forbids Resubmit", "Resubmit" in cspec)
    check("console spec carries nonce and start URL",
          nonce in cspec and "https://play.google.com/console" in cspec)
    cspec2 = m.build_console_spec("x", nonce, target="t", allow_change="스토어 설명 첫 문단 교체",
                                  extra_forbid=["프로모션 코드 발급"])
    check("allow-change is spelled out and still stops for approval",
          "허용 변경: 스토어 설명 첫 문단 교체" in cspec2 and "사람 승인" in cspec2)
    check("extra forbid is listed", "- 프로모션 코드 발급" in cspec2)
    good_c = (f"{nonce}\n| 항목 | 값 | 화면 경로 | 스크린샷 |\n"
              "| 프로덕션 | 0.8.0 (40) | 출시 > 프로덕션 | shot1.png |")
    check("console result with path passes", m.verify_result(good_c, nonce, mode="console") == [],
          str(m.verify_result(good_c, nonce, mode="console")))
    no_ev = f"{nonce}\n프로덕션 트랙 버전은 0.8.0 입니다"
    check("console result without screen evidence fails C1",
          any("C1" in f for f in m.verify_result(no_ev, nonce, mode="console")))
    pressed = good_c + "\n요청대로 Resubmit 눌렀습니다"
    check("reported irreversible press escalates C2",
          any("C2" in f for f in m.verify_result(pressed, nonce, mode="console")))
    for said in ("검토 답변도 보냈습니다", "새 AAB 업로드 완료", "회신했습니다"):
        check(f"Korean irreversible report escalates C2: {said}",
              any("C2" in f for f in m.verify_result(good_c + "\n" + said, nonce, mode="console")))
    held = good_c + "\nReply 버튼은 누르지 않았고 제출하지 않았다"
    check("negated press does not trigger C2",
          not any("C2" in f for f in m.verify_result(held, nonce, mode="console")),
          str(m.verify_result(held, nonce, mode="console")))
    check("general mode ignores C1 and C2", m.verify_result(no_ev, nonce) == [],
          str(m.verify_result(no_ev, nonce)))
    check("cli console mode without --target exits 2",
          m.main(["--mode", "console", "--task", "출시 트랙 상태를 읽어 표로 정리"]) == 2)

    # roster + hub bus (0.4.0)
    import tempfile
    roster = m.load_roster()
    ids = {b["id"] for b in roster}
    check("roster has 19 reported bots", len(roster) == 19, str(sorted(ids)))
    check("relay is the default intake", "relay" in ids
          and next(b for b in roster if b["id"] == "relay").get("default"))
    # 0.7.0 B8 - Simon's boundary: /vibe keeps CLI work, bots get screens.
    for phrase, why in [("eas submit 로 스토어에 올려줘", "eas-cli"),
                        ("gh pr 목록을 정리해줘", "git / gh"),
                        ("npm run verify 돌려줘", "node / npm"),
                        ("supabase functions deploy 해줘", "supabase cli"),
                        ("터미널에서 상태를 확인해줘", "shell")]:
        check(f"B8 warns on CLI work ({why})",
              any("B8" in w for w in m.check_request(phrase)["warns"]), phrase)
    check("a screen task draws no B8",
          not any("B8" in w for w in m.check_request(
              "Play Console 데이터 보안 양식 화면에서 선언 상태를 읽어 표로 정리")["warns"]))
    check("play console target routes to play-console",
          (m.resolve_bot(roster, "Google Play Console · com.simonk.secondbrain", "") or {}).get("id")
          == "play-console")
    check("app store connect routes to apple-dev",
          (m.resolve_bot(roster, "App Store Connect · 6792266942", "심사 상태 확인") or {}).get("id")
          == "apple-dev")
    check("unknown work falls back to the default bot",
          (m.resolve_bot(roster, "", "아무 일이나 해줘") or {}).get("id") == "relay")
    # 0.7.0 - measured 2026-09-20: the task prose named another bot's tool and stole the sheet.
    check("the console in --target beats a tool name in the task prose",
          (m.resolve_bot(roster, "App Store Connect · 2nd Brain · 6792266942",
                         "Auto Review 허용목록에 eas submit 이 있어서 제출 이력을 확인한다",
                         url="https://appstoreconnect.apple.com/apps") or {}).get("id") == "apple-dev")
    check("a task that really is EAS work still routes to eas",
          (m.resolve_bot(roster, "EAS · expo 빌드 목록", "eas submit 상태 확인") or {}).get("id") == "eas")
    check("explicit --bot by name wins",
          (m.resolve_bot(roster, "Google Play Console", "", explicit="QA") or {}).get("id") == "qa")
    check("unknown explicit bot returns None", m.resolve_bot(roster, "", "", explicit="nope") is None)
    with tempfile.TemporaryDirectory() as hub:
        rc = m.main(["--mode", "console", "--target", "Google Play Console · com.simonk.secondbrain",
                     "--task", "출시 트랙 상태를 읽어 표로 정리", "--deliver", "hub",
                     "--hub", hub, "--out", hub])
        check("legacy hub delivery is refused before writing", rc == 2 and list(Path(hub).iterdir()) == [])
        # Synthetic consumer fixtures only; never call a live publishing path.
        n = "vb-00000042"
        fixture_paths = m.hub_paths(next(b for b in roster if b["id"] == "play-console"), n, Path(hub))
        fixture_paths["inbox"].parent.mkdir(parents=True)
        fixture_paths["result"].parent.mkdir(parents=True)
        fixture_paths["inbox"].write_text(m.add_routing(m.build_console_spec(
            "출시 트랙 상태를 읽어 표로 정리", n, target="Google Play Console"),
            next(b for b in roster if b["id"] == "play-console"), fixture_paths["result"]), encoding="utf-8")
        fixture_paths["meta"].write_text('{"mode":"console"}', encoding="utf-8")
        inbox = sorted(Path(hub, "bots", "relay", "inbox").glob("vb-*.md"))
        check("sheet lands only in the relay inbox", len(inbox) == 1, str(inbox))
        n = inbox[0].stem if inbox else "vb-none"
        sheet = inbox[0].read_text(encoding="utf-8") if inbox else ""
        check("sheet names the bot and the result file",
              "전달: Relay" in sheet and "(play-console)" in sheet
              and f"{n}.result.md" in sheet)
        out = Path(hub, "bots", "relay", "outbox")
        (out / f"{n}.result.md").write_text(
            f"{n}\n| 항목 | 값 | 화면 경로 | 스크린샷 |\n| 프로덕션 | 0.8.0 | 출시 > 프로덕션 | s.png |",
            encoding="utf-8")
        rows = m.collect(Path(hub))
        check("collect finds the result and passes it",
              len(rows) == 1 and rows[0]["findings"] == [] and rows[0]["mode"] == "console", str(rows))
        (out / f"{n}.result.md").write_text(f"{n}\n검토 답변도 보냈습니다", encoding="utf-8")
        rows = m.collect(Path(hub))
        check("collect re-checks with console rules (C1 and C2)",
              bool(rows) and any("C2" in f for f in rows[0]["findings"])
              and any("C1" in f for f in rows[0]["findings"]), str(rows))

    # shared bots + per-task project bus (0.6.0)
    projects = m.load_projects()
    check("2nd-b project root is E:/2ndB", projects.get("2nd-b", {}).get("root", "") == "E:/2ndB",
          str(projects))
    pc = next(b for b in roster if b["id"] == "play-console")
    check("bots carry no project tag - they are shared",
          all("project" not in b for b in roster), str([b["id"] for b in roster if "project" in b]))
    check("2nd-B words pick the 2nd-b project",
          m.resolve_project(projects, "Google Play Console · com.simonk.secondbrain", "") == "2nd-b")
    check("a task with no project words stays on the hub",
          m.resolve_project(projects, "", "경쟁 툴 가격 정리") is None)
    check("explicit --project wins", m.resolve_project(projects, "", "", explicit="2nd-b") == "2nd-b")
    check("unknown explicit project is rejected",
          m.resolve_project(projects, "", "", explicit="nope") is None)
    with tempfile.TemporaryDirectory() as hub2, tempfile.TemporaryDirectory() as proot:
        pj = {"2nd-b": {"root": proot, "bus": ".bots"}}
        check("project task lands under the project root",
              m.bus_root(Path(hub2), pj, "2nd-b") == Path(proot) / ".bots")
        check("no project means the shared hub", m.bus_root(Path(hub2), pj, None) == Path(hub2) / "bots")
        p = m.hub_paths(pc, "vb-00000001", Path(hub2), pj, "2nd-b")
        p["result"].parent.mkdir(parents=True, exist_ok=True)
        p["result"].write_text("vb-00000001\n검색 범위: 트랙 3곳\n| 트랙 | 0.8.0 |", encoding="utf-8")
        rows = m.collect(Path(hub2), projects=pj)
        check("collect scans project buses too",
              len(rows) == 1 and rows[0]["bot"] == "relay", str(rows))
        routed = m.add_routing("# t\nline2\nbody", pc, p["result"], ("2nd-b", proot))
        check("sheet names the project and its root", f"프로젝트: 2nd-b · 루트 {proot}" in routed)

    # CLI: blocked request exits 2, verify of a good file exits 0
    check("cli blocks write verb", m.main(["--task", "PR 머지해줘"]) == 2)

    print("=" * 46)
    print(f"PASS {PASS} · FAIL {FAIL}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
