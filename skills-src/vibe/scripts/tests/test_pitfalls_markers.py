"""pitfalls.md quarantine-marker regression checks.

Reads one reference file only: no child processes, network or writes.
A new pitfall that prescribes a quarantined or out-of-allowlist Orca action
must carry "⛔ [격리]" or "⚠ [가드 밖]" right after its "- " bullet marker.
Lines above the first bullet may name such actions only on a line that
explains one of those markers.
"""
import re
import unittest
from pathlib import Path

PITFALLS = Path(__file__).resolve().parents[2] / "references" / "pitfalls.md"

# (label, regex). Extend this list; never shorten it.
DANGEROUS = (
    ("terminal send", r"terminal\s+send"),
    ("terminal read", r"terminal\s+read"),
    ("worker-start", r"worker-start"),
    ("worker-stop", r"worker-stop"),
    ("--retry-of", r"--retry-of"),
    ("kill_worker", r"kill_worker"),
    ("codex exec", r"codex\s+exec"),
    ("run_codex_exec", r"run_codex_exec"),
    ("--probe-efforts", r"--probe-efforts"),
    ("task-update", r"task-update"),
    ("PID 실존", r"PID\s*실존"),
    ("orchestration check", r"orchestration\s+check"),
    ("orchestration send", r"orchestration\s+send"),
    ("send --body", r"send\s+--body"),
    ("check --ack", r"check\s+--ack"),
    ("check --wait", r"check\s+--wait"),
    ("--objective", r"--objective"),
    # 2026-09-28 review: dispatch flags and quarantined entrypoints that can be
    # prescribed without the literal verb names above.
    ("--agent", r"--agent\b"),
    ("--setup", r"--setup\b"),
    ("--enter", r"--enter\b"),
    ("quarantined entrypoint", r"run_dispatch|validate_and_dispatch|probe_orca_efforts"),
    ("worker-release", r"worker-release"),
    ("orchestration ack/reply", r"orchestration\s+(?:ack|reply)"),
    ("terminal write verb", r"terminal\s+(?:create|close|kill|stop|write)"),
    ("nudge_held_prompt", r"nudge_held_prompt"),
    ("worker launch (ko)", r"워커[^\n]{0,20}띄"),
)
_DANGEROUS = [(label, re.compile(rx, re.IGNORECASE)) for label, rx in DANGEROUS]

BULLET = re.compile(r"^\s*[-*+]\s+")
QUARANTINED = re.compile(r"^\s*[-*+]\s+⛔️? \[격리\]\s")
OUTSIDE_GUARD = re.compile(r"^\s*[-*+]\s+⚠️? \[가드 밖\]\s")

# Bullets the 2026-09-28 audit classed as strictly forbidden prescriptions.
STRICT_ANCHORS = (
    "`agent_prompt_blocked` 는 프롬프트 탓이",
    "실패한 task 는 재디스패치가",
    "`codex exec` 는 `--effort` 를 거부한다",
    "그 측정은 이제 공짜다",
    "worker-stop이 프로세스를 안 죽인다",
    "`turnStart: observed` 여도",
    "`Waiting for workflow` 로 쉬는 워커는",
    "claude 워커를 Claude Code 가 신뢰하지 않는",
)
# Bullets that describe actions outside the read-only allowlist.
GUARD_ANCHORS = (
    "codex 보안 감사는 Trusted Access",
    "`orca orchestration check` 응답은",
    "Git Bash 가 `/` 로 시작하는",
    "게이트 워커는 `worker_done` 이나",
    "heartbeat 만 든 배달도 ack 한다",
    "감시 루프 하나가 run 전체의 메시지를",
    "`check --wait --types worker_done,…` 는",
    "`worker-start` 셀렉터는 Orca 터미널 밖에서",
    "bash 큰따옴표 안의 백틱은 `send --body`",
    "Orca agent id ≠ CLI 이름",
    "생성 플래그는 새 워크트리에만",
    "`--model` 은 Claude·Codex·Cursor 만",
    "`validate_plan` 은 쿼터를 보지 않는다",
)
# A header line may name dangerous verbs only while explaining a marker.
HEADER_TOKENS = ("⛔ [격리]", "⚠ [가드 밖]")


def parse(text):
    """Split into (header_lines, items). An item is (first_line, joined_text).

    The header is everything before the first bullet. Indented non-blank lines
    after a bullet are its continuation. Any other line is its own item so a
    dangerous prescription written as a plain paragraph is still checked.
    """
    lines = text.splitlines()
    first = next((i for i, line in enumerate(lines) if BULLET.match(line)), len(lines))
    header, items, current = lines[:first], [], None
    for line in lines[first:]:
        if BULLET.match(line):
            current = [line, line]
            items.append(current)
        elif line.strip() and line[:1].isspace() and current is not None:
            current[1] += "\n" + line
        else:
            current = None
            if line.strip():
                items.append([line, line])
    return header, [(head, body) for head, body in items]


def hits(body):
    return [label for label, rx in _DANGEROUS if rx.search(body)]


def is_marked(head):
    return bool(QUARANTINED.match(head) or OUTSIDE_GUARD.match(head))


def unmarked(text):
    header, items = parse(text)
    # The header is not exempt: a new note placed above the first bullet must
    # not smuggle a prescription past the per-bullet check.
    found = [(line[:80], hits(line)) for line in header
             if hits(line) and not any(token in line for token in HEADER_TOKENS)]
    return found + [(head[:80], hits(body)) for head, body in items
                    if hits(body) and not is_marked(head)]


class PitfallsMarkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PITFALLS.read_bytes().decode("utf-8")
        cls.header, cls.items = parse(cls.text)

    def test_every_dangerous_line_is_marked(self):
        self.assertEqual(unmarked(self.text), [])

    def test_at_least_eight_quarantined_lines(self):
        count = sum(1 for head, _ in self.items if QUARANTINED.match(head))
        self.assertGreaterEqual(count, 8)
        guard = sum(1 for head, _ in self.items if OUTSIDE_GUARD.match(head))
        self.assertGreaterEqual(guard, 7)

    def test_audited_lines_keep_their_class(self):
        for anchor in STRICT_ANCHORS:
            heads = [h for h, _ in self.items if anchor in h]
            self.assertEqual(len(heads), 1, anchor)
            self.assertRegex(heads[0], QUARANTINED, anchor)
        for anchor in GUARD_ANCHORS:
            heads = [h for h, _ in self.items if anchor in h]
            self.assertEqual(len(heads), 1, anchor)
            self.assertTrue(is_marked(heads[0]), anchor)

    def test_header_note_explains_quarantine_and_doorbell(self):
        self.assertTrue(self.header and self.header[0].startswith("# "))
        note = "\n".join(self.header)
        for needle in ("peer_link.py", "Legacy Orca routing", "⛔ [격리]",
                       "⚠ [가드 밖]", "과거 함정 기록"):
            self.assertIn(needle, note)
        self.assertEqual([line for line in self.header if BULLET.match(line)], [])

    def test_utf8_claim_is_corrected_without_erasing_history(self):
        line = next(h for h, _ in self.items if "cp949 크래시" in h)
        self.assertIn("스크립트가 stdout을 UTF-8로 고정한다", line)
        self.assertIn("2026-09-28", line)
        self.assertIn("check_tooling.py", line)
        self.assertIn("바이트로 읽어 UTF-8 로 디코드", line)

    def test_checker_bites_on_synthetic_additions(self):
        base = ("# t\n\n> `⛔ [격리]` note: terminal send\n\n"
                "- ⛔ [격리] **old**: `worker-start` x\n")
        self.assertEqual(unmarked(base), [])
        for added in ("- **new**: `orca terminal send --enter` 로 깨운다\n",
                      "- **new**: 설명\n  이어서 `kill_worker.py --kill`\n",
                      "새 문단: `codex exec -` 로 돌린다\n",
                      "- ⚠ 표시가 본문에만 있다 `check --ack`\n",
                      "- **new**: grok 은 `--agent grok` 만 준다\n",
                      "- **new**: 게이트 없이 코딩 워커만 먼저 띄운다\n"):
            found = unmarked(base + added)
            self.assertEqual(len(found), 1, added)
        self.assertEqual(unmarked(base + "- ⚠ [가드 밖] **new**: `check --wait`\n"), [])
        # A new note above the first bullet is checked too.
        top = base.replace("# t\n\n", "# t\n\n> 팁: `orca terminal send --enter` 로 깨운다\n\n", 1)
        self.assertEqual(len(unmarked(top)), 1)


if __name__ == "__main__":
    unittest.main()
