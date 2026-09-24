import hashlib
import json
from pathlib import Path
import subprocess

from analysis.validate_diagnostic_player_build import validate_build


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "analysis" / "validate_diagnostic_player_build.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path: Path) -> tuple[Path, Path, Path, dict]:
    checkout = tmp_path / "checkout"
    source = checkout / "Assets/Scripts/Physics/Land/CraneReferenceWarehouse.cs"
    scene = checkout / "Assets/Scenes/TurtleBot3 Warehouse Validation.unity"
    source.parent.mkdir(parents=True)
    scene.parent.mkdir(parents=True)
    source.write_text("current source\n", encoding="utf-8")
    scene.write_text("current scene\n", encoding="utf-8")
    catalog = checkout / "Assets/Resources/ReferenceEnvironments/catalog.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_text('{"catalog":"current"}\n', encoding="utf-8")
    player = tmp_path / "build" / "CRANE.x86_64"
    resources = player.parent / "CRANE_Data/resources.assets"
    resources.parent.mkdir(parents=True)
    player.write_text("launcher\n", encoding="utf-8")
    resources.write_bytes(b"prefix\0" + catalog.read_bytes() + b"\0suffix")
    provenance = {
        "schema": "crane-build-run-provenance-v1",
        "build_manifest": {
            "sha256": "a" * 64,
            "content": {
                "assets": [
                    {
                        "path": "Assets/Scripts/Physics/Land/CraneReferenceWarehouse.cs",
                        "sha256": digest(source).upper(),
                        "bytes": source.stat().st_size,
                    },
                    {
                        "path": "Assets/Scenes/TurtleBot3 Warehouse Validation.unity",
                        "sha256": digest(scene).upper(),
                        "bytes": scene.stat().st_size,
                    },
                ]
            },
        },
        "managed_assemblies": {"sha256": "b" * 64},
        "checkout_at_run": {"commit": "deadbeef", "dirty": False},
        "build_source_commit_proven": False,
        "provenance_limit": "embedded source commit unavailable",
    }
    return checkout, player, catalog, provenance


def test_matching_declared_bundle_and_checkout_assets_pass(tmp_path):
    checkout, player, catalog, provenance = fixture(tmp_path)

    result = validate_build(
        provenance, checkout, "a" * 64, "b" * 64, player, catalog
    )

    assert result["accepted"] is True
    assert result["failed_checks"] == []
    assert result["source_commit_proven"] is False


def test_stale_embedded_warehouse_source_fails_closed(tmp_path):
    checkout, player, catalog, provenance = fixture(tmp_path)
    provenance["build_manifest"]["content"]["assets"][0]["sha256"] = "0" * 64

    result = validate_build(
        provenance, checkout, "a" * 64, "b" * 64, player, catalog
    )

    assert result["accepted"] is False
    assert "warehouse_source_hash_matches_checkout" in result["failed_checks"]


def test_wrong_declared_assembly_set_fails_closed(tmp_path):
    checkout, player, catalog, provenance = fixture(tmp_path)

    result = validate_build(
        provenance, checkout, "a" * 64, "c" * 64, player, catalog
    )

    assert result["accepted"] is False
    assert "declared_managed_assemblies" in result["failed_checks"]


def test_cli_retains_rejected_audit(tmp_path):
    checkout, player, catalog, provenance = fixture(tmp_path)
    provenance_path = tmp_path / "provenance.json"
    output = tmp_path / "audit.json"
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")

    completed = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--provenance",
            str(provenance_path),
            "--checkout",
            str(checkout),
            "--player",
            str(player),
            "--catalog",
            str(catalog),
            "--expected-build-manifest-sha256",
            "f" * 64,
            "--expected-managed-assemblies-sha256",
            "b" * 64,
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert output.is_file()
    assert json.loads(output.read_text(encoding="utf-8"))["accepted"] is False


def test_missing_exact_catalog_payload_fails_closed(tmp_path):
    checkout, player, catalog, provenance = fixture(tmp_path)
    (player.parent / "CRANE_Data/resources.assets").write_bytes(b"different catalog")

    result = validate_build(
        provenance, checkout, "a" * 64, "b" * 64, player, catalog
    )

    assert result["accepted"] is False
    assert "exact_catalog_embedded" in result["failed_checks"]
