#!/usr/bin/env python3
"""Source-owned overlay builder/verifier. No network, provider calls or home install.

Hash equality covers packaged bytes and portable executable modes, NOT external
dependencies, host skill schema compatibility, behavior or a whole plugin release.
Materialization is an explicit, isolated install.sh path; never a legacy fallback.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import threading

OWNERS = {"SimonKAIHub", "SimonKCore", "SimonKDesign", "SimonKMarket", "SimonKStack"}
SCOPE = "source-owned-overlay-v1"
MAX_FILE = 8 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_FILES = 10000
ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
HEX = re.compile(r"[a-f0-9]{64}\Z")
_PINS = threading.local()
if os.name == "nt":
    _KERNEL = ctypes.WinDLL("kernel32", use_last_error=True)
    _KERNEL.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    _KERNEL.CreateFileW.restype = wintypes.HANDLE
    _KERNEL.CloseHandle.argtypes = [wintypes.HANDLE]
    _KERNEL.GetFileInformationByHandleEx.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    _KERNEL.GetFileType.argtypes = [wintypes.HANDLE]
    _KERNEL.ReadFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p]
    _KERNEL.SetFilePointerEx.argtypes = [wintypes.HANDLE, ctypes.c_longlong, ctypes.c_void_p, wintypes.DWORD]
    _KERNEL.SetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    _KERNEL.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    _KERNEL.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    _KERNEL.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
    _KERNEL.GetDriveTypeW.restype = wintypes.UINT


def local_path(path):
    if os.name != "nt":
        raise ValueError("Guarded package I/O currently supports Windows only")
    path = Path(os.path.abspath(path))
    # Reject UNC/device namespaces before any filesystem inspection/SMB access.
    if not re.fullmatch(r"[A-Za-z]:", path.drive) or _KERNEL.GetDriveTypeW(path.anchor) != 3:
        raise ValueError("Only fixed local Windows drive paths are supported")
    return path


@contextmanager
def pinned(path, directory=False, delete=False, create_dirs=False):
    """Hold a no-reparse Windows ancestor chain; nested operations reuse handles.

    Parent directory sharing denies deletion/rename. A stage gets DELETE access
    from the beginning so its SAME handle can publish it without reopening a name.
    Child file handles close before directory rename (Windows sharing semantics).
    This does not seal a directory against same-user concurrent child additions.
    """
    path = local_path(path)
    pool = getattr(_PINS, "paths", None)
    if pool is None:
        pool = _PINS.paths = {}
    opened = []
    try:
        for part in [*reversed(path.parents), path]:
            key = os.path.normcase(str(part))
            is_dir = part != path or directory
            if key in pool:
                handle, existing_dir, can_delete = pool[key]
                if existing_dir != is_dir or delete and part == path and not can_delete:
                    raise ValueError("Incompatible pinned path use")
                continue
            if create_dirs and is_dir and not os.path.lexists(part):
                part.mkdir()  # Its parent is already pinned; no recursive path traversal.
            access = (0x80 if is_dir else 0x80000000) | (0x10000 if delete and part == path else 0)
            handle = _KERNEL.CreateFileW(str(part), access, 3 if is_dir else 1, None,
                                         3, 0x02000000 | 0x00200000, None)
            if handle == ctypes.c_void_p(-1).value:
                raise ctypes.WinError(ctypes.get_last_error())
            pool[key] = (handle, is_dir, bool(delete and part == path))
            opened.append(key)
            info = (wintypes.DWORD * 2)()
            if not _KERNEL.GetFileInformationByHandleEx(handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
                raise ctypes.WinError(ctypes.get_last_error())
            if info[0] & 0x400 or bool(info[0] & 0x10) != is_dir or _KERNEL.GetFileType(handle) != 1:
                raise ValueError("Opened path is reparse/non-regular or has the wrong type")
            if not is_dir:
                class StandardInfo(ctypes.Structure):
                    _fields_ = [("AllocationSize", ctypes.c_longlong), ("EndOfFile", ctypes.c_longlong),
                                ("NumberOfLinks", wintypes.DWORD), ("DeletePending", ctypes.c_ubyte),
                                ("Directory", ctypes.c_ubyte)]
                standard = StandardInfo()
                if not _KERNEL.GetFileInformationByHandleEx(handle, 1, ctypes.byref(standard), ctypes.sizeof(standard)):
                    raise ctypes.WinError(ctypes.get_last_error())
                if standard.NumberOfLinks != 1:
                    raise ValueError("Hardlinked files are outside the package boundary")
        yield pool[os.path.normcase(str(path))][0]
    finally:
        for key in reversed(opened):
            handle, _, _ = pool.pop(key)
            _KERNEL.CloseHandle(handle)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("Duplicate JSON key")
        out[key] = value
    return out


def no_links(path):
    path = local_path(path)
    for part in [*reversed(path.parents), path]:
        if not os.path.lexists(part):
            continue
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Links/reparse points are outside the package boundary")
    return path


def relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("Invalid relative member path")
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value or any(p in {".", ".."} for p in path.parts):
        raise ValueError("Non-canonical member path")
    for part in path.parts:
        if part.endswith((".", " ")) or any(ord(c) < 32 or c in '<>"|?*' for c in part):
            raise ValueError("Non-portable member name")
        if re.fullmatch(r"(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part, re.I):
            raise ValueError("Reserved member name")
    return path


def safe_member(root, name):
    path = no_links(root / relative(name))
    if not path.is_relative_to(root):
        raise ValueError("Member escapes root")
    return path


def read_file(path, limit=MAX_FILE):
    path = no_links(path)
    with pinned(path) as handle:
        if not _KERNEL.SetFilePointerEx(handle, 0, None, 0):
            raise ctypes.WinError(ctypes.get_last_error())
        buffer = ctypes.create_string_buffer(limit + 1)
        count = wintypes.DWORD()
        if not _KERNEL.ReadFile(handle, buffer, limit + 1, ctypes.byref(count), None):
            raise ctypes.WinError(ctypes.get_last_error())
        data = buffer.raw[:count.value]
    if len(data) > limit:
        raise ValueError("Package member exceeds byte limit")
    return data


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Non-finite JSON numbers are forbidden")
    return number


def reject_constant(value):
    raise ValueError("Non-finite JSON constants are forbidden")


def decoded(data):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=unique_pairs,
                          parse_float=finite_float, parse_constant=reject_constant)
    except RecursionError:
        raise ValueError("JSON nesting exceeds the parser limit") from None


def load_json(path):
    return decoded(read_file(path))


def validate_config(config):
    fields = {"schema_version", "scope", "owners", "development_only", "preserve_unowned",
              "plugin_only_out_of_scope", "external_dependencies"}
    if (not isinstance(config, dict) or set(config) != fields
            or type(config["schema_version"]) is not int or config["schema_version"] != 1):
        raise ValueError("Invalid ownership schema")
    if config["scope"] != SCOPE or config["preserve_unowned"] is not True:
        raise ValueError("Only source-owned preserving overlays are supported")
    owners = config["owners"]
    if not isinstance(owners, dict) or not owners or len(owners) > 1000:
        raise ValueError("Invalid owner mapping")
    if any(not isinstance(n, str) or not NAME.fullmatch(n)
           or not isinstance(owner, str) or owner not in OWNERS for n, owner in owners.items()):
        raise ValueError("Invalid skill name or plugin owner")
    for field in ("development_only", "plugin_only_out_of_scope"):
        names = config[field]
        if not isinstance(names, list) or len(names) > 1000:
            raise ValueError("Invalid excluded-name list")
        if any(not isinstance(n, str) or not NAME.fullmatch(n) for n in names):
            raise ValueError("Invalid excluded skill name")
        if len(set(names)) != len(names):
            raise ValueError("Duplicate excluded skill name")
        if set(names) & set(owners):
            raise ValueError("Owned and excluded skills overlap")
    if not isinstance(config["external_dependencies"], list) or len(config["external_dependencies"]) > 100:
        raise ValueError("Invalid external dependency declarations")
    dependency_names = set()
    for dependency in config["external_dependencies"]:
        if not isinstance(dependency, dict) or set(dependency) != {"name", "status"}:
            raise ValueError("Invalid external dependency fields")
        for field in ("name", "status"):
            value = dependency[field]
            if (not isinstance(value, str) or not value.strip() or len(value) > 4096
                    or value != value.strip() or any(ord(c) < 32 for c in value)):
                raise ValueError("Invalid external dependency text")
        name = dependency["name"].casefold()
        if name in dependency_names:
            raise ValueError("Duplicate external dependency name")
        dependency_names.add(name)
    return config


def skill_names(root):
    if not root.is_dir():
        return set()
    names = set()
    for index, child in enumerate(root.iterdir()):
        if index >= MAX_FILES:
            raise ValueError("Source directory exceeds entry limit")
        no_links(child)
        if child.is_dir() and (child / "SKILL.md").exists():
            no_links(child / "SKILL.md")
            names.add(child.name)
    return names


def forbidden_member(path):
    return any(p.casefold() in {".git", "__pycache__", "node_modules", ".env", "credentials"}
               or p.casefold().startswith(".env.") and p != ".env.example"
               or ".bak" in p.casefold() or p.casefold().endswith(("~", ".pyc", ".sqlite", ".db", ".key", ".pem", ".p12", ".pfx"))
               for p in path.parts)


def collect(repo, config):
    config = validate_config(config)
    repo = no_links(repo)
    roots = {"skills-src": set(config["owners"]), ".claude/skills": set(config["development_only"])}
    for root, names in roots.items():
        if skill_names(no_links(repo / root)) != names:
            raise ValueError("Source inventory is not exactly explained by ownership/development scope")
    p = subprocess.run(["git", "-C", str(repo), "ls-files", "--stage", "-z", "--",
                        "skills-src/", "LICENSE", "NOTICE"], capture_output=True, timeout=30, check=True)
    if len(p.stdout) > 2 * 1024 * 1024:
        raise ValueError("Tracked inventory exceeds limit")
    members, blobs, seen, total = [], {}, set(), 0
    for entry in p.stdout.decode("utf-8").split("\0"):
        if not entry:
            continue
        index_info, source = entry.split("\t", 1)
        mode, _, stage = index_info.split()
        parts = relative(source)
        if mode not in {"100644", "100755"} or stage != "0" or forbidden_member(parts):
            raise ValueError("Unsafe/conflicted tracked member")
        if source == "skills-src/VENDORED.md":
            package, installed = "VENDORED.md", ".simonk-source-release/VENDORED.md"
        elif parts.parts[0] == "skills-src":
            if len(parts.parts) < 3 or parts.parts[1] not in config["owners"]:
                raise ValueError("Tracked source has no owner")
            name = parts.parts[1]
            suffix = "/".join(parts.parts[2:])
            package = f"plugins/{config['owners'][name]}/skills/{name}/{suffix}"
            installed = f"{name}/{suffix}"
        else:
            package, installed = source, ".simonk-source-release/" + source
        if package.casefold() in seen or len(members) >= MAX_FILES:
            raise ValueError("Duplicate/case-colliding or excessive members")
        seen.add(package.casefold())
        data = read_file(safe_member(repo, source), min(MAX_FILE, MAX_TOTAL - total))
        total += len(data)
        if source.endswith("/SKILL.md"):
            text = data.decode("utf-8").replace("\r\n", "\n")
            header = text.split("\n---\n", 1)[0] if text.startswith("---\n") else ""
            names = re.findall(r"(?m)^name:[ \t]*(?:([a-z0-9-]+)|\"([a-z0-9-]+)\"|'([a-z0-9-]+)')[ \t]*$", header)
            if len(names) != 1 or next((n for n in names[0] if n), None) != parts.parts[1]:
                raise ValueError("Skill declaration does not match its owned path")
        blobs[package] = data
        members.append({"source_path": source, "package_path": package, "install_path": installed,
                        "size": len(data), "sha256": digest(data), "mode": mode})
    if sum(len(b) for b in blobs.values()) > MAX_TOTAL:
        raise ValueError("Package exceeds aggregate byte limit")
    if {m["source_path"] for m in members if m["source_path"].endswith("/SKILL.md")} != {
            f"skills-src/{name}/SKILL.md" for name in config["owners"]}:
        raise ValueError("Owned skills must be tracked completely")
    if not {"LICENSE", "NOTICE", "VENDORED.md"}.issubset(blobs):
        raise ValueError("License, notice and vendored attribution must be included")
    manifest = {**config, "full_plugin_build": False, "runtime_closure_verified": False,
                "source_state": "tracked-working-tree-bytes", "files": sorted(members, key=lambda m: m["package_path"])}
    return manifest, blobs


def canonical_directory(path):
    with pinned(path, directory=True) as handle:
        buffer = ctypes.create_unicode_buffer(32768)
        count = _KERNEL.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
        if not count or count >= len(buffer):
            raise ValueError("Cannot determine a pinned canonical directory")
        name = buffer.value
        if name.startswith("\\\\?\\"):
            name = name[4:]
        return local_path(name)


def destination(path, *protected):
    raw = Path(path)
    if not raw.is_absolute():
        raise ValueError("An explicit absolute isolated target is required")
    path = no_links(raw)
    reserved = {".claude", ".codex", ".agents", "simonk-plugins", "gstack"}
    if any(p.casefold() in reserved for p in path.parts):
        raise ValueError("Live/protected installation roots are forbidden")
    parent = canonical_directory(path.parent)
    path = canonical_directory(path) if os.path.lexists(path) else parent / path.name
    if any(p.casefold() in reserved for p in path.parts):
        raise ValueError("Live/protected installation roots are forbidden")
    canonical_inputs = [canonical_directory(root) for root in protected]
    canonical_root = canonical_directory(ROOT)
    for root in (canonical_directory(Path.home()), canonical_root, *canonical_inputs):
        if path == root or root.is_relative_to(path):
            raise ValueError("Root/ancestor target is forbidden")
    if any(path.is_relative_to(root) for root in [canonical_root, *canonical_inputs]):
        raise ValueError("Input/output roots must not overlap")
    if not path.parent.is_dir():
        raise ValueError("Target parent must already exist")
    return path


def publish_new(stage, target):
    """Same pinned stage handle, pinned parent, atomic Windows no-replace rename."""
    no_links(target.parent)
    if stage.parent != target.parent:
        raise ValueError("Publication must remain inside one pinned parent")
    with pinned(target.parent, directory=True), pinned(stage, directory=True, delete=True) as handle:
        if os.path.lexists(target):
            raise ValueError("Target already exists")
        name = str(target)
        name_bytes = name.encode("utf-16-le")
        class RenameInfo(ctypes.Structure):
            _fields_ = [("ReplaceIfExists", ctypes.c_ubyte), ("RootDirectory", wintypes.HANDLE),
                        ("FileNameLength", wintypes.DWORD), ("FileName", wintypes.WCHAR * (len(name_bytes) // 2 + 1))]
        info = RenameInfo()
        info.ReplaceIfExists = 0
        info.RootDirectory = None
        info.FileNameLength = len(name_bytes)
        info.FileName = name
        if not _KERNEL.SetFileInformationByHandle(handle, 3, ctypes.byref(info), ctypes.sizeof(info)):
            raise ctypes.WinError(ctypes.get_last_error())


def write_member(root, name, data, mode):
    path = safe_member(root, name)
    with pinned(path.parent, directory=True, create_dirs=True):
        with path.open("xb") as handle:
            handle.write(data)
        # Windows cannot apply POSIX execute bits. Keep Git mode in the manifest;
        # never reopen a written path for chmod (which could follow a replaced link).


def build_release(repo, config, output):
    repo = no_links(repo)
    target = destination(output, repo)
    if os.path.lexists(target):
        raise ValueError("Build never overwrites existing output")
    with pinned(repo, directory=True):
        manifest, blobs = collect(repo, config)
    data = encoded(manifest)
    release = digest(data)
    with pinned(target.parent, directory=True):
        stage = Path(tempfile.mkdtemp(prefix=".simonk-build-", dir=target.parent))
        with pinned(stage, directory=True, delete=True):
            for member in manifest["files"]:
                write_member(stage, member["package_path"], blobs[member["package_path"]], member["mode"])
            write_member(stage, "release.json", data, "100644")
            verify_release(stage, release)
            publish_new(stage, target)
        verify_release(target, release)
    return {"status": "staged_release_verified", "scope": SCOPE, "release_digest": release,
            "skills": len(config["owners"]), "files": len(manifest["files"]), "path": str(target)}


def files_under(root):
    found = set()
    entries = 0
    def visit(parent):
        nonlocal entries
        with pinned(parent, directory=True), os.scandir(parent) as children:
            for child in children:
                entries += 1
                if entries > MAX_FILES:
                    raise ValueError("Package entry limit exceeded")
                path = no_links(Path(child.path))
                if child.is_dir(follow_symlinks=False):
                    visit(path)
                else:
                    with pinned(path):
                        found.add(path.relative_to(root).as_posix())
    visit(root)
    return found


def validate_manifest(m):
    fields = {"schema_version", "scope", "owners", "development_only", "preserve_unowned",
              "plugin_only_out_of_scope", "external_dependencies"}
    if not isinstance(m, dict) or set(m) != fields | {"full_plugin_build", "runtime_closure_verified", "source_state", "files"}:
        raise ValueError("Invalid release manifest")
    validate_config({key: m[key] for key in fields})
    if m["full_plugin_build"] is not False or m["runtime_closure_verified"] is not False:
        raise ValueError("Unsupported completeness claim")
    if m["source_state"] != "tracked-working-tree-bytes":
        raise ValueError("Unsupported source provenance claim")
    if not isinstance(m["files"], list) or not 1 <= len(m["files"]) <= MAX_FILES:
        raise ValueError("Invalid release members")
    seen_package, seen_install, skills = set(), set(), set()
    for f in m["files"]:
        if not isinstance(f, dict) or set(f) != {"source_path", "package_path", "install_path", "sha256", "size", "mode"}:
            raise ValueError("Invalid file record")
        source = relative(f["source_path"])
        for key, seen in (("package_path", seen_package), ("install_path", seen_install)):
            value = str(relative(f[key]))
            if value.casefold() in seen:
                raise ValueError("Duplicate/case-colliding member")
            seen.add(value.casefold())
        if (not isinstance(f["sha256"], str) or not HEX.fullmatch(f["sha256"])
                or type(f["size"]) is not int or not 0 <= f["size"] <= MAX_FILE
                or not isinstance(f["mode"], str) or f["mode"] not in {"100644", "100755"}):
            raise ValueError("Invalid file hash/size/mode")
        if f["source_path"] == "skills-src/VENDORED.md":
            package, installed = "VENDORED.md", ".simonk-source-release/VENDORED.md"
        elif source.parts[0] == "skills-src" and len(source.parts) >= 3:
            name = source.parts[1]
            if name not in m["owners"] or forbidden_member(source):
                raise ValueError("Unowned/unsafe file")
            suffix = "/".join(source.parts[2:])
            package = f"plugins/{m['owners'][name]}/skills/{name}/{suffix}"
            installed = f"{name}/{suffix}"
            if suffix == "SKILL.md":
                skills.add(name)
        elif f["source_path"] in {"LICENSE", "NOTICE"}:
            package, installed = f["source_path"], ".simonk-source-release/" + f["source_path"]
        else:
            raise ValueError("Unsupported source scope")
        if (f["package_path"], f["install_path"]) != (package, installed):
            raise ValueError("Member paths do not match ownership")
    if skills != set(m["owners"]) or not {"license", "notice", "vendored.md"}.issubset(seen_package):
        raise ValueError("Incomplete skill/license membership")
    if sum(f["size"] for f in m["files"]) > MAX_TOTAL:
        raise ValueError("Release exceeds aggregate byte limit")


def check_members(root, manifest, key):
    for f in manifest["files"]:
        path = safe_member(root, f[key])
        data = read_file(path)
        if len(data) != f["size"] or digest(data) != f["sha256"]:
            raise ValueError("Member bytes differ from the pinned release")
        if os.name != "nt" and bool(path.stat().st_mode & 0o111) != (f["mode"] == "100755"):
            raise ValueError("Executable mode differs from the pinned release")


def verify_release(root, expected_digest):
    root = no_links(root)
    with pinned(root, directory=True):
        return _verify_release(root, expected_digest)


def _verify_release(root, expected_digest):
    if not isinstance(expected_digest, str) or not HEX.fullmatch(expected_digest):
        raise ValueError("A pinned release SHA-256 is required")
    data = read_file(root / "release.json")
    if digest(data) != expected_digest:
        raise ValueError("Release manifest digest mismatch")
    manifest = decoded(data)
    validate_manifest(manifest)
    if data != encoded(manifest):
        raise ValueError("Release manifest must use the builder's canonical JSON bytes")
    if files_under(root) != {f["package_path"] for f in manifest["files"]} | {"release.json"}:
        raise ValueError("Missing or extra package files")
    check_members(root, manifest, "package_path")
    return manifest


def verify_target(target, manifest, release):
    with pinned(target, directory=True):
        return _verify_target(target, manifest, release)


def _verify_target(target, manifest, release):
    data = read_file(target / ".simonk-source-release/release.json")
    if digest(data) != release:
        raise ValueError("Target belongs to a different release")
    expected = {f["install_path"] for f in manifest["files"]} | {".simonk-source-release/release.json"}
    found = set()
    for name in [*manifest["owners"], ".simonk-source-release"]:
        owned = no_links(target / name)
        found.update(f"{name}/{rel}" for rel in files_under(owned))
    if found != expected:
        raise ValueError("Missing or extra owned target files")
    check_members(target, manifest, "install_path")


def materialize(bundle, target, expected_digest, apply=False):
    bundle = no_links(bundle)
    target = destination(target, bundle)
    manifest = verify_release(bundle, expected_digest)
    result = {"scope": SCOPE, "release_digest": expected_digest, "target": str(target),
              "skills": len(manifest["owners"]), "files": len(manifest["files"]),
              "runtime_closure_verified": False, "mode_verified": os.name != "nt"}
    if target.exists():
        if not (target / ".simonk-source-release/release.json").is_file():
            raise ValueError("Unmanaged target; no overwrite/migration is authorized")
        verify_target(target, manifest, expected_digest)
        return {**result, "status": "existing_verified"}
    if not apply:
        return {**result, "status": "preview"}
    with pinned(target.parent, directory=True):
        stage = Path(tempfile.mkdtemp(prefix=".simonk-materialize-", dir=target.parent))
        with pinned(stage, directory=True, delete=True):
            for f in manifest["files"]:
                data = read_file(safe_member(bundle, f["package_path"]))
                if digest(data) != f["sha256"]:
                    raise ValueError("Package changed before materialization")
                write_member(stage, f["install_path"], data, f["mode"])
            write_member(stage, ".simonk-source-release/release.json", encoded(manifest), "100644")
            verify_target(stage, manifest, expected_digest)
            publish_new(stage, target)
        verify_target(target, manifest, expected_digest)
    return {**result, "status": "materialized_verified"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--repo", type=Path, required=True)
    build.add_argument("--ownership", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify")
    install = commands.add_parser("materialize")
    for command in (verify, install):
        command.add_argument("--package", "--offline-package", dest="package", type=Path, required=True)
        command.add_argument("--expected-digest", required=True)
    install.add_argument("--target", type=Path, required=True)
    install.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = build_release(args.repo, load_json(args.ownership), args.output)
        elif args.command == "verify":
            m = verify_release(args.package, args.expected_digest)
            result = {"status": "staged_release_verified", "release_digest": args.expected_digest,
                      "skills": len(m["owners"]), "files": len(m["files"]), "scope": SCOPE}
        else:
            result = materialize(args.package, args.target, args.expected_digest, args.apply)
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError, UnicodeError, TypeError, KeyError) as exc:
        # Do not echo untrusted file contents, native stderr or secrets.
        print(json.dumps({"status": "blocked", "error_type": type(exc).__name__,
                          "message": str(exc) if isinstance(exc, ValueError) else "Package operation failed"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
