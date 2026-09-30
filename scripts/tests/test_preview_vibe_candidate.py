"""A candidate preview must fail closed before any subscription model session."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "scripts" / "preview-vibe-candidate.ps1"
PWSH = shutil.which("pwsh")
ALTERNATE_AUTH_VARS = {
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY", "CLAUDE_CODE_OAUTH_TOKEN",
}


@unittest.skipUnless(PWSH, "PowerShell 7 is required")
class PreviewVibeCandidateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="vibe-preview-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.candidate = self.root / "missing-candidate"

    def run_preview(self, *extra, candidate=None, digest="0" * 64, env_overrides=None):
        env = {key: value for key, value in os.environ.items()
               if key not in ALTERNATE_AUTH_VARS}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env.update(env_overrides or {})
        return subprocess.run(
            [PWSH, "-NoProfile", "-NonInteractive", "-File", str(LAUNCHER),
             "-CandidateRoot", str(candidate or self.candidate),
             "-ExpectedDigest", digest, *extra],
            cwd=self.root, env=env, capture_output=True, text=True,
            encoding="utf-8", timeout=45,
        )

    def test_invalid_digest_blocks_before_any_host_or_verifier_call(self):
        result = self.run_preview("-Run", "-SubscriptionOnlyConfirmed", digest="bad")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("DIGEST_INVALID", result.stderr)
        self.assertFalse(self.candidate.exists())

    def test_missing_candidate_blocks_check_only(self):
        result = self.run_preview()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("CANDIDATE_MISSING", result.stderr)
        self.assertFalse(self.candidate.exists())

    def test_unapproved_model_blocks_before_any_host_or_verifier_call(self):
        result = self.run_preview("-Model", "sonnet", "-Run", "-SubscriptionOnlyConfirmed")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("MODEL_NOT_ALLOWLISTED", result.stderr)
        self.assertFalse(self.candidate.exists())

    def test_run_requires_explicit_subscription_confirmation(self):
        result = self.run_preview("-Run")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("SUBSCRIPTION_CONFIRMATION_REQUIRED", result.stderr)
        self.assertFalse(self.candidate.exists())

    @unittest.skipUnless(os.environ.get("VIBE_PREVIEW_CANDIDATE") and
                         os.environ.get("VIBE_PREVIEW_DIGEST"),
                         "Set isolated immutable candidate and digest for check-only integration")
    def test_immutable_candidate_check_only_does_not_launch_model(self):
        candidate = Path(os.environ["VIBE_PREVIEW_CANDIDATE"])
        digest = os.environ["VIBE_PREVIEW_DIGEST"]
        result = self.run_preview(candidate=candidate, digest=digest)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "candidate_verified")
        self.assertEqual(payload["bundle_digest"], digest)
        self.assertFalse(payload["model_called"])
        self.assertEqual(payload["model"], "claude-sonnet-5")

    @unittest.skipUnless(os.environ.get("VIBE_PREVIEW_CANDIDATE") and
                         os.environ.get("VIBE_PREVIEW_DIGEST"),
                         "Set isolated immutable candidate and digest for security integration")
    def test_api_key_route_blocks_before_model_call(self):
        result = self.run_preview(
            "-Run", "-SubscriptionOnlyConfirmed",
            candidate=Path(os.environ["VIBE_PREVIEW_CANDIDATE"]),
            digest=os.environ["VIBE_PREVIEW_DIGEST"],
            env_overrides={"ANTHROPIC_API_KEY": "test-only-sentinel"},
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("NON_SUBSCRIPTION_CREDENTIAL_PRESENT", result.stderr)

    @unittest.skipUnless(os.name == "nt" and os.environ.get("VIBE_PREVIEW_CANDIDATE") and
                         os.environ.get("VIBE_PREVIEW_DIGEST"),
                         "Windows immutable candidate is required for fake-host integration")
    def test_all_plugins_uses_only_preapproved_skill_without_plan_mode(self):
        fake_bin = self.root / "bin"
        fake_bin.mkdir()
        fake_claude = fake_bin / "claude.cmd"
        fake_claude.write_text(
            "@echo off\n"
            "if \"%1\"==\"auth\" (\n"
            "  echo {\"loggedIn\":true,\"authMethod\":\"claude.ai\","
            "\"apiProvider\":\"firstParty\",\"subscriptionType\":\"max\"}\n"
            "  exit /b 0\n"
            ")\n"
            "echo %* > \"%VIBE_TEST_ARGV%\"\n"
            "echo %ENABLE_CLAUDEAI_MCP_SERVERS% > \"%VIBE_TEST_MCP%\"\n"
            "cd > \"%VIBE_TEST_CWD%\"\n"
            "exit /b 0\n", encoding="ascii",
        )
        argv_file = self.root / "argv.txt"
        mcp_file = self.root / "mcp.txt"
        cwd_file = self.root / "cwd.txt"
        result = self.run_preview(
            "-Run", "-SubscriptionOnlyConfirmed", "-AllPlugins",
            "-Model", "claude-sonnet-5-5",
            candidate=Path(os.environ["VIBE_PREVIEW_CANDIDATE"]),
            digest=os.environ["VIBE_PREVIEW_DIGEST"],
            env_overrides={
                "PATH": str(fake_bin) + os.pathsep + os.environ["PATH"],
                "VIBE_TEST_ARGV": str(argv_file),
                "VIBE_TEST_MCP": str(mcp_file),
                "VIBE_TEST_CWD": str(cwd_file),
            },
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        argv = argv_file.read_text(encoding="utf-8")
        self.assertEqual(argv.count("--plugin-dir"), 5)
        for name in ("SimonKCore", "SimonKDesign", "SimonKStack", "SimonKMarket", "SimonKAIHub"):
            self.assertIn(name, argv)
        self.assertIn("--permission-mode dontAsk", argv)
        self.assertIn("--model claude-sonnet-5-5", argv)
        self.assertIn("--allowedTools Skill", argv)
        self.assertIn("--tools Skill", argv)
        self.assertIn("--disallowedTools mcp__*", argv)
        self.assertIn("--permission-prompts none", argv)
        self.assertNotIn("--permission-mode plan", argv)
        self.assertEqual(mcp_file.read_text(encoding="utf-8").strip(), "false")
        self.assertIn("simonk-vibe-preview-", cwd_file.read_text(encoding="utf-8"))
        self.assertNotIn(str(ROOT), cwd_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
