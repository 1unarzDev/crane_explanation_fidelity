from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "manifests/annotation/luna-checked-composition-multifamily-screen-v1-predeclaration.json"
)
OUTPUT_ROOT = (
    ROOT / "model_outputs/dev/diagnostic-checked-composition-multifamily-screen-v1"
)
KEY_ROOT = (
    ROOT
    / "data/evaluator_only/dev/diagnostic-checked-composition-multifamily-screen-v1"
    / "annotation_keys"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_frozen_screen_artifact_inventory_is_exact() -> None:
    manifest = load(MANIFEST)
    assert manifest["status"] == "FROZEN_BEFORE_ANY_LUNA_STUDY_CALL"
    assert manifest["inferential_status"] == "DEVELOPMENT_ONLY_NOT_CONFIRMATORY"
    assert manifest["statistical_boundary"] == {
        "independent_unit": "scenario configuration",
        "independent_clusters": 6,
        "paired_masks": 1,
        "paired_masks_add_clusters": 0,
        "question_variants_add_clusters": 0,
        "model_generations_add_clusters": 0,
        "luna_passes_add_clusters": 0,
        "confirmatory_alpha_consumed": 0.0,
    }
    assert manifest["judge_execution"]["planned_judgments"] == 28
    assert manifest["judge_execution"]["judge_calls_at_freeze"] == 0
    assert manifest["judge_execution"]["usable_judgment_retry_allowed"] is False

    artifacts = manifest["artifacts"]
    assert len(artifacts) == 7
    assert len({item["case_id"] for item in artifacts}) == 7
    response_ids: set[str] = set()
    for item in artifacts:
        case_id = item["case_id"]
        paths = {
            "result_sha256": OUTPUT_ROOT / "results" / f"{case_id}.json",
            "reference_sha256": OUTPUT_ROOT / "references" / f"{case_id}.json",
            "packet_sha256": OUTPUT_ROOT / "annotation_packets" / f"{case_id}.jsonl",
            "key_sha256": KEY_ROOT / f"{case_id}.json",
        }
        for field, path in paths.items():
            assert path.is_file()
            assert item[field] == sha256(path)
        rows = [
            json.loads(line)
            for line in paths["packet_sha256"].read_text(encoding="utf-8").splitlines()
            if line
        ]
        key = load(paths["key_sha256"])
        assert len(rows) == 2
        assert {entry["condition"] for entry in key["entries"]} == {"R", "P"}
        assert {row["response_id"] for row in rows} == {
            entry["response_id"] for entry in key["entries"]
        }
        assert not response_ids.intersection(row["response_id"] for row in rows)
        response_ids.update(row["response_id"] for row in rows)
    assert len(response_ids) == 14


def test_frozen_screen_uses_exact_qualified_v12_release() -> None:
    manifest = load(MANIFEST)
    release = manifest["judge_release"]
    paths = {
        "qualification_manifest_sha256": ROOT / release["qualification_manifest"],
        "freeze_sha256": ROOT / release["freeze"],
        "prompt_sha256": ROOT / release["prompt"],
        "output_schema_sha256": ROOT / release["output_schema"],
        "caller_sha256": ROOT / release["caller"],
        "runner_sha256": ROOT / release["runner"],
    }
    for field, path in paths.items():
        assert release[field] == sha256(path)
    qualification = load(paths["qualification_manifest_sha256"])
    assert qualification["status"] == "HELDOUT_QUALIFIED"
    assert qualification["study_evaluation_allowed"] is True
    assert qualification["freeze"]["sha256"] == release["freeze_sha256"]
    freeze = load(paths["freeze_sha256"])
    assert freeze["prompt_sha256"] == release["prompt_sha256"]
    assert freeze["output_schema_sha256"] == release["output_schema_sha256"]
    assert freeze["caller_source_sha256"] == release["caller_sha256"]
