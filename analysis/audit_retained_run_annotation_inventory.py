#!/usr/bin/env python3
"""Inventory retained semantic-run artifacts without reinterpreting old labels.

This is deliberately a file/provenance audit, not an endpoint rescore.  Historical
packet schemas remain historical; compatibility means only that an artifact can be
used as development input after evidence-closure review.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOTS = (
    "analysis/results",
    "artifacts",
    "data/evaluator_only",
    "data/robot_visible",
    "manifests",
    "model_outputs",
    "research/explanation_fidelity",
)
REDIRECT_MARKERS = ("evidence-calibration", "evidence_calibration")
SELF_OUTPUTS = {
    "manifests/study/evidence-calibration-retrospective-run-audit-v1.json",
    "manifests/study/evidence-calibration-retrospective-findings-v1.json",
    # This living readiness file binds the audit hash; excluding it prevents a hash cycle.
    "manifests/study/evidence-calibration-p11-prefreeze-readiness.json",
}
LEGACY_MARKERS = ("provenance-study", "provenance_study", "/pn-", "legacy-calibration")
DEVELOPMENT_MARKERS = (
    "contract-complete", "contract_limit", "contract-limit", "focused-supported",
    "measurement-complete", "coverage-complete", "checked-composition",
    "causal-restraint", "diagnostic-development", "/dev/", "/development/",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json_summary(path: Path) -> tuple[list[str], int, dict[str, Any] | None, str | None]:
    """Return schemas, row count, one representative object, and parse error."""
    try:
        if path.suffix == ".json":
            value = json.loads(path.read_text(encoding="utf-8"))
            schema = value.get("schema", "<none>") if isinstance(value, dict) else "<nonobject>"
            return [schema], 1, value if isinstance(value, dict) else None, None
        schemas: set[str] = set()
        first: dict[str, Any] | None = None
        count = 0
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                count += 1
                # Schema and identifiers are expected to be stable within retained JSONL packets.
                # Parse the first 32 records to detect mixed packet files without loading giant logs.
                if count <= 32:
                    value = json.loads(line)
                    if isinstance(value, dict):
                        first = first or value
                        schemas.add(value.get("schema", "<none>"))
                    else:
                        schemas.add("<nonobject>")
        return sorted(schemas or {"<blank>"}), count, first, None
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return ["<parse-error>"], 0, None, f"{type(error).__name__}: {error}"


def _classify(path: str, schemas: Iterable[str], representative: dict[str, Any] | None) -> str:
    haystack = (path + " " + " ".join(schemas)).lower()
    status = str((representative or {}).get("status", "")).lower()
    if "qualification" in haystack:
        return "JUDGE_QUALIFICATION"
    if any(marker in haystack for marker in REDIRECT_MARKERS):
        return "NEW_REDIRECT_DEVELOPMENT"
    if any(marker in haystack for marker in LEGACY_MARKERS) or "provenance" in haystack:
        return "LEGACY_EXPLORATORY_UNDER_TARGET"
    if "invalidated" in status or "invalid_release" in haystack or "invalidated-release" in haystack:
        return "INVALID_REGISTERED_RELEASE_RETAINED"
    if any(marker in haystack for marker in DEVELOPMENT_MARKERS):
        return "DEVELOPMENT_REGRESSION"
    if any(token in haystack for token in ("model-call", "response-pair", "annotation", "luna-")):
        return "DEVELOPMENT_REVIEW_REQUIRED"
    return "GOVERNANCE_PHYSICAL_OR_INFRASTRUCTURE"


def _role(path: str, schemas: Iterable[str]) -> str:
    value = (path + " " + " ".join(schemas)).lower()
    if "response-pair" in value or "/pairs/" in value:
        return "RESPONSE_PAIR"
    if "model-call" in value or "/calls/" in value or "model_cache" in value:
        return "MODEL_CALL"
    if "annotation" in value and ("packet" in value or path.endswith(".jsonl")):
        return "ANNOTATION_PACKET"
    if "qualification" in value:
        return "QUALIFICATION"
    if "summary" in value or "result" in value or "/analysis/" in value:
        return "SUMMARY_OR_ANALYSIS"
    if "reference" in value or "evaluator_only" in path:
        return "EVALUATOR_OR_REFERENCE"
    if "robot_visible" in path:
        return "ROBOT_VISIBLE_EVIDENCE"
    return "OTHER"


def _annotation_compatibility(role: str, schemas: Iterable[str], disposition: str) -> str:
    joined = " ".join(schemas)
    if "crane-blinded-agent-atomic-annotation" in joined:
        return "NEW_SCHEMA_EXACT_TASK_QUALIFICATION_PENDING"
    if role == "ANNOTATION_PACKET":
        return "HISTORICAL_SCHEMA_PRESERVE_LABELS_NO_AUTOMATIC_CONVERSION"
    if role == "RESPONSE_PAIR" and disposition != "NEW_REDIRECT_DEVELOPMENT":
        return "DEVELOPMENT_ONLY_FRESH_ATOMIC_ANNOTATION_REQUIRES_EVIDENCE_CLOSURE_AUDIT"
    return "NOT_AN_ANNOTATION_CANDIDATE"


def _ids(value: Any, out: dict[str, set[str]], depth: int = 0) -> None:
    if depth > 8:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"episode_id", "configuration_id", "cluster_id", "condition_id", "question_id", "pass_id"} and isinstance(item, (str, int)):
                out[key].add(str(item))
            else:
                _ids(item, out, depth + 1)
    elif isinstance(value, list):
        for item in value[:512]:
            _ids(item, out, depth + 1)


def build(repo_root: Path = ROOT, roots: Iterable[str] = DEFAULT_ROOTS) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    identifiers: dict[str, set[str]] = defaultdict(set)
    for relative_root in roots:
        base = repo_root / relative_root
        if not base.exists():
            continue
        for path in sorted(p for p in base.rglob("*") if p.is_file() and p.suffix in {".json", ".jsonl"}):
            relative = path.relative_to(repo_root).as_posix()
            if relative in SELF_OUTPUTS:
                continue
            schemas, records, representative, error = _read_json_summary(path)
            disposition = _classify(relative, schemas, representative)
            role = _role(relative, schemas)
            if representative:
                _ids(representative, identifiers)
            entries.append({
                "path": relative,
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
                "format": path.suffix.lstrip("."),
                "record_count": records,
                "schemas_observed_in_sample": schemas,
                "parse_error": error,
                "artifact_role": role,
                "scientific_disposition": disposition,
                "new_atomic_annotation_compatibility": _annotation_compatibility(role, schemas, disposition),
            })
    by_schema = Counter(schema for item in entries for schema in item["schemas_observed_in_sample"])
    by_role = Counter(item["artifact_role"] for item in entries)
    by_disposition = Counter(item["scientific_disposition"] for item in entries)
    compatibility = Counter(item["new_atomic_annotation_compatibility"] for item in entries)
    explicit_units = {key: sorted(values) for key, values in identifiers.items()}
    return {
        "schema": "crane-evidence-calibration-retrospective-run-audit/v1",
        "generated_from_retained_files_only": True,
        "historical_labels_reinterpreted": False,
        "confirmation_independent_n": 0,
        "replication_independent_n": 0,
        "independent_unit_rule": "episode/configuration; masks, questions, model calls, and annotation passes are repeated measurements",
        "scope_roots": list(roots),
        "summary": {
            "files": len(entries),
            "bytes": sum(item["bytes"] for item in entries),
            "parse_errors": sum(item["parse_error"] is not None for item in entries),
            "files_by_role": dict(sorted(by_role.items())),
            "files_by_disposition": dict(sorted(by_disposition.items())),
            "files_by_annotation_compatibility": dict(sorted(compatibility.items())),
            "files_by_sampled_schema": dict(sorted(by_schema.items())),
            "explicit_identifier_counts_not_sample_sizes": {key: len(values) for key, values in explicit_units.items()},
        },
        "independent_unit_warning": "Identifier counts are provenance diagnostics, not study N; repeated artifacts can bind the same unit and historical cluster semantics vary.",
        "explicit_identifiers": explicit_units,
        "artifacts": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "manifests/study/evidence-calibration-retrospective-run-audit-v1.json")
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
