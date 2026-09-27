"""The candidate probe must execute tests only on a disposable copy."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/candidate_runtime_probe.py"
sys.path.insert(0, str(ROOT / "scripts"))


@unittest.skipUnless(sys.platform == "win32", "Pinned package I/O is Windows-only")
class CandidateRuntimeProbeTests(unittest.TestCase):
    def test_probe_leaves_verified_source_unchanged_when_step_writes(self):
        self.assertTrue(HELPER.is_file(), "Candidate runtime probe is not implemented")
        spec = importlib.util.spec_from_file_location("candidate_runtime_probe", HELPER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix="candidate-probe-test-") as temp:
            source = Path(temp) / "source"
            source.mkdir()
            (source / "bundle.json").write_bytes(b"{}")
            (source / "fixture.txt").write_bytes(b"original")
            receipt = {"files": [{"path": "fixture.txt", "size": 8,
                                  "sha256": module.r.digest(b"original"), "mode": "100644"}]}
            calls = []

            def verify(candidate, digest):
                calls.append(Path(candidate))
                self.assertEqual(digest, "a" * 64)
                self.assertEqual((Path(candidate) / "fixture.txt").read_bytes(), b"original")
                self.assertEqual((Path(candidate) / "bundle.json").read_bytes(), b"{}")
                self.assertFalse((Path(candidate) / "probe-marker").exists())
                return receipt

            step = ("write-marker", (sys.executable, "-B", "-c",
                                     "import os; from pathlib import Path; "
                                     "assert 'simonk-candidate-probe-' in str(Path.home()); "
                                     "assert 'OPENAI_API_KEY' not in os.environ; "
                                     "assert 'ANTHROPIC_API_KEY' not in os.environ; "
                                     "Path('probe-marker').write_text('scratch')"), ".")
            with patch.dict("os.environ", {"OPENAI_API_KEY": "fixture", "ANTHROPIC_API_KEY": "fixture"}):
                with patch.object(module.plugin_bundle, "verify_bundle", side_effect=verify):
                    result = module.probe(source, "a" * 64, steps=(step,))
            self.assertEqual(result["status"], "candidate_runtime_probe_passed")
            self.assertFalse(result["runtime_closure_verified"])
            self.assertEqual(len(calls), 3)
            self.assertEqual(calls[0], source)
            self.assertNotEqual(calls[1], source)
            self.assertEqual(calls[2], source)
            self.assertFalse((source / "probe-marker").exists())


if __name__ == "__main__":
    unittest.main()
