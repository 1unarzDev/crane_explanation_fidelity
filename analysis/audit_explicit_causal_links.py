#!/usr/bin/env python3
"""Audit explicit causal-link assertions covered by a finite public contract.

This intentionally detects only named, overt relation assertions. Absence of a finding is not a
general semantic-correctness judgment. The detector is suitable for independently auditable
causal-restraint measurements, not as a replacement for unrestricted semantic annotation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DETECTOR_SOURCE = Path(__file__).resolve()
SUPPORTED_FAMILIES = {
    "persistent_command_motion_discrepancy",
    "measured_response_recovery",
}

SHIELD = re.compile(
    r"(?i)(?:does|do|did)\s+not\s+(?:establish|prove|show|demonstrate)\s+that\s+$"
    r"|(?:cannot|can't)\s+(?:establish|prove|show|demonstrate)\s+that\s+$"
    r"|(?:cannot|can't)\s+be\s+(?:established|proved|proven|shown|demonstrated)\s+that\s+$"
    r"|(?:is|are|was|were)\s+not\s+shown\s+to\s+$"
    r"|(?:is|are|was|were)\s+(?:unproved|unproven|unestablished)\s+that\s+$"
    r"|(?:there\s+is|there's)\s+no\s+evidence\s+that\s+$"
)

RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "wait_to_outcome_effect",
        re.compile(
            r"(?i)\b(?:the\s+)?wait(?:s|\s+invocations?)?\s+"
            r"(?:(?:probably|plausibly|may\s+have|might\s+have)\s+)?"
            r"(?:(?:did\s+not|didn't)\s+)?(?:lead\s+to|yield(?:ed)?|produce[ds]?|"
            r"resulted\s+in|caused)\s+"
            r"(?:a\s+)?(?:successful\s+action|task\s+success|success)\b"
        ),
    ),
    (
        "wait_to_recovery_effect",
        re.compile(
            r"(?i)\b(?:(?:the\s+recorded\s+failure\s+and\s+)?wait\s+invocations?\s+"
            r"make\s+wait-to-recovery\s+plausible|"
            r"(?:the\s+(?:recorded\s+)?)?wait(?:s|\s+invocations?)?\s+"
            r"(?:(?:probably|plausibly|may\s+have|might\s+have)\s+)?"
            r"(?:(?:(?:did\s+not|didn't)\s+)?caused?\s+(?:the\s+)?recovery|"
            r"resulted\s+in\s+(?:the\s+)?recovery|"
            r"restored\s+motion|helped\s+(?:the\s+robot\s+)?(?:regain|restore)\s+motion))\b"
        ),
    ),
    (
        "recovery_to_outcome_effect",
        re.compile(
            r"(?i)\b(?:the\s+)?recovery\s+(?:(?:probably|plausibly|may\s+have|"
            r"might\s+have|directly)\s+)?(?:caused|led\s+to|resulted\s+in)\s+"
            r"(?:the\s+)?(?:eventual\s+)?(?:success|abort|failure|outcome)\b"
        ),
    ),
    (
        "discrepancy_to_outcome_effect",
        re.compile(
            r"(?i)\b(?:the\s+)?discrepancy\s+(?:(?:probably|plausibly|may\s+have|"
            r"might\s+have|directly)\s+)?(?:caused|led\s+to|resulted\s+in)\s+"
            r"(?:the\s+)?(?:abort|failure|outcome)\b"
        ),
    ),
    (
        "physical_cause_assertion",
        re.compile(
            r"(?i)\b(?:a\s+)?(?:physical\s+obstacle|blocked\s+wheel|collision|"
            r"obstruction|slip|motor\s+failure|actuator\s+rejection)\s+"
            r"(?:(?:probably|plausibly|may\s+have|might\s+have)\s+)?"
            r"(?:caused|led\s+to|resulted\s+in)\s+"
            r"(?:the\s+)?(?:discrepancy(?:\s+and\s+abort)?|abort|failure|outcome)\b"
        ),
    ),
)

RULE_IDS = frozenset(relation for relation, _ in RULES)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shielded(text: str, start: int) -> bool:
    prefix = re.sub(r"[*_`]", "", text[max(0, start - 80):start])
    return SHIELD.search(prefix) is not None


def classify_text(
    text: str, prohibited_relations: set[str] | frozenset[str] = RULE_IDS
) -> list[dict[str, Any]]:
    unknown = set(prohibited_relations) - RULE_IDS
    if unknown:
        raise ValueError(f"unknown prohibited relation IDs: {sorted(unknown)}")
    findings: list[dict[str, Any]] = []
    occupied: set[tuple[int, int]] = set()
    for relation, pattern in RULES:
        if relation not in prohibited_relations:
            continue
        for match in pattern.finditer(text):
            location = (match.start(), match.end())
            if location in occupied or shielded(text, match.start()):
                continue
            occupied.add(location)
            findings.append(
                {
                    "relation": relation,
                    "span": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "rule_version": "explicit-prohibited-causal-link-v1",
                }
            )
    return sorted(findings, key=lambda item: (item["start"], item["end"], item["relation"]))


def audit_pair(
    pair: dict[str, Any],
    source_path: Path,
    prohibited_by_family: dict[str, frozenset[str]],
) -> dict[str, Any]:
    family = pair.get("family")
    if family not in SUPPORTED_FAMILIES:
        raise ValueError(f"unsupported family for causal-link audit: {family!r}")
    outputs = pair.get("outputs", [])
    if [item.get("condition") for item in outputs] != ["P-contract", "R-contract"]:
        raise ValueError("pair must preserve exact P-contract/R-contract order")
    if family not in prohibited_by_family:
        raise ValueError(f"contract has no prohibited-relation set for family: {family!r}")
    prohibited_relations = prohibited_by_family[family]
    return {
        "cluster_id": pair["cluster_id"],
        "episode_id": pair["episode_id"],
        "family": family,
        "source_path": source_path.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(source_path),
        "conditions": {
            item["condition"]: {
                "explicit_prohibited_causal_link": bool(
                    findings := classify_text(item["text"], prohibited_relations)
                ),
                "findings": findings,
            }
            for item in outputs
        },
    }


def candidate_version(pair: dict[str, Any]) -> str | None:
    candidate = pair.get("candidate")
    if isinstance(candidate, str):
        return candidate
    if isinstance(candidate, dict):
        version = candidate.get("version")
        return version if isinstance(version, str) else None
    return None


def load_contract(contract: Path) -> dict[str, frozenset[str]]:
    value = json.loads(contract.read_text(encoding="utf-8"))
    if value.get("schema") != "crane-explicit-prohibited-causal-link-contract/v1":
        raise ValueError("unsupported causal-link contract schema")
    raw = value.get("prohibited_relation_ids_by_family")
    if not isinstance(raw, dict) or set(raw) != SUPPORTED_FAMILIES:
        raise ValueError("contract must define exactly the supported families")
    result: dict[str, frozenset[str]] = {}
    for family, relation_ids in raw.items():
        if (
            not isinstance(relation_ids, list)
            or not relation_ids
            or any(not isinstance(item, str) for item in relation_ids)
            or len(relation_ids) != len(set(relation_ids))
        ):
            raise ValueError(f"invalid prohibited relation IDs for {family}")
        relations = frozenset(relation_ids)
        unknown = relations - RULE_IDS
        if unknown:
            raise ValueError(f"unknown relation IDs for {family}: {sorted(unknown)}")
        result[family] = relations
    return result


def build_report(paths: list[Path], contract: Path) -> dict[str, Any]:
    prohibited_by_family = load_contract(contract)
    rows = [
        audit_pair(
            json.loads(path.read_text(encoding="utf-8")), path, prohibited_by_family
        )
        for path in paths
    ]
    condition_counts = {
        condition: sum(row["conditions"][condition]["explicit_prohibited_causal_link"] for row in rows)
        for condition in ("P-contract", "R-contract")
    }
    discordance = {
        "P_only": sum(
            row["conditions"]["P-contract"]["explicit_prohibited_causal_link"]
            and not row["conditions"]["R-contract"]["explicit_prohibited_causal_link"]
            for row in rows
        ),
        "R_only": sum(
            row["conditions"]["R-contract"]["explicit_prohibited_causal_link"]
            and not row["conditions"]["P-contract"]["explicit_prohibited_causal_link"]
            for row in rows
        ),
    }
    return {
        "schema": "crane-explicit-causal-link-development-audit/v1",
        "status": "POST_HOC_DEVELOPMENT_ONLY",
        "detector_version": "explicit-prohibited-causal-link-v1",
        "detector_source": DETECTOR_SOURCE.relative_to(ROOT).as_posix(),
        "detector_source_sha256": sha256(DETECTOR_SOURCE),
        "contract": contract.relative_to(ROOT).as_posix(),
        "contract_sha256": sha256(contract),
        "independent_cluster_count": len(rows),
        "condition_event_counts": condition_counts,
        "discordant_clusters": discordance,
        "descriptive_R_minus_P_risk": (
            condition_counts["R-contract"] - condition_counts["P-contract"]
        ) / len(rows),
        "confirmatory_alpha_consumed": 0.0,
        "allowed_use": "Candidate and endpoint development only; not significance, confirmation, or replication.",
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs-root", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    pairs_root = args.pairs_root.resolve(strict=True)
    contract = args.contract.resolve(strict=True)
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing existing report: {output}")
    paths = sorted(pairs_root.glob("cc-pilot-*.json"))
    if len(paths) != 19:
        raise ValueError(f"expected all 19 retained pilot pairs, found {len(paths)}")
    primary_paths = [
        path for path in paths
        if json.loads(path.read_text(encoding="utf-8")).get("family") in SUPPORTED_FAMILIES
        and candidate_version(json.loads(path.read_text(encoding="utf-8"))) == "p-contract-v2-development"
    ]
    if len(primary_paths) != 14:
        raise ValueError(f"expected 14 v2 primary pairs, found {len(primary_paths)}")
    report = build_report(primary_paths, contract)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "N": report["independent_cluster_count"],
        "events": report["condition_event_counts"],
        "discordance": report["discordant_clusters"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
