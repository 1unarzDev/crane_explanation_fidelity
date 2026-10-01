"""Prospective episode identities; never creates robot evidence or semantic labels."""
import argparse
import hashlib
import json
from pathlib import Path

FAMILIES = ("charging", "dynamic_env", "localization", "manual_joystick", "obstacle", "success")

def episode_seed(master_seed: str, phase: str, family: str, ordinal: int) -> int:
    payload = json.dumps(["hexar-tiago-acquisition/v1", master_seed, phase, family, ordinal], separators=(",", ":"))
    return int.from_bytes(hashlib.sha256(payload.encode()).digest()[:4], "big")

def make_plan(master_seed: str, per_family: int, reserve_per_family: int, phase: str = "development") -> dict:
    if phase != "development":
        raise ValueError("Confirmation allocation requires completed acquisition qualification and frozen protocol; development planner cannot admit it")
    if per_family < 1 or reserve_per_family < 0:
        raise ValueError("invalid cohort dimensions")
    records = []
    for family in FAMILIES:
        for ordinal in range(per_family + reserve_per_family):
            seed = episode_seed(master_seed, phase, family, ordinal)
            records.append({"episode_id": f"hexar-tiago-dev-{family}-{ordinal:04d}", "family": family,
                            "ordinal": ordinal, "seed": seed, "role": "primary" if ordinal < per_family else "reserve",
                            "status": "PLANNED_NOT_ACQUIRED", "independent_simulator_process": True,
                            "raw_bag_sha256": None, "semantic_outputs_generated": False})
    if len({r["seed"] for r in records}) != len(records):
        raise ValueError("seed collision: choose a different master seed before acquisition")
    return {"schema": "hexar-tiago-acquisition-plan/v1", "phase": phase, "master_seed": master_seed,
            "status": "DEVELOPMENT_ONLY", "cohort_type": "adapted simulated HEXAR external-validation benchmark",
            "unit": "independently generated simulated robot episode", "records": records,
            "reserve_rule": "ordered within-family replacement only for frozen outcome-blind technical invalidity; no semantic replacement"}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--master-seed", required=True)
    ap.add_argument("--per-family", type=int, default=1)
    ap.add_argument("--reserve-per-family", type=int, default=1)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    plan = make_plan(args.master_seed, args.per_family, args.reserve_per_family)
    with args.output.open("x") as stream:
        json.dump(plan, stream, indent=2)
        stream.write("\n")
