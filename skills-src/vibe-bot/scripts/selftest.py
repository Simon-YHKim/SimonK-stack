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
    domain_conclusion = f"{nonce}\n결론: 가격이 올랐다 (cursor.com/pricing)"
    check("domain counts as evidence for a conclusion",
          m.verify_result(domain_conclusion, nonce) == [],
          str(m.verify_result(domain_conclusion, nonce)))

    # transport stays shut until measured
    ok, note = m.send_webhook({"nonce": nonce})
    check("webhook refused before measurement", ok is False and "실측" in note, note)
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

    # CLI: blocked request exits 2, verify of a good file exits 0
    check("cli blocks write verb", m.main(["--task", "PR 머지해줘"]) == 2)

    print("=" * 46)
    print(f"PASS {PASS} · FAIL {FAIL}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
