from __future__ import annotations

from score_contract_complete_judgment import score


def judgment(statuses: dict[str, str], *, material: bool = False, categories=None) -> dict:
    return {
        "judgment_status": "resolved",
        "material_error": material,
        "material_error_categories": categories or [],
        "required_units": [
            {"unit_id": code, "status": value, "response_span": code, "justification": "checked"}
            for code, value in statuses.items()
        ],
        "claims": [],
    }


def test_claim_a_is_exact_mqol_composite_and_claim_b_is_substantive_risk() -> None:
    result = score(judgment({code: "covered" for code in "MQOL"}))
    assert result["fields"] == {code: True for code in "MQOL"}
    assert result["claim_a_complete_supported_communication"] is True
    assert result["claim_b_substantive_assertion_error"] is False


def test_omission_fails_completeness_without_becoming_assertion_error() -> None:
    result = score(judgment({"M": "covered", "Q": "omitted", "O": "covered", "L": "covered"}))
    assert result["claim_a_complete_supported_communication"] is False
    assert result["claim_b_substantive_assertion_error"] is False
    assert result["failed_fields"] == ["Q"]


def test_wrong_measurement_fails_both_claim_endpoints() -> None:
    result = score(
        judgment(
            {"M": "covered", "Q": "incorrect", "O": "covered", "L": "covered"},
            material=True,
            categories=["incorrect_measurement"],
        )
    )
    assert result["claim_a_complete_supported_communication"] is False
    assert result["claim_b_substantive_assertion_error"] is True


def test_unresolved_field_stays_unresolved() -> None:
    result = score(judgment({"M": "covered", "Q": "unresolved", "O": "covered", "L": "covered"}))
    assert result["claim_a_complete_supported_communication"] is None
    assert result["unresolved_fields"] == ["Q"]


def test_independently_verified_cosmetic_citation_format_is_not_substantive() -> None:
    value = judgment(
        {code: "covered" for code in "MQOL"},
        material=True,
        categories=["incorrect_identifier"],
    )
    result = score(value, deterministic_citation_format_only=True)
    assert result["claim_a_complete_supported_communication"] is True
    assert result["claim_b_substantive_assertion_error"] is False
    assert result["broader_material_error"] is True
