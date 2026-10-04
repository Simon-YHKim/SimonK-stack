# -*- coding: utf-8 -*-
"""정답 생성기 — app-screen-files: src/app 아래 .tsx 중 `_layout`·`+` 로 시작하는 파일을 뺀 수.

이 문항이 노리는 함정:
  1) 저장소 CLAUDE.md 가 이 수를 "100"(2026-09-07 실측)으로 적고 있다. 수는 그 뒤에 바뀐다.
     문서의 수를 옮겨 적으면 틀린다 — 세어야 맞는다.
  2) `git ls-files 'src/app/*.tsx'` 의 `*` 는 pathspec 에서 `/` 를 넘는다(하위까지 센다).
     반대로 `ls-tree` 를 -r 없이 쓰거나 `:(glob)` 를 쓰면 바로 아래만 센다.
  3) `(auth)` 그룹 디렉터리와 `[id]` 동적 세그먼트 — bash 에서 괄호는 문법 오류가 되고,
     PowerShell `-Path` 에서 `[]` 는 와일드카드 문자 클래스라 그 파일이 조용히 빠진다.

정답은 ls-tree -r 전체 목록을 파이썬에서 거른다. 셸 글롭을 쓰지 않는다.
"""
import subprocess
import sys

repo = sys.argv[1]
PREFIX = "src/app/"

p = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "-z", "--name-only", "origin/main", "src/app"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
if p.returncode != 0:
    sys.stderr.write(p.stderr or "ls-tree 실패")
    raise SystemExit(2)

files = [f for f in p.stdout.split("\0") if f.startswith(PREFIX)]
if not files:
    # src/app 이 통째로 없다면 '0개'가 아니라 문항이 무효가 된 것이다
    sys.stderr.write("src/app 아래 추적 파일이 0개 — 경로가 바뀌었는지 확인할 것\n")
    raise SystemExit(2)

n = 0
for f in files:
    base = f.rsplit("/", 1)[-1]
    if not base.endswith(".tsx"):
        continue
    if base.startswith("_layout") or base.startswith("+"):
        continue
    n += 1
print(n)
