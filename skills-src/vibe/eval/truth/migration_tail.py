# -*- coding: utf-8 -*-
"""정답 생성기 — db/migrations 에서 0147 이상 .sql 중 최상위 BEGIN; 을 가진 파일 수.

손으로 핀한 정답(`manual:0`)을 대체한다. 핀은 저장소가 바뀌어도 안 바뀌므로
언젠가 반드시 거짓이 된다 — 정답은 저장소에서 다시 만들어져야 한다.
"""
import re
import subprocess
import sys

repo = sys.argv[1]

ls = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "--name-only",
                     "origin/main", "db/migrations"],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=120)
if ls.returncode != 0:
    sys.stderr.write(ls.stderr or "ls-tree failed")
    raise SystemExit(2)

num = re.compile(r"/(\d{4})[_.-]")
hits = 0
for path in (ls.stdout or "").splitlines():
    path = path.strip()
    if not path.endswith(".sql"):
        continue
    m = num.search(path)
    if not m or int(m.group(1)) < 147:
        continue
    body = subprocess.run(["git", "-C", repo, "show", "origin/main:" + path],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=120)
    if body.returncode != 0:
        continue
    for line in (body.stdout or "").splitlines():
        # 최상위 = 들여쓰기 없음. 함수 본문 안의 BEGIN 은 세지 않는다.
        if line.rstrip().upper() == "BEGIN;" and line[:1] not in (" ", "\t"):
            hits += 1
            break
print(hits)
