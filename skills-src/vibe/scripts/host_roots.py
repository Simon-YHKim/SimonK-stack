# host_roots.py - observe the current host's flat skill roots for /vibe discovery.
#
# Split-home step 1 (references/orchestration.md): the coordinator composes
# explicit --root values from the active host's observed, authorized locations
# and approved plugin scope. This helper only reads; it never writes, caches or
# persists a root list, never opens the network and never guesses a cache or
# version path. Re-run it before each inventory/plan: old output is not evidence.
#
# Usage:
#   python -B host_roots.py --host claude [--project DIR] [--candidate-first]
#   python -B host_roots.py --host codex
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

if __name__ == "__main__":
    sys.dont_write_bytecode = True

SCHEMA_VERSION = 1
MAX_JSON_BYTES = 2 * 1024 * 1024
KST = timezone(timedelta(hours=9))
SCOPE_RANK = {"user": 0, "project": 1, "local": 2}


class HostRootsError(ValueError):
    """Host-level input that cannot be observed without guessing."""


def _key(path):
    return os.path.normcase(os.path.realpath(path))


def _read_json(path, sources, required_type=dict):
    """Read one bounded JSON file and record its hash. Missing -> None."""
    try:
        with open(path, "rb") as stream:
            raw = stream.read(MAX_JSON_BYTES + 1)
    except FileNotFoundError:
        return None
    if len(raw) > MAX_JSON_BYTES:
        raise HostRootsError(f"{path} is larger than {MAX_JSON_BYTES} bytes")

    def nonfinite(value):
        raise HostRootsError(f"{path} contains a nonfinite number")

    try:
        data = json.loads(raw.decode("utf-8-sig"), parse_constant=nonfinite)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HostRootsError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, required_type):
        raise HostRootsError(f"{path} must contain a JSON {required_type.__name__}")
    sources.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()})
    return data


class Collector:
    def __init__(self):
        self.roots, self.skipped, self.notes, self.sources = [], [], [], []
        self._seen = set()

    def add(self, path, origin):
        path = Path(path)
        if not path.is_dir():
            self.skipped.append({"root": str(path), "origin": origin, "reason": "missing"})
            return
        key = _key(path)
        if key in self._seen:
            self.skipped.append({"root": str(path), "origin": origin, "reason": "duplicate_physical_root"})
            return
        self._seen.add(key)
        self.roots.append({"path": str(path), "origin": origin})


def _enabled_plugins(settings_files, collector):
    """Merge enabledPlugins with later files overriding earlier ones."""
    state, order = {}, []
    for path in settings_files:
        data = _read_json(path, collector.sources)
        if data is None:
            continue
        enabled = data.get("enabledPlugins")
        if enabled is None:
            continue
        if not isinstance(enabled, dict):
            raise HostRootsError(f"{path} enabledPlugins must be an object")
        for plugin_id, value in enabled.items():
            if plugin_id not in state:
                order.append(plugin_id)
            state[plugin_id] = value is True
    return [(plugin_id, state[plugin_id]) for plugin_id in order]


def _install_record(records, project):
    """Pick the most specific applicable record; ties are ambiguous."""
    applicable = []
    for record in records:
        if not isinstance(record, dict):
            continue
        scope = record.get("scope")
        if scope not in SCOPE_RANK:
            continue
        if scope != "user":
            path = record.get("projectPath")
            if project is None or not isinstance(path, str) or _key(path) != _key(project):
                continue
        applicable.append(record)
    if not applicable:
        return None, "no_applicable_install_record"
    best = max(SCOPE_RANK[r["scope"]] for r in applicable)
    top = [r for r in applicable if SCOPE_RANK[r["scope"]] == best]
    if len(top) > 1:
        return None, "ambiguous_install_record"
    return top[0], None


def _plugin_skill_roots(install, collector):
    """Default skills/ plus manifest-declared paths that stay inside the plugin."""
    roots = [install / "skills"]
    manifest_path = install / ".claude-plugin" / "plugin.json"
    try:
        manifest = _read_json(manifest_path, collector.sources)
    except HostRootsError as exc:
        return None, f"manifest_invalid: {exc}"
    declared = (manifest or {}).get("skills")
    if declared is not None:
        entries = [declared] if isinstance(declared, str) else declared
        if not isinstance(entries, list) or not all(isinstance(e, str) for e in entries):
            return None, "manifest_skills_invalid"
        base = _key(install)
        skill_dirs = {}
        for entry in entries:
            target = (install / entry)
            if not _key(target).startswith(base + os.sep) and _key(target) != base:
                return None, "manifest_skills_outside_plugin"
            if (target / "SKILL.md").is_file():
                skill_dirs.setdefault(target.parent, set()).add(_key(target))
            else:
                roots.append(target)
        # A declared skill directory is scanned through its flat parent, which
        # is only safe when that parent holds no undeclared skill.
        for parent, declared_keys in skill_dirs.items():
            # The flat scan root itself must stay inside the plugin: a skill
            # declared at the install root would otherwise scan sibling installs.
            if not _key(parent).startswith(base + os.sep) and _key(parent) != base:
                return None, "manifest_skill_root_outside_plugin"
            present = {_key(child) for child in parent.iterdir() if (child / "SKILL.md").is_file()}
            if _key(parent) != _key(install / "skills") and present - declared_keys:
                return None, "manifest_partial_skill_dir"
            roots.append(parent)
    unique = {}
    for root in roots:
        unique.setdefault(_key(root), root)
    return list(unique.values()), None


def observe_claude(home, project, collector, env):
    config = Path(env["CLAUDE_CONFIG_DIR"]) if env.get("CLAUDE_CONFIG_DIR") else home / ".claude"
    if env.get("CLAUDE_CONFIG_DIR"):
        collector.notes.append("CLAUDE_CONFIG_DIR is set; it replaces ~/.claude.")
    collector.add(config / "skills", "claude-user-skills")
    collector.notes.append("claude.ai-synced plugins (plugins/synced) are not scanned; "
                           "describe them in a host-native snapshot instead.")

    settings = [config / "settings.json"]
    if project is not None:
        settings += [project / ".claude" / "settings.json", project / ".claude" / "settings.local.json"]
    else:
        collector.notes.append("Project and local plugin settings were not read; pass --project DIR to include them.")
    collector.notes.append("Managed (policy) settings and --settings overrides are not read.")
    plugins = _enabled_plugins(settings, collector)
    if not plugins:
        collector.notes.append("No plugin is enabled in the settings that were read.")
        return
    installed = _read_json(config / "plugins" / "installed_plugins.json", collector.sources)
    if installed is None:
        records = {}
        collector.notes.append("installed_plugins.json is missing; enabled plugins have no install record.")
    else:
        if installed.get("version") != 2 or not isinstance(installed.get("plugins"), dict):
            raise HostRootsError("installed_plugins.json has an unsupported schema (expected version 2)")
        records = installed["plugins"]
    for plugin_id, enabled in plugins:
        origin = f"claude-plugin:{plugin_id}"
        if not enabled:
            collector.skipped.append({"plugin": plugin_id, "reason": "disabled"})
            continue
        entries = records.get(plugin_id)
        if not isinstance(entries, list):
            collector.skipped.append({"plugin": plugin_id, "reason": "no_install_record"})
            continue
        record, reason = _install_record(entries, project)
        if record is None:
            collector.skipped.append({"plugin": plugin_id, "reason": reason})
            continue
        install = record.get("installPath")
        if not isinstance(install, str) or not os.path.isabs(install) or not os.path.isdir(install):
            collector.skipped.append({"plugin": plugin_id, "reason": "install_path_missing"})
            continue
        roots, reason = _plugin_skill_roots(Path(install), collector)
        if roots is None:
            collector.skipped.append({"plugin": plugin_id, "reason": reason})
            continue
        if not any(Path(r).is_dir() for r in roots):
            collector.skipped.append({"plugin": plugin_id, "reason": "no_skills_dir"})
            continue
        for root in roots:
            if Path(root).is_dir():
                collector.add(root, origin)


def observe_codex(home, collector, env):
    codex = Path(env["CODEX_HOME"]) if env.get("CODEX_HOME") else home / ".codex"
    if env.get("CODEX_HOME"):
        collector.notes.append("CODEX_HOME is set; it replaces ~/.codex.")
    collector.add(codex / "skills", "codex-user-skills")
    collector.add(home / ".agents" / "skills", "agents-skills")
    collector.add(codex / "skills" / ".system", "codex-system-skills")
    collector.notes.append("Codex plugin skills are not resolved from cache versions; "
                           "describe them in a host-native snapshot instead.")


def candidate_roots(collector):
    """Prepend the intact bundle's five plugin roots when this script is in one."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import orchestrate  # noqa: E402  (same scripts directory)

    try:
        inventory = orchestrate.candidate_inventory()
    except ValueError as exc:
        raise HostRootsError(f"candidate is not intact: {exc}") from exc
    if inventory is None:
        collector.skipped.append({"root": "candidate", "reason": "not_in_candidate"})
        return []
    collector.notes.append("Explicit roots skip the candidate receipt check; "
                           "run the bundle verifier separately when SimonK members matter.")
    return [r["path"] for r in inventory["roots"]]


def observe(host, home, project=None, candidate_first=False, env=None, now=None):
    env = os.environ if env is None else env
    collector = Collector()
    if candidate_first:
        for root in candidate_roots(collector):
            collector.add(root, "candidate")
    if host == "claude":
        observe_claude(home, project, collector, env)
    elif host == "codex":
        if project is not None:
            raise HostRootsError("--project applies to --host claude only")
        observe_codex(home, collector, env)
    else:
        raise HostRootsError(f"unknown host: {host}")
    collector.notes.append("Nothing was written or persisted. Re-run before each inventory/plan.")
    roots = [r["path"] for r in collector.roots]
    return {
        "schema_version": SCHEMA_VERSION,
        "host": host,
        "observed_at": (now or datetime.now(KST)).isoformat(timespec="seconds"),
        "roots": roots,
        "root_origins": collector.roots,
        "root_args": [arg for root in roots for arg in ("--root", root)],
        "sources": collector.sources,
        "skipped": collector.skipped,
        "notes": collector.notes,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Observe this host's skill roots (read-only).")
    parser.add_argument("--host", required=True, choices=("claude", "codex"))
    parser.add_argument("--project", type=Path, help="also read this project's plugin settings (claude)")
    parser.add_argument("--candidate-first", action="store_true",
                        help="prepend the intact candidate's five plugin roots")
    parser.add_argument("--home", type=Path, help=argparse.SUPPRESS)  # tests only
    args = parser.parse_args(argv)
    env = {} if args.home else os.environ
    home = args.home or Path.home()
    project = args.project.absolute() if args.project else None
    try:
        result = observe(args.host, home, project, args.candidate_first, env)
    except (HostRootsError, OSError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
