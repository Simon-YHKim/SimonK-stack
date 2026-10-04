# -*- coding: utf-8 -*-
"""정답 생성기 — locale-leaf-keys: locales/en 아래 JSON 을 끝까지 펼쳤을 때 말단 값의 수.

이 문항이 노리는 함정 (집계 단위가 넷이다):
  1) `grep -c '":'` 는 '키가 있는 줄'을 센다 — 중첩 객체의 키와 배열 키까지 들어간다.
  2) 최상위 키 수(`Object.keys`)는 네임스페이스 묶음 단위다.
  3) 배열이 있다. 원소를 하나씩 세는지 배열 하나로 세는지 문항이 정한다(여기서는 원소마다).
  4) 로케일 디렉터리는 5개(en·es·id·ko·pt)지만 문항은 en 하나만 묻는다.

정의(문항 문구와 같다): 값이 객체면 안으로 들어가고, 배열이면 원소마다 같은 규칙을 적용하고,
그 밖의 값(문자열·숫자·불리언·null) 하나를 1로 센다.
"""
import json
import subprocess
import sys

repo = sys.argv[1]
REF = "origin/main"
ROOT = "locales/en/"


def git(*args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60)


ls = git("ls-tree", "-r", "-z", "--name-only", REF, "locales/en")
if ls.returncode != 0:
    sys.stderr.write(ls.stderr or "ls-tree 실패")
    raise SystemExit(2)
files = sorted(f for f in ls.stdout.split("\0") if f.startswith(ROOT) and f.endswith(".json"))
if not files:
    sys.stderr.write("locales/en 아래 .json 이 0개 — 경로가 바뀌었다\n")
    raise SystemExit(2)


def leaves(v):
    if isinstance(v, dict):
        return sum(leaves(x) for x in v.values())
    if isinstance(v, list):
        return sum(leaves(x) for x in v)
    return 1


total = 0
for f in files:
    body = git("show", "%s:%s" % (REF, f))
    if body.returncode != 0:
        sys.stderr.write("읽기 실패 %s\n" % f)
        raise SystemExit(2)
    try:
        total += leaves(json.loads(body.stdout))
    except ValueError as e:
        sys.stderr.write("JSON 파싱 실패 %s: %s\n" % (f, e))
        raise SystemExit(2)
print(total)
