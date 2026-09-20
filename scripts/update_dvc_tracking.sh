#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd "${script_dir}/.." && pwd)"
cd "${workspace_root}"

dvc add \
    data/robot_visible/dev \
    data/robot_visible/final \
    data/evaluator_only/dev \
    data/evaluator_only/final \
    model_outputs \
    research/explanation_fidelity/model_cache

python3 scripts/check_dvc_r2_budget.py --operation push
echo "DVC pointers refreshed. Review and commit the six .dvc files before or with the run checkpoint."
