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
    assert record["build_source_dirty"] is None
    assert record["build_source_commit_proven"] is False
    assert "must not be represented" in record["provenance_limit"]


def test_build_record_proves_matching_clean_source_identity(tmp_path, monkeypatch) -> None:
    build_dir = tmp_path / "worker"
    build_dir.mkdir()
    player = build_dir / "CRANE.x86_64"
    player.write_bytes(b"player-artifact")
    managed = build_dir / "CRANE_Data" / "Managed"
    managed.mkdir(parents=True)
    (managed / "PhysicsAssembly.dll").write_bytes(b"physics-v1")
    commit = "a" * 40
    (build_dir / "crane-build-manifest.json").write_text(
        json.dumps({"sourceCommit": commit, "sourceDirty": False}), encoding="utf-8"
    )

    def fake_git_output(_checkout: Path, *arguments: str) -> str:
        return commit if arguments == ("rev-parse", "HEAD") else ""

    monkeypatch.setattr("scripts.record_build_provenance.git_output", fake_git_output)
    record = build_record(player, ROOT)

    assert record["build_source_commit"] == commit
    assert record["build_source_dirty"] is False
    assert record["build_source_commit_proven"] is True
    assert record["provenance_limit"] is None


def test_build_record_rejects_mismatched_source_identity(tmp_path, monkeypatch) -> None:
    build_dir = tmp_path / "worker"
    build_dir.mkdir()
    player = build_dir / "CRANE.x86_64"
    player.write_bytes(b"player-artifact")
    managed = build_dir / "CRANE_Data" / "Managed"
    managed.mkdir(parents=True)
    (managed / "PhysicsAssembly.dll").write_bytes(b"physics-v1")
    (build_dir / "crane-build-manifest.json").write_text(
        json.dumps({"sourceCommit": "a" * 40, "sourceDirty": False}), encoding="utf-8"
    )

    def fake_git_output(_checkout: Path, *arguments: str) -> str:
        return "b" * 40 if arguments == ("rev-parse", "HEAD") else ""

    monkeypatch.setattr("scripts.record_build_provenance.git_output", fake_git_output)
    record = build_record(player, ROOT)

    assert record["build_source_commit_proven"] is False
    assert "does not match" in record["provenance_limit"]
