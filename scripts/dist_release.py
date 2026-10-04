#!/usr/bin/env python3
"""Monotonic release version and dist-branch staging for the five plugins (D-76).

Release version (what a host compares): ``1.<N>.0`` where N is
``git rev-list --count HEAD`` of the built commit. Every commit added on top of
main raises N, so a later main build always sorts higher; one commit always
builds one version, so a rebuild stays byte-identical; a pin-only change is
itself a main commit (distribution/plugin-inputs.v1.json) and gets a new N.
Content identity is ``release.content_digest`` in bundle.json (plugin_bundle.py):
source + five pins + safety projection + version-normalized output files.

Rollback re-ships older content under a HIGHER version: revert on main, rebuild.
Nothing here pushes. ``gate``, ``decide`` and ``stage`` only prepare the commit
that the workflow's opt-in publish job pushes without force.

Publish approval (D-82) is its own gate, not the D-33 hold: the built commit
must carry ``distribution/dist-publish.allow`` naming a hub decision, the
session-tested candidate commit (an ancestor of the build) and that candidate's
content digest. The hold keeps blocking SessionStart and release.yml; the
repository variable SIMONK_DIST_PUBLISH stays the workflow's other key.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys

EPOCH = 1  # Raise only if main history is ever rewritten and N would go down.
CORE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
HEX40 = re.compile(r"[a-f0-9]{40}\Z")
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
DIST_SCOPE = "five-plugin-dist-v1"
RECORD = "RELEASE.json"
LEGACY_MANIFEST = ".claude-plugin/plugin.json"
OWNERS = {"SimonKAIHub", "SimonKCore", "SimonKDesign", "SimonKMarket", "SimonKStack"}
# Hosts must receive the exact built bytes whatever their core.autocrlf is; Git
# for Windows defaults to autocrlf=true, which would rewrite shell hooks to CRLF.
DIST_ATTRIBUTES = b"* -text\n"
DIST_TOP_LEVEL = {"plugins", RECORD, ".gitattributes"}
RECORD_KEYS = {"schema_version", "scope", "version", "content_digest", "bundle_digest",
               "source_commit", "source_digest", "pins", "codex_overlay_digest",
               "codex_subset_digest", "run"}
# Read from the built commit (git object, not the working tree). Not a build
# input, so committing it leaves the approved content digest unchanged.
ALLOW = "distribution/dist-publish.allow"
ALLOW_KEYS = {"schema_version", "scope", "decision", "source_commit", "content_digest"}
DECISION = re.compile(r"D-[1-9][0-9]*\Z")


def parse_version(value):
    """Strict MAJOR.MINOR.PATCH (no prerelease/build) as a comparable tuple."""
    match = CORE.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise ValueError("Release version must be MAJOR.MINOR.PATCH without prerelease or build metadata")
    return tuple(int(part) for part in match.groups())


def release_version(count, epoch=EPOCH):
    if type(count) is not int or count < 1 or type(epoch) is not int or epoch < 1:
        raise ValueError("Commit count and epoch must be positive integers")
    return f"{epoch}.{count}.0"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                            encoding="utf-8", timeout=120, check=True)
    return result.stdout.strip()


def compute(repo):
    """Release version of the checked-out commit; refuses an undercounted shallow clone."""
    repo = Path(repo)
    if git(repo, "rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("Shallow clone undercounts history; fetch the full history")
    commit = git(repo, "rev-parse", "HEAD")
    count = git(repo, "rev-list", "--count", "HEAD")
    if not HEX40.fullmatch(commit) or not count.isdigit():
        raise ValueError("Unexpected Git commit or count")
    version = release_version(int(count))
    floor = None
    legacy = repo / LEGACY_MANIFEST
    if legacy.is_file():
        floor = json.loads(legacy.read_text(encoding="utf-8")).get("version")
        if parse_version(version) <= parse_version(floor):
            raise ValueError("Release version must sort above the legacy root plugin version")
    return {"version": version, "commit": commit, "commit_count": int(count),
            "epoch": EPOCH, "legacy_floor": floor}


def _digest(value, label):
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise ValueError("Invalid " + label)


def validate_record(record):
    if not isinstance(record, dict) or set(record) != RECORD_KEYS:
        raise ValueError("Invalid dist release record fields")
    if (type(record["schema_version"]) is not int or record["schema_version"] != 1
            or record["scope"] != DIST_SCOPE):
        raise ValueError("Unknown dist release record schema")
    parse_version(record["version"])
    for key in ("content_digest", "bundle_digest", "source_digest",
                "codex_overlay_digest", "codex_subset_digest"):
        _digest(record[key], key)
    pins = record["pins"]
    if (not isinstance(record["source_commit"], str) or not HEX40.fullmatch(record["source_commit"])
            or not isinstance(pins, dict) or set(pins) != OWNERS
            or any(not isinstance(sha, str) or not HEX40.fullmatch(sha) for sha in pins.values())):
        raise ValueError("Invalid source commit or plugin pins")
    if record["run"] is not None and (not isinstance(record["run"], str)
                                      or not record["run"].startswith("https://")):
        raise ValueError("Invalid run reference")
    return record


def _receipt(candidate, bundle_digest):
    _digest(bundle_digest, "bundle digest")
    data = (Path(candidate) / "bundle.json").read_bytes()
    if hashlib.sha256(data).hexdigest() != bundle_digest:
        raise ValueError("bundle.json does not match the verified bundle digest")
    return json.loads(data)


def release_record(candidate, bundle_digest, source_commit, overlay_digest, subset_digest, run=None):
    """RELEASE.json for the dist branch, read from an already verified candidate."""
    receipt = _receipt(candidate, bundle_digest)
    release = receipt.get("release")
    if not isinstance(release, dict) or set(release) != {"version", "content_digest"}:
        raise ValueError("Candidate was not built with a release version")
    return validate_record({
        "schema_version": 1, "scope": DIST_SCOPE,
        "version": release["version"], "content_digest": release["content_digest"],
        "bundle_digest": bundle_digest, "source_commit": source_commit,
        "source_digest": receipt["source_digest"],
        "pins": {owner: info["commit"] for owner, info in receipt["inputs"]["plugins"].items()},
        "codex_overlay_digest": overlay_digest, "codex_subset_digest": subset_digest,
        "run": run,
    })


def decide(previous, current):
    """publish | skip (same content) | refuse (would not raise the dist version)."""
    current = validate_record(current)
    if previous is None:
        return {"action": "publish", "reason": "first-dist-release", "version": current["version"]}
    previous = validate_record(previous)
    if previous["content_digest"] == current["content_digest"]:
        return {"action": "skip", "reason": "identical-content", "version": previous["version"]}
    if parse_version(current["version"]) <= parse_version(previous["version"]):
        # A late or re-run older build. Hosts may ignore a lower version (D-76).
        return {"action": "refuse", "reason": "not-newer-than-dist",
                "version": current["version"], "dist_version": previous["version"]}
    return {"action": "publish", "reason": "new-content", "version": current["version"],
            "dist_version": previous["version"]}


def validate_allow(allow):
    if not isinstance(allow, dict) or set(allow) != ALLOW_KEYS:
        raise ValueError("Invalid dist publish approval fields")
    if (type(allow["schema_version"]) is not int or allow["schema_version"] != 1
            or allow["scope"] != DIST_SCOPE):
        raise ValueError("Unknown dist publish approval schema")
    if not isinstance(allow["decision"], str) or not DECISION.fullmatch(allow["decision"]):
        raise ValueError("Approval must name a hub decision code (D-<n>)")
    if not isinstance(allow["source_commit"], str) or not HEX40.fullmatch(allow["source_commit"]):
        raise ValueError("Invalid approved source commit")
    _digest(allow["content_digest"], "approved content digest")
    return allow


def _is_ancestor(repo, ancestor, commit):
    if git(repo, "rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("Shallow clone cannot place the approved commit; fetch the full history")
    result = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", ancestor, commit],
                            capture_output=True, timeout=120)
    if result.returncode not in (0, 1):
        raise ValueError("Approved source commit is not in this repository")
    return result.returncode == 0


def gate(repo, current):
    """publish | refuse: only content a committed approval names may reach dist (D-82)."""
    current = validate_record(current)
    if git(repo, "rev-parse", "HEAD") != current["source_commit"]:
        raise ValueError("Approval must be read from the built commit")
    shown = subprocess.run(["git", "-C", str(repo), "cat-file", "blob", "HEAD:" + ALLOW],
                           capture_output=True, timeout=120)
    if shown.returncode != 0:
        # Absent from the built commit; an uncommitted local file does not count.
        return {"action": "refuse", "reason": "no-approval", "version": current["version"]}
    allow = validate_allow(json.loads(shown.stdout))
    result = {"decision": allow["decision"], "version": current["version"],
              "approved_source": allow["source_commit"]}
    if allow["content_digest"] != current["content_digest"]:
        return {"action": "refuse", "reason": "content-not-approved", **result}
    if not _is_ancestor(repo, allow["source_commit"], current["source_commit"]):
        return {"action": "refuse", "reason": "source-outside-approval", **result}
    return {"action": "publish", "reason": "approved", **result}


def _member(value):
    path = PurePosixPath(value) if isinstance(value, str) else None
    if (path is None or not value or "\\" in value or ":" in value or path.is_absolute()
            or str(path) != value or any(p in {"", ".", ".."} for p in path.parts)
            or path.parts[0] != "plugins" or len(path.parts) < 3):
        raise ValueError("Unexpected candidate member path")
    return path.parts


def stage(candidate, dist, record):
    """Replace a dist worktree's content with the built plugins; return exec paths."""
    candidate, dist = Path(candidate), Path(dist)
    record = validate_record(record)
    receipt = _receipt(candidate, record["bundle_digest"])
    if not (dist / ".git").is_file():
        # Only a linked worktree (gitfile) is accepted: never wipe a main checkout.
        raise ValueError("Dist target must be a linked Git worktree")
    unexpected = {child.name for child in dist.iterdir()} - DIST_TOP_LEVEL - {".git"}
    if unexpected:
        raise ValueError("Dist worktree holds unexpected top-level entries")
    for child in dist.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    executables = []
    for item in receipt["files"]:
        parts = _member(item["path"])
        data = candidate.joinpath(*parts).read_bytes()
        if len(data) != item["size"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("Candidate member differs from its receipt")
        target = dist.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if item["mode"] == "100755":
            executables.append(item["path"])
    (dist / ".gitattributes").write_bytes(DIST_ATTRIBUTES)
    (dist / RECORD).write_bytes(encoded(record))
    return {"files": len(receipt["files"]), "executables": sorted(executables)}


def _load(path):
    return json.loads(Path(path).read_bytes())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    version = commands.add_parser("version", help="Release version of the checked-out commit")
    version.add_argument("--repo", type=Path, default=Path("."))
    record = commands.add_parser("record", help="Write RELEASE.json from a verified candidate")
    record.add_argument("--candidate", type=Path, required=True)
    record.add_argument("--bundle-digest", required=True)
    record.add_argument("--source-commit", required=True)
    record.add_argument("--overlay-digest", required=True)
    record.add_argument("--subset-digest", required=True)
    record.add_argument("--run")
    record.add_argument("--output", type=Path, required=True)
    approve = commands.add_parser("gate", help="Check the committed dist publish approval (D-82)")
    approve.add_argument("--repo", type=Path, default=Path("."))
    approve.add_argument("--current", type=Path, required=True)
    choose = commands.add_parser("decide", help="Compare with the current dist RELEASE.json")
    choose.add_argument("--current", type=Path, required=True)
    choose.add_argument("--previous", type=Path, help="Omit when the dist branch does not exist")
    place = commands.add_parser("stage", help="Fill a dist worktree from a verified candidate")
    place.add_argument("--candidate", type=Path, required=True)
    place.add_argument("--record", type=Path, required=True)
    place.add_argument("--dist", type=Path, required=True)
    place.add_argument("--executables", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "version":
            result = compute(args.repo)
        elif args.command == "record":
            result = release_record(args.candidate, args.bundle_digest, args.source_commit,
                                    args.overlay_digest, args.subset_digest, args.run)
            with args.output.open("xb") as handle:
                handle.write(encoded(result))
        elif args.command == "gate":
            result = gate(args.repo, _load(args.current))
        elif args.command == "decide":
            previous = _load(args.previous) if args.previous else None
            result = decide(previous, _load(args.current))
        else:
            result = stage(args.candidate, args.dist, _load(args.record))
            with args.executables.open("x", encoding="utf-8", newline="\n") as handle:
                handle.writelines(path + "\n" for path in result["executables"])
        print(encoded(result).decode("utf-8"), end="")
        return 1 if args.command in {"gate", "decide"} and result["action"] == "refuse" else 0
    except ValueError as error:
        print(json.dumps({"status": "blocked", "message": str(error)}), file=sys.stderr)
        return 2
    except (OSError, subprocess.SubprocessError, KeyError, TypeError, AttributeError):
        print('{"status":"blocked","message":"dist release step failed"}', file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
