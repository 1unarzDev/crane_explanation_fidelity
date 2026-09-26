#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "usage: $0 COMMAND [ARG ...]" >&2
    exit 2
}

(( $# > 0 )) || usage

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

# Aquatic evidence requires the ordinary rendered Vulkan/XWayland loop. An inactive special
# workspace eventually stopped HDRP depth readbacks during a full-length capture even with
# render_unfocused enabled. Give the window an active workspace on a compositor-owned virtual
# headless output instead. This keeps the real Vulkan surface rendered without placing it on a
# physical display; it is not Unity -batchmode or -nographics.
monitors_before="$(hyprctl monitors all -j)"
hyprctl output create headless >/dev/null
monitors_after="$(hyprctl monitors all -j)"
headless_state="$(jq -c --argjson before "${monitors_before}" '
    [.[] | select(.name as $name | ($before | map(.name) | index($name) | not)) |
      {id, name, workspace: .activeWorkspace.name}]' <<<"${monitors_after}")"
if ! jq -e 'length == 1 and .[0].name != null and .[0].workspace != null' \
    <<<"${headless_state}" >/dev/null; then
    echo "could not identify exactly one new Hyprland headless output: ${headless_state}" >&2
    exit 1
fi
headless_name="$(jq -r '.[0].name' <<<"${headless_state}")"
headless_monitor_id="$(jq -r '.[0].id' <<<"${headless_state}")"
headless_workspace="$(jq -r '.[0].workspace' <<<"${headless_state}")"
headless_windows="$(hyprctl workspaces -j | jq -r --arg monitor "${headless_name}" \
    '[.[] | select(.monitor == $monitor) | .windows] | add // 0')"
if [[ "${headless_windows}" != "0" ]]; then
    hyprctl output remove "${headless_name}" >/dev/null 2>&1 || true
    echo "new headless output captured an existing workspace with windows" >&2
    exit 1
fi

hyprctl eval \
    "hl.window_rule({ name = \"crane-headless-render\", match = { class = \"${window_class_pattern}\", title = \"^${window_title}$\" }, workspace = \"${headless_workspace} silent\", no_initial_focus = true, render_unfocused = true, suppress_event = \"activate activatefocus\" })" \
    >/dev/null

original_render_fps="$(hyprctl getoption misc:render_unfocused_fps | awk '$1 == "int:" { print $2; exit }')"
if [[ ! "${original_render_fps}" =~ ^[0-9]+$ ]]; then
    echo "could not read Hyprland misc:render_unfocused_fps" >&2
    exit 2
fi
hyprctl keyword misc:render_unfocused_fps "${render_fps}" >/dev/null

setsid --wait "$@" &
child_pid=$!
placement_verified=0

cleanup() {
    if kill -0 "${child_pid}" 2>/dev/null; then
        kill -TERM -- "-${child_pid}" 2>/dev/null || true
        wait "${child_pid}" 2>/dev/null || true
    fi
    hyprctl output remove "${headless_name}" >/dev/null 2>&1 || true
    hyprctl keyword misc:render_unfocused_fps "${original_render_fps}" >/dev/null 2>&1 || true
    # Drop the transient Lua rule so a later interactive CRANE launch is not redirected.
    hyprctl reload config-only >/dev/null 2>&1 || true
}
trap cleanup INT TERM EXIT

deadline="$(awk -v now="$(date +%s.%N)" -v timeout="${placement_timeout}" \
    'BEGIN { print now + timeout }')"
while kill -0 "${child_pid}" 2>/dev/null; do
    client_state="$(hyprctl clients -j | jq -c \
        --arg class "${window_class}" \
        --arg title "${window_title}" \
        '[.[] | select(.class == $class and .title == $title) |
          {address, class, title, workspace: .workspace.name, monitor, mapped}]')"
    if [[ "${client_state}" != "[]" ]]; then
        if ! jq -e --arg workspace "${headless_workspace}" \
            --argjson monitor "${headless_monitor_id}" \
            'length == 1 and all(.[];
              .workspace == $workspace and .monitor == $monitor and .mapped == true)' \
            <<<"${client_state}" >/dev/null; then
            echo "render window escaped headless output: ${client_state}" >&2
            exit 1
        fi
        if ! hyprctl monitors all -j | jq -e \
            --arg name "${headless_name}" --arg workspace "${headless_workspace}" \
            --argjson monitor "${headless_monitor_id}" \
            'any(.[]; .name == $name and .id == $monitor and
              .activeWorkspace.name == $workspace)' >/dev/null; then
            echo "headless render output disappeared during launch" >&2
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
hyprctl output remove "${headless_name}" >/dev/null
hyprctl keyword misc:render_unfocused_fps "${original_render_fps}" >/dev/null
hyprctl reload config-only >/dev/null 2>&1 || true
trap - INT TERM EXIT
exit "${child_status}"
