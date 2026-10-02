"""Development local repair: lack of causal evidence does not exclude causation.

Preserves v3, its ontology, and every retained answer. Applies a separately versioned
ontology wording correction before deterministic realization and local verification.
"""
import copy
import json
from pathlib import Path
from realize_evidence_calibrated_explanation_v3 import realize as realize_v3
from evidence_calibration_io import canonical_sha256

VERSION = "v4-development-causal-limitation"
RELATION = "ne-response-recovery-does-not-establish-task-outcome"
LIMITATION = "Measured response recovery alone does not establish the eventual task outcome or whether it caused that outcome."


def realize(ontology, entry, question_contract):
    corrected = copy.deepcopy(ontology)
    matches = [r for r in corrected["non_entailments"] if r["non_entailment_id"] == RELATION]
    if len(matches) != 1:
        raise ValueError("Expected unique measured-recovery non-entailment")
    matches[0]["rationale"] = LIMITATION
    result = realize_v3(corrected, entry, question_contract)
    result.update(version=VERSION, schema="crane-evidence-calibration-b4-development-output/v4",
                  ontology_sha256=canonical_sha256(corrected),
                  development_change="Local causal limitation repair; no denial of causal contribution")
    return result


def generate(pilot_path, validation_path, namespace):
    from run_evidence_calibration_b2_pilot import ROOT, _materialize
    pilot = json.loads(pilot_path.read_text())
    schedule = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json").read_text())
    validation = json.loads(validation_path.read_text())
    ontology = json.loads((ROOT / "configs/evidence_calibration_claim_contracts_v1.json").read_text())
    output = ROOT / "model_outputs" / namespace / "b4"
    output.mkdir(parents=True, exist_ok=True)
    for episode in validation["episodes"]:
        for condition in episode["condition_ids"]:
            entry, _, family = _materialize(ROOT, pilot, schedule, condition)
            result = realize(ontology, entry, dict(question_id=family+"-question-v1-development",
                      failure_premise=True, required_mechanism_families=["false_premise"]
                      if family == "nominal_false_premise" else ["command_motion"]))
            result["family"] = family
            path = output / (condition+".json")
            raw = json.dumps(result, indent=2, sort_keys=True)+"\n"
            if path.exists() and path.read_text() != raw: raise RuntimeError("Retained v4 output differs")
            if not path.exists(): path.write_text(raw)
    return len(list(output.glob("*.json")))


if __name__ == "__main__":
    from run_evidence_calibration_b2_pilot import ROOT
    n = generate(ROOT/"research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json",
                 ROOT/"manifests/study/evidence-calibration-b2-b4-pilot-v1-input-validation.json",
                 "evidence-calibration-b2-b4-development-v4")
    n += generate(ROOT/"analysis/results/development/evidence-calibration-extension-v1/pilot.json",
                  ROOT/"analysis/results/development/evidence-calibration-extension-v1/input-validation.json",
                  "evidence-calibration-development-extension-v4")
    print(json.dumps(dict(development_outputs=n, model_calls=0)))
