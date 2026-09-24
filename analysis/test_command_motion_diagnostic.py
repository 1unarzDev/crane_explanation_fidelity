import json
from pathlib import Path

import pytest

from export_command_motion_diagnostic import (
    _resolve_action_boundary,
    _source_qualified_wait_policy,
    export,
)
from reference_command_motion import calculate
from summarize_command_motion_qa import INDEPENDENT_DEVELOPMENT_STATUS, summarize


ROOT = Path(__file__).resolve().parents[1]
CAPTURE = (
    ROOT
    / "data"
    / "robot_visible"
    / "dev"
    / "diagnostic-motion-instrumentation-held-001"
    / "capture"
)
EVENTS = CAPTURE / "events.jsonl"
CAPTURE_MANIFEST = CAPTURE / "manifest.json"
RUNTIME_MANIFEST = CAPTURE / "runtime_manifest.json"
BT_XML = CAPTURE / "behavior_tree.xml"
NAV2_CONFIG = ROOT / "packages" / "crane_ml" / "Tools" / "Performance" / "nav2_land_fixture.yaml"
NOMINAL_EXPORT = (
    ROOT
    / "data"
    / "robot_visible"
    / "dev"
    / "diagnostic-pilot-v1"
    / "land-command-motion-nominal-001"
    / "evidence-and-diagnostic.json"
)
NOMINAL_REFERENCE = (
    ROOT
    / "data"
    / "evaluator_only"
    / "dev"
    / "diagnostic-reference-v1"
    / "land-command-motion-nominal-001"
    / "reference.json"
)
COMPENSATED_CAPTURE = (
    ROOT
    / "data"
    / "robot_visible"
    / "dev"
    / "diagnostic-motion-development-cm-002"
    / "capture"
)
NONTERMINAL_CAPTURE = (
    ROOT
    / "data"
    / "robot_visible"
    / "dev"
    / "diagnostic-land-composition-dev-009"
    / "capture"
)


def _export() -> dict:
    return export(
        EVENTS,
        CAPTURE_MANIFEST,
        RUNTIME_MANIFEST,
        BT_XML,
        NAV2_CONFIG,
        episode_id="diagnostic-motion-dev-cm-001",
    )


def test_retained_stream_supports_bounded_command_motion_diagnosis():
    payload = _export()

    assert payload["diagnostic_result"]["disposition"] == "supported"
    assert payload["final_text_verification"]["accepted"]
    assert payload["method_input"]["execution_sequence"] == {
        "follow_path_failure_count": 2,
        "follow_path_attempt_count": 3,
        "source_qualified_wait_recovery_count": 2,
        "recovery_node_classifier": {
            "classifier_basis": "retained_bt_recovery_child_exact_node_name",
            "classifier_rule": "Wait:IDLE->RUNNING",
            "node_name": "Wait",
            "number_of_retries": 2,
            "policy_sha256": "14939b78c72149b9c71b3806f2d3af63fc5de48c8bd9d07f0d13b55563f48520",
            "tree_path": "RecoveryNode/recovery_child/Sequence/Wait",
        },
    }
    serialized = json.dumps(payload).lower()
    assert "instrumentation-held" not in serialized
    assert "persistent hold" not in serialized
    assert "mobility hold" not in serialized
    assert "motor failure" not in payload["final_answer"].lower()


def test_terminal_result_export_does_not_add_nonterminal_boundary_fields():
    payload = _export()

    assert "terminal_result_observed" not in payload["method_input"]
    assert "observation_cutoff" not in payload["method_input"]
    assert "NavigateToPose goal/result status" in payload["evidence_boundary"]["included"]


def test_nested_nav2_policy_source_qualifies_single_wait_recovery_leaf():
    policy = _source_qualified_wait_policy(
        ROOT
        / "packages"
        / "crane_ml"
        / "Tools"
        / "Performance"
        / "nav2_roboboat_distance_replanning.xml"
    )

    assert policy["node_name"] == "Wait"
    assert policy["number_of_retries"] == 6
    assert policy["tree_path"].startswith("RecoveryNode/recovery_child/")
    assert policy["tree_path"].endswith("/Wait")


def test_low_speed_config_makes_proving_ground_stream_assessable(tmp_path: Path):
    capture = (
        ROOT
        / "data"
        / "robot_visible"
        / "dev"
        / "diagnostic-land-binding-dev-007"
        / "capture"
    )
    payload = export(
        capture / "events.jsonl",
        capture / "manifest.json",
        capture / "runtime_manifest.json",
        capture / "behavior_tree.xml",
        ROOT
        / "packages"
        / "crane_ml"
        / "Tools"
        / "Performance"
        / "nav2_land_proving_ground_fixture.yaml",
        episode_id="diagnostic-land-composition-development-007",
        diagnostic_config_path=(
            ROOT / "configs" / "diagnostic_command_motion_low_speed_v1.json"
        ),
    )

    assert payload["source"]["diagnostic_config_sha256"]
    assert payload["source"]["diagnostic_config_id"] == "diagnostic-command-motion-low-speed-v1"
    assert payload["method_input"]["windowing"]["minimum_commanded_speed_mps"] == 0.1
    assert payload["diagnostic_result"]["disposition"] != "insufficient"
    assert payload["final_text_verification"]["accepted"]


def test_nonterminal_stream_requires_explicit_observation_cutoff_opt_in():
    with pytest.raises(ValueError, match="exactly one accepted goal and one action result"):
        export(
            NONTERMINAL_CAPTURE / "events.jsonl",
            NONTERMINAL_CAPTURE / "manifest.json",
            NONTERMINAL_CAPTURE / "runtime_manifest.json",
            NONTERMINAL_CAPTURE / "behavior_tree.xml",
            ROOT
            / "packages"
            / "crane_ml"
            / "Tools"
            / "Performance"
            / "nav2_land_proving_ground_fixture.yaml",
            episode_id="diagnostic-land-composition-observation-009",
            diagnostic_config_path=(
                ROOT / "configs" / "diagnostic_command_motion_low_speed_v1.json"
            ),
        )


def test_nonterminal_stream_uses_declared_cutoff_without_terminal_claim():
    payload = export(
        NONTERMINAL_CAPTURE / "events.jsonl",
        NONTERMINAL_CAPTURE / "manifest.json",
        NONTERMINAL_CAPTURE / "runtime_manifest.json",
        NONTERMINAL_CAPTURE / "behavior_tree.xml",
        ROOT
        / "packages"
        / "crane_ml"
        / "Tools"
        / "Performance"
        / "nav2_land_proving_ground_fixture.yaml",
        episode_id="diagnostic-land-composition-observation-009",
        diagnostic_config_path=(
            ROOT / "configs" / "diagnostic_command_motion_low_speed_v1.json"
        ),
        allow_active_at_declared_cutoff=True,
    )

    method = payload["method_input"]
    assert method["terminal_result_observed"] is False
    assert method["action_result_record_id"] is None
    assert method["action_error_code"] is None
    assert method["action_status"] == "remained active at the observation cutoff"
    assert method["observation_cutoff"]["declared_action_duration_s"] == 100.0
    assert all(
        sample["offset_s"] <= method["analysis_duration_s"]
        for key in ("command_samples", "odometry_samples")
        for sample in method[key]
    )
    assert payload["diagnostic_result"]["disposition"] == "supported"
    assert "aborted" not in payload["final_answer"].lower()
    assert "failed" not in payload["final_answer"].lower()
    assert "remained active at the observation cutoff" in payload["final_answer"]
    reference = calculate(payload)
    assert reference["result"]["disposition"] == "supported"


def test_observation_cutoff_rejects_capture_that_stopped_too_early():
    records = [(9, {"type": "capture_stopped", "wall_time_ns": 100_000_000_999})]
    runtime = {"launch_contract": {"action_duration_s": 100.0}}

    with pytest.raises(ValueError, match="capture stopped before"):
        _resolve_action_boundary(
            records,
            runtime,
            [],
            goal_ns=1_000_000_000,
            goal_id="goal-1",
            allow_active_at_declared_cutoff=True,
        )


def test_diagnostic_config_rejects_missing_parameter(tmp_path: Path):
    invalid = tmp_path / "invalid.json"
    invalid.write_text(
        json.dumps(
            {
                "schema": "crane-command-motion-diagnostic-config/v1",
                "parameters": {"window_seconds": 1.0},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="parameters differ"):
        export(
            EVENTS,
            CAPTURE_MANIFEST,
            RUNTIME_MANIFEST,
            BT_XML,
            NAV2_CONFIG,
            episode_id="diagnostic-motion-dev-cm-001",
            diagnostic_config_path=invalid,
        )


def test_independent_reference_recomputes_supported_interval():
    payload = _export()
    reference = calculate(payload)
    measurements = {
        item["id"]: item["value"] for item in payload["diagnostic_result"]["measurements"]
    }

    assert reference["implementation_independence"]["imports_proposed_diagnostic_core"] is False
    assert reference["result"]["disposition"] == "supported"
    assert reference["result"]["interval_s"] == [7.0, 17.0]
    assert reference["result"]["healthy_measured_planar_speed_mps"] == pytest.approx(
        measurements["calibrated_healthy_planar_speed"]
    )
    assert reference["result"]["discrepancy_commanded_planar_speed_mps"] == pytest.approx(
        measurements["discrepancy_commanded_planar_speed"]
    )
    assert reference["result"]["discrepancy_measured_planar_speed_mps"] == pytest.approx(
        measurements["discrepancy_measured_planar_speed"]
    )


def test_independent_reference_recomputes_post_discrepancy_response_recovery(tmp_path: Path):
    payload = export(
        COMPENSATED_CAPTURE / "events.jsonl",
        COMPENSATED_CAPTURE / "manifest.json",
        COMPENSATED_CAPTURE / "runtime_manifest.json",
        COMPENSATED_CAPTURE / "behavior_tree.xml",
        NAV2_CONFIG,
        episode_id="diagnostic-motion-dev-cm-compensated-001",
    )
    reference = calculate(payload)
    measurements = {
        item["id"]: item["value"] for item in payload["diagnostic_result"]["measurements"]
    }

    assert payload["method_input"]["action_status"] == "succeeded"
    assert payload["diagnostic_result"]["disposition"] == "supported"
    assert reference["result"]["disposition"] == "supported"
    assert reference["result"]["interval_s"] == [8.0, 18.0]
    assert reference["result"]["response_recovery_interval_s"] == [20.0, 21.0]
    assert reference["result"]["recovered_measured_planar_speed_mps"] == pytest.approx(
        measurements["recovered_measured_planar_speed"]
    )
    assert reference["result"]["recovered_response_ratio"] == pytest.approx(
        measurements["recovered_response_ratio"]
    )
    assert "response recovered" in reference["allowed_conclusion"]
    serialized = json.dumps(payload).lower()
    assert "mobility hold" not in serialized
    assert "mobility release" not in serialized

    export_path = tmp_path / "export.json"
    reference_path = tmp_path / "reference.json"
    export_path.write_text(json.dumps(payload), encoding="utf-8")
    reference_path.write_text(json.dumps(reference), encoding="utf-8")
    qa = summarize(export_path, reference_path, INDEPENDENT_DEVELOPMENT_STATUS)
    assert qa["status"] == INDEPENDENT_DEVELOPMENT_STATUS
    assert qa["checks"]["all_reference_values_match"]
    assert qa["response_recovery_interval_s"] == [20.0, 21.0]
    assert "independently configured development scenario" in qa["limitations"][0]


def test_runtime_source_hash_mismatch_is_rejected(tmp_path: Path):
    changed = tmp_path / "changed-nav2.yaml"
    changed.write_text(NAV2_CONFIG.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Nav2 configuration hash"):
        export(
            EVENTS,
            CAPTURE_MANIFEST,
            RUNTIME_MANIFEST,
            BT_XML,
            changed,
            episode_id="diagnostic-motion-dev-cm-001",
        )


def test_evaluator_only_input_path_is_rejected():
    evaluator_path = (
        ROOT
        / "data"
        / "evaluator_only"
        / "dev"
        / "diagnostic-motion-instrumentation-held-001"
        / "fixture-summary.json"
    )
    with pytest.raises(ValueError, match="robot_visible"):
        export(
            evaluator_path,
            CAPTURE_MANIFEST,
            RUNTIME_MANIFEST,
            BT_XML,
            NAV2_CONFIG,
            episode_id="diagnostic-motion-dev-cm-001",
        )


def test_retained_nominal_stream_is_not_triggered_and_passes_qa():
    payload = json.loads(NOMINAL_EXPORT.read_text(encoding="utf-8"))
    reference = json.loads(NOMINAL_REFERENCE.read_text(encoding="utf-8"))
    qa = summarize(NOMINAL_EXPORT, NOMINAL_REFERENCE)

    assert payload["diagnostic_result"]["disposition"] == "not_triggered"
    assert reference["result"]["disposition"] == "not_triggered"
    assert qa["status"] == "VALID_DEVELOPMENT_INSTRUMENTATION_QUALIFICATION_NOT_INDEPENDENT_SCENARIO"
    assert qa["supported_interval_s"] is None
    assert "negative result" in qa["limitations"][2]
