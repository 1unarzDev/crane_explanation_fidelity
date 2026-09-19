#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd "${script_dir}/.." && pwd)"

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 RUN_ID DATA_DIRECTORY" >&2
    exit 2
fi
run_id="$1"
data_directory="$2"
if [[ ! "${run_id}" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "RUN_ID may contain only letters, numbers, dot, underscore, and dash" >&2
    exit 2
fi

"${script_dir}/check_data_governance.sh"
manifest_relative="manifests/data/${run_id}.json"
checkpoint="${workspace_root}/manifests/checkpoints/${run_id}.json"
if [[ -e "${checkpoint}" || -e "${workspace_root}/${manifest_relative}" ]]; then
    echo "Refusing to overwrite an existing manifest/checkpoint for ${run_id}" >&2
    exit 1
fi
"${script_dir}/build_data_manifest.py" --root "${data_directory}" \
    --output "${manifest_relative}" --provenance "validated experimental run ${run_id}"

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

python3 - "${workspace_root}" "${run_id}" "${manifest_relative}" "${checkpoint}" <<'PY'
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

root, run_id, manifest, output = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4])
def git(*args, cwd=root):
    return subprocess.check_output(("git", "-C", str(cwd), *args), text=True).strip()
record = {
    "schema": "crane-explain-run-checkpoint/v1",
    "run_id": run_id,
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "umbrella_parent": git("rev-parse", "HEAD"),
    "data_manifest": manifest,
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
    manifests/workspace.lock.json "${manifest_relative}" \
    "manifests/checkpoints/${run_id}.json"

staged_data="$(git -C "${workspace_root}" diff --cached --name-only -- \
    data/robot_visible data/evaluator_only)"
if [[ -n "${staged_data}" ]]; then
    echo "Refusing checkpoint because governed data is staged: ${staged_data}" >&2
    exit 1
fi
git -C "${workspace_root}" commit -m "data: checkpoint validated run ${run_id}"
echo "Checkpoint committed. Push the umbrella commit after review."
