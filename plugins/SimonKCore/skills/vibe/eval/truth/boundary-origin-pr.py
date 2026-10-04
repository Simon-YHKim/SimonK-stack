# -*- coding: utf-8 -*-
"""정답 생성기 — boundary-origin-pr: src/lib/llm/boundary.ts 가 (옛 이름 시절 포함) 처음 추가된 커밋의 PR 번호.

이 문항이 노리는 함정:
  1) 이 파일은 2026-08-18 커밋(#1229)에서 gemini.ts 로부터 이름이 바뀌었다.
     `git log --diff-filter=A -- src/lib/llm/boundary.ts` 는 개명 커밋을 '추가'로 보여준다
     → 1229. 옛 이름까지 거슬러 올라가려면 --follow 가 필요하다.
  2) 이력은 스쿼시 커밋 `(#N)` 과 머지 커밋 `Merge pull request #N` 이 섞여 있다.

정답: `git log --follow --name-status` 에서 상태가 A 인 가장 오래된 커밋의 제목에서 PR 번호를 뽑는다.
제목에 PR 번호가 없으면 추측하지 않고 실패로 닫는다.
"""
import re
import subprocess
import sys

repo = sys.argv[1]
REF = "origin/main"
TARGET = "src/lib/llm/boundary.ts"


def git(*args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)


if git("cat-file", "-e", "%s:%s" % (REF, TARGET)).returncode != 0:
    sys.stderr.write("%s 에 %s 가 없다 — 문항이 무효가 됐다\n" % (REF, TARGET))
    raise SystemExit(2)

log = git("log", "--follow", "--name-status", "--format=@@%H%x09%s", REF, "--", TARGET)
if log.returncode != 0:
    sys.stderr.write(log.stderr or "git log 실패")
    raise SystemExit(2)

blocks = []
for line in log.stdout.splitlines():
    if line.startswith("@@"):
        sha, _, subj = line[2:].partition("\t")
        blocks.append((sha, subj, []))
    elif line.strip() and blocks:
        blocks[-1][2].append(line)

added = [b for b in blocks if any(s.split("\t", 1)[0] == "A" for s in b[2])]
if not added:
    sys.stderr.write("추가(A) 커밋을 못 찾았다\n")
    raise SystemExit(2)

sha, subj, _ = added[-1]  # log 는 최신 → 과거 순이다. 마지막이 가장 오래된 추가
m = re.search(r"\(#(\d+)\)\s*$", subj) or re.search(r"Merge pull request #(\d+)", subj)
if not m:
    sys.stderr.write("가장 오래된 추가 커밋 %s 의 제목에 PR 번호가 없다: %s\n" % (sha[:8], subj))
    raise SystemExit(2)
print(m.group(1))
