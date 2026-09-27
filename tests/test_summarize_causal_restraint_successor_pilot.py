from summarize_causal_restraint_successor_pilot import CONFIRMED, FALSE_POSITIVE


def test_audit_dispositions_are_distinct_and_stable():
    assert FALSE_POSITIVE == "FALSE_POSITIVE_EXPLICIT_NONESTABLISHMENT"
    assert CONFIRMED == "CONFIRMED_PROHIBITED_ASSERTION"
    assert FALSE_POSITIVE != CONFIRMED
