"""Role bookkeeping integrity; no support/rank judgments or model calls."""
import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import build_evidence_calibration_role_disposition as module


def entry():
    return {"case_id": "blind-case", "response_text": "The action aborted.",
            "claims": [{"item_id": "atom", "claim_text": "The action aborted.", "response_span": "The action aborted."}]}


def role(kind="TASK_OUTCOME", polarity="POSITIVE"):
    return [{"item_id": "atom", "stance": "ASSERTED_FACT", "claim_kind": kind,
             "polarity": polarity, "rationale_span": "The action aborted."}]


def test_disagreement_retains_both_candidates_without_vote_or_rank():
    a, b = role(), role("SOFTWARE_ACTION_EVENT", "NEGATIVE")
    before = copy.deepcopy((a, b))
    row = module.disposition_rows(entry(), a, b, manual=False, missing=False)[0]
    assert (a, b) == before
    assert row["disposition"] == "RETAIN_BOTH_UNSELECTED"
    assert row["differing_axes"] == ["claim_kind", "polarity"]
    assert {item["claim_kind"] for item in row["role_tuple_candidates"]} == {"TASK_OUTCOME", "SOFTWARE_ACTION_EVENT"}
    assert row["selected_role"] is row["attached_contract"] is row["asserted_rank"] is row["mechanistic_flag"] is None
    assert row["endpoint_scoring_authorized"] is False


def test_missing_a_never_imputed_and_provenance_is_separate():
    row = module.disposition_rows(entry(), None, role(), manual=False, missing=True)[0]
    assert row["retained_roles"]["A"] is None and row["disposition"] == "INCOMPLETE_A_NO_IMPUTATION"
    assert row["manual_inventory_provenance"] is False
    assert len(row["role_tuple_candidates"]) == 1 and row["selected_role"] is None
    with pytest.raises(ValueError, match="missingness"):
        module.disposition_rows(entry(), role(), role(), manual=False, missing=True)
    with pytest.raises(ValueError, match="missingness"):
        module.disposition_rows(entry(), None, role(), manual=False, missing=False)


def test_agreement_does_not_erase_negative_causation_or_supply_rank():
    case = entry()
    case["response_text"] = "Measured response recovery does not cause the eventual task outcome."
    case["claims"][0].update(claim_text=case["response_text"], response_span=case["response_text"])
    a = role("RECOVERY_CAUSAL_RELATION", "NEGATIVE")
    a[0]["rationale_span"] = case["response_text"]
    row = module.disposition_rows(case, a, copy.deepcopy(a), manual=False, missing=False)[0]
    assert row["disposition"] == "RETAIN_AGREEMENT_ADVISORY_ONLY"
    assert row["project_review_concerns"] == ["EXPLICIT_NEGATIVE_CAUSATION_ASSERTION_MUST_NOT_BECOME_LIMITATION"]
    assert row["retained_roles"]["A"]["stance"] == "ASSERTED_FACT" and row["attached_contract"] is None


def test_raw_parsed_inconsistency_is_rejected_even_with_updated_file_hash(tmp_path):
    review = json.loads((module.ROOT / module.B_REVIEW).read_text())
    source = review["records"][0]["A_record"]
    record = json.loads((module.ROOT / source["path"]).read_text())
    record["parsed_final"]["claim_roles"][0]["claim_kind"] = "OTHER"
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(record))
    bundle = json.loads((module.ROOT / review["bindings"]["input_bundle"]["path"]).read_text())
    with pytest.raises(ValueError, match="raw return"):
        module.retained_roles(tmp_path, bundle["entries"][0], "A",
                              {"path": path.name, "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})


def test_full_bound_bank_reconstructs_all_reviewed_differences_and_distinct_missingness():
    result = module.build()
    saved = json.loads((module.ROOT / module.OUTPUT).read_text())
    assert result == saved
    assert (result["known_A_returns"], result["known_B_returns"], result["paired_atom_count"]) == (113, 114, 1071)
    assert result["manual_inventory_response_id"] != result["missing_role_A_response_id"]
    assert [item["atom_count"] for item in result["blind_sensitivity_triggers"]] == [15, 13]
    rows = result["rows"]
    assert len(rows) == 1084 and sum(row["disposition"] == "RETAIN_BOTH_UNSELECTED" for row in rows) == 53
    assert sum(row["retained_roles"]["A"] is None for row in rows) == 13
    assert sum("EXPLICIT_NEGATIVE_CAUSATION_ASSERTION_MUST_NOT_BECOME_LIMITATION" in row["project_review_concerns"] for row in rows) == 6
    assert sum("REVIEWED_ABORT_OCCURRENCE_POLARITY_ERROR_RAW_RETAINED" in row["project_review_concerns"] for row in rows) == 2
    assert not result["complete_two_pass_role_bank"] and not result["semantic_role_adjudication_claimed"]
    assert all(row["asserted_rank"] is None and row["selected_role"] is None for row in rows)
    assert result["sensitivity_policy"]["select_variant_by_effect_or_p_value_prohibited"] is True


def joined_metadata(same_episode=False):
    return [{"opaque_response_id": response, "episode_id": episode, "configuration_id": config}
            for response, episode, config in [("manual", "ep-1", "cfg-1"), ("other-method-other-mask", "ep-1", "cfg-1"),
                                              ("missing", "ep-1" if same_episode else "ep-2", "cfg-1" if same_episode else "cfg-2"),
                                              ("clean", "ep-3", "cfg-3")]]


def triggers():
    return [{"case_id": "manual", "reason": "PROJECT_AUTHORED_EXTRACTION_INVENTORY"},
            {"case_id": "missing", "reason": "ORIGINAL_ROLE_A_UNKNOWN_NO_REPLACEMENT"}]


def test_sensitivity_excludes_whole_episode_across_methods_and_masks():
    result = module.episode_sensitivity_sets(joined_metadata(), triggers(), join_authorized=True)
    manual = result["EXCLUDE_WHOLE_EPISODE_CONTAINING_MANUAL_INVENTORY"]
    assert manual["retained_response_ids"] == ["clean", "missing"]
    union = result["EXCLUDE_UNION_OF_BOTH_EPISODE_SETS"]
    assert union["retained_response_ids"] == ["clean"] and union["retained_independent_episode_configuration_count"] == 1
    assert result["FULL_RETAINED_BANK_WITH_FLAGS"]["retained_independent_episode_configuration_count"] == 3


def test_two_triggers_in_same_episode_do_not_duplicate_independent_exclusion():
    result = module.episode_sensitivity_sets(joined_metadata(True), triggers(), join_authorized=True)
    union = result["EXCLUDE_UNION_OF_BOTH_EPISODE_SETS"]
    assert union["excluded_episode_configuration_ids"] == [["ep-1", "cfg-1"]]
    assert union["retained_response_ids"] == ["clean"]


def test_sensitivity_rejects_premature_join_and_inconsistent_units():
    with pytest.raises(ValueError, match="separately authorized"):
        module.episode_sensitivity_sets(joined_metadata(), triggers())
    rows = joined_metadata()
    rows[1]["configuration_id"] = "cfg-9"
    with pytest.raises(ValueError, match="one-to-one"):
        module.episode_sensitivity_sets(rows, triggers(), join_authorized=True)
    with pytest.raises(ValueError, match="missing"):
        module.episode_sensitivity_sets(joined_metadata(), [*triggers(), triggers()[0]], join_authorized=True)
