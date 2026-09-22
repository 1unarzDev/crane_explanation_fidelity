#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd "${script_dir}/.." && pwd)"

if [[ -f "${workspace_root}/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${workspace_root}/.env"
    set +a
fi
cd "${workspace_root}"

if [[ $# -ne 1 || ! "$1" =~ ^(push|pull|status)$ ]]; then
    echo "Usage: $0 push|pull|status" >&2
    exit 2
fi

operation="$1"
if ! dvc remote list | awk '$1 == "r2" {found=1} END {exit !found}'; then
    echo "DVC remote 'r2' is not configured. Run scripts/configure_dvc_r2.sh first." >&2
    exit 1
fi

# Refuse all network operations unless current account-wide R2 metrics are readable and leave at
# least 10% headroom. This cannot replace a server-side cap, which R2 does not provide.
python3 scripts/check_dvc_r2_budget.py \
    --operation "${operation}" \
    --require-remote-metrics

targets=(
    data/robot_visible/dev.dvc
    data/robot_visible/final.dvc
    data/evaluator_only/dev.dvc
    data/evaluator_only/final.dvc
    data/evaluator_only/annotation_keys.dvc
    model_outputs.dvc
    research/explanation_fidelity/model_cache.dvc
)

case "${operation}" in
    push)
        dvc push --remote r2 --jobs 1 "${targets[@]}"
        ;;
    pull)
        dvc pull --remote r2 --jobs 1 "${targets[@]}"
        ;;
    status)
        dvc status --cloud --remote r2 "${targets[@]}"
        ;;
esac
