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
    assert result["out_of_model_possible"] is True
    assert len(result["registry_sha256"]) == 64
    assert "unmodeled mechanisms remain possible" in result["answer_plan"]["scope_limit"]


def test_registry_must_preserve_out_of_model_scope():
    unsafe = copy.deepcopy(REGISTRY)
    unsafe["out_of_model_possible"] = False
    try:
        compose(packet(("action_aborted", True, "action")), unsafe)
    except ValueError as error:
        assert "out-of-model" in str(error)
    else:
        raise AssertionError("registry without an out-of-model marker was accepted")


def test_stale_representation_is_distinct_from_obstacle_causation():
    result = compose(
        packet(
            ("current_observation_clear", True, "scan-current"),
            ("planning_representation_obstacle", True, "grid-old"),
            ("representation_timing_inconsistent", True, "timestamps"),
            ("decision_dependency_proven", False, "dependency-audit"),
        ),
        REGISTRY,
    )
    assert mechanisms(result)["stale_or_inconsistent_planning_representation"]["status"] == "entailed"
    assert mechanisms(result)["observation_linked_navigation_response"]["status"] == "excluded"


def test_answer_plan_compiles_declared_units_and_renderer_preserves_limits():
    value = packet(("command_motion_supported", True, "diagnostic"))
    value["answer_units"] = [
        {
            "unit_id": "healthy-comparator",
            "role": "evidence",
            "text": "Healthy measured-speed median was 0.31 m/s.",
            "evidence_ids": ["healthy"],
        },
        {
            "unit_id": "discrepancy-comparison",
            "role": "diagnosis",
            "text": "The interval supports a command-to-motion discrepancy.",
            "evidence_ids": ["diagnostic"],
        },
        {
            "unit_id": "cause-limit",
            "role": "limit",
            "text": "The unique physical cause is unresolved.",
            "evidence_ids": ["missing-feedback"],
        },
    ]
    result = compose(value, REGISTRY)
    assert result["answer_plan"]["language_ready"] is True
    assert result["answer_plan"]["missing_required_unit_ids"] == []
    assert [item["unit_id"] for item in result["answer_plan"]["units"]] == [
        "healthy-comparator",
        "discrepancy-comparison",
        "cause-limit",
    ]


def test_answer_plan_is_not_language_ready_when_registered_unit_is_missing():
    value = packet(("command_motion_supported", True, "diagnostic"))
    value["answer_units"] = [
        {
            "unit_id": "healthy-comparator",
            "role": "evidence",
            "text": "Healthy response was retained.",
            "evidence_ids": ["healthy"],
        }
    ]
    result = compose(value, REGISTRY)
    assert result["status"] == "composed"
    assert result["answer_plan"]["language_ready"] is False
    assert result["answer_plan"]["missing_required_unit_ids"] == [
        "cause-limit",
        "discrepancy-comparison",
    ]


def test_mechanism_only_certificate_cannot_silently_claim_language_readiness():
    result = compose(packet(("command_motion_supported", True, "diagnostic")), REGISTRY)

    assert result["answer_plan"]["primary_mechanism_id"] == "command_to_motion_discrepancy"
    assert result["answer_plan"]["language_ready"] is False
    assert result["answer_plan"]["missing_required_unit_ids"] == [
        "cause-limit",
        "discrepancy-comparison",
        "healthy-comparator",
    ]


def test_packet_applicability_scope_excludes_unrelated_missing_discriminators():
    value = packet(("command_motion_supported", True, "diagnostic"))
    value["applicable_mechanism_ids"] = ["command_to_motion_discrepancy"]
    result = compose(value, REGISTRY)

    assert result["applicable_mechanism_ids"] == ["command_to_motion_discrepancy"]
    assert result["answer_plan"]["unresolved_alternatives"] == []
    assert result["answer_plan"]["missing_discriminators"] == []


def test_packet_rejects_unknown_applicable_mechanism():
    value = packet(("command_motion_supported", True, "diagnostic"))
    value["applicable_mechanism_ids"] = ["invented-mechanism"]
    try:
        compose(value, REGISTRY)
    except ValueError as error:
        assert "applicable mechanism IDs" in str(error)
    else:
        raise AssertionError("unknown applicable mechanism was accepted")
