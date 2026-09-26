from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "analysis" / "run_luna_single_diagnostic_packet.py"
SPEC = importlib.util.spec_from_file_location("run_luna_single_diagnostic_packet", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_supported_success_requires_mechanism_and_no_material_error() -> None:
    assert MODULE.success({"mechanism_identification": "correct", "material_error": False})
    assert not MODULE.success({"mechanism_identification": "correct", "material_error": True})
    assert not MODULE.success({"mechanism_identification": "omitted", "material_error": False})


def test_v12_success_uses_atomic_mechanism_unit_not_generic_semantic_field() -> None:
    row = {
        "primary_endpoint_eligible": True,
        "mechanism_unit_id": "u-mechanism",
    }
    judgment = {
        "mechanism_identification": "not_applicable",
        "material_error": False,
        "required_units": [
            {"unit_id": "u-mechanism", "status": "covered"},
            {"unit_id": "u-limit", "status": "covered"},
        ],
    }
    assert MODULE.success(judgment, row) is True
    judgment["required_units"][0]["status"] = "omitted"
    assert MODULE.success(judgment, row) is False
    judgment["required_units"][0]["status"] = "covered"
    judgment["material_error"] = True
    assert MODULE.success(judgment, row) is False


def test_v12_guardrail_case_has_no_positive_mechanism_endpoint() -> None:
    row = {"primary_endpoint_eligible": False}
    judgment = {
        "mechanism_identification": "not_applicable",
        "material_error": False,
        "required_units": [{"unit_id": "u-qualification", "status": "covered"}],
    }
    assert MODULE.success(judgment, row) is None


def test_v12_coordinator_fields_are_not_exposed_to_frozen_judge_envelope() -> None:
    row = {
        "response_id": "opaque",
        "primary_endpoint_eligible": True,
        "mechanism_unit_id": "u-mechanism",
    }
    visible = MODULE.judge_visible_row(row)
    assert visible == {"response_id": "opaque"}


def test_incomplete_pass_is_represented_without_promoting_missing_label(tmp_path, monkeypatch) -> None:
    packet = tmp_path / "packet.jsonl"
    key = tmp_path / "key.json"
    rows = []
    entries = []
    for condition in ("R", "P", "T", "N"):
        response_id = f"opaque-{condition}"
        rows.append(
            {
                "response_id": response_id,
                "question": "What happened?",
                "question_kind": "diagnostic",
                "allowed_evidence": {},
                "required_units": [],
                "diagnosable": True,
                "prohibited_claims": [],
                "reference_status": "test",
                "response_text": "bounded",
            }
        )
        entries.append({"response_id": response_id, "condition": condition})
    packet.write_text("".join(__import__("json").dumps(row) + "\n" for row in rows))
    key.write_text(__import__("json").dumps({"entries": entries}))

    class FakeCaller:
        def __init__(self, *, cache, effort):
            self.pass_id = cache.name

        def call(self, envelope):
            if self.pass_id == "pass-2" and envelope["opaque_response_id"] == "opaque-R":
                raise RuntimeError("retained invalid judgment")
            return {
                "cache_key": f"{self.pass_id}-{envelope['opaque_response_id']}",
                "judgment": {
                    "mechanism_identification": "correct",
                    "material_error": False,
                },
            }

    monkeypatch.setattr(MODULE, "LunaIsolatedCodexCaller", FakeCaller)
    monkeypatch.setattr(
        MODULE,
        "packet_envelope",
        lambda row, rubric, pass_id: {"opaque_response_id": row["response_id"]},
    )
    report = MODULE.run(packet, key, tmp_path / "out")

    assert report["status"] == "DEVELOPMENT_ONLY_INCOMPLETE_JUDGE_FAILURE"
    assert report["valid_judgments"] == 7
    assert report["passes"]["pass-1"]["complete"] is True
    assert report["passes"]["pass-2"]["complete"] is False
    assert report["passes"]["pass-2"]["R"]["supported_diagnostic_success"] is None
    assert report["call_failures"][0]["condition"] == "R"


def test_two_condition_packet_runs_exactly_two_isolated_passes(tmp_path, monkeypatch) -> None:
    packet = tmp_path / "packet.jsonl"
    key = tmp_path / "key.json"
    rows = []
    entries = []
    for condition in ("R", "P"):
        response_id = f"opaque-{condition}"
        rows.append(
            {
                "response_id": response_id,
                "question": "What happened?",
                "question_kind": "diagnostic",
                "allowed_evidence": {},
                "required_units": [],
                "diagnosable": True,
                "prohibited_claims": [],
                "reference_status": "test",
                "response_text": "bounded",
            }
        )
        entries.append({"response_id": response_id, "condition": condition})
    packet.write_text("".join(__import__("json").dumps(row) + "\n" for row in rows))
    key.write_text(__import__("json").dumps({"entries": entries}))

    class FakeCaller:
        def __init__(self, *, cache, effort):
            self.pass_id = cache.name

        def call(self, envelope):
            return {
                "cache_key": f"{self.pass_id}-{envelope['opaque_response_id']}",
                "judgment": {
                    "mechanism_identification": "correct",
                    "material_error": False,
                },
            }

    monkeypatch.setattr(MODULE, "LunaIsolatedCodexCaller", FakeCaller)
    monkeypatch.setattr(
        MODULE,
        "packet_envelope",
        lambda row, rubric, pass_id: {"opaque_response_id": row["response_id"]},
    )
    report = MODULE.run(packet, key, tmp_path / "out")

    assert report["conditions"] == ["R", "P"]
    assert report["planned_judgments"] == 4
    assert report["valid_judgments"] == 4
    assert report["passes"]["pass-1"]["complete"] is True
    assert set(report["passes"]["pass-1"]) == {"R", "P", "complete"}
