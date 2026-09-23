#!/usr/bin/env bash
set -euo pipefail

workspace_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tectonic_version="0.17.0"
tectonic_archive_sha256="1a715688baf591e650c8aeb160ae934e181685eecbb38b317de30b269ac5d606"
tectonic_url="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-${tectonic_version}-x86_64-unknown-linux-gnu.tar.gz"
output_dir="${1:-${workspace_root}/output/pdf}"
tool_dir="$(mktemp -d)"

cleanup() {
  rm -rf "${tool_dir}"
}
trap cleanup EXIT

mkdir -p "${output_dir}"
curl --fail --location --silent --show-error "${tectonic_url}" \
  --output "${tool_dir}/tectonic.tar.gz"
printf '%s  %s\n' "${tectonic_archive_sha256}" "${tool_dir}/tectonic.tar.gz" \
  | sha256sum --check --status
tar -xzf "${tool_dir}/tectonic.tar.gz" -C "${tool_dir}"

"${tool_dir}/tectonic" "${workspace_root}/paper/main.tex" \
  --outdir "${output_dir}" \
  --keep-logs

pdfinfo "${output_dir}/main.pdf" | sed -n '1,24p'
