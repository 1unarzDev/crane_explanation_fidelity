#!/usr/bin/env python3
"""Anytime-valid monitoring for prospective diagnostic-study campaigns.

The monitor operates on one outcome row per independent scenario cluster.  It is deliberately
inapplicable to the legacy cohort and to diagnostic-development episodes whose outputs have already
been inspected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/prospective/"
    "diagnostic-sequential-protocol-v2.json"
)
DEFAULT_LEDGER = ROOT / "manifests/study/diagnostic-sequential-error-ledger-v2.json"


def _require_probability(value: Any, label: str) -> float:
    result = float(value)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{label} must be in [0, 1]")
    return result


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def paired_difference(proposed: Any, baseline: Any, label: str) -> float:
    return _require_probability(proposed, f"{label}.proposed") - _require_probability(
        baseline, f"{label}.baseline"
    )


def log_mixture_e_value(
    observations: Iterable[float],
    null_mean: float,
    bet_fractions: Iterable[float],
) -> float:
    """Log e-value for H0: conditional mean <= null_mean.

    For X in [-1, 1], null mean m > -1, and fixed fraction c in (0, 1), use
    lambda_c(m) = c / (1 + m).  Then every factor
    1 + lambda_c(m) * (X - m) is positive and has conditional expectation at most one
    under E[X_t | F_{t-1}] <= m.  A fixed mixture over c is also a supermartingale.
    """

    values = tuple(float(item) for item in observations)
    if not -1.0 <= null_mean <= 1.0:
        raise ValueError("null_mean must be in [-1, 1]")
    fractions = tuple(float(item) for item in bet_fractions)
    if not fractions or any(not 0.0 < item < 1.0 for item in fractions):
        raise ValueError("bet fractions must be a nonempty fixed set in (0, 1)")
    if any(not -1.0 <= item <= 1.0 for item in values):
        raise ValueError("observations must be in [-1, 1]")
    if null_mean == -1.0:
        return 0.0 if all(item == -1.0 for item in values) else math.inf

    components = []
    for fraction in fractions:
        bet = fraction / (1.0 + null_mean)
        total = 0.0
        for value in values:
            factor = 1.0 + bet * (value - null_mean)
            if factor < 0.0:
                raise AssertionError("nonnegative betting factor violated")
            if factor == 0.0:
                total = -math.inf
                break
            total += math.log(factor)
        components.append(total)
    maximum = max(components)
    if maximum == -math.inf:
        return -math.inf
    return maximum + math.log(
        sum(math.exp(item - maximum) for item in components) / len(components)
    )


def lower_confidence_bound(
    observations: Iterable[float], alpha: float, bet_fractions: Iterable[float]
) -> float:
    """Invert the monotone e-process to obtain an anytime-valid one-sided lower bound."""

    values = tuple(observations)
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    threshold = math.log(1.0 / alpha)
    if log_mixture_e_value(values, -1.0, bet_fractions) < threshold:
        return -1.0
    if log_mixture_e_value(values, 1.0, bet_fractions) >= threshold:
        return 1.0
    low, high = -1.0, 1.0
    for _ in range(80):
        middle = (low + high) / 2.0
        if log_mixture_e_value(values, middle, bet_fractions) >= threshold:
            low = middle
        else:
            high = middle
    return low


def upper_confidence_bound(
    observations: Iterable[float], alpha: float, bet_fractions: Iterable[float]
) -> float:
    return -lower_confidence_bound(
        (-float(item) for item in observations), alpha, bet_fractions
    )


def _endpoint(
    values: list[float],
    threshold: float,
    direction: str,
    alpha: float,
    bet_fractions: tuple[float, ...],
) -> dict[str, Any]:
    estimate = sum(values) / len(values) if values else None
    if not values:
        return {
            "n": 0,
            "estimate": None,
            "threshold": threshold,
            "direction": direction,
            "bound": None,
            "e_value": None,
            "passed": False,
        }
    if direction == "lower":
        bound = lower_confidence_bound(values, alpha, bet_fractions)
        log_e = log_mixture_e_value(values, threshold, bet_fractions)
        passed = bound > threshold
    elif direction == "upper":
        bound = upper_confidence_bound(values, alpha, bet_fractions)
        log_e = log_mixture_e_value(
            (-item for item in values), -threshold, bet_fractions
        )
        passed = bound < threshold
    else:
        raise ValueError(f"unsupported direction: {direction}")
    return {
        "n": len(values),
        "estimate": estimate,
        "threshold": threshold,
        "direction": direction,
        "bound": bound,
        "e_value": math.exp(log_e) if log_e < 700 else "overflow_gt_exp_700",
        "log_e_value": log_e,
        "passed": passed,
    }


def validate_protocol(protocol: dict[str, Any]) -> None:
    if protocol.get("schema") != "crane-diagnostic-sequential-protocol/v2":
        raise ValueError("unsupported sequential protocol")
    ledger = protocol["error_budget_ledger"]
    program_alpha = float(ledger["program_alpha"])
    if not 0.0 < program_alpha < 1.0:
        raise ValueError("program alpha must be in (0, 1)")
    total = sum(float(item["alpha"]) for item in ledger["allocations"])
    if total > program_alpha + 1e-12:
        raise ValueError("alpha ledger exceeds program alpha")
    if len({item["allocation_id"] for item in ledger["allocations"]}) != len(
        ledger["allocations"]
    ):
        raise ValueError("duplicate alpha allocation ID")
    for item in ledger["allocations"]:
        if not 0.0 < float(item["alpha"]) < 1.0:
            raise ValueError("every alpha allocation must be in (0, 1)")
        if item["role"] not in {"candidate", "replication"}:
            raise ValueError("unknown alpha-allocation role")
        if item["status"] != "AVAILABLE":
            raise ValueError("immutable protocol allocations must retain initial AVAILABLE status")
    probabilities = protocol["target_distribution"]["strata"]
    stratum_ids = [item["stratum_id"] for item in probabilities]
    if len(stratum_ids) != len(set(stratum_ids)):
        raise ValueError("duplicate target scenario stratum")
    if any(not 0.0 < float(item["probability"]) <= 1.0 for item in probabilities):
        raise ValueError("target scenario probabilities must be positive")
    if not math.isclose(
        sum(float(item["probability"]) for item in probabilities), 1.0, abs_tol=1e-12
    ):
        raise ValueError("target scenario probabilities must sum to one")
    fractions = [float(item) for item in protocol["analysis"]["betting_fractions"]]
    if fractions != sorted(set(fractions)) or any(
        not 0.0 < item < 1.0 for item in fractions
    ):
        raise ValueError("bet fractions must be unique, increasing, and in (0, 1)")


def protocol_sha256(protocol: dict[str, Any]) -> str:
    canonical = json.dumps(protocol, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def validate_ledger(ledger: dict[str, Any], protocol: dict[str, Any]) -> None:
    if ledger.get("schema") != "crane-diagnostic-error-ledger/v1":
        raise ValueError("unsupported cumulative error ledger")
    if ledger.get("protocol_id") != protocol["protocol_id"]:
        raise ValueError("error ledger names a different protocol")
    if not math.isclose(
        float(ledger["program_alpha"]),
        float(protocol["error_budget_ledger"]["program_alpha"]),
        abs_tol=1e-12,
    ):
        raise ValueError("error-ledger program alpha differs from protocol")
    planned = {
        item["allocation_id"]: (item["role"], float(item["alpha"]))
        for item in protocol["error_budget_ledger"]["allocations"]
    }
    actual = {item["allocation_id"]: item for item in ledger["allocations"]}
    if set(actual) != set(planned):
        raise ValueError("error-ledger allocations differ from protocol")
    consumed = 0.0
    for allocation_id, item in actual.items():
        role, alpha = planned[allocation_id]
        if item["role"] != role or not math.isclose(float(item["alpha"]), alpha, abs_tol=1e-12):
            raise ValueError("error-ledger allocation differs from protocol")
        if item["status"] == "AVAILABLE":
            if item.get("campaign_id") is not None or item.get("consumed_at") is not None:
                raise ValueError("available allocation cannot be campaign-bound")
        elif item["status"] == "CONSUMED":
            if not item.get("campaign_id") or not item.get("consumed_at"):
                raise ValueError("consumed allocation must retain campaign and timestamp")
            consumed += alpha
        else:
            raise ValueError("unknown cumulative-ledger allocation status")
    if not math.isclose(float(ledger["consumed_alpha"]), consumed, abs_tol=1e-12):
        raise ValueError("cumulative consumed alpha is inconsistent")


def analyze(
    payload: dict[str, Any], protocol: dict[str, Any], ledger: dict[str, Any]
) -> dict[str, Any]:
    validate_protocol(protocol)
    validate_ledger(ledger, protocol)
    if payload.get("schema") != "crane-diagnostic-sequential-results/v1":
        raise ValueError("unsupported result schema")
    campaign_id = str(payload["campaign_id"])
    if not campaign_id.startswith("diagnostic-seq-") or "legacy" in campaign_id.lower():
        raise ValueError("campaign must use a new diagnostic-seq namespace")
    if payload.get("development_or_legacy_data_included") is not False:
        raise ValueError("development and legacy data are prohibited")
    if payload.get("outcomes_inspected_before_freeze") is not False:
        raise ValueError("campaign outcomes were inspected before freeze")
    if payload.get("protocol_id") != protocol["protocol_id"]:
        raise ValueError("result payload does not name the frozen protocol")
    if payload.get("protocol_sha256") != protocol_sha256(protocol):
        raise ValueError("result payload protocol hash does not match")
    registration = payload.get("campaign_registration", {})
    if registration.get("registered_before_outcomes") is not True:
        raise ValueError("campaign was not registered before outcomes")
    if registration.get("information_tool_resource_parity_audited") is not True:
        raise ValueError("P/R information, tool, and resource parity was not audited")
    required_hashes = {
        "proposed_method",
        "baseline",
        "evidence_contract",
        "target_sampler",
        "question_references",
        "luna_judge",
        "analysis_code",
    }
    frozen_hashes = registration.get("frozen_hashes", {})
    if set(frozen_hashes) != required_hashes or any(
        not _is_sha256(value) for value in frozen_hashes.values()
    ):
        raise ValueError("campaign registration must contain all seven SHA-256 freeze hashes")

    allocation_id = str(payload["alpha_allocation_id"])
    allocations = {
        item["allocation_id"]: item for item in protocol["error_budget_ledger"]["allocations"]
    }
    if allocation_id not in allocations:
        raise ValueError("campaign has no predeclared alpha allocation")
    allocation = allocations[allocation_id]
    ledger_allocation = {
        item["allocation_id"]: item for item in ledger["allocations"]
    }[allocation_id]

    rows = payload["clusters"]
    if not isinstance(rows, list):
        raise ValueError("clusters must be a chronological list")
    if rows and (
        any(value == "0" * 64 for value in frozen_hashes.values())
        or payload.get("judge_quality", {}).get("qualification_manifest_sha256") == "0" * 64
    ):
        raise ValueError("zero-hash placeholders are allowed only for the empty dry run")
    if len(rows) > int(protocol["stopping_rule"]["maximum_total_clusters"]):
        raise ValueError("campaign exceeds its hard maximum cluster count")
    if rows and (
        ledger_allocation["status"] != "CONSUMED"
        or ledger_allocation["campaign_id"] != campaign_id
    ):
        raise ValueError("alpha allocation must be consumed by this campaign before outcomes")
    if not rows and ledger_allocation["status"] == "CONSUMED" and (
        ledger_allocation["campaign_id"] != campaign_id
    ):
        raise ValueError("alpha allocation is bound to another campaign")
    cluster_ids = [str(item["cluster_id"]) for item in rows]
    if len(cluster_ids) != len(set(cluster_ids)):
        raise ValueError("duplicate cluster ID; variants and paraphrases must remain clustered")
    if any(item.get("independent_cluster") is not True for item in rows):
        raise ValueError("every primary row must be an independent scenario cluster")
    configuration_ids = [str(item["configuration_id"]) for item in rows]
    if len(configuration_ids) != len(set(configuration_ids)):
        raise ValueError("configuration reuse is not an independent scenario cluster")
    sequence = [int(item["sequence_index"]) for item in rows]
    if sequence != list(range(1, len(rows) + 1)):
        raise ValueError("clusters must be supplied in chronological sequence")
    if payload.get("sampling_rule_changed_after_outcomes") is not False:
        raise ValueError("outcome-adaptive scenario sampling is prohibited")

    allowed_strata = {
        item["stratum_id"]: float(item["probability"])
        for item in protocol["target_distribution"]["strata"]
    }
    for row in rows:
        if row["stratum_id"] not in allowed_strata:
            raise ValueError(f"unknown scenario stratum: {row['stratum_id']}")
        if not math.isclose(
            float(row["declared_sampling_probability"]),
            allowed_strata[row["stratum_id"]],
            abs_tol=1e-12,
        ):
            raise ValueError("row sampling probability differs from frozen target")
        if row.get("answerability") not in {"diagnosable", "ambiguous"}:
            raise ValueError("answerability must be diagnosable or ambiguous")
        stratum_is_ambiguous = str(row["stratum_id"]).endswith("-ambiguous")
        if stratum_is_ambiguous != (row["answerability"] == "ambiguous"):
            raise ValueError("answerability disagrees with the frozen target stratum")

    primary = [
        paired_difference(
            item["supported_diagnostic_success_p"],
            item["supported_diagnostic_success_r"],
            "primary",
        )
        for item in rows
        if item["answerability"] == "diagnosable"
    ]
    material = [
        paired_difference(item["material_error_p"], item["material_error_r"], "material_error")
        for item in rows
    ]
    coverage = [
        paired_difference(item["useful_coverage_p"], item["useful_coverage_r"], "useful_coverage")
        for item in rows
    ]
    ambiguity = [
        paired_difference(
            item["correct_ambiguity_handling_p"],
            item["correct_ambiguity_handling_r"],
            "ambiguity",
        )
        for item in rows
        if item["answerability"] == "ambiguous"
    ]

    campaign_alpha = float(allocation["alpha"])
    # This is an intersection-union claim: overall success requires rejecting every
    # component null.  Testing each component at the campaign alpha controls the overall
    # type-I error because a false overall success must reject at least one true component
    # null.  Program-level alpha spending still applies across campaigns/candidates.
    gate_alpha = campaign_alpha
    bet_fractions = tuple(
        float(item) for item in protocol["analysis"]["betting_fractions"]
    )
    margins = protocol["decision_thresholds"]
    endpoints = {
        "supported_diagnostic_success": _endpoint(
            primary,
            float(margins["minimum_worthwhile_improvement"]),
            "lower",
            gate_alpha,
            bet_fractions,
        ),
        "material_error_difference": _endpoint(
            material,
            float(margins["maximum_material_error_degradation"]),
            "upper",
            gate_alpha,
            bet_fractions,
        ),
        "useful_coverage_difference": _endpoint(
            coverage,
            -float(margins["maximum_useful_coverage_degradation"]),
            "lower",
            gate_alpha,
            bet_fractions,
        ),
        "ambiguity_handling_difference": _endpoint(
            ambiguity,
            -float(margins["maximum_ambiguity_handling_degradation"]),
            "lower",
            gate_alpha,
            bet_fractions,
        ),
    }

    minimums = protocol["stopping_rule"]
    quality = payload["judge_quality"]
    judge_ready = (
        quality.get("heldout_qualification_passed") is True
        and quality.get("frozen_configuration_used") is True
        and _is_sha256(quality.get("qualification_manifest_sha256"))
        and quality.get("two_isolated_passes_completed") is True
        and int(quality.get("unresolved_labels", 0)) == 0
        and int(quality["maximum_allowed_unresolved_labels"]) == 0
    )
    enough = (
        len(rows) >= int(minimums["minimum_total_clusters_before_success"])
        and len(primary) >= int(minimums["minimum_diagnosable_clusters_before_success"])
        and len(ambiguity) >= int(minimums["minimum_ambiguous_clusters_before_success"])
    )
    all_bounds_pass = all(item["passed"] for item in endpoints.values())

    replication = payload.get("replication", {})
    replication_ready = True
    if allocation["role"] == "replication":
        replication_ready = (
            replication.get("same_frozen_method_and_baseline") is True
            and replication.get("fresh_configuration_overlap_count") == 0
            and replication.get("discovery_response_reuse_count") == 0
        )

    status = "CONTINUE"
    if len(rows) >= int(minimums["maximum_total_clusters"]):
        if all_bounds_pass and enough and judge_ready and replication_ready:
            status = "SUCCESS"
        else:
            status = "STOP_MAXIMUM_WITHOUT_SUCCESS"
    elif all_bounds_pass and enough and judge_ready and replication_ready:
        status = "SUCCESS"
    elif len(rows) in set(int(item) for item in minimums["futility_review_cluster_counts"]):
        primary_upper = (
            upper_confidence_bound(primary, 0.05, bet_fractions) if primary else 1.0
        )
        if primary_upper <= float(margins["minimum_worthwhile_improvement"]):
            status = "STOP_FOR_FUTILITY_REVIEW"

    counts: dict[str, int] = {item: 0 for item in allowed_strata}
    for row in rows:
        counts[row["stratum_id"]] += 1
    return {
        "schema": "crane-diagnostic-sequential-monitor/v1",
        "protocol_id": protocol["protocol_id"],
        "campaign_id": campaign_id,
        "alpha_allocation_id": allocation_id,
        "campaign_alpha": campaign_alpha,
        "per_gate_intersection_union_alpha": gate_alpha,
        "independent_clusters": len(rows),
        "diagnosable_clusters": len(primary),
        "ambiguous_clusters": len(ambiguity),
        "realized_stratum_counts": counts,
        "endpoints": endpoints,
        "judge_ready": judge_ready,
        "minimum_sample_requirements_met": enough,
        "replication_requirements_met": replication_ready,
        "status": status,
        "allowed_conclusion": (
            "meaningful_advantage_established_for_this_campaign"
            if status == "SUCCESS"
            else "meaningful_advantage_not_established"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    payload = json.loads(args.results.read_text(encoding="utf-8"))
    result = analyze(payload, protocol, ledger)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
