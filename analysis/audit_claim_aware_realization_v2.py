#!/usr/bin/env python3
"""Audit the finite-number repair's exact prospective source diff and closed execution scope."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests/study/evidence-calibration-realizer-finite-numbers-v2-development.json"


def audit(path: Path = MANIFEST) -> dict:
    manifest = json.loads(path.read_text())
    if (manifest.get("schema") != "crane-claim-realizer-finite-number-amendment/v1-development"
            or manifest.get("status") != "PROSPECTIVE_DEVELOPMENT_REPAIR_NOT_EXECUTION_FROZEN"
            or any(manifest.get(key) is not False for key in
                   ("old_realizer_changed", "old_outputs_rescored", "model_calls_authorized",
                    "pilot_annotation_authorized", "p11_authorized", "new_version_used_in_pilot"))):
        raise ValueError("finite-number repair governance boundary changed")
    expected_paths = {
        "old_realizer": "analysis/realize_evidence_calibrated_explanation.py",
        "new_realizer": "analysis/realize_evidence_calibrated_explanation_v2.py",
        "audit": "analysis/audit_claim_aware_realization_v2.py",
        "tests": "tests/test_claim_aware_realization_v2.py",
        "synthetic_fixtures": "tests/test_claim_aware_realization.py",
        "note": "docs/REALIZER_FINITE_NUMBER_REPAIR_2026-09-30.md",
        "failed_measurement_gate": "manifests/operations/evidence-calibration-combined-support-canary-disposition-v1.json",
    }
    bindings = manifest.get("bindings")
    if not isinstance(bindings, dict) or set(bindings) != set(expected_paths):
        raise ValueError("finite-number repair bindings incomplete")
    for key, relative in expected_paths.items():
        item = bindings[key]
        if (item.get("path") != relative or item.get("raw_sha256")
                != hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()):
            raise ValueError("finite-number repair component hash mismatch")
    old = (ROOT / expected_paths["old_realizer"]).read_text()
    new = (ROOT / expected_paths["new_realizer"]).read_text()
    numeric_check = '                        isinstance(supplied[slot_id]["value"], bool) or \\\n'
    replacements = [
        ("import json\n", "import json\nimport math\n"),
        ('REALIZER_VERSION = "v1-development"', 'REALIZER_VERSION = "v2-development-finite-numbers"'),
        (numeric_check, numeric_check + '                        (isinstance(supplied[slot_id]["value"], float) and \\\n                         not math.isfinite(supplied[slot_id]["value"])) or \\\n'),
    ]
    expected = old
    for before, after in replacements:
        if expected.count(before) != 1:
            raise ValueError("finite-number repair source seam changed")
        expected = expected.replace(before, after, 1)
    if new != expected:
        raise ValueError("new realizer changes behavior beyond the exact finite-number repair")
    return {"schema": "crane-claim-realizer-finite-number-audit/v1-development",
            "status": "PASS_EXACT_PROSPECTIVE_REPAIR_ONLY", "source_changes": 3,
            "old_realizer_changed": False, "old_outputs_rescored": False,
            "model_calls_authorized": False, "new_version_used_in_pilot": False, "p11_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
