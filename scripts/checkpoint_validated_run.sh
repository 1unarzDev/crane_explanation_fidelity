#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd "${script_dir}/.." && pwd)"

if [[ $# -ne 3 ]]; then
    echo "Usage: $0 RUN_ID ROBOT_VISIBLE_DIRECTORY EVALUATOR_ONLY_DIRECTORY" >&2
    exit 2
fi
run_id="$1"
robot_directory="$2"
evaluator_directory="$3"
if [[ ! "${run_id}" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "RUN_ID may contain only letters, numbers, dot, underscore, and dash" >&2
    exit 2
fi

"${script_dir}/check_data_governance.sh"
robot_manifest="manifests/data/${run_id}.robot-visible.json"
evaluator_manifest="manifests/data/${run_id}.evaluator-only.json"
checkpoint="${workspace_root}/manifests/checkpoints/${run_id}.json"
if [[ -e "${checkpoint}" || -e "${workspace_root}/${robot_manifest}" || \
      -e "${workspace_root}/${evaluator_manifest}" ]]; then
    echo "Refusing to overwrite an existing manifest/checkpoint for ${run_id}" >&2
    exit 1
fi
"${script_dir}/build_data_manifest.py" --root "${robot_directory}" \
    --output "${robot_manifest}" --provenance "validated robot-visible run ${run_id}"
"${script_dir}/build_data_manifest.py" --root "${evaluator_directory}" \
    --output "${evaluator_manifest}" --provenance "validated evaluator-only run ${run_id}"

python3 - "${workspace_root}" <<'PY'
import json, subprocess, sys
from pathlib import Path

root = Path(sys.argv[1])
lock_path = root / "manifests/workspace.lock.json"
lock = json.loads(lock_path.read_text(encoding="utf-8"))
def head(path):
    return subprocess.check_output(
        ("git", "-C", str(root / path), "rev-parse", "HEAD"), text=True).strip()
for item in lock["top_level_submodules"]:
    item["commit"] = head(item["path"])
for item in lock["nested_repositories"]:
    if (root / item["path"]).is_dir():
        item["commit"] = head(item["path"])
lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
PY

python3 - "${workspace_root}" "${run_id}" "${robot_manifest}" \
    "${evaluator_manifest}" "${checkpoint}" <<'PY'
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

root, run_id = Path(sys.argv[1]), sys.argv[2]
robot_manifest, evaluator_manifest, output = sys.argv[3], sys.argv[4], Path(sys.argv[5])
def git(*args, cwd=root):
    return subprocess.check_output(("git", "-C", str(cwd), *args), text=True).strip()
record = {
    "schema": "crane-explain-run-checkpoint/v1",
    "run_id": run_id,
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "umbrella_parent": git("rev-parse", "HEAD"),
    "data_manifests": [robot_manifest, evaluator_manifest],
    "components": {
        path: git("rev-parse", "HEAD", cwd=root / path)
        for path in ("packages/astro_dock", "packages/crane_ml")
    },
}
for name in ("crane_explain", "crane_explain_ros"):
    path = root / "packages/astro_dock/src" / name
    if path.is_dir():
        record["components"][str(path.relative_to(root))] = git("rev-parse", "HEAD", cwd=path)
output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

git -C "${workspace_root}" add .gitmodules packages/astro_dock packages/crane_ml \
    manifests/workspace.lock.json "${robot_manifest}" "${evaluator_manifest}" \
    "manifests/checkpoints/${run_id}.json"

staged_data="$(git -C "${workspace_root}" diff --cached --name-only -- \
    data/robot_visible data/evaluator_only)"
if [[ -n "${staged_data}" ]]; then
    echo "Refusing checkpoint because governed data is staged: ${staged_data}" >&2
    exit 1
fi
git -C "${workspace_root}" commit -m "data: checkpoint validated run ${run_id}"
echo "Checkpoint committed. Push the umbrella commit after review."
