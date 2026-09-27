from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from repair_luna_opaque_ids import repair_record


def _judgment(response_id: str) -> dict:
    return {
        "schema": "crane-luna-model-judge-output/v1",
        "annotation_origin": "automated",
        "arm_id": "luna-model-judge-v1",
        "opaque_response_id": response_id,
        "pass_id": "pass-1",
        "rubric": "diagnostic",
        "judgment_status": "resolved",
        "answerability": "answerable",
        "material_error": False,
        "material_error_categories": [],
        "claims": [],
        "required_units": [],
        "disposition": "full",
        "mechanism_identification": "correct",
        "correct_abstention": False,
        "causal_overclaim": False,
        "evidence_problem": False,
        "evidence_problem_detail": None,
        "unresolved_fields": [],
        "rationale": "The retained judgment is complete.",
    }


def _record(expected: str, returned: str) -> dict:
    judgment = _judgment(returned)
    return {
        "schema": "crane-luna-model-judge-call/v1",
        "status": "INVALID_JUDGMENT_NO_RETRY",
        "cache_key": "a" * 64,
        "request_identity": {
            "envelope": {
                "opaque_response_id": expected,
                "pass_id": "pass-1",
                "rubric": "diagnostic",
            }
        },
        "raw_final": json.dumps(judgment, sort_keys=True),
        "validation_error": "judgment opaque_response_id does not match request",
    }


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_repairs_only_the_uniquely_bound_opaque_id(tmp_path: Path) -> None:
    expected = "0123456789abcdef01234567"
    source = tmp_path / ("a" * 64 + ".json")
    output = tmp_path / "repaired.json"
    _write(source, _record(expected, "01234567-89ab-cdef-0123-4567"))

    provenance = repair_record(source, output, {expected, "fedcba9876543210fedcba98"})
    repaired = json.loads(output.read_text(encoding="utf-8"))

    assert repaired["status"] == "VALID"
    assert repaired["judgment"]["opaque_response_id"] == expected
    assert repaired["transport_repair"]["semantic_payload_unchanged"] is True
    assert provenance["changed_fields"] == ["opaque_response_id"]
    assert provenance["source_record_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda r: r.update(status="VALID"), "not a retained invalid judgment"),
        (lambda r: r.update(validation_error="judgment rubric does not match request"), "not ID-only"),
        (lambda r: r.update(raw_final="not-json"), "not valid JSON"),
    ],
)
def test_rejects_non_id_only_or_incomplete_failures(
    tmp_path: Path, mutation, match: str
) -> None:
    expected = "0123456789abcdef01234567"
    record = _record(expected, "0123456789abcdef0123456x")
    mutation(record)
    source = tmp_path / ("a" * 64 + ".json")
    _write(source, record)
    with pytest.raises(ValueError, match=match):
        repair_record(
            source,
            tmp_path / "repaired.json",
            {expected, "fedcba9876543210fedcba98"},
        )


def test_rejects_ambiguous_returned_id(tmp_path: Path) -> None:
    expected = "0123456789abcdef01234567"
    other = "fedcba9876543210fedcba98"
    source = tmp_path / ("a" * 64 + ".json")
    _write(source, _record(expected, other))
    with pytest.raises(ValueError, match="another packet response"):
        repair_record(source, tmp_path / "repaired.json", {expected, other})


def test_rejects_any_semantic_schema_defect(tmp_path: Path) -> None:
    expected = "0123456789abcdef01234567"
    record = _record(expected, "0123456789abcdef0123456x")
    raw = json.loads(record["raw_final"])
    del raw["material_error"]
    record["raw_final"] = json.dumps(raw)
    source = tmp_path / ("a" * 64 + ".json")
    _write(source, record)
    with pytest.raises(ValueError, match="fields differ from schema"):
        repair_record(
            source,
            tmp_path / "repaired.json",
            {expected, "fedcba9876543210fedcba98"},
        )
