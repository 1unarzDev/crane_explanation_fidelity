#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd "${script_dir}/.." && pwd)"

violations="$(git -C "${workspace_root}" ls-files \
    'data/robot_visible/**' 'data/evaluator_only/**' \
    | grep -Ev '(^data/(robot_visible|evaluator_only)/\.gitkeep$)' || true)"
if [[ -n "${violations}" ]]; then
    echo "Raw governed data is tracked by Git:" >&2
    echo "${violations}" >&2
    exit 1
fi

for component in packages/astro_dock packages/crane_ml; do
    if [[ -n "$(git -C "${workspace_root}/${component}" status --porcelain)" ]]; then
        echo "Dirty component checkout: ${component}" >&2
        exit 1
    fi
done

echo "Data governance check passed"
