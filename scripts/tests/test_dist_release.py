"""D-76 release version and dist staging, using only disposable Git repos and folders."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import dist_release as dist

OWNERS = sorted(dist.OWNERS)


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    return subprocess.check_output(
        ["git", "-c", "core.autocrlf=false", "-c", "commit.gpgSign=false", "-c", "core.hooksPath=" + os.devnull,
         "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-C", str(root), *args],
        text=True, encoding="utf-8", stderr=subprocess.PIPE, timeout=30, env=env)


def record(**changes):
    """A schema-2 record (D-88 stage 2): Claude and Codex content digests."""
    value = {"schema_version": 2, "scope": dist.DIST_SCOPE, "version": "1.10.0",
             "content_digest": "a" * 64, "bundle_digest": "b" * 64, "source_commit": "c" * 40,
             "source_digest": "d" * 64, "pins": {owner: "e" * 40 for owner in OWNERS},
             "codex_overlay_digest": "f" * 64, "codex_subset_digest": "0" * 64,
             "codex_content_digest": "7" * 64, "run": None}
    value.update(changes)
    return value


def record_v1(**changes):
    """The schema-1 shape dist already carries (1.777.0): no Codex content."""
    value = record(schema_version=1)
    del value["codex_content_digest"]
    value.update(changes)
    return value


class VersionSchemeTests(unittest.TestCase):
    def test_only_plain_semver_cores_are_release_versions(self):
        self.assertEqual(dist.parse_version("1.561.0"), (1, 561, 0))
        for bad in ("0.1.0-vibe.018825543742", "1.2.3-rc.1", "1.2.3+c0ffee", "1.01.0", "01.2.3",
                    "1.2", "v1.2.3", "1.2.3 ", "", None, 1, ["1.2.3"]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                dist.parse_version(bad)

    def test_versions_rise_with_the_count_and_compare_numerically(self):
        self.assertEqual(dist.release_version(561), "1.561.0")
        previous = dist.parse_version(dist.release_version(1))
        for count in (2, 9, 10, 99, 100, 999, 1000, 12345):
            current = dist.parse_version(dist.release_version(count))
            self.assertGreater(current, previous)  # 1.10.0 > 1.9.0, unlike string order
            previous = current
        for bad in (0, -1, True, 1.0, "3"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                dist.release_version(bad)

    def test_first_release_sorts_above_legacy_and_every_old_base(self):
        first = dist.parse_version(dist.release_version(1))
        self.assertEqual(dist.LEGACY_FLOOR, "0.1.0")  # the archived root plugin's version
        for old in (dist.LEGACY_FLOOR, "0.1.0", "0.3.0", "0.99.99"):
            self.assertGreater(first, dist.parse_version(old))


class ComputeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dist-release-test-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        (self.repo / "distribution").mkdir(parents=True)
        git(self.repo, "init", "-q")
        self.inputs = self.repo / "distribution/plugin-inputs.v1.json"
        self.write_pins("1" * 40)
        self.commit("first")

    def write_pins(self, sha):
        self.inputs.write_text(json.dumps({"schema_version": 1, "plugins": {
            owner: {"name": "simonk-" + owner.removeprefix("SimonK").lower(), "commit": sha}
            for owner in OWNERS}}), encoding="utf-8", newline="\n")

    def commit(self, message):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", message)

    def test_same_commit_same_version_and_pin_only_change_raises_it(self):
        first = dist.compute(self.repo)
        self.assertEqual(first["version"], "1.1.0")
        self.assertEqual(first["commit_count"], 1)
        self.assertEqual(first["commit"], git(self.repo, "rev-parse", "HEAD").strip())
        self.assertEqual(dist.compute(self.repo), first)  # rebuild of one commit: same version
        self.write_pins("2" * 40)  # pin-only change
        self.commit("chore: bump one plugin pin")
        second = dist.compute(self.repo)
        self.assertEqual(second["version"], "1.2.0")
        self.assertGreater(dist.parse_version(second["version"]), dist.parse_version(first["version"]))

    def test_merged_side_branch_still_raises_the_version(self):
        git(self.repo, "checkout", "-qb", "side")
        for n in range(3):
            (self.repo / f"side{n}.txt").write_text("x", encoding="utf-8")
            self.commit(f"side {n}")
        git(self.repo, "checkout", "-q", "-")
        (self.repo / "main.txt").write_text("y", encoding="utf-8")
        self.commit("main")
        before = dist.compute(self.repo)["commit_count"]
        git(self.repo, "merge", "-q", "--no-ff", "-m", "merge side", "side")
        self.assertGreater(dist.compute(self.repo)["commit_count"], before)

    def test_shallow_clone_is_refused(self):
        self.commit_twice()
        clone = Path(self.temp.name) / "shallow"
        git(self.temp.name, "clone", "-q", "--depth", "1", self.repo.as_uri(), str(clone))
        with self.assertRaisesRegex(ValueError, "Shallow"):
            dist.compute(clone)

    def commit_twice(self):
        for n in range(2):
            (self.repo / f"more{n}.txt").write_text("z", encoding="utf-8")
            self.commit(f"more {n}")

    def test_legacy_root_plugin_version_is_a_floor(self):
        # D-87 PR-B: the floor is the constant 0.1.0; no root manifest is read.
        self.assertEqual(dist.compute(self.repo)["legacy_floor"], "0.1.0")
        manifest = self.repo / ".claude-plugin/plugin.json"
        manifest.parent.mkdir()
        manifest.write_text(json.dumps({"name": "simonk-stack", "version": "1.5.0"}), encoding="utf-8")
        self.commit("stray root manifest above the scheme")
        result = dist.compute(self.repo)
        self.assertEqual((result["version"], result["legacy_floor"]), ("1.2.0", "0.1.0"))
        from unittest.mock import patch
        with patch.object(dist, "LEGACY_FLOOR", "1.5.0"), self.assertRaisesRegex(ValueError, "legacy"):
            dist.compute(self.repo)

    def test_cli_prints_the_version_json(self):
        import io
        from unittest.mock import patch
        with patch.object(sys, "stdout", io.StringIO()) as stdout:
            self.assertEqual(dist.main(["version", "--repo", str(self.repo)]), 0)
        self.assertEqual(json.loads(stdout.getvalue())["version"], "1.1.0")


class DecideTests(unittest.TestCase):
    def test_first_release_publishes(self):
        self.assertEqual(dist.decide(None, record())["action"], "publish")

    def test_identical_content_is_skipped_at_any_version(self):
        for version in ("1.9.0", "1.10.0", "1.11.0"):
            with self.subTest(version=version):
                decision = dist.decide(record(), record(version=version, bundle_digest="9" * 64))
                self.assertEqual((decision["action"], decision["reason"]), ("skip", "identical-content"))

    def test_new_content_needs_a_higher_version(self):
        self.assertEqual(dist.decide(record(), record(version="1.11.0", content_digest="1" * 64))["action"],
                         "publish")
        for version in ("1.10.0", "1.9.0", "0.99.0"):
            with self.subTest(version=version):
                decision = dist.decide(record(), record(version=version, content_digest="1" * 64))
                self.assertEqual((decision["action"], decision["reason"]), ("refuse", "not-newer-than-dist"))

    def test_rollback_reships_older_content_under_a_higher_version(self):
        good = record(version="1.10.0", content_digest="1" * 64)
        bad = record(version="1.20.0", content_digest="2" * 64)
        self.assertEqual(dist.decide(good, bad)["action"], "publish")
        rollback = record(version="1.25.0", content_digest="1" * 64)  # reverted on main
        self.assertEqual(dist.decide(bad, rollback)["action"], "publish")
        stale = record(version="1.15.0", content_digest="1" * 64)  # late old run
        self.assertEqual(dist.decide(bad, stale)["action"], "refuse")

    def test_records_are_exact(self):
        for change in ({"version": "1.10.0-rc.1"}, {"content_digest": "A" * 64}, {"source_commit": "c" * 39},
                       {"pins": {"SimonKCore": "e" * 40}}, {"run": "http://insecure"}, {"schema_version": True},
                       {"scope": "other"}, {"extra": 1}, {"schema_version": 3}, {"schema_version": 1},
                       {"codex_content_digest": "A" * 64}, {"codex_content_digest": None}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                dist.decide(None, record(**change))
        without_codex = record()
        del without_codex["codex_content_digest"]  # schema 2 must name the Codex content
        for bad in (without_codex, record_v1(schema_version=2), record_v1(schema_version=True)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                dist.decide(None, bad)
        with self.assertRaises(ValueError):
            dist.decide({"version": "1.1.0"}, record())

    def test_codex_content_counts_for_skip_and_publish(self):
        # Same Claude content, new Codex content: a new release, which must still be newer.
        newer = dist.decide(record(), record(version="1.11.0", codex_content_digest="8" * 64))
        self.assertEqual((newer["action"], newer["reason"]), ("publish", "new-content"))
        for version in ("1.10.0", "1.9.0"):
            with self.subTest(version=version):
                decision = dist.decide(record(), record(version=version, codex_content_digest="8" * 64))
                self.assertEqual((decision["action"], decision["reason"]), ("refuse", "not-newer-than-dist"))
        same = dist.decide(record(), record(version="1.12.0", bundle_digest="9" * 64, codex_subset_digest="1" * 64))
        self.assertEqual((same["action"], same["reason"]), ("skip", "identical-content"))

    def test_schema_1_record_on_dist_is_a_valid_previous_without_codex_content(self):
        on_dist = record_v1(version="1.777.0")
        self.assertEqual(dist.validate_record(on_dist), on_dist)
        first_codex = dist.decide(on_dist, record(version="1.778.0"))
        self.assertEqual((first_codex["action"], first_codex["reason"]), ("publish", "new-content"))
        # Same Claude content is not identical any more: the Codex content is new...
        late = dist.decide(on_dist, record(version="1.777.0"))
        self.assertEqual((late["action"], late["reason"]), ("refuse", "not-newer-than-dist"))
        # ...while two schema-1 records still compare as before.
        self.assertEqual(dist.decide(on_dist, record_v1(version="1.800.0"))["action"], "skip")

    def test_cli_refuse_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as raw:
            previous, current = Path(raw, "prev.json"), Path(raw, "cur.json")
            previous.write_bytes(dist.encoded(record(version="1.20.0", content_digest="2" * 64)))
            current.write_bytes(dist.encoded(record(version="1.15.0")))
            import io
            from unittest.mock import patch
            with patch.object(sys, "stdout", io.StringIO()):
                self.assertEqual(dist.main(["decide", "--previous", str(previous), "--current", str(current)]), 1)
                self.assertEqual(dist.main(["decide", "--current", str(current)]), 0)


class PublishGateTests(unittest.TestCase):
    """D-82 follow-up 1: publish approval is its own committed record, not the D-33 hold."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dist-gate-test-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        (self.repo / "distribution").mkdir(parents=True)
        git(self.repo, "init", "-q")
        (self.repo / "skills.txt").write_text("candidate", encoding="utf-8")
        self.commit("candidate")
        self.candidate = self.head()

    def head(self):
        return git(self.repo, "rev-parse", "HEAD").strip()

    def commit(self, message):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", message)

    def approve(self, drop=(), **changes):
        """A schema-2 approval naming both content digests unless told otherwise."""
        value = {"schema_version": 2, "scope": dist.DIST_SCOPE, "decision": "D-82",
                 "source_commit": self.candidate, "content_digest": "a" * 64,
                 "codex_content_digest": "7" * 64}
        value.update(changes)
        for key in drop:
            del value[key]
        (self.repo / dist.ALLOW).write_bytes(dist.encoded(value))

    def approve_v1(self, **changes):
        self.approve(drop=("codex_content_digest",), schema_version=1, **changes)

    def built(self, **changes):
        return record(source_commit=self.head(), **changes)

    def built_v1(self, **changes):
        return record_v1(source_commit=self.head(), **changes)

    def test_no_committed_approval_refuses(self):
        self.assertEqual(dist.gate(self.repo, self.built())["reason"], "no-approval")
        self.approve()  # in the working tree only: must not count
        self.assertEqual(dist.gate(self.repo, self.built())["reason"], "no-approval")

    def test_approval_publishes_with_or_without_the_hold(self):
        (self.repo / "distribution/main-source-only.hold").write_text("hold\n", encoding="utf-8")
        self.approve()
        self.commit("approve the session-tested candidate")
        decision = dist.gate(self.repo, self.built())
        self.assertEqual((decision["action"], decision["reason"], decision["decision"]),
                         ("publish", "approved", "D-82"))
        (self.repo / "distribution/main-source-only.hold").unlink()
        self.commit("hold removed later")
        self.assertEqual(dist.gate(self.repo, self.built())["action"], "publish")

    def test_other_content_is_refused(self):
        self.approve()
        self.commit("approve")
        decision = dist.gate(self.repo, self.built(content_digest="1" * 64))
        self.assertEqual((decision["action"], decision["reason"]), ("refuse", "content-not-approved"))
        decision = dist.gate(self.repo, self.built(codex_content_digest="8" * 64))
        self.assertEqual((decision["action"], decision["reason"]), ("refuse", "codex-content-not-approved"))

    def test_codex_content_needs_a_schema_2_approval_naming_it(self):
        # D-88 stage 2: a schema-1 approval (Claude content only) never lets Codex content
        # reach dist, and a schema-2 approval does not approve a record without Codex content.
        cases = ((1, 1, "publish", "approved"),
                 (1, 2, "refuse", "codex-content-not-approved"),
                 (2, 1, "refuse", "codex-content-not-approved"),
                 (2, 2, "publish", "approved"))
        for record_schema, allow_schema, action, reason in cases:
            with self.subTest(record=record_schema, allow=allow_schema):
                self.approve() if allow_schema == 2 else self.approve_v1()
                self.commit(f"approval schema {allow_schema} for record schema {record_schema}")
                current = self.built() if record_schema == 2 else self.built_v1()
                decision = dist.gate(self.repo, current)
                self.assertEqual((decision["action"], decision["reason"]), (action, reason))
        self.approve(codex_content_digest="8" * 64)
        self.commit("approval names other Codex content")
        decision = dist.gate(self.repo, self.built())
        self.assertEqual((decision["action"], decision["reason"]), ("refuse", "codex-content-not-approved"))

    def test_approved_commit_must_be_an_ancestor_of_the_build(self):
        git(self.repo, "checkout", "-qb", "side")
        (self.repo / "side.txt").write_text("side", encoding="utf-8")
        self.commit("side")
        side = self.head()
        git(self.repo, "checkout", "-q", "-")
        self.approve(source_commit=side)
        self.commit("approve a commit that is not in this lineage")
        decision = dist.gate(self.repo, self.built())
        self.assertEqual((decision["action"], decision["reason"]), ("refuse", "source-outside-approval"))
        self.approve(source_commit="9" * 40)
        self.commit("approve an unknown commit")
        with self.assertRaisesRegex(ValueError, "not in this repository"):
            dist.gate(self.repo, self.built())

    def test_record_must_be_the_checked_out_commit(self):
        with self.assertRaisesRegex(ValueError, "built commit"):
            dist.gate(self.repo, record(source_commit="c" * 40))

    def test_shallow_clone_cannot_prove_the_ancestor(self):
        self.approve()
        self.commit("approve")
        clone = Path(self.temp.name) / "shallow"
        git(self.temp.name, "clone", "-q", "--depth", "1", self.repo.as_uri(), str(clone))
        with self.assertRaisesRegex(ValueError, "Shallow"):
            dist.gate(clone, record(source_commit=git(clone, "rev-parse", "HEAD").strip()))

    def test_approval_fields_are_exact(self):
        for change in ({"decision": "D-0"}, {"decision": "d-82"}, {"decision": "D-82 "}, {"decision": 82},
                       {"source_commit": "C" * 40}, {"content_digest": "a" * 63}, {"schema_version": True},
                       {"scope": "other"}, {"extra": 1}, {"schema_version": 3},
                       {"schema_version": 1},  # a schema-1 approval cannot carry a Codex digest
                       {"codex_content_digest": "A" * 64}, {"codex_content_digest": None}):
            with self.subTest(change=change):
                self.approve(**change)
                self.commit(f"bad approval {change}")
                with self.assertRaises(ValueError):
                    dist.gate(self.repo, self.built())
        self.approve(drop=("codex_content_digest",))  # schema 2 must name the Codex content
        self.commit("schema-2 approval without a Codex digest")
        with self.assertRaises(ValueError):
            dist.gate(self.repo, self.built())

    def test_cli_exit_codes(self):
        import io
        from unittest.mock import patch
        current = Path(self.temp.name) / "RELEASE.json"
        current.write_bytes(dist.encoded(self.built()))
        argv = ["gate", "--repo", str(self.repo), "--current", str(current)]
        with patch.object(sys, "stdout", io.StringIO()):
            self.assertEqual(dist.main(argv), 1)  # no approval
        self.approve()
        self.commit("approve")
        current.write_bytes(dist.encoded(self.built()))
        with patch.object(sys, "stdout", io.StringIO()) as stdout:
            self.assertEqual(dist.main(argv), 0)
        self.assertEqual(json.loads(stdout.getvalue())["action"], "publish")
        self.approve(decision="approved")
        self.commit("malformed approval")
        current.write_bytes(dist.encoded(self.built()))
        with patch.object(sys, "stdout", io.StringIO()), patch.object(sys, "stderr", io.StringIO()):
            self.assertEqual(dist.main(argv), 2)


class PublishWorkflowTests(unittest.TestCase):
    """The publish job needs the variable AND the approval gate; the hold is not read there."""

    @classmethod
    def setUpClass(cls):
        workflow = (ROOT / ".github/workflows/five-plugin-dist.yml").read_text(encoding="utf-8")
        cls.publish = workflow.split("\n  publish:\n", 1)[1]
        cls.steps = cls.publish.split("\n      - ")[1:]

    def step_index(self, needle):
        found = [i for i, step in enumerate(self.steps) if needle in step]
        self.assertEqual(len(found), 1, needle)
        return found[0]

    def test_job_still_needs_the_variable_on_main_push(self):
        condition = next(line for line in self.publish.splitlines() if line.startswith("    if: "))
        self.assertEqual(condition, "    if: ${{ vars.SIMONK_DIST_PUBLISH == 'true' && github.event_name "
                                    "!= 'pull_request' && github.ref == 'refs/heads/main' }}")

    def test_gate_runs_before_anything_reaches_dist(self):
        gate = self.step_index("scripts/dist_release.py gate")
        self.assertIn('throw "dist publish not approved', self.steps[gate])
        self.assertLess(self.step_index("name: five-plugin-receipts-"), gate)
        for later in ("name: five-plugin-tree-", "plugin_bundle.py verify", "name: codex-subset-tree-",
                      "codex_safe_subset.py verify", "git -C $wt push"):
            self.assertGreater(self.step_index(later), gate, later)
        self.assertIn("fetch-depth: 0", self.steps[self.step_index("uses: actions/checkout@v4")])

    def test_codex_subset_is_reverified_then_staged_beside_the_plugins(self):
        # D-88 stage 2: the transferred subset is checked against the build's pin before
        # stage copies it, and the dist commit names the Codex content it ships.
        verify = self.step_index("codex_safe_subset.py verify")
        self.assertIn("--package (Join-Path $env:RUNNER_TEMP 'codex-tree') --expected-digest $env:SUBSET_DIGEST",
                      self.steps[verify])
        self.assertIn("path: ${{ runner.temp }}/codex-tree", self.steps[self.step_index("name: codex-subset-tree-")])
        commit = self.step_index("git -C $wt push")
        self.assertLess(verify, commit)
        self.assertIn("SUBSET_DIGEST: ${{ needs.build.outputs.subset_digest }}", self.publish)
        self.assertIn("dist_release.py stage --candidate $tree --subset $codexTree --record $record", self.steps[commit])
        self.assertIn('"codex $codex"', self.steps[commit])
        # The publish safety properties stay: plain push, one publisher, never force.
        self.assertIn("git -C $wt push origin HEAD:refs/heads/dist\n", self.steps[commit] + "\n")
        self.assertIn("group: five-plugin-dist-publish\n      cancel-in-progress: false", self.publish)
        for forced in ("--force", "push -f", "+HEAD:", "--force-with-lease"):
            self.assertNotIn(forced, self.publish)
        workflow = (ROOT / ".github/workflows/five-plugin-dist.yml").read_text(encoding="utf-8")
        build = workflow.split("\n  publish:\n", 1)[0]
        self.assertIn("      subset_digest: ${{ steps.subset.outputs.subset_digest }}\n", build)
        self.assertIn("--subset-package (Join-Path $env:RUNNER_TEMP 'candidate/codex-subset-safety')", build)

    def test_hold_no_longer_gates_publish(self):
        self.assertNotIn("main-source-only.hold", self.publish)

    def test_tree_artifact_keeps_dot_directories(self):
        # upload-artifact@v4 drops hidden files unless asked; without .claude-plugin/ and
        # .simonk-runtime/ the publish job's re-verify refused the first real publish (2026-10-05).
        workflow = (ROOT / ".github/workflows/five-plugin-dist.yml").read_text(encoding="utf-8")
        build = workflow.split("\n  publish:\n", 1)[0]
        uploads = [s for s in build.split("\n      - ") if "actions/upload-artifact@" in s]
        self.assertEqual(len(uploads), 3)  # receipts, Claude tree, Codex subset tree (D-88 stage 2)
        for step in uploads:
            self.assertIn("include-hidden-files: true", step)
        trees = [s for s in uploads if "five-plugin-receipts-" not in s]
        self.assertEqual(len(trees), 2)
        for step in trees:  # main only, and an empty tree is an error
            self.assertIn("if: ${{ success() && github.event_name != 'pull_request' }}", step)
            self.assertIn("if-no-files-found: error", step)
        codex = [s for s in trees if "name: codex-subset-tree-" in s]
        self.assertEqual(len(codex), 1)
        self.assertIn("path: ${{ runner.temp }}/candidate/codex-subset-safety\n", codex[0])

    def test_committed_approval_names_the_current_approved_content(self):
        # Each approval is its own reviewed change recorded in the hub: D-82 first publish
        # (59eaff15...), D-83 freeze 0.2.6 content for the HTTPS update check (ba8e9216...),
        # D-86 safety hook way-out wording without flat paths (85ccf593...),
        # D-89 vibe 2.15.3 registry refresh (a09f620f...),
        # D-88 stage 2: the same Claude content plus the Codex subset (2879e3ab...).
        # D-88 rollback rehearsal: step 2 reverts it (2879e3ab... again, higher version).
        # D-88 rollback rehearsal: step 1 reworded Codex notice (7c036566...).
        # D-90 Sonnet 5.5 out of the task-fit policy (1c4e534f... / Codex 9b9b0ded...).
        # D-91 class A to Sonnet 5.5 / GPT-6 Luna lanes (430c7ecc... / Codex 2cc4a6ac...).
        # D-92 stale out-of-CI fixtures fixed, multi-terminal-dispatcher 1.1.2 (09d71048... / Codex d2862e04...).
        allow = dist.validate_allow(json.loads((ROOT / dist.ALLOW).read_text(encoding="utf-8")))
        self.assertEqual(allow["schema_version"], 2)
        self.assertEqual(allow["decision"], "D-92")
        self.assertEqual(allow["source_commit"], "d7323fbf0f0983172e5d75ed9777624ea5ed0d77")
        self.assertEqual(allow["content_digest"],
                         "09d71048f527dca238cffd344642a967b3b2df9065a4594fc98719939aaf4036")
        self.assertEqual(allow["codex_content_digest"],
                         "d2862e040169fefb2d34496b8cd73b38a1f8b048334e61e956daae4c40b6953c")


class StageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dist-stage-test-")
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.candidate, self.dist, self.subset = base / "candidate", base / "dist", base / "codex-subset"
        self.dist.mkdir()
        (self.dist / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
        self.members = {
            "plugins/SimonKCore/.claude-plugin/plugin.json": (b'{"version":"1.10.0"}\n', "100644"),
            "plugins/SimonKCore/skills/careful/bin/check-careful.sh": (b"#!/bin/bash\necho ok\n", "100755"),
            "plugins/SimonKCore/skills/vibe/SKILL.md": (b"---\nname: vibe\n---\n", "100644"),
            "plugins/SimonKStack/skills/freeze/SKILL.md": (b"---\nname: freeze\n---\n", "100644"),
            "plugins/SimonKStack/skills/ship/bin/run.sh": (b"#!/bin/bash\necho ship\n", "100755"),
        }
        files = []
        for path, (data, mode) in sorted(self.members.items()):
            self.write(self.candidate, path, data)
            files.append({"path": path, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
                          "mode": mode, "origin": "source", "input_path": path})
        receipt = {"files": files, "source_digest": "d" * 64,
                   "inputs": {"schema_version": 1, "plugins": {o: {"name": o, "commit": "e" * 40} for o in OWNERS}},
                   "release": {"version": "1.10.0", "content_digest": "a" * 64}}
        data = dist.encoded(receipt)
        (self.candidate / "bundle.json").write_bytes(data)
        self.bundle_digest = hashlib.sha256(data).hexdigest()
        # The verified Codex subset: general skills and a Codex manifest, no .claude-plugin/,
        # plus the overlay/bundle receipt copies that name this build (provenance only).
        self.codex = {
            "plugins/SimonKCore/.codex-plugin/plugin.json": b'{"name":"simonk-core","version":"1.10.0"}\n',
            "plugins/SimonKCore/skills/vibe/SKILL.md": b"---\nname: vibe\n---\n",
            "plugins/SimonKStack/skills/ship/bin/run.sh": b"#!/bin/bash\necho ship\n",
        }
        overlay = dist.encoded({"schema_version": 2, "candidate_digest": self.bundle_digest})
        self.overlay_digest = hashlib.sha256(overlay).hexdigest()
        self.provenance = {"overlay.json": overlay, "bundle.json": data}
        self.subset_digest = self.write_subset()
        self.record = dist.release_record(self.candidate, self.bundle_digest, "c" * 40, self.overlay_digest,
                                          self.subset, self.subset_digest, "https://github.com/example/run/1")

    @staticmethod
    def write(root, path, data):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def write_subset(self, extra=None, **changes):
        """(Re)write the subset folder and its schema-2 receipt; return the receipt digest."""
        members = {**self.codex, **self.provenance, **(extra or {})}
        for path, data in members.items():
            self.write(self.subset, path, data)
        receipt = {"schema_version": 2, "scope": "five-plugin-codex-general-skills-only-v2",
                   "source_overlay_digest": self.overlay_digest, "content_digest": "7" * 64,
                   "excluded_skills": ["simonk-core:careful", "simonk-stack:freeze", "simonk-stack:guard",
                                       "simonk-stack:investigate", "simonk-core:unfreeze"],
                   "included_members": [{"path": path, "sha256": hashlib.sha256(data).hexdigest(),
                                         "size": len(data)} for path, data in sorted(members.items())]}
        receipt.update(changes)
        data = dist.encoded(receipt)
        (self.subset / dist.SUBSET_RECEIPT).write_bytes(data)
        return hashlib.sha256(data).hexdigest()

    def test_record_reads_the_verified_candidate_and_subset(self):
        self.assertEqual(self.record["schema_version"], 2)
        self.assertEqual(self.record["version"], "1.10.0")
        self.assertEqual(self.record["content_digest"], "a" * 64)
        self.assertEqual(self.record["codex_content_digest"], "7" * 64)
        self.assertEqual((self.record["codex_overlay_digest"], self.record["codex_subset_digest"]),
                         (self.overlay_digest, self.subset_digest))
        self.assertEqual(self.record["pins"], {o: "e" * 40 for o in OWNERS})
        head = (self.candidate, self.bundle_digest, "c" * 40)
        with self.assertRaisesRegex(ValueError, "bundle digest"):
            dist.release_record(self.candidate, "1" * 64, "c" * 40, self.overlay_digest, self.subset,
                                self.subset_digest)
        with self.assertRaisesRegex(ValueError, "subset digest"):
            dist.release_record(*head, self.overlay_digest, self.subset, "1" * 64)
        with self.assertRaisesRegex(ValueError, "recorded overlay"):
            dist.release_record(*head, "1" * 64, self.subset, self.subset_digest)
        with self.assertRaisesRegex(ValueError, "schema 2"):  # a pre-D-88 subset has no content digest
            dist.release_record(*head, self.overlay_digest, self.subset, self.write_subset(schema_version=1))
        with self.assertRaisesRegex(ValueError, "Codex content digest"):
            dist.release_record(*head, self.overlay_digest, self.subset, self.write_subset(content_digest="A" * 64))
        other = dist.encoded({"schema_version": 2, "candidate_digest": "1" * 64})
        self.provenance["overlay.json"] = other  # an overlay of another build
        self.overlay_digest = hashlib.sha256(other).hexdigest()
        with self.assertRaisesRegex(ValueError, "recorded bundle"):
            dist.release_record(*head, self.overlay_digest, self.subset, self.write_subset())

    def test_stage_writes_the_plugins_and_the_codex_subset(self):
        for stale in ("plugins/SimonKOld/stale.md", "codex/plugins/SimonKOld/stale.md", "codex/subset.json"):
            self.write(self.dist, stale, b"old")
        (self.dist / dist.RECORD).write_text("{}", encoding="utf-8")
        result = dist.stage(self.candidate, self.dist, self.record, self.subset)
        self.assertEqual(result, {"files": 5, "codex_files": 3, "executables": [
            "codex/plugins/SimonKStack/skills/ship/bin/run.sh",  # mode from the Claude bundle receipt
            "plugins/SimonKCore/skills/careful/bin/check-careful.sh",
            "plugins/SimonKStack/skills/ship/bin/run.sh"]})
        self.assertFalse((self.dist / "plugins/SimonKOld").exists())
        self.assertFalse((self.dist / "codex/plugins/SimonKOld").exists())
        for path, (data, _) in self.members.items():
            self.assertEqual((self.dist / path).read_bytes(), data)
        for path, data in self.codex.items():
            self.assertEqual((self.dist / "codex" / path).read_bytes(), data)
        self.assertEqual((self.dist / "codex/subset.json").read_bytes(),
                         (self.subset / "subset.json").read_bytes())
        shipped = sorted(p.relative_to(self.dist / "codex").as_posix()
                         for p in (self.dist / "codex").rglob("*") if p.is_file())
        self.assertEqual(shipped, sorted([*self.codex, "subset.json"]))  # no overlay.json / bundle.json
        self.assertEqual(sorted(p.name for p in self.dist.iterdir()),
                         [".git", ".gitattributes", "RELEASE.json", "codex", "plugins"])
        self.assertEqual((self.dist / ".gitattributes").read_bytes(), b"* -text\n")
        self.assertEqual(json.loads((self.dist / dist.RECORD).read_bytes()), self.record)
        self.assertEqual((self.dist / ".git").read_text(encoding="utf-8"), "gitdir: elsewhere\n")
        self.assertFalse((self.dist / "bundle.json").exists())  # receipts stay in the artifact

    def test_stage_refuses_tampered_or_unexpected_codex_members_before_touching_dist(self):
        stale = self.dist / "plugins/SimonKOld/stale.md"
        self.write(self.dist, "plugins/SimonKOld/stale.md", b"old")
        vibe = self.subset / "plugins/SimonKCore/skills/vibe/SKILL.md"
        vibe.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "differs"):
            dist.stage(self.candidate, self.dist, self.record, self.subset)
        self.assertTrue(stale.exists())  # checked before the dist worktree is wiped
        vibe.write_bytes(self.codex["plugins/SimonKCore/skills/vibe/SKILL.md"])
        for extra in ("plugins/SimonKCore/.claude-plugin/plugin.json",
                      "plugins/SimonKStack/.simonk-runtime/safety_runtime.py",
                      "plugins/SimonKStack/skills/guard/SKILL.md", "plugins/SimonKOther/skills/x/SKILL.md",
                      "README.md"):
            with self.subTest(extra=extra):
                digest = self.write_subset({extra: b"x\n"})
                with self.assertRaises(ValueError):
                    dist.stage(self.candidate, self.dist, dict(self.record, codex_subset_digest=digest),
                               self.subset)
                self.assertTrue(stale.exists())
                (self.subset / extra).unlink()

    def test_stage_needs_the_recorded_codex_content(self):
        v1 = dict(self.record, schema_version=1)
        del v1["codex_content_digest"]
        with self.assertRaisesRegex(ValueError, "schema-2"):
            dist.stage(self.candidate, self.dist, v1, self.subset)
        for change, message in (({"codex_content_digest": "8" * 64}, "content differs"),
                                ({"codex_subset_digest": "1" * 64}, "subset digest"),
                                ({"codex_overlay_digest": "1" * 64}, "recorded overlay")):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, message):
                dist.stage(self.candidate, self.dist, dict(self.record, **change), self.subset)

    def test_stage_never_wipes_a_main_checkout_or_unknown_tree(self):
        (self.dist / ".git").unlink()
        (self.dist / ".git").mkdir()
        with self.assertRaisesRegex(ValueError, "linked Git worktree"):
            dist.stage(self.candidate, self.dist, self.record, self.subset)
        (self.dist / ".git").rmdir()
        (self.dist / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
        (self.dist / "README.md").write_text("not dist", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unexpected top-level"):
            dist.stage(self.candidate, self.dist, self.record, self.subset)
        self.assertTrue((self.dist / "README.md").exists())

    def test_stage_rejects_changed_bytes_and_escaping_paths(self):
        (self.candidate / "plugins/SimonKStack/skills/freeze/SKILL.md").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "differs"):
            dist.stage(self.candidate, self.dist, self.record, self.subset)
        for bad in ("../x", "plugins/../x", "/plugins/a/b", "plugins\\a\\b", "skills/a/b", "plugins/a", "C:/x"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                dist._member(bad)

    def test_cli_record_and_stage(self):
        import io
        from unittest.mock import patch
        out = Path(self.temp.name) / "RELEASE.json"
        with patch.object(sys, "stdout", io.StringIO()):
            self.assertEqual(dist.main([
                "record", "--candidate", str(self.candidate), "--bundle-digest", self.bundle_digest,
                "--source-commit", "c" * 40, "--overlay-digest", self.overlay_digest,
                "--subset-package", str(self.subset), "--subset-digest", self.subset_digest,
                "--run", "https://github.com/example/run/1", "--output", str(out)]), 0)
        self.assertEqual(json.loads(out.read_bytes()), self.record)
        executables = Path(self.temp.name) / "executables.txt"
        with patch.object(sys, "stdout", io.StringIO()) as stdout:
            self.assertEqual(dist.main([
                "stage", "--candidate", str(self.candidate), "--subset", str(self.subset), "--record", str(out),
                "--dist", str(self.dist), "--executables", str(executables)]), 0)
        self.assertEqual(json.loads(stdout.getvalue())["codex_files"], 3)
        self.assertEqual(executables.read_text(encoding="utf-8").splitlines(), [
            "codex/plugins/SimonKStack/skills/ship/bin/run.sh",
            "plugins/SimonKCore/skills/careful/bin/check-careful.sh",
            "plugins/SimonKStack/skills/ship/bin/run.sh"])


if __name__ == "__main__":
    unittest.main()
