#!/usr/bin/env python3
"""Episode-clustered evidence-calibration metrics and paired B2/B4 inference."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import random
from typing import Any

import numpy as np

from evidence_calibration_io import canonical_json_bytes, canonical_sha256


INPUT_SCHEMA = "crane-evidence-calibration-adjudicated-results/v1"
PLAN_SCHEMA = "crane-evidence-calibration-analysis-plan/v1-development"
OUTPUT_SCHEMA = "crane-evidence-calibration-analysis/v1-development"
UNSUPPORTED_LABELS = {
    "CONTRADICTED_BY_VISIBLE_EVIDENCE",
    "INSUFFICIENT_VISIBLE_EVIDENCE",
    "PHYSICALLY_TRUE_BUT_UNSUPPORTED",
}


def exact_mcnemar_p(b2_only_failure: int, b4_only_failure: int) -> float:
    discordant = b2_only_failure + b4_only_failure
    if discordant == 0:
        return 1.0
    tail = min(b2_only_failure, b4_only_failure)
    probability = sum(math.comb(discordant, k) for k in range(tail + 1)) / (2 ** discordant)
    return min(1.0, 2 * probability)


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _response_failure(response: dict[str, Any]) -> bool:
    unsupported_mechanism = any(
        item["mechanistic"] and item["label"] in UNSUPPORTED_LABELS for item in response["claims"]
    )
    overspecific = response["highest_asserted_rank"] is not None and \
        response["highest_asserted_rank"] > response["maximum_justified_rank"]
    return unsupported_mechanism or overspecific


def _validate(data: dict[str, Any], plan: dict[str, Any]) -> None:
    if data.get("schema") != INPUT_SCHEMA or plan.get("schema") != PLAN_SCHEMA:
        raise ValueError("unsupported analysis input or plan schema")
    if set(plan["methods"]) != {"B2", "B4"}:
        raise ValueError("primary paired methods must be B2 and B4")
    if plan.get("clustered_model") != "LOGISTIC_CLUSTER_ROBUST_EPISODE":
        raise ValueError("clustered response model must be frozen explicitly")
    if not 0 <= plan["coverage_floor"] <= 1 or not 0 < plan["alpha"] < 1:
        raise ValueError("coverage floor or alpha is invalid")
    episode_ids = [item["episode_id"] for item in data["episodes"]]
    if len(episode_ids) != len(set(episode_ids)):
        raise ValueError("episode IDs must be unique independent clusters")
    for episode in data["episodes"]:
        condition_ids = [item["condition_id"] for item in episode["conditions"]]
        if len(condition_ids) != len(set(condition_ids)):
            raise ValueError("condition IDs must be unique within episode")
        levels = [item["level_index"] for item in episode["conditions"]]
        if levels != sorted(levels):
            raise ValueError("evidence conditions must follow registered ladder order")
        for condition in episode["conditions"]:
            if set(condition["methods"]) != {"B2", "B4"}:
                raise ValueError("every condition needs a paired B2/B4 result")
            for response in condition["methods"].values():
                if response["supported_required_emitted"] > response["supported_required_available"]:
                    raise ValueError("supported required emission cannot exceed availability")
                for claim in response["claims"]:
                    if claim["label"] not in UNSUPPORTED_LABELS | {"SUPPORTED_BY_VISIBLE_EVIDENCE", "UNINTERPRETABLE"}:
                        raise ValueError("unknown adjudicated claim label")


def _cluster_robust_logistic(data: dict[str, Any]) -> dict[str, Any]:
    """Fit logit(error) ~ method + level + method:level with episode sandwich SEs."""
    rows = []
    for cluster_index, episode in enumerate(data["episodes"]):
        levels = [item["level_index"] for item in episode["conditions"]]
        center = sum(levels) / len(levels)
        for condition in episode["conditions"]:
            level = condition["level_index"] - center
            for method in ("B2", "B4"):
                treatment = int(method == "B4")
                rows.append((cluster_index, float(_response_failure(condition["methods"][method])),
                             [1.0, treatment, level, treatment * level]))
    names = ["intercept", "method_B4", "evidence_level_centered", "B4_by_evidence_level"]
    if len({item[0] for item in rows}) <= len(names):
        return {"status": "INSUFFICIENT_EPISODE_CLUSTERS", "coefficient_names": names,
                "episode_clusters": len({item[0] for item in rows}), "observation_count": len(rows)}
    clusters = np.asarray([item[0] for item in rows])
    y = np.asarray([item[1] for item in rows])
    x = np.asarray([item[2] for item in rows], dtype=float)
    beta = np.zeros(x.shape[1])
    converged = False
    for _ in range(100):
        eta = np.clip(x @ beta, -30, 30)
        probability = 1 / (1 + np.exp(-eta))
        weights = np.maximum(probability * (1 - probability), 1e-9)
        information = x.T @ (weights[:, None] * x)
        step = np.linalg.pinv(information) @ (x.T @ (y - probability))
        beta += step
        if np.max(np.abs(step)) < 1e-8:
            converged = True
            break
        if np.max(np.abs(beta)) > 50:
            break
    if not converged:
        return {"status": "NONCONVERGED_OR_SEPARATED", "coefficient_names": names,
                "episode_clusters": len(set(clusters)), "observation_count": len(rows)}
    eta = np.clip(x @ beta, -30, 30)
    probability = 1 / (1 + np.exp(-eta))
    weights = np.maximum(probability * (1 - probability), 1e-9)
    bread = np.linalg.pinv(x.T @ (weights[:, None] * x))
    meat = np.zeros((x.shape[1], x.shape[1]))
    for cluster in np.unique(clusters):
        selected = clusters == cluster
        score = x[selected].T @ (y[selected] - probability[selected])
        meat += np.outer(score, score)
    cluster_count, observation_count, parameter_count = len(np.unique(clusters)), len(y), x.shape[1]
    correction = (cluster_count / (cluster_count - 1)) * \
        ((observation_count - 1) / (observation_count - parameter_count))
    covariance = correction * bread @ meat @ bread
    standard_errors = np.sqrt(np.maximum(np.diag(covariance), 0))
    return {
        "status": "FIT", "model": "logistic_cluster_robust_episode",
        "formula": "calibration_error ~ method_B4 + evidence_level_centered + method_B4:evidence_level_centered",
        "episode_clusters": cluster_count, "observation_count": observation_count,
        "coefficients": [
            {"term": name, "log_odds": float(coefficient), "cluster_robust_standard_error": float(error)}
            for name, coefficient, error in zip(names, beta, standard_errors)
        ],
    }


def _episode_summary(episode: dict[str, Any], method: str) -> dict[str, Any]:
    conditions = [item["methods"][method] for item in episode["conditions"]]
    claims = [claim for response in conditions for claim in response["claims"]]
    mechanistic = [claim for claim in claims if claim["mechanistic"]]
    unsupported = [claim for claim in mechanistic if claim["label"] in UNSUPPORTED_LABELS]
    emitted = sum(item["supported_required_emitted"] for item in conditions)
    available = sum(item["supported_required_available"] for item in conditions)
    monotonicity = 0
    for condition in episode["conditions"]:
        level = condition["level_index"]
        monotonicity += sum(
            claim["required_minimum_level"] > level
            for claim in condition["methods"][method]["claims"] if claim["mechanistic"]
        )
    insufficient = [item for item in episode["conditions"] if item["evidence_insufficient"]]
    sufficient = [item for item in episode["conditions"] if not item["evidence_insufficient"]]
    appropriate = sum(
        not _response_failure(item["methods"][method]) and
        item["methods"][method]["supported_required_emitted"] > 0 for item in insufficient
    )
    over_abstention = sum(
        item["methods"][method]["supported_required_emitted"] <
        item["methods"][method]["supported_required_available"] for item in sufficient
    )
    false_premise = [item for item in episode["conditions"] if item["false_premise"]]
    return {
        "episode_id": episode["episode_id"],
        "primary_failure": any(_response_failure(item) for item in conditions),
        "unsupported_mechanistic_claims": len(unsupported),
        "mechanistic_claims_emitted": len(mechanistic),
        "supported_required_emitted": emitted, "supported_required_available": available,
        "eca_correct_conditions": sum(
            item["highest_asserted_rank"] == item["maximum_justified_rank"] for item in conditions
        ),
        "condition_count": len(conditions), "monotonicity_violations": monotonicity,
        "insufficient_condition_count": len(insufficient), "appropriate_abstentions": appropriate,
        "sufficient_condition_count": len(sufficient), "over_abstentions": over_abstention,
        "false_premise_count": len(false_premise),
        "false_premise_rejections": sum(item["methods"][method]["false_premise_rejected"]
                                        for item in false_premise),
    }


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def analyze(data: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    _validate(data, plan)
    summaries = {
        method: [_episode_summary(episode, method) for episode in data["episodes"]]
        for method in ("B2", "B4")
    }
    pairs = list(zip(summaries["B2"], summaries["B4"]))
    counts = Counter((left["primary_failure"], right["primary_failure"]) for left, right in pairs)
    n = len(pairs)
    b2_failures = sum(left["primary_failure"] for left, _ in pairs)
    b4_failures = sum(right["primary_failure"] for _, right in pairs)
    difference = (b4_failures - b2_failures) / n if n else None
    rng = random.Random(plan["bootstrap_seed"])
    bootstrap = []
    if n:
        for _ in range(plan["bootstrap_replicates"]):
            sample = [pairs[rng.randrange(n)] for _ in range(n)]
            bootstrap.append((sum(right["primary_failure"] for _, right in sample) -
                              sum(left["primary_failure"] for left, _ in sample)) / n)
    method_metrics = {}
    for method, rows in summaries.items():
        totals = Counter()
        for row in rows:
            for key, value in row.items():
                if key != "episode_id" and isinstance(value, (int, bool)):
                    totals[key] += value
        coverage = _ratio(totals["supported_required_emitted"], totals["supported_required_available"])
        method_metrics[method] = {
            "episodes": n,
            "primary_failures": totals["primary_failure"],
            "primary_failure_rate": _ratio(totals["primary_failure"], n),
            "usr_numerator": totals["unsupported_mechanistic_claims"],
            "usr_denominator": totals["mechanistic_claims_emitted"],
            "unsupported_specificity_rate": _ratio(totals["unsupported_mechanistic_claims"], totals["mechanistic_claims_emitted"]),
            "sdr_numerator": totals["supported_required_emitted"],
            "sdr_denominator": totals["supported_required_available"],
            "supported_diagnostic_recall": coverage,
            "eca_numerator": totals["eca_correct_conditions"], "eca_denominator": totals["condition_count"],
            "evidence_calibration_accuracy": _ratio(totals["eca_correct_conditions"], totals["condition_count"]),
            "emvr_numerator": totals["monotonicity_violations"], "emvr_denominator": totals["mechanistic_claims_emitted"],
            "evidence_monotonicity_violation_rate": _ratio(totals["monotonicity_violations"], totals["mechanistic_claims_emitted"]),
            "appropriate_abstention_numerator": totals["appropriate_abstentions"],
            "appropriate_abstention_denominator": totals["insufficient_condition_count"],
            "appropriate_abstention_rate": _ratio(totals["appropriate_abstentions"], totals["insufficient_condition_count"]),
            "over_abstention_numerator": totals["over_abstentions"],
            "over_abstention_denominator": totals["sufficient_condition_count"],
            "over_abstention_rate": _ratio(totals["over_abstentions"], totals["sufficient_condition_count"]),
            "false_premise_rejection_numerator": totals["false_premise_rejections"],
            "false_premise_rejection_denominator": totals["false_premise_count"],
            "false_premise_rejection_rate": _ratio(totals["false_premise_rejections"], totals["false_premise_count"]),
            "coverage_floor": plan["coverage_floor"],
            "coverage_floor_met": coverage is not None and coverage >= plan["coverage_floor"],
        }
    ci = None if not bootstrap else [
        _percentile(bootstrap, plan["alpha"] / 2), _percentile(bootstrap, 1 - plan["alpha"] / 2)
    ]
    return {
        "schema": OUTPUT_SCHEMA, "input_sha256": canonical_sha256(data),
        "analysis_plan_sha256": canonical_sha256(plan), "independent_unit": "episode_configuration",
        "independent_episode_count": n,
        "within_episode_repeated_observations": ["evidence_conditions", "methods", "claims", "annotations"],
        "paired_primary": {
            "neither_failure": counts[(False, False)], "b2_only_failure": counts[(True, False)],
            "b4_only_failure": counts[(False, True)], "both_failure": counts[(True, True)],
            "b4_minus_b2_risk_difference": difference,
            "whole_episode_bootstrap_confidence_interval": ci,
            "bootstrap_replicates": plan["bootstrap_replicates"],
            "exact_mcnemar_two_sided_p": exact_mcnemar_p(counts[(True, False)], counts[(False, True)]),
            "minimum_practically_meaningful_reduction": plan["minimum_practically_meaningful_reduction"],
        },
        "method_metrics": method_metrics,
        "episode_summaries": summaries,
        "secondary_multiplicity": "HOLM_PREDECLARED_FAMILIES_REQUIRED_AT_FREEZE",
        "clustered_response_model": _cluster_robust_logistic(data),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = analyze(json.loads(args.results.read_text()), json.loads(args.plan.read_text()))
    args.output.write_bytes(canonical_json_bytes(output) + b"\n")


if __name__ == "__main__":
    main()
