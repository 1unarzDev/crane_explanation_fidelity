#!/usr/bin/env python3
"""Aggregate one prospectively frozen Luna-v7 qualification extension.

The original v7 qualification remains immutable.  This module may only add the fixed extension
denominators and errors; it never rescales, drops, or relabels either result.  Sensitivity bounds
are Wilson 95% upper endpoints rounded upward to four decimal places, matching annotation
amendment 2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from run_luna_judge_qualification_v5 import wilson_interval


ROOT = Path(__file__).resolve().parents[1]
PASS_MAP = {"pass_1": "pass-1", "pass_2": "pass-2"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def round_up_four(value: float) -> float:
    return math.ceil(value * 10_000.0 - 1e-12) / 10_000.0


def upper_error(errors: int, total: int) -> float:
    return round_up_four(wilson_interval(errors, total)["upper"])


def aggregate(base: dict[str, Any], extension: dict[str, Any]) -> dict[str, Any]:
    if base.get("status") != "HELDOUT_QUALIFIED":
        raise ValueError("base v7 result is not heldout-qualified")
    if extension.get("status") not in {"QUALIFIED", "FAILED"}:
        raise ValueError("extension result status is invalid")
    result_passes: dict[str, Any] = {}
    extension_qualified = extension["status"] == "QUALIFIED"
    combined_qualified = extension_qualified
    for output_pass, extension_pass in PASS_MAP.items():
        old = base["passes"][extension_pass]
        new = extension["passes"][extension_pass]
        composite_correct = old["composite_correct"] + new["composite"]["successes"]
        composite_total = old["composite_total"] + new["composite"]["total"]
        unit_correct = old["required_unit_correct"] + new["required_units"]["successes"]
        unit_total = old["required_unit_total"] + new["required_units"]["total"]
        core_correct = old["core_correct"] + new["core_fields"]["successes"]
        core_total = old["core_total"] + new["core_fields"]["total"]
        false_rejections = old["false_rejections"] + new["factual_false_rejections"]["errors"]
        factual_total = old["factual_total"] + new["factual_false_rejections"]["total"]
        false_acceptances = old["false_acceptances"] + new["unsupported_false_acceptances"]["errors"]
        unsupported_total = old["unsupported_total"] + new["unsupported_false_acceptances"]["total"]
        protected_failures = old["protected_failures"] + sum(
            len(items) for items in new["protected_failures"].values()
        )
        gates = {
            "composite_accuracy": composite_correct / composite_total >= 0.95,
            "required_unit_accuracy": unit_correct / unit_total >= 0.90,
            "core_semantic_field_accuracy": core_correct / core_total >= 0.90,
            "factual_false_rejection_rate": false_rejections / factual_total <= 0.15,
            "unsupported_false_acceptance_rate": false_acceptances / unsupported_total <= 0.05,
            "protected_tests": protected_failures == 0,
            "extension_standalone_qualified": new["qualified"] is True,
            "zero_extension_call_failures": new["call_failure_count"] == 0,
        }
        qualified = all(gates.values())
        combined_qualified &= qualified
        result_passes[output_pass] = {
            "qualified": qualified,
            "gates": gates,
            "composite_correct": composite_correct,
            "composite_total": composite_total,
            "required_unit_correct": unit_correct,
            "required_unit_total": unit_total,
            "core_correct": core_correct,
            "core_total": core_total,
            "false_rejections": false_rejections,
            "factual_total": factual_total,
            "false_acceptances": false_acceptances,
            "unsupported_total": unsupported_total,
            "protected_failures": protected_failures,
            "sensitivity_upper_bounds": {
                "false_acceptance": upper_error(false_acceptances, unsupported_total),
                "false_rejection": upper_error(false_rejections, factual_total),
                "required_unit_error": upper_error(unit_total - unit_correct, unit_total),
                "composite_error": upper_error(composite_total - composite_correct, composite_total),
            },
        }
    largest = {
        key: max(value["sensitivity_upper_bounds"][key] for value in result_passes.values())
        for key in ("false_acceptance", "false_rejection", "required_unit_error", "composite_error")
    }
    return {
        "schema": "crane-luna-v7-endpoint-extension-aggregate/v1",
        "status": "QUALIFIED_AGGREGATE" if combined_qualified else "FAILED_EXTENSION_RETAIN_PRIOR_V7",
        "prior_v7_result_preserved": True,
        "extension_result_preserved": True,
        "passes": result_passes,
        "largest_pass_specific_sensitivity_upper_bounds": largest,
        "eligible_for_prospective_amendment": combined_qualified,
        "hard_stop_no_additional_luna_iteration": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--extension", required=True, type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refusing to overwrite aggregate output")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    expected = freeze["inputs"]
    if digest(args.base) != expected["prior_v7_result_sha256"]:
        raise ValueError("prior v7 result hash mismatch")
    registered_extension = (ROOT / freeze["execution"]["result_path"]).resolve()
    if args.extension.resolve() != registered_extension:
        raise ValueError("extension result path differs from the pre-call registration")
    extension_payload = json.loads(args.extension.read_text(encoding="utf-8"))
    if extension_payload.get("suite_sha256") != expected["extension_suite_sha256"]:
        raise ValueError("extension result suite hash mismatch")
    payload = aggregate(
        json.loads(args.base.read_text(encoding="utf-8")),
        extension_payload,
    )
    payload["inputs"] = {
        "prior_v7_result_sha256": digest(args.base),
        "extension_result_sha256": digest(args.extension),
        "freeze_sha256": digest(args.freeze),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "bounds": payload["largest_pass_specific_sensitivity_upper_bounds"]}))
    return 0 if payload["eligible_for_prospective_amendment"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
