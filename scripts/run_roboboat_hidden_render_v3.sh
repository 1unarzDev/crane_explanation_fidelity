#!/usr/bin/env bash
set -euo pipefail
root_dir="$(cd "$(dirname "$0")/.." && pwd)"
exec python "${root_dir}/analysis/roboboat_hidden_render_v3.py" "$@"
