#!/usr/bin/env python3
"""Check deterministic emitted slots against the retained independent implementation.

This checks numeric fidelity and admitted motion claims, not natural-language
entailment. Full-answer blinded annotation remains a separate measurement.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    rows = []
    for namespace in ("evidence-calibration-b2-b4-development-v4", "evidence-calibration-development-extension-v4",
                      "evidence-calibration-b2-b4-development-v5", "evidence-calibration-development-extension-v5"):
        for path in sorted((ROOT / "model_outputs" / namespace / "b4").glob("*.json")):
            answer = json.loads(path.read_text())
            condition = answer["condition_id"]
            run, level = condition.rsplit("-E", 1)
            reference_path = ROOT / f"data/evaluator_only/dev/{run}/command-motion-independent-reference-v1.json"
            reference = json.loads(reference_path.read_text())
            assert reference["implementation_independence"]["imports_proposed_diagnostic_core"] is False
            result = reference["result"]
            claims = set(answer["diagnosis"]["approved_claim_ids"])
            expected = {"commanded_speed": result.get("discrepancy_commanded_planar_speed_mps"),
                        "measured_speed": result.get("discrepancy_measured_planar_speed_mps"),
                        "interval_start": (result.get("interval_s") or [None, None])[0],
                        "interval_end": (result.get("interval_s") or [None, None])[1]}
            errors = []
            for item in answer["plan"]["approved_numeric_values"]:
                if item["claim_id"] == "claim-command-motion-discrepancy":
                    want = expected[item["slot_id"]]
                    if want is None or not math.isclose(want, item["value"], abs_tol=1e-9):
                        errors.append(dict(slot=item["slot_id"], emitted=item["value"], independent=want))
            if "claim-command-motion-discrepancy" in claims:
                if level != "3" or result["disposition"] != "supported":
                    errors.append(dict(issue="unsupported discrepancy admission"))
            if "claim-measured-response-recovered" in claims:
                if level != "3" or result.get("response_recovery_interval_s") is None:
                    errors.append(dict(issue="unsupported measured recovery admission"))
            rows.append(dict(condition_id=condition, namespace=namespace, errors=errors,
                             numeric_slots_checked=len(answer["plan"]["approved_numeric_values"]),
                             independent_reference=str(reference_path.relative_to(ROOT))))
    output = ROOT / "manifests/analysis/evidence-calibration-handoff-b4-independent-fidelity-v1.json"
    report = dict(scope="DEVELOPMENT_ONLY", outputs=len(rows),
                  numeric_slots_checked=sum(r["numeric_slots_checked"] for r in rows),
                  mismatched_outputs=sum(bool(r["errors"]) for r in rows), rows=rows,
                  primary_failure_scored=False, human_validation_claimed=False)
    output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k != "rows"}))


if __name__ == "__main__": main()
