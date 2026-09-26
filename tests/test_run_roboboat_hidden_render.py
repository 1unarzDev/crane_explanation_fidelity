import json
import os
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "run_roboboat_hidden_render.sh"


def _write_fake_hyprctl(path: Path, workspace: str, monitor: int) -> None:
    state = path.parent / "headless-created"
    calls = path.parent / "hyprctl-calls"
    payload = json.dumps(
        [
            {
                "address": "0xboat",
                "class": "CRANE.x86_64",
                "title": "ASV",
                "workspace": {"name": workspace},
                "monitor": monitor,
                "mapped": True,
            }
        ]
    )
    path.write_text(
        "#!/usr/bin/env bash\n"
        f"printf '%s\\n' \"$*\" >>'{calls}'\n"
        "case \"$1\" in\n"
        "  eval|keyword|reload) exit 0 ;;\n"
        "  getoption) printf '%s\\n' 'int: 15' ;;\n"
        f"  clients) printf '%s\\n' '{payload}' ;;\n"
        f"  monitors) if [[ -e '{state}' ]]; then printf '%s\\n' "
        "'[{\"id\":1,\"name\":\"DP-2\",\"activeWorkspace\":{\"name\":\"2\"}},"
        "{\"id\":9,\"name\":\"HEADLESS-9\",\"activeWorkspace\":{\"name\":\"99\"}}]'; "
        "else printf '%s\\n' '[{\"id\":1,\"name\":\"DP-2\","
        "\"activeWorkspace\":{\"name\":\"2\"}}]'; fi ;;\n"
        "  workspaces) printf '%s\\n' '[{\"name\":\"99\",\"monitor\":"
        "\"HEADLESS-9\",\"windows\":0}]' ;;\n"
        f"  output) if [[ \"$2\" == create ]]; then touch '{state}'; "
        f"elif [[ \"$2\" == remove ]]; then rm -f '{state}'; fi ;;\n"
        "  *) exit 2 ;;\n"
        "esac\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _run(tmp_path: Path, workspace: str, monitor: int = 9) -> subprocess.CompletedProcess[str]:
    hyprctl = tmp_path / "hyprctl"
    _write_fake_hyprctl(hyprctl, workspace, monitor)
    env = os.environ | {
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "HYPRLAND_INSTANCE_SIGNATURE": "test-instance",
        "CRANE_NOGRAPHICS": "0",
    }
    return subprocess.run(
        [str(WRAPPER), "bash", "-c", "sleep 0.1"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_accepts_rendered_window_on_virtual_headless_output(tmp_path: Path) -> None:
    result = _run(tmp_path, "99")
    assert result.returncode == 0, result.stderr
    calls = (tmp_path / "hyprctl-calls").read_text()
    assert "output create headless" in calls
    assert "output remove HEADLESS-9" in calls
    assert "reload config-only" in calls


def test_fails_closed_if_rendered_window_maps_to_visible_workspace(tmp_path: Path) -> None:
    result = _run(tmp_path, "2", monitor=1)
    assert result.returncode == 1
    assert "escaped headless output" in result.stderr


def test_rejects_nographics_even_when_window_hiding_is_requested(tmp_path: Path) -> None:
    env = os.environ | {"CRANE_NOGRAPHICS": "1"}
    result = subprocess.run(
        [str(WRAPPER), "true"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "requires CRANE_NOGRAPHICS=0" in result.stderr


def test_preserves_rendered_graphics_contract() -> None:
    text = WRAPPER.read_text()
    assert "output create headless" in text
    assert "output remove" in text
    assert "render_unfocused = true" in text
    assert 'suppress_event = \\"activate activatefocus\\"' in text
    assert "misc:render_unfocused_fps" in text
    executable_lines = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    assert not any("-nographics" in line for line in executable_lines)
    assert not any("-batchmode" in line for line in executable_lines)
