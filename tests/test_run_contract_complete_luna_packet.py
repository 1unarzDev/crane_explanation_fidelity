from __future__ import annotations

from analysis.run_contract_complete_luna_packet import endpoint_record, qualified_release


def judgment(*, q: str = "covered", material: bool = False) -> dict:
    return {
        "material_error": material,
        "material_error_categories": ["incorrect_measurement"] if material else [],
        "required_units": [
            {"unit_id": code, "status": q if code == "Q" else "covered"}
            for code in ("M", "Q", "O", "L")
        ],
    }


def test_endpoint_record_derives_both_registered_claim_fields() -> None:
    complete = endpoint_record(judgment())
    assert complete["claim_a_complete_supported_communication"] is True
    assert complete["claim_b_substantive_assertion_error"] is False
    omitted = endpoint_record(judgment(q="omitted"))
    assert omitted["claim_a_complete_supported_communication"] is False
    assert omitted["claim_b_substantive_assertion_error"] is False
    erroneous = endpoint_record(judgment(q="incorrect", material=True))
    assert erroneous["claim_a_complete_supported_communication"] is False
    assert erroneous["claim_b_substantive_assertion_error"] is True


def test_runner_accepts_only_the_retained_qualified_v2_release() -> None:
    release = qualified_release()
    assert release["qualification_id"] == "contract-complete-luna-qualification-v2"
    assert release["qualification_status"] == "HELDOUT_QUALIFIED"
