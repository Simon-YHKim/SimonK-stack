# -*- coding: utf-8 -*-
"""정답 생성기 — vendor-branch-pair: 스위치 두 개를 건 환경에서 대화 한 턴(이미지 없음/있음)의 프록시.

이 문항이 노리는 함정 (위임·분기 너머의 사실):
  1) 이미지가 붙으면 대화 스위치보다 멀티모달 스위치가 먼저다(resolveVendorForPurpose 1번 줄).
  2) 멀티모달 스위치는 openai|gemini 만 받는다. claude 는 조용히 기본값(openai)으로 떨어진다.
  3) 대화 스위치는 normalizeVendor 를 거쳐 `grok` 을 `xai` 로 받아준다. LlmVendor 타입에는
     grok 이 없어서, 타입만 보면 '무효값 → 기본값'으로 오독한다.
  4) routing.ts 안의 주석 일부(`Unset → "gemini", exactly as before.`)와 CLAUDE.md 의 옛 서술
     (`EXPO_PUBLIC_CHAT_VENDOR`(`gemini`(기본·미설정) …)이 코드와 다르다.

정답은 추론하지 않고 **실행해서** 만든다: origin/main 의 routing.ts 를 git show 로 읽어
저장소의 typescript 로 트랜스파일하고, 가짜 process.env(두 변수만)로 평가한다.
상대 경로가 아닌 런타임 import 가 생기면(부작용 위험) 실패로 닫는다.
"""
import json
import os
import re
import subprocess
import sys

repo = sys.argv[1]
ENV = {"EXPO_PUBLIC_CHAT_VENDOR": "grok", "EXPO_PUBLIC_MULTIMODAL_VENDOR": "claude"}

if not os.path.isfile(os.path.join(repo, "node_modules", "typescript", "package.json")):
    sys.stderr.write("typescript 가 없다 (%s/node_modules) — 실행 기반 정답을 만들 수 없다\n" % repo)
    raise SystemExit(2)

JS = r"""
'use strict';
const path = require('path');
const { execFileSync } = require('child_process');
const repo = process.env.PROBE_REPO;
const ref = process.env.PROBE_REF;
const moduleEnv = JSON.parse(process.env.PROBE_ENV);
const ts = require(path.join(repo, 'node_modules', 'typescript'));
function exists(p) {
  try { execFileSync('git', ['-C', repo, 'cat-file', '-e', ref + ':' + p], { stdio: 'ignore' }); return true; }
  catch (e) { return false; }
}
function show(p) {
  return execFileSync('git', ['-C', repo, 'show', ref + ':' + p], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
}
const cache = new Map();
function load(p) {
  if (cache.has(p)) return cache.get(p).exports;
  const out = ts.transpileModule(show(p), {
    fileName: p,
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const mod = { exports: {} };
  cache.set(p, mod);
  const dir = path.posix.dirname(p);
  const req = (spec) => {
    if (!spec.startsWith('.')) throw new Error('non-relative runtime import: ' + spec + ' in ' + p);
    const base = path.posix.normalize(path.posix.join(dir, spec));
    const cand = [base + '.ts', base + '.tsx', base + '/index.ts', base].find(exists);
    if (!cand) throw new Error('unresolved import: ' + spec + ' in ' + p);
    return load(cand);
  };
  new Function('exports', 'require', 'module', 'process', out)(mod.exports, req, mod, { env: moduleEnv });
  return mod.exports;
}
const r = load('src/lib/llm/routing.ts');
for (const fn of ['resolveVendorForPurpose', 'proxyFnForVendor']) {
  if (typeof r[fn] !== 'function') throw new Error('missing export: ' + fn);
}
const text = r.proxyFnForVendor(r.resolveVendorForPurpose('secondb_chat', false));
const image = r.proxyFnForVendor(r.resolveVendorForPurpose('secondb_chat', true));
process.stdout.write(text + ',' + image + '\n');
"""

env = dict(os.environ, PROBE_REPO=repo, PROBE_REF="origin/main", PROBE_ENV=json.dumps(ENV))
try:
    p = subprocess.run(["node", "-e", JS], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env, timeout=90)
except (OSError, subprocess.TimeoutExpired) as e:
    sys.stderr.write("node 실행 실패: %s\n" % e)
    raise SystemExit(2)
if p.returncode != 0:
    sys.stderr.write((p.stderr or "node 비정상 종료")[-800:])
    raise SystemExit(2)
out = p.stdout.strip()
if not re.fullmatch(r"[a-z]+-proxy,[a-z]+-proxy", out):
    sys.stderr.write("예상 밖 출력: %r\n" % out)
    raise SystemExit(2)
print(out)
