import importlib.util
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER=load("build_luna_v11",ROOT/"analysis/build_luna_v11_qualification_suite.py")
RUNNER=load("run_luna_v11",ROOT/"analysis/run_luna_v11_qualification.py")


def test_v11_suite_is_fresh_and_endpoint_aligned():
    suite=BUILDER.build_suite(); BUILDER.validate(suite)
    cases=suite["cases"]
    assert len(cases)==22
    assert sum(case["accuracy_eligible"] for case in cases)==20
    assert sum(case["primary_endpoint_eligible"] for case in cases)==12
    assert all(case["case_id"].startswith("Q11") for case in cases)
    assert all(
        not case["primary_endpoint_eligible"] or case["mechanism_unit_id"]
        for case in cases
    )


def test_v11_endpoint_uses_atomic_mechanism_unit_and_material_risk():
    case=next(item for item in BUILDER.build_suite()["cases"] if item["case_id"]=="Q11H01S")
    actual={
        "material_error":False,
        "required_units":[
            {"unit_id":"u-measurements","status":"covered"},
            {"unit_id":"u-mechanism","status":"covered"},
            {"unit_id":"u-limit","status":"covered"},
        ],
    }
    assert RUNNER.endpoint_success(case,actual)
    actual["material_error"]=True
    assert not RUNNER.endpoint_success(case,actual)


def test_v11_nonmechanism_controls_exclude_ambiguous_mechanism_field():
    cases=BUILDER.build_suite()["cases"]
    for case in cases:
        if case["accuracy_eligible"] and not case["primary_endpoint_eligible"]:
            assert "mechanism_identification" not in case["scored_core_fields"]
