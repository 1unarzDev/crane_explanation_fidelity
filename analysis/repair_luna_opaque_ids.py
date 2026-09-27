#!/usr/bin/env python3
"""Create audited derivatives of Luna judgments rejected only for an opaque-ID typo.

The original call record is immutable.  This utility never calls a model and never changes a
semantic field.  It accepts only a complete retained judgment whose sole validation failure is the
transactional opaque response ID, and binds the correction to the original request envelope and
the unique response-ID inventory in the blinded packet.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

from luna_model_judge import canonical_json, validate_judgment


RULE_ID = "luna-opaque-response-id-transport-repair-v1"
ID_ERROR = "judgment opaque_response_id does not match request"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    if path.exists():
        if path.read_bytes() != encoded:
            raise FileExistsError(f"refusing to replace a different derivative: {path}")
        return
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(encoded)
        temporary = Path(handle.name)
    temporary.replace(path)


def _without_id(judgment: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(judgment)
    result.pop("opaque_response_id", None)
    return result


def repair_record(
    source: Path, output: Path, packet_response_ids: set[str]
) -> dict[str, Any]:
    """Repair one retained ID-only failure and return its audit provenance."""
    source_bytes = source.read_bytes()
    record = load_json(source)
    if record.get("status") != "INVALID_JUDGMENT_NO_RETRY":
        raise ValueError("source is not a retained invalid judgment")
    if record.get("validation_error") != ID_ERROR:
        raise ValueError("retained failure is not ID-only")
    envelope = record.get("request_identity", {}).get("envelope")
    if not isinstance(envelope, dict):
        raise ValueError("retained request has no complete envelope")
    expected = envelope.get("opaque_response_id")
    if not isinstance(expected, str) or expected not in packet_response_ids:
        raise ValueError("request ID is not uniquely bound to the blinded packet")
    if len(packet_response_ids) < 2:
        raise ValueError("packet response inventory is incomplete")
    raw_final = record.get("raw_final")
    if not isinstance(raw_final, str):
        raise ValueError("retained judgment has no raw final output")
    try:
        original = json.loads(raw_final)
    except json.JSONDecodeError as error:
        raise ValueError("retained judgment is not valid JSON") from error
    if not isinstance(original, dict):
        raise ValueError("retained judgment is not a JSON object")
    returned = original.get("opaque_response_id")
    if not isinstance(returned, str) or returned == expected:
        raise ValueError("retained judgment does not contain a distinct malformed ID")
    if returned in packet_response_ids:
        raise ValueError("returned ID identifies another packet response")

    repaired = copy.deepcopy(original)
    repaired["opaque_response_id"] = expected
    # This validates every schema/core consistency check after the one permitted correction.
    validate_judgment(repaired, envelope)
    before_semantics = canonical_json(_without_id(original))
    after_semantics = canonical_json(_without_id(repaired))
    if before_semantics != after_semantics:
        raise ValueError("transport repair changed semantic judgment content")

    repaired_raw = canonical_json(repaired)
    provenance = {
        "rule_id": RULE_ID,
        "source_path": str(source),
        "source_record_sha256": sha256_bytes(source_bytes),
        "original_raw_final_sha256": sha256_bytes(raw_final.encode()),
        "repaired_raw_final_sha256": sha256_bytes(repaired_raw.encode()),
        "expected_opaque_response_id": expected,
        "returned_opaque_response_id": returned,
        "mapping_basis": "immutable request envelope plus unique blinded-packet response inventory",
        "changed_fields": ["opaque_response_id"],
        "semantic_payload_unchanged": True,
        "model_recalled": False,
    }
    derivative = copy.deepcopy(record)
    derivative["status"] = "VALID"
    derivative["raw_final"] = repaired_raw
    derivative["judgment"] = repaired
    derivative.pop("validation_error", None)
    derivative["transport_repair"] = provenance
    atomic_write(output, derivative)
    return provenance


def packet_ids(path: Path) -> set[str]:
    ids: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        value = json.loads(line)
        response_id = value.get("response_id")
        if not isinstance(response_id, str) or not response_id:
            raise ValueError("packet contains an invalid response ID")
        ids.append(response_id)
    if len(ids) < 2 or len(ids) != len(set(ids)):
        raise ValueError("packet response IDs must be unique and complete")
    return set(ids)


def repair_cluster(source_root: Path, packet: Path, output_root: Path) -> dict[str, Any]:
    ids = packet_ids(packet)
    entries: list[dict[str, Any]] = []
    records = sorted((source_root / "calls" / "high").glob("pass-*/*.json"))
    if len(records) != 2 * len(ids):
        raise ValueError("call inventory does not match two passes over the packet")
    for source in records:
        record = load_json(source)
        destination = output_root / "calls" / "high" / source.parent.name / source.name
        if record.get("status") == "VALID":
            envelope = record.get("request_identity", {}).get("envelope")
            if not isinstance(envelope, dict) or envelope.get("opaque_response_id") not in ids:
                raise ValueError("valid source record is not bound to this packet")
            validate_judgment(record.get("judgment", {}), envelope)
            atomic_write(destination, record)
            continue
        entries.append(repair_record(source, destination, ids))
    if not entries:
        raise ValueError("cluster contains no ID-only failures to repair")
    manifest = {
        "schema": "crane-luna-transport-repair-manifest/v1",
        "rule_id": RULE_ID,
        "scope": "post-hoc deterministic transport correction; semantic labels unchanged",
        "source_root": str(source_root),
        "packet_path": str(packet),
        "packet_sha256": sha256_path(packet),
        "repaired_record_count": len(entries),
        "entries": entries,
    }
    atomic_write(output_root / "transport-repair-manifest.json", manifest)
    return manifest


def finalize_cluster(
    *, packet: Path, key_path: Path, output_root: Path, cluster_id: str,
    family: str, sequence_index: int,
) -> dict[str, Any]:
    """Revalidate the repaired cache and derive a separately marked reconciliation."""
    from focused_first_look_coordinator import cluster_rows
    from run_luna_single_diagnostic_packet import read_jsonl, run

    summary_path = output_root / "development-summary.json"
    if summary_path.exists():
        report = load_json(summary_path)
    else:
        report = run(packet, key_path, output_root)
    if report.get("call_failures") or report.get("valid_judgments") != report.get("planned_judgments"):
        raise ValueError("repaired derivative did not produce a complete two-pass summary")
    rows = read_jsonl(packet)
    if not rows or any(row.get("primary_endpoint_eligible") is not True for row in rows):
        raise ValueError("only primary-eligible repaired clusters may be reconciled")
    key = load_json(key_path)
    result = cluster_rows(
        packet_rows=rows,
        key=key,
        report=report,
        cache_root=output_root / "calls" / "high",
        cluster_id=cluster_id,
        configuration_id=cluster_id,
        family=family,
        sequence_index=sequence_index,
    )
    reconciliation = {
        "schema": "crane-focused-cluster-reconciliation-transport-correction/v1",
        "status": "POST_HOC_TRANSPORT_CORRECTED_NOT_ORIGINAL_REGISTERED_RELEASE",
        "cluster_id": cluster_id,
        "inputs": {
            "packet_sha256": sha256_path(packet),
            "key_sha256": sha256_path(key_path),
            "report_sha256": sha256_path(summary_path),
            "repair_manifest_sha256": sha256_path(output_root / "transport-repair-manifest.json"),
        },
        **result,
    }
    atomic_write(output_root / "reconciliation.json", reconciliation)
    return reconciliation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--key", type=Path)
    parser.add_argument("--cluster-id")
    parser.add_argument("--family")
    parser.add_argument("--sequence-index", type=int)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    output_root = args.output_root.resolve()
    result = repair_cluster(
        args.source_root.resolve(strict=True),
        packet,
        output_root,
    )
    finalize_values = (args.key, args.cluster_id, args.family, args.sequence_index)
    if any(value is not None for value in finalize_values):
        if any(value is None for value in finalize_values):
            parser.error("--key, --cluster-id, --family, and --sequence-index are all required together")
        finalize_cluster(
            packet=packet,
            key_path=args.key.resolve(strict=True),
            output_root=output_root,
            cluster_id=args.cluster_id,
            family=args.family,
            sequence_index=args.sequence_index,
        )
    print(json.dumps({
        "status": "REPAIRED_AND_RECONCILED" if args.key else "REPAIRED",
        "count": result["repaired_record_count"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
