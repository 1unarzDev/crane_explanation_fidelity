#!/usr/bin/env python3
"""Run one frozen v5 development pair with a raw-evidence, tool-enabled baseline R."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

import run_measurement_complete_v2_development as base
from build_checked_composition_annotation_reference import build_reference, load_inventory
from build_command_motion_composition_packet_v2 import build as build_command_packet
from build_geometric_composition_packet_v5 import build as build_geometric_packet
from claude_cli_caller import usage_from_record
from compose_diagnostic_hypotheses_v2 import compose
from render_diagnostic_composition_v2 import render
from run_diagnostic_command_motion_pilot import caller_for, load_prompt
from run_llm_episode_pilot import ANSWER_SCHEMA
from run_provenance_agent_pilot import extract_repository


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SCHEMA = "crane-raw-baseline-v5-development-screen/v1"
RUN_SCHEMA = "crane-raw-baseline-v5-development-case-result/v1"
FROZEN_STATUS = "FROZEN_BEFORE_ANY_RESPONSE_OR_JUDGMENT"
RUNNER_PATH = Path(__file__).resolve()
BASE_RUNNER_PATH = ROOT / "analysis/run_measurement_complete_v2_development.py"
GEOMETRIC_ADAPTER_PATH = ROOT / "analysis/build_geometric_composition_packet_v5.py"
RAW_BUILDER_PATH = ROOT / "analysis/build_raw_diagnostic_baseline_evidence.py"
CONTRACT_BUILDER_PATH = ROOT / "analysis/build_raw_baseline_v5_contract.py"
RAW_MANIFEST_PATH = (
    ROOT / "manifests/data/coverage-complete-v5-raw-baseline.robot-visible.json"
)
BASELINE_TOOL_PATHS = dict(base.BASELINE_TOOL_PATHS)
BASELINE_TOOL_PATHS["recompute_command_motion_v2"] = (
    ROOT / "analysis/recompute_command_motion_diagnostic_v2.py"
)
FORBIDDEN_BASELINE_KEYS = {
    "diagnostic_result",
    "reference_computation",
    "answer_plan",
    "final_answer",
    "final_text_verification",
    "land-evaluator-truth",
}


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        result = set(value)
        for item in value.values():
            result.update(_keys(item))
        return result
    if isinstance(value, list):
        result: set[str] = set()
        for item in value:
            result.update(_keys(item))
        return result
    return set()


def _case(contract: dict[str, Any], case_id: str) -> dict[str, Any]:
    matches = [item for item in contract.get("cases", []) if item.get("case_id") == case_id]
    if len(matches) != 1:
        raise ValueError(f"contract must contain exactly one case {case_id}")
    return matches[0]


def _build_packet(adapter: str, document: dict[str, Any], digest: str) -> dict[str, Any]:
    if adapter == "command_motion_v2":
        return build_command_packet(document, source_sha256=digest)
    if adapter == "geometric_v5":
        return build_geometric_packet(document, source_sha256=digest)
    raise ValueError(f"unsupported raw-baseline-v5 composition adapter: {adapter}")


def frozen_artifact_paths(contract: dict[str, Any]) -> dict[str, Path]:
    paths = {
        "registry": base.REGISTRY_PATH,
        "composer": base.COMPOSER_PATH,
        "command_adapter": base.COMMAND_ADAPTER_PATH,
        "geometric_adapter": GEOMETRIC_ADAPTER_PATH,
        "renderer": base.RENDERER_PATH,
        "reference_builder": base.REFERENCE_BUILDER_PATH,
        "command_reference_builder": base.COMMAND_REFERENCE_BUILDER_PATH,
        "packet_builder": base.PACKET_BUILDER_PATH,
        "base_runner": BASE_RUNNER_PATH,
        "runner": RUNNER_PATH,
        "raw_builder": RAW_BUILDER_PATH,
        "contract_builder": CONTRACT_BUILDER_PATH,
        "raw_manifest": RAW_MANIFEST_PATH,
        "baseline_prompt": ROOT / contract["baseline"]["prompt"],
        "reference_inventory": ROOT / contract["reference_inventory"],
    }
    paths.update(
        {f"baseline_tool:{name}": path for name, path in BASELINE_TOOL_PATHS.items()}
    )
    return paths


def verify_frozen_artifacts(contract: dict[str, Any]) -> None:
    declared = contract.get("frozen_artifact_sha256")
    paths = frozen_artifact_paths(contract)
    if not isinstance(declared, dict) or set(declared) != set(paths):
        raise ValueError("frozen artifact hash inventory is incomplete")
    mismatches = [
        name for name, path in paths.items() if declared[name] != base.sha256_path(path)
    ]
    if mismatches:
        raise ValueError("frozen artifact hash mismatch: " + ", ".join(sorted(mismatches)))


def _copy_baseline_tools(workspace: Path) -> dict[str, str]:
    destination = workspace / "_deterministic_tools"
    destination.mkdir()
    hashes: dict[str, str] = {}
    for name, source in BASELINE_TOOL_PATHS.items():
        target = destination / source.name
        shutil.copy2(source, target)
        hashes[name] = base.sha256_path(source)
    return hashes


def _reference(
    case: dict[str, Any], diagnostic: dict[str, Any], inventory: dict[str, Any]
) -> dict[str, Any]:
    reference_id = case["reference_case_id"]
    matches = [item for item in inventory.get("cases", []) if item.get("case_id") == reference_id]
    if len(matches) != 1:
        raise ValueError(f"reference inventory must contain exactly one case {reference_id}")
    reference_screen_case = copy.deepcopy(case)
    reference_screen_case["case_id"] = reference_id
    reference = build_reference(reference_screen_case, matches[0])
    if reference["episode_id"] != diagnostic["episode_id"]:
        raise ValueError("candidate diagnostic and independent reference episode mismatch")
    reference["question_id"] = f"raw-baseline-v5:{case['case_id']}"
    return reference


def run(args: argparse.Namespace, caller: Any = None) -> dict[str, Any]:
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    contract_raw = args.contract.read_bytes()
    contract = json.loads(contract_raw)
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise ValueError("development screen contract schema mismatch")
    if contract.get("status") != FROZEN_STATUS:
        raise ValueError("development screen is not committed/frozen for responses")
    unhashed = dict(contract)
    unhashed.pop("committed_contract_sha256", None)
    if contract.get("committed_contract_sha256") != base.sha256_json(unhashed):
        raise ValueError("development screen contract hash mismatch")
    verify_frozen_artifacts(contract)

    case = _case(contract, args.case_id)
    robot_root = (ROOT / "data/robot_visible").resolve(strict=True)
    diagnostic_path = (ROOT / case["diagnostic_path"]).resolve(strict=True)
    baseline_path = (ROOT / case["baseline_evidence_path"]).resolve(strict=True)
    if robot_root not in diagnostic_path.parents or robot_root not in baseline_path.parents:
        raise ValueError("candidate and baseline inputs must be governed robot-visible artifacts")

    diagnostic_raw = diagnostic_path.read_bytes()
    baseline_raw = baseline_path.read_bytes()
    diagnostic_digest = base.sha256_bytes(diagnostic_raw)
    baseline_digest = base.sha256_bytes(baseline_raw)
    if diagnostic_digest != case.get("diagnostic_sha256"):
        raise ValueError("candidate diagnostic hash mismatch")
    if baseline_digest != case.get("baseline_evidence_sha256"):
        raise ValueError("baseline evidence hash mismatch")
    diagnostic = json.loads(diagnostic_raw)
    baseline_evidence = json.loads(baseline_raw)
    if baseline_evidence.get("visibility") != "robot_visible":
        raise ValueError("baseline evidence is not robot-visible")
    leaked = FORBIDDEN_BASELINE_KEYS.intersection(_keys(baseline_evidence))
    if leaked:
        raise ValueError("baseline evidence leaks checked/evaluator fields: " + ", ".join(sorted(leaked)))

    inventory_path = (ROOT / contract["reference_inventory"]).resolve(strict=True)
    inventory = load_inventory(inventory_path)
    reference = _reference(case, diagnostic, inventory)

    packet = _build_packet(case["adapter"], diagnostic, diagnostic_digest)
    registry = json.loads(base.REGISTRY_PATH.read_text(encoding="utf-8"))
    certificate = compose(packet, registry)
    if certificate.get("status") != "composed" or not certificate.get("answer_plan", {}).get(
        "language_ready"
    ):
        raise ValueError("candidate certificate is not language-ready")
    proposed = render(certificate)
    if proposed != render(certificate):
        raise AssertionError("candidate rendering is not deterministic")

    model = contract["model"]
    baseline = contract["baseline"]
    prompt_path = ROOT / baseline["prompt"]
    prompt = load_prompt(
        str(prompt_path.relative_to(ROOT / "research/explanation_fidelity/prompts")),
        {"QUESTION": case["question"]},
    )
    caller = caller or caller_for(
        model["provider"], args.cache, model["model"], model["reasoning_effort"]
    )

    repositories = contract["repositories"]
    with tempfile.TemporaryDirectory(prefix="crane-raw-baseline-v5-r-") as temporary:
        workspace = Path(temporary) / "workspace"
        repository = workspace / "packages/crane_ml"
        core_repository = workspace / "packages/astro_dock/src/crane_explain"
        extract_repository(
            ROOT / repositories["crane_ml_path"], repositories["crane_ml_commit"], repository
        )
        extract_repository(
            ROOT / repositories["diagnostic_core_path"],
            repositories["diagnostic_core_commit"],
            core_repository,
        )
        visible = workspace / "_robot_visible"
        visible.mkdir(parents=True)
        shutil.copy2(baseline_path, visible / "evidence.json")
        tool_hashes = _copy_baseline_tools(workspace)
        record = caller.call(
            f"raw-baseline-v5-{case['case_id']}-R",
            prompt,
            ANSWER_SCHEMA,
            working_directory=workspace,
            workspace_identity={
                "screen_id": contract["screen_id"],
                "case_id": case["case_id"],
                "condition": "R",
                "contract_sha256": base.sha256_bytes(contract_raw),
                "baseline_evidence_sha256": baseline_digest,
                "baseline_tool_sha256": tool_hashes,
                "crane_ml_commit": repositories["crane_ml_commit"],
                "diagnostic_core_commit": repositories["diagnostic_core_commit"],
            },
        )

    supporting = diagnostic["diagnostic_result"]["supporting_evidence"]
    result = {
        "schema": RUN_SCHEMA,
        "status": "DEVELOPMENT_ONLY_RETAIN_REGARDLESS_OF_DIRECTION",
        "episode_id": diagnostic["episode_id"],
        "question_id": f"raw-baseline-v5:{case['case_id']}",
        "question_kind": case["question_kind"],
        "provider": model["provider"],
        "model": model["model"],
        "evaluator_truth_available_to_methods": False,
        "permitted_evidence_identifiers": sorted(supporting),
        "screen_id": contract["screen_id"],
        "case_id": case["case_id"],
        "cluster_id": case["cluster_id"],
        "family": case["family"],
        "independent_cluster": case["independent_cluster"],
        "paired_with": case.get("paired_with"),
        "question": case["question"],
        "candidate": contract["candidate"],
        "primary_comparison": "P versus R",
        "information_parity": {
            "same_underlying_robot_visible_observations": True,
            "same_relevant_source_and_configuration": True,
            "same_executable_diagnostic_tools": True,
            "baseline_receives_raw_observations": True,
            "precomputed_diagnostic_visible_to_R": False,
            "precomputed_reference_computation_visible_to_R": False,
            "episode_certificate_visible_to_R": False,
            "checked_answer_plan_visible_to_R": False,
            "candidate_final_answer_visible_to_R": False,
            "evaluator_truth_visible": False,
            "baseline_deterministic_tools": tool_hashes,
        },
        "inputs": {
            "contract_sha256": base.sha256_bytes(contract_raw),
            "diagnostic_sha256": diagnostic_digest,
            "baseline_evidence_sha256": baseline_digest,
            "packet_sha256": base.sha256_json(packet),
            "certificate_sha256": base.sha256_json(certificate),
            "registry_sha256": base.sha256_path(base.REGISTRY_PATH),
            "composer_sha256": base.sha256_path(base.COMPOSER_PATH),
            "prompt_sha256": base.sha256_path(prompt_path),
            "reference_inventory_sha256": base.sha256_path(inventory_path),
            "annotation_reference_sha256": base.sha256_json(reference),
        },
        "calls": [
            {
                "condition": "R",
                "cache_key": record["cache_key"],
                "latency_ms": record["latency_ms"],
                "cost_usd": record.get("cost_usd"),
                "usage": usage_from_record(record),
            }
        ],
        "outputs": [
            {
                "condition": "P",
                "text": proposed,
                "generation_method": "raw_baseline_v5_checked_composition_deterministic",
                "provider": "deterministic",
                "model": None,
                "model_calls": 0,
            },
            {
                "condition": "R",
                "text": record["parsed_final"]["answer"],
                "generation_method": "raw_evidence_tool_enabled_repository_agent",
                "provider": model["provider"],
                "model": model["model"],
                "model_calls": 1,
            },
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
