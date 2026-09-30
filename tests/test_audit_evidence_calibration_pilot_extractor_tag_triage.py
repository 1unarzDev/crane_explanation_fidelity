from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_extractor_tag_triage import audit  # noqa: E402


MANIFEST = ROOT / "manifests/annotation/evidence-calibration-pilot-extractor-tag-triage-v1.json"


def test_retained_deep_tag_triage_is_bound_but_not_qualified() -> None:
    result = audit()
    assert result["status"] == "PASS_BOUND_PRELIMINARY_TRIAGE_ONLY"
    assert result["deep_tagged_claims"] == 33
    assert result["preliminary_role_counts"]["explicit_non_entailment_or_limitation"] == 20
    assert result["support_annotation_authorized"] is False


def test_missing_cause_non_entailment_fails_closed(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    moved = manifest["preliminary_assertion_roles"]["explicit_non_entailment_or_limitation"].pop(4)
    manifest["preliminary_assertion_roles"]["visible_evidence_absence"].append(moved)
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="specific-cause tags"):
        audit(path)
