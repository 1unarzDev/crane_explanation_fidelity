#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "usage: $0 COMMAND [ARG ...]" >&2
    exit 2
}

(( $# > 0 )) || usage

workspace_name="${CRANE_HIDDEN_RENDER_WORKSPACE:-crane-headless}"
window_class="${CRANE_RENDER_WINDOW_CLASS:-CRANE.x86_64}"
window_class_pattern="${CRANE_RENDER_WINDOW_CLASS_PATTERN:-^CRANE[.]x86_64$}"
window_title="${CRANE_RENDER_WINDOW_TITLE:-ASV}"
placement_timeout="${CRANE_RENDER_WINDOW_TIMEOUT_SECONDS:-20}"
render_fps="${CRANE_RENDER_UNFOCUSED_FPS:-60}"

if [[ "${CRANE_NOGRAPHICS:-0}" == "1" ]]; then
    echo "hidden rendered RoboBoat mode requires CRANE_NOGRAPHICS=0" >&2
    exit 2
fi
if ! command -v hyprctl >/dev/null 2>&1; then
    echo "hidden rendered RoboBoat mode requires hyprctl" >&2
    exit 2
fi
if [[ -z "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]]; then
    echo "hidden rendered RoboBoat mode requires an active Hyprland session" >&2
    exit 2
fi
if [[ ! "${placement_timeout}" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    echo "CRANE_RENDER_WINDOW_TIMEOUT_SECONDS must be numeric" >&2
    exit 2
fi
if [[ ! "${render_fps}" =~ ^[1-9][0-9]*$ ]]; then
    echo "CRANE_RENDER_UNFOCUSED_FPS must be a positive integer" >&2
    exit 2
fi

# Aquatic evidence requires the ordinary rendered Vulkan/XWayland loop. Route that real window to
# an unshown special workspace before it maps; do not substitute Unity -batchmode or -nographics.
# Hyprland normally throttles invisible clients, so render_unfocused and the 60 Hz cap are required
# to preserve the validated real-time water/sensor path.
hyprctl eval \
    "hl.window_rule({ match = { class = \"${window_class_pattern}\", title = \"^${window_title}$\" }, workspace = \"special:${workspace_name} silent\", no_initial_focus = true, render_unfocused = true, suppress_event = \"activate activatefocus\" })" \
    >/dev/null

original_render_fps="$(hyprctl getoption misc:render_unfocused_fps | awk '$1 == "int:" { print $2; exit }')"
if [[ ! "${original_render_fps}" =~ ^[0-9]+$ ]]; then
    echo "could not read Hyprland misc:render_unfocused_fps" >&2
    exit 2
fi
hyprctl keyword misc:render_unfocused_fps "${render_fps}" >/dev/null

active_special="$({ hyprctl monitors -j || true; } | jq -r \
    --arg workspace "special:${workspace_name}" \
    '[.[] | .specialWorkspace.name // empty] | any(. == $workspace)')"
if [[ "${active_special}" == "true" ]]; then
    hyprctl dispatch togglespecialworkspace "${workspace_name}" >/dev/null
fi

setsid --wait "$@" &
child_pid=$!
placement_verified=0

cleanup() {
    if kill -0 "${child_pid}" 2>/dev/null; then
        kill -TERM -- "-${child_pid}" 2>/dev/null || true
        wait "${child_pid}" 2>/dev/null || true
    fi
    hyprctl keyword misc:render_unfocused_fps "${original_render_fps}" >/dev/null 2>&1 || true
}
trap cleanup INT TERM EXIT

deadline="$(awk -v now="$(date +%s.%N)" -v timeout="${placement_timeout}" \
    'BEGIN { print now + timeout }')"
while kill -0 "${child_pid}" 2>/dev/null; do
    client_state="$(hyprctl clients -j | jq -c \
        --arg class "${window_class}" \
        --arg title "${window_title}" \
        '[.[] | select(.class == $class and .title == $title) |
          {address, class, title, workspace: .workspace.name, mapped}]')"
    if [[ "${client_state}" != "[]" ]]; then
        if ! jq -e --arg workspace "special:${workspace_name}" \
            'length == 1 and all(.[]; .workspace == $workspace and .mapped == true)' \
            <<<"${client_state}" >/dev/null; then
            echo "render window escaped hidden workspace: ${client_state}" >&2
            exit 1
        fi
        active_special="$(hyprctl monitors -j | jq -r \
            --arg workspace "special:${workspace_name}" \
            '[.[] | .specialWorkspace.name // empty] | any(. == $workspace)')"
        if [[ "${active_special}" == "true" ]]; then
            echo "hidden render workspace became visible during launch" >&2
            exit 1
        fi
        placement_verified=1
        break
    fi
    if awk -v now="$(date +%s.%N)" -v deadline="${deadline}" \
        'BEGIN { exit !(now >= deadline) }'; then
        echo "timed out waiting for the rendered RoboBoat window" >&2
        exit 1
    fi
    sleep 0.05
done

if [[ "${placement_verified}" != "1" ]]; then
    wait "${child_pid}"
    child_status=$?
    echo "RoboBoat command exited before its rendered window was placement-verified" >&2
    exit "${child_status:-1}"
fi

wait "${child_pid}"
child_status=$?
hyprctl keyword misc:render_unfocused_fps "${original_render_fps}" >/dev/null
trap - INT TERM EXIT
exit "${child_status}"
