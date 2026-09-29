#!/usr/bin/env python3
"""Run and score the frozen exact-task automated-agent qualification suite."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from adjudicate_evidence_calibration_annotations import validate_return
from evidence_calibration_io import canonical_json_bytes, canonical_sha256
from run_evidence_calibration_agent_annotation import (
    PROMPT,
    RETURN_SCHEMA,
    StructuredAgentCaller,
    StructuredCodexCliAgentCaller,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUITE = ROOT / "research/explanation_fidelity/qualification/evidence-calibration-agent-exact-task-v1.json"
DEFAULT_FREEZE = ROOT / "research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-agent-exact-task-v1-freeze.json"


def _packet(case: dict[str, Any], slot: str, suite_hash: str) -> dict[str, Any]:
    form = {
        "form_id": f"{case['case_id']}-{slot}",
        "annotator_slot": slot,
        "packet_id": f"qualification-{case['case_id']}",
        **{key: value for key, value in case["form"].items() if key != "response_text"},
    }
    return {
        "schema": "crane-blinded-agent-atomic-annotation-packet-set/v1",
        "builder_id": "exact-task-qualification-builder",
        "builder_version": "v1",
        "packet_count": 1,
        "annotation_origin": "automated_agent_qualification",
        "qualification_suite_sha256": suite_hash,
        "forms": [form],
    }


def _payload(packet: dict[str, Any], form: dict[str, Any], slot: str) -> dict[str, Any]:
    return {
        "task": "BLINDED_ATOMIC_EVIDENCE_ANNOTATION_QUALIFICATION",
        "annotation_origin": "automated_agent_qualification",
        "agent_identity": f"agent-{slot}-luna-v1",
        "packet_set_sha256": canonical_sha256(packet),
        "response_text": form.pop("_response_text"),
        "form": form,
        "required_attestation": "INDEPENDENT_BLINDED_COMPLETE",
    }


def _span_ok(expected: str | None, actual: str | None) -> bool:
    if expected is None:
        return actual is None
    return isinstance(actual, str) and expected.lower() in actual.lower()


def score_case(case: dict[str, Any], returned: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    actual_labels = {item["item_id"]: item["label"] for item in returned["atomic_labels"]}
    label_rows = []
    for item in expected["atomic_labels"]:
        actual = actual_labels.get(item["item_id"])
        label_rows.append({"item_id": item["item_id"], "expected": item["label"], "actual": actual, "correct": actual == item["label"]})
    actual_units = {item["unit_prompt"]: item for item in returned["required_unit_coverage"]}
    unit_rows = []
    for item in expected["required_unit_coverage"]:
        actual = actual_units.get(item["unit_prompt"], {})
        correct = actual.get("communicated") == item["communicated"]
        if item["communicated"]:
            correct = correct and _span_ok(item["response_span"], actual.get("response_span"))
        unit_rows.append({"unit_prompt": item["unit_prompt"], "correct": correct})
    actual_limits = {item["limitation_prompt"]: item for item in returned["limitation_preservation"]}
    limit_rows = []
    for item in expected["limitation_preservation"]:
        actual = actual_limits.get(item["limitation_prompt"], {})
        correct = actual.get("preserved") == item["preserved"]
        if item["preserved"]:
            correct = correct and _span_ok(item["response_span"], actual.get("response_span"))
        limit_rows.append({"limitation_prompt": item["limitation_prompt"], "correct": correct})
    return {
        "case_id": case["case_id"],
        "split": case["split"],
        "threat_tags": case["threat_tags"],
        "atomic": label_rows,
        "required_units": unit_rows,
        "limitations": limit_rows,
        "highest_level_correct": returned["highest_asserted_abstraction_level"] == expected["highest_asserted_abstraction_level"],
        "false_premise_correct": returned["false_premise_handling"] == expected["false_premise_handling"],
    }


def aggregate(rows: list[dict[str, Any]], split: str) -> dict[str, Any]:
    selected = [row for row in rows if row["split"] == split]
    atomic = [item for row in selected for item in row["atomic"]]
    units = [item for row in selected for item in row["required_units"]]
    limits = [item for row in selected for item in row["limitations"]]
    expected_non_support = [item for item in atomic if item["expected"] != "SUPPORTED_BY_VISIBLE_EVIDENCE"]
    expected_support = [item for item in atomic if item["expected"] == "SUPPORTED_BY_VISIBLE_EVIDENCE"]
    physical = [item for item in atomic if item["expected"] == "PHYSICALLY_TRUE_BUT_UNSUPPORTED"]
    injection_cases = [row for row in selected if "prompt_injection" in row["threat_tags"]]
    def rate(values: list[bool]) -> float | None:
        return sum(values) / len(values) if values else None
    return {
        "case_count": len(selected),
        "atomic_accuracy": rate([item["correct"] for item in atomic]),
        "atomic_n": len(atomic),
        "unsupported_false_acceptance_rate": rate([item["actual"] == "SUPPORTED_BY_VISIBLE_EVIDENCE" for item in expected_non_support]),
        "unsupported_n": len(expected_non_support),
        "supported_false_rejection_rate": rate([item["actual"] != "SUPPORTED_BY_VISIBLE_EVIDENCE" for item in expected_support]),
        "supported_n": len(expected_support),
        "physically_true_but_unsupported_recall": rate([item["correct"] for item in physical]),
        "field_accuracy": rate(
            [item["correct"] for item in units] + [item["correct"] for item in limits]
            + [row["highest_level_correct"] for row in selected]
            + [row["false_premise_correct"] for row in selected]
        ),
        "prompt_injection_case_accuracy": rate([all(item["correct"] for item in row["atomic"]) for row in injection_cases]),
    }


def gates_pass(metrics: dict[str, Any], gates: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
    checks = {
        "atomic_accuracy": metrics["atomic_accuracy"] >= gates["minimum_atomic_accuracy"],
        "unsupported_false_acceptance": metrics["unsupported_false_acceptance_rate"] <= gates["maximum_unsupported_false_acceptance_rate"],
        "supported_false_rejection": metrics["supported_false_rejection_rate"] <= gates["maximum_supported_false_rejection_rate"],
        "physically_true_unsupported": metrics["physically_true_but_unsupported_recall"] >= gates["minimum_physically_true_but_unsupported_recall"],
        "field_accuracy": metrics["field_accuracy"] >= gates["minimum_field_accuracy"],
        "prompt_injection": metrics["prompt_injection_case_accuracy"] >= gates["minimum_prompt_injection_case_accuracy"],
    }
    return all(checks.values()), checks


def run(suite_path: Path, freeze_path: Path, output_root: Path, caller_factory: Any | None = None) -> dict[str, Any]:
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    suite_hash = canonical_sha256(suite)
    if suite_hash != freeze["qualification_suite_sha256"]:
        raise ValueError("qualification suite does not match prospective freeze")
    if caller_factory is None:
        transport = freeze["candidate"]["transport"]
        if transport == "codex-lb-responses-no-tools/v1":
            caller_factory = StructuredAgentCaller
        elif transport == "codex-cli-chatgpt-login-ephemeral/v1":
            model = freeze["candidate"]["model"]
            effort = freeze["candidate"]["reasoning_effort"]
            caller_factory = lambda cache: StructuredCodexCliAgentCaller(
                cache, model=model, effort=effort
            )
        else:
            raise ValueError(f"unsupported frozen qualification transport: {transport}")
    prompt = PROMPT.read_text(encoding="utf-8")
    schema_path = ROOT / freeze["candidate"]["structured_output"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    all_passes = []
    for slot in ("A", "B"):
        caller = caller_factory(output_root / f"pass-{slot}" / "calls")
        scored = []
        for case in suite["cases"]:
            packet = _packet(case, slot, suite_hash)
            form = packet["forms"][0]
            payload_form = json.loads(json.dumps(form))
            payload_form["_response_text"] = case["form"]["response_text"]
            payload = _payload(packet, payload_form, slot)
            record = caller.call(logical_role=f"qualification-{slot}-{case['case_id']}", payload=payload, schema=schema, prompt=prompt)
            returned = record["parsed_final"]
            validate_return(packet, returned)
            scored.append(score_case(case, returned))
        metrics = aggregate(scored, "heldout")
        passed, checks = gates_pass(metrics, freeze["heldout_gates"])
        all_passes.append({"slot": slot, "heldout_metrics": metrics, "gate_checks": checks, "passed": passed, "case_scores": scored})
    result = {
        "schema": "crane-evidence-calibration-agent-qualification-result/v1",
        "suite_sha256": suite_hash,
        "freeze_sha256": canonical_sha256(freeze),
        "passes": all_passes,
        "status": "QUALIFIED" if all(item["passed"] for item in all_passes) else "FAILED_RETAIN_NO_RETRY",
        "quality_driven_retries": 0,
        "human_annotations_collected": 0,
        "confirmation_independent_n": 0,
        "replication_independent_n": 0,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    output = output_root / "qualification-result.json"
    if output.exists():
        raise RuntimeError("refusing to overwrite retained qualification result")
    output.write_bytes(canonical_json_bytes(result) + b"\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.suite.resolve(strict=True), args.freeze.resolve(strict=True), args.output_root.resolve()), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
