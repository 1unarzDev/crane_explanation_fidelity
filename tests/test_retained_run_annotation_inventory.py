from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_retained_run_annotation_inventory import build  # noqa: E402


def test_inventory_hashes_and_never_promotes_historical_packets(tmp_path: Path) -> None:
    (tmp_path / "artifacts").mkdir()
    packet = tmp_path / "artifacts/old-packet.jsonl"
    packet.write_text('{"schema":"crane-diagnostic-annotation-row/v1","episode_id":"ep-1"}\n')
    result = build(tmp_path, ("artifacts",))
    assert result["summary"]["files"] == 1
    entry = result["artifacts"][0]
    assert len(entry["sha256"]) == 64
    assert entry["new_atomic_annotation_compatibility"] == "HISTORICAL_SCHEMA_PRESERVE_LABELS_NO_AUTOMATIC_CONVERSION"
    assert result["confirmation_independent_n"] == 0


def test_masks_calls_and_passes_are_not_reported_as_independent_n(tmp_path: Path) -> None:
    (tmp_path / "model_outputs/calls").mkdir(parents=True)
    (tmp_path / "model_outputs/calls/x.json").write_text(
        '{"schema":"crane-explain-model-call/v1","episode_id":"ep-1","condition_id":"E0","pass_id":"p1"}'
    )
    result = build(tmp_path, ("model_outputs",))
    counts = result["summary"]["explicit_identifier_counts_not_sample_sizes"]
    assert counts == {"condition_id": 1, "episode_id": 1, "pass_id": 1}
    assert "independent_n" not in counts


def test_inventory_never_hashes_its_own_generated_output(tmp_path: Path) -> None:
    output = tmp_path / "manifests/study/evidence-calibration-retrospective-run-audit-v1.json"
    output.parent.mkdir(parents=True)
    output.write_text('{"schema":"old-self"}')
    (output.parent / "evidence-calibration-retrospective-findings-v1.json").write_text('{"schema":"old-findings"}')
    (output.parent / "evidence-calibration-p11-prefreeze-readiness.json").write_text('{"schema":"living-readiness"}')
    result = build(tmp_path, ("manifests",))
    assert result["artifacts"] == []
