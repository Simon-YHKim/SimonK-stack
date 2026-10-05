#!/usr/bin/env python3
"""Build a pinned Codex general-skill subset without Claude-only safety controls.

This is an offline candidate projection of a verified Codex v2 overlay. It
neither installs plugins nor claims that Codex enforces safety policies.

Receipt schema 2 (D-88 stage 2):
- ``plugins/<Owner>/.claude-plugin/`` is excluded for all five owners; Codex
  reads ``.codex-plugin/plugin.json`` first.
- The SimonKCore and SimonKStack Codex manifests drop the Claude-only notice
  that plugin_bundle appends (DESCRIPTION_NOTICES) and instead say which
  Claude Code-only safety skills the Codex edition lacks. ``replaced_members``
  keeps each original so ``verify_subset`` re-derives the rewrite.
- ``content_digest`` is the release-version-independent identity of what the
  subset ships (dist_release compares it between releases).
"""
from __future__ import annotations

import argparse
import base64
import os
from pathlib import Path
import tempfile

import codex_overlay
import plugin_bundle as bundle
import skill_release as r

SCOPE = "five-plugin-codex-general-skills-only-v2"
SCHEMA_VERSION = 2
CONTENT_SCOPE = "five-plugin-codex-subset-content-v1"
DECISION_REF = "D-29"
EXCLUDED_SKILLS = (
    ("SimonKCore", "careful"),
    ("SimonKStack", "freeze"),
    ("SimonKStack", "guard"),
    ("SimonKStack", "investigate"),
    ("SimonKCore", "unfreeze"),
)
EXCLUDED_PREFIXES = (tuple(f"plugins/{owner}/skills/{skill}/"
                           for owner, skill in EXCLUDED_SKILLS)
                     + tuple(f"plugins/{owner}/.simonk-runtime/"
                             for owner in ("SimonKCore", "SimonKStack"))
                     + tuple(f"plugins/{owner}/.claude-plugin/"
                             for owner in sorted(r.OWNERS)))
REQUIRED_EXCLUDED_FILES = (tuple(f"plugins/{owner}/skills/{skill}/SKILL.md"
                                 for owner, skill in EXCLUDED_SKILLS)
                           + tuple(f"plugins/{owner}/.simonk-runtime/safety_runtime.py"
                                   for owner in ("SimonKCore", "SimonKStack"))
                           + tuple(f"plugins/{owner}/.claude-plugin/plugin.json"
                                   for owner in sorted(r.OWNERS)))
EXCLUDED_NAMES = tuple(f"simonk-{owner.removeprefix('SimonK').lower()}:{skill}"
                       for owner, skill in EXCLUDED_SKILLS)
# One sentence per owner that loses safety skills, derived from EXCLUDED_SKILLS.
CODEX_NOTICES = {
    owner: ("Codex판에는 Claude Code 전용 안전 스킬("
            + "·".join(skill for home, skill in EXCLUDED_SKILLS if home == owner)
            + ")이 없다.")
    for owner in sorted({home for home, _ in EXCLUDED_SKILLS})
}
# Provenance copied from the source overlay. Not shipped, and both change with
# the release version, so the content digest leaves them out.
PROVENANCE = ("bundle.json", "overlay.json")
LIMITATIONS = [
    "D-29: careful, guard, freeze and investigate are excluded because their Codex policy hooks are not verified.",
    "The dependent Claude-only unfreeze skill and Core/Stack safety runtimes are also excluded; source files remain unchanged.",
    "D-88: Claude manifests (.claude-plugin/) are excluded and the Core/Stack Codex manifests describe the Codex edition.",
    "The subset contains general skills only; it is not a user installation or host behavior test.",
    "The original overlay and all excluded source directories are preserved.",
    "Host skill selection, dependency closure, costs, plugin rollback and safety parity remain unverified.",
]
RECEIPT_NAME = "subset.json"
RECEIPT_KEYS = {"schema_version", "scope", "decision_ref", "source_overlay_digest",
                "excluded_skills", "included_members", "excluded_members", "replaced_members",
                "content_digest", "host_compatibility_verified", "installation_ready",
                "limitations"}
REPLACED_KEYS = {"path", "original_base64", "original_sha256", "original_size",
                 "sha256", "size"}


def _manifest_paths():
    return {codex_overlay.overlay_path(owner) for owner in r.OWNERS}


def _excluded(path):
    return any(path.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def _row(path, payload):
    return {"path": path, "sha256": r.digest(payload), "size": len(payload)}


def _member(source, path):
    return _row(path, r.read_file(r.safe_member(source, path)))


def codex_edition(owner, original):
    """Codex-edition manifest bytes for an owner that loses safety skills (D-88).

    Keeps the plugin's own description and replaces the Claude-only notice that
    plugin_bundle appended with one sentence naming the missing skills, in
    description, interface.shortDescription and interface.longDescription.
    Anything other than the exact projected text fails closed.
    """
    if set(bundle.DESCRIPTION_NOTICES) != set(CODEX_NOTICES) or owner not in CODEX_NOTICES:
        raise ValueError("Claude-only description notices and Codex rewrites differ")
    if not isinstance(original, bytes):
        raise ValueError("Codex manifest bytes are required")
    document = r.decoded(original)
    suffix = ". " + bundle.DESCRIPTION_NOTICES[owner]
    interface = document.get("interface") if isinstance(document, dict) else None
    description = document.get("description") if isinstance(document, dict) else None
    if (not isinstance(interface, dict) or not isinstance(description, str)
            or not description.endswith(suffix)
            or not description[:-len(suffix)].strip()
            or interface.get("shortDescription") != description
            or interface.get("longDescription") != description
            or r.encoded(document) != original):
        raise ValueError("Codex manifest does not carry the expected Claude-only notice")
    text = description[:-len(suffix)] + ". " + CODEX_NOTICES[owner]
    document["description"] = text
    interface["shortDescription"] = text
    interface["longDescription"] = text
    return r.encoded(document)


def _replacement(path, original, payload):
    return {"path": path, "original_base64": base64.b64encode(original).decode("ascii"),
            "original_sha256": r.digest(original), "original_size": len(original),
            "sha256": r.digest(payload), "size": len(payload)}


def content_digest(included, manifests):
    """Release-version-independent identity of what the subset ships (D-88).

    Covers the content scope, the excluded skill names and every shipped
    ``plugins/`` path with its SHA-256 after rewriting. The five Codex
    manifests count with their version field blanked, so two releases of the
    same content share one identity. Provenance receipts are not shipped.
    """
    rows = []
    for item in included:
        path = item["path"]
        if path in PROVENANCE:
            continue
        if not path.startswith("plugins/"):
            raise ValueError("Unexpected subset member outside plugins/")
        sha256 = item["sha256"]
        if path in manifests:
            payload = manifests[path]
            if r.digest(payload) != sha256:
                raise ValueError("Codex manifest differs from its subset row")
            document = r.decoded(payload)
            if not isinstance(document, dict) or not isinstance(document.get("version"), str):
                raise ValueError("Invalid Codex manifest version")
            document["version"] = ""
            sha256 = r.digest(r.encoded(document))
        rows.append({"path": path, "sha256": sha256})
    if (set(manifests) != _manifest_paths()
            or not set(manifests) <= {row["path"] for row in rows}):
        raise ValueError("Codex manifests are missing from the subset")
    return r.digest(r.encoded({"scope": CONTENT_SCOPE, "excluded_skills": list(EXCLUDED_NAMES),
                               "files": rows}))


def _project(source):
    """Inventory a verified overlay and derive the Codex-edition manifests."""
    files = r.files_under(source)
    if RECEIPT_NAME in files:
        raise ValueError("Source already contains a subset receipt")
    for path in REQUIRED_EXCLUDED_FILES:
        if path not in files:
            raise ValueError("Required Claude-only member is absent")
    included_paths = sorted(path for path in files if not _excluded(path))
    excluded = sorted(files - set(included_paths))
    if any(path not in included_paths for path in PROVENANCE):
        raise ValueError("Source provenance receipts are missing")
    if not _manifest_paths() <= set(included_paths):
        raise ValueError("Codex manifest is missing")
    rewritten, replaced = {}, []
    for owner in sorted(CODEX_NOTICES):
        path = codex_overlay.overlay_path(owner)
        original = r.read_file(r.safe_member(source, path))
        rewritten[path] = codex_edition(owner, original)
        replaced.append(_replacement(path, original, rewritten[path]))
    manifests = {path: rewritten[path] if path in rewritten
                 else r.read_file(r.safe_member(source, path))
                 for path in sorted(_manifest_paths())}
    included = [_row(path, rewritten[path]) if path in rewritten else _member(source, path)
                for path in included_paths]
    return (included, [_member(source, path) for path in excluded], replaced, rewritten,
            manifests)


def _receipt(source_digest, included, excluded, replaced, content):
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": SCOPE,
        "decision_ref": DECISION_REF,
        "source_overlay_digest": source_digest,
        "excluded_skills": list(EXCLUDED_NAMES),
        "included_members": included,
        "excluded_members": excluded,
        "replaced_members": replaced,
        "content_digest": content,
        "host_compatibility_verified": False,
        "installation_ready": False,
        "limitations": LIMITATIONS,
    }


def _checked_members(value, *, excluded):
    if not isinstance(value, list) or not value:
        raise ValueError("Invalid subset member list")
    paths = []
    for item in value:
        if (not isinstance(item, dict) or set(item) != {"path", "sha256", "size"}
                or not isinstance(item["path"], str)
                or str(r.relative(item["path"])) != item["path"]
                or not isinstance(item["sha256"], str)
                or not r.HEX.fullmatch(item["sha256"])
                or type(item["size"]) is not int
                or not 0 <= item["size"] <= r.MAX_FILE):
            raise ValueError("Invalid subset member")
        if _excluded(item["path"]) != excluded:
            raise ValueError("Safety-control membership differs")
        paths.append(item["path"])
    if paths != sorted(set(paths)):
        raise ValueError("Subset member order or uniqueness differs")
    return set(paths)


def _checked_replacements(value, rows):
    """Re-derive every recorded rewrite from its recorded original."""
    owners = sorted(CODEX_NOTICES)
    if (not isinstance(value, list) or len(value) != len(owners)
            or any(not isinstance(item, dict) or set(item) != REPLACED_KEYS for item in value)
            or [item["path"] for item in value]
            != [codex_overlay.overlay_path(owner) for owner in owners]):
        raise ValueError("Codex manifest rewrite set differs")
    for owner, item in zip(owners, value):
        encoded_original = item["original_base64"]
        if (not isinstance(encoded_original, str)
                or any(type(item[key]) is not int for key in ("original_size", "size"))):
            raise ValueError("Invalid Codex manifest rewrite record")
        original = base64.b64decode(encoded_original, validate=True)
        if base64.b64encode(original).decode("ascii") != encoded_original:
            raise ValueError("Invalid Codex manifest rewrite record")
        if item["original_sha256"] != r.digest(original) or item["original_size"] != len(original):
            raise ValueError("Codex manifest original differs from its record")
        payload = codex_edition(owner, original)
        row = rows.get(item["path"])
        if (item["sha256"] != r.digest(payload) or item["size"] != len(payload) or row is None
                or row["sha256"] != item["sha256"] or row["size"] != item["size"]):
            raise ValueError("Codex manifest rewrite differs from its original")


def verify_subset(package, expected_digest, source=None, source_digest=None):
    """Verify pinned bytes alone, or additionally prove source-overlay provenance."""
    package = r.no_links(package)
    if not isinstance(expected_digest, str) or not r.HEX.fullmatch(expected_digest):
        raise ValueError("A pinned subset SHA-256 is required")
    data = r.read_file(package / RECEIPT_NAME)
    if r.digest(data) != expected_digest:
        raise ValueError("Subset receipt digest mismatch")
    receipt = r.decoded(data)
    if (not isinstance(receipt, dict) or set(receipt) != RECEIPT_KEYS
            or type(receipt["schema_version"]) is not int
            or receipt["schema_version"] != SCHEMA_VERSION
            or receipt["scope"] != SCOPE or receipt["decision_ref"] != DECISION_REF
            or not isinstance(receipt["source_overlay_digest"], str)
            or not r.HEX.fullmatch(receipt["source_overlay_digest"])
            or not isinstance(receipt["content_digest"], str)
            or not r.HEX.fullmatch(receipt["content_digest"])
            or receipt["excluded_skills"] != list(EXCLUDED_NAMES)
            or receipt["host_compatibility_verified"] is not False
            or receipt["installation_ready"] is not False
            or receipt["limitations"] != LIMITATIONS or data != r.encoded(receipt)):
        raise ValueError("Invalid subset-only receipt")
    included = _checked_members(receipt["included_members"], excluded=False)
    excluded = _checked_members(receipt["excluded_members"], excluded=True)
    for path in REQUIRED_EXCLUDED_FILES:
        if path not in excluded:
            raise ValueError("Missing safety-control omission proof")
    if (any(path not in included for path in PROVENANCE)
            or r.files_under(package) != included | {RECEIPT_NAME}):
        raise ValueError("Missing or extra subset member")
    _checked_replacements(receipt["replaced_members"],
                          {item["path"]: item for item in receipt["included_members"]})
    manifests = {}
    for item in receipt["included_members"]:
        payload = r.read_file(r.safe_member(package, item["path"]))
        if len(payload) != item["size"] or r.digest(payload) != item["sha256"]:
            raise ValueError("Subset member differs from receipt")
        if item["path"] in _manifest_paths():
            manifests[item["path"]] = payload
    if content_digest(receipt["included_members"], manifests) != receipt["content_digest"]:
        raise ValueError("Subset content digest differs")
    if r.digest(r.read_file(package / "overlay.json")) != receipt["source_overlay_digest"]:
        raise ValueError("Copied source-overlay receipt differs")
    if source is None:
        if source_digest is not None:
            raise ValueError("Source pin needs a source directory")
    else:
        source = r.no_links(source)
        if source_digest != receipt["source_overlay_digest"]:
            raise ValueError("Source-overlay pin differs")
        with r.pinned(source, directory=True):
            codex_overlay.verify_overlay(source, source_digest)
            source_included, source_excluded, source_replaced, _, _ = _project(source)
        if (source_included != receipt["included_members"]
                or source_excluded != receipt["excluded_members"]
                or source_replaced != receipt["replaced_members"]):
            raise ValueError("Subset provenance differs from source overlay")
    return receipt


def build_subset(source, source_digest, output):
    source = r.no_links(source)
    if not isinstance(source_digest, str) or not r.HEX.fullmatch(source_digest):
        raise ValueError("A pinned source-overlay SHA-256 is required")
    target = r.destination(output, source)
    if os.path.lexists(target):
        raise ValueError("Build never overwrites existing output")
    with r.pinned(source, directory=True):
        if r.digest(r.read_file(source / "overlay.json")) != source_digest:
            raise ValueError("Source-overlay receipt digest mismatch")
        codex_overlay.verify_overlay(source, source_digest)
        included, excluded, replaced, rewritten, manifests = _project(source)
        content = content_digest(included, manifests)
        receipt_data = r.encoded(_receipt(source_digest, included, excluded, replaced, content))
        if len(receipt_data) > r.MAX_FILE:
            raise ValueError("Subset receipt exceeds byte limit")
        subset_digest = r.digest(receipt_data)
        originals = {item["path"]: item for item in replaced}
        with r.pinned(target.parent, directory=True):
            stage = Path(tempfile.mkdtemp(prefix=".simonk-codex-subset-", dir=target.parent))
            with r.pinned(stage, directory=True, delete=True):
                for item in included:
                    payload = r.read_file(r.safe_member(source, item["path"]))
                    if item["path"] in rewritten:
                        original = originals[item["path"]]
                        if (len(payload) != original["original_size"]
                                or r.digest(payload) != original["original_sha256"]):
                            raise ValueError("Source member changed during subset build")
                        payload = rewritten[item["path"]]
                    if len(payload) != item["size"] or r.digest(payload) != item["sha256"]:
                        raise ValueError("Source member changed during subset build")
                    r.write_member(stage, item["path"], payload, "100644")
                r.write_member(stage, RECEIPT_NAME, receipt_data, "100644")
                verify_subset(stage, subset_digest)
                codex_overlay.verify_overlay(source, source_digest)
                r.publish_new(stage, target)
    verify_subset(target, subset_digest, source, source_digest)
    return {"status": "codex_general_subset_bytes_verified",
            "source_overlay_digest": source_digest, "subset_digest": subset_digest,
            "content_digest": content, "plugins": 5,
            "skills": sum(item["path"].endswith("/SKILL.md") for item in included),
            "excluded_skills": list(EXCLUDED_NAMES), "installation_ready": False,
            "host_compatibility_verified": False, "path": str(target)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--source-overlay", type=Path, required=True)
    build.add_argument("--overlay-digest", required=True)
    build.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--package", type=Path, required=True)
    # --expected-digest matches the other builders' verify commands (dist publish job).
    verify.add_argument("--subset-digest", "--expected-digest", dest="subset_digest", required=True)
    verify.add_argument("--source-overlay", type=Path)
    verify.add_argument("--overlay-digest")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = build_subset(args.source_overlay, args.overlay_digest, args.output)
        else:
            checked = verify_subset(args.package, args.subset_digest,
                                    args.source_overlay, args.overlay_digest)
            result = {"status": "codex_general_subset_bytes_verified",
                      "subset_digest": args.subset_digest,
                      "content_digest": checked["content_digest"],
                      "source_provenance_verified": args.source_overlay is not None,
                      "installation_ready": checked["installation_ready"]}
        print(r.encoded(result).decode("utf-8"), end="")
        return 0
    except (ValueError, OSError, TypeError, KeyError, IndexError):
        print('{"status":"blocked","reason":"codex_subset_invalid"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
