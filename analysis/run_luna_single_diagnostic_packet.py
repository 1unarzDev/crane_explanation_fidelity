#!/usr/bin/env python3
"""Score one immutable diagnostic packet with two isolated Luna passes.

The bounded runner accepts either the historical four-arm R/P/T/N packet or the prospectively
declared strongest-baseline comparison containing exactly R/P.  It never adds absent conditions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from luna_model_judge import LunaIsolatedCodexCaller, atomic_write_json, packet_envelope


ROOT = Path(__file__).resolve().parents[1]
V12_PROMPT = ROOT / "research/explanation_fidelity/prompts/luna-model-judge-v5.md"
V12_SCHEMA = (
    ROOT / "research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json"
)
V12_CALLER = ROOT / "analysis/luna_model_judge.py"
V12_FREEZE = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/prospective"
    / "luna-model-judge-v12-final-freeze.json"
)
V12_QUALIFICATION = ROOT / "manifests/annotation/luna-model-judge-v1-heldout-v12-final.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def qualified_release() -> dict[str, str]:
    """Fail closed unless the exact qualified v12 judge release is present."""
    qualification = load_object(V12_QUALIFICATION)
    if qualification.get("status") != "HELDOUT_QUALIFIED" or qualification.get(
        "study_evaluation_allowed"
    ) is not True:
        raise ValueError("Luna v12 is not qualified and activated for study evaluation")
    if qualification.get("qualification_id") != "luna-model-judge-v12-binary-unit-final":
        raise ValueError("unexpected Luna qualification identity")

    freeze = load_object(V12_FREEZE)
    declared_freeze = qualification.get("freeze")
    if not isinstance(declared_freeze, dict) or declared_freeze.get("sha256") != digest(V12_FREEZE):
        raise ValueError("qualified Luna result does not pin the current v12 freeze")
    expected = {
        "prompt_sha256": V12_PROMPT,
        "output_schema_sha256": V12_SCHEMA,
        "caller_source_sha256": V12_CALLER,
    }
    for field, path in expected.items():
        if freeze.get(field) != digest(path):
            raise ValueError(f"qualified Luna v12 {field} differs from the current file")

    result_spec = qualification.get("result")
    if not isinstance(result_spec, dict):
        raise ValueError("qualified Luna manifest has no retained result specification")
    result_path = ROOT / str(result_spec.get("path", ""))
    if not result_path.is_file() or result_spec.get("sha256") != digest(result_path):
        raise ValueError("retained Luna v12 qualification result is absent or differs")

    return {
        "qualification_manifest_sha256": digest(V12_QUALIFICATION),
        "qualification_result_sha256": digest(result_path),
        "freeze_sha256": digest(V12_FREEZE),
        "prompt_sha256": digest(V12_PROMPT),
        "output_schema_sha256": digest(V12_SCHEMA),
        "caller_source_sha256": digest(V12_CALLER),
        "runner_source_sha256": digest(Path(__file__)),
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def judge_visible_row(row: dict[str, Any]) -> dict[str, Any]:
    """Remove coordinator-only v12 fields without changing the frozen judge caller."""
    return {
        key: value
        for key, value in row.items()
        if key not in {
            "primary_endpoint_eligible",
            "mechanism_unit_id",
            "complete_endpoint_unit_ids",
        }
    }


def success(judgment: dict[str, Any], row: dict[str, Any] | None = None) -> bool | None:
    """Score either the qualified v12 endpoint or a retained historical packet.

    V12 success defaults to coverage of the independently declared atomic mechanism
    unit with no material error. A prospective focused packet may explicitly bind all
    question-essential unit IDs; then every bound unit must be covered. Historical
    packets did not carry endpoint metadata, so their existing generic mechanism-field
    interpretation is preserved rather than retroactively rewritten.
    """
    if row is not None and "primary_endpoint_eligible" in row:
        if row["primary_endpoint_eligible"] is not True:
            return None
        mechanism_unit_id = row.get("mechanism_unit_id")
        if not isinstance(mechanism_unit_id, str) or not mechanism_unit_id:
            raise ValueError("eligible v12 row has no mechanism unit ID")
        required_ids = row.get("complete_endpoint_unit_ids", [mechanism_unit_id])
        if (
            not isinstance(required_ids, list)
            or not required_ids
            or any(not isinstance(item, str) or not item for item in required_ids)
            or len(required_ids) != len(set(required_ids))
        ):
            raise ValueError("eligible v12 row has invalid endpoint unit IDs")
        statuses: dict[str, str] = {}
        for item in judgment.get("required_units", []):
            unit_id = item.get("unit_id")
            if unit_id in statuses:
                raise ValueError("eligible v12 judgment contains duplicate required units")
            statuses[unit_id] = item.get("status")
        if any(unit_id not in statuses for unit_id in required_ids):
            raise ValueError("eligible v12 judgment omits an endpoint required unit")
        return (
            all(statuses[unit_id] == "covered" for unit_id in required_ids)
            and judgment["material_error"] is False
        )
    return judgment["mechanism_identification"] == "correct" and judgment["material_error"] is False


def run(packet: Path, key_path: Path, output_root: Path) -> dict[str, Any]:
    judge_release = qualified_release()
    rows = read_jsonl(packet)
    if len(rows) not in {2, 4} or len({row["response_id"] for row in rows}) != len(rows):
        raise ValueError("packet must contain two or four unique responses")
    key = json.loads(key_path.read_text(encoding="utf-8"))
    conditions = {item["response_id"]: item["condition"] for item in key["entries"]}
    rows_by_id = {row["response_id"]: row for row in rows}
    if set(conditions) != {row["response_id"] for row in rows}:
        raise ValueError("packet and condition-key inventories differ")
    condition_order = tuple(condition for condition in ("R", "P", "T", "N") if condition in set(conditions.values()))
    if set(condition_order) not in ({"R", "P"}, {"R", "P", "T", "N"}):
        raise ValueError("condition inventory must be exactly R/P or R/P/T/N")
    joined: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    cache_keys: dict[str, dict[str, str]] = {}
    for pass_id in ("pass-1", "pass-2"):
        caller = LunaIsolatedCodexCaller(
            cache=output_root / "calls" / "high" / pass_id,
            effort="high",
            prompt_path=V12_PROMPT,
        )
        cache_keys[pass_id] = {}
        for row in rows:
            response_id = row["response_id"]
            try:
                record = caller.call(packet_envelope(judge_visible_row(row), "diagnostic", pass_id))
            except RuntimeError as error:
                failures.append(
                    {
                        "pass_id": pass_id,
                        "response_id": response_id,
                        "condition": conditions[response_id],
                        "error": str(error),
                    }
                )
                continue
            cache_keys[pass_id][response_id] = record["cache_key"]
            joined.append(
                {
                    "pass_id": pass_id,
                    "response_id": response_id,
                    "condition": conditions[response_id],
                    "judgment": record["judgment"],
                }
            )
    passes: dict[str, Any] = {}
    for pass_id in ("pass-1", "pass-2"):
        selected = [item for item in joined if item["pass_id"] == pass_id]
        pass_result: dict[str, Any] = {}
        for condition in condition_order:
            matches = [
                item["judgment"]
                for item in selected
                if item["condition"] == condition
            ]
            if len(matches) > 1:
                raise ValueError(f"duplicate {pass_id} judgment for {condition}")
            if not matches:
                pass_result[condition] = {
                    "judgment_status": "missing_due_to_retained_call_failure",
                    "supported_diagnostic_success": None,
                    "material_error": None,
                    "mechanism_identification": None,
                }
                continue
            judgment = matches[0]
            response_id = next(
                item["response_id"]
                for item in selected
                if item["condition"] == condition
            )
            row = rows_by_id[response_id]
            endpoint = success(judgment, row)
            pass_result[condition] = {
                "judgment_status": "valid",
                "supported_diagnostic_success": endpoint,
                "primary_endpoint_eligible": row.get("primary_endpoint_eligible"),
                "mechanism_unit_id": row.get("mechanism_unit_id"),
                "complete_endpoint_unit_ids": row.get("complete_endpoint_unit_ids"),
                "endpoint_scoring_policy": (
                    (
                        "focused_all_question_essential_units_covered_and_no_material_error"
                        if row.get("complete_endpoint_unit_ids") is not None
                        else "v12_atomic_mechanism_unit_covered_and_no_material_error"
                    )
                    if "primary_endpoint_eligible" in row
                    else "historical_generic_mechanism_field_and_no_material_error"
                ),
                "material_error": judgment["material_error"],
                "mechanism_identification": judgment["mechanism_identification"],
            }
        pass_result["complete"] = all(
            pass_result[condition]["judgment_status"] == "valid"
            for condition in condition_order
        )
        passes[pass_id] = pass_result
    report = {
        "schema": "crane-luna-single-diagnostic-packet-result/v1",
        "status": (
            "DEVELOPMENT_ONLY_NOT_CONFIRMATORY"
            if not failures
            else "DEVELOPMENT_ONLY_INCOMPLETE_JUDGE_FAILURE"
        ),
        "packet_sha256": digest(packet),
        "condition_key_sha256": digest(key_path),
        "qualified_judge_release": judge_release,
        "passes": passes,
        "call_failures": failures,
        "valid_judgments": len(joined),
        "planned_judgments": 2 * len(rows),
        "conditions": list(condition_order),
        "cache_keys": cache_keys,
        "confirmatory_alpha_consumed": 0.0,
    }
    atomic_write_json(output_root / "development-summary.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    output = args.output_root.resolve()
    if (output / "development-summary.json").exists():
        raise SystemExit("refusing to overwrite completed result")
    report = run(args.packet.resolve(strict=True), args.key.resolve(strict=True), output)
    print(json.dumps({"status": report["status"], "call_failures": len(report["call_failures"])}))
    return 0 if not report["call_failures"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
