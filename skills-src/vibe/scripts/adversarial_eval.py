# -*- coding: utf-8 -*-
"""레인 간 적대적 상호평가 - 영역별 최적 모델·effort 를 데이터로 정한다.

왜 필요한가 (Simon 지시, 2026-09-12):
    모델은 계속 바뀌는데(gpt-6-astra 편입, daybreak 신설, codex 0.154 …) 라우팅 표는
    사람이 손으로 정한 값이다. 표가 언제 낡았는지 알 방법이 없다. 채택률 원장
    (`aggregate_ledger.py`)은 실제 라운드에서만 쌓이고, 실제 라운드는 늘 1순위만
    태우므로 **2순위 이하는 영원히 관측이 안 쌓인다.** 탐색 슬롯 1개로는 부족하다.

    그래서 라운드와 별개로, 정답이 기계로 확인되는 문제를 같은 조건에 여러 레인에
    풀리고 **제3의 레인이 채점**한다.

왜 '적대적'인가:
    자기 답을 자기가 채점하면 점수가 올라간다. 채점자는 생산자와 **벤더가 달라야**
    한다(G10). 그리고 채점자에게 "둘 다 틀렸을 가능성"을 먼저 보게 한다 - 확인이
    아니라 반증이 채점의 기본 동작이다.

설계 원칙:
    - **정답은 기계가 만든다.** 채점자가 정답을 지어내면 평가가 무의미하다.
      probe 마다 `truth_cmd` + `truth_post` 가 있고 그 출력이 정답이다.
    - **자동으로 표를 고치지 않는다.** 제안만 낸다. 기존 스왑 규칙과 같은 규율
      ("모델이 라우팅 표를 스스로 고치는 경로를 만들지 않는다").
    - **데몬을 만들지 않는다.** 주기는 `--due` 가 알려주고 사람이 실행한다.
      (상시 폴링 허브가 죽은 전례가 있다.)
    - 기본 동작은 `--plan`(비용 0). 실제 호출은 `--run` 을 명시해야 한다.

⚠ 2026-09-13 개정 — 껍데기 두 곳을 메웠다:
    (1) `truth_post` 가 선언만 되고 **구현이 없었다.** 세는 문제에 파일 목록이
        정답으로 들어가고, 부재 확인 문제는 `cat-file -e` 의 종료코드 1 이
        "정답 생성 실패"로 처리돼 **정답이 아예 안 만들어졌다.**
        지표가 질문보다 좁으면 0 은 안전이 아니라 침묵이다 - 같은 함정.
    (2) `--run` 이 "아직 수동 단계다" 만 찍고 끝나는 껍데기였다.
        지금은 벤더 CLI 를 직접 동기 호출한다(Orca 워커가 아니다 - 아래 참조).

⚠ 실행 경로가 Orca 워커가 **아니다.** 각 벤더의 headless CLI 를 직접 부른다:
      claude -p / codex exec / agy --print / grok -p
    그래서 라우팅 표의 "grok·gemini 는 effort 지정 불가" 는 **여기 해당하지 않는다** -
    그건 Orca 가 `--model` 을 거부한다는 뜻이고, CLI 직행에는 `--model`·`--effort` 가
    둘 다 있다(2026-09-13 실측: `agy --effort low|medium|high` · `grok --reasoning-effort`).
    표를 이 사실로 고치지 말 것 - 표는 워커 경로를 적는다.
    대신 이 경로에는 워크트리 격리·worker_done·gate 가 없다. 전부 read-only 로 돈다.

사용:
    python scripts/adversarial_eval.py --due                 # 평가할 때가 됐나
    python scripts/adversarial_eval.py --validate            # 정답 생성기 점검 (비용 0)
    python scripts/adversarial_eval.py --plan                # 대진표만 (비용 0)
    python scripts/adversarial_eval.py --preflight           # 벤더 가용성 (아주 싼 호출 4회)
    python scripts/adversarial_eval.py --run --dry           # 전 구간 배선 점검 (비용 0)
    python scripts/adversarial_eval.py --run --only count-files
    python scripts/adversarial_eval.py --run
    python scripts/adversarial_eval.py --report              # 누적 점수·제안
"""
import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import routing  # noqa: E402

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_DIR = os.path.join(SKILL_ROOT, "eval")
PROBES = os.path.join(EVAL_DIR, "probes.json")
STATE_DIR = os.path.join(SKILL_ROOT, "state")
LEDGER = os.path.join(STATE_DIR, "eval-ledger.jsonl")
VENDOR_CACHE = os.path.join(STATE_DIR, "eval-vendors.json")
DUE_DAYS = 14
VENDOR_CACHE_HOURS = 6
# 판정 버전. rc 를 보지 않던 시절(v1 이전)의 캐시는 '가용'이라고 적혀 있어도 근거가 다르다 —
# 그 캐시를 그대로 재사용하면 패치가 새 측정에만 적용되고 기존 오판은 6~24시간 더 살아남는다.
# (2026-09-20 비즈로직 게이트 B1) 버전이 낮거나 없으면 캐시를 버리고 다시 잰다.
VERDICT_V = 2

# 레인 -> 벤더. G10(채점자 벤더 분리) 판정에 쓴다.
VENDOR_OF = {
    "claude-opus-5": "claude",
    "gpt-6-astra": "codex",
    "gpt-5.6-sol": "codex",
    "gpt-5.6-terra": "codex",
    "gpt-5.6-luna": "codex",
    "gpt-daybreak-blue-latest": "codex",
    "gemini-3.8-flash": "gemini",
    "grok-4.6": "grok",
}

ALL_VENDORS = ("claude", "codex", "gemini", "grok")
PING = "Reply with exactly one line and nothing else: ANSWER: OK"


# --------------------------------------------------------- truth post-처리
# truth_cmd 의 출력을 '질문이 물은 단위'로 바꾼다.
# 이게 없으면 세는 문제에 파일 목록이, 부재 문제에 빈 문자열이 정답으로 들어간다.
def _lines(out):
    return [l.strip() for l in (out or "").splitlines() if l.strip()]


TRUTH_POST = {
    "raw": lambda out, rc, arg: (out or "").strip(),
    "count_lines": lambda out, rc, arg: str(len(_lines(out))),
    "count_suffix": lambda out, rc, arg: str(sum(1 for l in _lines(out) if l.endswith(arg))),
    "prefix_count": lambda out, rc, arg: str(sum(1 for l in (out or "").splitlines()
                                                 if l.startswith(arg))),
    "grep_count": lambda out, rc, arg: str(sum(1 for l in _lines(out) if arg in l)),
    "grep_yesno": lambda out, rc, arg: ("yes" if any(arg in l for l in _lines(out)) else "no"),
    # 종료코드 자체가 답인 경우. 여기서는 rc != 0 이 실패가 아니라 '아니오'다.
    "exit_to_yesno": lambda out, rc, arg: ("yes" if rc == 0 else "no"),
}
# 종료코드를 답으로 읽는 post 는 rc != 0 을 오류로 보면 안 된다.
RC_IS_ANSWER = {"exit_to_yesno"}


# ---------------------------------------------------------------- probes
def load_probes():
    if not os.path.isfile(PROBES):
        raise SystemExit("probe 세트가 없다: %s" % PROBES)
    probes = json.load(open(PROBES, encoding="utf-8"))["probes"]
    seen = set()
    for p in probes:
        pid = p.get("id")
        if not pid or pid in seen:
            raise SystemExit("probe id 가 없거나 중복이다: %r" % pid)
        seen.add(pid)
        post = p.get("truth_post")
        if post is None:
            raise SystemExit("probe %s 에 truth_post 가 없다" % pid)
        head = post.split(":", 1)[0]
        if head not in TRUTH_POST:
            raise SystemExit("probe %s 의 truth_post '%s' 를 모른다 (아는 것: %s)"
                             % (pid, post, sorted(TRUTH_POST)))
        vendors = {VENDOR_OF[l] for l in p.get("lanes", []) if l in VENDOR_OF}
        if len(vendors) < 3:
            raise SystemExit("probe %s 의 lanes 가 벤더 %d개뿐이다 (G10 은 3개를 요구한다)"
                             % (pid, len(vendors)))
    return probes


def ground_truth(probe, repo):
    """정답을 기계로 만든다. 채점자가 정답을 지어내지 못하게 하는 장치."""
    cmd = [a.replace("{repo}", repo).replace("{skill}", SKILL_ROOT)
           for a in probe["truth_cmd"]]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                           shell=False, encoding="utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        return None, "정답 생성 실패: %s" % e
    post = probe["truth_post"]
    head, _, arg = post.partition(":")
    if p.returncode != 0 and head not in RC_IS_ANSWER:
        return None, "정답 생성 종료코드 %s: %s" % (p.returncode, (p.stderr or "")[:200])
    try:
        value = TRUTH_POST[head](p.stdout, p.returncode, arg)
    except Exception as e:  # noqa: BLE001
        return None, "truth_post '%s' 적용 실패: %s" % (post, e)
    if value == "":
        return None, "정답이 빈 문자열이다 (truth_post '%s' 가 질문 단위를 못 만들었다)" % post
    return value, ""


# ------------------------------------------------------------- matchmaking
def pick_matchup(probe, rng, exclude_vendors=()):
    """생산자 2 + 채점자 1. 셋 다 벤더가 달라야 한다(G10).

    벤더가 3개 미만으로 남으면 그 probe 는 이번 회차에서 건너뛴다 - 채점자를
    생산자와 같은 벤더로 두느니 관측을 포기하는 쪽이 낫다.
    """
    cands = [l for l in probe["lanes"]
             if l in VENDOR_OF and VENDOR_OF[l] not in exclude_vendors]
    by_vendor = {}
    for l in cands:
        by_vendor.setdefault(VENDOR_OF[l], []).append(l)
    vendors = sorted(by_vendor)
    if len(vendors) < 3:
        return None, ("벤더 %d개뿐이라 채점자를 분리할 수 없다 (필요 3, 남은 벤더 %s)"
                      % (len(vendors), vendors or "없음"))
    rng.shuffle(vendors)
    pa, pb, pg = vendors[0], vendors[1], vendors[2]
    return {
        "producer_a": rng.choice(by_vendor[pa]),
        "producer_b": rng.choice(by_vendor[pb]),
        "grader": rng.choice(by_vendor[pg]),
    }, ""


def check_g10(m):
    va, vb, vg = (VENDOR_OF.get(m["producer_a"]), VENDOR_OF.get(m["producer_b"]),
                  VENDOR_OF.get(m["grader"]))
    bad = []
    if vg in (va, vb):
        bad.append("G10_GRADER_SAME_VENDOR")
    if va == vb:
        bad.append("G10_PRODUCERS_SAME_VENDOR")
    return bad


# --------------------------------------------------------------- 실행 백엔드
def exec_plan(lane, effort, prompt):
    """(argv, stdin) 를 만든다. 프롬프트는 절대 셸 문자열에 넣지 않는다.

    shell=False 로 실행하므로 argv 원소로 들어간 자유 문자열은 확장되지 않는다.
    """
    vendor = VENDOR_OF[lane]
    slug = routing.slug_for(lane, effort)
    if vendor == "claude":
        # effort 는 프롬프트 키워드다(routing.prompt_prefix). --effort 플래그가 아니다.
        pre = routing.prompt_prefix(lane, effort)
        body = (pre + "\n\n" + prompt) if pre else prompt
        return (["claude", "-p", "--model", slug, "--permission-mode", "plan"], body)
    if vendor == "codex":
        argv = routing.codex_exec_argv(slug, effort, sandbox="read-only", cwd_check=False)
        return (argv, prompt)
    if vendor == "gemini":
        # agy 는 effort 가 슬러그에 박힌다(gemini-3.8-flash-medium) - slug_for 가 붙인다.
        # ⚠ --disable-slash-commands 를 같이 주면 --mode plan 이 무효가 된다(실측 경고).
        return (["agy", "--print", prompt, "--model", slug,
                 "--mode", "plan", "--output-format", "text"], None)
    if vendor == "grok":
        return (["grok", "-p", prompt, "-m", lane, "--reasoning-effort", effort,
                 "--permission-mode", "plan", "--output-format", "plain"], None)
    raise ValueError("실행 백엔드가 없는 벤더: %s" % vendor)


def _resolve(argv):
    """Windows 의 .cmd/.bat 심은 cmd /c 로 감싸야 subprocess 가 찾는다."""
    exe = shutil.which(argv[0])
    if exe and os.path.splitext(exe)[1].lower() in (".cmd", ".bat"):
        return ["cmd", "/c", exe] + list(argv[1:])
    return ([exe] + list(argv[1:])) if exe else list(argv)


def _dry_answer(lane):
    """--dry 용 결정적 가짜 응답. 네트워크를 타지 않고 배선만 검사한다.

    일부러 **정답이 아닌 값**을 낸다 - dry 결과가 점수로 섞이면 안 되기 때문이고,
    섞였는지는 mode 필드로도 걸러진다(--report 가 dry 행을 제외한다).
    """
    return "범위: dry 모드 (실호출 없음)\nANSWER: DRY-%s" % lane


def run_lane(lane, effort, prompt, cwd, timeout=900, dry=False):
    """레인 하나를 동기 호출. 반환 (rc, stdout, stderr, sec)."""
    argv, stdin = exec_plan(lane, effort, prompt)
    if dry:
        return 0, _dry_answer(lane), "", 0.0
    t0 = time.time()
    try:
        p = subprocess.run(_resolve(argv), input=(stdin or ""), capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           cwd=cwd, timeout=timeout, shell=False)
    except subprocess.TimeoutExpired:
        return 124, "", "timeout %ds" % timeout, time.time() - t0
    except Exception as e:  # noqa: BLE001
        return 1, "", type(e).__name__, time.time() - t0
    return (p.returncode, (p.stdout or "").strip(),
            (p.stderr or "").strip()[:800], time.time() - t0)


ANSWER_RE = re.compile(r"^\s*ANSWER\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)


def extract_answer(text):
    """마지막 `ANSWER: <값>` 을 뽑는다. CLI 가 훅 로그를 섞어 찍으므로 마지막 것을 쓴다."""
    hits = ANSWER_RE.findall(text or "")
    return hits[-1].strip() if hits else None


JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def extract_json(text):
    m = JSON_RE.search(text or "")
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:  # noqa: BLE001
        return None


# ------------------------------------------------------------------ prompts
def producer_prompt(probe, repo):
    return """%s

[답 형식 - 이대로 지킬 것]
마지막 줄에 정확히 이 한 줄만 둔다:
ANSWER: <값>

[규칙]
- 저장소는 읽기만 한다. 수정·커밋·체크아웃 금지.
- 값을 셀 때 **무엇을 어디까지 셌는지 범위**를 답 직전에 한 줄로 적는다.
- 모르면 `ANSWER: UNKNOWN` 을 쓰고 왜 모르는지 적는다.
  **틀린 값을 자신 있게 쓰는 것이 UNKNOWN 보다 나쁘게 채점된다.**
""" % probe["prompt"].replace("{repo}", repo)


def grader_prompt(probe, truth, ans_a, ans_b):
    return """너는 채점자다. 아래 문제에 대해 두 답을 채점한다.

[문제]
%s

[기계가 만든 정답 - 이것이 기준이다. 네가 다시 계산하지 마라]
%s

[답 A]
%s

[답 B]
%s

[채점 방법 - 순서를 지킬 것]
1) **먼저 둘 다 틀렸을 가능성을 본다.** 정답과 형식이 달라 보이는 것과 값이 다른 것을
   구분하라(예: "12" 와 "12개" 는 같은 값이다).
2) 각 답에 correct = true/false 를 준다. 정답과 값이 같으면 true.
   UNKNOWN 은 false 지만 **틀린 확답보다 감점이 작다**(아래 evidence 로 반영).
3) evidence 점수 0~3: 범위를 명시했나 · 근거를 댔나 · 추측을 사실처럼 쓰지 않았나.
4) 한 줄 사유.

[출력 - JSON 만. 다른 말 금지. 도구를 쓰지 말고 위 정보만으로 판단한다]
{"a": {"correct": true, "evidence": 2, "why": "..."},
 "b": {"correct": false, "evidence": 0, "why": "..."},
 "both_wrong_considered": "어떻게 확인했는지 한 줄"}
""" % (probe["prompt"], truth, ans_a, ans_b)


# ------------------------------------------------------------ 벤더 가용성
def _why_down(blob):
    b = (blob or "").lower()
    if "402" in b or "balance" in b or "payment required" in b:
        return "잔액 소진(402)"
    if "ineligibletier" in b or "no longer supported" in b:
        return "이 CLI 가 계정 티어에서 막힘"
    if "401" in b or "unauthorized" in b or "please log in" in b:
        return "인증 필요"
    if "timeout" in b:
        return "응답 없음(timeout)"
    if "429" in b or "quota" in b or "rate limit" in b:
        return "쿼터·레이트 한도"
    return "ANSWER 줄을 못 받음"


def preflight(repo, force=False, dry=False):
    """벤더마다 아주 싼 호출 1회로 '지금 답을 만들 수 있는가'를 본다.

    왜 필요한가: 2026-09-13 실측에서 grok 은 402(잔액 소진), gemini 단독 CLI 는
    IneligibleTierError 였다. 쿼터 %만 보면 둘 다 '여유 있음'으로 보인다 -
    **못 쓰는 이유가 쿼터가 아니기 때문이다.** 가용성은 호출해봐야 안다.
    """
    if dry:
        return {v: {"ok": True, "note": "dry"} for v in ALL_VENDORS}
    if not force and os.path.isfile(VENDOR_CACHE):
        try:
            c = json.load(open(VENDOR_CACHE, encoding="utf-8"))
            if (int(c.get("verdict_v") or 0) >= VERDICT_V
                    and (time.time() - c.get("at_epoch", 0)) < VENDOR_CACHE_HOURS * 3600):
                return c["vendors"]
        except Exception:  # noqa: BLE001
            pass
    probe_lane = {"claude": "claude-opus-5", "codex": "gpt-5.6-luna",
                  "gemini": "gemini-3.8-flash", "grok": "grok-4.6"}
    probe_eff = {"claude": "standard", "codex": "low", "gemini": "low", "grok": "high"}
    out = {}
    for v in ALL_VENDORS:
        rc, so, se, sec = run_lane(probe_lane[v], probe_eff[v], PING, repo, timeout=300)
        ans = extract_answer(so)
        # 2026-09-20: rc 를 받아놓고 쓰지 않았다. 종료코드 1 짜리 실패 응답이라도 본문에
        # ANSWER 줄만 있으면 '가용'으로 6시간 캐시됐다 - G12 는 '쿼터로는 안 보이는 불가용'을
        # 잡으려고 만든 게이트인데 바로 그 자리에서 열려 있었다. rc 를 판정에 넣는다.
        ok = (rc == 0) and (ans is not None)
        if ans is not None and rc != 0:
            note = f"종료코드 {rc} - 답은 왔지만 호출이 실패했다"
        else:
            note = "ok" if ok else _why_down(so + "\n" + se)
        out[v] = {"ok": ok, "note": note, "sec": round(sec, 1), "rc": rc}
    os.makedirs(STATE_DIR, exist_ok=True)
    json.dump({"verdict_v": VERDICT_V,
               "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "at_epoch": time.time(),
               "vendors": out}, open(VENDOR_CACHE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return out


# --------------------------------------------------------------------- 실행
def plan_round(repo, seed=None, exclude=()):
    probes = load_probes()
    rng = random.Random(seed if seed is not None else int(time.time()))
    rows = []
    for p in probes:
        m, note = pick_matchup(p, rng, exclude_vendors=exclude)
        rows.append({"probe": p["id"], "domain": p["domain"], "class": p["class"],
                     "matchup": m, "skip_reason": note,
                     "guards": check_g10(m) if m else ["SKIPPED"]})
    return rows


def append_ledger(rows):
    """원장 append. 쓰기 전에 기존 행이 한 줄도 안 사라졌는지 검사한다.

    검사가 append 용이라는 것을 명시한다 - prepend 에 이 검사를 쓰면 안 된다
    (2026-09-13 에 색인에서 정확히 그 실수를 했다).
    """
    os.makedirs(STATE_DIR, exist_ok=True)
    prev = ""
    if os.path.isfile(LEDGER):
        prev = open(LEDGER, encoding="utf-8").read()
        if prev and not prev.endswith("\n"):
            prev += "\n"
    before = prev.splitlines()
    body = prev + "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    tmp = LEDGER + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    after = open(tmp, encoding="utf-8").read().splitlines()
    if len(after) != len(before) + len(rows) or after[:len(before)] != before:
        os.remove(tmp)
        raise SystemExit("원장 append 검사 실패 - 원본을 건드리지 않았다")
    shutil.move(tmp, LEDGER)
    return len(rows)


def cmd_validate(args):
    """정답 생성기를 전부 돌려본다. 비용 0. 평가 전에 이걸 먼저 통과해야 한다."""
    probes = load_probes()
    print("=== 정답 생성기 점검 (repo=%s) ===" % args.repo)
    bad = 0
    for p in probes:
        truth, err = ground_truth(p, args.repo)
        if truth is None:
            bad += 1
            print("  %-24s ❌ %s" % (p["id"], err))
        else:
            one = truth if len(truth) <= 60 else truth[:57] + "..."
            print("  %-24s ✅ %-22s 정답=%s" % (p["id"], p["truth_post"], one))
    print("\n%d/%d 통과" % (len(probes) - bad, len(probes)))
    if bad:
        print("⚠ 정답이 안 만들어지는 probe 는 채점이 불가능하다 - 그 문제는 라운드에서 빠진다.")
    return 1 if bad else 0


def _print_vendors(vend):
    print("=== 벤더 가용성 (실호출로 확인) ===")
    for name in ALL_VENDORS:
        s = vend.get(name) or {}
        print("  %-8s %s  %s" % (name, "✅" if s.get("ok") else "❌", s.get("note", "")))


def cmd_preflight(args):
    vend = preflight(args.repo, force=args.force, dry=args.dry)
    _print_vendors(vend)
    up = sorted(k for k, s in vend.items() if s.get("ok"))
    print("\n쓸 수 있는 벤더 %d개: %s" % (len(up), ", ".join(up) or "없음"))
    if len(up) < 3:
        print("⚠ G10 은 벤더 3개를 요구한다. 지금은 채점자를 분리할 수 없어 전 probe 가 건너뛰어진다.")
        return 1
    return 0


def cmd_plan(args):
    rows = plan_round(args.repo, args.seed)
    print("=== 적대적 평가 대진표 (비용 0 · 호출 안 함) ===")
    ok = True
    for r in rows:
        if not r["matchup"]:
            print("  %-24s SKIP - %s" % (r["probe"], r["skip_reason"]))
            continue
        m = r["matchup"]
        bad = [g for g in r["guards"] if g.startswith("G10")]
        if bad:
            ok = False
        print("  %-24s [%s] A=%-20s B=%-20s 채점=%-20s %s"
              % (r["probe"], r["domain"], m["producer_a"], m["producer_b"],
                 m["grader"], ("!! " + ",".join(bad)) if bad else ""))
    print("\n정답은 probe 의 truth_cmd + truth_post 가 만든다(채점자가 짓지 않는다).")
    print("이 표는 **가용성을 안 본다** - `--run` 이 preflight 로 죽은 벤더를 빼고 다시 짠다.")
    return 0 if ok else 1


def cmd_due(args):
    last = None
    if os.path.isfile(LEDGER):
        for line in open(LEDGER, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            if r.get("mode") == "dry":
                continue
            last = r.get("at") or last
    if not last:
        print("적대적 평가 기록 없음 - 한 번도 안 돌렸다. 권장: 지금 1회차.")
        return 1
    age = (time.time() - time.mktime(time.strptime(last[:19], "%Y-%m-%dT%H:%M:%S"))) / 86400
    print("마지막 평가 %s (%.1f일 전) · 주기 %d일" % (last, age, DUE_DAYS))
    if age >= DUE_DAYS:
        print("→ 평가할 때가 됐다. `--validate` → `--plan` → `--run` 순으로 간다.")
        return 1
    print("→ 아직 아니다.")
    return 0


def cmd_run(args):
    probes = {p["id"]: p for p in load_probes()}
    if args.only:
        missing = [i for i in args.only if i not in probes]
        if missing:
            raise SystemExit("모르는 probe: %s" % ", ".join(missing))

    vend = preflight(args.repo, force=args.force, dry=args.dry)
    _print_vendors(vend)
    down = tuple(k for k, s in vend.items() if not s.get("ok"))
    if len(ALL_VENDORS) - len(down) < 3:
        print("\n⛔ 쓸 수 있는 벤더가 3개 미만이다. G10 을 어기느니 라운드를 포기한다.")
        return 2

    rows = plan_round(args.repo, args.seed, exclude=down)
    if args.only:
        rows = [r for r in rows if r["probe"] in args.only]
    round_id = "ae_%s" % time.strftime("%y%m%d_%H%M%S")
    at = time.strftime("%Y-%m-%dT%H:%M:%S")
    mode = "dry" if args.dry else "live"
    out, skipped = [], []
    print("\n=== 회차 %s (%s) · probe %d개 ===" % (round_id, mode, len(rows)))

    for r in rows:
        pid = r["probe"]
        p = probes[pid]
        if not r["matchup"]:
            print("  %-24s SKIP - %s" % (pid, r["skip_reason"]))
            skipped.append((pid, r["skip_reason"]))
            continue
        bad = [g for g in r["guards"] if g.startswith("G10")]
        if bad:
            print("  %-24s SKIP - G10 위반 %s" % (pid, bad))
            skipped.append((pid, "G10 %s" % bad))
            continue
        truth, err = ground_truth(p, args.repo)
        if truth is None:
            print("  %-24s SKIP - %s" % (pid, err))
            skipped.append((pid, err))
            continue
        m = r["matchup"]
        pp = producer_prompt(p, args.repo)
        fal = (p.get("class") == "B")
        eff = {k: routing.effort_for(m[k], fal) for k in
               ("producer_a", "producer_b", "grader")}
        print("  %-24s 정답=%s" % (pid, truth if len(truth) <= 40 else truth[:37] + "..."))

        res = {}
        for role in ("producer_a", "producer_b"):
            lane = m[role]
            rc, so, se, sec = run_lane(lane, eff[role], pp, args.repo,
                                       timeout=args.timeout, dry=args.dry)
            ans = extract_answer(so)
            res[role] = {"lane": lane, "effort": eff[role], "rc": rc, "sec": sec,
                         "answer": ans, "raw_tail": (so or se)[-400:]}
            print("      %-10s %-20s @%-8s %5.0fs → %s"
                  % (role, lane, eff[role], sec,
                     ans if ans else "‼ ANSWER 없음 (%s)" % _why_down(so + se)))

        gl, ge = m["grader"], eff["grader"]
        gp = grader_prompt(
            p, truth,
            res["producer_a"]["answer"] or res["producer_a"]["raw_tail"],
            res["producer_b"]["answer"] or res["producer_b"]["raw_tail"])
        grc, gso, gse, gsec = run_lane(gl, ge, gp, args.repo,
                                       timeout=args.timeout, dry=args.dry)
        if args.dry:
            verdict = {"a": {"correct": False, "evidence": 0, "why": "dry"},
                       "b": {"correct": False, "evidence": 0, "why": "dry"},
                       "both_wrong_considered": "dry"}
        else:
            verdict = extract_json(gso)
        if verdict is None:
            print("      채점 실패 - JSON 을 못 받았다 (%s). 이 probe 는 점수에 안 넣는다."
                  % _why_down(gso + gse))
            out.append({"at": at, "round": round_id, "probe": pid, "domain": p["domain"],
                        "class": p["class"], "role": "grader", "lane": gl, "effort": ge,
                        "vendor": VENDOR_OF[gl], "mode": mode, "sec": round(gsec, 1),
                        "rc": grc, "grader_failed": True, "truth": truth,
                        "guard_violations": []})
            continue
        print("      %-10s %-20s @%-8s %5.0fs → a=%s b=%s"
              % ("grader", gl, ge, gsec,
                 verdict.get("a", {}).get("correct"), verdict.get("b", {}).get("correct")))
        for role, key in (("producer_a", "a"), ("producer_b", "b")):
            v = verdict.get(key) or {}
            out.append({
                "at": at, "round": round_id, "probe": pid, "domain": p["domain"],
                "class": p["class"], "role": role, "lane": res[role]["lane"],
                "effort": res[role]["effort"], "vendor": VENDOR_OF[res[role]["lane"]],
                "answer": res[role]["answer"], "correct": bool(v.get("correct")),
                "evidence": int(v.get("evidence") or 0), "why": (v.get("why") or "")[:300],
                "sec": round(res[role]["sec"], 1), "rc": res[role]["rc"],
                "grader": gl, "grader_vendor": VENDOR_OF[gl], "truth": truth,
                "mode": mode, "guard_violations": check_g10(m),
            })

    if skipped:
        print("\n건너뛴 probe %d개 (조용히 넘기지 않는다):" % len(skipped))
        for pid, why in skipped:
            print("  - %-24s %s" % (pid, why))
    if not out:
        print("\n기록할 행이 없다.")
        return 1
    if args.dry:
        print("\n[dry] 원장에 쓰지 않는다. 행 %d개를 만들 수 있었다." % len(out))
        return 0
    n = append_ledger(out)
    print("\n원장 append %d행 → %s" % (n, LEDGER))
    print("다음: `--report` 로 누적 점수를 본다. 표는 자동으로 안 고친다.")
    return 0


def cmd_report(args):
    if not os.path.isfile(LEDGER):
        print("기록 없음 (%s)" % LEDGER)
        return 0
    agg = {}
    skipped = 0
    for line in open(LEDGER, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        if r.get("mode") == "dry" or r.get("grader_failed"):
            skipped += 1
            continue
        k = (r.get("domain"), r.get("lane"), r.get("effort"))
        a = agg.setdefault(k, {"n": 0, "correct": 0, "evidence": 0, "sec": 0})
        a["n"] += 1
        a["correct"] += 1 if r.get("correct") else 0
        a["evidence"] += r.get("evidence") or 0
        a["sec"] += r.get("sec") or 0
    if not agg:
        print("유효 행 0건 (제외 %d행: dry·채점실패)" % skipped)
        return 0
    print("%-18s %-22s %-10s %4s %7s %6s %7s" %
          ("DOMAIN", "LANE", "EFFORT", "N", "정답률", "근거", "평균초"))
    best = {}
    for (dom, lane, eff), a in sorted(agg.items()):
        acc = a["correct"] / a["n"]
        ev = a["evidence"] / a["n"]
        print("%-18s %-22s %-10s %4d %6.0f%% %6.2f %7.0f"
              % (dom, lane, eff, a["n"], acc * 100, ev, a["sec"] / a["n"]))
        score = acc * 2 + ev / 3.0
        if a["n"] >= 3 and score > best.get(dom, (None, -1))[1]:
            best[dom] = ((lane, eff), score)
    if skipped:
        print("\n(제외 %d행 - dry 또는 채점 실패. 점수에 안 들어간다)" % skipped)
    # 포화 검사 — 전 레인이 다 맞히면 이 문제 세트는 **레인을 못 가른다.**
    # 100% 를 "모두 훌륭하다"로 읽으면 안 된다. 자가 너무 무딘 것이다.
    tot_n = sum(a["n"] for a in agg.values())
    tot_ok = sum(a["correct"] for a in agg.values())
    ev_max = max((a["evidence"] / a["n"]) for a in agg.values())
    if tot_n and tot_ok == tot_n:
        print("")
        print("⚠ 정답률이 전 레인 100%% (%d/%d) — 이 문제 세트는 레인을 못 가른다." % (tot_ok, tot_n))
        print("  '모두 훌륭하다'가 아니라 '자가 무디다'로 읽는다. 더 어려운 probe 가 필요하다:")
        print("  · 답은 한 줄인데 **틀리기 쉬운 것** — 집계 단위가 헷갈리는 수,")
        print("    위임·분기 너머의 사실, 부재와 오류가 같은 종료코드를 내는 확인,")
        print("    이름이 같고 뜻이 다른 값(예: 두 체계에 다 있는 `now`)")
    if tot_n and ev_max <= 1.0:
        print("")
        print("⚠ 근거 점수가 전 레인 %.2f 이하다(만점 3) — 채점자가 인색하거나 루브릭이 안 걸린다." % ev_max)
        print("  생산자에게 '범위 한 줄'을 요구하는데 채점자가 그걸 근거로 안 세고 있을 수 있다.")

    print("\n=== 제안 (표는 자동으로 안 고친다) ===")
    if not best:
        print("  관측 부족 - 영역별 3회 이상 필요. 지금은 제안하지 않는다.")
    for dom, ((lane, eff), score) in sorted(best.items()):
        print("  %-18s → %s @%s  (점수 %.2f)" % (dom, lane, eff, score))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--due", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--dry", action="store_true", help="실호출 없이 배선만 검사")
    ap.add_argument("--force", action="store_true", help="가용성 캐시 무시")
    ap.add_argument("--only", nargs="*", help="probe id 만 골라 실행")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--repo", default="E:/2ndB")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    if args.due:
        return cmd_due(args)
    if args.validate:
        return cmd_validate(args)
    if args.preflight:
        return cmd_preflight(args)
    if args.report:
        return cmd_report(args)
    if args.run:
        return cmd_run(args)
    return cmd_plan(args)


if __name__ == "__main__":
    sys.exit(main())
