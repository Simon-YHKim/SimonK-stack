"""Orca guide discovery and optional safe update of existing installed skills.

Pass the absolute executable selected through the orca-cli discovery stub.
--sync uses the official non-forced updater; never installs missing skills,
updates the Orca application, starts workers, controls GUI or calls models.
Reports guide availability, never execution or billing readiness.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


KNOWN_ALIASES = {'jira-tickets': 'orca-jira', 'linear-tickets': 'orca-linear'}
NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')


def update_operations(payload):
    if (not isinstance(payload, dict) or payload.get('executed') is not False
            or payload.get('scope') != 'global'
            or not isinstance(payload.get('planDigest'), str) or not payload['planDigest']
            or not isinstance(payload.get('plan'), dict)
            or not isinstance(payload['plan'].get('skills'), list)):
        raise ValueError('UPDATE_PLAN_INVALID')
    operations = []
    for skill in payload['plan']['skills']:
        if not isinstance(skill, dict) or not isinstance(skill.get('ops'), list):
            raise ValueError('UPDATE_PLAN_INVALID')
        for operation in skill['ops']:
            if not isinstance(operation, dict) or not isinstance(operation.get('kind'), str):
                raise ValueError('UPDATE_PLAN_INVALID')
            operations.append(operation['kind'])
    return operations


def synchronize(read):
    preview_args = ['skills', 'update', '--all', '--dry-run', '--json']
    before = read(preview_args)
    operations = update_operations(before)
    if operations and all(kind == 'keep' for kind in operations):
        return {'status': 'current', 'before': before, 'executed': False}
    if not operations:
        return {'status': 'nothing_installed', 'before': before, 'executed': False}
    result = read(['skills', 'update', '--all', '--json'])
    summary = result.get('summary') if isinstance(result, dict) else None
    if (not isinstance(summary, dict) or result.get('executed') is not True
            or summary.get('ok') is not True or summary.get('exitCode') != 0):
        raise ValueError('UPDATE_FAILED')
    after = read(preview_args)
    remaining = update_operations(after)
    clean = bool(remaining) and all(kind == 'keep' for kind in remaining)
    clean = clean and summary.get('leftAloneCount') == 0
    return {'status': 'updated' if clean else 'attention_required',
            'before': before, 'result': result, 'after': after, 'executed': True}


def discover(read, selected):
    version = read(['--version'])
    if not isinstance(version, str) or not version.strip():
        raise ValueError('VERSION_INVALID')
    catalog = read(['skills', 'list', '--json'])
    topics = catalog.get('topics') if isinstance(catalog, dict) else None
    if not isinstance(topics, list) or not topics:
        raise ValueError('CATALOG_INVALID')
    by_name = {}
    for topic in topics:
        if not isinstance(topic, dict):
            raise ValueError('CATALOG_INVALID')
        name, description = topic.get('name'), topic.get('description')
        if (not isinstance(name, str) or not NAME.fullmatch(name)
                or not isinstance(description, str) or not description.strip()
                or name in by_name):
            raise ValueError('CATALOG_INVALID')
        by_name[name] = {'name': name, 'description': description}
    aliases = {old: new for old, new in KNOWN_ALIASES.items()
               if old in by_name and new in by_name}
    names = []
    for requested in selected:
        if requested not in by_name:
            raise ValueError('TOPIC_NOT_LISTED')
        name = aliases.get(requested, requested)
        if name not in names:
            names.append(name)
    guides = []
    for name in names:
        guide = read(['skills', 'get', name, '--json'])
        markdown = guide.get('markdown') if isinstance(guide, dict) else None
        if (not isinstance(markdown, str) or not markdown.strip()
                or guide.get('name') != name):
            raise ValueError('GUIDE_INVALID')
        guides.append({'name': name, 'markdown': markdown,
                       'sha256': hashlib.sha256(markdown.encode('utf-8')).hexdigest()})
    return {'schema': 'vibe.orca-guides.v1', 'version': version.strip(),
            'topics': list(by_name.values()), 'aliases': aliases,
            'selected': guides, 'execution_verified': False,
            'scope': 'Guide discovery only; host must verify workspace, permissions and cost.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--orca', required=True, help='Absolute path to the selected Orca executable')
    parser.add_argument('--select', action='append', default=[], help='Exact topic from the live catalog')
    parser.add_argument('--sync', action='store_true', help='Update existing unmodified Orca skills before discovery')
    args = parser.parse_args()
    executable = Path(args.orca)
    if not executable.is_absolute() or not executable.is_file():
        parser.error('--orca must name an existing absolute executable; no PATH fallback')
    executable = str(executable.resolve())
    def read(argv):
        result = subprocess.run([executable, *argv], capture_output=True, text=True,
                                encoding='utf-8', errors='strict', timeout=30, check=False)
        if result.returncode:
            # Do not echo arbitrary CLI diagnostics: they may contain account data.
            raise ValueError('ORCA_DISCOVERY_FAILED: exit ' + str(result.returncode))
        return json.loads(result.stdout) if '--json' in argv else result.stdout
    try:
        sync = synchronize(read) if args.sync else {'status': 'not_requested'}
        result = discover(read, args.select)
        result['executable'] = executable
        result['skill_update'] = sync
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        code = str(error) if type(error) is ValueError else type(error).__name__
        print(json.dumps({'error': code, 'execution_verified': False}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
