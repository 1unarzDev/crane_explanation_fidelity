#!/usr/bin/env python3
"""Score one blinded P-contract/R-contract packet with two isolated Luna passes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from .luna_model_judge import LunaIsolatedCodexCaller, atomic_write_json, packet_envelope
    from .score_contract_complete_judgment import score as score_contract
except ImportError:  # Direct execution: ``python analysis/run_contract_complete_luna_packet.py``.
    from luna_model_judge import LunaIsolatedCodexCaller, atomic_write_json, packet_envelope
    from score_contract_complete_judgment import score as score_contract


ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "research/explanation_fidelity/prompts/luna-model-judge-v5.md"
OUTPUT_SCHEMA = ROOT / "research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json"
CALLER = ROOT / "analysis/luna_model_judge.py"
FREEZE = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "contract-complete-luna-qualification-v2-freeze.json"
)
QUALIFICATION_MANIFEST = ROOT / "manifests/annotation/contract-complete-luna-qualification-v2-result.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def qualified_release() -> dict[str, str]:
    manifest = load_object(QUALIFICATION_MANIFEST)
    if manifest.get("status") != "HELDOUT_QUALIFIED" or manifest.get("study_evaluation_allowed") is not True:
        raise ValueError("contract-complete Luna v2 is not qualified")
    if manifest.get("qualification_id") != "contract-complete-luna-qualification-v2":
        raise ValueError("unexpected contract-complete qualification identity")
    result_spec = manifest.get("result", {})
    result_path = ROOT / str(result_spec.get("path", ""))
    if not result_path.is_file() or result_spec.get("sha256") != digest(result_path):
        raise ValueError("retained contract-complete qualification result differs")
    result = load_object(result_path)
    if result.get("status") != "QUALIFIED" or result.get("study_scoring_allowed") is not True:
        raise ValueError("retained contract-complete qualification did not qualify")
    if result.get("freeze_sha256") != digest(FREEZE):
        raise ValueError("qualification result does not bind current v2 freeze")
    freeze = load_object(FREEZE)
    for field, path in {
        "prompt_sha256": PROMPT,
        "output_schema_sha256": OUTPUT_SCHEMA,
        "caller_source_sha256": CALLER,
    }.items():
        if freeze.get(field) != digest(path):
            raise ValueError(f"contract-complete qualified {field} differs")
    return {
        "qualification_id": manifest["qualification_id"],
        "qualification_status": manifest["status"],
        "qualification_manifest_sha256": digest(QUALIFICATION_MANIFEST),
        "qualification_result_sha256": digest(result_path),
        "freeze_sha256": digest(FREEZE),
        "prompt_sha256": digest(PROMPT),
        "output_schema_sha256": digest(OUTPUT_SCHEMA),
        "caller_source_sha256": digest(CALLER),
        "runner_source_sha256": digest(Path(__file__)),
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def judge_visible(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in row.items()
        if key not in {"primary_endpoint_eligible", "mechanism_unit_id", "complete_endpoint_unit_ids"}
    }


def endpoint_record(judgment: dict[str, Any]) -> dict[str, Any]:
    scored = score_contract(judgment)
    return {
        "claim_a_complete_supported_communication": scored["claim_a_complete_supported_communication"],
        "claim_b_substantive_assertion_error": scored["claim_b_substantive_assertion_error"],
        "fields": scored["fields"],
        "failed_fields": scored["failed_fields"],
        "unresolved_fields": scored["unresolved_fields"],
        "material_error": scored["broader_material_error"],
    }


def run(packet: Path, key_path: Path, output_root: Path) -> dict[str, Any]:
    release = qualified_release()
    rows = read_jsonl(packet)
    if len(rows) != 2 or len({row.get("response_id") for row in rows}) != 2:
        raise ValueError("contract packet must contain exactly two unique responses")
    for row in rows:
        if row.get("complete_endpoint_unit_ids") != ["M", "Q", "O", "L"]:
            raise ValueError("contract packet endpoint inventory is not exact M/Q/O/L")
    key = load_object(key_path)
    conditions = {item["response_id"]: item["condition"] for item in key["entries"]}
    if set(conditions.values()) != {"P", "R"} or set(conditions) != {row["response_id"] for row in rows}:
        raise ValueError("contract packet/key inventory mismatch")
    failures: list[dict[str, str]] = []
    judgments: list[dict[str, Any]] = []
    cache_keys: dict[str, dict[str, str]] = {}
    for pass_id in ("pass-1", "pass-2"):
        caller = LunaIsolatedCodexCaller(
            cache=output_root / "calls" / "high" / pass_id,
            effort="high", prompt_path=PROMPT,
        )
        cache_keys[pass_id] = {}
        for row in rows:
            response_id = row["response_id"]
            try:
                record = caller.call(packet_envelope(judge_visible(row), "diagnostic", pass_id))
            except RuntimeError as error:
                failures.append({"pass_id": pass_id, "response_id": response_id, "condition": conditions[response_id], "error": str(error)})
                continue
            cache_keys[pass_id][response_id] = record["cache_key"]
            judgments.append({
                "pass_id": pass_id, "response_id": response_id,
                "condition": conditions[response_id],
                "endpoint": endpoint_record(record["judgment"]),
            })
    passes: dict[str, Any] = {}
    for pass_id in ("pass-1", "pass-2"):
        pass_result: dict[str, Any] = {}
        for condition in ("P", "R"):
            matches = [item for item in judgments if item["pass_id"] == pass_id and item["condition"] == condition]
            if len(matches) > 1:
                raise ValueError("duplicate contract judgment")
            pass_result[condition] = (
                {"judgment_status": "valid", **matches[0]["endpoint"]}
                if matches else {
                    "judgment_status": "missing_due_to_retained_call_failure",
                    "claim_a_complete_supported_communication": None,
                    "claim_b_substantive_assertion_error": None,
                }
            )
        pass_result["complete"] = all(pass_result[c]["judgment_status"] == "valid" for c in ("P", "R"))
        passes[pass_id] = pass_result
    report = {
        "schema": "crane-contract-complete-luna-packet-result/v1",
        "status": "DEVELOPMENT_ONLY_COMPLETE" if not failures else "DEVELOPMENT_ONLY_INCOMPLETE_JUDGE_FAILURE",
        "packet_sha256": digest(packet), "condition_key_sha256": digest(key_path),
        "qualified_judge_release": release, "passes": passes,
        "call_failures": failures, "valid_judgments": len(judgments), "planned_judgments": 4,
        "cache_keys": cache_keys, "confirmatory_alpha_consumed": 0.0,
    }
    atomic_write_json(output_root / "development-summary.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--packet",required=True,type=Path);parser.add_argument("--key",required=True,type=Path);parser.add_argument("--output-root",required=True,type=Path);args=parser.parse_args()
    output=args.output_root.resolve()
    if (output/"development-summary.json").exists(): raise FileExistsError("contract packet result exists")
    report=run(args.packet.resolve(strict=True),args.key.resolve(strict=True),output)
    print(json.dumps({"status":report["status"],"call_failures":len(report["call_failures"])}))
    return 0 if not report["call_failures"] else 2


if __name__=="__main__": raise SystemExit(main())
