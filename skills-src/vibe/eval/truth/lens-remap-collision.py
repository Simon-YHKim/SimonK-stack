# -*- coding: utf-8 -*-
"""정답 생성기 — lens-remap-collision: 재매핑 '값'이 새 일곱 별 id 와 같은 글자가 되는 옛 축 id.

이 문항이 노리는 함정 (이름이 같고 뜻이 다른 값):
  1) `now` — 옛 자기이해 축에도, 새 일곱 별에도 있는 유명한 충돌이다(CLAUDE.md 가 경고한다).
     그러나 문항이 묻는 것은 '키'가 아니라 재매핑된 '값'이다. `now` 의 값은 렌즈 `return` 이다.
  2) `profile` — 렌즈 id 에도 새 별 id 에도 있다. 그러나 문항은 렌즈 id 가 아니라 그 값을 받는
     '옛 축 id'를 묻는다.
정답 = { 옛 축 id k | LEGACY_STAR_TO_LENS[k] ∈ SEVEN_STAR_IDS }, 사전순 쉼표 연결, 없으면 none.

견고성: SEVEN_STAR_IDS 배열과 SevenStarId 유니언 타입이 같은 집합인지, 매핑 값이 전부
LensId 유니언에 있는지, 매핑 블록에 해석 못 한 줄이 없는지 확인한다. 하나라도 어긋나면 실패로 닫는다.
"""
import re
import subprocess
import sys

repo = sys.argv[1]
REF = "origin/main"


def show(path):
    p = subprocess.run(["git", "-C", repo, "show", "%s:%s" % (REF, path)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=60)
    if p.returncode != 0:
        sys.stderr.write("읽기 실패: %s\n" % path)
        raise SystemExit(2)
    return p.stdout


def no_line_comments(text):
    return "\n".join(l.split("//", 1)[0] for l in text.splitlines())


def body_after(src, head, closer):
    m = re.search(head, src, re.M)
    if not m:
        sys.stderr.write("선언을 못 찾았다: %s\n" % head)
        raise SystemExit(2)
    rest = no_line_comments(src[m.end():])
    k = rest.find(closer)
    if k < 0:
        sys.stderr.write("닫는 %r 를 못 찾았다: %s\n" % (closer, head))
        raise SystemExit(2)
    return rest[:k]


seven_src = show("src/lib/persona/seven-stars.ts")
reg_src = show("src/lib/lenses/registry.ts")

ids_arr = re.findall(r'"([^"]+)"', body_after(seven_src, r"export const SEVEN_STAR_IDS\b[^=]*=\s*\[", "]"))
ids_typ = re.findall(r'"([^"]+)"', body_after(seven_src, r"export type SevenStarId\s*=", ";"))
if not ids_arr or set(ids_arr) != set(ids_typ) or len(ids_arr) != len(set(ids_arr)):
    sys.stderr.write("SEVEN_STAR_IDS(%s) 와 SevenStarId(%s) 가 어긋난다\n" % (ids_arr, ids_typ))
    raise SystemExit(2)
seven = set(ids_arr)

lens_ids = set(re.findall(r'"([^"]+)"', body_after(reg_src, r"export type LensId\s*=", ";")))
if not lens_ids:
    sys.stderr.write("LensId 유니언이 비었다\n")
    raise SystemExit(2)

block = body_after(reg_src, r"export const LEGACY_STAR_TO_LENS\b[^=]*=\s*\{", "}")
pair = re.compile(r"""^\s*(["']?)([A-Za-z_][\w-]*)\1\s*:\s*(["'])([\w-]+)\3\s*,?\s*$""")
mapping = {}
for line in block.splitlines():
    if not line.strip():
        continue
    m = pair.match(line)
    if not m:
        sys.stderr.write("매핑 블록에 해석 못 한 줄: %r\n" % line)
        raise SystemExit(2)
    if m.group(2) in mapping:
        sys.stderr.write("중복 키: %s\n" % m.group(2))
        raise SystemExit(2)
    mapping[m.group(2)] = m.group(4)

if not mapping or not set(mapping.values()) <= lens_ids:
    sys.stderr.write("매핑이 비었거나 LensId 밖의 값이 있다: %s\n" % mapping)
    raise SystemExit(2)

hits = sorted(k for k, v in mapping.items() if v in seven)
print(",".join(hits) if hits else "none")
