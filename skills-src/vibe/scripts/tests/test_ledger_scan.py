"""Secret-scanner equivalence and latency; synthetic data, no process/network I/O."""
import itertools
import json
import random
import re
import sys
import time
import unittest
from pathlib import Path


def deny_external(event, args):
    if event.startswith(("subprocess.", "os.system", "os.exec", "os.spawn",
                         "os.posix_spawn", "socket.connect", "socket.__new__")):
        raise RuntimeError("PROCESS_OR_NETWORK_FORBIDDEN")


sys.addaudithook(deny_external)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ledger
import run_state

URI = re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s:/@]+:[^\s:/@]+@")
JWT = re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.")


class LedgerScanTests(unittest.TestCase):
    def assert_offset(self, text, name, old):
        match = old.search(text)  # Bounded short inputs only; never the large cases.
        expected = [] if match is None else [(name, match.start())]
        self.assertEqual([hit for hit in ledger.scan_secrets(text) if hit[0] == name], expected)

    def test_plain_word_latency(self):
        start = time.perf_counter()
        self.assertEqual(ledger.scan_secrets("z" * 32768), [])
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.25, f"32KiB plain scan took {elapsed:.3f}s")

    def test_incomplete_jwt_latency(self):
        start = time.perf_counter()
        self.assertEqual(ledger.scan_secrets("eyJ" * 10923), [])
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.25, f"32KiB incomplete JWT scan took {elapsed:.3f}s")

    def test_uri_offsets_match_legacy(self):
        for prefix in ("", "123+.-", "_", "한", "\x00", "a", "9", "0://", "\n", "𝄞"):
            for scheme in ("a", "ab", "http", "git+ssh", "0ab", "--", ".", "A0-."):
                for authority in ("u:p@", "u:@", ":p@", "u:p", "u:p@@", "u:/p@",
                                  "u:p/", "u:한@", "u:\u00a0p@", "u:pa\\ss@"):
                    with self.subTest(prefix=prefix, scheme=scheme, authority=authority):
                        self.assert_offset(prefix + scheme + "://" + authority,
                                           "connection uri with password", URI)

    def test_uri_first_match_and_embedded_suffix(self):
        for chars in itertools.product("a0+._:/@ ", repeat=3):
            text = "".join(chars) + "1a://u:p@ " + "z://v:q@"
            self.assert_offset(text, "connection uri with password", URI)

    def test_jwt_offsets_match_legacy(self):
        for prefix in ("", "z", "eyJ", "eyJeyJ", "한", "a.", "\x00", "eyJ" + "a" * 10 + "."):
            for length in (0, 9, 10, 11, 30):
                for body in ("", "b" * 9, "b" * 10, "_" * 10, "한" * 10):
                    for ending in ("", ".", ".tail", "..", "\n."):
                        text = prefix + "eyJ" + "a" * length + "." + body + ending
                        self.assert_offset(text, "jwt", JWT)

    def test_random_short_equivalence(self):
        rng = random.Random(260924)
        atoms = ("eyJ", "a" * 10, "_" * 10, ".", " ", "http://", "u:p@", "1+",
                 "-", "\x00", "한", "\n", "@", "/", ":", "eyJeyJ", "z")
        for _ in range(2000):
            text = "".join(rng.choices(atoms, k=rng.randrange(1, 14)))
            self.assert_offset(text, "jwt", JWT)
            self.assert_offset(text, "connection uri with password", URI)

    def test_hit_order_and_redaction_are_unchanged(self):
        text = "x://u:p@ " + "eyJ" + "a" * 10 + "." + "b" * 10 + ". " + "sk-" + "c" * 20
        expected = []
        for regex, name in ledger.SECRET_PATTERNS:
            old = {"jwt": JWT, "connection uri with password": URI}.get(name, regex)
            match = old.search(text)
            if match:
                expected.append((name, match.start()))
        self.assertEqual(ledger.scan_secrets(text), expected)
        self.assertTrue(all(isinstance(offset, int) for _, offset in expected))

    def test_megabyte_payload_is_checked_without_truncation(self):
        limit = 1024 * 1024
        plain = "z" * (limit - len('{"note":""}'))
        start = time.perf_counter()
        encoded = run_state.safe_json({"note": plain})
        self.assertEqual(len(encoded.encode("utf-8")), limit)
        self.assertEqual(json.loads(encoded)["note"], plain)
        for ending in (" x://u:p@", " eyJ" + "a" * 10 + "." + "b" * 10 + "."):
            with self.assertRaisesRegex(run_state.StateError, "^SENSITIVE_PAYLOAD$"):
                run_state.safe_json({"note": plain[:-len(ending)] + ending})
        with self.assertRaisesRegex(run_state.StateError, "^PAYLOAD_TOO_LARGE$"):
            run_state.safe_json({"note": plain + "z"})
        self.assertLess(time.perf_counter() - start, 5.0)

    def test_long_malformed_segments_and_near_end_match(self):
        start = time.perf_counter()
        for text in ("eyJ" * 100000, "0+." * 100000, "eyJ" * 100000 + "." + "b" * 9 + "."):
            self.assertEqual(ledger.scan_secrets(text), [])
        text = "eyJ" * 100000 + " . eyJ" + "a" * 10 + "." + "b" * 10 + "."
        self.assertEqual([hit for hit in ledger.scan_secrets(text) if hit[0] == "jwt"],
                         [("jwt", 300003)])
        self.assertLess(time.perf_counter() - start, 5.0)


if __name__ == "__main__":
    unittest.main()
