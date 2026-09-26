"""Score recorded selections without invoking a provider or executing a skill."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, expected, label):
    require(isinstance(value, dict) and set(value) == set(expected.split()),
            f"{label}: expected exactly {expected}")


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label}: nonblank string required")


def names(value):
    require(isinstance(value, list), "skill names: array required")
    require(all(isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9_.-]+(?::[A-Za-z0-9_.-]+)*", item)
                for item in value), "skill names: exact identifiers required")
    require(len(set(value)) == len(value), "skill names: duplicates are invalid")
    return set(value)


def document(value, expected):
    fields(value, expected, "document")
    require(type(value["schema_version"]) is int and value["schema_version"] == 1,
            "schema_version must be integer 1")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def load_json(path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    with Path(path).open("rb") as stream:
        raw = stream.read(1024 * 1024 + 1)
    require(len(raw) <= 1024 * 1024, "input exceeds 1 MiB")
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique_keys)


def evaluate(cases, results=None):
    document(cases, "schema_version cases")
    require(isinstance(cases["cases"], list) and cases["cases"], "cases: nonempty array required")
    indexed = {}
    for case in cases["cases"]:
        fields(case, "id prompt acceptable forbidden kind", "case")
        text(case["id"], "case.id")
        text(case["prompt"], "case.prompt")
        require(case["id"] not in indexed, "duplicate case id")
        require(case["kind"] in ("positive", "negative", "explicit"), "unknown case kind")
        require(isinstance(case["acceptable"], list) and case["acceptable"],
                "acceptable: nonempty array required")
        forbidden = names(case["forbidden"])
        accepted = [names(selection) for selection in case["acceptable"]]
        require(all(not selection & forbidden for selection in accepted),
                "acceptable selection conflicts with forbidden skills")
        indexed[case["id"]] = (accepted, forbidden)
    output = {"schema_version": 1, "status": "pending", "cases_sha256": digest(cases),
              "native_compatibility_verified": False, "evidence_authenticity_verified": False,
              "catalog_binding_verified": False, "conditions": {}, "regressions": []}
    for arm in ("before", "after"):
        output["conditions"][arm] = {"catalog_sha256": None, "scored_count": 0, "correct_count": 0,
                                     "total_count": len(indexed), "missing_case_ids": list(indexed),
                                     "records": []}
    if results is None:
        return output
    document(results, "schema_version evaluator conditions")
    evaluator = results["evaluator"]
    fields(evaluator, "host model effort observation_kind", "evaluator")
    for key in ("host", "model", "effort"):
        text(evaluator[key], f"evaluator.{key}")
    require(evaluator["observation_kind"] in ("native-session", "isolated-description-only", "static-review"),
            "unknown observation_kind")
    require(isinstance(results["conditions"], list), "conditions: array required")
    output.update(evaluator=dict(evaluator), results_sha256=digest(results))
    seen_arms, correctness = set(), {}
    for condition in results["conditions"]:
        fields(condition, "id catalog_sha256 records", "condition")
        arm = condition["id"]
        require(isinstance(arm, str) and arm in ("before", "after") and arm not in seen_arms,
                "unknown or duplicate condition id")
        sha = condition["catalog_sha256"]
        require(isinstance(sha, str) and re.fullmatch(r"[0-9a-fA-F]{64}", sha), "invalid catalog_sha256")
        require(isinstance(condition["records"], list), "records: array required")
        seen_arms.add(arm)
        scored, selected_cases = output["conditions"][arm], set()
        scored["catalog_sha256"] = sha
        for record in condition["records"]:
            fields(record, "case_id selected evidence", "record")
            case_id = record["case_id"]
            require(isinstance(case_id, str) and case_id in indexed and case_id not in selected_cases,
                    "unknown or duplicate record case_id")
            selected = names(record["selected"])
            text(record["evidence"], "record.evidence")
            accepted, forbidden = indexed[case_id]
            correct = selected in accepted and not bool(selected & forbidden)
            selected_cases.add(case_id)
            correctness[(arm, case_id)] = correct
            scored["records"].append({"case_id": case_id, "selected": record["selected"], "correct": correct,
                                      "forbidden_selected": sorted(selected & forbidden)})
        scored.update(scored_count=len(selected_cases),
                      correct_count=sum(record["correct"] for record in scored["records"]),
                      missing_case_ids=[case_id for case_id in indexed if case_id not in selected_cases])
    output["regressions"] = [case_id for case_id in indexed
                             if correctness.get(("before", case_id)) is True
                             and correctness.get(("after", case_id)) is False]
    complete = all(not arm["missing_case_ids"] for arm in output["conditions"].values())
    passed = not output["regressions"] and output["conditions"]["after"]["correct_count"] == len(indexed)
    output["status"] = ("incomplete" if not complete else
                        "recorded_comparison_passed" if passed else "recorded_comparison_failed")
    return output


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def main(argv=None):
    parser = JsonArgumentParser(description=__doc__, add_help=False, allow_abbrev=False)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--results")
    try:
        args = parser.parse_args(argv)
        output = evaluate(load_json(args.cases), load_json(args.results) if args.results else None)
    except (OSError, ValueError, RecursionError) as error:
        output = {"schema_version": 1, "status": "invalid_input", "error": str(error)}
    print(json.dumps(output, ensure_ascii=True))
    return (0 if output["status"] == "recorded_comparison_passed" else
            2 if output["status"] in ("pending", "incomplete") else 1)


if __name__ == "__main__":
    raise SystemExit(main())
