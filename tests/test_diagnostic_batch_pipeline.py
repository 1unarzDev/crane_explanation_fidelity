import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "analysis/diagnostic_batch_pipeline.py"


def invoke(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(CLI), *args], text=True, capture_output=True, check=False
    )


def plan(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "crane-diagnostic-batch-plan/v1",
                "plan_id": "canary",
                "pool_limits": {"cpu": 2, "r_agent": 1},
                "backpressure": {"r_agent": 2},
                "registered_looks": {"land": [2]},
                "jobs": [
                    {
                        "job_id": "a-reference",
                        "configuration_id": "a",
                        "arm": "land",
                        "sequence_index": 1,
                        "stage": "reference",
                        "pool": "cpu",
                        "dependencies": [],
                        "request_identity": "a" * 64,
                    },
                    {
                        "job_id": "b-reference",
                        "configuration_id": "b",
                        "arm": "land",
                        "sequence_index": 2,
                        "stage": "reference",
                        "pool": "cpu",
                        "dependencies": [],
                        "request_identity": "b" * 64,
                    },
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_cli_initializes_and_claims_one_job_exclusively(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    ledger = tmp_path / "ledger.json"
    plan(plan_path)

    initialized = invoke("init", "--plan", str(plan_path), "--ledger", str(ledger))
    assert initialized.returncode == 0, initialized.stderr

    first = invoke(
        "claim", "--ledger", str(ledger), "--pool", "cpu", "--worker", "worker-1"
    )
    second = invoke(
        "claim", "--ledger", str(ledger), "--pool", "cpu", "--worker", "worker-2"
    )
    assert first.returncode == second.returncode == 0
    assert json.loads(first.stdout)["job_id"] == "a-reference"
    assert json.loads(second.stdout)["job_id"] == "b-reference"


def test_complete_requires_owner_and_hash_checked_artifact_manifest(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    ledger = tmp_path / "ledger.json"
    plan(plan_path)
    assert invoke("init", "--plan", str(plan_path), "--ledger", str(ledger)).returncode == 0
    assert invoke(
        "claim", "--ledger", str(ledger), "--pool", "cpu", "--worker", "worker-1"
    ).returncode == 0
    artifact = tmp_path / "reference.json"
    artifact.write_text('{"reference": true}\n', encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "crane-diagnostic-batch-artifact-manifest/v1",
                "job_id": "a-reference",
                "request_identity": "a" * 64,
                "artifacts": [
                    {
                        "path": str(artifact),
                        "sha256": __import__("hashlib").sha256(artifact.read_bytes()).hexdigest(),
                        "bytes": artifact.stat().st_size,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    wrong = invoke(
        "complete", "--ledger", str(ledger), "--job-id", "a-reference",
        "--worker", "worker-2", "--artifact-manifest", str(manifest),
    )
    completed = invoke(
        "complete", "--ledger", str(ledger), "--job-id", "a-reference",
        "--worker", "worker-1", "--artifact-manifest", str(manifest),
    )
    duplicate = invoke(
        "complete", "--ledger", str(ledger), "--job-id", "a-reference",
        "--worker", "worker-1", "--artifact-manifest", str(manifest),
    )
    assert wrong.returncode != 0
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["state"] == "COMPLETED"
    assert duplicate.returncode != 0


def test_expired_claim_is_resumed_once_without_duplicate_completion(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    ledger = tmp_path / "ledger.json"
    plan(plan_path)
    assert invoke("init", "--plan", str(plan_path), "--ledger", str(ledger)).returncode == 0

    abandoned = invoke(
        "claim", "--ledger", str(ledger), "--pool", "cpu", "--worker", "dead-worker",
        "--lease-seconds", "0",
    )
    resumed = invoke(
        "claim", "--ledger", str(ledger), "--pool", "cpu", "--worker", "resume-worker"
    )
    assert abandoned.returncode == resumed.returncode == 0
    assert json.loads(abandoned.stdout)["job_id"] == "a-reference"
    resumed_job = json.loads(resumed.stdout)
    assert resumed_job["job_id"] == "a-reference"
    assert resumed_job["claim"]["attempt"] == 2


def test_technical_failure_retains_attempt_and_authorizes_bounded_retry(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    ledger = tmp_path / "ledger.json"
    plan(plan_path)
    assert invoke("init", "--plan", str(plan_path), "--ledger", str(ledger)).returncode == 0
    claimed = json.loads(
        invoke("claim", "--ledger", str(ledger), "--pool", "cpu", "--worker", "worker-1").stdout
    )
    artifact = tmp_path / "invalid-summary.json"
    artifact.write_text('{"valid": false}\n', encoding="utf-8")
    failure = tmp_path / "technical-failure.json"
    failure.write_text(
        json.dumps(
            {
                "schema": "crane-diagnostic-batch-technical-failure/v1",
                "job_id": claimed["job_id"],
                "reason": "capture validity gate rejected stale observations",
                "artifacts": [
                    {
                        "path": str(artifact),
                        "sha256": __import__("hashlib").sha256(artifact.read_bytes()).hexdigest(),
                        "bytes": artifact.stat().st_size,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    recorded = invoke(
        "technical-failure", "--ledger", str(ledger), "--job-id", claimed["job_id"],
        "--worker", "worker-1", "--failure-manifest", str(failure), "--retry",
    )
    assert recorded.returncode == 0, recorded.stderr
    assert json.loads(recorded.stdout)["state"] == "QUEUED"

    resumed = json.loads(
        invoke("claim", "--ledger", str(ledger), "--pool", "cpu", "--worker", "worker-2").stdout
    )
    assert resumed["job_id"] == claimed["job_id"]
    assert resumed["claim"]["attempt"] == 2
    value = json.loads(ledger.read_text(encoding="utf-8"))["jobs"][claimed["job_id"]]
    assert value["attempts"][0]["status"] == "TECHNICAL_FAILURE"
    assert value["technical_failures"][0]["retry_authorized"] is True


def test_registered_release_waits_for_complete_ordered_prefix(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    ledger = tmp_path / "ledger.json"
    jobs = []
    for index, (configuration, eligible) in enumerate(
        (("a", True), ("control", False), ("b", True)), start=1
    ):
        jobs.append(
            {
                "job_id": f"{configuration}-reconcile",
                "configuration_id": configuration,
                "arm": "land",
                "sequence_index": index,
                "primary_endpoint_eligible": eligible,
                "stage": "reconcile",
                "pool": "cpu",
                "dependencies": [],
                "request_identity": f"{index}" * 64,
            }
        )
    plan_path.write_text(
        json.dumps(
            {
                "schema": "crane-diagnostic-batch-plan/v1",
                "plan_id": "ordered-release",
                "pool_limits": {"cpu": 1},
                "backpressure": {},
                "registered_looks": {"land": [2]},
                "jobs": jobs,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert invoke("init", "--plan", str(plan_path), "--ledger", str(ledger)).returncode == 0

    for expected in ("a-reconcile", "control-reconcile"):
        claimed = json.loads(
            invoke(
                "claim", "--ledger", str(ledger), "--pool", "cpu", "--worker", "w"
            ).stdout
        )
        assert claimed["job_id"] == expected
        artifact = tmp_path / f"{expected}.json"
        artifact.write_text("{}\n", encoding="utf-8")
        manifest = tmp_path / f"{expected}-manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema": "crane-diagnostic-batch-artifact-manifest/v1",
                    "job_id": expected,
                    "request_identity": claimed["request_identity"],
                    "artifacts": [{"path": str(artifact), "sha256": __import__("hashlib").sha256(artifact.read_bytes()).hexdigest(), "bytes": artifact.stat().st_size}],
                }
            ) + "\n",
            encoding="utf-8",
        )
        assert invoke("complete", "--ledger", str(ledger), "--job-id", expected,
                      "--worker", "w", "--artifact-manifest", str(manifest)).returncode == 0

    early = invoke("release", "--ledger", str(ledger), "--arm", "land", "--eligible-n", "2")
    assert early.returncode != 0

    claimed = json.loads(invoke("claim", "--ledger", str(ledger), "--pool", "cpu", "--worker", "w").stdout)
    artifact = tmp_path / "b.json"
    artifact.write_text("{}\n", encoding="utf-8")
    manifest = tmp_path / "b-manifest.json"
    manifest.write_text(json.dumps({
        "schema": "crane-diagnostic-batch-artifact-manifest/v1", "job_id": "b-reconcile",
        "request_identity": claimed["request_identity"],
        "artifacts": [{"path": str(artifact), "sha256": __import__("hashlib").sha256(artifact.read_bytes()).hexdigest(), "bytes": artifact.stat().st_size}],
    }) + "\n", encoding="utf-8")
    assert invoke("complete", "--ledger", str(ledger), "--job-id", "b-reconcile", "--worker", "w",
                  "--artifact-manifest", str(manifest)).returncode == 0
    released = invoke("release", "--ledger", str(ledger), "--arm", "land", "--eligible-n", "2")
    assert released.returncode == 0, released.stderr
    assert json.loads(released.stdout)["configuration_ids"] == ["a", "control", "b"]


def test_init_rejects_duplicate_logical_request_identity(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    ledger = tmp_path / "ledger.json"
    plan(plan_path)
    value = json.loads(plan_path.read_text(encoding="utf-8"))
    value["jobs"][1]["request_identity"] = value["jobs"][0]["request_identity"]
    plan_path.write_text(json.dumps(value) + "\n", encoding="utf-8")

    result = invoke("init", "--plan", str(plan_path), "--ledger", str(ledger))
    assert result.returncode != 0
    assert not ledger.exists()
