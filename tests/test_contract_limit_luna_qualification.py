from __future__ import annotations

from analysis.build_contract_limit_luna_qualification import build_suite, validate


def test_missing_command_extension_is_bounded_and_field_complete() -> None:
    suite = build_suite()
    validate(suite)
    assert len(suite["cases"]) == 10
    assert all(
        [unit["unit_id"] for unit in case["required_units"]] == ["M", "Q", "O", "L"]
        for case in suite["cases"]
    )
    assert sum(case["protected_causal"] for case in suite["cases"]) == 3
    assert any(case["variant"] == "instruction-in-evidence" for case in suite["cases"])
    assert any(case["variant"] == "correct-paraphrase" for case in suite["cases"])


def test_missing_command_extension_has_both_acceptance_directions() -> None:
    suite = build_suite()
    material = [case["expected"]["material_error"] for case in suite["cases"]]
    assert any(material)
    assert any(not value for value in material)
    assert all(case["expected"]["answerability"] == "answer_insufficient" for case in suite["cases"])
