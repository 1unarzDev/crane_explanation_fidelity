import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "freeze_readiness", ROOT / "scripts/audit_evidence_calibration_freeze_readiness.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
MANIFEST = json.loads((ROOT / "manifests/study/evidence-calibration-p11-prefreeze-readiness.json").read_text())


def test_current_repository_fails_closed_before_p11():
    result = MODULE.audit(ROOT, MANIFEST)
    assert not result["ready"]
    assert result["confirmation_independent_n"] == 0
    assert any("fresh_b2_b4_development_pilot" in item for item in result["failures"])
    assert any("P11 freeze" in item for item in result["failures"])


def test_hash_change_blocks_even_nominally_passed_manifest(tmp_path):
    staged = copy.deepcopy(MANIFEST)
    for requirement in staged["requirements"]:
        requirement.update(status="PASS", evidence="test evidence")
    staged.update(status="P11_FROZEN", confirmation_authorized=True)
    staged["development_components"][0]["sha256"] = "0" * 64
    result = MODULE.audit(ROOT, staged)
    assert not result["ready"]
    assert any("hash mismatch" in item for item in result["failures"])
