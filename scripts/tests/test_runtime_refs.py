"""Static check: runtime document references in skills-src point at files SimonK-stack ships.

Skills read support documents through "~/.simonk/runtime/<skill>/<path>". The
runtime installer lays every skill listed in skills-src/VENDORED.md over the
upstream folder of the same name (runtime/RUNTIME.json "skill_overlay"), so a
reference into such a folder must name a file that exists in skills-src.
Tool folders (bin, lib, browse/dist, ...) come from upstream and are not checked.
"""
import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "skills-src"
REF = re.compile(r"(?:~|\$HOME|\$\{HOME\})/\.simonk/runtime/([a-z0-9-]+)/([A-Za-z0-9_./-]+\.(?:md|json))")
VENDORED_LINE = re.compile(r"^- `([a-z0-9-]+)`")


def overlay_map():
    pin = json.loads((REPO / "runtime" / "RUNTIME.json").read_text(encoding="utf-8"))
    upstream_names = pin["skill_overlay"]["upstream_names"]
    names = [m.group(1) for line in (SRC / "VENDORED.md").read_text(encoding="utf-8").splitlines()
             if (m := VENDORED_LINE.match(line))]
    return {upstream_names.get(n, n): n for n in names if (SRC / n / "SKILL.md").is_file()}


class RuntimeReferenceTests(unittest.TestCase):
    def test_runtime_doc_references_exist_in_skills_src(self):
        folders = overlay_map()
        missing, checked = [], 0
        for f in sorted(SRC.rglob("*.md")):
            for m in REF.finditer(f.read_text(encoding="utf-8", errors="replace")):
                folder, rel = m.group(1), m.group(2)
                if folder not in folders:
                    continue
                checked += 1
                if not (SRC / folders[folder] / rel).is_file():
                    missing.append(f"{f.relative_to(REPO).as_posix()}: {m.group(0)}")
        self.assertGreater(checked, 50, "the reference pattern stopped matching")
        self.assertEqual(sorted(set(missing)), [])

    def test_overlay_names_match_existing_skills(self):
        pin = json.loads((REPO / "runtime" / "RUNTIME.json").read_text(encoding="utf-8"))
        for name in pin["skill_overlay"]["upstream_names"]:
            self.assertTrue((SRC / name / "SKILL.md").is_file(), name)


if __name__ == "__main__":
    unittest.main()
