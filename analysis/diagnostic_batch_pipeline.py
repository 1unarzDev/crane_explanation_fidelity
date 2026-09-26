#!/usr/bin/env python3
"""Durable coordinator for existing diagnostic pipeline adapters.

The coordinator owns only claims, transitions, backpressure, and ordered release. Scientific
work remains in the hash-frozen capture, reference, answer, judge, and monitor runners.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any, Iterator


PLAN_SCHEMA = "crane-diagnostic-batch-plan/v1"
LEDGER_SCHEMA = "crane-diagnostic-batch-ledger/v1"


def now() -> datetime:
    return datetime.now(timezone.utc)


def stamp(value: datetime | None = None) -> str:
    return (value or now()).isoformat().replace("+00:00", "Z")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as out:
        json.dump(value, out, indent=2, sort_keys=True)
        out.write("\n")
        temporary = Path(out.name)
    temporary.replace(path)


@contextmanager
def locked_ledger(path: Path) -> Iterator[dict[str, Any]]:
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        value = json.loads(path.read_text(encoding="utf-8"))
        yield value
        atomic_write(path, value)


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema") != PLAN_SCHEMA:
        raise ValueError("unexpected batch plan schema")
    jobs = plan.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("batch plan requires jobs")
    ids = [item.get("job_id") for item in jobs]
    if any(not isinstance(item, str) or not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("job IDs must be unique nonempty strings")
    id_set = set(ids)
    identities = [item.get("request_identity") for item in jobs]
    if len(identities) != len(set(identities)):
        raise ValueError("logical request identities must be unique")
    for job in jobs:
        if job.get("pool") not in plan.get("pool_limits", {}):
            raise ValueError(f"unknown pool for {job['job_id']}")
        if any(item not in id_set for item in job.get("dependencies", [])):
            raise ValueError(f"unknown dependency for {job['job_id']}")
        identity = job.get("request_identity")
        if not isinstance(identity, str) or len(identity) != 64:
            raise ValueError(f"invalid request identity for {job['job_id']}")


def initialize(plan_path: Path, ledger_path: Path) -> dict[str, Any]:
    if ledger_path.exists():
        raise FileExistsError("refusing to overwrite batch ledger")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    validate_plan(plan)
    ledger = {
        "schema": LEDGER_SCHEMA,
        "plan_id": plan["plan_id"],
        "plan_path": str(plan_path.resolve()),
        "plan_sha256": digest(plan_path),
        "created_utc": stamp(),
        "updated_utc": stamp(),
        "jobs": {
            item["job_id"]: {
                **item,
                "state": "QUEUED",
                "attempts": [],
                "claim": None,
                "artifact_manifest": None,
            }
            for item in plan["jobs"]
        },
        "releases": [],
    }
    atomic_write(ledger_path, ledger)
    return ledger


def _expired(claim: dict[str, Any], when: datetime) -> bool:
    return datetime.fromisoformat(claim["expires_utc"].replace("Z", "+00:00")) <= when


def claim(ledger_path: Path, pool: str, worker: str, lease_seconds: int) -> dict[str, Any] | None:
    with locked_ledger(ledger_path) as ledger:
        plan = json.loads(Path(ledger["plan_path"]).read_text(encoding="utf-8"))
        if digest(Path(ledger["plan_path"])) != ledger["plan_sha256"]:
            raise ValueError("batch plan changed after ledger initialization")
        when = now()
        jobs = ledger["jobs"]
        for item in jobs.values():
            if item["state"] == "RUNNING" and item["claim"] and _expired(item["claim"], when):
                item["state"] = "QUEUED"
                item["claim"] = None
        active = sum(
            item["state"] == "RUNNING" and item["pool"] == pool for item in jobs.values()
        )
        if pool not in plan["pool_limits"]:
            raise ValueError("unknown pool")
        if active >= int(plan["pool_limits"][pool]):
            return None
        completed = {job_id for job_id, item in jobs.items() if item["state"] == "COMPLETED"}
        ready = sorted(
            (
                item for item in jobs.values()
                if item["pool"] == pool
                and item["state"] == "QUEUED"
                and set(item.get("dependencies", [])) <= completed
            ),
            key=lambda item: (item["sequence_index"], item["job_id"]),
        )
        if not ready:
            return None
        item = ready[0]
        attempt = len(item["attempts"]) + 1
        item["state"] = "RUNNING"
        item["claim"] = {
            "worker": worker,
            "attempt": attempt,
            "claimed_utc": stamp(when),
            "expires_utc": stamp(when + timedelta(seconds=lease_seconds)),
        }
        item["attempts"].append({**item["claim"], "status": "RUNNING"})
        ledger["updated_utc"] = stamp(when)
        return {key: value for key, value in item.items() if key not in {"attempts"}}


def complete(
    ledger_path: Path, job_id: str, worker: str, artifact_manifest_path: Path
) -> dict[str, Any]:
    manifest = json.loads(artifact_manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "crane-diagnostic-batch-artifact-manifest/v1":
        raise ValueError("unexpected artifact manifest schema")
    with locked_ledger(ledger_path) as ledger:
        item = ledger["jobs"].get(job_id)
        if item is None:
            raise ValueError("unknown job")
        if item["state"] != "RUNNING" or item.get("claim", {}).get("worker") != worker:
            raise ValueError("only the current claim owner may complete a running job")
        if manifest.get("job_id") != job_id:
            raise ValueError("artifact manifest job mismatch")
        if manifest.get("request_identity") != item["request_identity"]:
            raise ValueError("artifact manifest request identity mismatch")
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError("artifact manifest is empty")
        for artifact in artifacts:
            path = Path(artifact["path"]).resolve(strict=True)
            if path.stat().st_size != artifact.get("bytes") or digest(path) != artifact.get("sha256"):
                raise ValueError(f"artifact hash/size mismatch: {path}")
        item["state"] = "COMPLETED"
        item["attempts"][-1]["status"] = "COMPLETED"
        item["attempts"][-1]["completed_utc"] = stamp()
        item["artifact_manifest"] = {
            "path": str(artifact_manifest_path.resolve()),
            "sha256": digest(artifact_manifest_path),
        }
        item["claim"] = None
        ledger["updated_utc"] = stamp()
        return {"job_id": job_id, "state": item["state"]}


def release(ledger_path: Path, arm: str, eligible_n: int) -> dict[str, Any]:
    with locked_ledger(ledger_path) as ledger:
        plan = json.loads(Path(ledger["plan_path"]).read_text(encoding="utf-8"))
        if eligible_n not in plan.get("registered_looks", {}).get(arm, []):
            raise ValueError("requested release is not a registered look")
        if any(item["arm"] == arm and item["eligible_n"] == eligible_n for item in ledger["releases"]):
            raise ValueError("registered look was already released")
        reconcile = sorted(
            (
                item for item in ledger["jobs"].values()
                if item["arm"] == arm and item["stage"] == "reconcile"
            ),
            key=lambda item: (item["sequence_index"], item["configuration_id"]),
        )
        prefix: list[dict[str, Any]] = []
        eligible = 0
        for item in reconcile:
            prefix.append(item)
            eligible += int(item.get("primary_endpoint_eligible") is True)
            if eligible == eligible_n:
                break
        if eligible != eligible_n:
            raise ValueError("registered eligible count is absent from the plan")
        incomplete = [item["configuration_id"] for item in prefix if item["state"] != "COMPLETED"]
        if incomplete:
            raise ValueError("ordered release prefix is incomplete: " + ", ".join(incomplete))
        record = {
            "arm": arm,
            "eligible_n": eligible_n,
            "released_utc": stamp(),
            "configuration_ids": [item["configuration_id"] for item in prefix],
            "last_sequence_index": prefix[-1]["sequence_index"],
        }
        ledger["releases"].append(record)
        ledger["updated_utc"] = record["released_utc"]
        return record


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--plan", required=True, type=Path)
    init.add_argument("--ledger", required=True, type=Path)
    get = commands.add_parser("claim")
    get.add_argument("--ledger", required=True, type=Path)
    get.add_argument("--pool", required=True)
    get.add_argument("--worker", required=True)
    get.add_argument("--lease-seconds", type=int, default=3600)
    done = commands.add_parser("complete")
    done.add_argument("--ledger", required=True, type=Path)
    done.add_argument("--job-id", required=True)
    done.add_argument("--worker", required=True)
    done.add_argument("--artifact-manifest", required=True, type=Path)
    publish = commands.add_parser("release")
    publish.add_argument("--ledger", required=True, type=Path)
    publish.add_argument("--arm", required=True)
    publish.add_argument("--eligible-n", required=True, type=int)
    args = parser.parse_args()
    if args.command == "init":
        result = initialize(args.plan.resolve(strict=True), args.ledger.resolve())
        print(json.dumps({"status": "INITIALIZED", "jobs": len(result["jobs"])}))
    elif args.command == "claim":
        result = claim(args.ledger.resolve(strict=True), args.pool, args.worker, args.lease_seconds)
        print(json.dumps(result or {"status": "NO_WORK"}, sort_keys=True))
    elif args.command == "complete":
        result = complete(
            args.ledger.resolve(strict=True), args.job_id, args.worker,
            args.artifact_manifest.resolve(strict=True),
        )
        print(json.dumps(result, sort_keys=True))
    else:
        print(json.dumps(release(args.ledger.resolve(strict=True), args.arm, args.eligible_n)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
