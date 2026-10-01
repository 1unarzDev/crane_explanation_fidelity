"""Confirmation outputs must be impossible without a prospective frozen design."""
import json
import subprocess
import sys
from pathlib import Path


def test_unfrozen_candidate_cannot_launch_semantic_methods(tmp_path):
    root=Path(__file__).resolve().parents[1]
    freeze=tmp_path/'candidate.json'
    freeze.write_text(json.dumps({'status':'UNOBSERVED_CANDIDATES_NOT_FROZEN'}))
    result=subprocess.run([sys.executable,str(root/'analysis/run_handoff_confirmation_pairs.py'),'--freeze',str(freeze)],capture_output=True,text=True)
    assert result.returncode != 0
    assert 'No prospective scientific freeze' in result.stderr
