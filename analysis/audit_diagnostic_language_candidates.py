#!/usr/bin/env python3
"""Post-hoc development audit for the bounded diagnostic-language verifier."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from crane_explain.diagnostic_language import verify_bounded_diagnostic_text
from crane_explain.diagnostics import (
    CausalLanguageLevel,
    DiagnosticDisposition,
    DiagnosticMeasurement,
    DiagnosticResult,
)


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def result_from_dict(value: dict) -> DiagnosticResult:
    return DiagnosticResult(
        schema_version=value["schema_version"],
        diagnostic_id=value["diagnostic_id"],
        episode_id=value["episode_id"],
        mechanism=value["mechanism"],
        disposition=DiagnosticDisposition(value["disposition"]),
        diagnosis=value["diagnosis"],
        measurements=tuple(DiagnosticMeasurement(**item) for item in value["measurements"]),
        computation=value["computation"],
        computation_version=value["computation_version"],
        assumptions=tuple(value["assumptions"]),
        supporting_evidence=tuple(value["supporting_evidence"]),
        contradictory_evidence=tuple(value["contradictory_evidence"]),
        unresolved_alternatives=tuple(value["unresolved_alternatives"]),
        causal_language_level=CausalLanguageLevel(value["causal_language_level"]),
        failure_chain=value["failure_chain"],
        limits=value["limits"],
        next_check=value["next_check"],
        source_anchor_ids=tuple(value["source_anchor_ids"]),
        decisive_measurement_ids=tuple(value.get("decisive_measurement_ids", ())),
    )


def p_candidate(model_output: dict) -> str:
    matches = [item for item in model_output["outputs"] if item["condition"] == "P"]
    if len(matches) != 1 or not matches[0].get("raw_candidate"):
        raise ValueError("expected exactly one P raw_candidate")
    return matches[0]["raw_candidate"]


def mutations(candidate: str) -> dict[str, str]:
    return {
        "append_unlicensed_wave_cause": candidate + "\n\nWave drift caused the failure.",
        "append_unlicensed_numeric_claim": candidate.replace(
            "## Limits and next check",
            "The platform moved 999.999 m.\n\n## Limits and next check",
            1,
        ),
        "remove_limits_section": candidate.split("## Limits and next check", 1)[0],
    }


def audit(config_path: Path) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    cases = []
    mutation_total = 0
    mutation_rejections = 0
    for item in config["cases"]:
        diagnostic_path = ROOT / item["diagnostic"]
        output_path = ROOT / item["model_output"]
        diagnostic_export = json.loads(diagnostic_path.read_text(encoding="utf-8"))
        output = json.loads(output_path.read_text(encoding="utf-8"))
        result = result_from_dict(diagnostic_export["diagnostic_result"])
        candidate = p_candidate(output)
        verification = verify_bounded_diagnostic_text(result, candidate)
        mutation_results = {}
        for name, changed in mutations(candidate).items():
            checked = verify_bounded_diagnostic_text(result, changed)
            mutation_total += 1
            mutation_rejections += int(not checked.accepted)
            mutation_results[name] = {
                "accepted": checked.accepted,
                "reasons": list(checked.reasons),
            }
        cases.append(
            {
                "case_id": item["case_id"],
                "diagnostic_path": item["diagnostic"],
                "diagnostic_sha256": sha256(diagnostic_path),
                "model_output_path": item["model_output"],
                "model_output_sha256": sha256(output_path),
                "raw_candidate_sha256": hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
                "original_exact_verification_accepted": False,
                "bounded_verification": {
                    "accepted": verification.accepted,
                    "repair_applied": verification.repair_applied,
                    "reasons": list(verification.reasons),
                    "checked_text_sha256": hashlib.sha256(
                        verification.checked_text.encode("utf-8")
                    ).hexdigest(),
                },
                "adversarial_mutations": mutation_results,
            }
        )
    return {
        "schema": "crane-diagnostic-language-verifier-development-audit-v1",
        "status": "POST_HOC_DEVELOPMENT_ONLY_NOT_AN_INDEPENDENT_EVALUATION",
        "config_path": str(config_path.relative_to(ROOT)),
        "config_sha256": sha256(config_path),
        "case_count": len(cases),
        "bounded_candidate_acceptance_count": sum(
            int(item["bounded_verification"]["accepted"]) for item in cases
        ),
        "evidence_id_repair_count": sum(
            int(item["bounded_verification"]["repair_applied"]) for item in cases
        ),
        "adversarial_mutation_count": mutation_total,
        "adversarial_mutation_rejection_count": mutation_rejections,
        "cases": cases,
        "limitations": [
            "The verifier and audit were authored after inspecting these development candidates.",
            "Mutation rejection is a regression check, not an estimate of verifier false-positive or false-negative rates.",
            "Human annotation and an independently constructed held-out verifier evaluation remain NOT_RUN.",
            "Immutable original outputs and their original exact-verification fallback decisions are unchanged."
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "diagnostic_language_verifier_dev_v1.json",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.config.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
