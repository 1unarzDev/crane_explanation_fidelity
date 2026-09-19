import json
from pathlib import Path

from scripts.record_build_provenance import build_record, managed_assembly_record, sha256_file


ROOT = Path(__file__).resolve().parents[1]


def test_build_record_does_not_equate_checkout_with_unproven_build_source(tmp_path) -> None:
    build_dir = tmp_path / "worker"
    build_dir.mkdir()
    player = build_dir / "CRANE.x86_64"
    player.write_bytes(b"player-artifact")
    managed = build_dir / "CRANE_Data" / "Managed"
    managed.mkdir(parents=True)
    (managed / "PhysicsAssembly.dll").write_bytes(b"physics-v1")
    (managed / "UtilsAssembly.dll").write_bytes(b"utils-v1")
    manifest = {"schema": "crane-build-manifest-v1", "assetSetHash": "ABC123"}
    manifest_path = build_dir / "crane-build-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    record = build_record(player, ROOT)

    assert record["player"]["sha256"] == sha256_file(player)
    assert record["managed_assemblies"] == managed_assembly_record(player)
    assert record["managed_assemblies"]["assembly_count"] == 2
    assert record["managed_assemblies"]["physics_assembly_sha256"] == sha256_file(
        managed / "PhysicsAssembly.dll"
    )
    assert record["build_manifest"]["content"] == manifest
    assert record["checkout_at_run"]["commit"]
    assert record["build_source_commit"] is None
    assert record["build_source_commit_proven"] is False
    assert "must not be represented" in record["provenance_limit"]
