#!/usr/bin/env python3
"""Offline five-plugin CANDIDATE, not an installer or a runtime compatibility test.

Pinned Git commit/tree objects authenticate the tracked path/mode/blob inventory,
NOT copied bytes: those are raw working-tree snapshots, not blob attestation.
Excluded payload is not read/copied by the packager; Git status may hash it.
Keep the full receipt SHA-256 separately. It is not a signature.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import ExitStack
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import skill_release as r

SCOPE = "five-plugin-candidate-v1"
SAFETY_SCOPE = "five-plugin-candidate-safety-v2"
OID = re.compile(r"[a-f0-9]{40}\Z")
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")
PLUGIN = ".claude-plugin/plugin.json"
MARKET = ".claude-plugin/marketplace.json"
ROOT_DOCS = {"LICENSE", "NOTICE", "README.md", "CHANGELOG.md", "CONTRIBUTING.md", "RELEASING.md"}
LIMITATIONS = [
    "Candidate only; prerelease metadata is not an installation guard.",
    "Git commit/tree proves inventory only; raw working-tree bytes are not blob attestation.",
    "External runtime dependencies and model/Bot behavior are not verified.",
    "Cross-plugin sibling paths (including guard -> careful) need runtime adapters.",
    "Claude hooks and disable-model-invocation remain unchanged; Codex policy compatibility is unverified.",
    "Single writer required; directory pins do not prevent concurrent child additions.",
    "Local Git metadata/config is trusted single-writer input; worktree traversal is no-follow and pinned.",
    "Windows records portable Git mode; physical POSIX executable mode is not verified.",
]
SAFETY_LIMITATIONS = [
    *LIMITATIONS[:3],
    "Selected safety commands/resources are an explicit projection, not source-exact copies.",
    "Native hook startup, interpreter availability and Codex policies are unverified.",
    *LIMITATIONS[5:],
    "Session state is a same-user namespace, not authentication; trusted single writer required.",
    "Setup rendering accepts only genuine one-line Windows paths and host session IDs.",
]
SAFETY_DOCS = {
    "careful": "plugins/SimonKCore/skills/careful/SKILL.md",
    "freeze": "plugins/SimonKStack/skills/freeze/SKILL.md",
    "guard": "plugins/SimonKStack/skills/guard/SKILL.md",
    "investigate": "plugins/SimonKStack/skills/investigate/SKILL.md",
    "unfreeze": "plugins/SimonKCore/skills/unfreeze/SKILL.md",
    "detail": "plugins/SimonKStack/skills/investigate/references/detail.md",
}
SAFETY_RESOURCES = {
    "careful/bin/check-careful.sh": "plugins/SimonKCore/skills/careful/bin/check-careful.sh",
    "careful/bin/hook-extract.sh": "plugins/SimonKCore/skills/careful/bin/hook-extract.sh",
    "freeze/bin/check-freeze.sh": "plugins/SimonKStack/skills/freeze/bin/check-freeze.sh",
    "safety_runtime.py": "plugins/SimonKStack/skills/freeze/bin/safety_runtime.py",
}
SAFETY_INPUTS = set(SAFETY_DOCS.values()) | set(SAFETY_RESOURCES.values())


def replace_exact(text, old, new, count=1):
    if text.count(old) != count:
        raise ValueError("Safety projection input drift; review required")
    return text.replace(old, new)


def safety_setup(action):
    """Static shell program; substituted one-line Windows values are DATA only.

    No claim that a malicious heredoc delimiter is made safe by a later Python
    check. Host values must satisfy the documented one-line Windows contract.
    """
    if action not in {"set", "clear"}:
        raise ValueError("Unknown safety setup action")
    count = 4 if action == "set" else 3
    code = ('import ctypes,os,pathlib,runpy,sys; rows=sys.stdin.read(32769).splitlines(); '
            f'len(rows)=={count} or sys.exit(2); '
            'root=pathlib.Path(rows[0]); '
            '(os.name=="nt" and root.is_absolute() and len(root.drive)==2 '
            'and root.drive[0].isascii() and root.drive[0].isalpha() '
            'and root.drive[1]==":") or sys.exit(2); '
            'ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(root.anchor))==3 or sys.exit(2); '
            'target=root/".simonk-runtime"/"safety_runtime.py"; '
            f'sys.argv=[str(target),"{action}","--project",rows[1],"--session",rows[2]]'
            + ('+["--boundary",rows[3]]' if action == "set" else '')
            + '; runpy.run_path(str(target),run_name="__main__")')
    values = '${CLAUDE_PLUGIN_ROOT}\n${CLAUDE_PROJECT_DIR}\n${CLAUDE_SESSION_ID}\n'
    if action == "set":
        values += '<absolute-existing-Windows-directory>\n'
    return ("```bash\npython -B -c '" + code + "' <<'SIMONK_SAFETY_INPUT'\n"
            + values + "SIMONK_SAFETY_INPUT\n```\n")


def safety_document(name, data):
    """Version 1 fixed transformations; never execute a candidate transformer."""
    raw = data.decode("utf-8")
    eol = "\r\n" if "\r\n" in raw else "\n"
    if ("\r" in raw.replace("\r\n", "")
            or eol == "\r\n" and "\n" in raw.replace("\r\n", "")):
        raise ValueError("Safety projection requires consistent source line endings")
    text = raw.replace("\r\n", "\n")
    commands = {
        "careful": [("bin/check-careful.sh", "careful", 1)],
        "freeze": [("bin/check-freeze.sh", "freeze", 2)],
        "guard": [("../careful/bin/check-careful.sh", "careful", 1),
                  ("../freeze/bin/check-freeze.sh", "freeze", 2)],
        "investigate": [("../freeze/bin/check-freeze.sh", "freeze", 2)],
    }
    for relative, kind, count in commands.get(name, []):
        old = '          command: "bash ${CLAUDE_SKILL_DIR}/' + relative + '"'
        args = ["-B", "${CLAUDE_PLUGIN_ROOT}/.simonk-runtime/safety_runtime.py",
                "check", kind, "--project", "${CLAUDE_PROJECT_DIR}"]
        new = '          command: "python"\n          args: ' + json.dumps(args)
        text = replace_exact(text, old, new, count)
    setup_note = ("Use only an existing, one-line absolute Windows directory. Replace the\n"
                  "boundary placeholder in the raw-data block below; do not paste arbitrary\n"
                  "multi-line text or shell code. Leave host placeholders for the host to render.\n"
                  "If the launcher fails, STOP: do not report that the boundary is active.\n\n")
    if name in {"freeze", "guard"}:
        old = '''1. Resolve it to an absolute path:
```bash
FREEZE_DIR=$(cd "<user-provided-path>" 2>/dev/null && pwd)
echo "$FREEZE_DIR"
```

2. Ensure trailing slash and save to the freeze state file:
```bash
FREEZE_DIR="${FREEZE_DIR%/}/"
STATE_DIR="${CLAUDE_PLUGIN_DATA:-$HOME/.gstack}"
mkdir -p "$STATE_DIR"
echo "$FREEZE_DIR" > "$STATE_DIR/freeze-dir.txt"
echo "Freeze boundary set: $FREEZE_DIR"
```
'''
        text = replace_exact(text, old, setup_note + safety_setup("set"))
    if name == "guard":
        text = replace_exact(text,
            '**Dependency note:** This skill references hook scripts from the sibling `/careful`\n'
            'and `/freeze` skill directories. Both must be installed (they are installed together\n'
            'by the gstack setup script).',
            '**Candidate dependency:** This plugin carries reviewed safety runtime resources.\n'
            'Python and Git Bash are required; native host activation remains unverified.')
    if name == "unfreeze":
        old = '''```bash
STATE_DIR="${CLAUDE_PLUGIN_DATA:-$HOME/.gstack}"
if [ -f "$STATE_DIR/freeze-dir.txt" ]; then
  PREV=$(cat "$STATE_DIR/freeze-dir.txt")
  rm -f "$STATE_DIR/freeze-dir.txt"
  echo "Freeze boundary cleared (was: $PREV). Edits are now allowed everywhere."
else
  echo "No freeze boundary was set."
fi
```
'''
        text = replace_exact(text, old, safety_setup("clear"))
        text = replace_exact(text,
            'session — they will just allow everything since no state file exists. To re-freeze,',
            'session — only an explicit inactive tombstone permits edits. Missing state denies. To re-freeze,')
    if name == "investigate":
        header, body = text.split("\n---\n", 1)
        text = (header + "\n---\n\n## Candidate session scope commands\n\n"
                + setup_note + "For Scope Lock in references/detail.md, use this rendered set command:\n\n"
                + safety_setup("set")
                + "\nIf scope is explicitly skipped, record an inactive tombstone with this command:\n\n"
                + safety_setup("clear")
                + "\nDo not run both: choose set or explicit skip. Missing/broken state denies edits.\n"
                + body)
    if name == "detail":
        old = '''```bash
[ -x "${CLAUDE_SKILL_DIR}/../freeze/bin/check-freeze.sh" ] && echo "FREEZE_AVAILABLE" || echo "FREEZE_UNAVAILABLE"
```

**If FREEZE_AVAILABLE:** Identify the narrowest directory containing the affected files. Write it to the freeze state file:

```bash
STATE_DIR="${CLAUDE_PLUGIN_DATA:-$HOME/.gstack}"
mkdir -p "$STATE_DIR"
echo "<detected-directory>/" > "$STATE_DIR/freeze-dir.txt"
echo "Debug scope locked to: <detected-directory>/"
```

Substitute `<detected-directory>` with the actual directory path (e.g., `src/auth/`). Tell the user: "Edits restricted to `<dir>/` for this debug session. This prevents changes to unrelated code. Run `/unfreeze` to remove the restriction."

If the bug spans the entire repo or the scope is genuinely unclear, skip the lock and note why.

**If FREEZE_UNAVAILABLE:** Skip scope lock. Edits are unrestricted.'''
        text = replace_exact(text, old,
            'Identify the narrowest existing directory containing the affected files.\n'
            'Use the **Candidate session scope commands** already rendered in this skill\'s\n'
            'SKILL.md, choosing set with that absolute directory. Do not execute unexpanded\n'
            'host placeholders from a supporting file read via Read.\n\n'
            'If the scope is genuinely unclear, explain why and use the explicit skip/clear\n'
            'command in SKILL.md. A missing/broken runtime does NOT imply unrestricted edits.\n'
            'On any launcher failure, stop and report that scope protection is not confirmed.')
    return text.replace("\n", eol).encode("utf-8")


def project_safety(source, projection, files, generated, add):
    exact(projection, {"version", "originals"}, "safety projection")
    if type(projection["version"]) is not int or projection["version"] != 1:
        raise ValueError("Unknown safety transformation version")
    exact(projection["originals"], SAFETY_INPUTS, "safety original inputs")
    source_files = {f["package_path"]: f for f in source["files"]}
    originals = {}
    for path, encoded in projection["originals"].items():
        if path not in source_files:
            raise ValueError("Safety source input is missing")
        data = unbase64(encoded)
        item = source_files[path]
        if len(data) != item["size"] or r.digest(data) != item["sha256"]:
            raise ValueError("Safety original differs from approved source")
        originals[path] = data
    for name, path in SAFETY_DOCS.items():
        data = safety_document(name, originals[path])
        generated[path] = data
        files[path] = content_record(path, data, source_files[path]["mode"], "generated", path)
    for owner in ("SimonKCore", "SimonKStack"):
        for relative, original in SAFETY_RESOURCES.items():
            path = f"plugins/{owner}/.simonk-runtime/{relative}"
            data = originals[original]
            generated[path] = data
            add(content_record(path, data, source_files[original]["mode"], "generated", original))


def exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError("Invalid " + label + " fields")


def validate_inputs(inputs):
    exact(inputs, {"schema_version", "plugins"}, "plugin inputs")
    if type(inputs["schema_version"]) is not int or inputs["schema_version"] != 1:
        raise ValueError("Invalid plugin input version")
    exact(inputs["plugins"], r.OWNERS, "five plugin inputs")
    for owner, info in inputs["plugins"].items():
        exact(info, {"name", "commit"}, "plugin input")
        if (info["name"] != "simonk-" + owner.removeprefix("SimonK").lower()
                or not isinstance(info["commit"], str) or not OID.fullmatch(info["commit"])):
            raise ValueError("Invalid pinned plugin identity")


def git_bytes(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(GIT_NO_LAZY_FETCH="1", GIT_ALLOW_PROTOCOL="", GIT_TERMINAL_PROMPT="0",
               GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_SYSTEM="NUL", GIT_CONFIG_GLOBAL="NUL", GIT_ATTR_NOSYSTEM="1")
    result = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
                             "-c", "core.attributesFile=NUL", "-c", "core.excludesFile=NUL",
                             "-C", str(root), *args], capture_output=True, timeout=30, check=True, env=env)
    if len(result.stdout) > 2 * 1024 * 1024:
        raise ValueError("Git metadata exceeds limit")
    return result.stdout


def git(root, *args):
    return git_bytes(root, *args).decode("utf-8")


def git_oid(kind, data):
    # SHA-1 is Git's object identifier here, not a new security/signature scheme.
    return hashlib.sha1(kind.encode("ascii") + b" " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def tree_oid(records):
    tree = {}
    for item in records:
        parts = r.relative(item["path"]).parts
        node = tree
        for name in parts[:-1]:
            child = node.setdefault(name, {})
            if not isinstance(child, dict):
                raise ValueError("Git file/directory prefix collision")
            node = child
        if parts[-1] in node:
            raise ValueError("Duplicate Git tree path")
        node[parts[-1]] = (item["mode"], item["git_blob"])
    def compute(node):
        entries = []
        for name, value in node.items():
            directory = isinstance(value, dict)
            mode, oid = ("40000", compute(value)) if directory else value
            key = name.encode("utf-8")
            entries.append((key + (b"/" if directory else b""), mode.encode("ascii") + b" " + key + b"\0" + bytes.fromhex(oid)))
        return git_oid("tree", b"".join(data for _, data in sorted(entries)))
    return compute(tree)


def unbase64(value):
    if not isinstance(value, str):
        raise ValueError("Invalid provenance encoding")
    try:
        data = base64.b64decode(value, validate=True)
    except ValueError:
        raise ValueError("Invalid provenance encoding") from None
    if base64.b64encode(data).decode("ascii") != value:
        raise ValueError("Non-canonical provenance encoding")
    return data


def check_base(root, commit):
    actual = r.canonical_directory(Path(git(root, "rev-parse", "--show-toplevel").strip()))
    if actual != r.canonical_directory(root):
        raise ValueError("Plugin input must be its own repository root")
    if (git(root, "rev-parse", "HEAD").strip() != commit
            or git(root, "status", "--porcelain=v1", "--untracked-files=no").strip()):
        raise ValueError("Plugin base HEAD differs or working tree is dirty")


def check_config(data):
    # Deliberately narrow physical-line grammar. Generic INI parsers treat an
    # indented [filter]/[include]/worktree as a continuation; Git does not.
    section = None
    for raw in data.decode("utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.endswith("\\"):
            raise ValueError("Multiline Git config is outside this contract")
        header = re.fullmatch(r'\[([A-Za-z0-9-]+)(?:[ \t]+"[^"\\]*"|\.[A-Za-z0-9._-]+)?\][ \t]*(?:[#;].*)?', line)
        if header:
            section = header[1].casefold()
            if section in {"include", "includeif", "filter"}:
                raise ValueError("External Git includes/filters are forbidden")
            continue
        option = re.fullmatch(r"([A-Za-z][A-Za-z0-9-]*)[ \t]*(?:=[ \t]*.*)?", line)
        if not section or not option:
            raise ValueError("Unsupported local Git config syntax")
        if section == "core" and option[1].casefold() == "worktree":
            raise ValueError("Redirected Git worktree is forbidden")


def pin_snapshot(root, stack):
    """No Git worktree scan before no-follow pins; untracked files fail too."""
    stack.enter_context(r.pinned(root, directory=True))
    metadata = root / ".git"
    stack.enter_context(r.pinned(metadata, directory=True))  # no linked worktrees/gitfiles
    for name in ("config", "index", "HEAD"):
        stack.enter_context(r.pinned(metadata / name))
    for name in ("commondir", "config.worktree", "objects/info/alternates"):
        if os.path.lexists(metadata / name):
            raise ValueError("Indirect Git metadata is outside this candidate contract")
    check_config(r.read_file(metadata / "config"))
    files, count = set(), 0
    def visit(parent):
        nonlocal count
        with os.scandir(parent) as entries:
            for entry in entries:
                if parent == root and entry.name == ".git":
                    continue
                count += 1
                if count > r.MAX_FILES:
                    raise ValueError("Base working tree exceeds entry limit")
                path = r.no_links(Path(entry.path))
                directory = entry.is_dir(follow_symlinks=False)
                stack.enter_context(r.pinned(path, directory=directory))
                if directory:
                    visit(path)
                else:
                    files.add(path.relative_to(root).as_posix())
    visit(root)
    return files


def classify(owner, path, paths, source):
    parts = r.relative(path).parts
    if owner == "SimonKAIHub" and parts[0] == "legacy":
        return "excluded", "inactive-legacy"
    if parts[0] == "skills" and len(parts) >= 3:
        name = parts[1]
        if not r.NAME.fullmatch(name):
            raise ValueError("Invalid base skill name")
        if name in source["owners"]:
            if source["owners"][name] != owner:
                raise ValueError("Source-owned skill is in the wrong plugin")
            member = f"plugins/{owner}/{path}"
            if member not in {f["package_path"] for f in source["files"]}:
                raise ValueError("Source-owned directory has unexplained supplementary files")
            return "replaced", "source-owned-exact"
        if name not in source["plugin_only_out_of_scope"]:
            raise ValueError("Base skill is not declared plugin-only")
        if len(parts) >= 5 and parts[-2] == "__pycache__" and path.endswith(".pyc"):
            match = re.fullmatch(r"(.+)\.cpython-[0-9]+(?:\.opt-[0-9]+)?\.pyc", parts[-1])
            paired = "/".join(parts[:-2]) + "/" + match[1] + ".py" if match else None
            if paired not in paths:
                raise ValueError("Generated cache has no tracked Python source")
            return "excluded", "nonportable-python-cache"
        if r.forbidden_member(r.relative(path)):
            raise ValueError("Unsafe plugin-only member")
        return "copied", "plugin-only"
    if path in {PLUGIN, MARKET}:
        return "transformed", "candidate-metadata"
    if path in ROOT_DOCS or parts[0] in {".github", "agents", "commands"} and len(parts) >= 2:
        if r.forbidden_member(r.relative(path)):
            raise ValueError("Unsafe base component")
        return "copied", "official-component"
    raise ValueError("Unclassified base path")


def collect_base(root, info, owner, source, actual_files):
    if git(root, "rev-parse", "HEAD").strip() != info["commit"]:
        raise ValueError("Plugin base HEAD differs from pinned input")
    tree = git(root, "rev-parse", info["commit"] + "^{tree}").strip()
    records = []
    for entry in git(root, "ls-tree", "-r", "-z", info["commit"]).split("\0"):
        if not entry:
            continue
        metadata, path = entry.split("\t", 1)
        mode, kind, blob = metadata.split()
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError("Non-regular Git tree member")
        records.append({"path": path, "mode": mode, "git_blob": blob})
    if not 1 <= len(records) <= r.MAX_FILES:
        raise ValueError("Invalid base inventory size")
    paths = {item["path"] for item in records}
    if actual_files != paths:
        raise ValueError("Base working tree files differ from pinned tracked inventory")
    index = set()
    for entry in git(root, "ls-files", "--stage", "-z").split("\0"):
        if not entry:
            continue
        info_text, path = entry.split("\t", 1)
        mode, oid, stage = info_text.split()
        if stage != "0":
            raise ValueError("Unmerged base index")
        index.add((path, mode, oid))
    if index != {(f["path"], f["mode"], f["git_blob"]) for f in records}:
        raise ValueError("Base index differs from pinned tree")
    check_base(root, info["commit"])
    blobs = {}
    for item in records:
        action, reason = classify(owner, item["path"], paths, source)
        item.update(action=action, reason=reason)
        if action != "excluded":
            data = r.read_file(r.safe_member(root, item["path"]))
            blobs[item["path"]] = data
            item.update(sha256=r.digest(data), size=len(data))
        if sum(len(b) for b in blobs.values()) > r.MAX_TOTAL:
            raise ValueError("Base snapshot exceeds byte limit")
    check_base(root, info["commit"])
    commit_object = git_bytes(root, "cat-file", "commit", info["commit"])
    return {"commit": info["commit"], "tree": tree, "commit_object": base64.b64encode(commit_object).decode("ascii"),
            "records": sorted(records, key=lambda f: f["path"]),
            "original_metadata": {p: base64.b64encode(blobs[p]).decode("ascii") for p in (PLUGIN, MARKET)}}, blobs


def content_record(path, data, mode, origin, input_path):
    return {"path": path, "sha256": r.digest(data), "size": len(data),
            "mode": mode, "origin": origin, "input_path": input_path}


def validate_content(item):
    if (not isinstance(item["sha256"], str) or not r.HEX.fullmatch(item["sha256"])
            or type(item["size"]) is not int or not 0 <= item["size"] <= r.MAX_FILE
            or item["mode"] not in {"100644", "100755"}):
        raise ValueError("Invalid raw file hash, size or mode")


def metadata_bytes(base, path, record):
    data = unbase64(base["original_metadata"][path])
    if len(data) != record["size"] or r.digest(data) != record["sha256"]:
        raise ValueError("Original metadata differs from base receipt")
    result = r.decoded(data)
    if not isinstance(result, dict):
        raise ValueError("Plugin metadata must be an object")
    return result


def derive(source, source_digest, inputs, bases, safety_projection=None):
    """Recompute exact candidate ownership/files from authenticated receipt inputs."""
    r.validate_manifest(source)
    if not isinstance(source_digest, str) or r.digest(r.encoded(source)) != source_digest:
        raise ValueError("Embedded source manifest digest mismatch")
    validate_inputs(inputs)
    exact(bases, r.OWNERS, "base receipts")
    owners = dict(source["owners"])
    files, generated, metadata = {}, {}, {}

    def add(record):
        path = record["path"]
        r.relative(path)
        if path.casefold() in {p.casefold() for p in files}:
            raise ValueError("Duplicate/case-colliding candidate path")
        files[path] = record

    for owner, base in sorted(bases.items()):
        exact(base, {"commit", "tree", "commit_object", "records", "original_metadata"}, "base receipt")
        if (base["commit"] != inputs["plugins"][owner]["commit"]
                or not isinstance(base["tree"], str) or not OID.fullmatch(base["tree"])):
            raise ValueError("Base provenance differs from pinned input")
        exact(base["original_metadata"], {PLUGIN, MARKET}, "original metadata")
        if not isinstance(base["records"], list) or not 1 <= len(base["records"]) <= r.MAX_FILES:
            raise ValueError("Invalid base record count")
        records = {}
        seen = set()
        for item in base["records"]:
            if not isinstance(item, dict):
                raise ValueError("Invalid base record")
            path = str(r.relative(item.get("path")))
            if path.casefold() in seen:
                raise ValueError("Duplicate/case-colliding base path")
            seen.add(path.casefold())
            records[path] = item
        if list(records) != sorted(records):
            raise ValueError("Base record order must be canonical")
        names = {r.relative(p).parts[1] for p in records if re.fullmatch(r"skills/[^/]+/SKILL\.md", p)}
        for item in records.values():
            path = item["path"]
            action, reason = classify(owner, path, records, source)
            keys = {"path", "mode", "git_blob", "action", "reason"}
            exact(item, keys if action == "excluded" else keys | {"sha256", "size"}, "base member")
            if (item["action"] != action or item["reason"] != reason
                    or not isinstance(item["git_blob"], str) or not OID.fullmatch(item["git_blob"])
                    or item["mode"] not in {"100644", "100755"}):
                raise ValueError("Invalid base classification/provenance")
            if path.startswith("skills/") and r.relative(path).parts[1] not in names:
                raise ValueError("Base skill is missing its SKILL.md")
            if action != "excluded":
                validate_content(item)
            if action == "copied":
                add({"path": f"plugins/{owner}/{path}", **{k: item[k] for k in ("sha256", "size", "mode")},
                     "origin": "official", "input_path": path})
        commit_data = unbase64(base["commit_object"])
        if (git_oid("commit", commit_data) != base["commit"]
                or commit_data.split(b"\n", 1)[0] != b"tree " + base["tree"].encode("ascii")
                or tree_oid(base["records"]) != base["tree"]):
            raise ValueError("Tracked inventory is not the pinned Git commit tree")
        if not {PLUGIN, MARKET, "LICENSE", "NOTICE"}.issubset(records):
            raise ValueError("Required base metadata/attribution is missing")
        for name in names - set(source["owners"]):
            if name in owners:
                raise ValueError("Plugin-only skill has more than one home")
            owners[name] = owner
        manifest = metadata_bytes(base, PLUGIN, records[PLUGIN])
        market = metadata_bytes(base, MARKET, records[MARKET])
        name = inputs["plugins"][owner]["name"]
        version = manifest.get("version")
        membership = [f"./skills/{n}/" for n in sorted(names)]
        if (manifest.get("name") != name or not isinstance(version, str) or not VERSION.fullmatch(version)
                or not isinstance(manifest.get("skills"), list)
                or any(not isinstance(p, str) for p in manifest["skills"])
                or sorted(manifest["skills"]) != sorted(membership)):
            raise ValueError("Base plugin identity/version/skill membership mismatch")
        if (market.get("name") != name or market.get("version") != version
                or not isinstance(market.get("plugins"), list) or len(market["plugins"]) != 1
                or not isinstance(market["plugins"][0], dict)):
            raise ValueError("Unsupported base self-marketplace")
        entry = market["plugins"][0]
        if (entry.get("name"), entry.get("source"), entry.get("version")) != (name, "./", version):
            raise ValueError("Marketplace identity/version mismatch")
        metadata[owner] = (manifest, market, records)
    if set(owners) - set(source["owners"]) != set(source["plugin_only_out_of_scope"]):
        raise ValueError("Plugin-only inventory is not exact")
    for owner, (manifest, market, records) in metadata.items():
        version = manifest["version"] + "-vibe." + source_digest[:12]
        manifest["version"] = version
        manifest["skills"] = [f"./skills/{n}/" for n, home in sorted(owners.items()) if home == owner]
        market["version"] = market["plugins"][0]["version"] = version
        for path, document in ((PLUGIN, manifest), (MARKET, market)):
            key = f"plugins/{owner}/{path}"
            data = r.encoded(document)
            generated[key] = data
            add(content_record(key, data, records[path]["mode"], "generated", path))
    for f in source["files"]:
        paths = ([f["package_path"]] if f["package_path"].startswith("plugins/") else
                 [f"plugins/{o}/.simonk-source-attribution/{f['package_path']}" for o in sorted(r.OWNERS)])
        for path in paths:
            add({"path": path, **{k: f[k] for k in ("sha256", "size", "mode")},
                 "origin": "source", "input_path": f["package_path"]})
    if safety_projection is not None:
        project_safety(source, safety_projection, files, generated, add)
    if len(files) > r.MAX_FILES or sum(f["size"] for f in files.values()) > r.MAX_TOTAL:
        raise ValueError("Candidate exceeds file/byte limits")
    return owners, sorted(files.values(), key=lambda f: f["path"]), generated


def check_content(path, data, owners, origin):
    parts = r.relative(path).parts
    if len(parts) == 5 and parts[2] == "skills" and parts[-1] == "SKILL.md":
        text = data.decode("utf-8").replace("\r\n", "\n")
        header = text.split("\n---\n", 1)[0] if text.startswith("---\n") else ""
        names = re.findall(r"(?m)^name:[ \t]*(?:([a-z0-9-]+)|\"([a-z0-9-]+)\"|'([a-z0-9-]+)')[ \t]*$", header)
        if len(names) != 1 or next((n for n in names[0] if n), None) != parts[3] or owners.get(parts[3]) != parts[1]:
            raise ValueError("Candidate skill declaration/owner mismatch")
    if (parts[2] in {".claude-plugin", "agents", "commands"}
            or origin == "official" and parts[2] == "skills" and Path(path).suffix.lower() in
            {".md", ".txt", ".json", ".py", ".sh", ".ps1", ".js", ".mjs", ".ts", ".yaml", ".yml", ".toml"}):
        # Conservative explicit-reference gate, not a shell/JS dependency resolver.
        text = data.decode("utf-8").replace("\\", "/").casefold()
        if re.search(r"(?:^|[^a-z0-9_-])legacy/|__pycache__|\.pyc(?:[^a-z0-9_]|$)", text):
            raise ValueError("Active component explicitly references excluded legacy/cache")


def verify_bundle(root, expected_digest):
    root = r.no_links(root)
    if not isinstance(expected_digest, str) or not r.HEX.fullmatch(expected_digest):
        raise ValueError("A pinned bundle SHA-256 is required")
    with r.pinned(root, directory=True):
        data = r.read_file(root / "bundle.json")
        if r.digest(data) != expected_digest:
            raise ValueError("Candidate receipt digest mismatch")
        m = r.decoded(data)
        if not isinstance(m, dict):
            raise ValueError("Invalid candidate receipt")
        safety = m.get("scope") == SAFETY_SCOPE
        keys = {"schema_version", "scope", "source_digest", "source_manifest", "inputs", "bases", "owners", "files",
                "runtime_closure_verified", "host_compatibility_verified", "installation_ready", "limitations"}
        exact(m, keys | ({"safety_projection"} if safety else set()), "candidate receipt")
        if (type(m["schema_version"]) is not int or m["schema_version"] != (2 if safety else 1)
                or m["scope"] != (SAFETY_SCOPE if safety else SCOPE)
                or any(m[k] is not False for k in ("runtime_closure_verified", "host_compatibility_verified", "installation_ready"))
                or m["limitations"] != (SAFETY_LIMITATIONS if safety else LIMITATIONS) or data != r.encoded(m)):
            raise ValueError("Invalid candidate-only contract")
        owners, files, _ = derive(m["source_manifest"], m["source_digest"], m["inputs"], m["bases"],
                                 m["safety_projection"] if safety else None)
        if r.encoded(m["owners"]) != r.encoded(owners) or r.encoded(m["files"]) != r.encoded(files):
            raise ValueError("Candidate does not match its source/base closure")
        if r.files_under(root) != {f["path"] for f in files} | {"bundle.json"}:
            raise ValueError("Missing or extra candidate files")
        for f in files:
            data = r.read_file(r.safe_member(root, f["path"]))
            if len(data) != f["size"] or r.digest(data) != f["sha256"]:
                raise ValueError("Candidate member differs from pinned receipt")
            check_content(f["path"], data, owners, f["origin"])
        return m


def build_bundle(source_package, source_digest, plugin_parent, inputs, output, *, safety_adapter=False):
    if type(safety_adapter) is not bool:
        raise ValueError("Safety adapter option must be boolean")
    validate_inputs(inputs)
    source_package, plugin_parent = r.no_links(source_package), r.no_links(plugin_parent)
    target = r.destination(output, source_package, plugin_parent)
    if os.path.lexists(target):
        raise ValueError("Build never overwrites existing output")
    with ExitStack() as stack:
        stack.enter_context(r.pinned(source_package, directory=True))
        stack.enter_context(r.pinned(plugin_parent, directory=True))
        source = r.verify_release(source_package, source_digest)
        projection = None
        if safety_adapter:
            if not SAFETY_INPUTS <= {f["package_path"] for f in source["files"]}:
                raise ValueError("Safety projection requires all reviewed source inputs")
            projection = {"version": 1, "originals": {
                path: base64.b64encode(r.read_file(r.safe_member(source_package, path))).decode("ascii")
                for path in sorted(SAFETY_INPUTS)}}
        bases, snapshots = {}, {}
        actual_files = {owner: pin_snapshot(r.safe_member(plugin_parent, owner), stack) for owner in sorted(r.OWNERS)}
        for owner, info in sorted(inputs["plugins"].items()):
            root = r.safe_member(plugin_parent, owner)
            stack.enter_context(r.pinned(root, directory=True))
            bases[owner], snapshots[owner] = collect_base(root, info, owner, source, actual_files[owner])
        owners, files, generated = derive(source, source_digest, inputs, bases, projection)
        blobs = {}
        for f in files:
            if f["origin"] == "source":
                data = r.read_file(r.safe_member(source_package, f["input_path"]))
            elif f["origin"] == "generated":
                data = generated[f["path"]]
            else:
                data = snapshots[r.relative(f["path"]).parts[1]][f["input_path"]]
            if len(data) != f["size"] or r.digest(data) != f["sha256"]:
                raise ValueError("Input changed during candidate construction")
            check_content(f["path"], data, owners, f["origin"])
            blobs[f["path"]] = data
    manifest = {"schema_version": 2 if safety_adapter else 1,
                "scope": SAFETY_SCOPE if safety_adapter else SCOPE, "source_digest": source_digest, "source_manifest": source,
                "inputs": copy.deepcopy(inputs), "bases": bases, "owners": owners, "files": files,
                "runtime_closure_verified": False, "host_compatibility_verified": False,
                "installation_ready": False, "limitations": SAFETY_LIMITATIONS if safety_adapter else LIMITATIONS}
    if safety_adapter:
        manifest["safety_projection"] = projection
    data = r.encoded(manifest)
    if len(data) > r.MAX_FILE:
        raise ValueError("Candidate receipt exceeds byte limit")
    bundle_digest = r.digest(data)
    with r.pinned(target.parent, directory=True):
        stage = Path(tempfile.mkdtemp(prefix=".simonk-plugin-candidate-", dir=target.parent))
        with r.pinned(stage, directory=True, delete=True):
            for f in files:
                r.write_member(stage, f["path"], blobs[f["path"]], f["mode"])
            r.write_member(stage, "bundle.json", data, "100644")
            verify_bundle(stage, bundle_digest)
            r.publish_new(stage, target)
        verify_bundle(target, bundle_digest)
    return {"status": "candidate_bytes_verified", "bundle_digest": bundle_digest,
            "plugins": len(bases), "skills": len(owners), "files": len(files), "path": str(target),
            "runtime_closure_verified": False, "host_compatibility_verified": False, "installation_ready": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--source-package", type=Path, required=True)
    build.add_argument("--source-digest", required=True)
    build.add_argument("--plugin-parent", type=Path, required=True)
    build.add_argument("--inputs", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--safety-adapter", action="store_true",
                       help="Opt in to reviewed v2 safety command/resource projection; not installation")
    verify = commands.add_parser("verify")
    verify.add_argument("--package", type=Path, required=True)
    verify.add_argument("--expected-digest", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = build_bundle(args.source_package, args.source_digest, args.plugin_parent,
                                  r.load_json(args.inputs), args.output, safety_adapter=args.safety_adapter)
        else:
            receipt = verify_bundle(args.package, args.expected_digest)
            result = {"status": "candidate_bytes_verified", "bundle_digest": args.expected_digest,
                      "plugins": len(receipt["bases"]), "skills": len(receipt["owners"]), "installation_ready": False}
        print(r.encoded(result).decode("utf-8"), end="")
        return 0
    except (ValueError, OSError, subprocess.SubprocessError, UnicodeError, TypeError, KeyError, IndexError):
        # Do not echo external metadata, credential-like text, paths or native stderr.
        print('{"status":"blocked","message":"Candidate validation failed"}', file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
