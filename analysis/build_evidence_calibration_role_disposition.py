#!/usr/bin/env python3
"""Retain paired role candidates and distinct provenance/missingness flags without endpoint scoring."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_pilot_role_continuation import audit as audit_continuation
from audit_evidence_calibration_pilot_role_inputs import audit as audit_inputs
from audit_evidence_calibration_pilot_role_prefix_project_review import audit_review
from build_evidence_calibration_pilot_support_packets import write_once
from validate_evidence_calibration_claim_roles_v2 import INPUT_SCHEMA, validate

ROOT = Path(__file__).resolve().parents[1]
B_REVIEW = "manifests/annotation/evidence-calibration-pilot-role-B-project-review-v1.json"
MANUAL = "manifests/annotation/evidence-calibration-pilot-manual-inventory-v1.json"
CONTINUATION = "manifests/study/evidence-calibration-pilot-role-v2r2-continuation-terminal-v1.json"
OUTPUT = "manifests/annotation/evidence-calibration-pilot-role-disposition-v1.json"
NOTE = "docs/ROLE_DISPOSITION_2026-09-30.md"
AXES = ("stance", "claim_kind", "polarity")
ABORT_ERRORS = {("ax-c1d98a11f06df96b8a782cfc7873b542", "ri-3f586b8d2413f5a65792"),
                ("ax-b7c675effc18c4a5f7624a6f10149946", "ri-f69651e323c4212a8fc9")}
RECOVERY_REFERENT = ("ax-8e8224a765650b9b9933e7b30281b835", "ri-9b41ac7cc72a5356e62e")
SOFTWARE_RESOLUTION = ("ax-d80abe3b7d2b0fffa2717ca37ba4aff7", "ri-575b4e553218fcc94228")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(root: Path, path: str) -> dict:
    return {"path": path, "raw_sha256": digest(root / path)}


def retained_roles(root: Path, entry: dict, slot: str, binding: dict | None) -> list[dict] | None:
    if binding is None:
        return None
    path = root / binding["path"]
    if digest(path) != binding["raw_sha256"]:
        raise ValueError("reviewed role-return hash changed")
    record = json.loads(path.read_text())
    parsed = json.loads(record["raw_final"])
    payload = {"schema": INPUT_SCHEMA, "opaque_response_id": f"{entry['case_id']}-{slot}",
               "response_text": entry["response_text"], "claims": entry["claims"]}
    structural = validate(payload, parsed)
    if (record.get("parsed_final") != parsed or record.get("structural_validation") != structural
            or record.get("status") != "STRUCTURALLY_VALID_ROLE_QUALIFICATION_UNSCORED"
            or record.get("attempt_count") != 1 or record.get("quality_driven_retries") != 0
            or record.get("return_code") != 0 or record.get("timed_out") is not False
            or record.get("invalid_event") is not None or record.get("method_key_accessed") is not False):
        raise ValueError("reviewed role record is not its retained one-shot raw return")
    return parsed["claim_roles"]


def disposition_rows(entry: dict, a: list[dict] | None, b: list[dict], *, manual: bool, missing: bool) -> list[dict]:
    if missing != (a is None) or len(b) != len(entry["claims"]) or (a is not None and len(a) != len(b)):
        raise ValueError("role missingness or inventory length changed")
    rows = []
    for index, claim in enumerate(entry["claims"]):
        roles = {"A": None if a is None else a[index], "B": b[index]}
        if any(role is not None and role["item_id"] != claim["item_id"] for role in roles.values()):
            raise ValueError("role candidates do not match the unchanged atom IDs")
        differences = [axis for axis in AXES if a is not None and a[index][axis] != b[index][axis]]
        candidates = sorted({tuple(role[axis] for axis in AXES) for role in roles.values() if role is not None})
        key = (entry["case_id"], claim["item_id"])
        concerns = []
        if key in ABORT_ERRORS:
            concerns.append("REVIEWED_ABORT_OCCURRENCE_POLARITY_ERROR_RAW_RETAINED")
        if key == RECOVERY_REFERENT:
            concerns.append("RECOVERY_REFERENT_REQUIRES_CLAIM_CONTEXT_ATTACHMENT")
        if key == SOFTWARE_RESOLUTION:
            concerns.append("SOFTWARE_RESOLUTION_NOT_AUTOMATIC_PHYSICAL_CAUSAL_DIAGNOSIS")
        if claim["claim_text"] in {"Measured response recovery does not cause the eventual task outcome.",
                                   "Measured robot response recovery does not cause the eventual task outcome."}:
            concerns.append("EXPLICIT_NEGATIVE_CAUSATION_ASSERTION_MUST_NOT_BECOME_LIMITATION")
        if "these specific physical causes" in claim["claim_text"]:
            concerns.append("LITERAL_DEICTIC_ANTECEDENT_NOT_SUPPLIED")
        if claim["response_span"].strip() in {"Yes.", "No."}:
            concerns.append("QUESTION_BOUND_AFFIRMATIVE_SCOPE_REQUIRES_ATTACHMENT")
        rows.append({"case_id": entry["case_id"], "claim": claim, "retained_roles": roles,
                     "role_tuple_candidates": [dict(zip(AXES, candidate)) for candidate in candidates],
                     "differing_axes": differences,
                     "disposition": "INCOMPLETE_A_NO_IMPUTATION" if missing else
                        "RETAIN_BOTH_UNSELECTED" if differences else "RETAIN_AGREEMENT_ADVISORY_ONLY",
                     "project_review_concerns": concerns, "manual_inventory_provenance": manual,
                     "selected_role": None, "attached_contract": None, "asserted_rank": None,
                     "mechanistic_flag": None, "endpoint_scoring_authorized": False})
    return rows



def episode_sensitivity_sets(joined_metadata: list[dict], triggers: list[dict], *, join_authorized: bool = False) -> dict:
    """Project already authorized metadata to whole-episode variants; never reads a key file."""
    if join_authorized is not True:
        raise ValueError("method-key join must be separately authorized after measurement gates")
    responses, episode_to_config, config_to_episode = {}, {}, {}
    for row in joined_metadata:
        required = ("opaque_response_id", "episode_id", "configuration_id")
        if any(not isinstance(row.get(key), str) or not row[key] for key in required):
            raise ValueError("sensitivity metadata needs exact response/episode/configuration IDs")
        response_id, episode, config = (row[key] for key in required)
        if response_id in responses:
            raise ValueError("duplicate joined response metadata")
        if episode_to_config.get(episode, config) != config or config_to_episode.get(config, episode) != episode:
            raise ValueError("episode/configuration mapping must be one-to-one for independent units")
        episode_to_config[episode], config_to_episode[config] = config, episode
        responses[response_id] = (episode, config)
    reasons = {"PROJECT_AUTHORED_EXTRACTION_INVENTORY": set(), "ORIGINAL_ROLE_A_UNKNOWN_NO_REPLACEMENT": set()}
    seen = set()
    for trigger in triggers:
        response_id = trigger["case_id"]
        if response_id in seen or response_id not in responses or trigger["reason"] not in reasons:
            raise ValueError("sensitivity trigger missing, duplicated, or undeclared")
        seen.add(response_id)
        reasons[trigger["reason"]].add(responses[response_id])
    if any(not values for values in reasons.values()):
        raise ValueError("both distinct provenance/missingness reasons must be represented")
    manual = reasons["PROJECT_AUTHORED_EXTRACTION_INVENTORY"]
    missing = reasons["ORIGINAL_ROLE_A_UNKNOWN_NO_REPLACEMENT"]
    excluded = {"FULL_RETAINED_BANK_WITH_FLAGS": set(),
                "EXCLUDE_WHOLE_EPISODE_CONTAINING_MANUAL_INVENTORY": manual,
                "EXCLUDE_WHOLE_EPISODE_CONTAINING_MISSING_ROLE_A": missing,
                "EXCLUDE_UNION_OF_BOTH_EPISODE_SETS": manual | missing}
    return {name: {"excluded_episode_configuration_ids": [list(unit) for unit in sorted(units)],
                   "retained_response_ids": sorted(response_id for response_id, unit in responses.items() if unit not in units),
                   "retained_independent_episode_configuration_count": len(set(responses.values()) - units)}
            for name, units in excluded.items()}


def build(root: Path = ROOT) -> dict:
    if root.resolve() != ROOT.resolve():
        raise ValueError("role disposition must use the audited checkout root")
    # Existing auditors reproduce the bound original and continuation histories without model calls.
    audit_inputs()
    audit_review()
    continuation = json.loads((root / CONTINUATION).read_text())
    if audit_continuation(process_terminal=True) != continuation:
        raise ValueError("role continuation differs from its bound terminal snapshot")
    review = json.loads((root / B_REVIEW).read_text())
    for item in review["bindings"].values():
        if digest(root / item["path"]) != item["raw_sha256"]:
            raise ValueError("B application review binding changed")
    for field in ("method_key_opened", "evaluator_truth_opened", "visible_evidence_opened", "support_labels_generated",
                  "endpoint_scores_generated", "returned_labels_changed", "p11_authorized"):
        if review.get(field) is not False:
            raise ValueError("blind role-review boundary changed")
    bundle = json.loads((root / review["bindings"]["input_bundle"]["path"]).read_text())
    entries = {entry["case_id"]: entry for entry in bundle["entries"]}
    if len(entries) != 114 or [row["case_id"] for row in review["records"]] != sorted(entries):
        raise ValueError("review records do not cover exactly the blind 114-answer bank")
    quarantine = continuation["original_quarantined_requests"]
    if len(quarantine) != 1 or quarantine[0]["slot"] != "A" or quarantine[0]["disposition"] != "UNKNOWN_DISPOSITION_NO_RETRY":
        raise ValueError("original unknown A quarantine changed")
    unknown = quarantine[0]["case_id"]
    manual = json.loads((root / MANUAL).read_text())
    manual_id = manual["opaque_response_id"]
    if manual_id == unknown or len(manual["atomic_claims"]) != 15:
        raise ValueError("manual extraction provenance must remain distinct from missing role A")
    all_rows, differences, b_only = [], [], []
    for row in review["records"]:
        entry = entries[row["case_id"]]
        if row["atomic_judgment_count"] != len(entry["claims"]):
            raise ValueError("reviewed claim count changed")
        a = retained_roles(root, entry, "A", row["A_record"])
        b = retained_roles(root, entry, "B", row["B_record"])
        if b is None:
            raise ValueError("B is incomplete")
        rows = disposition_rows(entry, a, b, manual=entry["case_id"] == manual_id, missing=entry["case_id"] == unknown)
        all_rows.extend(rows)
        for item in rows:
            if item["differing_axes"]:
                differences.append({"A": item["retained_roles"]["A"], "B": item["retained_roles"]["B"],
                                    "case_id": item["case_id"], "claim": item["claim"]})
            elif item["retained_roles"]["A"] is None:
                b_only.append({"B": item["retained_roles"]["B"], "case_id": item["case_id"], "claim": item["claim"]})
    axes = {axis: sum(axis in row["differing_axes"] for row in all_rows) for axis in AXES}
    if (differences != review["differing_paired_judgments"] or b_only != review["B_only_judgments"]
            or axes != review["axis_disagreement_counts"] or len(all_rows) != 1084
            or len(differences) != 53 or len(b_only) != 13):
        raise ValueError("paired role disagreements/missingness do not reproduce the reviewed bank")
    return {"schema": "crane-pilot-role-disposition/v1-development", "recorded_date": "2026-09-30",
            "status": "RAW_ROLE_DISAGREEMENT_AND_MISSINGNESS_HANDLING_BOUND_ENDPOINT_ATTACHMENT_OPEN",
            "bindings": {"B_review": bind(root, B_REVIEW), "manual_inventory": bind(root, MANUAL),
                         "continuation_terminal": bind(root, CONTINUATION),
                         "input_bundle": review["bindings"]["input_bundle"], "review_note": bind(root, NOTE),
                         "builder": bind(root, "analysis/build_evidence_calibration_role_disposition.py")},
            "response_count": 114, "atom_count": 1084, "known_A_returns": 113, "known_B_returns": 114,
            "paired_atom_count": 1071, "matching_tuple_count": 1018, "differing_tuple_count": 53,
            "axis_disagreement_counts": axes, "B_only_atom_count": 13,
            "complete_two_pass_role_bank": False, "original_quarantine": quarantine,
            "manual_inventory_response_id": manual_id, "missing_role_A_response_id": unknown,
            "blind_sensitivity_triggers": [
                {"case_id": manual_id, "reason": "PROJECT_AUTHORED_EXTRACTION_INVENTORY", "atom_count": 15},
                {"case_id": unknown, "reason": "ORIGINAL_ROLE_A_UNKNOWN_NO_REPLACEMENT", "atom_count": 13}],
            "sensitivity_policy": {"scope": "DEVELOPMENT_ONLY_AFTER_AUTHORIZED_METHOD_KEY_JOIN",
                "variants": ["FULL_RETAINED_BANK_WITH_FLAGS", "EXCLUDE_WHOLE_EPISODE_CONTAINING_MANUAL_INVENTORY",
                             "EXCLUDE_WHOLE_EPISODE_CONTAINING_MISSING_ROLE_A", "EXCLUDE_UNION_OF_BOTH_EPISODE_SETS"],
                "exclusion_unit": "episode/configuration across all methods, masks and questions",
                "repeated_episodes_deduplicated": True, "method_specific_filtering_prohibited": True,
                "select_variant_by_effect_or_p_value_prohibited": True,
                "execute_only_after_support_adjudication_and_claim_attachment": True},
            "role_policy": "Retain all A/B candidates; no majority vote, pass selection, missing-A imputation, or role-kind/rank conversion. Attach exact claims independently under a prospectively validated contract/rank map.",
            "rows": all_rows, "bookkeeping_disposition_complete": True, "semantic_role_adjudication_claimed": False,
            "claim_specific_endpoint_attachment_complete": False, "returned_labels_changed": False,
            "model_call_attempted": False, "support_labels_generated": False, "endpoint_scores_generated": False,
            "method_key_opened": False, "visible_evidence_opened": False, "evaluator_truth_opened": False,
            "human_validation_claimed": False, "pilot_annotation_authorized": False, "p11_authorized": False,
            "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = build()
    if args.write:
        write_once(ROOT / OUTPUT, result)
    elif (ROOT / OUTPUT).exists() and json.loads((ROOT / OUTPUT).read_text()) != result:
        raise ValueError("role disposition does not reproduce its retained inputs")
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2))
