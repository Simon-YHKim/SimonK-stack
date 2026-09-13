# -*- coding: utf-8 -*-
"""정답 생성기 — privacy.trustTitle 이 기본 배포에서 렌더되는가 (yes/no).

기계로 만드는 방법: privacy.tsx 안에서
  (1) 그 문자열을 품은 컴포넌트가 무엇인지
  (2) 기본 UI 모드 분기가 그 컴포넌트보다 **먼저** return 하는지
둘을 읽어 판정한다. 사람이 'no' 라고 적어두면 코드가 고쳐져도 정답이 안 바뀐다.
"""
import re
import subprocess
import sys

repo = sys.argv[1]


def show(path):
    p = subprocess.run(["git", "-C", repo, "show", "origin/main:" + path],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    return p.stdout if p.returncode == 0 else None


src = show("src/app/privacy.tsx")
if src is None:
    print("no")  # 파일이 없으면 렌더될 수 없다
    raise SystemExit(0)

lines = src.splitlines()
trust_line = next((i for i, l in enumerate(lines) if "privacy.trustTitle" in l), None)
if trust_line is None:
    print("no")
    raise SystemExit(0)

# 그 문자열을 품은 함수(컴포넌트) 이름 — 위로 올라가며 첫 선언을 찾는다
decl = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?function\s+([A-Za-z0-9_]+)")
owner = None
for i in range(trust_line, -1, -1):
    m = decl.match(lines[i])
    if m:
        owner = m.group(1)
        break
if owner is None:
    print("unknown")
    raise SystemExit(0)

# 기본 모드 분기가 그 컴포넌트 호출보다 먼저 return 하면 렌더되지 않는다
guard = next((i for i, l in enumerate(lines)
              if "isDeepSpaceUI()" in l and "return" in l), None)
call = next((i for i, l in enumerate(lines)
             if ("<%s" % owner) in l and "return" in l), None)
print("no" if (guard is not None and (call is None or guard < call)) else "yes")
