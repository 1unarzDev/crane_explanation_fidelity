#!/usr/bin/env python3
"""Freeze the one-shot raw-evidence v5 development treatment contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import run_measurement_complete_v2_development as base
from run_raw_baseline_v5_development import frozen_artifact_paths


ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/development"
    / "coverage-complete-v4-language-screen-v1.json"
)
DEFAULT_OUTPUT = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/development"
    / "raw-baseline-v5-language-screen-v1.json"
)
RAW_ROOT = ROOT / "data/robot_visible/dev/coverage-complete-v5-raw-baseline"
CASE_MAP = {
    "ccv4-geometry-001": ("ccv5-geometry-001", "ccv5-geometry-001.json"),
    "ccv4-geometry-masked-001m": (
        "ccv5-geometry-masked-001m",
        "ccv5-geometry-masked-001m.json",
    ),
    "ccv4-geometry-002": ("ccv5-geometry-002", "ccv5-geometry-002.json"),
    "ccv4-geometry-003": ("ccv5-geometry-003", "ccv5-geometry-003.json"),
    "ccv4-persistent-004": ("ccv5-persistent-004", "ccv5-persistent-004.json"),
    "ccv4-missing-odometry-004m": (
        "ccv5-missing-odometry-004m",
        "ccv5-missing-odometry-004m.json",
    ),
    "ccv4-compensation-005": ("ccv5-compensation-005", "ccv5-compensation-005.json"),
}


def _cases(predecessor: dict[str, Any]) -> list[dict[str, Any]]:
    renamed = {old: new for old, (new, _) in CASE_MAP.items()}
    result = []
    for old in predecessor["cases"]:
        old_id = old["case_id"]
        case_id, raw_name = CASE_MAP[old_id]
        raw_path = RAW_ROOT / raw_name
        case = {
            "case_id": case_id,
            "reference_case_id": old_id,
            "cluster_id": old["cluster_id"],
            "family": old["family"],
            "question_kind": old["question_kind"],
            "adapter": "geometric_v5" if old["adapter"].startswith("geometric") else old["adapter"],
            "diagnostic_path": old["diagnostic_path"],
            "diagnostic_sha256": old["diagnostic_sha256"],
            "baseline_evidence_path": raw_path.relative_to(ROOT).as_posix(),
            "baseline_evidence_sha256": base.sha256_path(raw_path),
            "independent_cluster": old["independent_cluster"],
            "question": old["question"],
        }
        if old.get("paired_with"):
            case["paired_with"] = renamed[old["paired_with"]]
        result.append(case)
    return result


def build() -> dict[str, Any]:
    predecessor = json.loads(PREDECESSOR.read_text(encoding="utf-8"))
    contract: dict[str, Any] = {
        "schema": "crane-raw-baseline-v5-development-screen/v1",
        "screen_id": "raw-baseline-v5-language-screen-v1",
        "status": "FROZEN_BEFORE_ANY_RESPONSE_OR_JUDGMENT",
        "purpose": (
            "One fixed development-only comparison that corrects the predecessor treatment: R "
            "receives raw robot-visible observations, exact source/configuration, and executable "
            "diagnostic tools, but no precomputed checked diagnostic or reference result. It can "
            "select or reject a prospective candidate but cannot establish confirmation, "
            "significance, or replication."
        ),
        "predecessor_screen": PREDECESSOR.relative_to(ROOT).as_posix(),
        "predecessor_result": (
            "manifests/annotation/luna-coverage-complete-v4-evidence-complete-v2-result.json"
        ),
        "physical_source_screen": predecessor["physical_screen"],
        "reference_inventory": predecessor["reference_inventory"],
        "candidate": "coverage-complete-checked-composition-v5",
        "statistical_boundary": {
            "confirmatory": False,
            "confirmatory_semantic_n": 0,
            "confirmatory_alpha_consumed": 0.0,
            "independent_unit": "scenario configuration",
            "independent_clusters": 5,
            "new_independent_clusters": 0,
            "response_pairs": 7,
            "paired_masks_add_clusters": 0,
            "question_variants_add_clusters": 0,
            "model_repetitions_add_clusters": 0,
            "luna_passes_add_clusters": 0,
        },
        "repositories": predecessor["repositories"],
        "model": predecessor["model"],
        "baseline": {
            "id": "R-strong-repository-tool-enabled-raw-v1",
            "prompt": (
                "research/explanation_fidelity/prompts/"
                "diagnostic_repository_agent_raw_v1.txt"
            ),
            "same_underlying_robot_visible_observations": True,
            "same_relevant_source_and_configuration": True,
            "same_executable_diagnostic_tools": True,
            "similar_or_greater_model_resource_budget": True,
            "precomputed_diagnostic_visible": False,
            "precomputed_reference_computation_visible": False,
            "episode_certificate_visible": False,
            "checked_answer_plan_visible": False,
            "candidate_final_answer_visible": False,
            "model_calls": 1,
        },
        "candidate_policy": {
            "checked_diagnostic_computation": True,
            "mandatory_finite_composition": True,
            "geometry_adapter": "land-geometric-composition-adapter-v5",
            "command_motion_adapter": "command-motion-composition-adapter-v2",
            "deterministic_rendering": True,
            "model_calls": 0,
            "fail_closed_on_missing_required_units": True,
        },
        "treatment_rationale": {
            "correction": (
                "The predecessor gave R diagnostic_result and reference_computation, which "
                "substantially encoded P's mechanism. V5 tests the registered distinction between "
                "an agent that may compute from raw permitted evidence and a pipeline that "
                "prospectively performs checked diagnostic computation and finite composition."
            ),
            "fairness": (
                "R retains the same raw evidence, exact repositories/configuration, executable "
                "diagnostic tools, model strength, reasoning effort, and one-call budget. No tool "
                "or measurement is withheld merely to create an advantage."
            ),
            "inferential_limit": (
                "All physical configurations and questions were already used in development; this "
                "screen adds zero independent clusters and cannot provide confirmatory evidence."
            ),
        },
        "cases": _cases(predecessor),
        "readiness_gate": predecessor["readiness_gate"],
        "stopping": (
            "Run each fixed case exactly once for R and once deterministically for P, retain every "
            "usable answer, do not resample an inconvenient result, and stop after seven pairs."
        ),
    }
    contract["frozen_artifact_sha256"] = {
        name: base.sha256_path(path) for name, path in frozen_artifact_paths(contract).items()
    }
    contract["committed_contract_sha256"] = base.sha256_json(contract)
    return contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    contract = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
