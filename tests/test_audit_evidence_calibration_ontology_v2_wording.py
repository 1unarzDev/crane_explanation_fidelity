import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_ontology_v2_wording import MANIFEST, NEW, audit  # noqa: E402


def test_v2_repairs_only_limitation_wording():
    result = audit()
    assert result["changed_rationales"] == 3
    assert result["claim_contracts_changed"] is False
    assert result["old_outputs_rescored"] is False
    assert result["p11_authorized"] is False
    text = NEW.read_text()
    assert "these specific physical causes" not in text
    assert "does not establish or cause the eventual task outcome" not in text


def test_amendment_cannot_claim_old_outputs_were_rescored(tmp_path):
    manifest = json.loads(MANIFEST.read_text())
    manifest["old_outputs_rescored"] = True
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="governance boundary"):
        audit(path)
