from __future__ import annotations

import importlib.util
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


if __name__ == "__main__":
    unittest.main()
