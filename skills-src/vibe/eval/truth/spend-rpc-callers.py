# -*- coding: utf-8 -*-
"""정답 생성기 — spend-rpc-callers: RPC bump_gemini_spend 를 코드로 호출하는 엣지 함수 수.

이 문항이 노리는 함정:
  1) 이름이 뜻과 다르다. `bump_gemini_spend` 는 gemini 전용이 아니라 벤더 프록시 공용
     지출 한도다. 이름을 믿으면 gemini-proxy 하나만 센다.
  2) 저장소 CLAUDE.md 는 "프록시 3종이 이 이름으로 호출"한다고 적는다. 그 뒤 xai-proxy 가 생겼다.
  3) 주석 속 언급이 있다(`subscription-manage`, `_shared/llm-proxy-common.ts`).
     `git grep -l` 로 세면 디렉터리가 늘어나고, `-c` 로 세면 파일별 '줄 수'가 나온다.
  4) `_shared` 는 엣지 함수가 아니다.

정의(문항 문구와 같다):
  - 엣지 함수 = supabase/functions 바로 아래 디렉터리 중 `_` 로 시작하지 않는 것
  - 호출 = 주석을 걷어낸 코드에 `.rpc('bump_gemini_spend'` 형태가 있는 것
  - 함수 디렉터리가 (상대 경로로) import 하는 `_shared` 모듈 안의 호출은 그 함수의 호출로 센다
  - 테스트 파일(__tests__/ · *.test.*)은 제외

견고성: 주석 제거기를 두 벌(토크나이저 / 줄 단위) 돌려 결과가 다르면 실패로 닫는다.
호출 모양이 아닌 곳에서 코드 속 리터럴로 이름이 쓰이면(상수로 뺀 경우 등) 역시 실패로 닫는다 —
그때는 문항 정의를 사람이 다시 봐야 한다.
"""
import posixpath
import re
import subprocess
import sys

repo = sys.argv[1]
REF = "origin/main"
ROOT = "supabase/functions/"
SHARED = ROOT + "_shared/"
RPC = "bump_gemini_spend"
CODE_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs")
CALL = re.compile(r"\.rpc\s*\(\s*(['\"`])" + RPC + r"\1")
IMPORT = re.compile(r"""(?:\bfrom\s*|\bimport\s*\(?\s*)(['"])(\.{1,2}/[^'"]+)\1""")


class Undecidable(Exception):
    pass


def git(*args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60)


ls = git("ls-tree", "-r", "-z", "--name-only", REF, "supabase/functions")
if ls.returncode != 0:
    sys.stderr.write(ls.stderr or "ls-tree 실패")
    raise SystemExit(2)
TRACKED = {f for f in ls.stdout.split("\0") if f}


def is_test(p):
    return "/__tests__/" in p or re.search(r"\.test\.[jt]sx?$", p) is not None


def strip_comments(s):
    """JS/TS 주석을 같은 길이의 공백으로 바꾼다. 문자열·템플릿·정규식 리터럴은 보존한다."""
    out, i, n, prev = [], 0, len(s), ""
    while i < n:
        c = s[i]
        nx = s[i + 1] if i + 1 < n else ""
        if c == "/" and nx == "/":
            j = s.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
            continue
        if c == "/" and nx == "*":
            j = s.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", s[i:j]))
            i = j
            continue
        if c in "'\"`":
            j = i + 1
            while j < n:
                if s[j] == "\\":
                    j += 2
                    continue
                if s[j] == c:
                    j += 1
                    break
                if c != "`" and s[j] == "\n":
                    break
                j += 1
            out.append(s[i:j])
            i = j
            prev = c
            continue
        if c == "/" and (prev == "" or prev in "(,=:[!&|?{};+-*%<>~^"):
            j, cls = i + 1, False
            while j < n and s[j] != "\n":
                if s[j] == "\\":
                    j += 2
                    continue
                if s[j] == "[":
                    cls = True
                elif s[j] == "]":
                    cls = False
                elif s[j] == "/" and not cls:
                    j += 1
                    break
                j += 1
            out.append(s[i:j])
            i = j
            prev = "/"
            continue
        out.append(c)
        if not c.isspace():
            prev = c
        i += 1
    return "".join(out)


def calls_by_lines(src):
    """두 번째 판정기 — 줄 단위. 줄 머리가 주석이거나 호출 앞에 // 가 있으면 제외."""
    for line in src.splitlines():
        m = CALL.search(line)
        if not m:
            continue
        head = line.lstrip()
        if head.startswith("//") or head.startswith("*") or head.startswith("/*"):
            continue
        if "//" in line[:m.start()]:
            continue
        return True
    return False


_src = {}


def show(path):
    if path not in _src:
        p = git("show", "%s:%s" % (REF, path))
        if p.returncode != 0:
            raise Undecidable("읽기 실패: %s" % path)
        _src[path] = p.stdout
    return _src[path]


def scan(path, seen):
    """(토크나이저 판정, 줄 단위 판정) — path 와 그것이 import 하는 _shared 모듈까지."""
    if path in seen:
        return False, False
    seen.add(path)
    src = show(path)
    code = strip_comments(src)
    tok = CALL.search(code) is not None
    lin = calls_by_lines(src)
    if not tok and re.search(RPC, code):
        raise Undecidable("호출 모양이 아닌 코드 리터럴: %s" % path)
    for m in IMPORT.finditer(code):
        target = posixpath.normpath(posixpath.join(posixpath.dirname(path), m.group(2)))
        if not target.startswith(SHARED):
            continue
        cand = next((c for c in (target, target + ".ts", target + "/index.ts") if c in TRACKED), None)
        if cand is None:
            raise Undecidable("해석 못 한 _shared import: %s → %s" % (path, m.group(2)))
        t2, l2 = scan(cand, seen)
        tok, lin = tok or t2, lin or l2
    return tok, lin


funcs = sorted({f[len(ROOT):].split("/", 1)[0] for f in TRACKED
                if f.startswith(ROOT) and "/" in f[len(ROOT):]})
funcs = [d for d in funcs if not d.startswith("_")]
if len(funcs) < 3:
    sys.stderr.write("엣지 함수 디렉터리가 %d개뿐 — 구조가 바뀌었다\n" % len(funcs))
    raise SystemExit(2)

hits = 0
try:
    for d in funcs:
        seen = set()
        tok = lin = False
        for f in sorted(TRACKED):
            if f.startswith(ROOT + d + "/") and f.endswith(CODE_EXT) and not is_test(f):
                t, l = scan(f, seen)
                tok, lin = tok or t, lin or l
        if tok != lin:
            raise Undecidable("두 판정기가 %s 에서 갈렸다 (토크나이저=%s, 줄=%s)" % (d, tok, lin))
        hits += 1 if tok else 0
except Undecidable as e:
    sys.stderr.write("기계 판정 불가: %s\n" % e)
    raise SystemExit(2)
print(hits)
