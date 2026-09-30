"""Development local-computation isolation seam; no model/provider execution."""
from __future__ import annotations

from pathlib import Path
import subprocess

from stage_evidence_calibration_workspace import verify

BWRAP = Path("/usr/bin/bwrap")
PYTHON = "/usr/bin/python3"


def command(workspace: Path, identity: dict, python_arguments: list[str]) -> list[str]:
    """Isolate primitive stdlib Python with read-only job files and private scratch/network/PIDs.

    The system /usr runtime is exposed. It still needs prospective environment binding; this
    helper is not a complete provider harness or a general security certification.
    """
    verify(workspace, identity)
    if not BWRAP.is_file() or BWRAP.is_symlink():
        raise ValueError("registered bubblewrap executable unavailable")
    if not isinstance(python_arguments, list) or not python_arguments or any(not isinstance(a, str) for a in python_arguments):
        raise ValueError("primitive Python arguments required")
    # Bind only the host's registered merged-/usr layout, never a caller-provided runtime tree.
    links = []
    for name in ("bin", "lib", "lib64"):
        path = Path("/") / name
        if not path.is_symlink() or str(path.readlink()) not in (f"usr/{name}", "usr/lib"):
            raise ValueError("unsupported runtime filesystem layout")
        links.extend(["--symlink", str(path.readlink()), "/" + name])
    return [str(BWRAP), "--unshare-all", "--die-with-parent", "--new-session",
            "--ro-bind", "/usr", "/usr", *links, "--proc", "/proc", "--dev", "/dev",
            "--tmpfs", "/tmp", "--ro-bind", str(workspace.resolve()), "/work", "--chdir", "/work",
            "--clearenv", "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "LC_ALL", "C.UTF-8",
            "--", PYTHON, "-I", "-S", "-B", *python_arguments]


def run(workspace: Path, identity: dict, python_arguments: list[str], *, timeout_seconds: int = 10) -> subprocess.CompletedProcess:
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 60:
        raise ValueError("local computation timeout must be 1–60 seconds")
    argv = command(workspace, identity, python_arguments)
    try:
        # No shell, inherited environment, extra descriptors, provider configuration or fallback.
        return subprocess.run(argv, env={}, close_fds=True, capture_output=True, text=True,
                              check=False, timeout=timeout_seconds)
    finally:
        verify(workspace, identity)
