import copy
import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_atomic_claim_annotation_packets import build  # noqa: E402
from evidence_calibration_io import canonical_sha256  # noqa: E402
import adjudicate_evidence_calibration_annotations as module  # noqa: E402

SPEC = importlib.util.spec_from_file_location("packet_fixtures", ROOT / "tests/test_atomic_claim_annotation_packets.py")
FIXTURES = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FIXTURES)


def packet_and_return(slot: str, annotator: str):
    packet, _ = build(*FIXTURES.inputs(), "development-blinding-secret-v1")
    form = next(item for item in packet["forms"] if item["annotator_slot"] == slot)
    returned = {
        "schema": module.RETURN_SCHEMA,
        "packet_set_sha256": canonical_sha256(packet),
        "form_id": form["form_id"],
        "packet_id": form["packet_id"],
        "annotator_slot": slot,
        "annotator_id": annotator,
        "atomic_labels": [
            {"item_id": item["item_id"], "label": "SUPPORTED_BY_VISIBLE_EVIDENCE", "annotation_notes": None}
            for item in form["atomic_statements"]
        ],
        "required_unit_coverage": [
            {"unit_prompt": item["unit_prompt"], "communicated": True, "response_span": "exact span"}
            for item in form["required_unit_coverage"]
        ],
        "highest_asserted_abstraction_level": "execution_discrepancy",
        "limitation_preservation": [
            {"limitation_prompt": item["limitation_prompt"], "preserved": False, "response_span": None}
            for item in form["limitation_preservation"]
        ],
        "false_premise_handling": "NOT_APPLICABLE",
        "annotator_attestation": "INDEPENDENT_BLINDED_COMPLETE",
    }
    return packet, returned


def test_two_distinct_returns_produce_blinded_agreement_report() -> None:
    packet, first = packet_and_return("A", "human-a")
    _, second = packet_and_return("B", "human-b")
    report = module.compare(packet, first, second)
    assert report["disagreement_count"] == 0
    assert report["agreement_count"] == report["decision_count"]
    assert report["method_identity_visible"] is False
    assert report["condition_key_joined"] is False
    assert report["scientific_sample_count_increment"] == 0


def test_same_person_cannot_fill_both_slots() -> None:
    packet, first = packet_and_return("A", "same-human")
    _, second = packet_and_return("B", "same-human")
    with pytest.raises(ValueError, match="same person"):
        module.compare(packet, first, second)


def test_missing_exact_span_fails_closed() -> None:
    packet, returned = packet_and_return("A", "human-a")
    returned["required_unit_coverage"][0]["response_span"] = None
    with pytest.raises(ValueError, match="exact response span"):
        module.validate_return(packet, returned)


def test_distinct_third_person_resolves_only_disagreements() -> None:
    packet, first = packet_and_return("A", "human-a")
    _, second = packet_and_return("B", "human-b")
    second["atomic_labels"][0]["label"] = "INSUFFICIENT_VISIBLE_EVIDENCE"
    report = module.compare(packet, first, second)
    assert report["disagreement_count"] == 1
    handoff = module.build_handoff(report)
    assert handoff["disagreements"] == report["disagreements"]
    assert "annotator_ids" not in handoff
    assert "agreed_decisions" not in handoff
    assert handoff["method_identity_visible"] is False
    disagreement = report["disagreements"][0]
    adjudication = {
        "schema": module.ADJUDICATION_SCHEMA,
        "agreement_report_sha256": canonical_sha256(report),
        "adjudicator_id": "human-c",
        "decisions": [{"disagreement_id": disagreement["disagreement_id"],
                       "selected_value": disagreement["annotator_a_value"],
                       "rationale": "Visible evidence directly supports the recorded statement."}],
        "attestation": "DISAGREEMENT_ONLY_BLINDED_COMPLETE",
    }
    final = module.finalize(report, adjudication)
    assert final["ready_for_separate_key_join"] is True
    assert final["condition_key_joined"] is False
    assert final["original_disagreements_preserved"] == report["disagreements"]


def test_annotator_cannot_adjudicate_own_disagreement() -> None:
    packet, first = packet_and_return("A", "human-a")
    _, second = packet_and_return("B", "human-b")
    second["atomic_labels"][0]["label"] = "INSUFFICIENT_VISIBLE_EVIDENCE"
    report = module.compare(packet, first, second)
    adjudication = {
        "schema": module.ADJUDICATION_SCHEMA,
        "agreement_report_sha256": canonical_sha256(report),
        "adjudicator_id": "human-a", "decisions": [],
        "attestation": "DISAGREEMENT_ONLY_BLINDED_COMPLETE",
    }
    with pytest.raises(ValueError, match="distinct"):
        module.finalize(report, adjudication)
