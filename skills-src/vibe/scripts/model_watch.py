"""Zero-model-call release watch; official changes are evidence, not routes.

The Friday scan records newly linked model announcements. A coordinator must
verify general availability and collect public feedback before any route review.
This script never invokes an LLM, Bot, API key, installer, Git or payment path.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
import errno
import hashlib
import ipaddress
import json
import os
import re
import tempfile
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path


KST = timezone(timedelta(hours=9))
MAX_PAGE_BYTES = 2 * 1024 * 1024
MAX_STATE_BYTES = 4 * 1024 * 1024
MAX_CAPTURED_POSTS = 128
MAX_FEEDBACK_URL_LENGTH = 2048
SOURCES = {
    "openai": "https://openai.com/news/rss.xml",
    "anthropic": "https://www.anthropic.com/news",
    "google": "https://blog.google/innovation-and-ai/models-and-research/",
    "xai": "https://x.ai/news",
}
MODEL_NAME = re.compile(
    r"\b(?:GPT[-\s]?\d+(?:\.\d+)*(?:[-\s]?(?:o(?:[-\s]mini)?|mini|nano|turbo|Astra|Sol|Luna|Terra))?|"
    r"o\d+(?:[-\s](?:mini|preview|pro))?|"
    r"(?:Claude\s+)?(?:Sonnet|Opus|Haiku|Fable|Mythos)\s+\d+(?:\.\d+)?|"
    r"Gemini\s+\d+(?:\.\d+)?(?:\s+(?:Pro|Flash))?|Grok\s+\d+(?:\.\d+)?)\b",
    re.IGNORECASE,
)


def iso(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("timezone-aware time required")
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("stored time has no zone")
    return parsed.astimezone(timezone.utc)


def canonical_link(base: str, href: str) -> str | None:
    target = urllib.parse.urljoin(base, href)
    parsed = urllib.parse.urlsplit(target)
    origin = urllib.parse.urlsplit(base)
    if parsed.scheme != "https" or parsed.hostname != origin.hostname or parsed.port not in (None, 443):
        return None
    if parsed.username or parsed.password or not parsed.path:
        return None
    return urllib.parse.urlunsplit(("https", parsed.hostname.lower(),
                                   parsed.path.rstrip("/") or "/", "", ""))


class LinkParser(HTMLParser):
    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.href: str | None = None
        self.parts: list[str] = []
        self.links: dict[str, str] = {}
        self.heading_tag: str | None = None
        self.heading_parts: list[str] = []
        self.headings: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h2", "h3", "h4"}:
            self.heading_tag = tag
            self.heading_parts = []
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.heading_tag is not None:
            self.heading_parts.append(data)
        if self.href is not None:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == self.heading_tag:
            title = " ".join(" ".join(self.heading_parts).split())[:240]
            if MODEL_NAME.search(title):
                self.headings.add(title)
            self.heading_tag = None
            self.heading_parts = []
        if tag != "a" or self.href is None:
            return
        title = " ".join(" ".join(self.parts).split())[:240]
        link = canonical_link(self.base, self.href)
        if link and MODEL_NAME.search(title):
            self.links[link] = title
        self.href = None
        self.parts = []


def extract_model_links(page: str, base: str) -> dict[str, str]:
    return extract_model_mentions(page, base)[0]


def extract_model_mentions(page: str, base: str) -> tuple[dict[str, str], set[str]]:
    if base.endswith(".xml"):
        links: dict[str, str] = {}
        for item in ET.fromstring(page).findall(".//item"):
            title = " ".join((item.findtext("title") or "").split())[:240]
            link = canonical_link(base, item.findtext("link") or "")
            if link and MODEL_NAME.search(title):
                links[link] = title
        return links, set()
    parser = LinkParser(base)
    parser.feed(page)
    parser.close()
    return parser.links, parser.headings


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, hostname: str):
        self.hostname = hostname

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        target = urllib.parse.urlsplit(newurl)
        if target.scheme != "https" or target.hostname != self.hostname or target.port not in (None, 443):
            raise ValueError("cross-host redirect rejected")
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def fetch_public_page(_provider: str, url: str) -> str:
    request = urllib.request.Request(
        url, headers={"User-Agent": "SimonKModelWatch/1.0 (public-release-check)",
                      "Accept": "text/html,application/rss+xml,text/xml"}
    )
    opener = urllib.request.build_opener(OfficialRedirect(urllib.parse.urlsplit(url).hostname))
    with opener.open(request, timeout=12) as response:
        if urllib.parse.urlsplit(response.geturl()).hostname != urllib.parse.urlsplit(url).hostname:
            raise ValueError("cross-host redirect rejected")
        raw = response.read(MAX_PAGE_BYTES + 1)
    if len(raw) > MAX_PAGE_BYTES:
        raise ValueError("release page too large")
    return raw.decode("utf-8", errors="replace")


def feedback_query(item: dict) -> str | None:
    model = MODEL_NAME.search(item["title"])
    if model is None:
        return None
    return "https://www.reddit.com/search.rss?" + urllib.parse.urlencode(
        {"q": model.group(0), "sort": "new", "t": "week"})


def model_label(value: str) -> str:
    """Treat separator spellings alike without conflating model variants."""
    return re.sub(r"[-\s]+", "-", value.casefold())


def extract_public_feedback(feed: str, item: dict) -> list[dict]:
    root = ET.fromstring(feed)
    namespace = "{http://www.w3.org/2005/Atom}"
    model = MODEL_NAME.search(item["title"])
    if model is None:
        return []
    found: list[dict] = []
    for entry in root.findall(f"{namespace}entry")[:30]:
        title = " ".join((entry.findtext(f"{namespace}title") or "").split())[:240]
        if not any(model_label(match.group(0)) == model_label(model.group(0))
                   for match in MODEL_NAME.finditer(title)):
            continue
        link = entry.find(f"{namespace}link[@rel='alternate']")
        if link is None:
            link = entry.find(f"{namespace}link")
        url = link.get("href") if link is not None else None
        published = entry.findtext(f"{namespace}published")
        if not url or not published:
            continue
        parsed = urllib.parse.urlsplit(url)
        try:
            port = parsed.port
        except ValueError:
            continue
        if (len(url) > MAX_FEEDBACK_URL_LENGTH or parsed.scheme != "https"
                or parsed.hostname != "www.reddit.com" or parsed.query
                or parsed.username or parsed.password or port not in (None, 443)
                or not parsed.path):
            continue
        try:
            posted_at = parse_time(published)
        except ValueError:
            continue
        if posted_at < parse_time(item["release_verified_at"]):
            continue
        canonical_url = urllib.parse.urlunsplit(("https", "www.reddit.com", parsed.path, "", ""))
        found.append({"url": canonical_url, "title": title, "published_at": iso(posted_at)})
    return found


def empty_state() -> dict:
    return {"schema_version": 1, "sources": {}, "candidates": {}}


def scan_state(state: dict, fetch, now: datetime, force: bool = False,
               feedback_fetch=None) -> tuple[dict, dict]:
    current = copy.deepcopy(state) if state else empty_state()
    if current.get("schema_version") != 1:
        raise ValueError("unsupported watch state")
    current.setdefault("sources", {})
    current.setdefault("candidates", {})
    pending = any(item.get("status") == "official_unreviewed" or
                  (item.get("status") == "released" and candidate_status(item, now) != "review_ready")
                  for item in current["candidates"].values())
    previous_report = current.get("last_report") or {}
    retry_errors = bool(previous_report.get("errors") or previous_report.get("feedback_errors"))
    today = now.astimezone(KST).date()
    latest_friday = today - timedelta(days=(today.weekday() - 4) % 7)
    last_check = previous_report.get("checked_at")
    weekly_due = not last_check or parse_time(last_check).astimezone(KST).date() < latest_friday
    if not force and not weekly_due and not pending and not retry_errors:
        return current, {"status": "not_due", "new_candidates": [], "candidate_details": {},
                         "changed_sources": [], "errors": {}}
    report = {"status": "scanned", "checked_at": iso(now), "new_candidates": [],
              "candidate_details": {}, "changed_sources": [], "errors": {}, "feedback_captures": [],
              "feedback_errors": {}, "routing_changed": False}
    for provider, url in SOURCES.items():
        try:
            page = fetch(provider, url)
            if not isinstance(page, str):
                raise ValueError("invalid page")
            digest = hashlib.sha256(page.encode("utf-8")).hexdigest()
            links, headings = extract_model_mentions(page, url)
        except (OSError, ValueError, TimeoutError, ET.ParseError) as exc:
            report["errors"][provider] = type(exc).__name__
            continue
        previous = current["sources"].get(provider)
        if previous and previous["sha256"] != digest:
            report["changed_sources"].append(provider)
        if previous:
            for link, title in links.items():
                if link in previous.get("links", []):
                    continue
                key = hashlib.sha256(f"{provider}\n{link}".encode("utf-8")).hexdigest()[:20]
                if key not in current["candidates"]:
                    current["candidates"][key] = {
                        "provider": provider, "title": title, "official_url": link,
                        "first_seen_at": iso(now), "status": "official_unreviewed",
                        "routing_ready": False,
                    }
                    report["new_candidates"].append(key)
            for title in sorted(headings - set(previous.get("headings", []))):
                if title in links.values():
                    continue
                key = hashlib.sha256(f"{provider}\n{url}\n{title}".encode("utf-8")).hexdigest()[:20]
                if key not in current["candidates"]:
                    current["candidates"][key] = {
                        "provider": provider, "title": title, "official_url": url,
                        "first_seen_at": iso(now), "status": "official_unreviewed",
                        "routing_ready": False,
                    }
                    report["new_candidates"].append(key)
        current["sources"][provider] = {
            "url": url, "sha256": digest, "links": sorted(links),
            "headings": sorted(headings), "checked_at": iso(now)
        }
    if feedback_fetch is not None:
        for key, item in current["candidates"].items():
            if item.get("status") != "released":
                continue
            query = feedback_query(item)
            if query is None:
                continue
            try:
                posts = extract_public_feedback(feedback_fetch("reddit", query), item)
            except (OSError, ValueError, TimeoutError, ET.ParseError) as exc:
                report["feedback_errors"][key] = type(exc).__name__
                continue
            captures = item.setdefault("captures", [])
            existing = ({post["url"] for post in captures}
                        | {post["url"] for post in item.get("feedback", [])})
            for post in posts:
                if post["url"] not in existing:
                    captures.append({**post, "observed_at": iso(now), "reviewed": False})
                    existing.add(post["url"])
                    report["feedback_captures"].append(key)
            # Reviewed evidence already lives in feedback; bound unreviewed queue growth.
            captures[:] = [post for post in captures if not post.get("reviewed")][-MAX_CAPTURED_POSTS:]
    report["candidate_details"] = {
        key: {field: current["candidates"][key][field]
              for field in ("provider", "title", "official_url", "status")}
        for key in report["new_candidates"]
    }
    return current, report


def confirm_release(state: dict, key: str, now: datetime, official_url: str) -> None:
    item = state["candidates"][key]
    parsed = urllib.parse.urlsplit(official_url)
    stored = canonical_link(item["official_url"], item["official_url"])
    canonical = canonical_link(item["official_url"], official_url) if parsed.scheme == "https" else None
    if item["status"] != "official_unreviewed" or stored is None or canonical != stored:
        raise ValueError("official release evidence does not match candidate")
    if now < parse_time(item["first_seen_at"]):
        raise ValueError("release confirmation predates discovery")
    item.update(status="released", release_verified_at=iso(now), feedback=[],
                captures=[], routing_ready=False)


def add_feedback(state: dict, key: str, now: datetime, url: str, sentiment: str) -> None:
    item = state["candidates"][key]
    parsed = urllib.parse.urlsplit(url)
    if item["status"] != "released" or now < parse_time(item["release_verified_at"]):
        raise ValueError("release is not in the observation window")
    safe_query = (not parsed.query or
                  (parsed.hostname == "news.ycombinator.com" and re.fullmatch(r"id=\d+", parsed.query)))
    hostname = (parsed.hostname or "").rstrip(".")
    public_host = bool(hostname and "." in hostname and
                       not hostname.endswith((".local", ".localhost", ".internal",
                                                  ".lan", ".test", ".example", ".invalid")))
    if public_host:
        try:
            ipaddress.ip_address(hostname)
        except ValueError:
            pass
        else:
            public_host = False
    if (len(url) > MAX_FEEDBACK_URL_LENGTH or parsed.scheme != "https" or not public_host
            or parsed.username or parsed.password
            or parsed.port not in (None, 443) or not safe_query):
        raise ValueError("public HTTPS feedback URL without credentials required")
    if sentiment not in {"positive", "mixed", "negative"}:
        raise ValueError("invalid sentiment label")
    canonical = urllib.parse.urlunsplit(("https", hostname, parsed.path, parsed.query, ""))
    if any(entry["url"] == canonical for entry in item["feedback"]):
        raise ValueError("duplicate feedback URL")
    capture = next((entry for entry in item.get("captures", []) if entry["url"] == canonical), None)
    observed_at = capture["observed_at"] if capture else iso(now)
    item["feedback"].append({"url": canonical, "observed_at": observed_at,
                             "reviewed_at": iso(now), "sentiment": sentiment})
    if capture:
        capture["reviewed"] = True


def candidate_status(item: dict, now: datetime) -> str:
    if item["status"] != "released":
        return "waiting_official_review"
    observations = [parse_time(entry["observed_at"]) for entry in item["feedback"]]
    release = parse_time(item["release_verified_at"])
    if (now - release < timedelta(hours=24) or len(observations) < 2
            or max(observations) - min(observations) < timedelta(hours=20)):
        return "monitoring"
    return "review_ready"


def default_state_path() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise ValueError("LOCALAPPDATA is required; pass --state explicitly elsewhere")
    return Path(local) / "SimonK" / "vibe" / "model-watch.json"


def read_state(path: Path) -> dict:
    if not path.exists():
        return empty_state()
    if path.stat().st_size > MAX_STATE_BYTES:
        raise ValueError("watch state too large")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported watch state")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if len(payload) > MAX_STATE_BYTES:
        raise ValueError("watch state too large")
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".model-watch-", delete=False) as temp:
        temporary = Path(temp.name)
        temp.write(payload)
        temp.flush()
        os.fsync(temp.fileno())
    try:
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


@contextmanager
def state_lock(path: Path, timeout: float = 120):
    """Serialize a complete read/scan/write transaction across CLI processes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    acquired = False
    try:
        if os.fstat(fd).st_size == 0:
            os.write(fd, b"\0")
        deadline = time.monotonic() + timeout
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN):
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError("model watch state is locked") from exc
                time.sleep(min(0.05, max(0, deadline - time.monotonic())))
        yield
    finally:
        try:
            if acquired:
                if os.name == "nt":
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["scan", "status", "confirm-release", "add-feedback"])
    parser.add_argument("--state", type=Path)
    parser.add_argument("--force", action="store_true", help="scan outside Friday/pending follow-up")
    parser.add_argument("--key")
    parser.add_argument("--url")
    parser.add_argument("--sentiment", choices=["positive", "mixed", "negative"])
    args = parser.parse_args()
    path = args.state or default_state_path()
    with state_lock(path):
        state = read_state(path)
        now = datetime.now(timezone.utc)
        if args.action == "scan":
            state, result = scan_state(state, fetch_public_page, now, force=args.force,
                                       feedback_fetch=fetch_public_page)
            if result["status"] == "scanned":
                state["last_report"] = result
                write_json(path, state)
        elif args.action == "status":
            result = {"checked_at": iso(now), "candidates": {
                key: candidate_status(item, now) for key, item in state["candidates"].items()},
                "candidate_details": {
                    key: {"provider": item["provider"], "title": item["title"],
                          "official_url": item["official_url"]}
                    for key, item in state["candidates"].items()},
                "last_report": state.get("last_report")}
        elif args.action == "confirm-release":
            if not args.key or not args.url:
                parser.error("--key and --url are required")
            confirm_release(state, args.key, now, args.url)
            write_json(path, state)
            result = {"status": "monitoring", "key": args.key, "routing_changed": False}
        else:
            if not args.key or not args.url or not args.sentiment:
                parser.error("--key, --url and --sentiment are required")
            add_feedback(state, args.key, now, args.url, args.sentiment)
            write_json(path, state)
            result = {"status": candidate_status(state["candidates"][args.key], now),
                      "key": args.key, "routing_changed": False}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not (result.get("errors") or result.get("feedback_errors")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
