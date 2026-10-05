#!/usr/bin/env bash
# simon-stack installer - only the explicit offline overlay entry remains.
#
# The git-clone install (plugin repo clone/pull, copying skills into
# ~/.claude/skills, Gstack, instincts, CLAUDE.md, hooks) was retired by hub
# decision D-87 (2026-10-05). Its last version is _archive/legacy-install/install.sh.

set -euo pipefail

# Explicit offline overlay mode exits before ALL legacy prerequisites/effects.
# Default is preview; --apply only publishes a new isolated target or verifies an
# identical release. No --force, live-home install, network or fallback here.
for arg in "$@"; do
  case "$arg" in
    --offline-package|--offline-package=*)
      RELEASE_REPO="$(cd "$(dirname "$0")/.." && pwd)"
      exec "${SIMONK_PYTHON:-python3}" -B "$RELEASE_REPO/scripts/skill_release.py" materialize "$@"
      ;;
  esac
done

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      cat <<'USAGE'
Usage:
  ./scripts/install.sh --offline-package <package> --target <new folder> --expected-digest <release digest> [--apply]
  ./scripts/install.sh --help

--offline-package runs scripts/skill_release.py materialize on a verified source
release package. Default is a preview; --apply only publishes a new isolated
target or verifies an identical release. No network, no ~/.claude writes.

The git-clone install that this script used to run is retired (hub D-87):
  Users:   /plugin marketplace add Simon-YHKim/SimonK-stack  (README section 3)
  This PC: pwsh -File scripts/windows/update-local.ps1        (preview; -Apply installs)
The old script is kept in _archive/legacy-install/install.sh.
USAGE
      exit 0 ;;
  esac
done

echo "install.sh: the git-clone install is retired (hub D-87). Users: /plugin marketplace add Simon-YHKim/SimonK-stack. This PC: pwsh -File scripts/windows/update-local.ps1. Only --offline-package remains (see --help)." >&2
exit 2
