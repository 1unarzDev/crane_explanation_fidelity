from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_evidence_calibration_atomization_bank import build  # noqa: E402
from evidence_calibration_io import canonical_sha256  # noqa: E402


def test_blinded_bank_covers_fixed_pairs_and_separates_join_key() -> None:
    bank, key = build("development-bank-secret-with-32-characters")
    assert bank["response_count"] == 114
    assert len(bank["entries"]) == len(key["entries"]) == 114
    assert key["bank_sha256"] == canonical_sha256(bank)
    assert sum(row["paired_episode_analysis_eligible"] for row in key["entries"]) == 112
    assert len({row["episode_id"] for row in key["entries"] if row["paired_episode_analysis_eligible"]}) == 15
    assert all(set(row) == {"opaque_response_id", "response_text"} for row in bank["entries"])
    assert all("method_id" not in row and "condition_id" not in row for row in bank["entries"])


def test_blinding_secret_changes_ids_without_changing_response_inventory() -> None:
    left, _ = build("development-bank-secret-with-32-characters")
    right, _ = build("another-development-bank-secret-32-chars")
    assert {row["response_text"] for row in left["entries"]} == {row["response_text"] for row in right["entries"]}
    assert {row["opaque_response_id"] for row in left["entries"]}.isdisjoint(
        row["opaque_response_id"] for row in right["entries"]
    )
