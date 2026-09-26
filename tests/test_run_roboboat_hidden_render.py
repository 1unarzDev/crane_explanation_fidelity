import json
import os
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "run_roboboat_hidden_render.sh"


def _write_fake_hyprctl(path: Path, workspace: str) -> None:
    payload = json.dumps(
        [
            {
                "address": "0xboat",
                "class": "CRANE.x86_64",
                "title": "ASV",
                "workspace": {"name": workspace},
                "mapped": True,
            }
        ]
    )
    path.write_text(
        "#!/usr/bin/env bash\n"
        "case \"$1\" in\n"
        "  eval|dispatch|keyword) exit 0 ;;\n"
        "  getoption) printf '%s\\n' 'int: 15' ;;\n"
        f"  clients) printf '%s\\n' '{payload}' ;;\n"
        "  monitors) printf '%s\\n' '[{\"specialWorkspace\":{\"name\":\"\"}}]' ;;\n"
        "  *) exit 2 ;;\n"
        "esac\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _run(tmp_path: Path, workspace: str) -> subprocess.CompletedProcess[str]:
    hyprctl = tmp_path / "hyprctl"
    _write_fake_hyprctl(hyprctl, workspace)
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


def test_accepts_rendered_window_on_unshown_special_workspace(tmp_path: Path) -> None:
    result = _run(tmp_path, "special:crane-headless")
    assert result.returncode == 0, result.stderr


def test_fails_closed_if_rendered_window_maps_to_visible_workspace(tmp_path: Path) -> None:
    result = _run(tmp_path, "2")
    assert result.returncode == 1
    assert "escaped hidden workspace" in result.stderr


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
    assert "render_unfocused = true" in text
    assert 'suppress_event = \\"activate activatefocus\\"' in text
    assert "misc:render_unfocused_fps" in text
    executable_lines = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    assert not any("-nographics" in line for line in executable_lines)
    assert not any("-batchmode" in line for line in executable_lines)
