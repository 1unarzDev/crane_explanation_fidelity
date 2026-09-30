from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import audit_evidence_calibration_pilot_inventory_triage as triage  # noqa: E402
from audit_evidence_calibration_pilot_inventory_triage import audit  # noqa: E402


MANIFEST = ROOT / "manifests/annotation/evidence-calibration-pilot-inventory-triage-v1.json"
PREFIX_REVIEW = ROOT / "manifests/annotation/evidence-calibration-pilot-inventory-prefix-review-v1.json"


def test_proposed_repairs_are_bound_without_approving_inventory() -> None:
    result = audit()
    assert result["status"] == "PASS_BOUND_PROPOSED_REPAIRS_ONLY"
    assert result["review_forms"] == 17
    assert result["candidate_claims"] == 160
    assert result["proposed_claim_repairs"] == 3
    assert result["provisional_prefix_review_forms"] == 17
    assert result["support_annotation_authorized"] is False


def test_changed_repair_fails_closed(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["findings"][1]["proposed_claim_text_replacements"]["4"] = "The trace records two Nav2 failures."
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="bound proposed repairs changed"):
        audit(path)


def test_changed_blind_bank_response_fails_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    original = triage.load_declared_inputs

    def altered_inputs():
        declaration, entries, freeze_path, freeze, prompt, schema = original()
        entries = [dict(entry) for entry in entries]
        entries[0]["response_text"] += " Altered."
        return declaration, entries, freeze_path, freeze, prompt, schema

    monkeypatch.setattr(triage, "load_declared_inputs", altered_inputs)
    with pytest.raises(ValueError, match="blind response provenance changed"):
        audit()


def test_prefix_review_cannot_drop_a_retained_form(tmp_path: Path) -> None:
    review = json.loads(PREFIX_REVIEW.read_text(encoding="utf-8"))
    review["per_response_provisional_disposition"].pop()
    path = tmp_path / "incomplete-prefix.json"
    path.write_text(json.dumps(review), encoding="utf-8")
    with pytest.raises(ValueError, match="exact 17-form inventory"):
        audit(prefix_review_path=path)
