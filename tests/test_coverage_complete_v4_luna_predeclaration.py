import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREDECLARATION = (
    ROOT
    / "manifests/annotation/luna-coverage-complete-v4-language-screen-v1-predeclaration.json"
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_predeclaration_binds_exact_artifacts_and_qualified_judge_release():
    manifest = json.loads(PREDECLARATION.read_text())
    treatment = manifest["treatment_contract"]
    correction = manifest["transport_amendment"]
    artifacts = manifest["frozen_artifacts"]
    judge = manifest["judge_release"]

    for path_key, hash_key in (
        ("path", "file_sha256"),
    ):
        assert _digest(ROOT / treatment[path_key]) == treatment[hash_key]
    assert _digest(ROOT / correction["path"]) == correction["sha256"]
    assert _digest(ROOT / correction["reference_builder"]) == correction["reference_builder_sha256"]
    assert _digest(ROOT / artifacts["results_references_packets_manifest"]) == (
        artifacts["results_references_packets_manifest_sha256"]
    )
    assert _digest(ROOT / artifacts["condition_key_manifest"]) == (
        artifacts["condition_key_manifest_sha256"]
    )
    assert _digest(ROOT / artifacts["packet_builder"]) == artifacts["packet_builder_sha256"]
    for path_key, hash_key in (
        ("qualification_manifest", "qualification_manifest_sha256"),
        ("freeze", "freeze_sha256"),
        ("prompt", "prompt_sha256"),
        ("output_schema", "output_schema_sha256"),
        ("caller", "caller_sha256"),
        ("runner", "runner_sha256"),
    ):
        assert _digest(ROOT / judge[path_key]) == judge[hash_key]


def test_frozen_artifact_list_covers_exact_results_references_and_packets():
    manifest = json.loads(PREDECLARATION.read_text())
    path = ROOT / manifest["frozen_artifacts"]["results_references_packets_manifest"]
    inventory = json.loads(path.read_text())
    artifacts = inventory["artifacts"]

    assert inventory["status"] == "DEVELOPMENT_FROZEN_BEFORE_LUNA"
    assert len(artifacts) == inventory["artifact_count"] == 21
    assert len({item["path"] for item in artifacts}) == 21
    for item in artifacts:
        artifact = ROOT / item["path"]
        assert artifact.stat().st_size == item["bytes"]
        assert _digest(artifact) == item["sha256"]


def test_blinded_packets_and_evaluator_keys_have_exact_one_to_one_mapping():
    manifest = json.loads(PREDECLARATION.read_text())
    key_manifest = json.loads(
        (ROOT / manifest["frozen_artifacts"]["condition_key_manifest"]).read_text()
    )
    assert key_manifest["file_count"] == 7
    response_ids = set()
    conditions = []
    for entry in key_manifest["files"]:
        path = ROOT / entry["path"]
        assert _digest(path) == entry["sha256"]
        key = json.loads(path.read_text())
        packet = ROOT / key["packet"]
        assert _digest(packet) == key["packet_sha256"]
        rows = [json.loads(line) for line in packet.read_text().splitlines()]
        assert len(rows) == len(key["entries"]) == 2
        assert {row["response_id"] for row in rows} == {
            item["response_id"] for item in key["entries"]
        }
        assert all("condition" not in row and "model" not in row for row in rows)
        assert not response_ids & {row["response_id"] for row in rows}
        response_ids.update(row["response_id"] for row in rows)
        conditions.extend(item["condition"] for item in key["entries"])

    assert len(response_ids) == 14
    assert sorted(conditions) == ["P"] * 7 + ["R"] * 7


def test_cluster_and_call_accounting_remains_development_only():
    manifest = json.loads(PREDECLARATION.read_text())
    boundary = manifest["statistical_boundary"]
    cases = manifest["cases"]
    assert sum(item["independent_cluster"] for item in cases) == 5
    assert len({item["cluster_id"] for item in cases if item["independent_cluster"]}) == 5
    assert boundary["responses"] == 14
    assert manifest["judge_execution"]["planned_judgments"] == 28
    assert boundary["confirmatory_semantic_n"] == 0
    assert boundary["confirmatory_alpha_consumed"] == 0.0
