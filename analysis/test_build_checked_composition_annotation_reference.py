import copy
import hashlib
import json
from pathlib import Path

import pytest

from build_checked_composition_annotation_reference import (
    REFERENCE_SCHEMA,
    build_reference,
    load_inventory,
    validate_inventory,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "research/explanation_fidelity/experiment_configs/development/diagnostic-checked-composition-multifamily-screen-v1.json"
INVENTORY_PATH = ROOT / "research/explanation_fidelity/references/development/diagnostic-checked-composition-multifamily-references-v1.json"


def documents():
    return json.loads(CONTRACT_PATH.read_text()), load_inventory(INVENTORY_PATH)


def indexed(values):
    return {item["case_id"]: item for item in values}


def test_all_screen_cases_have_hash_checked_atomic_references():
    contract, inventory = documents()
    references = validate_inventory(contract, inventory)

    assert len(references) == 7
    assert {item["question_id"].split(":", 1)[1] for item in references} == {
        item["case_id"] for item in contract["cases"]
    }
    for reference in references:
        assert reference["schema"] == REFERENCE_SCHEMA
        assert reference["completeness_audit"]["accepted"] is True
        assert reference["completeness_audit"]["atomic_required_units"] is True
        unit_ids = [item["unit_id"] for item in reference["required_units"]]
        assert len(unit_ids) == len(set(unit_ids))
        assert "answer_plan" not in json.dumps(reference)
        assert "final_text_verification" not in json.dumps(reference)


def test_only_supported_execution_mechanisms_are_primary_endpoint_eligible():
    _, inventory = documents()
    cases = indexed(inventory["cases"])

    eligible = {case_id for case_id, item in cases.items() if item["primary_endpoint_eligible"]}
    assert eligible == {"ccdev-persistent-001", "ccdev-compensation-002"}
    for case_id, item in cases.items():
        units = {unit["unit_id"] for unit in item["required_units"]}
        if case_id in eligible:
            assert item["diagnosable"] is True
            assert item["mechanism_unit_id"] in units
        else:
            assert item["primary_endpoint_eligible"] is False
            assert item["mechanism_unit_id"] is None


def test_every_required_unit_has_one_unique_declared_atomic_predicate():
    _, inventory = documents()
    for case in inventory["cases"]:
        predicates = [item["atomic_predicate"] for item in case["required_units"]]
        assert all(isinstance(value, str) and value for value in predicates)
        assert len(predicates) == len(set(predicates))


def test_reference_source_hash_mutation_fails_closed():
    contract, inventory = documents()
    screen_case = indexed(contract["cases"])["ccdev-persistent-001"]
    reference_case = copy.deepcopy(indexed(inventory["cases"])["ccdev-persistent-001"])
    reference_case["reference_sources"][0]["sha256"] = "0" * 64

    with pytest.raises(ValueError, match="independent reference hash mismatch"):
        build_reference(screen_case, reference_case)


def test_reference_sources_are_bound_to_exact_retained_bytes():
    _, inventory = documents()
    for case in inventory["cases"]:
        for source in case["reference_sources"]:
            assert hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"]


def test_reference_measurements_cover_key_persistent_compensation_and_geometry_facts():
    contract, inventory = documents()
    references = {
        item["question_id"].split(":", 1)[1]: item
        for item in validate_inventory(contract, inventory)
    }

    persistent = json.dumps(references["ccdev-persistent-001"])
    assert "0.260 m/s" in persistent and "0.000 m/s" in persistent
    assert "10.0 to 20.0 s" in persistent

    compensation = json.dumps(references["ccdev-compensation-002"])
    assert "0.2597 m/s during 24.0 to 25.0 s" in compensation

    route_change = json.dumps(references["ccdev-route-change-007"])
    assert "-1.407 m" in route_change and "1.231 m" in route_change
    assert "does not establish the physical trigger" in route_change

    nonterminal = json.dumps(references["ccdev-nonterminal-insufficient-009"])
    assert "remained active" in nonterminal
    assert "does not cover the complete requested route" in nonterminal
