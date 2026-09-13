# -*- coding: utf-8 -*-
"""정답 생성기 — reward-exec-roles: 마이그레이션을 전부 적용한 뒤 anon·authenticated·service_role 중
public.grant_chat_ad_bonus(uuid) 를 EXECUTE 할 수 있는 역할 (사전순 쉼표, 없으면 none).

이 문항이 노리는 함정:
  1) 가장 먼저 걸리는 grep 결과가 0090 의 `GRANT EXECUTE ... TO authenticated` 다.
     0090 만 보면 authenticated(명시 GRANT)에 service_role(기본 권한, 0090 이 안 건드림)까지 열려 있다.
     그 뒤 0172 가 `REVOKE ALL ... FROM PUBLIC, anon, authenticated, service_role` 로 전부 닫았다.
  2) 접두사가 같은 다른 함수 `grant_chat_ad_bonus_ssv(uuid, text)` 가 있다. 그쪽 줄에는
     `FROM authenticated`·`TO service_role` 이 섞여 있어 grep 결과가 양방향으로 오염된다.
  3) 0172 의 확인 블록(DO $verify$)에도 역할 이름과 함수 이름이 같이 나온다 — 권한문이 아니다.
  4) Postgres 기본값(PUBLIC 에 EXECUTE)과 Supabase 기본 권한 때문에 명시 GRANT 가 없어도 처음엔 열려 있다.

모델(문항 문구와 같다):
  - db/migrations 바로 아래 .sql 을 파일명 사전순으로 적용한다(rollback/ 제외).
  - public 함수를 새로 만들면 PUBLIC·anon·authenticated·service_role 이 EXECUTE 를 받는다.
    CREATE OR REPLACE 는 기존 권한을 유지하고, DROP 뒤 다시 만들면 기본값으로 돌아간다.
  - 최상위 GRANT/REVOKE(ON FUNCTION · ON ALL FUNCTIONS IN SCHEMA public)만 적용한다.
    DO 블록·함수 본문 안의 글자는 권한문이 아니다.
  - 역할의 실효 권한 = 그 역할의 권한 OR PUBLIC 의 권한.

실패로 닫는 경우(추측하지 않는다): ALTER DEFAULT PRIVILEGES · 대상 함수 RENAME ·
본문 안 동적 SQL(EXECUTE '… GRANT/REVOKE … grant_chat_ad_bonus …') · 오버로드가 있는데 서명 없는 참조.

두 번째 인자(선택): 번호 상한. 예) `0171` 이면 0171 이하 파일만 적용한다 — 함정 값 실측용이며
채점 경로(truth_cmd)는 이 인자를 쓰지 않는다.
"""
import re
import subprocess
import sys

repo = sys.argv[1]
UPTO = int(sys.argv[2]) if len(sys.argv) > 2 else None
REF = "origin/main"
ROOT = "db/migrations/"
TARGET = "grant_chat_ad_bonus"
TARGET_ARGS = ["uuid"]
ROLES = ("public", "anon", "authenticated", "service_role")
ANSWER_ROLES = ("anon", "authenticated", "service_role")
MULTIWORD_TYPES = ("double precision", "character varying", "timestamp with time zone",
                   "timestamp without time zone", "time with time zone", "time without time zone",
                   "bit varying")


class Undecidable(Exception):
    pass


def git(*args, **kw):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, timeout=120, **kw)


def batch_show(paths):
    """git 프로세스 하나로 blob 여러 개를 읽는다 (파일마다 git show 를 띄우면 수십 초가 걸린다)."""
    specs = "".join("%s:%s\n" % (REF, p) for p in paths).encode("utf-8")
    p = git("cat-file", "--batch", input=specs)
    if p.returncode != 0:
        raise Undecidable("cat-file --batch 실패")
    out, pos, res = p.stdout, 0, {}
    for path in paths:
        nl = out.index(b"\n", pos)
        header = out[pos:nl].decode("utf-8", "replace")
        pos = nl + 1
        parts = header.split(" ")
        if len(parts) != 3 or parts[1] != "blob":
            raise Undecidable("예상 밖 응답(%s): %s" % (path, header))
        size = int(parts[2])
        res[path] = out[pos:pos + size].decode("utf-8", "replace")
        pos += size + 1
    return res


def top_level(sql):
    """주석을 지우고 문자열 리터럴·달러 인용 본문을 자리표시로 바꾼 최상위 텍스트와 본문 목록."""
    out, bodies, i, n = [], [], 0, len(sql)
    while i < n:
        c = sql[i]
        if sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j < 0 else j
            out.append(" ")
            continue
        if sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
            continue
        if c == "'":
            j = i + 1
            while j < n:
                if sql[j] == "'":
                    if j + 1 < n and sql[j + 1] == "'":
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            out.append("''")
            i = j
            continue
        if c == '"':
            j = sql.find('"', i + 1)
            j = n if j < 0 else j + 1
            out.append(sql[i:j])
            i = j
            continue
        if c == "$":
            m = re.match(r"\$(?:[A-Za-z_]\w*)?\$", sql[i:])
            if m:
                tag = m.group(0)
                j = sql.find(tag, i + len(tag))
                if j < 0:
                    raise Undecidable("닫히지 않은 달러 인용 %s" % tag)
                bodies.append(sql[i + len(tag):j])
                out.append(" $body$ ")
                i = j + len(tag)
                continue
        out.append(c)
        i += 1
    return "".join(out), bodies


def split_top_commas(text):
    parts, depth, cur = [], 0, []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip()]


def arg_types(argtext, has_names):
    types = []
    for a in split_top_commas(argtext):
        a = re.split(r"\s+default\s+|\s*=\s*", a, maxsplit=1)[0].strip()
        a = re.sub(r"^(in|out|inout|variadic)\s+", "", a)
        if has_names and not any(a.startswith(t) for t in MULTIWORD_TYPES):
            toks = a.split(" ", 1)
            if len(toks) == 2:
                a = toks[1].strip()
        types.append(a.replace("public.", "").strip())
    return types


def parse_ref(ref, has_names=False):
    """'public.f(uuid)' → (schema, name, [types] | None)."""
    m = re.match(r'^([\w".]+)\s*(?:\((.*)\))?\s*$', ref, re.S)
    if not m:
        return None
    parts = [p.strip('"') for p in m.group(1).split(".")]
    schema, name = (parts[0], parts[1]) if len(parts) == 2 else ("public", parts[-1])
    args = None if m.group(2) is None else arg_types(m.group(2), has_names)
    return schema, name, args


def is_target(ref, overloads):
    r = parse_ref(ref)
    if not r or r[0] != "public" or r[1] != TARGET:
        return False
    if r[2] is None:
        if len(overloads) > 1:
            raise Undecidable("오버로드가 있는데 서명 없는 참조: %s" % ref)
        return True
    return r[2] == TARGET_ARGS


def roles_of(text):
    text = re.sub(r"\s+(with grant option|cascade|restrict|granted by .*)$", "", text.strip())
    return [r.strip().strip('"') for r in text.split(",") if r.strip()]


def main():
    ls = git("ls-tree", "-r", "-z", "--name-only", REF, "db/migrations")
    if ls.returncode != 0:
        raise Undecidable("ls-tree 실패")
    names = ls.stdout.decode("utf-8", "replace").split("\0")
    files = sorted(f for f in names
                   if f.startswith(ROOT) and "/" not in f[len(ROOT):] and f.endswith(".sql"))
    if UPTO is not None:
        files = [f for f in files if re.match(r"\d{4}", f[len(ROOT):])
                 and int(f[len(ROOT):len(ROOT) + 4]) <= UPTO]
    if len(files) < 10:
        raise Undecidable("마이그레이션이 %d개뿐 — 구조가 바뀌었다" % len(files))

    blobs = batch_show(files)
    acl = None  # None = 함수 없음
    overloads = set()
    seen_create = False
    dyn = re.compile(r"\bexecute\s+(?:format\s*\(\s*)?'((?:[^']|'')*)'", re.I)
    for f in files:
        top, bodies = top_level(blobs[f])
        for b in bodies:
            for m in dyn.finditer(b):
                s = m.group(1).lower()
                if re.search(r"\b(grant|revoke)\b", s) and re.search(r"\b%s\b(?!_)" % TARGET, s):
                    raise Undecidable("동적 SQL 권한문 %s" % f)
        for raw in top.split(";"):
            s = re.sub(r"\s+", " ", raw).strip().lower()
            if not s:
                continue
            if s.startswith("alter default privileges"):
                raise Undecidable("ALTER DEFAULT PRIVILEGES 는 모델 밖 (%s)" % f)
            m = re.match(r"^create (?:or replace )?function ([\w\".]+)\s*\(", s)
            if m:
                start = m.end() - 1
                depth, k = 0, start
                while k < len(s):
                    depth += s[k] == "("
                    depth -= s[k] == ")"
                    if depth == 0:
                        break
                    k += 1
                r = parse_ref(m.group(1) + s[start:k + 1], has_names=True)
                if r and r[0] == "public" and r[1] == TARGET:
                    overloads.add(tuple(r[2] or []))
                    if r[2] == TARGET_ARGS:
                        seen_create = True
                        if acl is None:
                            acl = {role: True for role in ROLES}
                continue
            m = re.match(r"^alter function ([\w\".]+(?:\s*\([^)]*\))?) rename ", s)
            if m and is_target(m.group(1), overloads):
                raise Undecidable("대상 함수 RENAME (%s)" % f)
            m = re.match(r"^drop function (?:if exists )?(.+?)(?: cascade| restrict)?$", s)
            if m:
                if any(is_target(x, overloads) for x in split_top_commas(m.group(1))):
                    acl = None
                continue
            m = re.match(r"^(grant|revoke) (grant option for )?(.+?) on "
                         r"(all functions in schema|function|functions|routine|routines) "
                         r"(.+?) (to|from) (.+)$", s)
            if m:
                verb, opt, privs, kind, objs, _, who = m.groups()
                if opt or not re.search(r"\b(execute|all)\b", privs):
                    continue
                if kind == "all functions in schema":
                    hit = "public" in [x.strip().strip('"') for x in objs.split(",")]
                else:
                    hit = any(is_target(x, overloads) for x in split_top_commas(objs))
                if hit and acl is not None:
                    for role in roles_of(who):
                        if role in acl:
                            acl[role] = (verb == "grant")
    if not seen_create:
        raise Undecidable("public.%s(uuid) 를 만드는 마이그레이션을 못 찾았다 — 문항이 무효" % TARGET)
    if acl is None:
        return "none"
    can = [r for r in ANSWER_ROLES if acl[r] or acl["public"]]
    return ",".join(can) if can else "none"


try:
    print(main())
except Undecidable as e:
    sys.stderr.write("기계 판정 불가: %s\n" % e)
    raise SystemExit(2)
