import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

from build_evidence_calibration_agent_qualification import LEVELS
from build_evidence_calibration_neutral_level_suite import build as old_build
from build_evidence_calibration_neutral_level_suite_v2 import NON_RANK_OPTIONS, build
from evidence_calibration_io import canonical_sha256
from evidence_calibration_neutral_level_qualification import packet_for as old_packet_for
from evidence_calibration_neutral_level_qualification_v2 import aggregate, packet_for, score_return


def synthetic_return(case, level):
    packet = packet_for(case, "A", "offline-synthetic-test")
    form = packet["forms"][0]
    return {"schema": "crane-blinded-atomic-annotation-return/v1",
            "packet_set_sha256": canonical_sha256(packet), "form_id": form["form_id"],
            "packet_id": form["packet_id"], "annotator_slot": "A", "annotator_id": "agent-A-offline-test",
            "annotator_attestation": "INDEPENDENT_BLINDED_COMPLETE",
            "atomic_labels": [{**item, "annotation_notes": "offline structural fixture"}
                              for item in case["expected"]["atomic_labels"]],
            "required_unit_coverage": copy.deepcopy(case["expected"]["required_unit_coverage"]),
            "limitation_preservation": copy.deepcopy(case["expected"]["limitation_preservation"]),
            "false_premise_handling": case["expected"]["false_premise_handling"],
            "highest_asserted_abstraction_level": level}


def score(case, returned):
    return score_return(case, returned, slot="A", suite_hash="offline-synthetic-test")


def test_uniform_options_do_not_mutate_frozen_legacy_payloads():
    legacy_before = old_build()
    suite = build()
    assert build() == suite
    assert old_build() == legacy_before
    assert len(LEVELS) == 6
    assert all(case["form"]["abstraction_level_options"] == [*LEVELS, *NON_RANK_OPTIONS]
               for case in suite["cases"])
    assert len(suite["cases"]) == 20
    assert sum(case["split"] == "heldout" for case in suite["cases"]) == 16
    assert not ({case["form"]["response_text"] for case in suite["cases"]}
                & {case["form"]["response_text"] for case in legacy_before["cases"]})
    for name in ("evidence-calibration-agent-exact-task-v4.json",):
        old = json.loads((Path(__file__).resolve().parents[1] /
                         "research/explanation_fidelity/qualification" / name).read_text())
        assert not ({case["form"]["response_text"] for case in suite["cases"]}
                    & {case["form"]["response_text"] for case in old["cases"]})


def test_non_rank_sentinels_do_not_supply_accuracy_or_endpoint_rank():
    case = build()["cases"][3]
    rows = [score(case, synthetic_return(case, level)) for level in [*LEVELS, *NON_RANK_OPTIONS]]
    assert all(row == rows[0] for row in rows)
    assert rows[0]["highest_level_qualified"] is False
    assert rows[0]["endpoint_scoring_authorized"] is False
    assert rows[0]["atomic"][0]["expected"] == "UNINTERPRETABLE"
    # The original stopped interface still rejects its failed value.
    old = old_build()["cases"][3]
    old_packet = old_packet_for(old, "A", "offline-synthetic-test")
    returned = synthetic_return(case, "UNINTERPRETABLE")
    returned.update(packet_set_sha256=canonical_sha256(old_packet),
                    form_id=old_packet["forms"][0]["form_id"],
                    packet_id=old_packet["forms"][0]["packet_id"])
    returned["atomic_labels"][0]["item_id"] = old["expected"]["atomic_labels"][0]["item_id"]
    from adjudicate_evidence_calibration_annotations import validate_return
    with pytest.raises(ValueError, match="outside the packet options"):
        validate_return(old_packet, returned)


def test_new_options_preserve_support_error_and_positive_span_checks():
    suite = build()
    rows = [score(case, synthetic_return(case, "NO_DIAGNOSTIC_ASSERTION")) for case in suite["cases"]]
    metrics = aggregate(rows)
    assert metrics["atomic_accuracy"] == metrics["field_accuracy"] == 1
    case = next(c for c in suite["cases"] if c["case_id"] == "nl2-ho-06")
    returned = synthetic_return(case, "UNINTERPRETABLE")
    returned["atomic_labels"][0]["label"] = "SUPPORTED_BY_VISIBLE_EVIDENCE"
    metrics = aggregate([score(case, returned)])
    assert metrics["unsupported_false_acceptance_rate"] == 1
    assert metrics["required_unit_accuracy"] == 1
    returned["required_unit_coverage"][0]["response_span"] = "invented span"
    with pytest.raises(ValueError, match="exact response text"):
        score(case, returned)


def test_payload_does_not_adapt_options_to_reference_labels_or_supply_anchors():
    case = copy.deepcopy(build()["cases"][0])
    case["form"]["abstraction_level_options"].remove("UNINTERPRETABLE")
    with pytest.raises(ValueError, match="uniform"):
        packet_for(case, "A", "offline-synthetic-test")
    case = copy.deepcopy(build()["cases"][0])
    case["form"]["atomic_statements"][0]["asserted_abstraction_level"] = "task_outcome"
    with pytest.raises(ValueError, match="anchor"):
        packet_for(case, "A", "offline-synthetic-test")
