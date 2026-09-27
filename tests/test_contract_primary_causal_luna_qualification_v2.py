import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load():
    path = ROOT / "analysis/build_contract_primary_causal_luna_qualification_v2.py"
    spec = importlib.util.spec_from_file_location("primary_causal_builder_v2", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_v2_uses_fresh_cases_and_separates_extra_errors_from_required_units():
    builder = load()
    suite = builder.build_suite()
    builder.validate(suite)
    assert len(suite["cases"]) == 12
    assert all(case["case_id"].startswith("CCP2") for case in suite["cases"])
    for variant in ("additional-plausible-cause", "additional-probable-help", "additional-no-success-effect", "additional-obstacle-cause"):
        case = next(item for item in suite["cases"] if item["variant"] == variant)
        assert case["expected"]["material_error"] is True
        assert case["expected"]["causal_overclaim"] is True
        assert set(case["expected"]["required_unit_statuses"].values()) == {"covered"}
        assert case["expected"]["disposition"] == "full"
