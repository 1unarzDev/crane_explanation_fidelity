import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load("primary_causal_builder", "analysis/build_contract_primary_causal_luna_qualification.py")


def test_primary_causal_suite_is_bounded_and_field_complete():
    suite = builder.build_suite()
    builder.validate(suite)
    assert len(suite["cases"]) == 12
    assert {case["split"] for case in suite["cases"]} == {"heldout"}
    assert all([unit["unit_id"] for unit in case["required_units"]] == ["M", "Q", "O", "L"] for case in suite["cases"])


def test_primary_causal_suite_covers_observed_gap_without_study_answers():
    suite = builder.build_suite()
    variants = {case["variant"] for case in suite["cases"]}
    assert {"hedged-plausible-wait-cause", "hedged-probable-wait-help", "wait-did-not-lead-to-success", "meaning-preserving-recovery-paraphrase"} <= variants
    assert sum(case["protected_causal"] for case in suite["cases"]) >= 8
    assert all("cc-pilot" not in str(case) for case in suite["cases"])
