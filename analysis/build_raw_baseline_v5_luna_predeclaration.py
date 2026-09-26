#!/usr/bin/env python3
"""Freeze the Luna arm for the raw-baseline-v5 development screen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import run_measurement_complete_v2_development as base


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/development"
    / "raw-baseline-v5-language-screen-v1.json"
)
ARTIFACT_MANIFEST = (
    ROOT / "manifests/model_outputs/raw-baseline-v5-language-screen-v1-freeze.json"
)
KEY_MANIFEST = (
    ROOT
    / "manifests/data/raw-baseline-v5-language-screen-v1.annotation-keys.evaluator-only.json"
)
REFERENCE_BUILDER = ROOT / "analysis/build_raw_baseline_v5_annotation_reference.py"
PACKET_BUILDER = ROOT / "analysis/build_diagnostic_annotation_packet.py"
QUALIFICATION = ROOT / "manifests/annotation/luna-model-judge-v1-heldout-v12-final.json"
JUDGE_FREEZE = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/prospective"
    / "luna-model-judge-v12-final-freeze.json"
)
JUDGE_PROMPT = ROOT / "research/explanation_fidelity/prompts/luna-model-judge-v5.md"
JUDGE_SCHEMA = (
    ROOT / "research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json"
)
JUDGE_CALLER = ROOT / "analysis/luna_model_judge.py"
JUDGE_RUNNER = ROOT / "analysis/run_luna_single_diagnostic_packet.py"
DEFAULT_OUTPUT = (
    ROOT
    / "manifests/annotation/luna-raw-baseline-v5-language-screen-v1-predeclaration.json"
)


def build() -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    cases = [
        {
            "case_id": item["case_id"],
            "cluster_id": item["cluster_id"],
            "independent_cluster": item["independent_cluster"],
            "primary_endpoint_eligible": item["reference_case_id"]
            not in {
                "ccv4-geometry-masked-001m",
                "ccv4-missing-odometry-004m",
            },
            "mechanism_unit_id": {
                "ccv4-geometry-001": "mechanism-bounded-geometric-restriction",
                "ccv4-geometry-002": "mechanism-bounded-geometric-restriction",
                "ccv4-geometry-003": "mechanism-bounded-geometric-restriction",
                "ccv4-persistent-004": "mechanism-command-motion-discrepancy",
                "ccv4-compensation-005": "mechanism-measured-response-recovery",
            }.get(item["reference_case_id"]),
        }
        for item in contract["cases"]
    ]
    return {
        "schema": "crane-luna-raw-baseline-v5-development-predeclaration/v1",
        "arm_id": "raw-baseline-v5-language-screen-v1",
        "status": "FROZEN_BEFORE_ANY_LUNA_STUDY_CALL",
        "declared_utc": "2026-09-26T16:30:00Z",
        "inferential_status": "DEVELOPMENT_ONLY_NOT_CONFIRMATORY_NOT_REPLICATION",
        "purpose": (
            "Evaluate the seven immutable one-shot P/R pairs after correcting method treatment "
            "parity: R received raw robot-visible evidence plus exact source/configuration and "
            "executable tools, but no precomputed checked diagnosis. This screen can select or "
            "reject a future prospective candidate; it cannot establish significance."
        ),
        "prior_exposure": {
            "physical_configurations_previously_used_in_development": True,
            "predecessor_v4_results_and_luna_labels_inspected": True,
            "v5_candidate_responses_generated": 7,
            "v5_baseline_responses_generated": 7,
            "v5_baseline_responses_semantically_reviewed_before_freeze": False,
            "luna_study_judgments_generated": 0,
            "confirmatory_alpha_consumed": 0.0,
        },
        "treatment_contract": {
            "path": CONTRACT.relative_to(ROOT).as_posix(),
            "file_sha256": base.sha256_path(CONTRACT),
            "committed_contract_sha256": contract["committed_contract_sha256"],
            "status": contract["status"],
        },
        "frozen_artifacts": {
            "results_references_packets_manifest": ARTIFACT_MANIFEST.relative_to(ROOT).as_posix(),
            "results_references_packets_manifest_sha256": base.sha256_path(ARTIFACT_MANIFEST),
            "artifact_count": 21,
            "condition_key_manifest": KEY_MANIFEST.relative_to(ROOT).as_posix(),
            "condition_key_manifest_sha256": base.sha256_path(KEY_MANIFEST),
            "condition_key_count": 7,
            "reference_builder": REFERENCE_BUILDER.relative_to(ROOT).as_posix(),
            "reference_builder_sha256": base.sha256_path(REFERENCE_BUILDER),
            "packet_builder": PACKET_BUILDER.relative_to(ROOT).as_posix(),
            "packet_builder_sha256": base.sha256_path(PACKET_BUILDER),
        },
        "reference_boundary": {
            "independent_reference_computations": True,
            "raw_evidence_and_source_configuration_binding": True,
            "proposed_diagnostic_used_as_gold": False,
            "proposed_plan_verifier_or_answer_visible_to_judge": False,
            "evaluator_truth_visible_to_judge": False,
            "required_units_changed_from_predecessor": False,
        },
        "statistical_boundary": {
            "independent_unit": "scenario configuration",
            "independent_clusters": 5,
            "new_independent_clusters": 0,
            "response_pairs": 7,
            "responses": 14,
            "paired_masks_add_clusters": 0,
            "repeated_judge_passes_add_clusters": 0,
            "confirmatory_semantic_n": 0,
            "confirmatory_alpha_consumed": 0.0,
        },
        "cases": cases,
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
            "output_root": (
                "model_outputs/automated_annotations/luna-model-judge-v1/"
                "raw-baseline-v5-language-screen-v1"
            ),
        },
        "scoring": {
            "primary_endpoint": (
                "For independently declared diagnosable questions, the atomic mechanism unit is "
                "covered and the final answer contains no material unsupported or contradicted assertion."
            ),
            "primary_endpoint_cases": [
                item["case_id"] for item in cases if item["primary_endpoint_eligible"]
            ],
            "guardrail_cases": [
                item["case_id"] for item in cases if not item["primary_endpoint_eligible"]
            ],
            "readiness_gate": (
                "Recurring P advantage across at least two independent clusters and two mechanism "
                "families; no P excess material error or causal overclaim; no useful-coverage "
                "degradation; correct masked and false-premise handling; complete method and judge "
                "evidence parity. Do not relax this gate after labels."
            ),
        },
        "stopping": (
            "Run exactly two isolated Luna judgments for each of fourteen immutable responses. "
            "Retain all usable judgments; do not retry inconvenient labels."
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
