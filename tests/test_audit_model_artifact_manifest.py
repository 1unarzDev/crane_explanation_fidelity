from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_model_artifact_manifest", ROOT / "analysis/audit_model_artifact_manifest.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class InventoryTests(unittest.TestCase):
    def test_inventory_is_path_and_content_sensitive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.json"
            second = root / "second.json"
            first.write_bytes(b"one")
            second.write_bytes(b"two")
            value = MODULE.inventory([("b", second), ("a", first)])
            self.assertEqual(value["file_count"], 2)
            self.assertEqual(value["bytes"], 6)
            self.assertEqual(
                value["sha256"],
                MODULE.inventory([("a", first), ("b", second)])["sha256"],
            )
            self.assertNotEqual(value["sha256"], MODULE.inventory([("x", first), ("b", second)])["sha256"])

    def test_current_per_episode_manifest_validates_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "model_outputs" / "final" / "episode" / "answer.json"
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b'{"answer":"retained"}\n')
            manifest = {
                "schema": "crane-explain-model-artifact-manifest/v1",
                "artifacts": [
                    {
                        "path": str(artifact.relative_to(root)),
                        "bytes": artifact.stat().st_size,
                        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    }
                ],
            }

            result = MODULE.audit_artifact_list_manifest(root, manifest)

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["artifact_count"], 1)

    def test_current_manifest_rejects_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "artifact.json"
            artifact.write_text(json.dumps({"answer": "retained"}))
            manifest = {
                "artifacts": [
                    {
                        "path": "artifact.json",
                        "bytes": artifact.stat().st_size,
                        "sha256": "0" * 64,
                    }
                ]
            }

            with self.assertRaisesRegex(SystemExit, "sha256 differs"):
                MODULE.audit_artifact_list_manifest(root, manifest)

    def test_current_manifest_rejects_workspace_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {
                "artifacts": [
                    {"path": "../outside.json", "bytes": 0, "sha256": hashlib.sha256().hexdigest()}
                ]
            }

            with self.assertRaisesRegex(SystemExit, "escapes workspace"):
                MODULE.audit_artifact_list_manifest(root, manifest)


if __name__ == "__main__":
    unittest.main()
