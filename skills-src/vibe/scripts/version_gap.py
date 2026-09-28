# -*- coding: utf-8 -*-
"""스킬 버전 정합 점검 - 읽기 전용.

왜 있는가 (2026-09-28):
    vibe 버전이 SKILL.md frontmatter · evals/cases.json · CHANGELOG.md 에
    제각각 적혀 있었고(2.12.1 / 2.12.0 / 2.12.0), 서로 맞는지 대조하는 코드가
    없었다. 설치된 실행본(~/.claude/skills/<이름>)이 소스보다 뒤처져도
    알려 주는 곳이 없었다.

사용법:
    python -B version_gap.py check --skill DIR
        DIR/SKILL.md 의 frontmatter `version:`, DIR/evals/cases.json 의 "version",
        DIR/CHANGELOG.md 의 첫 `## <semver>` 제목(위의 `## Unreleased` 는 허용,
        `[1.2.3]` · `[1.2.3](링크)` · `v1.2.3` 형식 허용, 코드펜스와 HTML 주석 안은
        건너뜀)을 읽어 JSON {skill_md, cases, changelog, consistent} 를 출력한다.
        종료코드: 0 모두 같음 · 1 다름 · 2 파일 없음/읽기 실패/버전 표기를 못 찾음
        (frontmatter 가 깨졌거나 `version:` 이 중복·따옴표 미닫힘이면 2).

    python -B version_gap.py gap --running DIR --source DIR [--json]
        두 폴더의 SKILL.md frontmatter `version:` 을 비교해 한 줄로 알린다.
        예: "vibe 실행본 2.11.6 ≠ 소스 2.13.0 (설치 갱신 필요)"
        실행본이 semver 우선순위로 앞서면 "실행본이 소스보다 앞선다"로 따로 알린다.
        종료코드: 0 같음 · 1 다름 · 2 읽기 실패.
        정션·심볼릭 링크는 표시용으로만 해석한다(Path.resolve).

    인자 오류는 argparse 규칙대로 종료코드 2 로 끝난다(읽기 실패와 같은 값).

원칙:
    - 아무것도 쓰지 않는다. 설치·복사·수정은 사람이 정한다.
    - 읽기 실패는 "다름"이 아니라 별도 상태(종료코드 2)다.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SEMVER = r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?"
_SEMVER_FULL = re.compile(r"^" + SEMVER + r"$")
_H2 = re.compile(r"^ {0,3}##(?!#)\s*(.*?)\s*$")
# `1.2.3 - date` · `[1.2.3] - date` · `[1.2.3](link) (date)` · `1.2.3: title`.
# The version must end at a non-word boundary so `1.2.3.4` is not read as 1.2.3.
_VERSION_HEADING = re.compile(r"^\[?[vV]?(" + SEMVER + r")\]?(?![\w.+-])")
_UNRELEASED = re.compile(r"^\[?unreleased\]?(?![\w.+-])", re.IGNORECASE)
_FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")


class Unreadable(Exception):
    """입력이 없거나 읽을 수 없거나 버전을 찾을 수 없다."""


def _read_text(path):
    try:
        return path.read_bytes().decode("utf-8-sig")
    except FileNotFoundError:
        raise Unreadable("%s 없음" % path.name) from None
    except (OSError, UnicodeError) as exc:
        raise Unreadable("%s 읽기 실패: %s" % (path.name, exc.__class__.__name__)) from None


def _frontmatter(text, filename):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise Unreadable("%s frontmatter 없음" % filename)
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index]
    raise Unreadable("%s frontmatter 가 닫히지 않음" % filename)


def _frontmatter_value(lines, key):
    """최상위(들여쓰기 없는) `key: value` 한 줄만 읽는다.

    같은 키가 두 번 나오거나 따옴표가 닫히지 않으면 YAML 로더와 다른 값을 읽을 수
    있으므로 추측하지 않고 Unreadable 로 올린다.
    """
    pattern = re.compile(r"^" + re.escape(key) + r"\s*:\s*(.*?)\s*$")
    matches = [m for m in (pattern.match(line) for line in lines) if m]
    if not matches:
        return None
    if len(matches) > 1:
        raise Unreadable("SKILL.md frontmatter 에 %s 키가 %d번 있음" % (key, len(matches)))
    value = matches[0].group(1)
    if value[:1] in ("'", '"'):
        end = value.find(value[0], 1)
        if end < 0:
            raise Unreadable("SKILL.md frontmatter %s 의 따옴표가 닫히지 않음" % key)
        value = value[1:end]
    else:
        value = re.sub(r"\s+#.*$", "", value)
    return value.strip()


def skill_md_info(skill_dir):
    """(name, version) from SKILL.md frontmatter."""
    path = Path(skill_dir) / "SKILL.md"
    lines = _frontmatter(_read_text(path), "SKILL.md")
    version = _frontmatter_value(lines, "version")
    if not version:
        raise Unreadable("SKILL.md frontmatter 에 version 없음")
    if not _SEMVER_FULL.match(version):
        raise Unreadable("SKILL.md version 이 semver 가 아님: %s" % version)
    return _frontmatter_value(lines, "name"), version


def cases_version(skill_dir):
    path = Path(skill_dir) / "evals" / "cases.json"
    try:
        data = json.loads(_read_text(path))
    except ValueError:
        raise Unreadable("evals/cases.json JSON 파싱 실패") from None
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str) or not version.strip():
        raise Unreadable("evals/cases.json 에 version 없음")
    return version.strip()


def changelog_version(skill_dir):
    """첫 `## <semver>` 제목. 그 위에는 `## Unreleased` 만 허용한다.

    코드펜스(여는 것과 같은 문자·그 이상 길이로만 닫힌다)와 여러 줄 HTML 주석
    안의 제목은 보지 않는다.
    """
    text = _read_text(Path(skill_dir) / "CHANGELOG.md")
    fence, in_comment = None, False
    for line in text.splitlines():
        fence_match = _FENCE.match(line)
        if fence:
            marker = fence_match.group(1) if fence_match else ""
            if (marker[:1] == fence[0] and len(marker) >= len(fence)
                    and not fence_match.group(2).strip()):
                fence = None
            continue
        if in_comment:
            in_comment = "-->" not in line
            continue
        if fence_match and not (fence_match.group(1)[0] == "`" and "`" in fence_match.group(2)):
            fence = fence_match.group(1)
            continue
        stripped = line.lstrip()
        if stripped.startswith("<!--"):
            in_comment = "-->" not in stripped[4:]
            continue
        match = _H2.match(line)
        if not match:
            continue
        title = match.group(1)
        version = _VERSION_HEADING.match(title)
        if version:
            return version.group(1)
        if _UNRELEASED.match(title):
            continue
        raise Unreadable("CHANGELOG.md 첫 버전 제목 앞에 다른 제목: %s" % title[:60])
    raise Unreadable("CHANGELOG.md 에 `## <semver>` 제목 없음")


def check(skill_dir):
    """(exit_code, result_dict)."""
    result = {"skill": str(Path(skill_dir).resolve()), "skill_md": None,
              "cases": None, "changelog": None, "consistent": False, "errors": []}
    for key, reader in (("skill_md", lambda d: skill_md_info(d)[1]),
                        ("cases", cases_version), ("changelog", changelog_version)):
        try:
            result[key] = reader(skill_dir)
        except Unreadable as exc:
            result["errors"].append(str(exc))
    if result["errors"]:
        return 2, result
    values = {result["skill_md"], result["cases"], result["changelog"]}
    result["consistent"] = len(values) == 1
    return (0 if result["consistent"] else 1), result


def _precedence(version):
    """semver 2.0.0 §11 우선순위 키. 빌드 메타데이터(+...)는 무시한다."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?", version or "")
    if not match:
        return None
    core = tuple(int(part) for part in match.groups()[:3])
    if match.group(4) is None:
        return core, 1, []          # 정식 릴리스 > 같은 core 의 프리릴리스
    idents = [(0, int(p), "") if p.isdigit() else (1, 0, p)
              for p in match.group(4).split(".")]
    return core, 0, idents


def gap(running_dir, source_dir):
    """(exit_code, result_dict). 실행본 = 설치된 사본, 소스 = 저장소."""
    result = {"skill": None, "equal": False, "message": "", "errors": []}
    sides = {}
    for key, directory in (("running", running_dir), ("source", source_dir)):
        given = Path(directory)
        side = {"path": str(given), "resolved": str(given.resolve()), "version": None}
        try:
            name, side["version"] = skill_md_info(given)
            result["skill"] = result["skill"] or name
        except Unreadable as exc:
            result["errors"].append("%s: %s" % ("실행본" if key == "running" else "소스", exc))
        sides[key] = side
    result.update(sides)
    skill = result["skill"] or Path(source_dir).resolve().name or "skill"
    result["skill"] = skill
    run_v, src_v = sides["running"]["version"], sides["source"]["version"]
    if result["errors"]:
        result["message"] = "%s 버전 읽기 실패 (%s)" % (skill, "; ".join(result["errors"]))
        return 2, result
    if run_v == src_v:
        result["equal"] = True
        result["message"] = "%s 실행본과 소스 버전 일치 (%s)" % (skill, src_v)
        return 0, result
    run_key, src_key = _precedence(run_v), _precedence(src_v)
    if run_key and src_key and run_key > src_key:
        hint = "실행본이 소스보다 앞선다 - 소스 브랜치 확인 필요"
    else:
        hint = "설치 갱신 필요"
    result["message"] = "%s 실행본 %s ≠ 소스 %s (%s)" % (skill, run_v, src_v, hint)
    return 1, result


def _parser():
    parser = argparse.ArgumentParser(
        prog="version_gap.py", description="스킬 버전 정합 점검 (읽기 전용)",
        epilog="자세한 설명은 모듈 docstring 참조. 아무것도 쓰지 않는다.")
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("check", help="한 스킬 폴더 안의 세 버전 표기 대조")
    one.add_argument("--skill", required=True, help="스킬 폴더 (SKILL.md 가 있는 곳)")
    two = sub.add_parser("gap", help="설치된 실행본과 소스의 SKILL.md 버전 비교")
    two.add_argument("--running", required=True, help="설치된 실행본 폴더")
    two.add_argument("--source", required=True, help="소스 폴더")
    two.add_argument("--json", action="store_true", help="JSON 으로 출력")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    if args.command == "check":
        code, result = check(args.skill)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    code, result = gap(args.running, args.source)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["message"])
    return code


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
