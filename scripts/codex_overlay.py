#!/usr/bin/env python3
"""Offline Codex compatibility overlay for a pinned five-plugin candidate.

This copies a verified candidate and adds five Codex compatibility manifests.
It does not install, trust hooks, certify runtime closure, or promote readiness.
"""
from __future__ import annotations

import argparse
import base64
import os
from pathlib import Path
import tempfile

import plugin_bundle as bundle
import skill_release as r

SCOPE = "five-plugin-codex-compat-overlay-v2"
ZOOM_PATH = "plugins/SimonKStack/skills/zoom-out/SKILL.md"
ZOOM_POLICY_PATH = "plugins/SimonKStack/skills/zoom-out/agents/openai.yaml"
MANUAL_FLAG = b"disable-model-invocation: true\n"
ZOOM_POLICY = (b"interface:\n  display_name: Zoom Out\n"
               b"  short_description: One-layer-up code map on explicit request.\n"
               b"policy:\n  allow_implicit_invocation: false\n")
LIMITATIONS = [
    "Compatibility manifests and one manual-only skill policy projection; not a user installation or host load test.",
    "Claude skill-scoped hooks are not projected into Codex lifecycle hooks.",
    "Codex hook trust, runtime closure, model behavior and rollback are unverified.",
    "The pinned candidate receipt authenticates copied bytes, not provider behavior.",
]


def overlay_path(owner):
    if owner not in r.OWNERS:
        raise ValueError("Unknown plugin owner")
    return f"plugins/{owner}/.codex-plugin/plugin.json"


def codex_manifest(owner, source):
    """Generate a narrow compatibility manifest from already verified metadata."""
    suffix = owner.removeprefix("SimonK")
    name = "simonk-" + suffix.lower()
    if (not isinstance(source, dict) or source.get("name") != name
            or not isinstance(source.get("version"), str)
            or not isinstance(source.get("description"), str) or not source["description"].strip()
            or not isinstance(source.get("author"), dict)
            or not isinstance(source["author"].get("name"), str)
            or not source["author"]["name"].strip()):
        raise ValueError("Invalid verified plugin identity")
    title = "SimonK " + suffix
    result = {
        "name": name,
        "version": source["version"],
        "description": source["description"],
        "author": source["author"],
        "skills": "./skills/",
        "interface": {
            "displayName": title,
            "shortDescription": source["description"],
            "longDescription": source["description"],
            "developerName": source["author"]["name"],
            "category": "Productivity",
            "capabilities": [],
            "defaultPrompt": "Use " + title + " skills for this task.",
        },
    }
    for field in ("repository", "license", "keywords", "homepage"):
        if field in source:
            result[field] = source[field]
    return r.encoded(result)


def generated_members(root, candidate_receipt, *, original_zoom=None):
    owners = candidate_receipt["bases"]
    if set(owners) != set(r.OWNERS):
        raise ValueError("Five-plugin ownership differs")
    base_paths = {item["path"] for item in candidate_receipt["files"]}
    generated = {}
    for owner in sorted(r.OWNERS):
        path = overlay_path(owner)
        if path in base_paths:
            raise ValueError("Candidate already owns a Codex compatibility manifest")
        source_path = f"plugins/{owner}/.claude-plugin/plugin.json"
        source = r.decoded(r.read_file(r.safe_member(root, source_path)))
        generated[path] = codex_manifest(owner, source)
    if ZOOM_PATH not in base_paths or ZOOM_POLICY_PATH in base_paths:
        raise ValueError("Zoom-out manual-only source is missing or already projected")
    zoom = original_zoom if original_zoom is not None else r.read_file(r.safe_member(root, ZOOM_PATH))
    if not isinstance(zoom, bytes) or zoom.count(MANUAL_FLAG) != 1:
        raise ValueError("Zoom-out manual-only marker differs")
    frontmatter_end = zoom.find(b"\n---\n", 4)
    marker_offset = zoom.find(MANUAL_FLAG)
    if not zoom.startswith(b"---\n") or frontmatter_end < 0 or marker_offset > frontmatter_end:
        raise ValueError("Zoom-out manual-only marker must be in frontmatter")
    generated[ZOOM_PATH] = zoom.replace(MANUAL_FLAG, b"", 1)
    generated[ZOOM_POLICY_PATH] = ZOOM_POLICY
    return generated


def receipt_for(candidate_digest, generated, original_zoom):
    return {
        "schema_version": 2,
        "scope": SCOPE,
        "candidate_digest": candidate_digest,
        "replacement_originals": {ZOOM_PATH: base64.b64encode(original_zoom).decode("ascii")},
        "generated": {path: {"sha256": r.digest(data), "size": len(data)}
                      for path, data in sorted(generated.items())},
        "host_compatibility_verified": False,
        "installation_ready": False,
        "limitations": LIMITATIONS,
    }


def verify_overlay(root, expected_digest):
    root = r.no_links(root)
    if not isinstance(expected_digest, str) or not r.HEX.fullmatch(expected_digest):
        raise ValueError("A pinned overlay SHA-256 is required")
    data = r.read_file(root / "overlay.json")
    if r.digest(data) != expected_digest:
        raise ValueError("Overlay receipt digest mismatch")
    receipt = r.decoded(data)
    r_keys = {"schema_version", "scope", "candidate_digest", "generated", "replacement_originals",
              "host_compatibility_verified", "installation_ready", "limitations"}
    if (not isinstance(receipt, dict) or set(receipt) != r_keys
            or type(receipt["schema_version"]) is not int or receipt["schema_version"] != 2
            or receipt["scope"] != SCOPE
            or receipt["host_compatibility_verified"] is not False
            or receipt["installation_ready"] is not False
            or receipt["limitations"] != LIMITATIONS or data != r.encoded(receipt)
            or not isinstance(receipt["generated"], dict)
            or not isinstance(receipt["replacement_originals"], dict)):
        raise ValueError("Invalid Codex overlay receipt")
    expected_paths = {overlay_path(owner) for owner in r.OWNERS} | {ZOOM_PATH, ZOOM_POLICY_PATH}
    if set(receipt["generated"]) != expected_paths:
        raise ValueError("Codex projection set differs")
    if set(receipt["replacement_originals"]) != {ZOOM_PATH}:
        raise ValueError("Codex replacement provenance differs")
    encoded_original = receipt["replacement_originals"][ZOOM_PATH]
    if not isinstance(encoded_original, str):
        raise ValueError("Codex replacement provenance differs")
    try:
        original_zoom = base64.b64decode(encoded_original, validate=True)
    except ValueError as exc:
        raise ValueError("Codex replacement provenance differs") from exc
    if base64.b64encode(original_zoom).decode("ascii") != encoded_original:
        raise ValueError("Codex replacement provenance differs")
    candidate = bundle.verify_bundle(root, receipt["candidate_digest"],
                                     allowed_extra=expected_paths - {ZOOM_PATH} | {"overlay.json"},
                                     base_overrides={ZOOM_PATH: original_zoom})
    base_paths = {item["path"] for item in candidate["files"]} | {"bundle.json"}
    if r.files_under(root) != base_paths | expected_paths | {"overlay.json"}:
        raise ValueError("Missing or extra Codex overlay member")
    generated = generated_members(root, candidate, original_zoom=original_zoom)
    if receipt["generated"] != receipt_for(receipt["candidate_digest"], generated,
                                           original_zoom)["generated"]:
        raise ValueError("Codex manifest provenance differs")
    for path, expected in generated.items():
        if r.read_file(r.safe_member(root, path)) != expected:
            raise ValueError("Codex manifest bytes differ")
    return receipt


def build_overlay(candidate, candidate_digest, output):
    candidate = r.no_links(candidate)
    if not isinstance(candidate_digest, str) or not r.HEX.fullmatch(candidate_digest):
        raise ValueError("A pinned candidate SHA-256 is required")
    if r.digest(r.read_file(candidate / "bundle.json")) != candidate_digest:
        raise ValueError("Candidate receipt digest mismatch")
    target = r.destination(output, candidate)
    if os.path.lexists(target):
        raise ValueError("Build never overwrites existing output")
    with r.pinned(candidate, directory=True):
        source = bundle.verify_bundle(candidate, candidate_digest)
        original_zoom = r.read_file(r.safe_member(candidate, ZOOM_PATH))
        generated = generated_members(candidate, source, original_zoom=original_zoom)
        receipt = receipt_for(candidate_digest, generated, original_zoom)
        data = r.encoded(receipt)
        if len(data) > r.MAX_FILE:
            raise ValueError("Overlay receipt exceeds byte limit")
        overlay_digest = r.digest(data)
        members = [(item["path"], item["sha256"], item["size"], item["mode"])
                   for item in source["files"]]
        members.append(("bundle.json", candidate_digest, len(r.read_file(candidate / "bundle.json")), "100644"))
        member_paths = {path for path, _, _, _ in members}
        with r.pinned(target.parent, directory=True):
            stage = Path(tempfile.mkdtemp(prefix=".simonk-codex-overlay-", dir=target.parent))
            with r.pinned(stage, directory=True, delete=True):
                for path, digest, size, mode in members:
                    payload = r.read_file(r.safe_member(candidate, path))
                    if len(payload) != size or r.digest(payload) != digest:
                        raise ValueError("Candidate member changed during overlay construction")
                    r.write_member(stage, path, generated.get(path, payload), mode)
                for path, payload in sorted(generated.items()):
                    if path not in member_paths:
                        r.write_member(stage, path, payload, "100644")
                r.write_member(stage, "overlay.json", data, "100644")
                verify_overlay(stage, overlay_digest)
                r.publish_new(stage, target)
    verify_overlay(target, overlay_digest)
    return {"status": "codex_compat_bytes_verified", "candidate_digest": candidate_digest,
            "overlay_digest": overlay_digest, "plugins": 5, "installation_ready": False,
            "host_compatibility_verified": False, "path": str(target)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--candidate", type=Path, required=True)
    build.add_argument("--candidate-digest", required=True)
    build.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--package", type=Path, required=True)
    verify.add_argument("--overlay-digest", required=True)
    args = parser.parse_args(argv)
    try:
        result = (build_overlay(args.candidate, args.candidate_digest, args.output)
                  if args.command == "build" else
                  {"status": "codex_compat_bytes_verified", "overlay_digest": args.overlay_digest,
                   "installation_ready": verify_overlay(args.package, args.overlay_digest)["installation_ready"]})
        print(r.encoded(result).decode("utf-8"), end="")
        return 0
    except (ValueError, OSError, TypeError, KeyError, IndexError):
        print('{"status":"blocked","reason":"codex_overlay_invalid"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
