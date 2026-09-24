# ledger.py — /vibe v2.1 학습 원장
#
# 발주 §9  : routing_ledger.jsonl 1개. 워커 1개 = 1줄. 집계 키 = (class, lane, effort).
# 발주 §10 : 다운로드 폴더의 decisions_*.json 을 자동 탐지해 items/accepted 를 merge 하고 소비한다.
# 발주 §14 : 데몬·상시 폴링 금지. /vibe 실행 시점에만 동작한다.
# 발주 S1  : append 전 시크릿 스캔. 검출되면 중단하고 보고한다.
# 발주 S2  : 다운로드 입력은 신뢰 경계 밖. 화이트리스트 정규식 · basename · 1MB · 엄격 스키마.
#
# ── 2026-09-04 독립 보안 감사 반영 ──────────────────────────────
# HIGH-3 시크릿 스캔이 정상 JSON 자격증명(`"password":"..."`)과 주요 토큰 prefix 를 놓쳤다
#        → generic 정규식 수정 + prefix 보강 + 민감 키를 재귀 스키마로 거부.
# HIGH-4 새 줄만 검사하고 최종 파일·staged blob 은 검사하지 않아 경합 시크릿이 커밋됐다
#        → 시작 시 dirty/staged 면 중단, 커밋 직전 전체 파일 재스캔 + staged blob hash 대조.
# HIGH-5 lock 없이 read-modify-truncate-write 해서 병렬 레코드와 손상 증거를 잃었다
#        → 프로세스 lock + 임시파일 fsync + os.replace. broken>0 이면 rewrite 거부.
# 테스트 주입: LEDGER/DOWNLOADS/git 러너를 교체할 수 있게 해 selftest 가 실제 상태를
#        건드리지 않게 한다 (HIGH-7 대응).
import datetime
import hashlib
import json
import math
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
import uuid

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

HUB = r"E:\Coding Infra\AI Infra\Communication"
LEDGER = os.path.join(HUB, "routing_ledger.jsonl")
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")

LOCK_TIMEOUT_S = 30
LOCK_STALE_S = 300

# ── S2 · 신뢰 경계 밖 입력 규칙 ─────────────────────────────────
# fullmatch 를 쓴다 — Python 의 $ 는 끝 개행 앞에도 일치한다 (감사 LOW).
DECISION_RE = re.compile(r"decisions_(run_[A-Za-z0-9]{1,40})\.json")
RUN_RE = re.compile(r"run_[A-Za-z0-9]{1,40}")
MAX_DECISION_BYTES = 1 * 1024 * 1024
DECISION_TOP_KEYS = {"run", "by_lane", "nonce"}
DECISION_LANE_KEYS = {"items", "accepted"}
MAX_DECISION_FILES = 50

# ── S1 · 시크릿 패턴 ────────────────────────────────────────────
# HIGH-3: 기존 generic 은 키워드 직후 ':'/'=' 와 여는 따옴표를 요구해
#         정상 JSON `"password":"..."`(키 뒤에 닫는 따옴표)를 놓쳤다.
SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "openai-style key"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "github token"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "github fine-grained pat"),
    (re.compile(r"A(?:KIA|SIA)[0-9A-Z]{16}"), "aws access key"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"), "slack token"),
    (re.compile(r"xapp-[0-9]-[A-Za-z0-9\-]{10,}"), "slack app token"),
    (re.compile(r"glpat-[A-Za-z0-9_\-]{16,}"), "gitlab pat"),
    (re.compile(r"hf_[A-Za-z0-9]{30,}"), "huggingface token"),
    (re.compile(r"pypi-AgEIcHlwaS5vcmc[A-Za-z0-9_\-]{10,}"), "pypi token"),
    (re.compile(r"(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{20,}"), "stripe key"),
    (re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\."), "jwt"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{35}"), "google api key"),
    (re.compile(r"sbp_[a-f0-9]{40}"), "supabase token"),
    (re.compile(r"npm_[A-Za-z0-9]{36}"), "npm token"),
    # 재검증 HIGH-1: 아래 형식들이 전부 스캐너를 통과해 HEAD 에 커밋됐다(격리 재현).
    (re.compile(r"GOCSPX-[A-Za-z0-9_\-]{20,}"), "google oauth client secret"),
    (re.compile(r"dckr_pat_[A-Za-z0-9_\-]{20,}"), "docker pat"),
    (re.compile(r"dapi[0-9a-f]{28,}"), "databricks token"),
    (re.compile(r"shp(?:at|ca|pa|ss)_[0-9a-fA-F]{28,}"), "shopify token"),
    (re.compile(r"SG\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}"), "sendgrid key"),
    (re.compile(r"AC[0-9a-fA-F]{32}"), "twilio sid"),
    (re.compile(r"figd_[A-Za-z0-9_\-]{30,}"), "figma token"),
    (re.compile(r"lin_api_[A-Za-z0-9]{30,}"), "linear key"),
    (re.compile(r"ntn_[A-Za-z0-9]{30,}"), "notion token"),
    (re.compile(r"vercel_[A-Za-z0-9]{20,}"), "vercel token"),
    # Attempt each maximal ASCII scheme run once, not every suffix of a long
    # word. Leading nonletters belong to the scan, not the reported credential.
    (re.compile(r"(?<![A-Za-z0-9+.\-])[0-9+.\-]*"
                r"(?P<credential>[A-Za-z][A-Za-z0-9+.\-]*://[^\s:/@]+:[^\s:/@]+@)"),
     "connection uri with password"),
    # JSON·ini 양쪽을 덮는다. 레코드 안에 JSON 문자열이 들어가면 따옴표가 \" 로
    # 이스케이프되므로 구분자 자리에 백슬래시를 허용해야 한다 (검증에서 실제로 새어나갔다).
    (re.compile(r"(?i)[\"'\\]{0,2}\b(?:api[_-]?key|secret|password|passwd|passphrase|"
                r"token|authorization|private[_-]?key|client[_-]?secret)\b[\"'\\]{0,2}"
                r"\s*[:=]\s*[\"'\\]{0,2}[^\s\"',}\]\\]{8,}"), "inline credential"),
]

# 민감 키는 값과 함께 거부한다 (정규식이 값 형태를 못 알아봐도 막힌다).
#
# 재검증 HIGH-A (2026-09-04): 단어 경계(\b) 기반이라 compound key 를 놓쳤다 —
# refresh_token · db_password · accessToken · id_token 이 전부 통과했다.
# → 키를 camelCase / _ / - / . 로 토큰화해서 판정한다.
SENSITIVE_TOKENS = {
    "password", "passwd", "passphrase", "secret", "secrets", "token", "tokens",
    "credential", "credentials", "authorization", "bearer", "cookie", "session",
    "apikey", "privatekey", "accesskey", "clientsecret", "refreshtoken",
}
# 두 토큰이 붙어야 민감한 것들 (bare "key" 는 오탐이 많아 단독으로 쓰지 않는다)
SENSITIVE_PAIRS = {("api", "key"), ("private", "key"), ("access", "key"),
                   ("secret", "key"), ("client", "secret"), ("auth", "token"),
                   ("id", "token"), ("refresh", "token"), ("access", "token")}


def _tokens(key):
    """키를 camelCase·구분자로 분해해 소문자 토큰 목록으로."""
    out = []
    for part in re.split(r"[_\-.\s/]+", str(key)):
        out += re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z]+|\d+", part)
    return [t.lower() for t in out if t]


TOKENISH_RUN = 20          # 구분자 없는 영숫자 연속이 이 길이를 넘으면 토큰 의심
HEXISH_RUN = 28            # 순수 hex 연속


def _looks_high_entropy(s, min_len=20):
    """자유 문자열이 '무작위 토큰처럼' 보이면 형식을 몰라도 거부한다.

    감사 MED (재현): 처음엔 Shannon 엔트로피를 썼는데 정상 식별자를 오탐했다.
    `security-bizlogic-2nd`(**우리 자신의 공정 ID**)와 `log-history-triage-2026`,
    32자 hex UUID 가 전부 걸려 보안 인가 게이트가 원장에 기록될 수 없었다.

    → 엔트로피가 아니라 **구조**로 본다. 사람이 쓰는 식별자는 `-_.` 로 끊긴
      짧은 단어들이다. 자격증명은 구분자 없는 긴 영숫자 덩어리다.
      GOCSPX-<28자>, dckr_pat_<27자>, dapi<32hex> 는 마지막 조각이 길다.
    """
    if not isinstance(s, str) or len(s) < min_len:
        return False
    for seg in re.split(r"[-_.]+", s):
        if not seg:
            continue
        if len(seg) >= HEXISH_RUN and re.fullmatch(r"[0-9a-fA-F]+", seg):
            return True                      # 긴 hex 덩어리
        if len(seg) >= TOKENISH_RUN and seg.isalnum() \
                and any(c.isdigit() for c in seg) and any(c.isalpha() for c in seg):
            return True                      # 긴 영숫자 혼합 덩어리
    return False


def _is_sensitive_key(key):
    toks = _tokens(key)
    joined = "".join(toks)
    if joined in SENSITIVE_TOKENS:
        return True
    if any(t in SENSITIVE_TOKENS for t in toks):
        return True
    return any((a, b) in SENSITIVE_PAIRS for a, b in zip(toks, toks[1:]))

RECORD_KEYS = {"run", "ts", "task", "class", "lane", "effort", "falsifiable",
               "explore", "status", "sec", "retries", "quota_delta",
               "items", "accepted", "guard_violations"}
REQUIRED_KEYS = {"run", "ts", "task", "class", "lane", "effort", "status"}
VALID_STATUS = {"done", "failed", "timeout", "cancelled", "unknown"}
# D-28 #4 (Q-260913-08 Simon 승인 2026-09-16): A-verify(대조·판정) 추가. 원장 class 값은 되돌리기 어렵다 —
#   되돌릴 때는 이 목록에서 빼지 말고 CLASS_LANES 에서만 뺀다(기존 원장 행이 손상 판정을 받는다).
VALID_CLASSES = {"A", "A-verify", "B", "C-realtime", "C-platform", "D", "N"}
TASK_RE = re.compile(r"[A-Za-z0-9_\-.]{1,64}")      # 비식별 ID 만
TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}[+\-]\d{4}")
LANE_RE = re.compile(r"[A-Za-z0-9._\-]{1,60}")
EFFORT_RE = re.compile(r"[a-z]{2,16}")


# ── 주입 지점 (테스트가 실제 상태를 안 건드리게 한다) ────────────
class Config:
    """selftest 가 임시 경로·mock git 으로 갈아끼우는 지점 (감사 HIGH-7)."""

    def __init__(self, ledger=None, downloads=None, git_runner=None):
        self.ledger = ledger or LEDGER
        self.downloads = downloads or DOWNLOADS
        self.git_runner = git_runner      # (args, cwd, env, stdin) -> (rc, out, err)


_CFG = Config()


def configure(ledger=None, downloads=None, git_runner=None):
    """반환된 이전 설정을 나중에 restore() 로 되돌린다."""
    global _CFG
    prev = _CFG
    _CFG = Config(ledger or prev.ledger, downloads or prev.downloads,
                  git_runner if git_runner is not None else prev.git_runner)
    return prev


def restore(prev):
    global _CFG
    _CFG = prev


def _ledger_path():
    return _CFG.ledger


def _downloads_dir():
    return _CFG.downloads


# ── 시크릿 검사 ─────────────────────────────────────────────────
_BASE64URL_RUN = re.compile(r"[A-Za-z0-9_\-]+")


def _first_jwt(text):
    """Preserve the JWT pattern's first offset without retrying every eyJ.

    A maximal run's first eyJ has the longest possible header suffix. If that
    suffix is too short, a later eyJ in the same run cannot match either.
    Keep only the previous run; adjacent dots and payload length determine the
    result. No signature, decoding, truncation or token values are returned.
    """
    previous = None
    for run in _BASE64URL_RUN.finditer(text):
        if previous is not None:
            offset, end = previous
            if (run.start() == end + 1 and text[end] == "."
                    and run.end() - run.start() >= 10
                    and text[run.end():run.end() + 1] == "."):
                return offset
        offset = text.find("eyJ", run.start(), run.end())
        previous = (offset, run.end()) if offset >= 0 and run.end() - offset >= 13 else None
    return None


def scan_secrets(text):
    """검출된 (패턴이름, 위치) 목록. 값 자체는 반환하지 않는다."""
    hits = []
    for rx, name in SECRET_PATTERNS:
        # Keep the legacy regex as the format contract, but do not execute its
        # quadratic search on repeated eyJ prefixes with a missing delimiter.
        if name == "jwt":
            offset = _first_jwt(text)
            if offset is not None:
                hits.append((name, offset))
            continue
        m = rx.search(text)
        if m:
            hits.append((name, m.start("credential") if "credential" in rx.groupindex else m.start()))
    return hits


def scan_sensitive_keys(obj, path="", depth=0):
    """민감 '키' 자체를 거부한다. 값 안에 JSON 이 들어간 경우도 파고든다.

    재검증 HIGH-A: task 를 '{"refresh_token":"..."}' 문자열로 두면 dict 가 아니라
    문자열이라 키 검사를 통과했다. 문자열이 JSON 처럼 보이면 파싱해서 다시 본다.
    """
    bad = []
    if depth > 8:
        return bad
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}" if path else str(k)
            if isinstance(k, str) and _is_sensitive_key(k):
                bad.append(here)
            bad += scan_sensitive_keys(v, here, depth + 1)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            bad += scan_sensitive_keys(v, f"{path}[{i}]", depth + 1)
    elif isinstance(obj, str):
        s = obj.strip()
        if s[:1] in "{[" and len(s) <= 64 * 1024:
            try:
                bad += scan_sensitive_keys(json.loads(s), path + "~json", depth + 1)
            except Exception:
                pass
    return bad


def _canonical_lanes():
    import routing
    return set(routing.LANES)


def _canonical_efforts(lane):
    # 2026-09-06: 정책 두 단만 받으면 allow_off_ladder 로 올려 부른 라운드가
    # 원장에 못 들어간다 — 기록이 빠지면 스왑 분석이 그 관측을 영영 못 본다.
    # routing 이 주는 '정책 ∪ Orca 실측' 닫힌 집합으로 넓힌다.
    import routing
    return routing.ledger_efforts(lane)


def _validate_record(r):
    """원장 레코드 스키마. append·read·collect 가 모두 이걸 쓴다 (감사 MED)."""
    if not isinstance(r, dict):
        return f"레코드가 객체가 아니다 ({type(r).__name__})"
    unknown = set(r) - RECORD_KEYS
    if unknown:
        return f"정의되지 않은 필드 {len(unknown)}개"
    missing = REQUIRED_KEYS - set(r)
    if missing:
        return f"필수 필드 누락 {sorted(missing)}"
    if not isinstance(r["run"], str) or not RUN_RE.fullmatch(r["run"]):
        return "run 형식 불일치"
    # 재검증 HIGH-A: task/ts/class/lane/effort 의 타입·길이·enum 이 없어서
    # task 에 JSON 자격증명을 통째로 넣을 수 있었다.
    if not isinstance(r["task"], str) or not TASK_RE.fullmatch(r["task"]):
        return "task 는 영숫자·_·-·. 1~64자(비식별 ID)만 허용"
    if _looks_high_entropy(r["task"]):
        return "task 가 무작위 토큰처럼 보인다 — 비식별 ID 만 허용"
    if not isinstance(r["ts"], str) or not TS_RE.fullmatch(r["ts"]):
        return "ts 형식 불일치(ISO8601 ±hhmm)"
    # 타입을 먼저 본다 — set 멤버십은 unhashable 값에서 TypeError 를 내고
    # 그건 통제된 거부가 아니라 크래시다 (감사 MED).
    if not isinstance(r["class"], str) or r["class"] not in VALID_CLASSES:
        return f"class 는 {sorted(VALID_CLASSES)} 중 하나여야 한다"
    # 재검증 HIGH-1: 정규식만 보면 아무 문자열이나 통과한다.
    # routing 정본의 canonical lane/effort 쌍으로 검증한다.
    if not isinstance(r["lane"], str) or r["lane"] not in _canonical_lanes():
        return "lane 이 routing 정본에 없다"
    if not isinstance(r["effort"], str) or r["effort"] not in _canonical_efforts(r["lane"]):
        return "effort 가 이 lane 의 허용값이 아니다"
    if not isinstance(r["status"], str) or r["status"] not in VALID_STATUS:
        return f"status 는 {sorted(VALID_STATUS)} 중 하나여야 한다"
    for k in ("sec", "retries", "items", "accepted"):
        if k in r:
            v = r[k]
            if type(v) is not int or v < 0:      # bool 은 int 하위형이라 type() 로 막는다
                return f"{k} 는 0 이상 정수여야 한다"
    if r.get("accepted", 0) > r.get("items", 0):
        return "accepted > items"
    for k in ("falsifiable", "explore"):
        if k in r and type(r[k]) is not bool:
            return f"{k} 는 bool 이어야 한다"
    qd = r.get("quota_delta", {})
    if not isinstance(qd, dict):
        return "quota_delta 는 객체여야 한다"
    for k, v in qd.items():
        if k not in ("claude", "codex", "gemini", "grok"):
            return "quota_delta 키는 4벤더만 허용"
        if type(v) is not int or not (-100 <= v <= 100):
            return "quota_delta 값은 -100~100 정수"
    gv = r.get("guard_violations", [])
    if not isinstance(gv, list) or any(
            not isinstance(x, str) or not re.fullmatch(r"[A-Z0-9_]{2,32}", x) for x in gv):
        return "guard_violations 는 대문자 코드 배열이어야 한다"
    return ""


# ── 프로세스 lock (HIGH-5) ──────────────────────────────────────
def _pid_alive(pid):
    """LOW-104: lock 주인이 아직 살아 있는지. 못 알아보면 '살아있다'로 본다(보수적)."""
    if not pid:
        return False
    try:
        if os.name == "nt":
            p = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                               capture_output=True, text=True, timeout=20)
            return str(pid) in (p.stdout or "")
        os.kill(pid, 0)
        return True
    except Exception:
        return True


class _Lock:
    """O_EXCL 기반 파일 lock. Windows 에서도 동작한다.

    한계: lock 을 무시하고 같은 파일을 여는 writer 는 막지 못한다.
    그래서 커밋 직전에 blob hash 를 다시 대조한다(HIGH-4).
    """

    def __init__(self, target, timeout=LOCK_TIMEOUT_S):
        self.path = target + ".lock"
        self.timeout = timeout
        self.fd = None

    def __enter__(self):
        deadline = time.time() + self.timeout
        while True:
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, str(os.getpid()).encode())
                return self
            except FileExistsError:
                # LOW-104: 나이만 보고 지우면 오래 걸리는 '살아있는' 작업의 lock 을 뺏는다.
                # PID 가 살아 있으면 나이와 무관하게 기다린다.
                try:
                    age = time.time() - os.path.getmtime(self.path)
                    holder = 0
                    try:
                        holder = int(open(self.path, encoding="utf-8").read().strip() or 0)
                    except Exception:
                        holder = 0
                    if age > LOCK_STALE_S and not _pid_alive(holder):
                        os.remove(self.path)        # 죽은 프로세스가 남긴 lock 만 회수
                        continue
                except OSError:
                    pass
                if time.time() > deadline:
                    raise TimeoutError(f"원장 lock 획득 실패 ({self.timeout}s)")
                time.sleep(0.15)

    def __exit__(self, *a):
        try:
            if self.fd is not None:
                os.close(self.fd)
            os.remove(self.path)
        except OSError:
            pass
        return False


def _atomic_write_bytes(path, data):
    """HIGH-5: 임시파일 → fsync → os.replace. 중간 중단이 원장을 0바이트로 만들지 않는다.

    바이트를 그대로 쓴다 — 검증한 바이트와 기록한 바이트와 커밋한 바이트가
    모두 같은 객체여야 post-scan 경합이 사라진다 (HIGH-B).
    """
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".ledger-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


# ── git ─────────────────────────────────────────────────────────
def _git(args, cwd=None, env=None, stdin=None):
    """S3 — 인자 배열. shell=True 금지."""
    if _CFG.git_runner is not None:
        # LOW-99: 이전 판은 env/stdin 을 버려서, mock 을 쓰는 테스트가
        # exact-byte(hash-object --stdin)와 전용 index(GIT_INDEX_FILE) 경로를
        # 실제로 검증하지 못했다. 전부 넘긴다.
        return _CFG.git_runner(args, cwd, env, stdin)
    if cwd is None:
        cwd = os.path.dirname(_ledger_path()) or "."
    e = None
    if env:
        e = dict(os.environ)
        e.update(env)
    try:
        p = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                           input=stdin, env=e, timeout=120)
        dec = (p.stdout or b"").decode("utf-8", "replace").strip()
        err = (p.stderr or b"").decode("utf-8", "replace").strip()
        return p.returncode, dec, err
    except Exception as ex:
        return 1, "", type(ex).__name__


def _sha1_blob(path):
    """워크트리 파일의 git blob 해시.

    감사 MED (재현 확인): 직접 SHA-1 을 계산하면 core.autocrlf=true 에서
    체크아웃 직후의 clean 파일을 dirty 로 오판한다. git 은 blob 에 LF 를 저장하고
    워크트리에는 CRLF 를 쓰기 때문이다. 이 환경은 전역·허브 모두 autocrlf=true 라
    체크아웃 한 번이면 _ledger_dirty() 가 항상 True 가 되어 원장 커밋이 영구 차단된다.
    → git 에게 물어본다. hash-object 는 체크인 필터를 그대로 적용한다.
    아래 raw 계산은 git 을 못 부를 때의 폴백으로만 남긴다.
    """
    rc, out, _ = _git(["hash-object", "--", path])
    if rc == 0 and re.fullmatch(r"[0-9a-f]{40}", out.strip()):
        return out.strip()
    data = open(path, "rb").read()
    h = hashlib.sha1()
    h.update(b"blob " + str(len(data)).encode() + b"\0")
    h.update(data)
    return h.hexdigest()


def _ledger_dirty():
    """시작 시 워크트리 원장이 HEAD 와 다르면(=누가 커밋 안 한 변경을 갖고 있으면) 보류한다.

    index 가 아니라 **워크트리 ↔ HEAD** 를 비교한다.
    _commit_cas 는 공유 index 를 쓰지 않고 HEAD 만 옮기므로, index 기준으로 보면
    우리가 방금 만든 커밋조차 "누가 staged 했다"로 오판된다 (실제로 회귀가 났다).
    커밋되는 것은 우리가 검증한 바이트뿐이라 index 상태는 안전성과 무관하고,
    여기서 막고 싶은 것은 '남의 미커밋 변경을 우리가 덮어쓰는 것' 하나다.
    """
    p = _ledger_path()
    name = os.path.basename(p)
    rc, head_blob, _ = _git(["rev-parse", f"HEAD:{name}"])
    if rc != 0:
        return False, ""                      # 아직 추적되지 않는 새 파일
    if not os.path.exists(p):
        return True, "원장 파일이 사라졌다"
    if _sha1_blob(p) != head_blob.strip():
        return True, "워크트리 원장이 HEAD 와 다르다(미커밋 변경)"
    return False, ""


def verify_payload(data_bytes):
    """커밋될 '정확한 바이트'를 레코드 단위로 다시 검증한다.

    재검증 HIGH-A: 최종 재검사가 scan_secrets(whole) 만 불러서
    JSON 을 다시 파싱한 민감-키 검사를 하지 않았다.
    """
    try:
        text = data_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return "UTF-8 디코드 실패 — 손상된 원장"
    for i, ln in enumerate(text.splitlines(), 1):
        if not ln.strip():
            continue
        try:
            r = json.loads(ln, object_pairs_hook=_reject_dupe_keys,
                           parse_constant=_reject_constant)
        except Exception:
            return f"{i}행 JSON 파싱 실패(중복 키·NaN 포함)"
        why = _validate_record(r)
        if why:
            return f"{i}행 스키마 위반: {why}"
        bad = scan_sensitive_keys(r)
        if bad:
            return f"{i}행 민감 키 {len(bad)}개"
    hits = scan_secrets(text)
    if hits:
        return f"시크릿 패턴({', '.join(n for n, _ in hits)})"
    return ""


def _journal(kind, data):
    """부분 성공·복구 필요 상태를 durable 하게 남긴다 (감사 HIGH-4).

    ref 는 이미 움직였는데 index 갱신이 실패한 상태는 오류 반환만으로 복구되지 않는다.
    다음 실행이 무엇을 손봐야 하는지 알 수 있게 기록해 둔다.
    """
    try:
        p = os.path.join(_pending_dir(), "journal.jsonl")
        rec = {"ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
               "kind": kind, **{k: v for k, v in (data or {}).items()}}
        with open(p, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _journal_saw_index(blob):
    """이 index blob 을 우리가 이전 실패에서 남긴 적이 있나.

    journal 은 우리 자신이 쓴 기록이므로, 여기 있는 blob 은 '남의 staged 작업'이
    아니라 우리 실패의 잔해다. 이걸 구분해야 재시도가 교착되지 않는다.
    """
    p = os.path.join(_pending_dir(), "journal.jsonl")
    if not blob or not os.path.exists(p):
        return False
    try:
        with open(p, encoding="utf-8") as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                if r.get("index_blob") == blob or r.get("head_blob") == blob:
                    return True
    except OSError:
        pass
    return False


def _txn_baseline():
    """원장을 **읽기 전에** 기준 HEAD 와 ledger blob 을 캡처한다.

    재검증 HIGH-2: 이전 판은 payload 를 만든 '뒤'에 HEAD 를 읽어서,
    그 사이 다른 워커가 커밋한 레코드를 stale payload 로 덮어썼다.
    CAS 는 늦게 읽은 HEAD 이후의 이동만 막으므로 그 전 커밋은 보호되지 않았다.
    격리 재현에서 B 의 레코드가 실패 신호 없이 사라졌다.
    """
    name = os.path.basename(_ledger_path())
    rc, head, _ = _git(["rev-parse", "HEAD"])
    if rc != 0:
        return None
    rc, blob, _ = _git(["rev-parse", f"HEAD:{name}"])
    return {"head": head.strip(), "blob": blob.strip() if rc == 0 else None}


def _commit_cas(data_bytes, msg, baseline=None):
    """검증한 '그 바이트'를 커밋한다. 워크트리를 다시 읽지 않는다.

    재검증 HIGH-B (2026-09-04): 이전 판은 스캔 후 파일을 다시 읽어 기대값을 만들고
    `git commit -- <path>` 로 커밋했다. 스캔↔hash 사이의 변경은 새 '기대값'이 되고,
    hash 확인 뒤 변경도 pathspec commit 이 워크트리에서 다시 집어갔다.
    격리 재현에서 검증 후 추가된 sk-... 가 HEAD 에 들어갔다.

    → 검증한 바이트를 object DB 에 직접 넣고(hash-object -w --stdin),
      공유 index 를 건드리지 않는 전용 GIT_INDEX_FILE 에서 트리를 만들고,
      update-ref <ref> <new> <old> 로 CAS 커밋한다.
      마지막에 HEAD:<path> 가 그 blob 인지 확인한다.
    """
    name = os.path.basename(_ledger_path())

    rc, blob, err = _git(["hash-object", "-w", "--stdin"], stdin=data_bytes)
    if rc != 0 or not re.fullmatch(r"[0-9a-f]{40}", blob):
        return "failed", f"blob 생성 실패(코드 {rc})"

    # HIGH-2: 기준은 '원장을 읽기 전'에 잡은 것이어야 한다. 여기서 새로 읽지 않는다.
    if baseline is None:
        return "failed", "트랜잭션 기준(baseline) 없이 커밋할 수 없다"
    head = baseline["head"]
    rc, cur_head, _ = _git(["rev-parse", "HEAD"])
    if rc != 0 or cur_head.strip() != head:
        return "failed", "기준 HEAD 가 이동했다 — 재읽기 후 재시도 필요"
    rc, cur_blob, _ = _git(["rev-parse", f"HEAD:{name}"])
    cur_blob = cur_blob.strip() if rc == 0 else None
    if cur_blob != baseline["blob"]:
        return "failed", "기준 원장 blob 이 바뀌었다 — 재읽기 후 재시도 필요"
    rc, ref, _ = _git(["symbolic-ref", "HEAD"])
    if rc != 0:
        return "failed", "브랜치 조회 실패"

    idx = _ledger_path() + ".casindex"
    env = {"GIT_INDEX_FILE": idx}
    try:
        rc, _, _ = _git(["read-tree", head], env=env)
        if rc != 0:
            return "failed", "read-tree 실패"
        rc, _, _ = _git(["update-index", "--add", "--cacheinfo",
                         f"100644,{blob},{name}"], env=env)
        if rc != 0:
            return "failed", "update-index 실패"
        rc, tree, _ = _git(["write-tree"], env=env)
        if rc != 0:
            return "failed", "write-tree 실패"
    finally:
        try:
            os.remove(idx)          # 공유 index 를 오염시키지 않는다
        except OSError:
            pass

    rc, commit, _ = _git(["commit-tree", tree, "-p", head, "-m", msg])
    if rc != 0 or not re.fullmatch(r"[0-9a-f]{40}", commit):
        return "failed", "commit-tree 실패"

    # CAS: old 를 명시해 그 사이 HEAD 가 움직였으면 실패한다
    rc, _, _ = _git(["update-ref", ref, commit, head])
    if rc != 0:
        return "failed", "update-ref CAS 실패 — 그 사이 HEAD 가 움직였다"

    rc, got, _ = _git(["rev-parse", f"HEAD:{name}"])
    if rc != 0 or got.strip() != blob:
        return "failed", "커밋 후 HEAD blob 이 검증본과 다르다"

    # 재검증 HIGH-3: 이전 판은 공유 index 를 **조건 없이** 우리 blob 으로 덮고
    # 반환 코드를 버렸다. 다른 AI 가 staged 해 둔 ledger 가 사라졌고,
    # index.lock 으로 실패시켜도 "commit 완료" 를 반환해 이후 unrelated commit 이
    # 오래된 index blob 을 함께 커밋하며 원장을 0바이트로 되돌렸다.
    #
    # → index 가 '우리가 기준으로 삼은 blob' 그대로일 때만 compare-and-set 한다.
    #   남이 다른 것을 staged 했으면 건드리지 않고, 그 사실을 반환에 실어 보낸다.
    #   갱신 실패도 성공으로 감추지 않는다.
    #
    # 재검증 HIGH-4: 이 지점의 실패를 True 로 감추면 호출자가 decision 원본과
    # manifest 를 소비해 버린다. ref 는 이미 움직였으므로 단순 오류 반환으로도 부족하다.
    # → 'partial' 이라는 별도 상태를 만들고, 호출자는 'ok' 일 때만 소비한다.
    #   부분 성공은 journal 에 남겨 다음 실행이 복구할 수 있게 한다.
    rc, idx, _ = _git(["rev-parse", f":{name}"])
    idx = idx.strip() if rc == 0 else None
    if idx == baseline["blob"]:
        rc2, _, _ = _git(["update-index", "--add", "--cacheinfo", f"100644,{blob},{name}"])
        rc3, idx2, _ = _git(["rev-parse", f":{name}"])
        if rc2 != 0 or rc3 != 0 or idx2.strip() != blob:
            _journal("index_update_failed", {"head_blob": blob, "index_blob": idx2.strip()})
            return "partial", ("commit 은 됐으나 공유 index 갱신이 실패했다 — "
                               "다음 커밋이 옛 index 를 집어가 원장을 되돌릴 수 있다. "
                               "입력을 소비하지 않았다. 수동 확인 필요")
    elif idx is not None and idx != blob:
        # 우리 자신의 이전 실패가 남긴 stale index 인지 구분한다.
        # 이걸 구분하지 않으면 1차 실패 뒤 2차가 자기 잔해를 '남의 작업'으로 보고
        # 영원히 partial 을 반환해 교착에 빠진다 (재시도 검증에서 실제로 발생).
        if _journal_saw_index(idx):
            rc2, _, _ = _git(["update-index", "--add", "--cacheinfo",
                              f"100644,{blob},{name}"])
            rc3, idx2, _ = _git(["rev-parse", f":{name}"])
            if rc2 == 0 and rc3 == 0 and idx2.strip() == blob:
                _journal("index_recovered", {"head_blob": blob, "was": idx})
                return "ok", "commit 완료(CAS) · 이전 실패가 남긴 index 를 복구했다"
            _journal("index_update_failed", {"head_blob": blob, "index_blob": idx})
            return "partial", ("commit 은 됐으나 index 복구에 실패했다. "
                               "입력을 소비하지 않았다. 수동 확인 필요")
        _journal("foreign_staged_index", {"head_blob": blob, "index_blob": idx})
        return "partial", ("commit 은 됐으나 공유 index 에 타 에이전트의 staged ledger 가 있어 "
                           "건드리지 않았다. 입력을 소비하지 않았다. 수동 통합 필요")
    return "ok", "commit 완료(CAS)"


# ── 읽기 ────────────────────────────────────────────────────────
def read_ledger(validate=True):
    """원장을 읽어 (레코드, 깨진 줄 수). 깨진 줄은 세기만 하고 버리지 않는다.

    감사 MED: docstring 은 append·read·collect 가 공통 validator 를 쓴다고 했지만
    read 경로에서는 dict 여부만 봤다. class=[] 같은 값이 그대로 흘러 aggregate 에서
    unhashable TypeError 를 냈다. 이제 read 에서도 검증하고, 실패는 손상으로 센다.
    invalid UTF-8 도 예외로 죽지 않고 손상으로 처리한다.
    """
    recs, broken = [], 0
    p = _ledger_path()
    if not os.path.exists(p):
        return recs, broken
    with open(p, "rb") as f:
        raw = f.read()
    for chunk in raw.split(b"\n"):
        if not chunk.strip():
            continue
        try:
            ln = chunk.decode("utf-8")
        except UnicodeDecodeError:
            broken += 1
            continue
        try:
            # MED-54: 표준 json 은 중복 키를 조용히 마지막 값으로 채택한다.
            # 원장 한 줄에 run 을 두 번 넣어 검증을 우회할 수 있었다.
            o = json.loads(ln, object_pairs_hook=_reject_dupe_keys,
                           parse_constant=_reject_constant)
        except Exception:
            broken += 1
            continue
        if not isinstance(o, dict):
            broken += 1                 # 배열 한 줄이 collect 를 죽이던 문제
            continue
        if validate and _validate_record(o):
            broken += 1
            continue
        recs.append(o)
    return recs, broken


# ── provenance manifest (감사 MED) ──────────────────────────────
# Downloads 는 신뢰 경계 밖이라 파일만으로는 "우리가 만든 시트의 결과"임을 증명할 수 없었다.
# 알려진 run 과 lane 만 알면 9999/9999 를 넣어 회수시키고, 지운 뒤 같은 이름으로
# 다시 넣어 값을 덮을 수 있었다(감사관이 격리에서 재현).
# → 시트를 만들 때 Downloads **밖**에 nonce 매니페스트를 남기고, 회수는 그것과
#   정확히 맞는 미소비 결과 하나만 처리한 뒤 nonce 를 소비 기록한다.
MANIFEST_TTL_S = 14 * 24 * 3600


def _pending_dir():
    d = os.path.join(os.path.dirname(_ledger_path()) or ".", ".vibe-pending")
    os.makedirs(d, exist_ok=True)
    return d


def _restore_quarantine(max_age_days=14):
    """격리에 남은 입력을 원래 이름으로 Downloads 에 되돌린다 (MED-29).

    격리는 처리 중 객체를 고정하려는 것이지 보관소가 아니다. 부분 실패로 남으면
    UUID 이름이라 다음 Downloads 스캔에 걸리지 않아, "보존했다"고 해놓고
    영원히 재처리되지 않았다. 되돌려 놓으면 다음 스캔이 정상 경로로 다시 집는다.
    오래된 것은 정리해 숨은 폴더에 무한 누적되지 않게 한다 (MED-44b).
    """
    notes = []
    q = _quarantine_dir()
    if not os.path.isdir(q):
        return notes
    dl = _downloads_dir()
    now = time.time()
    for fn in sorted(os.listdir(q)):
        if not fn.endswith(".json"):
            continue
        fp = os.path.join(q, fn)
        meta = fp + ".name"
        try:
            if now - os.path.getmtime(fp) > max_age_days * 86400:
                os.remove(fp)
                for side in (meta, fp + ".rejected"):
                    if os.path.exists(side):
                        os.remove(side)
                notes.append(f"격리 정리: {max_age_days}일 경과분 제거")
                continue
            if not os.path.exists(meta):
                continue                      # 이름을 모르면 되돌릴 수 없다
                                              # (영구 거부분도 여기서 빠진다 — _reject_perm)
            orig = os.path.basename(open(meta, encoding="utf-8").read().strip())
            if not DECISION_RE.fullmatch(orig):
                continue
            dest = os.path.join(dl, orig)
            if os.path.exists(dest):
                continue                      # 새 결과가 이미 있으면 건드리지 않는다
            os.replace(fp, dest)
            os.remove(meta)
            notes.append(f"격리 복귀: {orig} (이전 실행의 미완 입력을 재시도한다)")
        except OSError:
            pass
    return notes


def _quarantine_dir():
    """격리 폴더는 **Downloads 와 같은 볼륨**이어야 한다.

    실사용에서 잡힘 (2026-09-04): 격리 폴더를 허브(E:)에 뒀더니 Downloads(C:)에서
    os.replace 가 교차 볼륨이라 실패했고, 회수가 통째로 건너뛰어졌다.
    atomic rename 으로 객체를 고정하는 게 목적이므로 copy+delete 폴백은 쓰지 않는다.
    Downloads 의 부모(사용자 홈)에 두면 같은 볼륨이면서 Downloads 밖이다.
    """
    d = os.path.join(os.path.dirname(_downloads_dir().rstrip("\\/")) or ".",
                     ".vibe-quarantine")
    os.makedirs(d, exist_ok=True)
    return d


def write_pending_manifest(run, items):
    """시트 생성 시 호출. 반환된 dict 의 nonce 를 시트 payload 에 싣는다."""
    lanes = {}
    for it in items:
        lanes[it["lane"]] = lanes.get(it["lane"], 0) + 1
    m = {"run": run, "nonce": uuid.uuid4().hex, "created": int(time.time()),
         "expires": int(time.time()) + MANIFEST_TTL_S,
         "expected": lanes, "item_ids": sorted(i["id"] for i in items),
         "consumed": False}
    with open(os.path.join(_pending_dir(), f"{run}.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
    return m


def _read_manifest(run):
    p = os.path.join(_pending_dir(), f"{run}.json")
    if not os.path.exists(p):
        return None, "pending manifest 가 없다(시트를 만든 적 없는 run)"
    try:
        with open(p, "r", encoding="utf-8") as f:
            m = json.load(f)
    except Exception:
        return None, "manifest 파싱 실패"
    if m.get("consumed"):
        return None, "이미 소비된 manifest(재생 시도)"
    if int(m.get("expires", 0)) < time.time():
        return None, "manifest 만료"
    # MED-39: 스키마를 확인하지 않으면 손상된 manifest 가 collector 를 예외로 죽인다.
    need = {"run", "nonce", "created", "expires", "expected", "item_ids", "consumed"}
    if not isinstance(m, dict) or need - set(m):
        return None, "manifest 스키마 불일치"
    if not isinstance(m.get("expected"), dict) or not m["expected"]:
        return None, "manifest expected 가 비었다"
    for k, v in m["expected"].items():
        if not isinstance(k, str) or type(v) is not int or v < 0:
            return None, "manifest expected 형식 불일치"
    if not isinstance(m.get("nonce"), str) or len(m["nonce"]) < 16:
        return None, "manifest nonce 형식 불일치"
    return m, ""


def _nonce_spent(nonce):
    """MED-34: consumed 플래그 쓰기가 실패하면(권한·크래시) 같은 nonce 를 재제출할 수 있었다.
    소비 기록을 append-only 파일에도 남기고, 병합 전에 여기부터 확인한다."""
    p = os.path.join(_pending_dir(), "spent-nonces.txt")
    try:
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return any(ln.strip() == nonce for ln in f)
    except OSError:
        pass
    return False


def _mark_nonce_spent(nonce):
    """반환 True 여야 소비를 확정한다 — 기록 실패를 삼키지 않는다."""
    p = os.path.join(_pending_dir(), "spent-nonces.txt")
    try:
        with open(p, "a", encoding="utf-8", newline="\n") as f:
            f.write(nonce + "\n")
            f.flush()
            os.fsync(f.fileno())
        return True
    except OSError:
        return False


def _consume_manifest(run):
    """반환 True 여야 소비를 확정한다. 실패를 삼키면 재생 방지가 조용히 사라진다."""
    p = os.path.join(_pending_dir(), f"{run}.json")
    try:
        with open(p, "r", encoding="utf-8") as f:
            m = json.load(f)
        m["consumed"] = True
        m["consumed_at"] = int(time.time())
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            json.dump(m, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception:
        return False


# ── 쓰기 ────────────────────────────────────────────────────────
def append_records(records, commit=True):
    """레코드를 원장에 append 하고 커밋한다. 반환 (written, note)."""
    if not records:
        return 0, "레코드 없음"

    lines = []
    for r in records:
        why = _validate_record(r)
        if why:
            return 0, f"스키마 거부: {why}"
        bad_keys = scan_sensitive_keys(r)
        if bad_keys:
            return 0, f"민감 키 {len(bad_keys)}개 검출 — append 중단 (발주 S1)"
        line = json.dumps(r, ensure_ascii=False, separators=(",", ":"))
        hits = scan_secrets(line)
        if hits:
            names = ", ".join(n for n, _ in hits)
            return 0, f"시크릿 패턴 검출({names}) — append 중단 (발주 S1)"
        lines.append(line)

    p = _ledger_path()
    with _Lock(p):
        if commit:
            dirty, why = _ledger_dirty()
            if dirty:
                return 0, f"자동 커밋 중단 — {why} (수동 확인 필요)"

        # HIGH-2: 기준을 '읽기 전'에 잡는다
        baseline = _txn_baseline() if commit else None
        existing = []
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                existing = [ln.rstrip("\n") for ln in f if ln.strip()]

        # 커밋될 '정확한 바이트'를 먼저 만들고, 그 바이트를 검증하고, 그 바이트를 쓴다.
        payload = ("\n".join(existing + lines) + "\n").encode("utf-8")
        why = verify_payload(payload)
        if why:
            return 0, f"최종 payload 검증 실패({why}) — 기록하지 않았다"

        if not commit:
            _atomic_write_bytes(p, payload)
            return len(lines), "append 만 (commit 생략)"

        # 감사 MED: 이전 판은 worktree 를 먼저 바꾸고 실패 시 되돌리지 않아,
        # 다음 실행이 _ledger_dirty() 에서 스스로 막혔다. preimage 를 잡아 둔다.
        preimage = open(p, "rb").read() if os.path.exists(p) else b""
        _atomic_write_bytes(p, payload)
        st, note = _commit_cas(payload, f"chore(vibe): routing ledger +{len(lines)}", baseline)
        if st == "failed":
            cur = open(p, "rb").read() if os.path.exists(p) else b""
            if cur == payload:                 # 내가 쓴 그대로면 되돌려도 안전하다
                _atomic_write_bytes(p, preimage)
                return 0, f"{note} — 워크트리를 원상복구했다. 재시도 가능"
            _journal("restore_skipped", {"reason": "worktree changed by someone else"})
            return 0, f"{note} — 그 사이 파일이 바뀌어 복구하지 않았다. 수동 확인 필요"
        if st == "partial":
            return len(lines), note
        return len(lines), note


# ── §10 · 결정 시트 결과 회수 ───────────────────────────────────
def _validate_decision(obj, expect_run):
    """S2 — 엄격 스키마. 파일명의 run 과 payload 의 run 이 같아야 한다 (감사 MED)."""
    if not isinstance(obj, dict):
        return None, "최상위가 객체가 아니다"
    extra = set(obj) - DECISION_TOP_KEYS
    if extra:
        return None, f"정의되지 않은 최상위 필드 {len(extra)}개"
    if not DECISION_TOP_KEYS <= set(obj):
        return None, f"필수 필드 누락 {sorted(DECISION_TOP_KEYS - set(obj))}"
    run = obj["run"]
    if not isinstance(run, str) or not RUN_RE.fullmatch(run):
        return None, "run 형식 불일치"
    if run != expect_run:
        return None, "파일명의 run 과 내용의 run 이 다르다"
    # provenance: 우리가 만든 시트의 결과임을 nonce 로 증명해야 한다 (감사 MED)
    man, why = _read_manifest(run)
    if man is None:
        return None, why
    if obj.get("nonce") != man["nonce"]:
        return None, "nonce 불일치(위조 또는 재생)"
    if _nonce_spent(man["nonce"]):
        return None, "이미 소비된 nonce(재생 시도)"
    # MED-39: manifest 의 모든 레인이 결과에 있어야 한다.
    # 일부 레인만 담긴 결과를 받으면 나머지가 영구 미회수로 남는다.
    if set(obj["by_lane"]) != set(man.get("expected") or {}):
        return None, "manifest 의 레인 집합과 결과가 다르다(부분 제출 거부)"

    by = obj["by_lane"]
    if not isinstance(by, dict) or not by:
        return None, "by_lane 이 비었거나 객체가 아니다"
    expected = man.get("expected") or {}
    clean = {}
    for lane, v in by.items():
        if not isinstance(lane, str) or not re.fullmatch(r"[A-Za-z0-9._\-]{1,60}", lane):
            return None, "레인 키 형식 불일치"
        if lane not in expected:
            return None, "manifest 에 없는 레인"
        if not isinstance(v, dict) or set(v) != DECISION_LANE_KEYS:
            return None, "by_lane 항목은 items·accepted 정확히 두 키여야 한다"
        items, acc = v["items"], v["accepted"]
        # bool 은 int 하위형이므로 type() 로 막는다. float·문자열도 거부.
        if type(items) is not int or type(acc) is not int:
            return None, "items/accepted 는 정수여야 한다"
        if items < 0 or acc < 0 or acc > items:
            return None, "items/accepted 범위 위반"
        if items != expected[lane]:
            return None, f"레인 항목 수가 manifest 와 다르다(기대 {expected[lane]})"
        clean[lane] = {"items": items, "accepted": acc}
    return {"run": run, "by_lane": clean}, ""


def _reject_constant(c):
    """NaN/Infinity 는 JSON 표준 밖이다 — 거부한다."""
    raise ValueError(f"비표준 상수 거부: {c}")


def _reject_dupe_keys(pairs):
    """중복 JSON 키를 거부한다 (표준 json 은 마지막 값을 조용히 채택한다)."""
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError("중복 키")
        seen[k] = v
    return seen


def _reject_perm(path, notes, msg):
    """영구 거부 — 격리에 남기되 **복귀 대상에서 뺀다.**

    실사용에서 잡힘 (2026-09-04): 거부된 입력이 격리에 그대로 남으면
    다음 실행의 _restore_quarantine() 이 Downloads 로 되돌려 놓고,
    스캔이 다시 집고, 또 거부하고, 또 되돌린다 — 14일 퍼지까지 매 라운드
    같은 오류 줄을 뱉어 진짜 실패를 덮는다. 되돌릴 근거(이름 사이드카)를
    지우면 복귀 대상에서 빠지고 퍼지가 정리한다. 사유는 남긴다.

    스키마·크기·재생처럼 **다시 시도해도 결과가 같은** 거부에만 쓴다.
    커밋 실패·원장 dirty 같은 일시적 실패에는 쓰지 않는다(재시도해야 한다).
    """
    notes.append(msg)
    try:
        meta = path + ".name"
        if os.path.exists(meta):
            os.remove(meta)
        with open(path + ".rejected", "w", encoding="utf-8", newline="\n") as f:
            f.write(msg + "\n")
    except OSError:
        pass


def collect_decisions(consume=True):
    """다운로드 폴더의 decisions_run_*.json 을 원장에 merge 한다.

    반환 (merged_runs, notes). 파일 내용은 명령·경로로 해석하지 않는다 (S2).
    """
    notes, merged = [], []
    dl = _downloads_dir()
    if not os.path.isdir(dl):
        return merged, ["다운로드 폴더 없음"]

    p = _ledger_path()
    seen = 0
    with _Lock(p):
        # MED-29 · MED-44b: 이전 실행이 격리에 남긴 입력을 원래 이름으로 되돌려
        # 아래 Downloads 스캔이 자연스럽게 다시 집게 한다. 오래된 것은 정리한다.
        for note in _restore_quarantine():
            notes.append(note)

        for entry in sorted(os.scandir(dl), key=lambda e: e.name):
            m = DECISION_RE.fullmatch(entry.name)
            if not m:
                continue
            seen += 1
            if seen > MAX_DECISION_FILES:
                notes.append("후보 파일이 너무 많다 — 나머지는 다음 실행으로 미룬다")
                break
            expect_run = m.group(1)
            src = os.path.join(dl, entry.name)

            # 감사 MED: 이름 기준으로 stat → open → remove 하면 그 사이 같은 이름이
            # symlink 로 바뀌거나 새 다운로드로 교체될 수 있다(둘 다 재현됨).
            # → 먼저 전용 quarantine 으로 atomic rename 해 **객체를 고정**한다.
            #   이후 모든 작업(읽기·삭제)은 quarantine 쪽 경로만 쓴다.
            path = os.path.join(_quarantine_dir(), f"{uuid.uuid4().hex}.json")
            try:
                if entry.is_symlink():
                    notes.append(f"{entry.name}: symlink — 거부")
                    continue
                os.replace(src, path)          # 같은 볼륨이므로 atomic
                # 실패 시 되돌릴 원래 이름을 사이드카로 남긴다 (MED-29)
                with open(path + ".name", "w", encoding="utf-8") as mf:
                    mf.write(entry.name)
            except OSError as e:
                # 여기서 실패하면 격리 폴더가 Downloads 와 다른 볼륨이라는 뜻이다.
                # copy+delete 로 눙치지 않는다 — 객체 고정이 목적이라 폴백은 보증을 깬다.
                notes.append(f"{entry.name}: 격리 이동 실패({type(e).__name__}) — "
                             f"격리 폴더가 Downloads 와 다른 볼륨이 아닌지 확인할 것")
                continue

            try:
                with open(path, "rb") as fh:
                    stt = os.fstat(fh.fileno())
                    if not stat.S_ISREG(stt.st_mode):
                        _reject_perm(path, notes, f"{entry.name}: 일반 파일이 아니다 — 거부")
                        continue
                    if stt.st_size > MAX_DECISION_BYTES:
                        _reject_perm(path, notes, f"{entry.name}: 1MB 초과 — 거부")
                        continue
                    blob = fh.read(MAX_DECISION_BYTES + 1)
                if len(blob) > MAX_DECISION_BYTES:
                    _reject_perm(path, notes, f"{entry.name}: 1MB 초과 — 거부")
                    continue
                raw = json.loads(blob.decode("utf-8"),
                                 object_pairs_hook=_reject_dupe_keys,
                                 parse_constant=lambda c: (_ for _ in ()).throw(
                                     ValueError("NaN/Infinity 거부")))
            except Exception as e:
                _reject_perm(path, notes,
                             f"{entry.name}: 읽기/파싱 실패({type(e).__name__}) — 거부")
                continue

            obj, why = _validate_decision(raw, expect_run)
            if obj is None:
                _reject_perm(path, notes, f"{entry.name}: 스키마 거부 — {why}")
                continue

            baseline = _txn_baseline()          # HIGH-2: 읽기 전에 기준 캡처
            recs, broken = read_ledger()
            if broken:
                # HIGH-5: 손상 줄이 있으면 rewrite 로 증거를 지우지 않는다
                notes.append(f"{entry.name}: 원장에 손상 줄 {broken}개 — "
                             f"rewrite 보류(증거 보존). 수동 확인 필요")
                continue
            if not any(r.get("run") == obj["run"] for r in recs):
                notes.append(f"{entry.name}: 원장에 해당 run 없음 — 보류")
                continue

            # 감사 MED: 같은 run/lane 의 **모든** 행에 총계를 복사해 집계가 배로 뻥튀기됐다
            # (2행이면 4/3 이 8/6 이 됐다). 레인당 정확히 한 행에만 기록한다.
            # 여러 워커가 한 레인을 공유하면 크레딧이 첫 행에 몰리는 한계는 남는다 —
            # 정확한 귀속은 시트 항목에 record_id 를 넣어야 하고 그건 별도 작업이다.
            # MED-59: 첫 record 에 몰면 원장 줄 순서에 따라 어느 effort 가
            # 크레딧을 받는지 달라진다. (ts, task) 로 정렬해 결정적으로 고른다.
            changed = 0
            done_lanes = set()
            # 실사용에서 잡힘 (2026-09-04): (ts, task) 로만 정렬하니
            # 실패한 워커 레코드가 채택률 크레딧을 받았다.
            # 실패한 워커는 산출물이 없으므로 채택될 항목도 없다 —
            # status=done 을 먼저 놓고, 그 안에서 (ts, task) 로 결정한다.
            for r in sorted((x for x in recs if x.get("run") == obj["run"]),
                            key=lambda x: (0 if x.get("status") == "done" else 1,
                                           str(x.get("ts", "")), str(x.get("task", "")))):
                lane = r.get("lane")
                if lane in done_lanes:
                    continue
                b = obj["by_lane"].get(lane)
                if b:
                    r["items"], r["accepted"] = b["items"], b["accepted"]
                    done_lanes.add(lane)
                    changed += 1
            if not changed:
                notes.append(f"{entry.name}: 일치하는 레인 없음 — 보류")
                continue

            dirty, dwhy = _ledger_dirty()
            if dirty:
                notes.append(f"{entry.name}: {dwhy} — merge 보류")
                continue

            payload = ("\n".join(json.dumps(r, ensure_ascii=False,
                                            separators=(",", ":")) for r in recs)
                       + "\n").encode("utf-8")
            why = verify_payload(payload)
            if why:
                notes.append(f"{entry.name}: merge 후 payload 검증 실패({why}) — 중단")
                continue

            _atomic_write_bytes(p, payload)
            st, cnote = _commit_cas(
                payload, f"chore(vibe): merge decisions {obj['run']} ({changed} rec)",
                baseline)
            if st != "ok":
                # 감사 HIGH-4: 부분 성공에서 소비하면 재처리할 입력이 사라진다.
                # quarantine 파일과 manifest 를 그대로 남긴다.
                _journal("collect_not_consumed", {"run": obj["run"], "status": st})
                notes.append(f"{entry.name}: {cnote} — 입력 보존(재시도 가능)")
                continue
            merged.append(obj["run"])

            # 재생 방지는 2층이다. append-only 레지스트리를 **먼저** 쓴다 —
            # 여기서 죽어도 재제출이 막히는 쪽(fail-closed)으로 남아야 한다.
            # 실사용에서 잡힘 (2026-09-04): Simon 이 같은 결정을 두 번 붙여넣어
            # 확인해 보니 _mark_nonce_spent 가 정의만 되고 아무도 부르지 않았다.
            # manifest 의 consumed 플래그 한 층뿐이었고, 그 쓰기는 예외를
            # 통째로 삼키고 있었다 — 정확히 레지스트리가 막으려던 실패 모드다.
            man_now, _ = _read_manifest(obj["run"])
            nonce_ok = _mark_nonce_spent(man_now["nonce"]) if man_now else False
            man_ok = _consume_manifest(obj["run"])
            if not (nonce_ok or man_ok):
                # 두 층 다 실패 = 같은 파일을 다시 넣으면 또 merge 된다. 크게 알린다.
                _journal("replay_guard_failed", {"run": obj["run"]})
                notes.append(f"{entry.name}: ⚠ 재생 방지 기록 실패 — "
                             f"이 결과를 다시 제출하면 중복 반영된다. 수동 확인 필요")
            elif not nonce_ok:
                notes.append(f"{entry.name}: nonce 레지스트리 기록 실패 "
                             f"(manifest 층은 살아 있다)")
            elif not man_ok:
                notes.append(f"{entry.name}: manifest 소비 기록 실패 "
                             f"(nonce 레지스트리는 살아 있다)")
            notes.append(f"{entry.name}: {changed}개 레코드 merge · 커밋됨")
            if consume:
                try:
                    os.remove(path)            # quarantine 사본만 지운다
                    if os.path.exists(path + ".name"):
                        os.remove(path + ".name")
                    notes.append(f"{entry.name}: 소비(삭제)")
                except OSError:
                    notes.append(f"{entry.name}: 소비 실패 — 수동 삭제 필요")

    return merged, notes


def unmerged_runs():
    """items 가 비어 있는(=채택률 미회수) run 목록. §10 경고용."""
    recs, _ = read_ledger()
    by_run = {}
    for r in recs:
        by_run.setdefault(r.get("run"), []).append(r)
    return [run for run, rs in by_run.items()
            if all(r.get("items") in (None, 0) for r in rs)]


# 워커가 산출물을 못 낸 종료 상태. 이 run 은 '채택률 미회수'가 아니라 '라운드 실패'다.
NO_OUTPUT_STATUSES = {"failed", "timeout", "cancelled", "unknown"}


def run_recovery_state():
    """run 마다 **채택률이 왜 없는가**를 가른다. 반환 {run: (state, detail)}.

    `unmerged_runs()` 는 items==0 인 run 을 전부 '미회수' 한 덩어리로 보고한다.
    그런데 그 안에는 처방이 서로 다른 상태가 셋 섞여 있다:

      no-output      워커가 산출물을 0건 냈다(timeout·failed). 채택할 항목 자체가
                     없다 — 학습 정지가 아니라 **라운드 실패**다. 시트를 만들어도
                     채워질 것이 없다. 고칠 곳은 디스패치·타임아웃 쪽이다.
      sheet-pending  시트는 만들었고 회수만 안 됐다. 처방 = 시트에서 [결과 저장] 한 번.
      no-sheet       시트를 **아예 안 만들었다**. 이게 진짜 학습 정지다.
                     처방 = `make_decision_sheet.py` 로 만든다 — 손으로 조립한 시트는
                     `decisions_run_*.json` 을 내지 않아 회수 경로가 통째로 빠진다.
                     (2026-09-13 실측: 미회수 4건 중 4건이 이 상태였다.)

    왜 가르나: 셋을 한 신호로 보고하면 "라운드가 실패했다"와 "내가 절차를 건너뛰었다"가
    같은 경고가 되어, **고쳐야 할 쪽을 고를 수 없다.** 모든 입력에 같은 답을 주는
    신호는 신호가 아니다.
    """
    recs, _ = read_ledger()
    by_run = {}
    for r in recs:
        by_run.setdefault(r.get("run"), []).append(r)
    out = {}
    for run, rs in by_run.items():
        if any((r.get("items") or 0) > 0 for r in rs):
            out[run] = ("recovered", "채택률 회수됨")
            continue
        statuses = {(r.get("status") or "unknown") for r in rs}
        if statuses and statuses <= NO_OUTPUT_STATUSES:
            out[run] = ("no-output",
                        "워커 %d개가 전부 %s — 채택할 항목이 없다"
                        % (len(rs), "·".join(sorted(statuses))))
            continue
        if os.path.exists(os.path.join(_pending_dir(), f"{run}.json")):
            out[run] = ("sheet-pending", "시트는 있다 — [결과 저장]만 안 돌아왔다")
            continue
        out[run] = ("no-sheet", "시트를 만든 적이 없다 — 회수 경로가 통째로 없다")
    return out


def new_record(run, task, cls, lane, effort, falsifiable, explore, status,
               sec=0, retries=0, quota_delta=None, guard_violations=None):
    """§9 스키마 그대로. 산출물 본문은 넣지 않는다 — 메트릭만."""
    return {
        "run": run,
        "ts": datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M%z"),
        "task": task, "class": cls, "lane": lane, "effort": effort,
        "falsifiable": bool(falsifiable), "explore": bool(explore),
        "status": status, "sec": int(sec), "retries": int(retries),
        "quota_delta": quota_delta or {},
        "items": 0, "accepted": 0,
        "guard_violations": guard_violations or [],
    }


def main():
    if "--collect" in sys.argv:
        merged, notes = collect_decisions()
        for n in notes:
            print(" ", n)
        print(f"merge 된 run: {merged or '없음'}")
    elif "--status" in sys.argv:
        recs, broken = read_ledger()
        um = unmerged_runs()
        print(f"원장 {_ledger_path()}")
        print(f"  레코드 {len(recs)} · 깨진 줄 {broken}")
        print(f"  채택률 미회수 run {len(um)}개")
    else:
        print("--collect : 다운로드의 decisions_run_*.json 회수")
        print("--status  : 원장 상태")


if __name__ == "__main__":
    main()
