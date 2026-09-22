"""Assert that every hash-frozen study file still matches its manifest.

The Claude replication arm deliberately adds new files instead of editing frozen ones. This test
makes that discipline mechanical: if anyone edits a frozen artifact without writing an amendment
that records the new hash, the suite fails.

Amendments are applied in order, so a later amendment's corrected hash supersedes the base freeze.
Alphabetical globbing does not produce that order, because '-amendment-N.json' sorts before
'.json'.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
BASE = WORKSPACE / "manifests/study/provenance-study-freeze-v1.json"


def amendment_chain() -> list[Path]:
    chain = [BASE]
    index = 1
    while True:
        candidate = WORKSPACE / f"manifests/study/provenance-study-freeze-v1-amendment-{index}.json"
        if not candidate.is_file():
            return chain
        chain.append(candidate)
        index += 1


def authoritative_hashes() -> dict[str, tuple[str, str]]:
    latest: dict[str, tuple[str, str]] = {}
    for manifest in amendment_chain():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        for key in ("frozen_files", "files"):
            for entry in payload.get(key, []):
                latest[entry["path"]] = (entry["sha256"], manifest.name)
    return latest


def test_the_amendment_chain_is_contiguous_and_nonempty():
    chain = amendment_chain()
    assert chain[0] == BASE
    assert len(chain) == 7, "expected the base freeze plus six recorded amendments"


def test_every_frozen_file_matches_its_authoritative_hash():
    mismatched = []
    for path, (expected, source) in sorted(authoritative_hashes().items()):
        actual = hashlib.sha256((WORKSPACE / path).read_bytes()).hexdigest()
        if actual != expected:
            mismatched.append(f"{path} (pinned by {source})")
    assert not mismatched, "frozen files changed without an amendment: " + ", ".join(mismatched)


def test_the_claude_arm_runner_is_not_a_frozen_file():
    """The arm must extend the study by addition, never by editing a frozen artifact."""

    frozen = authoritative_hashes()
    assert "analysis/run_provenance_agent_pilot.py" in frozen
    assert "analysis/run_provenance_claude_arm.py" not in frozen
    assert "analysis/claude_cli_caller.py" not in frozen


def test_the_arm_declaration_exists_and_disclaims_amending_the_freeze():
    declaration = json.loads(
        (WORKSPACE / "manifests/study/provenance-claude-replication-arm-v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert declaration["amends"] is None
    assert declaration["frozen_study_unchanged"] is True
    assert declaration["relationship_to_frozen_study"]["this_arm_is_an_amendment"] is False
