# sync_task_ranking.py — SKILL.md 의 기본 작업 순위표를 references/task-fit-policy.json 에서 다시 만든다 (D-127).
#
# 정본은 task-fit-policy.json 이다. SKILL.md 의 TASK-RANKING 마커 사이는 파생물이라 손으로 고치지 않는다.
#
# 사용:
#   python sync_task_ranking.py --check   표가 어긋났는지만 본다 (어긋나면 exit 1)
#   python sync_task_ranking.py           SKILL.md 의 마커 사이를 다시 쓴다
import hashlib
import itertools
import os
import sys

# Plain Python entrypoints must not add unreceipted bytecode to a bundle.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import orchestrate  # noqa: E402

SKILL = os.path.join(os.path.dirname(_HERE), "SKILL.md")
POLICY = orchestrate.TASK_FIT_PATH
BEGIN = "<!-- TASK-RANKING:BEGIN"
END = "<!-- TASK-RANKING:END -->"
TOOL_LABELS = {"agy-prose": "Gemini 4 Argon via `agy-prose`", "codex-image": "Codex `image_gen`",
               "host-image": "host image adapter"}


def label(entry):
    if "tool" in entry:
        return TOOL_LABELS[entry["tool"]]
    name = "`" + entry["model"] + "`"
    return name + (" @" + "/".join(entry["efforts"]) if entry.get("efforts") else "")


def render(policy, policy_bytes):
    """The generated block, markers included. Equal ranks are joined with '='."""
    sha = hashlib.sha256(policy_bytes).hexdigest()[:12]
    lines = [BEGIN + " generated from references/task-fit-policy.json sha256 " + sha
             + " by scripts/sync_task_ranking.py; edit the JSON, not this table -->",
             "| Task type | Default order (first = rank 1) | Every ranked route blocked |",
             "| --- | --- | --- |"]
    fallbacks = policy.get("fallback_task_types", {})
    for name, contract in orchestrate.TASK_TYPE_MAP.items():
        entries = sorted(policy["profiles"].get(name, []), key=lambda entry: entry["rank"])
        if entries:
            groups = itertools.groupby(entries, key=lambda entry: entry["rank"])
            order = " → ".join(" = ".join(label(entry) for entry in group) for _, group in groups)
            blocked = "replan as `" + fallbacks[name] + "`" if name in fallbacks else "situational"
        elif contract["kind"] == "gui":
            order, blocked = "vibe-bot (Grok Bot) only", "fixed route"
        else:
            order, blocked = "not ranked", "situational"
        lines.append("| `" + name + "` | " + order + " | " + blocked + " |")
    lines.append("Valid " + policy["checked_at"] + " to " + policy["valid_until"] + " (`" + policy["version"]
                 + "`); outside that window every type is situational.")
    lines.append(END)
    return "\n".join(lines)


def current_block(text):
    start, end = text.find(BEGIN), text.find(END)
    if start < 0 or end < 0:
        return None, start, end
    return text[start:end + len(END)], start, end


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raw = open(POLICY, "rb").read()
    fresh = render(orchestrate.load_task_fit_policy(POLICY), raw)
    with open(SKILL, "r", encoding="utf-8") as stream:
        text = stream.read()
    block, start, end = current_block(text)
    if block is None:
        print("SKILL.md 에 TASK-RANKING 마커가 없다 — 단일 출처가 깨졌다")
        return 2
    if block == fresh:
        print("동기 OK — SKILL.md 순위표가 task-fit-policy.json 과 일치한다")
        return 0
    if "--check" in argv:
        print("어긋남 — SKILL.md 순위표가 task-fit-policy.json 과 다르다. `python sync_task_ranking.py` 로 다시 만들 것")
        return 1
    with open(SKILL, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(text[:start] + fresh + text[end + len(END):])
    print("SKILL.md 순위표를 task-fit-policy.json 에서 다시 만들었다")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
