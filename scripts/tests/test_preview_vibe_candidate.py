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


@unittest.skipUnless(PWSH, "PowerShell 7 is required")
class PreviewVibeCandidateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="vibe-preview-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.candidate = self.root / "missing-candidate"

    def run_preview(self, *extra, candidate=None, digest="0" * 64, env_overrides=None):
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
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


if __name__ == "__main__":
    unittest.main()
