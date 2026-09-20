#!/usr/bin/env python3
"""Drive the secondary Claude replication arm over retained episodes.

This resolves each episode's already-retained inputs and invokes
``analysis/run_provenance_claude_arm.py`` once per question. It captures nothing, derives nothing,
and never writes into a robot-visible or evaluator-only data root. An episode whose retained input
hashes do not match the corresponding frozen Luna result is refused, so the two arms are guaranteed
to have been given byte-identical evidence.

Existing outputs are skipped rather than overwritten, and every model call is content-addressed by
the adapter's own cache, so an interrupted batch resumes without resampling anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parent.parent
RUNNER = WORKSPACE / "analysis/run_provenance_claude_arm.py"
REPOSITORY = WORKSPACE / "packages/crane_ml"
REPOSITORY_URL = "https://github.com/1unarzDev/crane_ml.git"
QUESTION_KINDS = ("recovery-mechanism", "failure-cause")

DEVELOPMENT_EPISODES = ("e019", "e021", "e037", "e038")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def development_paths(episode: str, question_kind: str) -> dict[str, Path]:
    root = WORKSPACE / f"data/robot_visible/dev/land-nav-20260919-{episode}"
    # e037 predates the -v2 provenance layout; every other development episode uses it.
    pilot = root / "provenance-pilot-v2"
    if not (pilot / "bounded-provenance").is_dir():
        pilot = root / "provenance-pilot"
    parity = root / "provenance-pilot-v2" / question_kind
    if not parity.is_dir():
        parity = root / "provenance-parity-v2" / question_kind
    case = root / f"parity2-{question_kind}"
    return {
        "case_dir": case,
        "capture_dir": root / "capture",
        "provenance_dir": pilot / "bounded-provenance",
        "runtime_presentation": parity / "runtime-presentation.json",
        "parity_audit": parity / "information-parity-audit.json",
        "prior_a_e": case / "outputs.json",
    }


def sealed_paths(episode: str, question_kind: str) -> dict[str, Path]:
    root = WORKSPACE / f"data/robot_visible/final/{episode}"
    case = root / ("case-mechanism" if question_kind == "recovery-mechanism" else "case-cause")
    parity = root / "parity" / question_kind
    return {
        "case_dir": case,
        "capture_dir": root / "capture",
        "provenance_dir": root / "provenance",
        "runtime_presentation": parity / "runtime-presentation.json",
        "parity_audit": parity / "information-parity-audit.json",
        "prior_a_e": case / "outputs.json",
    }


def reference_result(batch: str, episode: str, question_kind: str) -> Path:
    if batch == "development":
        return (
            WORKSPACE
            / f"model_outputs/dev/provenance-model-strength-luna-v1/{episode}/{question_kind}.json"
        )
    return WORKSPACE / f"model_outputs/final/{episode}/{question_kind}.json"


def assert_identical_evidence(reference: Path, paths: dict[str, Path]) -> None:
    """Refuse to run unless this arm receives exactly the evidence the Luna arm received."""

    if not reference.is_file():
        raise SystemExit(f"no frozen reference result to compare evidence against: {reference}")
    retained = json.loads(reference.read_text(encoding="utf-8"))["information_parity"]
    mismatches = []
    if sha256(paths["runtime_presentation"]) != retained["runtime_presentation_sha256"]:
        mismatches.append("runtime presentation")
    if sha256(paths["parity_audit"]) != retained["audit_sha256"]:
        mismatches.append("information-parity audit")
    if mismatches:
        raise SystemExit(
            f"retained evidence differs from {reference.name}: {', '.join(mismatches)}"
        )


def run_one(
    batch: str,
    episode: str,
    question_kind: str,
    model: str,
    effort: str,
    cache: Path,
    output: Path,
    study_status: str,
    commit: str,
) -> dict[str, Any] | None:
    paths = development_paths(episode, question_kind) if batch == "development" else sealed_paths(
        episode, question_kind
    )
    for name, path in paths.items():
        if not path.exists():
            raise SystemExit(f"missing retained input {name}: {path}")
    assert_identical_evidence(reference_result(batch, episode, question_kind), paths)
    if output.exists():
        print(f"skip (already retained): {output.relative_to(WORKSPACE)}")
        return None
    command = [
        sys.executable,
        str(RUNNER),
        "--case-dir", str(paths["case_dir"]),
        "--capture-dir", str(paths["capture_dir"]),
        "--provenance-dir", str(paths["provenance_dir"]),
        "--runtime-presentation", str(paths["runtime_presentation"]),
        "--parity-audit", str(paths["parity_audit"]),
        "--prior-a-e", str(paths["prior_a_e"]),
        "--repository", str(REPOSITORY),
        "--repository-url", REPOSITORY_URL,
        "--commit", commit,
        "--question-kind", question_kind,
        "--cache", str(cache),
        "--output", str(output),
        "--model", model,
        "--reasoning-effort", effort,
        "--study-status", study_status,
    ]
    environment = {
        "PYTHONPATH": ":".join(
            (
                str(WORKSPACE / "packages/astro_dock/src/crane_explain/src"),
                str(WORKSPACE / "analysis"),
            )
        )
    }
    completed = subprocess.run(command, env={**os.environ, **environment}, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"arm run failed for {episode} {question_kind}")
    return json.loads(output.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", choices=("development", "sealed"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument(
        "--episodes",
        nargs="+",
        help="episode identifiers; defaults to the four development control episodes",
    )
    parser.add_argument(
        "--commit",
        default="c559932a5ebef00bfa7752511799fd904e5c9dbe",
        help="pinned crane_ml commit; must match manifests/workspace.lock.json",
    )
    args = parser.parse_args()

    lock = json.loads((WORKSPACE / "manifests/workspace.lock.json").read_text(encoding="utf-8"))
    pinned = next(
        item["commit"] for item in lock["top_level_submodules"] if item["name"] == "crane_ml"
    )
    if args.commit != pinned:
        raise SystemExit(f"commit {args.commit} is not the pinned crane_ml commit {pinned}")

    episodes = args.episodes or list(DEVELOPMENT_EPISODES)
    study_status = (
        "CLAUDE_ARM_DEVELOPMENT_MODEL_STRENGTH_CONTROL"
        if args.batch == "development"
        else "CLAUDE_ARM_SECONDARY_REPLICATION"
    )
    completed = 0
    for episode in episodes:
        for question_kind in QUESTION_KINDS:
            output = (WORKSPACE / args.output_root) / episode / f"{question_kind}.json"
            result = run_one(
                args.batch,
                episode,
                question_kind,
                args.model,
                args.reasoning_effort,
                WORKSPACE / args.cache,
                output,
                study_status,
                args.commit,
            )
            if result is not None:
                completed += 1
                print(
                    f"retained {episode} {question_kind}: "
                    f"{len(result['calls'])} calls, "
                    f"read_only_verified={result['read_only_workspace_verified']}"
                )
    print(f"{completed} new question runs retained under {args.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
