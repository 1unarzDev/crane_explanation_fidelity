import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_geometric_composition_packet_v5 import build  # noqa: E402
from compose_diagnostic_hypotheses_v2 import compose  # noqa: E402
from render_diagnostic_composition_v2 import render  # noqa: E402


MASKED = (
    ROOT
    / "data/robot_visible/dev/mccv4-dev-001-mask-no-costmap-cells/"
    "geometric-route-diagnostic-v2.json"
)
SUPPORTED = ROOT / "data/robot_visible/dev/mccv4-dev-001/geometric-route-diagnostic-v2.json"
REGISTRY = json.loads((ROOT / "configs/diagnostic_composition_registry_v1.json").read_text())


def _answer(path: Path) -> str:
    raw = path.read_bytes()
    packet = build(json.loads(raw), source_sha256=hashlib.sha256(raw).hexdigest())
    certificate = compose(packet, REGISTRY)
    assert certificate["status"] == "composed"
    return render(certificate)


def test_masked_cells_state_missing_payload_without_inventing_spatial_coverage():
    answer = _answer(MASKED)
    assert "costmap cell payload is unavailable" in answer
    assert "physical trigger cannot be classified" in answer
    assert "does not cover enough" not in answer
    assert "does not cover the complete requested route" not in answer
    assert "-1.383 to 1.272 m signed lateral deviation" in answer
    assert "action succeeded" in answer.lower()


def test_supported_geometry_output_is_byte_equivalent_to_v4_semantics():
    answer = _answer(SUPPORTED)
    assert "non-traversable near x=12.425 m" in answer
    assert "does not prove global physical no-path" in answer
    assert "exact Nav2 consumption" in answer
