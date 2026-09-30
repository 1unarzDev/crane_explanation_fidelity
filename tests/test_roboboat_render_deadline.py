"""Exercise the actual shell deadline expression at a pinned epoch."""
from pathlib import Path
import re
import subprocess


def test_render_placement_deadline_preserves_twenty_seconds():
    root = Path(__file__).resolve().parents[1]
    script = (root / 'scripts/run_roboboat_hidden_render.sh').read_text()
    expression = re.search(r'^deadline="\$\(awk.*?\)"$', script,
                           re.MULTILINE | re.DOTALL).group()
    command = "date() { printf '1790771100.125'; }; placement_timeout=20; "
    command += expression + '\nprintf "%s" "$deadline"'
    result = subprocess.run(['bash', '-c', command], text=True,
                            capture_output=True, check=True)
    assert abs(float(result.stdout) - 1790771120.125) < .001
