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

    # CLI: blocked request exits 2, verify of a good file exits 0
    check("cli blocks write verb", m.main(["--task", "PR 머지해줘"]) == 2)

    print("=" * 46)
    print(f"PASS {PASS} · FAIL {FAIL}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
