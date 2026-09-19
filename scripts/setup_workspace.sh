#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd "${script_dir}/.." && pwd)"
lock_file="${workspace_root}/manifests/workspace.lock.json"

if [[ ! -f "${lock_file}" ]]; then
    echo "Missing workspace lock: ${lock_file}" >&2
    exit 1
fi

git -C "${workspace_root}" submodule update --init --recursive \
    packages/astro_dock packages/crane_ml

mapfile -t top_level < <(python3 - "${lock_file}" <<'PY'
import json, sys
for item in json.load(open(sys.argv[1], encoding="utf-8"))["top_level_submodules"]:
    print("\t".join((item["name"], item["path"], item["commit"])))
PY
)

for entry in "${top_level[@]}"; do
    IFS=$'\t' read -r name relative_path expected <<<"${entry}"
    actual="$(git -C "${workspace_root}/${relative_path}" rev-parse HEAD)"
    if [[ "${actual}" != "${expected}" ]]; then
        echo "${name} is ${actual}; expected ${expected}. Check the umbrella gitlink." >&2
        exit 1
    fi
done

astro_root="${workspace_root}/packages/astro_dock"
git -C "${astro_root}" submodule update --init --recursive

# These are intentionally ordinary pinned clones. Ignore them only in this local astro_dock
# checkout so the pinned top-level submodule remains clean.
exclude_file="$(git -C "${astro_root}" rev-parse --git-path info/exclude)"
for pattern in "/src/crane_explain/" "/src/crane_explain_ros/"; do
    grep -Fxq "${pattern}" "${exclude_file}" 2>/dev/null || printf '%s\n' "${pattern}" >>"${exclude_file}"
done

mapfile -t nested < <(python3 - "${lock_file}" <<'PY'
import json, sys
for item in json.load(open(sys.argv[1], encoding="utf-8"))["nested_repositories"]:
    print("\t".join((item["name"], item["path"], item["url"], item["commit"])))
PY
)

for entry in "${nested[@]}"; do
    IFS=$'\t' read -r name relative_path url expected <<<"${entry}"
    destination="${workspace_root}/${relative_path}"
    if [[ ! -d "${destination}/.git" ]]; then
        if [[ -e "${destination}" ]]; then
            echo "Refusing to replace non-repository path: ${destination}" >&2
            exit 1
        fi
        git clone --filter=blob:none --no-checkout "${url}" "${destination}"
    fi
    actual_url="$(git -C "${destination}" remote get-url origin)"
    if [[ "${actual_url}" != "${url}" ]]; then
        echo "${name} origin is ${actual_url}; expected ${url}" >&2
        exit 1
    fi
    git -C "${destination}" fetch --quiet origin "${expected}"
    git -C "${destination}" checkout --quiet --detach "${expected}"
    actual="$(git -C "${destination}" rev-parse HEAD)"
    if [[ "${actual}" != "${expected}" ]]; then
        echo "Failed to pin ${name}: got ${actual}, expected ${expected}" >&2
        exit 1
    fi
done

"${script_dir}/check_data_governance.sh"
echo "Workspace initialized at ${workspace_root}"
