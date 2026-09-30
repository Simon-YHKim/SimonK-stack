"""Offline tests for the read-only model-release watch state machine."""

import copy
import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import model_watch


UTC = timezone.utc
FRIDAY = datetime(2026, 10, 2, 0, 0, tzinfo=UTC)


class ModelWatchTests(unittest.TestCase):
    def setUp(self):
        self.pages = {
            provider: '<html><a href="/news/old">Unrelated announcement</a></html>'
            for provider in model_watch.SOURCES
        }
        self.pages["openai"] = "<rss><channel><item><title>Unrelated announcement</title></item></channel></rss>"

    def fetch(self, provider, _url):
        return self.pages[provider]

    def test_friday_initial_scan_is_baseline_not_release(self):
        state, report = model_watch.scan_state({}, self.fetch, FRIDAY)
        self.assertEqual(report["status"], "scanned")
        self.assertEqual(state["candidates"], {})
        self.assertEqual(len(state["sources"]), len(model_watch.SOURCES))

    def test_new_official_model_link_is_unreviewed_not_ga(self):
        state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)
        self.pages["anthropic"] = (
            '<html><a href="/news/old">Unrelated announcement</a>'
            '<a href="/news/claude-haiku-5-5">Claude Haiku 5.5 coming soon</a></html>'
        )
        updated, report = model_watch.scan_state(state, self.fetch, FRIDAY + timedelta(days=7))
        self.assertEqual(len(report["new_candidates"]), 1)
        self.assertEqual(report["candidate_details"][report["new_candidates"][0]]["title"],
                         "Claude Haiku 5.5 coming soon")
        candidate = next(iter(updated["candidates"].values()))
        self.assertEqual(candidate["status"], "official_unreviewed")
        self.assertNotIn("released_at", candidate)
        self.assertFalse(candidate["routing_ready"])

    def test_legacy_default_port_source_link_is_not_new_candidate(self):
        self.pages["xai"] += '<a href="/news/grok-4-8">Grok 4.8</a>'
        state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)
        state["sources"]["xai"]["links"] = ["https://x.ai:443/news/grok-4-8"]
        state, report = model_watch.scan_state(state, self.fetch, FRIDAY + timedelta(days=7))
        self.assertEqual(report["new_candidates"], [])
        self.assertEqual(state["sources"]["xai"]["links"],
                         ["https://x.ai/news/grok-4-8"])

    def test_changed_page_without_model_link_is_reported_not_promoted(self):
        state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)
        self.pages["openai"] = self.pages["openai"].replace(
            "</channel>", "<item><title>Unrelated product update</title></item></channel>")
        updated, report = model_watch.scan_state(state, self.fetch, FRIDAY + timedelta(days=7))
        self.assertIn("openai", report["changed_sources"])
        self.assertEqual(updated["candidates"], {})

    def test_new_model_heading_without_article_link_is_unreviewed(self):
        state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)
        self.pages["google"] += "<h2>Gemini 4 Pro and Gemini 4 Flash</h2>"
        updated, report = model_watch.scan_state(state, self.fetch, FRIDAY + timedelta(days=7))
        self.assertEqual(len(report["new_candidates"]), 1)
        candidate = updated["candidates"][report["new_candidates"][0]]
        self.assertEqual(candidate["status"], "official_unreviewed")
        self.assertEqual(candidate["official_url"], model_watch.SOURCES["google"])
        model_watch.confirm_release(updated, report["new_candidates"][0],
                                    FRIDAY + timedelta(days=7, minutes=1),
                                    model_watch.SOURCES["google"])
        self.assertEqual(candidate["status"], "released")

    def test_non_friday_without_pending_does_not_fetch(self):
        state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)
        state["last_report"] = {"checked_at": model_watch.iso(FRIDAY), "errors": {}}

        def forbidden(*_args):
            raise AssertionError("network should not be used")

        updated, report = model_watch.scan_state(state, forbidden, FRIDAY + timedelta(days=1))
        self.assertEqual(report["status"], "not_due")
        self.assertEqual(updated, state)

    def test_missed_friday_is_checked_on_next_available_day(self):
        state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)
        state["last_report"] = {"checked_at": model_watch.iso(FRIDAY), "errors": {}}
        later, report = model_watch.scan_state(state, self.fetch, FRIDAY + timedelta(days=8))
        self.assertEqual(report["status"], "scanned")
        self.assertEqual(len(later["sources"]), len(model_watch.SOURCES))

    def test_source_error_retries_next_day(self):
        state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)
        state["last_report"] = {"checked_at": model_watch.iso(FRIDAY),
                                "errors": {"anthropic": "TimeoutError"}}
        _, report = model_watch.scan_state(state, self.fetch, FRIDAY + timedelta(days=1))
        self.assertEqual(report["status"], "scanned")

    def test_failed_fetch_keeps_existing_evidence_and_reports_error(self):
        state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)

        def failed(provider, _url):
            if provider == "anthropic":
                raise TimeoutError("offline")
            return self.pages[provider]

        prior = copy.deepcopy(state["sources"]["anthropic"])
        updated, report = model_watch.scan_state(state, failed, FRIDAY + timedelta(days=7))
        self.assertEqual(updated["sources"]["anthropic"], prior)
        self.assertIn("anthropic", report["errors"])

    def test_release_and_two_temporally_separated_feedback_items_are_required(self):
        state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)
        self.pages["anthropic"] += (
            '<a href="/news/claude-haiku-5-5">Claude Haiku 5.5</a>'
        )
        state, report = model_watch.scan_state(state, self.fetch, FRIDAY + timedelta(days=7))
        key = report["new_candidates"][0]
        release_time = FRIDAY + timedelta(days=7, minutes=1)
        model_watch.confirm_release(state, key, release_time, "https://www.anthropic.com/news/claude-haiku-5-5")
        model_watch.add_feedback(state, key, release_time + timedelta(hours=1),
                                 "https://www.reddit.com/r/ClaudeAI/comments/example1", "mixed")
        self.assertEqual(model_watch.candidate_status(state["candidates"][key], release_time + timedelta(hours=25)),
                         "monitoring")
        model_watch.add_feedback(state, key, release_time + timedelta(hours=23),
                                 "https://news.ycombinator.com/item?id=123", "positive")
        self.assertEqual(model_watch.candidate_status(state["candidates"][key], release_time + timedelta(hours=23)),
                         "monitoring")
        self.assertEqual(model_watch.candidate_status(state["candidates"][key], release_time + timedelta(hours=25)),
                         "review_ready")
        self.assertFalse(state["candidates"][key]["routing_ready"])

    def test_feedback_cannot_be_backdated_or_duplicate(self):
        state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)
        self.pages["xai"] += '<a href="/news/grok-4-8">Grok 4.8</a>'
        state, report = model_watch.scan_state(state, self.fetch, FRIDAY + timedelta(days=7))
        key = report["new_candidates"][0]
        now = FRIDAY + timedelta(days=7, minutes=1)
        model_watch.confirm_release(state, key, now, "https://x.ai/news/grok-4-8")
        with self.assertRaises(ValueError):
            model_watch.add_feedback(state, key, now - timedelta(seconds=1),
                                     "https://x.com/example/status/1", "positive")
        model_watch.add_feedback(state, key, now, "https://x.com/example/status/1", "positive")
        with self.assertRaises(ValueError):
            model_watch.add_feedback(state, key, now + timedelta(hours=1),
                                     "https://x.com/example/status/1", "negative")
        first_feedback = copy.deepcopy(state["candidates"][key]["feedback"][0])
        for legacy_url in ("https://x.com:443/example/status/1",
                           "https://x.com.:443/example/status/1"):
            state["candidates"][key]["feedback"] = [{**first_feedback, "url": legacy_url}]
            with self.subTest(legacy_url=legacy_url), self.assertRaises(ValueError):
                model_watch.add_feedback(state, key, now + timedelta(hours=23),
                                         "https://x.com/example/status/1", "negative")
            self.assertEqual(len(state["candidates"][key]["feedback"]), 1)
        with self.assertRaises(ValueError):
            model_watch.add_feedback(state, key, now + timedelta(hours=1),
                                     "https://127.0.0.1/internal", "positive")
        for host in ("localhost", "localhost.", "intranet", "host.internal",
                     "host.internal.", "host.local"):
            with self.subTest(host=host), self.assertRaises(ValueError):
                model_watch.add_feedback(state, key, now + timedelta(hours=1),
                                         f"https://{host}/post", "positive")

    def test_release_url_accepts_canonical_same_host_variants(self):
        state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)
        self.pages["xai"] += '<a href="/news/grok-4-8">Grok 4.8</a>'
        state, report = model_watch.scan_state(state, self.fetch, FRIDAY + timedelta(days=7))
        key = report["new_candidates"][0]
        now = FRIDAY + timedelta(days=7, minutes=1)
        with self.assertRaises(ValueError):
            model_watch.confirm_release(state, key, now, "https://other.example/news/grok-4-8")
        model_watch.confirm_release(state, key, now,
                                    "https://x.ai/news/grok-4-8/?source=watch#release")
        self.assertEqual(state["candidates"][key]["status"], "released")

    def test_official_link_cannot_escape_source_host_or_use_extra_port(self):
        base = model_watch.SOURCES["xai"]
        self.assertIsNone(model_watch.canonical_link(base, "https://other.example/news/grok-5"))
        self.assertIsNone(model_watch.canonical_link(base, "https://x.ai:8443/news/grok-5"))

    def test_official_rss_item_is_detected_without_html(self):
        feed = ('<?xml version="1.0"?><rss><channel><item>'
                '<title>Introducing GPT-7 Sol</title>'
                '<link>https://openai.com/index/gpt-7-sol/</link>'
                '</item></channel></rss>')
        links, headings = model_watch.extract_model_mentions(feed, model_watch.SOURCES["openai"])
        self.assertEqual(links, {"https://openai.com/index/gpt-7-sol": "Introducing GPT-7 Sol"})
        self.assertEqual(headings, set())

    def test_common_openai_model_names_are_detected(self):
        for name in ("GPT-4o", "GPT-4o mini", "o3", "o4-mini", "GPT-4.1-mini"):
            with self.subTest(name=name):
                feed = ("<rss><channel><item><title>Introducing " + name + "</title>"
                        "<link>https://openai.com/index/release/</link></item></channel></rss>")
                links, _ = model_watch.extract_model_mentions(feed, model_watch.SOURCES["openai"])
                self.assertEqual(len(links), 1)

    def test_gpt_4o_mini_feedback_does_not_admit_base_model_posts(self):
        item = {"title": "Introducing GPT-4o mini", "release_verified_at": model_watch.iso(FRIDAY)}
        self.assertEqual(model_watch.MODEL_NAME.search(item["title"]).group(0), "GPT-4o mini")
        self.assertIn("GPT-4o+mini", model_watch.feedback_query(item))
        feed = ('<feed xmlns="http://www.w3.org/2005/Atom">'
                '<entry><title>GPT-4o impressions</title>'
                '<link href="https://www.reddit.com/r/OpenAI/comments/base" />'
                '<published>2026-10-02T01:00:00+00:00</published></entry>'
                '<entry><title>GPT-4o-mini impressions</title>'
                '<link href="https://www.reddit.com/r/OpenAI/comments/mini" />'
                '<published>2026-10-02T01:00:00+00:00</published></entry></feed>')
        self.assertEqual([post["title"] for post in model_watch.extract_public_feedback(feed, item)],
                         ["GPT-4o-mini impressions"])

    def test_spaced_o_series_variants_do_not_admit_base_model_posts(self):
        for base, suffix in (("o4", "mini"), ("o3", "pro"), ("o1", "preview")):
            with self.subTest(base=base, suffix=suffix):
                variant = f"{base} {suffix}"
                item = {"title": f"Introducing {variant}",
                        "release_verified_at": model_watch.iso(FRIDAY)}
                self.assertEqual(model_watch.MODEL_NAME.search(item["title"]).group(0),
                                 variant)
                self.assertIn(f"{base}+{suffix}", model_watch.feedback_query(item))
                feed = ('<feed xmlns="http://www.w3.org/2005/Atom">'
                        f'<entry><title>{base} impressions</title>'
                        '<link href="https://www.reddit.com/r/OpenAI/comments/base" />'
                        '<published>2026-10-02T01:00:00+00:00</published></entry>'
                        f'<entry><title>{base}-{suffix} impressions</title>'
                        '<link href="https://www.reddit.com/r/OpenAI/comments/variant" />'
                        '<published>2026-10-02T01:00:00+00:00</published></entry></feed>')
                self.assertEqual(
                    [post["title"] for post in model_watch.extract_public_feedback(feed, item)],
                    [f"{base}-{suffix} impressions"])

    def test_hyphenated_model_variants_do_not_count_for_base_models(self):
        for base, variant in (("o3", "o3-deep-research"),
                              ("GPT-4o", "GPT-4o-voice"),
                              ("Grok 4.8", "Grok 4.8-fast")):
            with self.subTest(base=base, variant=variant):
                self.assertEqual(model_watch.MODEL_NAME.search(variant).group(0), variant)
                feed = ('<feed xmlns="http://www.w3.org/2005/Atom">'
                        f'<entry><title>{variant} impressions</title>'
                        '<link href="https://www.reddit.com/r/AI/comments/variant" />'
                        '<published>2026-10-02T01:00:00+00:00</published></entry>'
                        f'<entry><title>{base} impressions</title>'
                        '<link href="https://www.reddit.com/r/AI/comments/base" />'
                        '<published>2026-10-02T01:00:00+00:00</published></entry></feed>')
                for candidate, expected in ((base, f"{base} impressions"),
                                            (variant, f"{variant} impressions")):
                    item = {"title": f"Introducing {candidate}",
                            "release_verified_at": model_watch.iso(FRIDAY)}
                    self.assertEqual(
                        [post["title"] for post in model_watch.extract_public_feedback(feed, item)],
                        [expected])
        self.assertEqual(model_watch.MODEL_NAME.search("o3 deep research").group(0),
                         "o3 deep research")

    def test_model_aliases_match_without_admitting_other_variants(self):
        for candidate, alias, unrelated in (
                ("Sonnet 5.5", "Claude Sonnet 5.5", "Claude Sonnet 5.6"),
                ("Claude Opus 5.5", "Opus 5.5", "Opus 5.6"),
                ("o3-deep-research", "o3 deep research", "o3"),
                ("GPT4o", "GPT-4o", "GPT-4o mini"),
                ("GPT-4o mini", "GPT4o mini", "GPT-4o")):
            with self.subTest(candidate=candidate, alias=alias):
                item = {"title": f"Introducing {candidate}",
                        "release_verified_at": model_watch.iso(FRIDAY)}
                feed = ('<feed xmlns="http://www.w3.org/2005/Atom">'
                        f'<entry><title>{unrelated} impressions</title>'
                        '<link href="https://www.reddit.com/r/AI/comments/other" />'
                        '<published>2026-10-02T01:00:00+00:00</published></entry>'
                        f'<entry><title>{alias} impressions</title>'
                        '<link href="https://www.reddit.com/r/AI/comments/alias" />'
                        '<published>2026-10-02T01:00:00+00:00</published></entry></feed>')
                self.assertEqual(
                    [post["title"] for post in model_watch.extract_public_feedback(feed, item)],
                    [f"{alias} impressions"])

    def test_legacy_duplicate_feedback_urls_do_not_satisfy_review_gate(self):
        item = {"status": "released", "release_verified_at": model_watch.iso(FRIDAY),
                "feedback": [
                    {"url": "https://x.com:443/u/status/1",
                     "observed_at": model_watch.iso(FRIDAY + timedelta(hours=1))},
                    {"url": "https://x.com./u/status/1",
                     "observed_at": model_watch.iso(FRIDAY + timedelta(hours=23))}]}
        self.assertEqual(model_watch.candidate_status(item, FRIDAY + timedelta(hours=25)),
                         "monitoring")

    def test_public_feedback_feed_is_captured_but_not_auto_graded(self):
        state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)
        self.pages["xai"] += '<a href="/news/grok-4-8">Grok 4.8</a>'
        state, report = model_watch.scan_state(state, self.fetch, FRIDAY + timedelta(days=7))
        key = report["new_candidates"][0]
        release = FRIDAY + timedelta(days=7, minutes=1)
        model_watch.confirm_release(state, key, release, "https://x.ai/news/grok-4-8")

        def public_feed(_provider, _url):
            return ('<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
                    '<title>Grok 4.8 coding impressions</title>'
                    '<link href="https://www.reddit.com/r/grok/comments/post1#context" />'
                    '<published>2026-10-09T00:02:00+00:00</published>'
                    '</entry><entry><title>Grok 4.8 invalid redirect</title>'
                    '<link href="https://www.reddit.com:8443/r/grok/comments/invalid" />'
                    '<published>2026-10-09T00:02:00+00:00</published>'
                    '</entry></feed>')

        first = release + timedelta(hours=1)
        state, report = model_watch.scan_state(state, self.fetch, first, feedback_fetch=public_feed)
        self.assertEqual(report["feedback_captures"], [key])
        item = state["candidates"][key]
        self.assertEqual(len(item["captures"]), 1)
        self.assertEqual(item["captures"][0]["url"],
                         "https://www.reddit.com/r/grok/comments/post1")
        self.assertEqual(item["feedback"], [])
        self.assertFalse(item["routing_ready"])
        item["captures"][0]["url"] = "https://www.reddit.com:443/r/grok/comments/post1"
        state, alias_report = model_watch.scan_state(state, self.fetch,
                                                     first + timedelta(hours=1),
                                                     feedback_fetch=public_feed)
        self.assertEqual(alias_report["feedback_captures"], [])
        item = state["candidates"][key]
        self.assertEqual(len(item["captures"]), 1)
        model_watch.add_feedback(state, key, first + timedelta(hours=2),
                                 "https://www.reddit.com/r/grok/comments/post1", "mixed")
        self.assertEqual(item["feedback"][0]["observed_at"], model_watch.iso(first))
        self.assertTrue(item["captures"][0]["reviewed"])
        item["feedback"][0]["url"] = "https://www.reddit.com:443/r/grok/comments/post1"
        state, next_report = model_watch.scan_state(state, self.fetch,
                                                     first + timedelta(hours=3),
                                                     feedback_fetch=public_feed)
        self.assertEqual(next_report["feedback_captures"], [])
        self.assertEqual(state["candidates"][key]["captures"], [])
        state, later_report = model_watch.scan_state(state, self.fetch,
                                                      first + timedelta(hours=4),
                                                      feedback_fetch=public_feed)
        self.assertEqual(later_report["feedback_captures"], [])
        self.assertEqual(state["candidates"][key]["captures"], [])

    def test_feedback_filter_keeps_exact_model_version(self):
        item = {"title": "Grok 4.8", "release_verified_at": model_watch.iso(FRIDAY)}
        feed = ('<feed xmlns="http://www.w3.org/2005/Atom">'
                '<entry><title>Grok 4.7 impressions</title>'
                '<link href="https://www.reddit.com/r/grok/comments/old" />'
                '<published>2026-10-02T01:00:00+00:00</published></entry>'
                '<entry><title>Grok 4.8 impressions</title>'
                '<link href="https://www.reddit.com/r/grok/comments/new" />'
                '<published>2026-10-02T01:00:00+00:00</published></entry>'
                '<entry><title>Grok 4.80 impressions</title>'
                '<link href="https://www.reddit.com/r/grok/comments/newer" />'
                '<published>2026-10-02T01:00:00+00:00</published></entry></feed>')
        posts = model_watch.extract_public_feedback(feed, item)
        self.assertEqual([post["title"] for post in posts], ["Grok 4.8 impressions"])

    def test_feedback_captures_are_bounded_without_losing_reviewed_feedback(self):
        state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)
        self.pages["xai"] += '<a href="/news/grok-4-8">Grok 4.8</a>'
        state, report = model_watch.scan_state(state, self.fetch, FRIDAY + timedelta(days=7))
        key = report["new_candidates"][0]
        release = FRIDAY + timedelta(days=7, minutes=1)
        model_watch.confirm_release(state, key, release, "https://x.ai/news/grok-4-8")
        item = state["candidates"][key]
        item["feedback"].append({"url": "https://www.reddit.com/r/grok/comments/old",
                                 "observed_at": model_watch.iso(release),
                                 "reviewed_at": model_watch.iso(release), "sentiment": "mixed"})
        item["captures"] = [
            {"url": f"https://www.reddit.com/r/grok/comments/{number}",
             "title": "Grok 4.8", "observed_at": model_watch.iso(release),
             "published_at": model_watch.iso(release), "reviewed": False}
            for number in range(200)
        ]
        item["captures"].append({"url": "https://www.reddit.com/r/grok/comments/old",
                                 "reviewed": True})
        state, _ = model_watch.scan_state(state, self.fetch, release + timedelta(days=1),
                                           feedback_fetch=lambda *_: "<feed />")
        self.assertLessEqual(len(state["candidates"][key]["captures"]),
                             model_watch.MAX_CAPTURED_POSTS)
        self.assertEqual(len(state["candidates"][key]["feedback"]), 1)

    def test_cli_persists_last_scan_report_for_scheduler_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "watch.json"
            with (mock.patch("sys.argv", ["model_watch.py", "scan", "--force", "--state", str(path)]),
                  mock.patch.object(model_watch, "fetch_public_page", side_effect=self.fetch),
                  contextlib.redirect_stdout(io.StringIO())):
                self.assertEqual(model_watch.main(), 0)
            state = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(state["last_report"]["status"], "scanned")
            with (mock.patch("sys.argv", ["model_watch.py", "status", "--state", str(path)]),
                  contextlib.redirect_stdout(io.StringIO()) as output):
                self.assertEqual(model_watch.main(), 0)
            self.assertEqual(json.loads(output.getvalue())["last_report"]["status"], "scanned")
            self.assertIn("candidate_details", json.loads(output.getvalue()))

    def test_cli_returns_failure_for_feedback_fetch_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "watch.json"
            state, _ = model_watch.scan_state({}, self.fetch, FRIDAY)
            self.pages["xai"] += '<a href="/news/grok-4-8">Grok 4.8</a>'
            state, report = model_watch.scan_state(state, self.fetch, FRIDAY + timedelta(days=7))
            model_watch.confirm_release(state, report["new_candidates"][0],
                                        FRIDAY + timedelta(days=7, minutes=1),
                                        "https://x.ai/news/grok-4-8")
            model_watch.write_json(path, state)

            def broken(provider, url):
                if provider == "reddit":
                    raise TimeoutError("feed unavailable")
                return self.fetch(provider, url)

            with (mock.patch("sys.argv", ["model_watch.py", "scan", "--force", "--state", str(path)]),
                  mock.patch.object(model_watch, "fetch_public_page", side_effect=broken),
                  contextlib.redirect_stdout(io.StringIO()) as output):
                self.assertEqual(model_watch.main(), 2)
            self.assertTrue(json.loads(output.getvalue())["feedback_errors"])

    def test_state_lock_is_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "watch.json"
            with model_watch.state_lock(path):
                with self.assertRaises(TimeoutError):
                    with model_watch.state_lock(path, timeout=0.02):
                        pass

    def test_oversized_state_is_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "watch.json"
            with self.assertRaises(ValueError):
                model_watch.write_json(path, {"content": "x" * model_watch.MAX_STATE_BYTES})
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
