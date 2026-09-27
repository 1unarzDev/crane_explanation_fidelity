import json
from pathlib import Path

import pytest

from analysis.audit_explicit_causal_links import (
    RULE_IDS,
    candidate_version,
    classify_text,
    load_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / (
    "research/explanation_fidelity/experiment_configs/development/"
    "explicit-prohibited-causal-link-contract-v1.json"
)


SAFE = [
    "The record does not establish that Wait caused recovery.",
    "Recovery preceded success, but that order does not prove that recovery caused success.",
    "Recovery preceded success, but that order does **not establish that recovery caused success**.",
    "The sequence is consistent with recovery after Wait.",
    "A Wait invocation occurred, measured motion later recovered, and the action subsequently aborted.",
    "The physical cause remains unresolved.",
    "The discrepancy and abort were both recorded; their causal relationship is unknown.",
    "### Limitation\n**The record does not establish that Wait caused recovery.**",
    "The record does not establish that the discrepancy caused the abort; therefore the cause remains unresolved.",
    "There is no evidence that Wait caused recovery.",
    "It cannot be shown that recovery led to success.",
    "An obstruction could explain the discrepancy, but it is only an unresolved alternative.",
]

VIOLATIONS = {
    "The Waits did not lead to task success.": "wait_to_outcome_effect",
    "The Wait invocations did not yield a successful action.": "wait_to_outcome_effect",
    "The Waits did not produce task success.": "wait_to_outcome_effect",
    "Wait probably helped the robot regain motion.": "wait_to_recovery_effect",
    "The recorded Wait plausibly caused recovery.": "wait_to_recovery_effect",
    "The recorded failure and Wait invocation make Wait-to-recovery plausible.": "wait_to_recovery_effect",
    "Wait restored motion.": "wait_to_recovery_effect",
    "Recovery caused the eventual success.": "recovery_to_outcome_effect",
    "The discrepancy caused the abort.": "discrepancy_to_outcome_effect",
    "A physical obstacle caused the failure.": "physical_cause_assertion",
    "A blocked wheel caused the discrepancy and abort.": "physical_cause_assertion",
    "Wait may have caused the recovery.": "wait_to_recovery_effect",
    "Wait resulted in recovery.": "wait_to_recovery_effect",
    "The recovery led to success.": "recovery_to_outcome_effect",
    "The discrepancy resulted in failure.": "discrepancy_to_outcome_effect",
    "Motor failure may have led to the abort.": "physical_cause_assertion",
}


def test_safe_limit_and_chronology_language_is_not_flagged():
    for text in SAFE:
        assert classify_text(text) == [], text


def test_explicit_prohibited_relations_are_flagged_with_exact_spans():
    for text, relation in VIOLATIONS.items():
        findings = classify_text(text)
        assert len(findings) == 1, text
        assert findings[0]["relation"] == relation
        assert findings[0]["span"] in text


def test_mixed_answer_retains_only_the_asserted_relation():
    text = (
        "The record does not establish that Wait caused recovery. "
        "Recovery preceded success. The Waits did not lead to task success."
    )
    findings = classify_text(text)
    assert [item["relation"] for item in findings] == ["wait_to_outcome_effect"]


def test_candidate_version_accepts_retained_and_structured_pair_schemas():
    assert candidate_version({"candidate": "p-contract-v2-development"}) == "p-contract-v2-development"
    assert candidate_version({"candidate": {"version": "p-contract-v3"}}) == "p-contract-v3"
    assert candidate_version({"candidate": None}) is None


def test_contract_selects_rules_by_family_and_cannot_silently_name_unknown_rules(tmp_path):
    prohibited = load_contract(CONTRACT)
    assert set(prohibited) == {
        "persistent_command_motion_discrepancy",
        "measured_response_recovery",
    }
    assert prohibited["persistent_command_motion_discrepancy"] == RULE_IDS

    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    value["prohibited_relation_ids_by_family"]["measured_response_recovery"].append(
        "invented_relation"
    )
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown relation IDs"):
        load_contract(invalid)


def test_supported_relation_can_be_excluded_prospectively():
    text = "The discrepancy caused the abort."
    assert classify_text(text)
    permitted = RULE_IDS - {"discrepancy_to_outcome_effect"}
    assert classify_text(text, permitted) == []


def test_markdown_and_multiple_findings_preserve_exact_offsets():
    text = (
        "### Outcome\n**The Waits did not lead to task success.** "
        "Later, the discrepancy caused the abort."
    )
    findings = classify_text(text)
    assert [item["relation"] for item in findings] == [
        "wait_to_outcome_effect",
        "discrepancy_to_outcome_effect",
    ]
    for finding in findings:
        assert text[finding["start"] : finding["end"]] == finding["span"]


def test_finite_detector_does_not_claim_to_cover_unregistered_wording():
    # This is intentionally outside v1's finite grammar. Semantic review remains necessary.
    assert classify_text("The stall was responsible for the mission ending.") == []
