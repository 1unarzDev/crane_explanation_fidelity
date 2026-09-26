#!/usr/bin/env python3
"""Freeze the evidence-closure Luna reevaluation for raw-baseline v5."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import run_measurement_complete_v2_development as base


ROOT = Path(__file__).resolve().parents[1]
ARM = "raw-baseline-v5-language-screen-v1-evidence-closure-v2"
ORIGINAL_ARM = "raw-baseline-v5-language-screen-v1"
AMENDMENT = ROOT / (
    "research/explanation_fidelity/experiment_configs/development/"
    "raw-baseline-v5-language-screen-v1-annotation-amendment-1.json"
)
CLOSURE_BUILDER = ROOT / "analysis/build_raw_baseline_v5_evidence_closure.py"
ARTIFACT_MANIFEST = ROOT / f"manifests/model_outputs/{ARM}-freeze.json"
KEY_MANIFEST = ROOT / f"manifests/data/{ARM}.annotation-keys.evaluator-only.json"
ORIGINAL_RESPONSE_MANIFEST = ROOT / (
    "manifests/model_outputs/raw-baseline-v5-language-screen-v1-freeze.json"
)
ORIGINAL_PREDECLARATION = ROOT / (
    "manifests/annotation/luna-raw-baseline-v5-language-screen-v1-predeclaration.json"
)
INVALID_RESULT = ROOT / (
    "manifests/annotation/luna-raw-baseline-v5-language-screen-v1-result.json"
)
QUALIFICATION = ROOT / "manifests/annotation/luna-model-judge-v1-heldout-v12-final.json"
JUDGE_FREEZE = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "luna-model-judge-v12-final-freeze.json"
)
JUDGE_PROMPT = ROOT / "research/explanation_fidelity/prompts/luna-model-judge-v5.md"
JUDGE_SCHEMA = ROOT / "research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json"
JUDGE_CALLER = ROOT / "analysis/luna_model_judge.py"
JUDGE_RUNNER = ROOT / "analysis/run_luna_single_diagnostic_packet.py"
DEFAULT_OUTPUT = ROOT / f"manifests/annotation/luna-{ARM}-predeclaration.json"


def build() -> dict[str, Any]:
    original = json.loads(ORIGINAL_PREDECLARATION.read_text(encoding="utf-8"))
    return {
        "schema": "crane-luna-raw-baseline-v5-evidence-closure-predeclaration/v1",
        "arm_id": ARM,
        "status": "FROZEN_BEFORE_ANY_REVISED_LUNA_CALL",
        "declared_utc": "2026-09-26T17:45:00Z",
        "inferential_status": "DEVELOPMENT_REEVALUATION_NOT_CONFIRMATORY_NOT_REPLICATION",
        "purpose": (
            "Re-evaluate fourteen unchanged v5 responses after prospectively freezing a systematic, "
            "response-independent closure of facts exposed by R's raw evidence and tools. This arm "
            "can assess development readiness only; it cannot establish significance."
        ),
        "prior_exposure": {
            "responses_unchanged_and_previously_inspected": True,
            "first_luna_arm_judgments_inspected": 28,
            "first_luna_arm_rationales_inspected": True,
            "first_arm_invalid_for_promotion": INVALID_RESULT.relative_to(ROOT).as_posix(),
            "first_arm_invalid_result_sha256": base.sha256_path(INVALID_RESULT),
            "revised_luna_calls_generated": 0,
            "confirmatory_alpha_consumed": 0.0,
        },
        "correction": {
            "amendment": AMENDMENT.relative_to(ROOT).as_posix(),
            "amendment_sha256": base.sha256_path(AMENDMENT),
            "closure_builder": CLOSURE_BUILDER.relative_to(ROOT).as_posix(),
            "closure_builder_sha256": base.sha256_path(CLOSURE_BUILDER),
            "systematic_schema_driven_closure": True,
            "responses_changed": False,
            "required_units_changed": False,
            "prohibited_claims_changed": False,
            "judge_release_changed": False,
        },
        "frozen_artifacts": {
            "references_and_packets_manifest": ARTIFACT_MANIFEST.relative_to(ROOT).as_posix(),
            "references_and_packets_manifest_sha256": base.sha256_path(ARTIFACT_MANIFEST),
            "artifact_count": 14,
            "condition_key_manifest": KEY_MANIFEST.relative_to(ROOT).as_posix(),
            "condition_key_manifest_sha256": base.sha256_path(KEY_MANIFEST),
            "condition_key_count": 7,
            "immutable_response_manifest": ORIGINAL_RESPONSE_MANIFEST.relative_to(ROOT).as_posix(),
            "immutable_response_manifest_sha256": base.sha256_path(ORIGINAL_RESPONSE_MANIFEST),
        },
        "statistical_boundary": {
            **original["statistical_boundary"],
            "this_reevaluation_adds_clusters": 0,
        },
        "cases": original["cases"],
        "judge_release": {
            "arm": "luna-model-judge-v1",
            "qualification_manifest": QUALIFICATION.relative_to(ROOT).as_posix(),
            "qualification_manifest_sha256": base.sha256_path(QUALIFICATION),
            "qualification_status": "HELDOUT_QUALIFIED",
            "freeze": JUDGE_FREEZE.relative_to(ROOT).as_posix(),
            "freeze_sha256": base.sha256_path(JUDGE_FREEZE),
            "model": "gpt-6-luna",
            "provider": "codex-lb",
            "reasoning_effort": "high",
            "temperature": None,
            "seed": None,
            "prompt": JUDGE_PROMPT.relative_to(ROOT).as_posix(),
            "prompt_sha256": base.sha256_path(JUDGE_PROMPT),
            "output_schema": JUDGE_SCHEMA.relative_to(ROOT).as_posix(),
            "output_schema_sha256": base.sha256_path(JUDGE_SCHEMA),
            "caller": JUDGE_CALLER.relative_to(ROOT).as_posix(),
            "caller_sha256": base.sha256_path(JUDGE_CALLER),
            "runner": JUDGE_RUNNER.relative_to(ROOT).as_posix(),
            "runner_sha256": base.sha256_path(JUDGE_RUNNER),
        },
        "judge_execution": {
            "passes": ["pass-1", "pass-2"],
            "isolated_context_per_response": True,
            "planned_judgments": 28,
            "usable_judgment_retry_allowed": False,
            "inconvenient_label_retry_allowed": False,
            "output_root": f"model_outputs/automated_annotations/luna-model-judge-v1/{ARM}",
        },
        "scoring": original["scoring"],
        "stopping": (
            "Run exactly two isolated Luna judgments for each of fourteen unchanged responses. "
            "Retain every usable judgment and do not retry inconvenient labels."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    payload = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
