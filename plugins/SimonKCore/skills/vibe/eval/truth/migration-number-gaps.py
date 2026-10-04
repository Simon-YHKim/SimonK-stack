# -*- coding: utf-8 -*-
"""정답 생성기 — migration-number-gaps: db/migrations 번호 0001..최대 중 파일이 하나도 없는 번호 수.

이 문항이 노리는 함정 (집계 단위가 셋이다 — 파일 · 번호 · 하위 디렉터리):
  1) 같은 번호를 쓰는 파일이 여럿 있다(예: 0092 가 두 파일). '최대 번호 - 파일 수'는 틀린다.
  2) db/migrations/rollback/ 아래에도 번호 붙은 .sql 이 있다. -r 로 세면 파일 수가 늘어난다.
  3) 번호가 연속이라고 가정하면 0 이 나온다.
정답 = 최대 번호 - (1..최대 범위 안의 서로 다른 번호 개수).
"""
import re
import subprocess
import sys

repo = sys.argv[1]
ROOT = "db/migrations/"

p = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "-z", "--name-only", "origin/main", "db/migrations"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
if p.returncode != 0:
    sys.stderr.write(p.stderr or "ls-tree 실패")
    raise SystemExit(2)

nums = set()
for f in p.stdout.split("\0"):
    if not f.startswith(ROOT):
        continue
    rest = f[len(ROOT):]
    if "/" in rest or not rest.endswith(".sql"):  # 하위 디렉터리(rollback/ 등) 제외
        continue
    m = re.match(r"(\d{4})", rest)
    if m:
        nums.add(int(m.group(1)))

if not nums:
    sys.stderr.write("번호 붙은 .sql 이 0개 — 경로나 명명 규칙이 바뀌었다\n")
    raise SystemExit(2)

top = max(nums)
print(sum(1 for n in range(1, top + 1) if n not in nums))
