import hashlib
import json
from pathlib import Path

import pytest

from build_focused_annotation_reference_v2 import build_command, build_geometry
from focused_sequential_monitor_v2 import analyze


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "research/explanation_fidelity/experiment_configs/prospective/focused-supported-diagnostic-communication-v1.json"
FREEZE_PATH = ROOT / "research/explanation_fidelity/experiment_configs/prospective/focused-supported-diagnostic-communication-v1-resource-freeze.json"
LEDGER_PATH = ROOT / "manifests/study/diagnostic-sequential-error-ledger-v2.json"
REGISTRY_PATH = ROOT / "research/explanation_fidelity/experiment_configs/prospective/focused-supported-diagnostic-communication-v1-questions.json"
AMENDMENT_PATH = ROOT / "research/explanation_fidelity/experiment_configs/prospective/focused-supported-diagnostic-communication-v1-coordinator-amendment-1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def payload() -> dict:
    return {
        "schema": "crane-focused-supported-diagnostic-results/v1",
        "campaign_id": "focused-supported-diagnostic-communication-v1-confirmation",
        "protocol_id": "focused-supported-diagnostic-communication-v1",
        "protocol_sha256": hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest(),
        "resource_freeze_sha256": hashlib.sha256(FREEZE_PATH.read_bytes()).hexdigest(),
        "development_or_legacy_data_included": False,
        "sampling_rule_changed_after_outcomes": False,
        "judge": {
            "qualification_id": "luna-model-judge-v12-complete-endpoint-extension-v1",
            "two_isolated_passes": True,
        },
        "clusters": [],
    }


def row(index: int, family: str, *, eligible: bool = True) -> dict:
    return {
        "cluster_id": f"focused-{index:03d}",
        "configuration_id": f"configuration-{index:03d}",
        "sequence_index": index,
        "independent_scenario_configuration": True,
        "family": family,
        "primary_endpoint_eligible": eligible,
        "complete_supported_diagnostic_communication_p": int(eligible),
        "complete_supported_diagnostic_communication_r": 0,
        "material_error_p": 0,
        "material_error_r": 0,
        "mechanism_correct_p": int(eligible),
        "mechanism_correct_r": 0,
        "measurement_correct_p": int(eligible),
        "measurement_correct_r": 0,
        "causal_limit_preserved_p": 1,
        "causal_limit_preserved_r": 1,
        "essential_unit_total": 4,
        "essential_units_covered_p": 4 if eligible else 3,
        "essential_units_covered_r": 2,
    }


def bound_ledger(value: dict) -> dict:
    ledger = load(LEDGER_PATH)
    allocation = next(x for x in ledger["allocations"] if x["allocation_id"] == "candidate-v1-confirmation")
    allocation.update(status="CONSUMED", campaign_id=value["campaign_id"], consumed_at="2026-09-26T00:00:00Z")
    ledger["consumed_alpha"] = 0.02
    return ledger


def test_coordinator_amendment_freezes_exact_artifacts_before_semantic_confirmation():
    amendment = load(AMENDMENT_PATH)
    assert amendment["inspection_boundary"]["semantic_primary_N"] == 0
    assert amendment["inspection_boundary"]["P_confirmatory_responses_opened"] == 0
    assert amendment["inspection_boundary"]["R_confirmatory_responses_opened"] == 0
    for artifact in amendment["frozen_artifacts"].values():
        path = ROOT / artifact["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]


def test_primary_family_with_insufficient_independent_reference_is_retained_but_not_counted():
    value = payload()
    value["clusters"] = [row(1, "bounded_geometric_restriction", eligible=False)]
    result = analyze(value, load(PROTOCOL_PATH), bound_ledger(value), load(FREEZE_PATH))
    assert result["independent_configuration_count"] == 1
    assert result["scheduled_configuration_count"] == 1
    assert result["primary_eligible_count"] == 0
    assert result["retained_primary_family_configurations_ineligible_by_independent_reference"] == 1
    assert result["status"] == "CONTINUE"


def test_final_review_uses_all_64_scheduled_configurations_when_eligible_n_is_below_47():
    value = payload()
    families = (
        ["bounded_geometric_restriction"] * 5
        + ["persistent_command_motion_discrepancy"] * 21
        + ["measured_response_recovery"] * 21
        + ["missing_decisive_or_ambiguous_evidence"] * 10
        + ["nominal_false_premise_or_irrelevant_obstacle"] * 7
    )
    value["clusters"] = [
        row(i, family, eligible=family in {
            "bounded_geometric_restriction",
            "persistent_command_motion_discrepancy",
            "measured_response_recovery",
        })
        for i, family in enumerate(families, start=1)
    ]
    value["clusters"][1].update(primary_endpoint_eligible=False, complete_supported_diagnostic_communication_p=0, mechanism_correct_p=0, measurement_correct_p=0)
    value["clusters"][3].update(primary_endpoint_eligible=False, complete_supported_diagnostic_communication_p=0, mechanism_correct_p=0, measurement_correct_p=0)
    result = analyze(value, load(PROTOCOL_PATH), bound_ledger(value), load(FREEZE_PATH))
    assert result["scheduled_configuration_count"] == 64
    assert result["primary_eligible_count"] == 45
    assert result["status"] == "INCONCLUSIVE_FINAL"


def test_masked_command_reference_uses_exact_control_registry_units():
    export = load(ROOT / "data/robot_visible/dev/cm-land-conf-048-mask-no-odometry/command-motion-diagnostic-v3.json")
    independent = load(ROOT / "data/evaluator_only/dev/cm-land-conf-048-mask-no-odometry/command-motion-missing-odometry-reference-v1.json")
    result = build_command(
        export,
        independent,
        family="missing_decisive_or_ambiguous_evidence",
        question_id="focused-cm-land-conf-048",
    )
    registry = next(x for x in load(REGISTRY_PATH)["questions"] if x["family"] == "missing_decisive_or_ambiguous_evidence")
    assert result["primary_endpoint_eligible"] is False
    assert [x["unit_id"] for x in result["required_units"]] == registry["essential_units"]
    assert "475 command samples" in result["required_units"][0]["text"]
    assert "0 odometry samples" in result["required_units"][1]["text"]


@pytest.mark.parametrize(
    ("run_id", "family"),
    [
        ("cm-land-conf-046", "persistent_command_motion_discrepancy"),
        ("cm-land-conf-049", "measured_response_recovery"),
    ],
)
def test_supported_command_references_use_exact_primary_registry_units(run_id: str, family: str):
    export = load(ROOT / f"data/robot_visible/dev/{run_id}/command-motion-diagnostic-v3.json")
    independent = load(ROOT / f"data/evaluator_only/dev/{run_id}/command-motion-independent-reference-v1.json")
    result = build_command(export, independent, family=family, question_id=f"focused-{run_id}")
    registry = next(x for x in load(REGISTRY_PATH)["questions"] if x["family"] == family)
    assert result["primary_endpoint_eligible"] is True
    assert [x["unit_id"] for x in result["required_units"]] == registry["essential_units"]
    assert result["complete_endpoint_unit_ids"] == registry["essential_units"]


def test_supported_geometry_reference_uses_exact_primary_registry_units():
    run_id = "fsdc-land-geometry-001"
    export = load(ROOT / f"data/robot_visible/dev/{run_id}/geometric-route-diagnostic-v2.json")
    geometric = load(ROOT / f"data/evaluator_only/dev/{run_id}/geometric-independent-reference-v1.json")
    plan = load(ROOT / f"data/evaluator_only/dev/{run_id}/plan-geometry-independent-reference-v1.json")
    result = build_geometry(export, geometric, plan, question_id=f"focused-{run_id}")
    registry = next(x for x in load(REGISTRY_PATH)["questions"] if x["family"] == "bounded_geometric_restriction")
    assert result["primary_endpoint_eligible"] is True
    assert [x["unit_id"] for x in result["required_units"]] == registry["essential_units"]


@pytest.mark.parametrize("run_id", ["fsdc-land-geometry-002", "fsdc-land-geometry-004"])
def test_outcome_insufficient_geometry_builds_control_reference(run_id: str):
    export = load(ROOT / f"data/robot_visible/dev/{run_id}/geometric-route-diagnostic-v2.json")
    geometric = load(ROOT / f"data/evaluator_only/dev/{run_id}/geometric-independent-reference-v1.json")
    plan = load(ROOT / f"data/evaluator_only/dev/{run_id}/plan-geometry-independent-reference-v1.json")
    result = build_geometry(export, geometric, plan, question_id=f"focused-{run_id}")
    registry = next(x for x in load(REGISTRY_PATH)["questions"] if x["family"] == "missing_decisive_or_ambiguous_evidence")
    assert result["primary_endpoint_eligible"] is False
    assert result["mechanism_unit_id"] is None
    assert [x["unit_id"] for x in result["required_units"]] == registry["essential_units"]
    assert "not established" in result["required_units"][2]["text"]
