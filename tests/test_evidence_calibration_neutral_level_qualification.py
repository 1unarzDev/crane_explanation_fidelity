import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

from build_evidence_calibration_neutral_level_suite import build
from evidence_calibration_io import canonical_sha256
from evidence_calibration_neutral_level_qualification import aggregate, packet_for, score_return


def synthetic_return(case, slot="A", level="task_outcome"):
    packet = packet_for(case, slot, "offline-synthetic-test")
    form = packet["forms"][0]
    return {
        "schema": "crane-blinded-atomic-annotation-return/v1",
        "packet_set_sha256": canonical_sha256(packet), "form_id": form["form_id"],
        "packet_id": form["packet_id"], "annotator_slot": slot, "annotator_id": "offline-test",
        "annotator_attestation": "INDEPENDENT_BLINDED_COMPLETE",
        "atomic_labels": [{**item, "annotation_notes": "offline structural test"}
                          for item in case["expected"]["atomic_labels"]],
        "required_unit_coverage": copy.deepcopy(case["expected"]["required_unit_coverage"]),
        "limitation_preservation": copy.deepcopy(case["expected"]["limitation_preservation"]),
        "false_premise_handling": case["expected"]["false_premise_handling"],
        "highest_asserted_abstraction_level": level,
    }


def score(case, returned):
    return score_return(case, returned, slot="A", suite_hash="offline-synthetic-test")


def test_raw_rank_cannot_change_support_qualification():
    case = build()["cases"][4]
    low = synthetic_return(case, level="task_outcome")
    high = synthetic_return(case, level="specific_physical_cause")
    assert score(case, low) == score(case, high)
    assert score(case, high)["endpoint_scoring_authorized"] is False
    anchored = copy.deepcopy(case)
    anchored["form"]["atomic_statements"][0]["asserted_abstraction_level"] = "specific_physical_cause"
    with pytest.raises(ValueError, match="anchor"):
        packet_for(anchored, "A", "offline-synthetic-test")


def test_unsupported_measured_recovery_preserves_useful_event_coverage():
    case = next(case for case in build()["cases"] if case["case_id"] == "nl-ho-06")
    returned = synthetic_return(case)
    row = score(case, returned)
    assert row["atomic"][0]["expected"] == "INSUFFICIENT_VISIBLE_EVIDENCE"
    assert row["required_units"][0]["correct"] is True
    returned["atomic_labels"][0]["label"] = "SUPPORTED_BY_VISIBLE_EVIDENCE"
    metrics = aggregate([score(case, returned)])
    assert metrics["unsupported_false_acceptance_rate"] == 1
    assert metrics["required_unit_accuracy"] == 1
    returned["required_unit_coverage"][0]["response_span"] = "a fabricated response span"
    with pytest.raises(ValueError, match="exact response text"):
        score(case, returned)


def test_all_five_labels_are_exercised_without_rank_gold_or_study_text():
    suite = build()
    assert suite["pilot_annotation_authorized"] is False
    assert len(suite["cases"]) == 20
    assert sum(case["split"] == "heldout" for case in suite["cases"]) == 16
    old = json.loads((Path(__file__).resolve().parents[1] /
                      "research/explanation_fidelity/qualification/evidence-calibration-agent-exact-task-v4.json").read_text())
    assert not ({case["form"]["response_text"] for case in suite["cases"]}
                & {case["form"]["response_text"] for case in old["cases"]})
    rows = [score(case, synthetic_return(case)) for case in suite["cases"]]
    assert {item["expected"] for row in rows for item in row["atomic"]} == {
        "SUPPORTED_BY_VISIBLE_EVIDENCE", "CONTRADICTED_BY_VISIBLE_EVIDENCE",
        "INSUFFICIENT_VISIBLE_EVIDENCE", "PHYSICALLY_TRUE_BUT_UNSUPPORTED", "UNINTERPRETABLE"}
    metrics = aggregate(rows)
    assert metrics["atomic_accuracy"] == 1
    assert metrics["field_accuracy"] == 1
    assert metrics["highest_level_qualified"] is False


def test_negative_cause_and_nonestablishment_have_distinct_references():
    cases = {case["case_id"]: case for case in build()["cases"]}
    assert cases["nl-ho-08"]["expected"]["atomic_labels"][0]["label"] == "INSUFFICIENT_VISIBLE_EVIDENCE"
    assert cases["nl-ho-09"]["expected"]["atomic_labels"][0]["label"] == "SUPPORTED_BY_VISIBLE_EVIDENCE"
    assert cases["nl-ho-08"]["expected"]["limitation_preservation"][0]["preserved"] is False
    assert cases["nl-ho-09"]["expected"]["limitation_preservation"][0]["preserved"] is True
