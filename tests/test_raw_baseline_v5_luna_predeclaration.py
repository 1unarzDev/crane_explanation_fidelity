import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    ROOT / "manifests/annotation/luna-raw-baseline-v5-language-screen-v1-predeclaration.json"
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_luna_arm_is_frozen_before_calls_and_adds_no_clusters():
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["status"] == "FROZEN_BEFORE_ANY_LUNA_STUDY_CALL"
    assert manifest["prior_exposure"]["luna_study_judgments_generated"] == 0
    assert manifest["judge_execution"]["planned_judgments"] == 28
    boundary = manifest["statistical_boundary"]
    assert boundary["independent_clusters"] == 5
    assert boundary["new_independent_clusters"] == 0
    assert boundary["confirmatory_semantic_n"] == 0
    assert boundary["confirmatory_alpha_consumed"] == 0.0


def test_all_frozen_paths_and_counts_are_hash_bound():
    manifest = json.loads(MANIFEST_PATH.read_text())
    for section in ("treatment_contract", "frozen_artifacts", "judge_release"):
        values = manifest[section]
        for key, value in values.items():
            if not key.endswith("_sha256") or key == "committed_contract_sha256":
                continue
            path_key = key[: -len("_sha256")]
            if section == "treatment_contract" and path_key == "file":
                path_key = "path"
            assert path_key in values, (section, key)
            assert _digest(ROOT / values[path_key]) == value
    artifact_manifest = json.loads(
        (ROOT / manifest["frozen_artifacts"]["results_references_packets_manifest"]).read_text()
    )
    key_manifest = json.loads(
        (ROOT / manifest["frozen_artifacts"]["condition_key_manifest"]).read_text()
    )
    assert artifact_manifest["artifact_count"] == 21
    assert key_manifest["file_count"] == 7


def test_judge_references_exclude_proposed_diagnostic_and_evaluator_truth():
    manifest = json.loads(MANIFEST_PATH.read_text())
    artifact_manifest = json.loads(
        (ROOT / manifest["frozen_artifacts"]["results_references_packets_manifest"]).read_text()
    )
    references = [
        ROOT / item["path"]
        for item in artifact_manifest["artifacts"]
        if "/references/" in item["path"]
    ]
    assert len(references) == 7
    for path in references:
        reference = json.loads(path.read_text())
        allowed = reference["allowed_evidence"]
        assert "primitive_diagnostic" not in allowed
        audit = reference["completeness_audit"]
        assert audit["proposed_diagnostic_excluded_from_gold"] is True
        assert audit["evaluator_truth_excluded"] is True
