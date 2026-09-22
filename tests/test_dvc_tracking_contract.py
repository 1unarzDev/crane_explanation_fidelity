from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

GOVERNED_POINTERS = {
    "data/robot_visible/dev.dvc",
    "data/robot_visible/final.dvc",
    "data/evaluator_only/dev.dvc",
    "data/evaluator_only/final.dvc",
    "data/evaluator_only/annotation_keys.dvc",
    "model_outputs.dvc",
    "research/explanation_fidelity/model_cache.dvc",
}


def test_sync_wrapper_names_every_governed_pointer():
    script = (ROOT / "scripts/dvc_r2_sync.sh").read_text(encoding="utf-8")
    for pointer in GOVERNED_POINTERS:
        assert pointer in script


def test_tracking_refresh_names_every_governed_root():
    script = (ROOT / "scripts/update_dvc_tracking.sh").read_text(encoding="utf-8")
    for pointer in GOVERNED_POINTERS:
        root = pointer.removesuffix(".dvc")
        assert root in script
