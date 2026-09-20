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

required=(R2_ACCOUNT_ID R2_BUCKET R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY)
for name in "${required[@]}"; do
    if [[ -z "${!name:-}" ]]; then
        echo "Missing required environment variable: ${name}" >&2
        exit 2
    fi
done

prefix="${R2_PREFIX:-crane-explanation-fidelity}"
endpoint="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

cd "${workspace_root}"
python3 scripts/check_dvc_r2_budget.py --operation status

# Bucket identity and all credentials are local because account/bucket names can reveal deployment
# details and credentials must never enter Git. .dvc/config.local is ignored by DVC initialization.
dvc remote add --local --force --default r2 "s3://${R2_BUCKET}/${prefix}"
dvc remote modify --local r2 endpointurl "${endpoint}"
dvc remote modify --local r2 region auto
dvc remote modify --local r2 access_key_id "${R2_ACCESS_KEY_ID}"
dvc remote modify --local r2 secret_access_key "${R2_SECRET_ACCESS_KEY}"
dvc remote modify --local r2 jobs 1
dvc remote modify --local r2 verify true

echo "Configured local DVC remote 'r2' for bucket ${R2_BUCKET} and prefix ${prefix}."
echo "Credentials were written only to ignored .dvc/config.local."
echo "Run scripts/dvc_r2_sync.sh status before the first transfer."
