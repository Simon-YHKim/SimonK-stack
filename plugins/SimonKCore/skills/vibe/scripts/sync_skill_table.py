# sync_skill_table.py — 참고 문서의 레거시 라우팅 표를 routing.py 에서 다시 생성한다.
#
# 발주 §2: "표를 두 모드에 중복 기재하지 말 것 — 단일 출처로 두고 양쪽이 참조한다."
# → 정본은 routing.py 다. references/legacy-routing.md 의 마커 사이는 파생물이다.
#   이 스크립트가 없으면 "단일 출처"는 말뿐이고 곧 어긋난다.
#
# 사용:
#   python sync_skill_table.py --check   표가 어긋났는지만 본다 (어긋나면 exit 1)
#   python sync_skill_table.py           참고 문서를 다시 생성한다
import os
import sys

# Plain Python entrypoints must not add unreceipted bytecode to a bundle.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import routing  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TABLE = os.path.join(os.path.dirname(_HERE), "references", "legacy-routing.md")
BEGIN = "<!-- ROUTING:BEGIN"
END = "<!-- ROUTING:END -->"


def main():
    try:
        with open(TABLE, "r", encoding="utf-8") as f:
            doc = f.read()
    except OSError:
        print("legacy-routing.md 를 읽을 수 없다 — 단일 출처가 깨졌다")
        raise SystemExit(2)

    i = doc.find(BEGIN)
    j = doc.find(END)
    if i < 0 or j < 0:
        print("legacy-routing.md 에 ROUTING 마커가 없다 — 단일 출처가 깨졌다")
        raise SystemExit(2)

    current = doc[i:j + len(END)]
    fresh = routing.emit_md()

    if current.strip() == fresh.strip():
        print("동기 OK — legacy-routing.md 표가 routing.py 와 일치한다")
        return

    if "--check" in sys.argv:
        print("어긋남 — legacy-routing.md 표가 routing.py 와 다르다. `python sync_skill_table.py` 로 재생성할 것")
        # 어디가 다른지 줄 단위로 보여준다
        a, b = current.strip().split("\n"), fresh.strip().split("\n")
        for n in range(max(len(a), len(b))):
            x = a[n] if n < len(a) else "(없음)"
            y = b[n] if n < len(b) else "(없음)"
            if x != y:
                print(f"  L{n+1}\n    reference: {x}\n    routing  : {y}")
                break
        raise SystemExit(1)

    with open(TABLE, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc[:i] + fresh + doc[j + len(END):])
    print("legacy-routing.md 표를 routing.py 에서 다시 생성했다")


if __name__ == "__main__":
    main()
