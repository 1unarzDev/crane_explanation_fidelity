import copy
import json
from pathlib import Path

import pytest

from analysis.hexar_external.acquisition.reliability_native_batch import write_derived
from analysis.hexar_external.acquisition.reliability_review import execute, schedule

ROOT = Path(__file__).resolve().parents[2]


def fixture():
    plan = json.loads((ROOT / 'manifests/hexar_external/acquisition/development_episode_plan_v16.json').read_text())
    receipts = [dict(episode_id=r['episode_id'], method_outputs_generated=False,
                     judge_labels_generated=False) for r in plan['records']]
    run = dict(phase='development_only', status='DEVELOPMENT_RUNS_RECORDED_UNQUALIFIED', episodes=receipts)
    return plan, run


def test_reliability_review_requires_every_original_attempt_and_no_semantic_exposure():
    plan, run = fixture()
    schedule(plan, run)
    for change in ('live', 'missing', 'reordered', 'exposed', 'replaced'):
        p, r = copy.deepcopy((plan, run))
        if change == 'live':
            r['status'] = 'IN_PROGRESS'
        elif change == 'missing':
            r['episodes'].pop()
        elif change == 'reordered':
            r['episodes'].reverse()
        elif change == 'exposed':
            r['episodes'][0]['judge_labels_generated'] = True
        else:
            r['episodes'][0]['episode_id'] = 'substituted'
        with pytest.raises(ValueError):
            schedule(p, r)


def test_live_run_is_rejected_before_any_extraction_or_report_namespace(tmp_path):
    plan, run = fixture(); run['status'] = 'IN_PROGRESS'
    p, r = tmp_path / 'plan.json', tmp_path / 'run.json'
    p.write_text(json.dumps(plan)); r.write_text(json.dumps(run))
    out = tmp_path / 'new-report'
    with pytest.raises(ValueError, match='live runs cannot be scored'):
        execute(p, r, out)
    assert not out.exists()


def test_derived_reproduction_keeps_original_bytes_and_refuses_differences(tmp_path):
    path = tmp_path / 'derived.json'
    write_derived(path, {'event': 1})
    before = path.read_bytes()
    write_derived(path, {'event': 1})
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match='differs from raw reproduction'):
        write_derived(path, {'event': 2})
    assert path.read_bytes() == before
