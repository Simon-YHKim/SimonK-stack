"""Offline bus watcher tests: disposable bus only, no process or network."""
import sys


def deny_effects(event, args):
    if event.startswith(("subprocess.", "socket.", "os.exec", "os.spawn")) or event in {
            "os.system", "os.kill", "os.killpg"}:
        raise AssertionError("External effects forbidden in bus watcher fixtures")


sys.addaudithook(deny_effects)

import collections
import contextlib
import glob
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

BOT_ROOT = Path(__file__).resolve().parents[2]
AGENT_LABELS = {"claude": "Claude Code", "codex": "Codex"}
# The 2026-09-26 pattern; the default --coding-label must rebuild it exactly.
ORIGINAL_CODING_MARK = (r"(담당 봇|보낼 봇|수신|Task for)\s*[:：—-]?.*Coding LLM"
                        r"|^#\s*Task\s*[—-]+\s*Coding\b"
                        r"|Coding LLM\s*[:·(]")


def load_watcher(bus: Path, drafts: Path, hub: Path, home: Path = None):
    env = {"VIBE_BOT_BUS": str(bus), "VIBE_BOT_DRAFTS": str(drafts), "VIBE_BOT_HUB_STATUS": str(hub)}
    if home is not None:
        # expanduser reads USERPROFILE on Windows and HOME elsewhere.
        env.update({"HOME": str(home), "USERPROFILE": str(home)})
    with patch.dict(os.environ, env):
        spec = importlib.util.spec_from_file_location("bus_watch_fixture", BOT_ROOT / "scripts/bus_watch.py")
        value = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(value)
    return value


def write(path: Path, text: str, age_seconds: float = 0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if age_seconds:
        past = time.time() - age_seconds
        os.utime(path, (past, past))
    return path


def tree_digest(root: Path) -> dict:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def make_bus(base: Path):
    bus, drafts, hub = base / "bus", base / "drafts", base / "hub" / "STATUS.md"
    for d in ("relay/inbox", "relay/outbox", "keys/inbox", "keys/outbox"):
        (bus / d).mkdir(parents=True)
    drafts.mkdir(parents=True)
    write(hub, "nonce|task\n")
    write(bus / "relay/STATUS.md", "# Relay STATUS\n")
    return bus, drafts, hub


def invoke(watcher, *args):
    out, err = io.StringIO(), io.StringIO()
    with patch.object(sys, "argv", ["bus_watch.py", *args]), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        watcher.main()
    return out.getvalue(), err.getvalue()


def norm(path) -> str:
    return os.fspath(path).replace("\\", "/")


class BusWatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.bus, self.drafts, self.hub = make_bus(base)
        self.state = base / "state" / "bus_watch.json"
        self.w = load_watcher(self.bus, self.drafts, self.hub)

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, *args):
        return invoke(self.w, "--state", str(self.state), *args)[0]

    def test_classification_separates_production_changes_and_org_noise(self):
        self.assertEqual(self.w.classify("x/keys/outbox/vb-simon-go-enabled-1.result.md"), "ALERT")
        self.assertEqual(self.w.classify("x/relay/outbox/vb-0123abcd.result.md"), "CODING")
        self.assertEqual(self.w.classify("x/relay/inbox/ping-relay-vb-0123abcd.md"), "CODING")
        for noise in ("x/drafts/hr-kpi.md", "x/relay/outbox/_tmp-hr-draft.md", "x/drafts/_relay-copy.md"):
            self.assertEqual(self.w.classify(noise), "NOISE", noise)

    def test_reply_is_found_in_any_outbox_with_any_suffix(self):
        write(self.bus / "relay/inbox/vb-11111111.claim", "Relay\n")
        write(self.bus / "keys/outbox/vb-11111111-adunit-label.result.md", "vb-11111111\n")
        status, paths = self.w.outbound_status("vb-11111111", {"pinged": False})
        self.assertEqual(status, "ANSWERED")
        self.assertTrue(paths[0].endswith("vb-11111111-adunit-label.result.md"))

    def test_one_reminder_only_after_claim_ttl(self):
        self.assertEqual(self.w.outbound_status("vb-22222222", {})[0], "UNCLAIMED")
        claim = write(self.bus / "relay/inbox/vb-22222222.claim", "Relay\n")
        self.assertTrue(self.w.outbound_status("vb-22222222", {"pinged": False})[0].startswith("CLAIMED"))
        past = time.time() - (self.w.PING_AFTER_MIN + 5) * 60
        os.utime(claim, (past, past))
        self.assertTrue(self.w.outbound_status("vb-22222222", {"pinged": False})[0].startswith("PING-DUE"))
        self.assertTrue(self.w.outbound_status("vb-22222222", {"pinged": True})[0].startswith("CLAIMED"))

    def test_coding_task_detection_ignores_own_outbound_tasks(self):
        task = write(self.bus / "relay/inbox/vb-33333333.md", "# 과제\n담당 봇: Coding LLM (via relay pointer)\n")
        own = write(self.bus / "relay/inbox/vb-44444444.md", "# 과제서\n작성 · 발행 Claude Code · 담당 봇: Coding LLM\n")
        # The monitor agrees with the scan: its own task is only a new file.
        watch = self.run_watch().splitlines()
        self.assertIn(f"CODING TASK: {norm(task)}", watch)
        self.assertIn(f"NEW bus file: {norm(own)}", watch)
        out = self.run_main()
        self.assertIn("OPEN-CODING-TASK vb-33333333", out)
        self.assertNotIn("vb-44444444", out.split("OPEN-CODING-TASK", 1)[-1])

    def test_heading_task_stays_open_until_the_coding_session_answers(self):
        nonce = "vb-1865-date-q5-fix"
        write(self.bus / f"relay/inbox/{nonce}.md", "# Task — Coding · #1865 date 09-26\n\n- From: Relay\n")
        self.assertIn(f"OPEN-CODING-TASK {nonce}", self.run_main())
        # Relay's own dispatch note reuses the nonce and names the Coding LLM.
        write(self.bus / f"relay/outbox/{nonce}.result.md",
              "# Result — dispatch\n- **Bot:** `aurelius`\n1. Coding LLM (file bus) will update the PR.\n")
        self.assertIn(f"OPEN-CODING-TASK {nonce}", self.run_main())
        write(self.bus / f"relay/outbox/{nonce}.coding.result.md",
              f"{nonce}\n# Result\n- **Bot:** Claude Code (코딩 LLM)\n")
        self.assertNotIn(f"OPEN-CODING-TASK {nonce}", self.run_main())

    def run_watch(self, *args):
        return invoke(self.w, "--state", str(self.state), "--watch", "--once", *args)[0]

    def test_watch_reports_an_answer_that_landed_before_the_monitor_started(self):
        # 2026-09-26 22:18: the review result arrived, then a monitor armed at
        # 22:19 took it as already present. The baseline must be the saved state.
        self.run_main("--track", "vb-b36e42bf")
        write(self.bus / "relay/outbox/vb-b36e42bf.result.md", "vb-b36e42bf\n# Result\n")
        out = self.run_watch()
        self.assertIn("ANSWER vb-b36e42bf:", out)

    def test_watch_orders_by_urgency_and_drops_org_noise(self):
        self.run_main("--track", "vb-88888888")
        write(self.drafts / "hr-kpi.md", "# HR\n")
        write(self.bus / "relay/outbox/_tmp-copy.md", "# tmp\n")
        write(self.bus / "relay/inbox/vb-99999999.md", "# Task — Coding · fix the copy\n")
        write(self.bus / "keys/outbox/vb-simon-go-x.result.md", "# Simon GO\n")
        write(self.bus / "keys/outbox/vb-88888888.result.md", "vb-88888888\n")
        lines = [l for l in self.run_watch().splitlines() if l]
        self.assertEqual([l.split(" ", 1)[0] for l in lines], ["ANSWER", "ALERT", "CODING"])
        self.assertFalse(any("hr-kpi" in l or "_tmp-copy" in l for l in lines))

    def test_watch_sees_a_nonce_tracked_after_it_started(self):
        # 2026-09-26 22:38: a request was tracked by a scan while the monitor
        # was already running; its answer must still read as ANSWER.
        self.run_main()
        state = self.w.load_state()
        emitted = set()
        self.assertEqual(self.w.watch_events(state, self.w.snapshot(), emitted), [])
        self.run_main("--track", "vb-5dd53ebc")
        write(self.bus / "relay/outbox/vb-5dd53ebc.result.md", "vb-5dd53ebc\n# Result\n")
        lines = self.w.watch_tick(state, emitted)
        self.assertEqual([l.split(" ", 1)[0] for l in lines], ["ANSWER"])

    def test_watch_never_writes_state(self):
        self.run_main()
        before = self.state.read_bytes()
        write(self.bus / "relay/outbox/vb-12121212.result.md", "vb-12121212\n")
        self.assertIn("NEW bus file:", self.run_watch())
        self.assertEqual(self.state.read_bytes(), before)

    def test_scan_never_writes_to_the_bus_and_keeps_state_outside(self):
        write(self.bus / "keys/outbox/vb-simon-go-x.result.md", "# Simon GO\n")
        write(self.drafts / "hr-org.md", "# HR\n")
        before = tree_digest(self.bus)
        out = self.run_main("--track", "vb-55555555")
        self.assertEqual(tree_digest(self.bus), before)
        self.assertIn("[ALERT]", out)
        self.assertIn("[NOISE] 1 file(s) skipped", out)
        self.assertIn("OUTBOUND vb-55555555: UNCLAIMED", out)
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertIn("vb-55555555", state["outbound"])
        self.assertFalse(Path(self.w.DEFAULT_STATE).resolve().is_relative_to(BOT_ROOT.resolve()))

    def test_second_scan_reports_only_changes(self):
        self.run_main()
        write(self.bus / "relay/outbox/vb-66666666.result.md", "vb-66666666\n")
        out = self.run_main()
        self.assertIn("vb-66666666.result.md", out)
        self.assertNotIn("STATUS.md", out.split("RELAY STATUS", 1)[0])

    def test_claude_defaults_are_unchanged(self):
        expected = os.path.join(os.path.expanduser("~"), ".claude", "state", "vibe-bot", "bus_watch.json")
        self.assertEqual(self.w.DEFAULT_STATE, expected)
        self.assertIs(self.w.DEFAULT_STATES["claude"], self.w.DEFAULT_STATE)
        self.w.configure()
        self.assertEqual((self.w.AGENT, self.w.STATE, self.w.SELF_LABEL), ("claude", expected, "Claude Code"))
        self.assertEqual(self.w.CODING_MARK.pattern, ORIGINAL_CODING_MARK)
        self.assertEqual(self.w.RELAY_STATUS, str(self.bus) + "/relay/STATUS.md")

    def test_files_that_vanish_between_glob_and_stat_or_open_are_skipped(self):
        task = write(self.bus / "relay/inbox/vb-77777777.md", "# Task — Coding · survives the race\n")
        claim = write(self.bus / "relay/inbox/vb-race.claim", "Relay\n")
        locked = write(self.bus / "keys/outbox/vb-race-locked.result.md", "vb-race\n- **Bot:** Claude Code\n")
        busy = write(self.bus / "relay/inbox/vb-race-busy.md", "# Task — Coding · locked while read\n")
        real_glob, real_stat, real_open = glob.glob, os.stat, open
        stat_errors = {norm(claim): FileNotFoundError, norm(locked): PermissionError,
                       norm(self.bus / "relay/STATUS.md"): FileNotFoundError}
        open_errors = {norm(locked): PermissionError, norm(busy): PermissionError}

        def fake_glob(pattern, *args, **kwargs):
            # Every pattern also returns a path that is gone by the time it is used.
            ghost = pattern.replace("*", "vanished") if "*" in pattern else pattern + ".vanished"
            return [*real_glob(pattern, *args, **kwargs), ghost]

        def fake_stat(path, *args, **kwargs):
            error = stat_errors.get(norm(path)) if isinstance(path, (str, os.PathLike)) else None
            if error:
                raise error("simulated race", os.fspath(path))
            return real_stat(path, *args, **kwargs)

        def fake_open(path, *args, **kwargs):
            error = open_errors.get(norm(path)) if isinstance(path, (str, os.PathLike)) else None
            if error:
                raise error("simulated race", os.fspath(path))
            return real_open(path, *args, **kwargs)

        with patch.object(self.w.glob, "glob", fake_glob), patch.object(self.w.os, "stat", fake_stat), \
                patch.object(self.w, "open", fake_open, create=True):
            watch_lines = self.run_watch().splitlines()
            out = self.run_main("--track", "vb-race", "--no-save")
            snap = self.w.snapshot()
            ghost_head = self.w.head(str(self.bus / "relay/inbox/vanished.md"))
        self.assertFalse(any("vanished" in l for l in watch_lines + out.splitlines()))
        self.assertIn(f"CODING TASK: {norm(task)}", watch_lines)
        self.assertEqual(sum(norm(busy) in l for l in watch_lines), 1)
        self.assertFalse(any(norm(claim) in l or norm(locked) in l for l in watch_lines))
        self.assertIn("OPEN-CODING-TASK vb-77777777", out)
        self.assertNotIn("OPEN-CODING-TASK vb-race-busy", out)
        self.assertIn("OUTBOUND vb-race: UNCLAIMED", out)
        self.assertNotIn("RELAY STATUS", out)
        self.assertIn("HUB STATUS", out)
        self.assertFalse({norm(claim), norm(locked)} & set(snap))
        self.assertFalse(any("vanished" in p for p in snap))
        self.assertEqual(ghost_head, [])
        # The skip lasts one pass only: once readable, the files count again.
        out = self.run_main("--track", "vb-race", "--no-save")
        self.assertIn("OPEN-CODING-TASK vb-race-busy", out)
        self.assertIn("OUTBOUND vb-race: ANSWERED", out)
        self.assertIn("RELAY STATUS", out)

    def test_a_seen_file_that_fails_stat_once_is_not_reported_again(self):
        # Dropping it from the saved state would print REMOVED, then NEW to the
        # monitor and to the next scan: three reports for one unchanged file.
        seen = write(self.bus / "relay/outbox/vb-seen-1.result.md", "vb-seen-1\n")
        self.run_main()
        real_stat = os.stat

        def flaky_stat(path, *args, **kwargs):
            if isinstance(path, (str, os.PathLike)) and norm(path) == norm(seen):
                raise PermissionError("simulated race", os.fspath(path))
            return real_stat(path, *args, **kwargs)

        with patch.object(self.w.os, "stat", flaky_stat):
            out = self.run_main()
        self.assertNotIn("REMOVED", out)
        self.assertIn(norm(seen), json.loads(self.state.read_text(encoding="utf-8"))["files"])
        self.assertNotIn(norm(seen), self.run_watch())
        self.assertNotIn(norm(seen), self.run_main())
        # A real change still shows on the next scan, and a real removal too.
        write(seen, "vb-seen-1\nrewritten\n")
        self.assertIn("CHANGED", [l.split()[1] for l in self.run_main().splitlines() if norm(seen) in l])
        seen.unlink()
        self.assertIn(f"REMOVED {norm(seen)}", self.run_main())

    def test_main_survives_a_cp949_or_ascii_console(self):
        # Emulates PYTHONIOENCODING=ascii/cp949 on a pipe in-process: this
        # suite forbids child processes, so the text streams are built the way
        # the interpreter builds them for such a console.
        heading = "# Task — Coding · em dash heading"
        write(self.bus / "relay/inbox/vb-emdash.md", heading + "\n")
        for encoding in ("ascii", "cp949"):
            with self.subTest(encoding=encoding):
                probe = io.TextIOWrapper(io.BytesIO(), encoding=encoding, errors="strict")
                with self.assertRaises(UnicodeEncodeError):
                    probe.write("—")
                raw_out, raw_err = io.BytesIO(), io.BytesIO()
                out = io.TextIOWrapper(raw_out, encoding=encoding, errors="strict")
                err = io.TextIOWrapper(raw_err, encoding=encoding, errors="strict")
                argv = ["bus_watch.py", "--state", str(self.state), "--no-save"]
                with patch.object(sys, "argv", argv), patch.object(sys, "stdout", out), \
                        patch.object(sys, "stderr", err):
                    self.w.main()
                    out.flush()
                    err.flush()
                text = raw_out.getvalue().decode("utf-8")
                self.assertIn("| " + heading, text)
                self.assertIn("OPEN-CODING-TASK vb-emdash", text)
                self.assertEqual(out.encoding, "utf-8")
                self.assertFalse(self.state.exists())


class LabelAndPathFlagTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.bus, self.drafts, self.hub = make_bus(self.base / "flag")
        self.state = self.base / "state" / "bus_watch.json"
        self.w = load_watcher(self.bus, self.drafts, self.hub, home=self.base / "home")

    def tearDown(self):
        self.tmp.cleanup()

    def scan(self, *args):
        return invoke(self.w, "--state", str(self.state), "--no-save", *args)[0]

    def test_self_label_decides_which_result_answers_a_task(self):
        nonce = "vb-label-1"
        write(self.bus / f"relay/inbox/{nonce}.md", "# Task — Coding · label check\n")
        write(self.bus / f"relay/outbox/{nonce}.result.md", f"{nonce}\n# Result\n- **Bot:** Codex (coding LLM)\n")
        line = f"OPEN-CODING-TASK {nonce}"
        self.assertIn(line, self.scan())
        self.assertNotIn(line, self.scan("--self-label", "Codex"))
        self.assertNotIn(line, self.scan("--agent", "codex"))
        self.assertIn(line, self.scan("--agent", "codex", "--self-label", "Claude Code"))

    def test_self_label_hides_only_this_sessions_own_tasks(self):
        write(self.bus / "relay/inbox/vb-from-codex.md", "# 과제\n작성 · 발행 Codex · 담당 봇: Coding LLM\n")
        write(self.bus / "relay/inbox/vb-from-claude.md", "# 과제\n작성 · 발행 Claude Code · 담당 봇: Coding LLM\n")
        claude, codex = self.scan(), self.scan("--agent", "codex")
        self.assertIn("OPEN-CODING-TASK vb-from-codex", claude)
        self.assertNotIn("OPEN-CODING-TASK vb-from-claude", claude)
        self.assertIn("OPEN-CODING-TASK vb-from-claude", codex)
        self.assertNotIn("OPEN-CODING-TASK vb-from-codex", codex)

    def test_coding_label_builds_the_task_address(self):
        self.assertEqual(self.w.coding_mark("Coding LLM").pattern, ORIGINAL_CODING_MARK)
        owner = write(self.bus / "relay/inbox/vb-addr-1.md", "# 과제\n담당 봇: Claude Code\n")
        write(self.bus / "relay/inbox/vb-addr-2.md", "# Task — Claude Code · heading form\n")
        default = self.scan()
        labelled = self.scan("--coding-label", "Claude Code")
        for nonce in ("vb-addr-1", "vb-addr-2"):
            self.assertNotIn(f"OPEN-CODING-TASK {nonce}", default)
            self.assertIn(f"OPEN-CODING-TASK {nonce}", labelled)
        watch = invoke(self.w, "--state", str(self.state), "--watch", "--once", "--coding-label", "Claude Code")[0]
        self.assertIn(f"CODING TASK: {norm(owner)}", watch)
        watch = invoke(self.w, "--state", str(self.state), "--watch", "--once")[0]
        self.assertIn(f"NEW bus file: {norm(owner)}", watch)

    def test_empty_labels_are_refused(self):
        for flag in ("--self-label", "--coding-label"):
            with self.subTest(flag=flag), self.assertRaises(SystemExit):
                invoke(self.w, "--state", str(self.state), "--no-save", flag, "  ")

    def test_path_flags_override_the_environment_and_follow_the_bus(self):
        env_bus, env_drafts, env_hub = make_bus(self.base / "env")
        other = load_watcher(env_bus, env_drafts, env_hub, home=self.base / "home")
        write(self.bus / "relay/inbox/vb-flag-1.md", "# Task — Coding · flag bus\n")
        write(self.drafts / "flag-note.md", "# draft note\n")
        write(self.hub, "hub from the flag\n")
        out = invoke(other, "--state", str(self.state), "--no-save", "--bus", str(self.bus),
                     "--drafts", str(self.drafts), "--hub-status", str(self.hub))[0]
        self.assertIn("OPEN-CODING-TASK vb-flag-1", out)
        self.assertIn("flag-note.md", out)
        self.assertIn("hub from the flag", out)
        self.assertEqual(other.RELAY_STATUS, str(self.bus) + "/relay/STATUS.md")
        self.assertEqual(other.WATCH[:2], [str(self.bus) + "/*/inbox/*", str(self.bus) + "/*/outbox/*"])
        self.assertEqual(other.WATCH[2:], [str(self.drafts) + "/*.md", str(self.hub), other.RELAY_STATUS])
        # Without the flags the environment values come back; nothing leaks between runs.
        out = invoke(other, "--state", str(self.state), "--no-save")[0]
        self.assertNotIn("vb-flag-1", out)
        self.assertEqual((other.BUS, other.DRAFTS, other.HUB_STATUS), (str(env_bus), str(env_drafts), str(env_hub)))

    def test_each_agent_has_its_own_default_state_and_state_flag_wins(self):
        home = self.base / "home"
        claude, codex = Path(self.w.DEFAULT_STATES["claude"]), Path(self.w.DEFAULT_STATES["codex"])
        self.assertEqual(claude, home / ".claude" / "state" / "vibe-bot" / "bus_watch.json")
        self.assertEqual(codex, home / ".codex" / "state" / "vibe-bot" / "bus_watch.json")
        self.assertEqual(Path(self.w.DEFAULT_STATE), claude)
        for path in (claude, codex):
            self.assertFalse(path.resolve().is_relative_to(BOT_ROOT.resolve()))
        invoke(self.w, "--agent", "codex", "--state", str(self.state))
        self.assertTrue(self.state.exists())
        self.assertFalse(codex.exists() or claude.exists())
        self.assertEqual(json.loads(self.state.read_text(encoding="utf-8"))["agent"], "codex")
        _, err = invoke(self.w, "--agent", "claude", "--state", str(self.state), "--no-save")
        self.assertIn("WARN state", err)


class PeerSessionTests(unittest.TestCase):
    """Claude Code and Codex watch one bus, each from its own saved state."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.bus, self.drafts, self.hub = make_bus(base)
        self.home = base / "home"
        self.home.mkdir()
        # One module per session, as two processes would load it.
        self.w = {a: load_watcher(self.bus, self.drafts, self.hub, home=self.home) for a in AGENT_LABELS}
        for agent, w in self.w.items():
            # Stop before any scan could write into the real home.
            self.assertTrue(Path(w.DEFAULT_STATES[agent]).is_relative_to(self.home))

    def tearDown(self):
        self.tmp.cleanup()

    def state_path(self, agent):
        return self.home / f".{agent}" / "state" / "vibe-bot" / "bus_watch.json"

    def scan(self, agent, *args):
        return invoke(self.w[agent], "--agent", agent, *args)[0]

    def watch_once(self, agent):
        return invoke(self.w[agent], "--agent", agent, "--watch", "--once")[0].splitlines()

    def arm(self, agent):
        """A running monitor: one state and one emitted set across ticks."""
        w = self.w[agent]
        w.configure(agent=agent)
        return {"w": w, "state": w.load_state(), "emitted": set(), "lines": []}

    @staticmethod
    def tick(monitor):
        lines = monitor["w"].watch_tick(monitor["state"], monitor["emitted"])
        monitor["lines"].extend(lines)
        return lines

    def roundtrip(self, sender, receiver):
        s_label, r_label = AGENT_LABELS[sender], AGENT_LABELS[receiver]
        n = [f"vb-{sender}-{receiver}-{i}" for i in range(1, 5)]

        def task(nonce):
            return write(self.bus / f"relay/inbox/{nonce}.md",
                         f"# 과제 {nonce}\n작성 · 발행 {s_label} · 담당 봇: Coding LLM\n")

        def result(nonce):
            return write(self.bus / f"relay/outbox/{nonce}.result.md",
                         f"{nonce}\n# Result\n- **Bot:** {r_label} (coding LLM)\n")

        def kinds(lines):
            return [line.split(" ", 1)[0] for line in lines]

        self.assertNotEqual(self.state_path(sender), self.state_path(receiver))
        # 0. Each session processes the bus once; the sender tracks its requests.
        self.scan(receiver)
        self.scan(sender, *[x for nonce in n for x in ("--track", nonce)])
        # 1. Two tasks land back to back after both scans, before any monitor is armed.
        t1, t2 = task(n[0]), task(n[1])
        # 2. Arming --watch --once reports each of them exactly once, to both sessions.
        r_arm, s_arm = self.watch_once(receiver), self.watch_once(sender)
        self.assertEqual(sorted(r_arm), sorted(f"CODING TASK: {norm(p)}" for p in (t1, t2)))
        self.assertEqual(len(s_arm), 2)
        for path in (t1, t2):
            self.assertEqual(sum(norm(path) in line for line in s_arm), 1)
        # 3. Wake: each session catches up with one processing scan, then re-arms.
        out = self.scan(receiver)
        self.assertIn(f"OPEN-CODING-TASK {n[0]}", out)
        self.assertIn(f"OPEN-CODING-TASK {n[1]}", out)
        out = self.scan(sender)
        self.assertNotIn("OPEN-CODING-TASK", out)
        self.assertIn(f"OUTBOUND {n[0]}: UNCLAIMED", out)
        rmon, smon = self.arm(receiver), self.arm(sender)
        self.assertEqual((self.tick(rmon), self.tick(smon)), ([], []))
        # 4. Two results and a third task, written back to back, reach both monitors.
        r1, r2, t3 = result(n[0]), result(n[1]), task(n[2])
        r_lines, s_lines = self.tick(rmon), self.tick(smon)
        # The sender's own task is a plain new file for it, never its coding work.
        self.assertEqual(kinds(s_lines), ["ANSWER", "ANSWER", "NEW"])
        self.assertEqual(set(s_lines), {f"ANSWER {n[0]}: {norm(r1)}", f"ANSWER {n[1]}: {norm(r2)}",
                                        f"NEW bus file: {norm(t3)}"})
        self.assertEqual(kinds(r_lines), ["CODING", "NEW", "NEW"])
        # 5. The receiver answers from its own scan; the sender's state is untouched.
        before = self.state_path(sender).read_bytes()
        out = self.scan(receiver)
        self.assertEqual(self.state_path(sender).read_bytes(), before)
        self.assertNotIn(f"OPEN-CODING-TASK {n[0]}", out)
        self.assertIn(f"OPEN-CODING-TASK {n[2]}", out)
        # 6. A result and a fourth task land; the receiver ticks and scans them
        #    before the sender's monitor looks. The sender must still see both.
        r3, t4 = result(n[2]), task(n[3])
        self.assertEqual(kinds(self.tick(rmon)), ["CODING", "NEW"])
        self.assertIn(f"OPEN-CODING-TASK {n[3]}", self.scan(receiver))
        shared = json.loads(self.state_path(receiver).read_text(encoding="utf-8"))
        shared["outbound"] = dict(smon["state"]["outbound"])
        lost = self.w[sender].watch_events(shared, self.w[sender].snapshot(), set())
        self.assertNotIn(f"ANSWER {n[2]}: {norm(r3)}", lost)  # a shared baseline would lose it
        self.assertEqual(set(self.tick(smon)), {f"ANSWER {n[2]}: {norm(r3)}", f"NEW bus file: {norm(t4)}"})
        # 7. The sender's scan closes its requests and leaves the receiver's state alone.
        before = self.state_path(receiver).read_bytes()
        out = self.scan(sender)
        self.assertEqual(self.state_path(receiver).read_bytes(), before)
        for nonce in n[:3]:
            self.assertIn(f"OUTBOUND {nonce}: ANSWERED", out)
        self.assertIn(f"OUTBOUND {n[3]}: UNCLAIMED", out)
        # 8. Quiet ticks repeat nothing; every file reached each monitor exactly once.
        self.assertEqual((self.tick(rmon), self.tick(smon)), ([], []))
        expected = {norm(p) for p in (r1, r2, t3, r3, t4)}
        for monitor in (rmon, smon):
            seen = collections.Counter(line.rsplit(": ", 1)[1] for line in monitor["lines"])
            self.assertEqual(set(seen), expected)
            self.assertEqual(set(seen.values()), {1})
        s_state = json.loads(self.state_path(sender).read_text(encoding="utf-8"))
        r_state = json.loads(self.state_path(receiver).read_text(encoding="utf-8"))
        self.assertEqual((s_state["agent"], r_state["agent"]), (sender, receiver))
        self.assertEqual(set(s_state["outbound"]), {n[3]})
        self.assertEqual(r_state["outbound"], {})

    def test_codex_sender_to_claude_receiver_is_lossless(self):
        self.roundtrip("codex", "claude")

    def test_claude_sender_to_codex_receiver_is_lossless(self):
        self.roundtrip("claude", "codex")


if __name__ == "__main__":
    unittest.main(verbosity=2)
