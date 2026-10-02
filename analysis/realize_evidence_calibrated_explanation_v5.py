"""Development coverage repair: describe delivered commands, beyond stream presence."""
import json
import math
import statistics
from realize_evidence_calibrated_explanation_v4 import realize as previous

VERSION = "v5-development-command-observation"


def realize(ontology, entry, question_contract):
    output = previous(ontology, entry, question_contract)
    samples = entry["method_packet"]["evidence"].get("delivered_command_stream", {}).get("samples", [])
    if samples and all(type(s.get(k)) in (float, int) and math.isfinite(s[k])
                       for s in samples for k in ("offset_s", "planar_speed_mps")):
        median = statistics.median(s["planar_speed_mps"] for s in samples)
        lower = min(s["offset_s"] for s in samples)
        upper = max(s["offset_s"] for s in samples)
        clause = dict(clause_id="delivered-command-observation", kind="PACKET_DERIVED",
                      contract_id="delivered-command-observation",
                      support_references=["delivered-command-stream"],
                      text=f"The stream records {len(samples)} delivered command samples from {lower:.12g} to {upper:.12g} s, with median commanded planar speed {median:.12g} m/s.")
        output["clauses"].append(clause)
        output["answer"] = " ".join(c["text"] for c in output["clauses"])
    output.update(version=VERSION, schema="crane-evidence-calibration-b4-development-output/v5",
                  development_change="Local command observation coverage repair after causal limitation repair")
    return output


if __name__ == "__main__":
    from pathlib import Path
    from run_evidence_calibration_b2_pilot import ROOT, _materialize
    ontology = json.loads((ROOT/"configs/evidence_calibration_claim_contracts_v1.json").read_text())
    schedule = json.loads((ROOT/"research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json").read_text())
    count = 0
    groups = [(ROOT/"research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json",
               ROOT/"manifests/study/evidence-calibration-b2-b4-pilot-v1-input-validation.json", "evidence-calibration-b2-b4-development-v5"),
              (ROOT/"analysis/results/development/evidence-calibration-extension-v1/pilot.json",
               ROOT/"analysis/results/development/evidence-calibration-extension-v1/input-validation.json", "evidence-calibration-development-extension-v5")]
    for pilot_path, validation_path, namespace in groups:
        pilot = json.loads(pilot_path.read_text())
        validation = json.loads(validation_path.read_text())
        out = ROOT/"model_outputs"/namespace/"b4"
        out.mkdir(parents=True, exist_ok=True)
        for episode in validation["episodes"]:
            for condition in episode["condition_ids"]:
                entry, _, family = _materialize(ROOT,pilot,schedule,condition)
                output = realize(ontology,entry,dict(question_id=family+"-question-v1-development", failure_premise=True,
                    required_mechanism_families=["false_premise"] if family=="nominal_false_premise" else ["command_motion"]))
                output["family"] = family
                path = out/(condition+".json"); raw = json.dumps(output,indent=2,sort_keys=True)+"\n"
                if path.exists() and path.read_text()!=raw: raise RuntimeError("Existing v5 answer differs")
                if not path.exists(): path.write_text(raw)
                count += 1
    print(json.dumps(dict(development_outputs=count,model_calls=0)))
