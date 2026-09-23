"""Offline benchmark collection regressions; all I/O is inside a temp directory."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "fetch-model-benchmarks.py"


class BenchmarkCollectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.wiki = self.root / "wiki" / "concepts" / "ai-model-benchmarks.md"
        self.wiki.parent.mkdir(parents=True)
        self.wiki.write_text("---\nlast-updated: 2020-01-01\n---\nHistorical rows.\n", encoding="utf-8")
        self.log = self.root / "wiki" / "log.md"
        self.log.write_text("Existing history.\n", encoding="utf-8")
        self.cache = self.root / "cache" / "benchmarks-cache.json"
        self.original_wiki = self.wiki.read_bytes()
        self.original_log = self.log.read_bytes()
        with mock.patch.dict("os.environ", {"SIMON_WIKI_DIR": str(self.root)}):
            spec = importlib.util.spec_from_file_location("benchmark_fetcher_fixture", SCRIPT)
            self.m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.m)
        self.m.CACHE_DIR, self.m.CACHE_FILE = str(self.cache.parent), str(self.cache)
        self.good_rows = [{"name": "Fixture Model", "arena_score": 1234, "category": "fixture"}]

    def seed_cache(self):
        self.cache.parent.mkdir()
        self.cache.write_bytes(b'{"previous": {"models": ["preserve old cache"]}}\n')
        return self.cache.read_bytes()

    def invoke(self, args=(), rows=None, network_failure=False):
        rows = self.good_rows if rows is None else rows
        def response(url, **kwargs):
            if network_failure:
                return None
            return json.dumps({"models": rows}) if url.endswith("/api/leaderboard") else "<html>fixture</html>"
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(self.m, "fetch", side_effect=response), \
                mock.patch.object(self.m.time, "sleep"), \
                mock.patch("sys.argv", [str(SCRIPT), "--source", "lmarena", *args]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = self.m.main()
        self.assertEqual(self.wiki.read_bytes(), self.original_wiki, "No data merge means no Wiki edit")
        self.assertEqual(self.log.read_bytes(), self.original_log, "No invented Wiki log entry")
        return rc, out.getvalue() + err.getvalue()

    def test_success_is_raw_collection_only_and_never_refreshes_wiki(self):
        rc, output = self.invoke()
        self.assertEqual(rc, 0)
        data = json.loads(self.cache.read_text(encoding="utf-8"))
        item = data["lmarena"]
        self.assertEqual(item["models"][0]["name"], "Fixture Model")
        self.assertEqual(item["validation_status"], "unverified")
        self.assertIsNone(item["data_as_of"])
        self.assertFalse(item["wiki_updated"])
        self.assertIsNotNone(datetime.fromisoformat(item["attempted_at"]).tzinfo)
        self.assertNotIn("fetched_at", item)
        self.assertIn("Wiki unchanged", output)
        self.assertIn("unverified", output)

    def test_zero_rows_returns_failure_and_preserves_existing_cache(self):
        before = self.seed_cache()
        rc, _ = self.invoke(rows=[])
        self.assertEqual(rc, 2)
        self.assertEqual(self.cache.read_bytes(), before)

    def test_network_failure_does_not_create_cache_or_claim_success(self):
        rc, _ = self.invoke(network_failure=True)
        self.assertEqual(rc, 2)
        self.assertFalse(self.cache.parent.exists())

    def test_unimplemented_parser_is_not_success(self):
        rc, _ = self.invoke(args=("--source", "vellum"))
        self.assertEqual(rc, 2)
        self.assertFalse(self.cache.exists())

    def test_partial_collection_is_incomplete_and_preserves_prior_snapshot(self):
        before = self.seed_cache()
        rc, output = self.invoke(args=("--source", "all"))
        self.assertEqual(rc, 2)
        self.assertEqual(self.cache.read_bytes(), before)
        self.assertIn("incomplete", output)

    def test_dry_run_is_read_only_even_with_successful_collection(self):
        rc, output = self.invoke(args=("--dry-run",))
        self.assertEqual(rc, 0)
        self.assertFalse(self.cache.parent.exists())
        self.assertIn("not written", output)

    def test_dry_run_does_not_replace_an_existing_cache(self):
        before = self.seed_cache()
        rc, _ = self.invoke(args=("--dry-run",))
        self.assertEqual(rc, 0)
        self.assertEqual(self.cache.read_bytes(), before)

    def test_invalid_source_is_rejected_before_network_or_filesystem_writes(self):
        with mock.patch.object(self.m, "fetch") as fetch, \
                mock.patch("sys.argv", [str(SCRIPT), "--source", "unknown"]), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            self.m.main()
        self.assertEqual(error.exception.code, 2)
        fetch.assert_not_called()
        self.assertFalse(self.cache.parent.exists())
        self.assertEqual(self.wiki.read_bytes(), self.original_wiki)

    def test_malformed_model_rows_cannot_make_collection_successful(self):
        invalid = [None, "string-row", {}, {"name": "", "arena_score": 1200},
                   {"name": "Fixture", "arena_score": None}, {"name": "Fixture", "arena_score": True},
                   {"name": "Fixture", "arena_score": float("nan")},
                   {"name": "Fixture", "arena_score": float("inf")},
                   {"name": "Fixture", "arena_score": -1}]
        for row in invalid:
            with self.subTest(row=row):
                rc, _ = self.invoke(rows=[row])
                self.assertEqual(rc, 2)
                self.assertFalse(self.cache.exists())

    def test_mixed_valid_invalid_rows_do_not_replace_a_complete_cache(self):
        before = self.seed_cache()
        rc, _ = self.invoke(rows=[self.good_rows[0], {"name": None, "arena_score": 1234}])
        self.assertEqual(rc, 2)
        self.assertEqual(self.cache.read_bytes(), before)

    def test_malformed_models_container_is_not_success(self):
        for rows in (None, "text", {"name": "not-a-list"}):
            with self.subTest(rows=rows), mock.patch.object(self.m, "fetch", return_value=json.dumps({"models": rows})), \
                    mock.patch.object(self.m.time, "sleep"), \
                    mock.patch("sys.argv", [str(SCRIPT), "--source", "lmarena"]), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(self.m.main(), 2)
        self.assertFalse(self.cache.exists())
        self.assertEqual(self.wiki.read_bytes(), self.original_wiki)

    def test_parser_exception_is_incomplete_not_a_fresh_cache(self):
        before = self.seed_cache()
        with mock.patch.dict(self.m.PARSERS, {"lmarena": mock.Mock(side_effect=ValueError("fixture parse failure"))}):
            rc, output = self.invoke()
        self.assertEqual(rc, 2)
        self.assertEqual(self.cache.read_bytes(), before)
        self.assertIn("parser", output.lower())

    def test_cache_replace_failure_preserves_previous_bytes(self):
        before = self.seed_cache()
        with mock.patch.object(self.m.os, "replace", side_effect=OSError("fixture replacement failure")):
            rc, _ = self.invoke()
        self.assertEqual(rc, 2)
        self.assertEqual(self.cache.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.cache.parent.iterdir()), [self.cache.name])

    def test_cache_serialization_failure_does_not_truncate_existing_data(self):
        before = self.seed_cache()
        with self.assertRaises((TypeError, ValueError)):
            self.m.save_cache({"source": {"models": [], "unsupported": object()}})
        self.assertEqual(self.cache.read_bytes(), before)

    def test_sync_failure_preserves_cache_and_removes_only_owned_temp(self):
        before = self.seed_cache()
        unrelated = self.cache.parent / 'unrelated.tmp'
        unrelated.write_bytes(b'not ours')
        with mock.patch.object(self.m.os, 'fsync', side_effect=OSError('fixture sync failure')):
            rc, _ = self.invoke()
        self.assertEqual(rc, 2)
        self.assertEqual(self.cache.read_bytes(), before)
        self.assertEqual(unrelated.read_bytes(), b'not ours')
        self.assertEqual(sorted(p.name for p in self.cache.parent.iterdir()),
                         sorted([self.cache.name, unrelated.name]))

    def test_directory_failure_preserves_previous_cache(self):
        before = self.seed_cache()
        with mock.patch.object(self.m.os, 'makedirs', side_effect=OSError('fixture directory failure')):
            rc, _ = self.invoke()
        self.assertEqual(rc, 2)
        self.assertEqual(self.cache.read_bytes(), before)

    def test_dry_run_partial_failure_preserves_existing_files(self):
        before = self.seed_cache()
        rc, _ = self.invoke(args=('--source', 'all', '--dry-run'))
        self.assertEqual(rc, 2)
        self.assertEqual(self.cache.read_bytes(), before)

    def test_zero_is_not_confused_with_a_missing_score(self):
        rc, _ = self.invoke(rows=[{'name': 'Fixture zero', 'arena_score': 0}])
        self.assertEqual(rc, 0)
        data = json.loads(self.cache.read_text(encoding='utf-8'))
        self.assertEqual(data['lmarena']['models'][0]['arena_elo'], 0)

    def test_percentage_metric_bounds_and_unimplemented_source_are_explicit(self):
        for score, expected in [(0, True), (100, True), (100.1, False), (-1, False), (True, False)]:
            with self.subTest(score=score):
                self.assertEqual(self.m.usable_row('swebench',
                                 {'name': 'Fixture', 'swe_bench_verified_pct': score}), expected)
        self.assertFalse(self.m.usable_row('vellum', {'name': 'Fixture', 'arena_elo': 1234}))


if __name__ == "__main__":
    unittest.main()
