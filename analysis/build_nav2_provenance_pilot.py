#!/usr/bin/env python3
"""Build an auditable bounded-provenance bundle for one retained Nav2 benchmark case."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from crane_explain.io import episode_from_dict
from crane_explain.models import SourceArtifact, SourceArtifactKind
from crane_explain.nav2_provenance import build_behavior_tree_provenance
from crane_explain.provenance import resolve_provenance
from crane_explain.reasoning import plan_recovery_mechanism


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git_blob(repository: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(
        ("git", "-C", str(repository), "show", f"{commit}:{path}")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--capture-dir", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--repository-path", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise SystemExit(f"refusing existing output: {args.output_dir}")

    structured_path = args.case_dir / "structured.json"
    captured_path = args.capture_dir / "behavior_tree.xml"
    capture_manifest_path = args.capture_dir / "manifest.json"
    episode_payload = structured_path.read_bytes()
    captured = captured_path.read_bytes()
    capture_manifest_payload = capture_manifest_path.read_bytes()
    capture_manifest = json.loads(capture_manifest_payload)
    if sha256(captured) != capture_manifest["bt_xml_sha256"]:
        raise ValueError("captured BT XML does not match its capture manifest")
    committed = git_blob(args.repository, args.commit, args.repository_path)
    if captured != committed:
        raise ValueError(
            "captured BT XML is not byte-identical to the declared Git object"
        )

    episode = episode_from_dict(json.loads(episode_payload))
    artifact = SourceArtifact(
        id="captured-nav2-recovery-bt",
        kind=SourceArtifactKind.BEHAVIOR_TREE_XML,
        uri=str(captured_path),
        content_sha256=sha256(captured),
        repository=args.repository_url,
        commit=args.commit,
        package="crane_ml",
        path=args.repository_path,
    )
    bundle = build_behavior_tree_provenance(episode, captured.decode("utf-8"), artifact)
    runtime_ids = {
        evidence.id for evidence in episode.evidence if evidence.kind == "bt_transition"
    }
    resolved = resolve_provenance(
        bundle,
        known_runtime_evidence_ids={evidence.id for evidence in episode.evidence},
        requested_runtime_evidence_ids=runtime_ids,
    )
    plan = plan_recovery_mechanism(episode, resolved)

    args.output_dir.mkdir(parents=True)
    (args.output_dir / "provenance.json").write_text(
        json.dumps(bundle.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "bounded-source-context.json").write_text(
        json.dumps(
            {
                "schema": "crane-explain-bounded-source-context/v1",
                "runtime_evidence_ids": sorted(runtime_ids),
                "artifacts": [item.__dict__ for item in resolved.artifacts],
                "anchors": [item.__dict__ for item in resolved.anchors],
                "links": [item.__dict__ for item in resolved.links],
                "unresolved_runtime_evidence_ids": resolved.unresolved_runtime_evidence_ids,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "checked-answer-plan.json").write_text(
        json.dumps(plan.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    audit = {
        "schema": "crane-explain-provenance-pilot-audit/v1",
        "episode_id": episode.episode_id,
        "status": "PASS",
        "inputs": {
            "structured_episode_sha256": sha256(episode_payload),
            "capture_manifest_sha256": sha256(capture_manifest_payload),
            "captured_bt_xml_sha256": sha256(captured),
            "git_bt_xml_sha256": sha256(committed),
        },
        "source_identity": {
            "repository": args.repository_url,
            "commit": args.commit,
            "path": args.repository_path,
            "byte_identical_to_capture": True,
        },
        "limitations": [
            "This proves the exact BT configuration artifact, not a Nav2 binary rebuild.",
            "BT node UIDs are episode-local and are not stable source identifiers.",
            "The BT topic can omit terminal-tick transitions under the audited Nav2 version.",
            "The source anchor establishes configured control flow, not physical failure cause.",
        ],
    }
    (args.output_dir / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
