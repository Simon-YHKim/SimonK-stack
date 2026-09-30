"""Run offline /vibe smoke tests on a disposable, receipt-verified candidate copy.

This is a regression probe, not an OS sandbox, model-call test, full runtime
closure check, host compatibility check, or installation authorization.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import plugin_bundle
import skill_release as r


SCRIPT_DIR = "plugins/SimonKCore/skills/vibe/scripts"
DEFAULT_STEPS = (
    ("vibe-selftest", (sys.executable, "-B", "selftest.py"), SCRIPT_DIR),
    ("vibe-runtime-unit", (sys.executable, "-B", "-m", "unittest", "test_runtime_collect",
                            "test_run_state", "test_execute_orca", "test_model_registry",
                            "test_orchestrate", "test_model_watch", "-q"), SCRIPT_DIR),
    ("vibe-prepare-unit", (sys.executable, "-B", "-m", "unittest", "discover", "-s",
                            "tests", "-p", "test_prepare*.py", "-q"), SCRIPT_DIR),
    ("vibe-table-sync", (sys.executable, "-B", "sync_skill_table.py", "--check"), SCRIPT_DIR),
)
CHILD_ENV_KEYS = ("COMSPEC", "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR")


def _copy_verified(source, scratch, receipt):
    scratch.mkdir()
    for member in receipt["files"]:
        name = member["path"]
        blob = r.read_file(r.safe_member(source, name))
        if len(blob) != member["size"] or r.digest(blob) != member["sha256"]:
            raise ValueError("Candidate changed during copy")
        r.write_member(scratch, name, blob, member["mode"])
    r.write_member(scratch, "bundle.json", r.read_file(r.safe_member(source, "bundle.json")), "100644")


def probe(source, digest, *, steps=DEFAULT_STEPS):
    source = r.no_links(Path(source))
    receipt = plugin_bundle.verify_bundle(source, digest)
    env = {key: value for key in CHILD_ENV_KEYS if (value := os.environ.get(key)) is not None}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
    results = []
    try:
        with tempfile.TemporaryDirectory(prefix="simonk-candidate-probe-") as temp:
            scratch = Path(temp) / "candidate"
            _copy_verified(source, scratch, receipt)
            plugin_bundle.verify_bundle(scratch, digest)
            profile = Path(temp) / "profile"
            profile.mkdir()
            env.update(USERPROFILE=str(profile), LOCALAPPDATA=str(profile / "local"),
                       TEMP=str(profile), TMP=str(profile))
            for name, argv, cwd in steps:
                directory = scratch if cwd == "." else r.safe_member(scratch, cwd)
                if not directory.is_dir():
                    raise ValueError(f"Missing probe directory: {name}")
                completed = subprocess.run(argv, cwd=directory, env=env, capture_output=True,
                                           text=True, encoding="utf-8", errors="replace",
                                           timeout=300, check=False)
                results.append({"step": name, "exit_code": completed.returncode})
                if completed.returncode:
                    raise ValueError(f"Probe step failed: {name}")
    finally:
        # Detect concurrent edits to the source even if a test fails. Never write there.
        plugin_bundle.verify_bundle(source, digest)
    return {"status": "candidate_runtime_probe_passed", "steps": results,
            "runtime_closure_verified": False, "host_compatibility_verified": False,
            "installation_ready": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--expected-digest", required=True)
    args = parser.parse_args(argv)
    try:
        result = probe(args.package, args.expected_digest)
    except (ValueError, OSError, subprocess.SubprocessError, KeyError, TypeError, IndexError):
        print('{"status":"blocked","message":"Candidate runtime probe failed"}', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
