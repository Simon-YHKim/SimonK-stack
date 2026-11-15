"""D-129 local GUI tool observation: temporary files only, no browser or npx runs."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import collect_gui_tools as m  # noqa: E402
import orchestrate  # noqa: E402

NOW = "2026-11-16T03:00:00+00:00"


class CollectGuiToolsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="vibe-gui-tools-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.config = self.root / "playwright-mcp.config.json"
        self.config.write_text(json.dumps({"browser": {"isolated": True, "launchOptions": {"headless": True}}}),
                               encoding="utf-8")
        self.claude_json = self.root / "claude.json"
        self.write_entry(["-y", "@playwright/mcp@latest", "--config", str(self.config)])
        self.browsers = self.root / "ms-playwright"
        (self.browsers / "chromium-1234").mkdir(parents=True)
        self.paths = {"claude_json": self.claude_json, "browsers": self.browsers,
                      "guard": self.root / "guard.js"}

    def write_entry(self, args, extra=None):
        data = {"oauthAccount": {"emailAddress": "never-read@example.invalid"},
                "mcpServers": {"playwright": {"type": "stdio", "command": "npx", "args": args}}}
        data.update(extra or {})
        self.claude_json.write_text(json.dumps(data), encoding="utf-8")

    def playwright(self, **kwargs):
        result = m.observe("fixture-host", now=NOW, paths=self.paths, **kwargs)
        return result, result["gui_tools"][0]

    def test_observes_headless_isolated_config_and_reports_the_missing_guard(self):
        result, tool = self.playwright()
        self.assertEqual((tool["transport"], tool["available"], tool["headless"], tool["isolated"]),
                         ("playwright", True, True, True))
        self.assertFalse(tool["pointer_lock_guard"])
        self.assertFalse(tool["version_pinned"])
        self.assertTrue(any("unpinned" in note for note in result["notes"]))
        self.assertNotIn("never-read", json.dumps(result))  # Only mcpServers.playwright is read.
        # The planner rejects it until the guard is in place.
        runtime = {"host_ref": "fixture-host"}
        reasons = orchestrate.assess_gui_tool(tool, {"kind": "gui"}, runtime, NOW)
        self.assertEqual(reasons, ["GUI_POINTER_LOCK_UNGUARDED"])

    def test_install_adds_the_guard_once_with_a_backup_and_skips_present_chromium(self):
        runs = []
        changes = m.install(self.paths, run=lambda argv: runs.append(argv) or 0, stamp="20261116")
        self.assertEqual(runs, [])  # Chromium is already there.
        self.assertTrue(any("backed up" in c for c in changes))
        self.assertTrue((self.root / "playwright-mcp.config.json.bak-20261116").exists())
        config = json.loads(self.config.read_text(encoding="utf-8"))
        self.assertEqual(config["browser"]["initScript"], [str(self.paths["guard"])])
        self.assertTrue(config["browser"]["isolated"])
        self.assertIn(m.GUARD_MARKER, self.paths["guard"].read_text(encoding="utf-8"))
        _, tool = self.playwright()
        self.assertTrue(tool["pointer_lock_guard"])
        self.assertEqual(orchestrate.assess_gui_tool(tool, {"kind": "gui"}, {"host_ref": "fixture-host"}, NOW), [])
        self.assertEqual(m.install(self.paths, run=lambda argv: runs.append(argv) or 0), [])  # Idempotent.

    def test_missing_chromium_runs_the_playwright_cli_and_must_produce_a_browser(self):
        (self.browsers / "chromium-1234").rmdir()
        _, tool = self.playwright()
        self.assertFalse(tool["available"])

        def installer(argv):
            self.assertEqual(argv[1:], ["-y", "playwright", "install", "chromium"])
            (self.browsers / "chromium-1300").mkdir()
            return 0

        m.install(self.paths, run=installer, stamp="1")
        self.assertTrue(self.playwright()[1]["available"])
        (self.browsers / "chromium-1300").rmdir()
        with self.assertRaises(m.GuiToolError) as raised:
            m.install(self.paths, run=lambda argv: 0, stamp="2")
        self.assertEqual(raised.exception.code, "CHROMIUM_INSTALL_FAILED")

    def test_flags_count_and_unregistered_or_flag_only_setups_are_not_changed(self):
        self.write_entry(["@playwright/mcp@0.0.70", "--headless", "--isolated",
                          "--init-script", str(self.paths["guard"])])
        self.paths["guard"].write_text(m.GUARD_SCRIPT, encoding="utf-8")
        _, tool = self.playwright()
        self.assertTrue(tool["headless"] and tool["isolated"] and tool["pointer_lock_guard"] and tool["version_pinned"])
        self.write_entry(["@playwright/mcp@latest", "--headless"])
        with self.assertRaises(m.GuiToolError) as raised:
            m.install(self.paths, run=lambda argv: 0)
        self.assertEqual(raised.exception.code, "PLAYWRIGHT_CONFIG_NOT_USED")
        self.claude_json.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
        result, tool = self.playwright()
        self.assertFalse(tool["available"])
        self.assertTrue(any("not registered" in note for note in result["notes"]))
        with self.assertRaises(m.GuiToolError) as raised:
            m.install(self.paths)
        self.assertEqual(raised.exception.code, "PLAYWRIGHT_MCP_NOT_REGISTERED")

    def test_session_tools_are_host_attested_and_need_simon_present(self):
        result = m.observe("fixture-host", chrome=True, computer_use=True, now=NOW, paths=self.paths)
        chrome = next(t for t in result["gui_tools"] if t["transport"] == "claude-in-chrome")
        self.assertFalse(chrome["interactive"])
        self.assertIn("GUI_REQUIRES_INTERACTIVE_HOST",
                      orchestrate.assess_gui_tool(chrome, {"kind": "gui"}, {"host_ref": "fixture-host"}, NOW))
        result = m.observe("fixture-host", interactive=True, chrome=True, now=NOW, paths=self.paths)
        chrome = next(t for t in result["gui_tools"] if t["transport"] == "claude-in-chrome")
        self.assertEqual(orchestrate.assess_gui_tool(chrome, {"kind": "gui"}, {"host_ref": "fixture-host"}, NOW), [])
        self.assertEqual([t["transport"] for t in result["gui_tools"]], ["playwright", "claude-in-chrome"])
        with self.assertRaises(m.GuiToolError):
            m.observe(" ", paths=self.paths)


if __name__ == "__main__":
    unittest.main()
