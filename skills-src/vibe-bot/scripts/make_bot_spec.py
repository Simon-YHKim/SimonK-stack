#!/usr/bin/env python3
"""vibe-bot - build a Grok Bot task sheet, gate it, route it, and check what comes back.

Stage 1 (2026-09-17): composing, gating and checking all run offline. Delivery
over a webhook stays refused until the transport is measured once, because xAI
publishes no official Grok Bot task API and the webhook trigger appears only in
third-party write-ups.

Console mode (2026-09-19, Simon): console and GUI work goes to Grok Bot with an
explicit sheet - target, goal, scope, buttons it must not press, stop points,
screen evidence and result format. The result check then also demands screen
evidence (C1) and escalates any report of an irreversible action (C2).

Roster and hub bus (0.4.0, 2026-09-19): bots.json names the owning bot for each
kind of work. --deliver hub drops the sheet into that bot's hub inbox
(AI Infra/Communication/bots/<id>/inbox) and the bot writes its result to the
matching outbox. --collect scans every outbox once and checks each result.

Usage:
    python make_bot_spec.py --task "<request>" [--deliver manual|hub|webhook|github] [--bot <id|name>]
    python make_bot_spec.py --mode console --target "<console · app id>" --task "<goal>"
                            [--url URL] [--allow-change "<item and value>"] [--forbid "<button>"]
    python make_bot_spec.py --verify <result file> --nonce <nonce> [--mode console]
    python make_bot_spec.py --collect [--nonce <nonce>]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
DEFAULT_OUT = Path(os.environ.get("VIBE_BOT_OUT", r"E:\Coding Infra\reports"))
WEBHOOK_URL_ENV = "GROK_BOT_WEBHOOK_URL"
WEBHOOK_KEY_ENV = "GROK_BOT_WEBHOOK_KEY"
# Flipped to True only after one measured end-to-end webhook run (see SKILL.md).
TRANSPORT_VERIFIED = False
SKILL_DIR = Path(__file__).resolve().parent.parent
ROSTER_PATH = SKILL_DIR / "bots.json"
HUB_DIR = Path(os.environ.get("VIBE_BOT_HUB", r"E:\Coding Infra\AI Infra\Communication"))

SECRET_PATTERNS = [
    ("openai/anthropic style key", re.compile(r"\b(?:sk|pk)-[A-Za-z0-9_-]{16,}")),
    ("cursor key", re.compile(r"\bcrsr_[A-Za-z0-9]{16,}")),
    ("github token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}")),
    ("xai key", re.compile(r"\bxai-[A-Za-z0-9]{16,}")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("password assignment", re.compile(
        r"(?i)\b(?:password|passwd|비밀번호|암호)\s*[:=]\s*\S+")),
    ("token assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|token|secret|자격증명)\s*[:=]\s*\S+")),
]

WRITE_PATTERNS = [
    ("repo write / merge", re.compile(
        r"(?i)(?:\bgit\s+(?:push|merge|reset|rebase)\b|force[- ]push|"
        r"머지(?:해|하고|해줘|할)|병합해|pull request.*머지|auto[- ]?merge)")),
    ("deploy / release", re.compile(
        r"(?i)(?:\bdeploy\b|배포(?:해|하고|해줘)|릴리스해|프로덕션에 올려|production 반영)")),
    ("delete / drop", re.compile(
        r"(?i)(?:\brm\s+-rf\b|drop\s+table|삭제(?:해|하고|해줘)|지워(?:줘|버려)|계정을 정리해)")),
    ("payment", re.compile(
        r"(?i)(?:결제(?:해|하고|해줘)|구매해|송금|환불 처리|카드로 지불|subscribe and pay)")),
    ("permission change", re.compile(
        r"(?i)(?:권한을 (?:바꾸|부여|변경)|access.*grant|IAM 정책 변경|공개로 전환)")),
]

CONFIDENTIAL_PATTERNS = [
    ("company confidential hint", re.compile(
        r"(?i)(?:\bLOT\b|설비명|공정 ?수치|택트 ?타임 실측|CapEx|고객사명|단가표|원가표)")),
]

SCOPE_WORDS = re.compile(
    r"(?i)(?:범위|스캔|검색한|조회한|찾아본|확인한 곳|\d+\s*곳|에서 확인|searched|scanned|"
    r"scope|looked at|checked \d)")
# A line that names its own source (URL or bare domain) is scoped by that source,
# e.g. a table row "| Cursor | 변경일 없음 | cursor.com/pricing |" (2026-09-19 pilot).
SOURCE_RE = re.compile(
    r"(?i)(?:https?://\S+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\."
    r"(?:com|ai|dev|io|org|net|co|app|gov|edu|kr)\b)")
ABSENCE_WORDS = re.compile(
    r"(?i)(?:0\s*건|없었|없습니다|없음|찾지 못|not found|no results|none found)")
EVIDENCE_WORDS = re.compile(
    r"(?i)(?:https?://|\.md\b|\.py\b|\.json\b|:\d+\b|출처|근거|source:)")
CONCLUSION_WORDS = re.compile(
    r"(?i)(?:결론|판단하면|추정|원인은|때문이다|therefore|conclusion|root cause)")

SPEC_SECTIONS = ("Outcome", "Sources", "Constraints", "Deliverable", "Review point")

# --- console mode ---------------------------------------------------------------
CONSOLE_SECTIONS = ("대상", "목표", "범위", "누르지 말 것", "멈춤 지점", "증거", "결과 형식",
                    "Review point")
CONSOLE_FORBID_DEFAULT = (
    "제출 · Submit", "게시 · Publish", "출시 · Release · Rollout", "검토 요청 · Send for review",
    "Reply · 답변 보내기", "Resubmit", "삭제 · Delete · Archive", "결제 · 구매 · 구독 · Purchase",
    "권한 변경 · 사용자 초대 · Invite", "허용 변경 밖의 저장 · Save",
)
CONSOLE_STOPS = (
    "로그인 · 2단계 인증 · 비밀번호 입력 화면",
    "결제 · 카드 · 구독 화면",
    "'누르지 말 것' 버튼이 필요한 순간 - 누르기 직전에 멈추고 사람 승인을 받는다",
    "지시와 다른 화면이나 경고가 나올 때",
)
# Screen evidence: a menu path ("출시 > 프로덕션", "→"), or a screenshot mention.
SCREEN_EVIDENCE_RE = re.compile(
    r"(?i)(?:\S\s>\s\S|→|메뉴 경로|화면 경로|스크린샷|screenshot|\.png\b|\.jpe?g\b)")
# A report that an irreversible action was carried out. Reading a status label such
# as "제출 완료" also matches - that errs on the safe side (a human looks).
IRREVERSIBLE_DONE_RE = re.compile(
    r"(?i)(?:(?:제출|게시|출시|전송|발송|삭제|결제|구매|구독|답변|회신|업로드|"
    r"reply|resubmit|submit|publish|release|upload)"
    r"[^\n]{0,6}?(?:했|함|완료|됐|하였|눌렀|보냈)"
    r"|\b(?:submitted|published|released|deleted|purchased|sent the reply)\b)")


def make_nonce() -> str:
    return "vb-" + secrets.token_hex(4)


def now_kst() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")


def check_request(task: str) -> dict:
    """Return {'blocks': [...], 'warns': [...]} for one request string."""
    blocks, warns = [], []
    for label, rx in SECRET_PATTERNS:
        if rx.search(task):
            blocks.append(f"B1 자격증명 추정 문자열({label})이 요청에 있다")
    for label, rx in WRITE_PATTERNS:
        if rx.search(task):
            blocks.append(f"B2 봇에게 위임하지 않는 작업({label})이다")
    for label, rx in CONFIDENTIAL_PATTERNS:
        if rx.search(task):
            warns.append(f"B3 회사 기밀일 수 있는 표현({label}) - 보내기 전에 지운다")
    if len(task.strip()) < 12:
        warns.append("요청이 너무 짧다 - Outcome 한 줄을 더 쓰면 결과가 좋아진다")
    return {"blocks": blocks, "warns": warns}


def build_spec(task: str, nonce: str, *, sources: str = "", constraints: str = "",
               deliverable: str = "", review: str = "", return_to: str = "") -> str:
    sources = sources or "봇이 접근 가능한 공개 웹. 로그인이 필요한 곳은 들어가지 않는다."
    constraints = constraints or (
        "파일을 고치거나 배포·결제·삭제하지 않는다. 승인 요청이 뜨면 멈추고 사람을 기다린다.")
    deliverable = deliverable or "표 1개(행별 출처 링크 포함)와 한 줄 요약."
    review = review or "표의 행 수와 출처 링크가 맞는지 사람이 확인한 뒤 사용한다."
    return_to = return_to or "이 대화창"
    return "\n".join([
        f"# Grok Bot 과제서 · {nonce}",
        f"작성 {now_kst()} · 발행 Claude Code · 스킬 vibe-bot",
        "",
        "## Outcome",
        task.strip(),
        "",
        "## Sources",
        sources,
        "",
        "## Constraints",
        constraints,
        "- 부재 보고에는 찾은 범위를 쓴다. 범위 없는 '0건'은 결과로 인정하지 않는다.",
        "- 판단에는 근거(URL·파일·명령 출력)를 붙인다.",
        "- 자격증명을 묻거나 되돌려 보내지 않는다. 로그인 화면이 나오면 사람에게 넘긴다.",
        "",
        "## Deliverable",
        deliverable,
        f"- 결과 첫 줄에 이 표식을 그대로 적는다: {nonce}",
        f"- 결과는 {return_to}에 남긴다.",
        "",
        "## Review point",
        review,
        "",
    ])


def build_console_spec(task: str, nonce: str, *, target: str, url: str = "",
                       allow_change: str = "", extra_forbid=(), return_to: str = "") -> str:
    """Console / GUI task sheet. Every slot is filled - an empty slot is where a bot guesses."""
    return_to = return_to or "이 대화창"
    forbid = list(CONSOLE_FORBID_DEFAULT) + [x.strip() for x in extra_forbid if x and x.strip()]
    if allow_change.strip():
        scope = (f"허용 변경: {allow_change.strip()} - 이것 말고는 아무것도 바꾸지 않는다. "
                 "바꾸기 직전 화면을 증거로 남기고, 저장·제출 버튼은 누르기 직전에 멈춰 사람 승인을 받는다.")
    else:
        scope = "읽기 전용. 어떤 값도 바꾸거나 저장하지 않는다."
    target_line = target.strip() + (f" · 시작 URL {url.strip()}" if url.strip() else "")
    return "\n".join([
        f"# Grok Bot 콘솔 과제서 · {nonce}",
        f"작성 {now_kst()} · 발행 Claude Code · 스킬 vibe-bot (콘솔 모드)",
        "",
        "## 대상",
        target_line,
        "",
        "## 목표 (Outcome)",
        task.strip(),
        "",
        "## 범위",
        scope,
        "",
        "## 누르지 말 것",
        *[f"- {x}" for x in forbid],
        "",
        "## 멈춤 지점 - 여기서는 멈추고 사람에게 넘긴다",
        *[f"- {x}" for x in CONSOLE_STOPS],
        "",
        "## 증거 - 화면마다",
        "- 메뉴 경로 (예: 출시 > 프로덕션)",
        "- 그 화면에서 읽은 값 그대로",
        "- 스크린샷 1장",
        "- 찾지 못한 항목은 어느 메뉴까지 봤는지 적는다. 범위 없는 '없음'은 결과로 인정하지 않는다.",
        "- 자격증명을 묻거나 되돌려 보내지 않는다.",
        "",
        "## 결과 형식 (Deliverable)",
        f"- 첫 줄에 이 표식을 그대로 적는다: {nonce}",
        "- 표 하나: 항목 | 값 | 화면 경로 | 스크린샷",
        "- 한 일과 하지 않은 일을 나눠 적는다. 누른 버튼이 있으면 이름을 그대로 적는다.",
        "- 다음 행동은 누르지 말고 제안만 한다.",
        f"- 결과는 {return_to}에 남긴다.",
        "",
        "## Review point",
        "사람이 표의 값과 스크린샷을 대조한 뒤 쓴다. 되돌릴 수 없는 버튼은 사람이 승인한다.",
        "",
    ])


def verify_result(text: str, nonce: str, mode: str = "general") -> list[str]:
    """Return a list of findings. Empty list means the result is usable."""
    findings = []
    if nonce and nonce not in text:
        findings.append(f"B5 결과에 nonce({nonce})가 없다 - 다른 실행의 결과일 수 있다")
    for label, rx in SECRET_PATTERNS:
        if rx.search(text):
            findings.append(f"B1 결과에 자격증명 추정 문자열({label})이 섞여 있다")
    if _absence_unscoped(text):
        findings.append("G6 범위 없는 부재 보고 - 어디를 찾았는지가 없다")
    if CONCLUSION_WORDS.search(text) and not (
            EVIDENCE_WORDS.search(text) or SOURCE_RE.search(text)):
        findings.append("B4 근거 없는 결론 - 출처나 파일 표기가 없다")
    if mode == "console":
        if not SCREEN_EVIDENCE_RE.search(text):
            findings.append("C1 화면 근거 없음 - 메뉴 경로나 스크린샷이 없다")
        hit = IRREVERSIBLE_DONE_RE.search(text)
        if hit:
            findings.append(f"C2 되돌릴 수 없는 동작 보고('{hit.group(0)[:30]}') - "
                            "사람이 콘솔에서 바로 확인한다")
    return findings


def _absence_unscoped(text: str) -> bool:
    """An absence claim is scoped if the text states a search scope anywhere,
    or if every line that reports an absence names its own source."""
    if not ABSENCE_WORDS.search(text) or SCOPE_WORDS.search(text):
        return False
    return any(ABSENCE_WORDS.search(line) and not SOURCE_RE.search(line)
               for line in text.splitlines())


# --- roster and hub bus (0.4.0) -----------------------------------------------------
def load_roster(path: Path = ROSTER_PATH) -> list[dict]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return data.get("bots", [])


def resolve_bot(roster: list[dict], target: str = "", task: str = "",
                explicit: str = "") -> dict | None:
    """Pick the bot that owns this work. An explicit --bot (id or name) wins; otherwise
    the roster entry whose keywords hit target + task most often; ties go to roster
    order; nothing matched falls back to the default bot."""
    if explicit:
        key = explicit.strip().lower()
        for b in roster:
            if key in (b["id"].lower(), b["name"].lower()):
                return b
        return None
    text = f"{target} {task}".lower()
    best, best_hits = None, 0
    for b in roster:
        hits = sum(1 for k in b.get("keywords", []) if k.lower() in text)
        if hits > best_hits:
            best, best_hits = b, hits
    if best is None:
        best = next((b for b in roster if b.get("default")), None)
    return best


def load_projects(path: Path = ROSTER_PATH) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data.get("projects", {})


def resolve_project(projects: dict, target: str = "", task: str = "",
                    explicit: str = "") -> str | None:
    """Pick the project this task belongs to (0.6.0). Bots are shared - the project is
    chosen per task. An explicit --project wins; otherwise the project whose keywords
    hit target + task most often; nothing matched means the shared hub bus."""
    if explicit:
        key = explicit.strip().lower()
        for pid in projects:
            if pid.lower() == key:
                return pid
        return None
    text = f"{target} {task}".lower()
    best, best_hits = None, 0
    for pid, p in projects.items():
        hits = sum(1 for k in p.get("keywords", []) if k.lower() in text)
        if hits > best_hits:
            best, best_hits = pid, hits
    return best


def bus_root(hub: Path = HUB_DIR, projects: dict | None = None,
             project_id: str | None = None) -> Path:
    """Where the sheet and the result land: that project's own bus when the task belongs
    to a project (2nd-B -> E:/2ndB/.bots, so the work accumulates with the project),
    otherwise the shared hub."""
    proj = (projects or {}).get(project_id or "")
    if proj and proj.get("root"):
        return Path(proj["root"]) / proj.get("bus", ".bots")
    return Path(hub) / "bots"


def hub_paths(bot: dict, nonce: str, hub: Path = HUB_DIR, projects: dict | None = None,
              project_id: str | None = None) -> dict:
    base = bus_root(hub, projects, project_id) / bot["id"]
    return {"inbox": base / "inbox" / f"{nonce}.md",
            "meta": base / "inbox" / f"{nonce}.meta.json",
            "result": base / "outbox" / f"{nonce}.result.md"}


def add_routing(spec: str, bot: dict | None, result_path: Path | None,
                project: tuple | None = None) -> str:
    """Insert 'which bot', 'which project' and 'where the result goes' under the titles.
    project = (id, root)."""
    if not bot:
        return spec
    extra = [f"보낼 봇: {bot['name']} ({bot['id']})"]
    if project:
        extra.append(f"프로젝트: {project[0]} · 루트 {project[1]} (이 경로를 기준으로 일한다)")
    if result_path:
        extra.append(f"결과 파일: {result_path} (대화창에도 같은 내용을 남긴다)")
    lines = spec.split("\n")
    return "\n".join(lines[:2] + extra + lines[2:])


def bus_roots(hub: Path = HUB_DIR, projects: dict | None = None) -> list[Path]:
    return [Path(hub) / "bots"] + [Path(p["root"]) / p.get("bus", ".bots")
                                   for p in (projects or {}).values() if p.get("root")]


def collect(hub: Path = HUB_DIR, nonce: str = "", projects: dict | None = None) -> list[dict]:
    """One-shot scan of every bot outbox on the hub and on each project bus - no
    polling (B7). Each result is checked with the mode recorded in its inbox meta."""
    rows, seen = [], set()
    for root in bus_roots(hub, projects):
        for res in sorted(root.glob("*/outbox/*.result.md")):
            if res in seen:
                continue
            seen.add(res)
            n = res.name[: -len(".result.md")]
            if nonce and n != nonce:
                continue
            meta_p = res.parent.parent / "inbox" / f"{n}.meta.json"
            mode = "general"
            if meta_p.exists():
                try:
                    mode = json.loads(meta_p.read_text(encoding="utf-8")).get("mode", "general")
                except ValueError:
                    pass
            text = res.read_text(encoding="utf-8", errors="replace")
            rows.append({"bot": res.parent.parent.name, "nonce": n, "mode": mode,
                         "path": str(res), "findings": verify_result(text, n, mode=mode)})
    return rows


def webhook_argv(url: str) -> list[str]:
    """Display-only argv. The key is referenced by env name, never inlined."""
    return [
        "curl", "-X", "POST", url,
        "-H", f"Authorization: Bearer ${WEBHOOK_KEY_ENV}",
        "-H", "Content-Type: application/json",
        "-d", "@spec.json",
    ]


def send_webhook(payload: dict) -> tuple[bool, str]:
    if not TRANSPORT_VERIFIED:
        return False, ("전달 경로가 아직 실측되지 않았다. SKILL.md '실측 절차'를 한 번 "
                       "통과한 뒤 TRANSPORT_VERIFIED 를 켠다.")
    url, key = os.environ.get(WEBHOOK_URL_ENV), os.environ.get(WEBHOOK_KEY_ENV)
    if not url or not key:
        return False, f"{WEBHOOK_URL_ENV} / {WEBHOOK_KEY_ENV} 가 환경에 없다(.env 확인)"
    import urllib.request
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return True, f"HTTP {resp.status}"
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as text
        return False, f"전송 실패: {type(exc).__name__}"


def write_outputs(spec: str, meta: dict, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"vibe-bot-{meta['nonce']}"
    spec_path = out_dir / f"{stem}.md"
    meta_path = out_dir / f"{stem}.meta.json"
    spec_path.write_text(spec, encoding="utf-8")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    return spec_path, meta_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Grok Bot task sheet builder")
    ap.add_argument("--task", help="what the bot should achieve")
    ap.add_argument("--mode", choices=("general", "console"), default="general",
                    help="console = console or GUI work with the explicit console sheet")
    ap.add_argument("--target", default="", help="console mode: console or app name and app/package id")
    ap.add_argument("--url", default="", help="console mode: start URL")
    ap.add_argument("--allow-change", dest="allow_change", default="",
                    help="console mode: the exact change allowed (default read-only)")
    ap.add_argument("--forbid", action="append", default=[],
                    help="console mode: extra button the bot must not press (repeatable)")
    ap.add_argument("--bot", default="", help="owning bot id or name (default: routed from bots.json)")
    ap.add_argument("--project", default="",
                    help="project id from bots.json (default: routed from its keywords; "
                         "none means the shared hub bus)")
    ap.add_argument("--hub", type=Path, default=None,
                    help="hub root holding bots/<id>/inbox|outbox; giving it sends every bot there "
                         "and ignores project buses (for tests)")
    ap.add_argument("--sources"), ap.add_argument("--constraints")
    ap.add_argument("--deliverable"), ap.add_argument("--review")
    ap.add_argument("--return-to", dest="return_to", default="")
    ap.add_argument("--deliver", choices=("manual", "hub", "webhook", "github"),
                    default="manual")
    ap.add_argument("--send", action="store_true",
                    help="actually POST the webhook (refused until measured)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--verify", type=Path, help="result file to check")
    ap.add_argument("--collect", action="store_true",
                    help="scan every bot outbox once and check each result")
    ap.add_argument("--nonce", default="")
    a = ap.parse_args(argv)
    hub = a.hub if a.hub is not None else HUB_DIR
    projects = {} if a.hub is not None else load_projects()

    if a.collect:
        rows = collect(hub, a.nonce, projects)
        if not rows:
            scope = ", ".join(str(r) for r in bus_roots(hub, projects))
            print(f"결과 없음 - 찾은 범위: {scope} 아래 */outbox/*.result.md")
            return 0
        bad = 0
        for r in rows:
            mark = "합격" if not r["findings"] else "불합격"
            print(f"[{mark}] {r['bot']} · {r['nonce']} · {r['mode']} · {r['path']}")
            for f in r["findings"]:
                print(f"    - {f}")
            bad += bool(r["findings"])
        return 1 if bad else 0

    if a.verify:
        text = a.verify.read_text(encoding="utf-8", errors="replace")
        findings = verify_result(text, a.nonce, mode=a.mode)
        if findings:
            print("결과 불합격:")
            for f in findings:
                print(f"  - {f}")
            return 1
        extra = ", 화면 근거 있음, 되돌릴 수 없는 동작 보고 없음" if a.mode == "console" else ""
        print("결과 합격 - nonce 확인, 범위 있는 보고, 근거 있음" + extra)
        return 0

    if not a.task:
        ap.error("--task, --verify, --collect 중 하나가 필요하다")

    gate = check_request(a.task)
    for w in gate["warns"]:
        print(f"[주의] {w}")
    if gate["blocks"]:
        print("이 요청은 봇에게 보내지 않는다:")
        for b in gate["blocks"]:
            print(f"  - {b}")
        return 2
    if a.mode == "console" and not a.target.strip():
        print("콘솔 모드는 --target 이 필요하다 (예: \"Google Play Console · com.example.app\")")
        return 2

    roster = load_roster()
    bot = resolve_bot(roster, a.target, a.task, a.bot)
    if a.bot and bot is None:
        print(f"명단에 없는 봇: {a.bot} - bots.json 의 id 또는 이름을 쓴다")
        return 2
    project_id = resolve_project(projects, a.target, a.task, a.project)
    if a.project and project_id is None:
        print(f"명단에 없는 프로젝트: {a.project} - bots.json 의 projects 키를 쓴다")
        return 2

    nonce = make_nonce()
    if a.mode == "console":
        spec = build_console_spec(a.task, nonce, target=a.target, url=a.url,
                                  allow_change=a.allow_change, extra_forbid=a.forbid,
                                  return_to=a.return_to)
    else:
        spec = build_spec(a.task, nonce, sources=a.sources or "",
                          constraints=a.constraints or "",
                          deliverable=a.deliverable or "", review=a.review or "",
                          return_to=a.return_to)
    paths = hub_paths(bot, nonce, hub, projects, project_id) if bot else None
    proj = projects.get(project_id or "")
    spec = add_routing(spec, bot, paths["result"] if paths else None,
                       (project_id, proj.get("root")) if proj else None)
    meta = {"nonce": nonce, "created": now_kst(), "deliver": a.deliver, "mode": a.mode,
            "bot": bot["id"] if bot else None, "project": project_id,
            "target": a.target, "task": a.task,
            "transport_verified": TRANSPORT_VERIFIED}
    spec_path, meta_path = write_outputs(spec, meta, a.out)
    print(f"과제서: {spec_path}")
    print(f"메타:   {meta_path}")
    print(f"nonce:  {nonce}")
    if bot:
        print(f"담당 봇: {bot['name']} ({bot['id']})")
    print(f"프로젝트: {project_id + ' · ' + str(proj.get('root')) if proj else '없음 (공용 허브)'}")

    if a.deliver == "hub":
        if not paths:
            print("허브 전달에는 담당 봇이 필요하다(bots.json 확인)")
            return 2
        paths["inbox"].parent.mkdir(parents=True, exist_ok=True)
        paths["result"].parent.mkdir(parents=True, exist_ok=True)
        paths["inbox"].write_text(spec, encoding="utf-8")
        paths["meta"].write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"과제함: {paths['inbox']}")
        print(f"{bot['name']} 에게 보낼 한 줄:")
        print(f"  과제함 {paths['inbox']} 를 읽고 그대로 수행해. 결과는 {paths['result']} 에 "
              "저장하고 대화창에도 남겨.")
        print(f"회수: make_bot_spec.py --collect --nonce {nonce}")
    elif a.deliver == "webhook":
        url = os.environ.get(WEBHOOK_URL_ENV, "<" + WEBHOOK_URL_ENV + ">")
        print("웹훅 명령(표시용, 키는 환경변수로):")
        print("  " + " ".join(webhook_argv(url)))
        if a.send:
            ok, note = send_webhook({"nonce": nonce, "spec": spec})
            print(("전송됨: " if ok else "전송 안 됨: ") + note)
            if not ok:
                return 3
    elif a.deliver == "github":
        print("GitHub 경로: 전용 레포 이슈로 남기고 루틴이 그 알림으로 시작하게 한다.")
        print("  gh issue create --repo <owner>/<repo> --title \"" + nonce +
              "\" --body-file " + str(spec_path))
    else:
        print("전달: 과제서를 봇 대화창에 붙여넣는다(기본 경로).")
        if a.mode == "console":
            print(f"회수: 결과를 파일로 저장한 뒤 --verify <파일> --nonce {nonce} --mode console")
    return 0


if __name__ == "__main__":
    sys.exit(main())
