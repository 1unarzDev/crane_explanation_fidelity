import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads(
    (
        ROOT
        / "manifests/annotation/luna-coverage-complete-v4-evidence-complete-v2-predeclaration.json"
    ).read_text()
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_revised_arm_is_hash_frozen_before_calls_and_adds_no_clusters():
    assert MANIFEST["status"] == "FROZEN_BEFORE_ANY_REVISED_LUNA_CALL"
    assert MANIFEST["prior_exposure"]["revised_luna_calls_generated"] == 0
    assert MANIFEST["judge_execution"]["planned_judgments"] == 28
    boundary = MANIFEST["statistical_boundary"]
    assert boundary["independent_clusters"] == 5
    assert boundary["this_reevaluation_adds_clusters"] == 0
    assert boundary["confirmatory_semantic_n"] == 0
    assert boundary["confirmatory_alpha_consumed"] == 0.0


def test_exact_correction_and_packet_artifacts_are_bound():
    correction = MANIFEST["correction"]
    assert _digest(ROOT / correction["amendment"]) == correction["amendment_sha256"]
    assert _digest(ROOT / correction["reference_builder"]) == correction[
        "reference_builder_sha256"
    ]
    frozen = MANIFEST["frozen_artifacts"]
    assert _digest(ROOT / frozen["references_and_packets_manifest"]) == frozen[
        "references_and_packets_manifest_sha256"
    ]
    assert _digest(ROOT / frozen["condition_key_manifest"]) == frozen[
        "condition_key_manifest_sha256"
    ]


def test_every_revised_packet_contains_full_primitive_and_source_excerpts():
    artifact_manifest = json.loads(
        (ROOT / MANIFEST["frozen_artifacts"]["references_and_packets_manifest"]).read_text()
    )
    assert artifact_manifest["artifact_count"] == 14
    reference_paths = [
        ROOT / item["path"]
        for item in artifact_manifest["artifacts"]
        if "/references/" in item["path"]
    ]
    assert len(reference_paths) == 7
    for path in reference_paths:
        reference = json.loads(path.read_text())
        allowed = reference["allowed_evidence"]
        assert allowed["primitive_diagnostic"]["method_input"]
        assert len(allowed["source_and_config_excerpts"]) == 7
        assert reference["evidence_parity_revision"]["method_response_content_changed"] is False
