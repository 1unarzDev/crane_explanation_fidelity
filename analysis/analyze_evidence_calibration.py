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


def _response_failure(response: dict[str, Any], level_index: int) -> bool:
    unsupported_mechanism = any(
        item["mechanistic"] and
        (item["label"] in UNSUPPORTED_LABELS or item["required_minimum_level"] > level_index)
        for item in response["claims"]
    )
    overspecific = response["highest_asserted_rank"] is not None and \
        response["highest_asserted_rank"] > response["maximum_justified_rank"]
    return unsupported_mechanism or overspecific


def _validate(data: dict[str, Any], plan: dict[str, Any]) -> None:
    def nonnegative_int(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0

    def probability(value: Any) -> bool:
        return (isinstance(value, (int, float)) and not isinstance(value, bool)
                and math.isfinite(value) and 0 <= value <= 1)

    if data.get("schema") != INPUT_SCHEMA or plan.get("schema") != PLAN_SCHEMA:
        raise ValueError("unsupported analysis input or plan schema")
    if set(plan["methods"]) != {"B2", "B4"}:
        raise ValueError("primary paired methods must be B2 and B4")
    family_roles = ("primary_families", "control_families", "secondary_families")
    declared_families = []
    for role in family_roles:
        families = plan.get(role)
        if not isinstance(families, list) or any(not isinstance(item, str) or not item for item in families):
            raise ValueError(f"{role} must list named mechanism families")
        declared_families.extend(families)
    if not plan["primary_families"] or len(declared_families) != len(set(declared_families)):
        raise ValueError("primary families must be nonempty and family roles disjoint")
    if plan.get("clustered_model") != "LOGISTIC_CLUSTER_ROBUST_EPISODE":
        raise ValueError("clustered response model must be frozen explicitly")
    if not probability(plan["coverage_floor"]) or not probability(plan["alpha"]) or not 0 < plan["alpha"] < 1:
        raise ValueError("coverage floor or alpha is invalid")
    if (not probability(plan["minimum_practically_meaningful_reduction"])
            or not nonnegative_int(plan["bootstrap_replicates"])
            or plan["bootstrap_replicates"] == 0
            or not nonnegative_int(plan["bootstrap_seed"])):
        raise ValueError("analysis effect or bootstrap settings are invalid")
    episode_ids = [item["episode_id"] for item in data["episodes"]]
    if any(not isinstance(item, str) or not item for item in episode_ids) or len(episode_ids) != len(set(episode_ids)):
        raise ValueError("episode IDs must be unique independent clusters")
    for episode in data["episodes"]:
        if episode.get("mechanism_family") not in declared_families:
            raise ValueError("episode mechanism family has no declared analysis role")
        if not episode["conditions"]:
            raise ValueError("an independent episode needs at least one condition")
        condition_ids = [item["condition_id"] for item in episode["conditions"]]
        if (any(not isinstance(item, str) or not item for item in condition_ids)
                or len(condition_ids) != len(set(condition_ids))):
            raise ValueError("condition IDs must be unique within episode")
        levels = [item["level_index"] for item in episode["conditions"]]
        if (any(not nonnegative_int(level) for level in levels)
                or levels != sorted(levels) or len(levels) != len(set(levels))):
            raise ValueError("evidence conditions must have distinct ordered ladder levels")
        for condition in episode["conditions"]:
            if not isinstance(condition["evidence_insufficient"], bool) or not isinstance(condition["false_premise"], bool):
                raise ValueError("condition evidence and false-premise flags must be boolean")
            if set(condition["methods"]) != {"B2", "B4"}:
                raise ValueError("every condition needs a paired B2/B4 result")
            for response in condition["methods"].values():
                emitted, available = response["supported_required_emitted"], response["supported_required_available"]
                if not nonnegative_int(emitted) or not nonnegative_int(available) or emitted > available:
                    raise ValueError("supported required counts must be nonnegative and emission cannot exceed availability")
                if not isinstance(response["false_premise_rejected"], bool):
                    raise ValueError("false-premise rejection must be boolean")
                maximum, asserted = response["maximum_justified_rank"], response["highest_asserted_rank"]
                if not nonnegative_int(maximum) or (asserted is not None and not nonnegative_int(asserted)):
                    raise ValueError("diagnostic abstraction ranks must be nonnegative integers or null assertion")
                claim_ids = [claim["claim_id"] for claim in response["claims"]]
                if (any(not isinstance(item, str) or not item for item in claim_ids)
                        or len(claim_ids) != len(set(claim_ids))):
                    raise ValueError("atomic claim IDs must be nonempty and unique within a response")
                for claim in response["claims"]:
                    if not isinstance(claim["mechanistic"], bool):
                        raise ValueError("mechanistic claim flag must be an adjudicated boolean")
                    minimum = claim["required_minimum_level"]
                    if minimum is not None and not nonnegative_int(minimum):
                        raise ValueError("required minimum evidence level must be a nonnegative integer or null")
                    if claim["mechanistic"] and minimum is None:
                        raise ValueError("mechanistic claim needs a required minimum evidence level")
                    if claim["label"] not in UNSUPPORTED_LABELS | {"SUPPORTED_BY_VISIBLE_EVIDENCE", "UNINTERPRETABLE"}:
                        raise ValueError("unknown adjudicated claim label")
                    if claim["label"] == "UNINTERPRETABLE":
                        raise ValueError("UNINTERPRETABLE has no prospectively bound endpoint mapping")
            b2, b4 = condition["methods"]["B2"], condition["methods"]["B4"]
            if (b2["maximum_justified_rank"] != b4["maximum_justified_rank"]
                    or b2["supported_required_available"] != b4["supported_required_available"]):
                raise ValueError("paired methods must share the same evaluator reference for a condition")


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
                rows.append((cluster_index, float(_response_failure(condition["methods"][method],
                                                                   condition["level_index"])),
                             [1.0, treatment, level, treatment * level]))
    names = ["intercept", "method_B4", "evidence_level_centered", "B4_by_evidence_level"]
    if len({item[0] for item in rows}) <= len(names):
        return {"status": "INSUFFICIENT_EPISODE_CLUSTERS", "coefficient_names": names,
                "episode_clusters": len({item[0] for item in rows}), "observation_count": len(rows)}
    clusters = np.asarray([item[0] for item in rows])
    y = np.asarray([item[1] for item in rows])
    x = np.asarray([item[2] for item in rows], dtype=float)
    rank = int(np.linalg.matrix_rank(x))
    if rank < x.shape[1]:
        return {"status": "RANK_DEFICIENT_DESIGN", "coefficient_names": names,
                "design_rank": rank, "required_rank": x.shape[1],
                "episode_clusters": len(set(clusters)), "observation_count": len(rows)}
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
    claims_with_levels = [(claim, condition["level_index"])
                          for condition in episode["conditions"]
                          for claim in condition["methods"][method]["claims"]]
    mechanistic = [(claim, level) for claim, level in claims_with_levels if claim["mechanistic"]]
    unsupported = [(claim, level) for claim, level in mechanistic
                   if claim["label"] in UNSUPPORTED_LABELS or claim["required_minimum_level"] > level]
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
        not _response_failure(item["methods"][method], item["level_index"]) and
        item["methods"][method]["supported_required_emitted"] > 0 for item in insufficient
    )
    over_abstention = sum(
        item["methods"][method]["supported_required_emitted"] <
        item["methods"][method]["supported_required_available"] for item in sufficient
    )
    false_premise = [item for item in episode["conditions"] if item["false_premise"]]
    return {
        "episode_id": episode["episode_id"],
        "primary_failure": any(_response_failure(item["methods"][method], item["level_index"])
                               for item in episode["conditions"]),
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
    primary = [episode for episode in data["episodes"]
               if episode["mechanism_family"] in plan["primary_families"]]
    if not primary:
        raise ValueError("primary comparison has no independent episodes")
    summaries = {
        method: [_episode_summary(episode, method) for episode in primary]
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
    nonprimary = {}
    for role in ("control_families", "secondary_families"):
        for family in plan[role]:
            episodes = [episode for episode in data["episodes"] if episode["mechanism_family"] == family]
            nonprimary[family] = {
                "role": role.removesuffix("_families"),
                "independent_episode_count": len(episodes),
                "B2_episode_failures": sum(_episode_summary(episode, "B2")["primary_failure"] for episode in episodes),
                "B4_episode_failures": sum(_episode_summary(episode, "B4")["primary_failure"] for episode in episodes),
            }
    return {
        "schema": OUTPUT_SCHEMA, "input_sha256": canonical_sha256(data),
        "analysis_plan_sha256": canonical_sha256(plan), "independent_unit": "episode_configuration",
        "independent_episode_count": n,
        "total_independent_episode_count": len(data["episodes"]),
        "primary_families": plan["primary_families"],
        "primary_family_counts": {family: sum(episode["mechanism_family"] == family for episode in primary)
                                  for family in plan["primary_families"]},
        "primary_family_weighting": "OBSERVED_EPISODE_MIX_DEVELOPMENT_ONLY",
        "nonprimary_family_descriptives": nonprimary,
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
        "clustered_response_model": _cluster_robust_logistic({"episodes": primary}),
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
