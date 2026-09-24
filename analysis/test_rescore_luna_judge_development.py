import json
from pathlib import Path

from rescore_luna_judge_development import rescore
from run_luna_judge_qualification import CORE_FIELDS, load_suite


ROOT = Path(__file__).resolve().parents[1]
SUITE = (
    ROOT
    / "research/explanation_fidelity/qualification/"
    "luna-model-judge-v3-reference-amendment.json"
)


def _write_perfect_retained_calls(tmp_path: Path) -> tuple[Path, Path]:
    cases = [case for case in load_suite(SUITE)["cases"] if case["split"] == "development"]
    keys = {}
    calls_root = tmp_path / "calls"
    for index, case in enumerate(cases):
        key = f"key-{index}"
        keys[case["case_id"]] = key
        path = calls_root / "medium" / "qualification" / f"{key}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        judgment = {
            **{field: case["expected"][field] for field in CORE_FIELDS},
            "opaque_response_id": case["case_id"],
            "required_units": [
                {"unit_id": unit_id, "status": status}
                for unit_id, status in case["expected"]["required_unit_statuses"].items()
            ],
        }
        path.write_text(
            json.dumps({"status": "VALID", "judgment": judgment}), encoding="utf-8"
        )
    report = tmp_path / "prior.json"
    report.write_text(
        json.dumps({"call_cache_keys": {"medium": keys}}), encoding="utf-8"
    )
    return report, calls_root


def test_offline_rescore_uses_every_retained_call_without_new_model_calls(tmp_path):
    prior, calls = _write_perfect_retained_calls(tmp_path)
    report = rescore(
        suite_path=SUITE,
        prior_report_path=prior,
        calls_root=calls,
        effort="medium",
    )
    assert report["status"] == "QUALIFIED"
    assert report["model_calls_made"] == 0
    assert len(report["retained_call_sha256"]) == 14


def test_offline_rescore_rejects_response_id_mismatch(tmp_path):
    prior, calls = _write_perfect_retained_calls(tmp_path)
    first = next((calls / "medium" / "qualification").glob("*.json"))
    value = json.loads(first.read_text(encoding="utf-8"))
    value["judgment"]["opaque_response_id"] = "wrong"
    first.write_text(json.dumps(value), encoding="utf-8")
    try:
        rescore(
            suite_path=SUITE,
            prior_report_path=prior,
            calls_root=calls,
            effort="medium",
        )
    except ValueError as error:
        assert "response ID differs" in str(error)
    else:
        raise AssertionError("mismatched retained response ID was accepted")
