import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "analysis" / "mask_geometric_costmap_evidence.py"
SPEC = importlib.util.spec_from_file_location("mask_geometric_costmap_evidence", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_mask_removes_only_costmap_cells_without_mutating_source():
    source = {
        "status": "aborted",
        "latestCostmapSnapshot": {
            "data": "compressed-cells",
            "dataSha256": "a" * 64,
            "frameId": "odom",
        },
    }
    masked, removed = MODULE.mask_costmap_cells(source)

    assert source["latestCostmapSnapshot"]["data"] == "compressed-cells"
    assert "data" not in masked["latestCostmapSnapshot"]
    assert masked["latestCostmapSnapshot"]["dataSha256"] == "a" * 64
    assert removed == ["/latestCostmapSnapshot/data"]


def test_mask_rejects_already_missing_cells():
    try:
        MODULE.mask_costmap_cells({"latestCostmapSnapshot": {}})
    except ValueError as error:
        assert "absent" in str(error)
    else:
        raise AssertionError("missing costmap cells were accepted")


def test_governed_partition_recognizes_both_visibility_roots():
    assert MODULE.governed_partition(
        (MODULE.ROOT / "data/robot_visible/dev/example.json").resolve()
    ) == "robot_visible"
    assert MODULE.governed_partition(
        (MODULE.ROOT / "data/evaluator_only/dev/example.json").resolve()
    ) == "evaluator_only"
    assert MODULE.governed_partition((MODULE.ROOT / "docs/example.json").resolve()) is None
