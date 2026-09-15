# split.py — SIMON 지침 단일본 → 환경별 사본 생성기
#
# 정본은 SIMON_지침_v8.1_단일본.md **하나뿐**이다. 사본은 전부 이 스크립트의 산출물이고
# 손으로 고치지 않는다(§0-2). 사본을 고쳐야 할 일이 생기면 단일본을 고치고 다시 만든다.
#
# 사용:
#   python split.py                 사본 생성 (out/)
#   python split.py --check         사본 머리말 sha 와 단일본 실제 sha 대조   [완료조건 7]
#   python split.py --refs          사본 안의 끊긴 §N 상호참조 검출          [완료조건 8]
#   python split.py --verify        --check + --refs + 절 구성 검사를 한 번에
#   python split.py --apply         ~/.claude/CLAUDE.md 를 백업 후 교체
#
# 2026-09-10 신설. 그 전까지 이 스크립트는 어디에도 상주하지 않아 아무도 찾지 못했다
# (Q-260830-02, 11일 이월). 이제 이 저장소가 상주 위치다.
import argparse
import hashlib
import os
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "SIMON_지침_v8.1_단일본.md")
OUTDIR = os.path.join(HERE, "out")
KST = timezone(timedelta(hours=9))

# ── 절 → 자리 배정 ───────────────────────────────────────────────
#  GLOBAL 이 '전역 범위 판정'이다. §0 이 여기 들어 있어야 모든 사본에 실린다.
#  (v8.1 에서 §0 을 추가했다. 그 전에는 {1..6} 이었다.)
GLOBAL = list(range(0, 7))          # §0~§6 — 어느 환경에서나 읽는다
ENV_ONLY = {7: "Claude Code", 8: "Cowork"}

TARGETS = {
    "profile_§0-6": {
        "sections": GLOBAL,
        "place": "claude.ai → 설정 → 개인 프로필 지침",
    },
    "claude-code_§0-7": {
        "sections": GLOBAL + [7],
        "place": "~/.claude/CLAUDE.md (Claude Code 사용자 메모리)",
        "apply_to": os.path.join(os.path.expanduser("~"), ".claude", "CLAUDE.md"),
    },
    # 2026-09-10 Simon 실측으로 B안 확정 (Q-260830-01 해소, 11일 이월 끝).
    #   판정: Cowork 세션에 "로드된 지침에 '📌 채팅 제목' 규칙이 몇 번 나오나?" → **1**.
    #   2 였으면 claude.ai 프로필이 Cowork 에도 실린다는 뜻이라 §8 만 보내면 됐다(A안).
    #   1 이므로 프로필은 Cowork 에 닿지 않는다 → Cowork 가 전역 절을 직접 들고 간다.
    #   A안 사본은 이 결정으로 폐기했다. 되살릴 일이 생기면 이 주석부터 읽을 것.
    "cowork_§0-6+§8": {
        "sections": GLOBAL + [8],
        "place": "Cowork → 상시 지시사항",
    },
}

SEC_RE = re.compile(r"(?m)^(?=## \d+\.)")
HEAD_RE = re.compile(r"## (\d+)\.")
# 사본 머리말의 sha 를 되읽는 자리. --check 가 이 값을 실제 sha 와 대조한다.
HEADER_SHA_RE = re.compile(r"sha256 ([0-9a-f]{12})")
# 본문 안의 절 상호참조. §3-1 같은 하위 번호도 §3 으로 센다.
REF_RE = re.compile(r"§(\d)")


def read_source():
    if not os.path.exists(SOURCE):
        sys.exit(f"단일본이 없다: {SOURCE}")
    with open(SOURCE, encoding="utf-8", newline="") as f:
        text = f.read()
    return text


def sha12(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def parse(text):
    """머리말과 절을 가른다.

    ⚠ 머리말 경계를 '첫 `## <숫자>.` 이전 전부'로 잡는다. '`## 1.` 이전'으로 잡으면
      §0 이 머리말에 흡수돼 사본에서 사라진다 — 2026-09-10 설계 검토에서 지목된 위험이다.
      아래 단언이 그 실수를 다시 못 하게 막는다.
    """
    parts = SEC_RE.split(text)
    pre = parts[0]
    secs = {}
    for p in parts[1:]:
        secs[int(HEAD_RE.match(p).group(1))] = p.rstrip("\n") + "\n"
    if 0 not in secs:
        sys.exit("§0 을 찾지 못했다 — 머리말 경계 판정이 §0 을 삼켰을 수 있다")
    if HEAD_RE.search(pre):
        sys.exit("머리말에 절 헤더가 남아 있다 — 경계 판정이 깨졌다")
    return pre, secs


def header_for(name, spec, src_sha, stamp, secs):
    """사본 머리에 붙는 3줄. 형식은 §0-2 가 정한다."""
    have = spec["sections"]
    missing = [n for n in sorted(secs) if n not in have]
    where = []
    for n in missing:
        where.append(f"§{n}은 {ENV_ONLY.get(n, '다른')} 사본에" if n in ENV_ONLY
                     else f"§{n} 없음")
    tail = " · ".join(where) if where else "빠진 절 없음"
    return (
        f"# Simon 지침 v8.1 — {spec['place']} 용 사본 · 포함 "
        f"{'§' + '·§'.join(str(n) for n in have)}\n"
        f"> 생성물. 원본 `{os.path.basename(SOURCE)}` sha256 {src_sha} · 생성 {stamp}\n"
        f"> {tail}. **직접 고치지 않는다** — 단일본을 고치고 `split.py` 로 다시 만든다(§0-2). "
        f"**repo `./CLAUDE.md`에는 넣지 않는다.**\n\n---\n\n"
    )


def build(text):
    pre, secs = parse(text)
    src_sha = sha12(text)
    stamp = datetime.now(KST).strftime("%y%m%d %H:%M")
    out = {}
    for name, spec in TARGETS.items():
        body = header_for(name, spec, src_sha, stamp, secs)
        body += "".join(secs[n] + "\n" for n in spec["sections"] if n in secs)
        out[name] = body.rstrip("\n") + "\n"
    return out, src_sha


def write(out):
    os.makedirs(OUTDIR, exist_ok=True)
    for name, body in out.items():
        path = os.path.join(OUTDIR, name + ".md")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        print(f"  {name+'.md':<26} {len(body):>6}자")
    return True


def check_sha(text):
    """완료조건 7 — 사본 머리말의 sha 가 단일본 실제 sha 와 같은가.

    사본에 sha 를 적어두고도 아무도 대조하지 않아서, 2026-09-10 에 한 세대 이전본을
    단일본으로 오인할 뻔했다. 그 일이 이 검사가 존재하는 이유다.
    """
    src_sha = sha12(text)
    bad = []
    for name in TARGETS:
        path = os.path.join(OUTDIR, name + ".md")
        if not os.path.exists(path):
            bad.append((name, "사본 없음")); continue
        head = open(path, encoding="utf-8").read()[:600]
        m = HEADER_SHA_RE.search(head)
        if not m:
            bad.append((name, "머리말에 sha 없음"))
        elif m.group(1) != src_sha:
            bad.append((name, f"{m.group(1)} ≠ {src_sha}"))
    for name, why in bad:
        print(f"  X {name}: {why}")
    print(f"  단일본 sha256 {src_sha} · 불일치 {len(bad)}건")
    return not bad


# 끊긴 참조 기준선 — 2026-09-10 v8.1 시점의 실측값.
#  0 을 요구할 수 없다: §6 이 "Cowork 에서는 §8-3 을 따른다"고 **일부러** 다른 환경을
#  가리키고(안내), §8 이 §7 을 참조하는 것은 v8.0 부터의 기존 결함이다(Q-260830-03).
#  그래서 절대값이 아니라 **래칫**으로 지킨다 — 늘면 실패, 줄면 기준선을 내리라고 알린다.
REFS_BASELINE = {
    "profile_§0-6": 1,          # §6 → §8 (안내)
    "claude-code_§0-7": 1,      # §6 → §8 (안내)
    "cowork_§0-6+§8": 1,        # §8 → §7 (Q-260830-03, v8.0 부터의 기존 결함)
}


def check_refs(text):
    """완료조건 8 — 그 사본에 없는 절을 본문이 참조하는가. 래칫으로 판정한다.

    §8 이 §7 을 참조하는데 Cowork 사본에는 §7 이 없다(Q-260830-03). §0 이 §1·§5 를
    참조하므로 폐기된 A안(§0+§8)에서는 결함이 2건 더 늘어났었다 — B안은 §1~§6 을 갖고
    있어 §0 의 참조가 전부 해소된다.
    """
    total = 0
    over = 0
    for name, spec in TARGETS.items():
        path = os.path.join(OUTDIR, name + ".md")
        if not os.path.exists(path):
            continue
        body = open(path, encoding="utf-8").read()
        # 머리말은 '§7·§8 은 다른 사본에 있다'를 **일부러** 설명하는 자리다.
        # 그건 끊긴 참조가 아니라 안내다 → 절 본문만 센다.
        i = body.find("\n## ")
        rules = body[i:] if i >= 0 else body
        have = set(spec["sections"])
        broken = sorted({int(n) for n in REF_RE.findall(rules)} - have)
        total += len(broken)
        base = REFS_BASELINE.get(name)
        if base is None:
            mark, note = "?", "기준선 없음 — REFS_BASELINE 에 추가할 것"
        elif len(broken) > base:
            mark, note = "X", f"기준선 {base} 초과 ({len(broken)}건)"; over += 1
        elif len(broken) < base:
            mark, note = "↓", f"기준선 {base} → {len(broken)} 로 내릴 것"
        else:
            mark, note = "OK", f"기준선 {base} 유지"
        detail = " ".join(f"§{n}" for n in broken) or "없음"
        print(f"  {mark:>4} {name:<26} {detail:<22} {note}")
    print(f"  끊긴 참조 {total}건 · 기준선 초과 {over}건")
    return over == 0


def check_sections(text):
    """각 사본의 절 구성이 배정표와 같은가 + §0 이 모든 사본에 있는가(완료조건 4)."""
    ok = True
    for name, spec in TARGETS.items():
        path = os.path.join(OUTDIR, name + ".md")
        if not os.path.exists(path):
            print(f"  X {name}: 사본 없음"); ok = False; continue
        body = open(path, encoding="utf-8").read()
        found = sorted(int(m) for m in re.findall(r"(?m)^## (\d+)\.", body))
        want = sorted(spec["sections"])
        has0 = body.count("\n## 0.") + body.startswith("## 0.")
        flag = "OK" if found == want and has0 == 1 else "X"
        if flag == "X":
            ok = False
        print(f"  {flag:>4} {name:<26} 절 {found} · §0 {has0}회")
    return ok


def apply_copies(out):
    """--apply — 붙일 수 있는 자리에만 붙인다. claude.ai·Cowork 는 사람이 붙인다."""
    stamp = datetime.now(KST).strftime("%y%m%d_%H%M")
    for name, spec in TARGETS.items():
        dest = spec.get("apply_to")
        if not dest:
            print(f"  - {name}: 수동 — {spec['place']}")
            continue
        if os.path.exists(dest):
            bak = f"{dest}.bak_{stamp}"
            shutil.copyfile(dest, bak)
            print(f"  백업 {bak}")
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(out[name])
        print(f"  교체 {dest}")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--refs", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    text = read_source()
    out, src_sha = build(text)

    if a.check or a.refs or a.verify:
        ok = True
        if a.check or a.verify:
            print("[sha 대조 — 완료조건 7]"); ok &= check_sha(text)
        if a.verify:
            print("[절 구성 — 완료조건 4]"); ok &= check_sections(text)
        if a.refs or a.verify:
            print("[상호참조 — 완료조건 8]"); ok &= check_refs(text)
        raise SystemExit(0 if ok else 1)

    print(f"단일본 {len(text)}자 · sha256 {src_sha}")
    write(out)
    if a.apply:
        print("[적용]"); apply_copies(out)
    else:
        print("적용하려면 --apply. claude.ai·Cowork 는 out/ 의 파일을 사람이 붙인다.")


if __name__ == "__main__":
    main()
