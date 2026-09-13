# -*- coding: utf-8 -*-
"""정답 생성기 — path-kind-mix: 경로 7개 중 origin/main 트리에 '일반 파일'로 있는 것의 수.

이 문항이 노리는 함정 네 가지 (2026-09-13 실측 · E:/2ndB · Windows · Git Bash):
  1) MSYS 경로 변환. Git Bash 에서 `git cat-file -e origin/main:.env.test` 는 콜론 뒤가
     점으로 시작해서 인자가 `origin\\main;.env.test` 로 바뀌고 128 을 낸다. 파일은 있다.
     종료코드만 믿으면 '없음'이 된다 — 부재와 오류가 같은 종료코드를 낸다.
  2) `git cat-file -e` 는 트리(디렉터리)에도 0 을 낸다. docs/handoff 는 디렉터리다.
  3) Windows 파일시스템은 대소문자를 안 가린다. 디스크에서는 docs/handoff.md 가
     docs/HANDOFF.md 로 열린다. git 트리에는 그 이름이 없다.
  4) .env · .claude/settings.local.json 은 작업 트리에 있지만 gitignore 대상이라 트리에는 없다.
     반대로 .claude/settings.json 은 추적된다 — 짐작으로는 가려지지 않는다.

정답은 셸을 거치지 않고(인자 목록) `ls-tree -r -t -z --full-tree` 로 트리 전체 목록을 만든 뒤
경로 문자열을 대소문자 그대로 비교해서 만든다. pathspec 해석(대소문자·와일드카드)에 기대지 않는다.
"""
import subprocess
import sys

repo = sys.argv[1]
REF = "origin/main"
PATHS = (".env.test", ".claude/settings.json", ".env", "docs/handoff", "docs/handoff.md",
         "vercel.json", ".claude/settings.local.json")
# 120000(심볼릭 링크)·160000(서브모듈)·040000(트리)은 일반 파일이 아니다
REGULAR = ("100644", "100755")


def git(*args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60)


ok = git("rev-parse", "--verify", "--quiet", REF + "^{commit}")
if ok.returncode != 0:
    sys.stderr.write("%s 를 커밋으로 풀 수 없다 — 부재가 아니라 오류다\n" % REF)
    raise SystemExit(2)

ls = git("ls-tree", "-r", "-t", "-z", "--full-tree", REF)
if ls.returncode != 0:
    sys.stderr.write(ls.stderr or "ls-tree 실패")
    raise SystemExit(2)

modes = {}
for rec in ls.stdout.split("\0"):
    if not rec:
        continue
    meta, _, path = rec.partition("\t")
    modes[path] = meta.split(" ", 1)[0]

# 목록이 비정상적으로 작으면 '없음'을 믿지 않는다 — 부재와 오류를 여기서 가른다
if len(modes) < 100 or "README.md" not in modes:
    sys.stderr.write("트리 목록이 비정상이다 (%d개)\n" % len(modes))
    raise SystemExit(2)

print(sum(1 for p in PATHS if modes.get(p) in REGULAR))
