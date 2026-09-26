import copy
import json
from pathlib import Path

from compose_diagnostic_hypotheses import compose


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads(
    (ROOT / "configs/diagnostic_composition_registry_v1.json").read_text(encoding="utf-8")
)


def packet(*observations):
    return {
        "schema": "crane-diagnostic-predicate-packet/v1",
        "packet_id": "development-case",
        "observations": [
            {"predicate": name, "value": value, "evidence_ids": [evidence_id]}
            for name, value, evidence_id in observations
        ],
    }


def mechanisms(result):
    return {item["mechanism_id"]: item for item in result["mechanisms"]}


def test_geometry_and_execution_with_same_abort_are_discriminated_by_measurements():
    geometry = compose(
        packet(
            ("action_aborted", True, "action"),
            ("geometry_sufficient", True, "coverage"),
            ("geometry_supported", True, "footprint"),
            ("command_motion_supported", False, "motion"),
        ),
        REGISTRY,
    )
    execution = compose(
        packet(
            ("action_aborted", True, "action"),
            ("geometry_sufficient", True, "coverage"),
            ("geometry_supported", False, "connectivity"),
            ("command_motion_supported", True, "response"),
        ),
        REGISTRY,
    )

    assert mechanisms(geometry)["geometric_route_restriction"]["status"] == "entailed"
    assert mechanisms(geometry)["command_to_motion_discrepancy"]["status"] == "excluded"
    assert mechanisms(execution)["geometric_route_restriction"]["status"] == "excluded"
    assert mechanisms(execution)["command_to_motion_discrepancy"]["status"] == "entailed"


def test_visual_obstacle_does_not_become_consumed_or_causal():
    result = compose(
        packet(
            ("obstacle_observed", True, "camera-frame"),
            ("route_change_observed", True, "plans"),
            ("nav2_consumption_proven", False, "runtime-audit"),
            ("decision_dependency_proven", False, "dependency-audit"),
        ),
        REGISTRY,
    )

    assert mechanisms(result)["recorded_route_change"]["status"] == "entailed"
    assert mechanisms(result)["observation_linked_navigation_response"]["status"] == "excluded"


def test_logged_replanning_without_physical_restriction_only_entails_route_change():
    result = compose(
        packet(
            ("route_change_observed", True, "plan-log"),
            ("geometry_sufficient", False, "coverage-audit"),
        ),
        REGISTRY,
    )

    assert mechanisms(result)["recorded_route_change"]["status"] == "entailed"
    assert mechanisms(result)["geometric_route_restriction"]["status"] == "excluded"


def test_masking_decisive_motion_broadens_entailed_to_unresolved():
    complete = packet(("command_motion_supported", True, "diagnostic"))
    masked = copy.deepcopy(complete)
    masked["observations"] = []

    complete_result = compose(complete, REGISTRY)
    masked_result = compose(masked, REGISTRY)

    assert mechanisms(complete_result)["command_to_motion_discrepancy"]["status"] == "entailed"
    unresolved = mechanisms(masked_result)["command_to_motion_discrepancy"]
    assert unresolved["status"] == "unresolved"
    assert unresolved["missing_discriminators"] == ["command_motion_supported"]
    assert unresolved["witnesses"]["supporting_completion"] != unresolved["witnesses"]["excluding_completion"]


def test_successful_compensation_does_not_get_equated_with_task_outcome():
    result = compose(
        packet(
            ("command_motion_supported", True, "discrepancy"),
            ("response_recovered", True, "recovery-window"),
            ("action_aborted", True, "action-result"),
        ),
        REGISTRY,
    )

    assert mechanisms(result)["measured_response_recovery"]["status"] == "entailed"
    assert result["answer_plan"]["primary_mechanism_id"] == "measured_response_recovery"
    assert "action-result" not in result["answer_plan"]["decisive_evidence_ids"]


def test_nominal_false_premise_is_an_entailed_first_class_state():
    result = compose(
        packet(
            ("command_motion_not_triggered", True, "negative-diagnostic"),
            ("command_motion_supported", False, "negative-diagnostic"),
            ("action_succeeded", True, "action-result"),
        ),
        REGISTRY,
    )

    assert mechanisms(result)["nominal_command_motion"]["status"] == "entailed"
    assert mechanisms(result)["command_to_motion_discrepancy"]["status"] == "excluded"


def test_conflicting_observations_fail_closed():
    result = compose(
        packet(
            ("command_motion_supported", True, "a"),
            ("command_motion_supported", False, "b"),
        ),
        REGISTRY,
    )

    assert result["status"] == "evidence_problem"
    assert result["admissible_world_count"] == 0
    assert result["answer_plan"] is None


def test_constraint_conflict_fails_closed():
    result = compose(
        packet(
            ("action_succeeded", True, "success"),
            ("action_aborted", True, "abort"),
        ),
        REGISTRY,
    )

    assert result["status"] == "evidence_problem"


def test_out_of_model_packet_retains_unresolved_alternatives_without_inventing_one():
    result = compose(packet(("action_aborted", True, "action")), REGISTRY)

    assert result["status"] == "composed"
    assert result["answer_plan"]["primary_mechanism_id"] is None
    assert "command_to_motion_discrepancy" in result["answer_plan"]["unresolved_alternatives"]
    assert "geometric_route_restriction" in result["answer_plan"]["unresolved_alternatives"]
