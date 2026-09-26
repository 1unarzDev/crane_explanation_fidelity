import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARM = "raw-baseline-v5-language-screen-v1-evidence-closure-v2"
MANIFEST_PATH = ROOT / f"manifests/annotation/luna-{ARM}-predeclaration.json"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_revised_arm_is_frozen_before_calls_and_adds_no_clusters():
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["status"] == "FROZEN_BEFORE_ANY_REVISED_LUNA_CALL"
    assert manifest["prior_exposure"]["revised_luna_calls_generated"] == 0
    assert manifest["judge_execution"]["planned_judgments"] == 28
    boundary = manifest["statistical_boundary"]
    assert boundary["independent_clusters"] == 5
    assert boundary["this_reevaluation_adds_clusters"] == 0
    assert boundary["confirmatory_semantic_n"] == 0
    assert boundary["confirmatory_alpha_consumed"] == 0.0


def test_all_correction_and_frozen_artifact_hashes_validate():
    manifest = json.loads(MANIFEST_PATH.read_text())
    for section in ("correction", "frozen_artifacts", "judge_release"):
        values = manifest[section]
        for key, value in values.items():
            if not key.endswith("_sha256"):
                continue
            path_key = key[: -len("_sha256")]
            assert path_key in values, (section, key)
            assert _digest(ROOT / values[path_key]) == value


def test_every_reference_has_systematic_raw_closure_without_changed_units():
    manifest = json.loads(MANIFEST_PATH.read_text())
    artifact_manifest = json.loads(
        (ROOT / manifest["frozen_artifacts"]["references_and_packets_manifest"]).read_text()
    )
    references = [
        ROOT / item["path"]
        for item in artifact_manifest["artifacts"]
        if "/references/" in item["path"]
    ]
    assert len(references) == 7
    for path in references:
        reference = json.loads(path.read_text())
        closure = reference["allowed_evidence"]["raw_evidence_closure"]
        assert closure["schema"] == "crane-raw-baseline-v5-judge-evidence-closure/v1"
        assert closure["selection_rule"]
        revision = reference["evidence_closure_revision"]
        assert revision["method_response_content_changed"] is False
        assert revision["required_units_changed"] is False
        assert revision["prohibited_claims_changed"] is False
