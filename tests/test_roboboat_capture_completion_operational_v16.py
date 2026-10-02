import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import run_roboboat_capture_completion_operational_v16 as probe


def test_completion_marker_hash_matches_publisher_receipt():
    token = 'a' * 64
    assert probe.digest_token(token + '\n') == hashlib.sha256(token.encode()).hexdigest()
    for value in (token, token + '\n\n', 'partial\n'):
        with pytest.raises(ValueError): probe.digest_token(value)


def test_declaration_requires_fixed_zero_n_and_candidate_closure(tmp_path):
    original = {'id': 'origin', 'action_mode': 'navigate-to-pose', 'seed': 1}
    originals = tmp_path / 'original.json'
    originals.write_text(json.dumps({'rows': [original]}))
    rows = [{**original, 'id': f'op-{i}'} for i in range(4)]
    registry = tmp_path / 'registry.json'
    registry.write_text(json.dumps({'status': 'NONSTUDY_OPERATIONAL_REPLAYS_ZERO_INDEPENDENT_N', 'rows': rows}))
    build = tmp_path / 'build.json'; build.write_text('{}')
    candidate = tmp_path / 'candidate'; (candidate / 'Tools/Performance').mkdir(parents=True)
    names = ('run_nav2_controller_fixture_capture_v15.sh', 'nav2_follow_path_fixture_capture_v15.py',
             'roboboat_capture_completion_v1.py', 'run_worker.sh', 'summarize_nav2_reset.py')
    for name in names: (candidate / 'Tools/Performance' / name).write_text('fixture')
    # Inherited and candidate closure are mandatory even for zero-N probes.
    dependencies = [Path(probe.__file__), originals, registry, build]
    dependencies += [probe.ROOT / 'analysis' / name for name in (
        'export_roboboat_trace_qualified_v3.py', 'audit_roboboat_launcher_terminal_v1.py',
        'export_roboboat_population_v2.py', 'roboboat_trace_qualified_validity_v1.py',
        'audit_roboboat_trace_semantics_v1.py', 'audit_roboboat_action_trace_v1.py',
        'audit_roboboat_frame_timing_v1.py', 'roboboat_owned_player_bundle_v1.py', 'roboboat_hidden_render_v3.py')]
    dependencies += [candidate / 'Tools/Performance' / name for name in names]
    d = {'schema': 'roboboat-capture-completion-operational-declaration/v1',
         'independent_n_added': 0, 'confirmation_n': 0, 'replication_n': 0,
         'registry': str(registry), 'original_registry': str(originals),
         'rows': [r['id'] for r in rows], 'origin_rows': {r['id']: 'origin' for r in rows},
         'domain': 198, 'port': 11488, 'maximum_delta_time': .04,
         'dependencies': [{'path': str(p.resolve()), 'sha256': probe.digest(p)} for p in dependencies]}
    with patch.object(probe, 'BUILD_IDENTITY', build), patch.object(probe, 'INSTRUMENTATION_PROJECT', candidate), patch.object(probe, 'verify_player'):
        assert len(probe.validate_declaration(d, tmp_path / 'declaration.json')[2]) == 4
        missing = {**d, 'dependencies': d['dependencies'][:-1]}
        with pytest.raises(ValueError, match='candidate launch closure'): probe.validate_declaration(missing, tmp_path / 'declaration.json')
        with pytest.raises(ValueError): probe.validate_declaration({**d, 'independent_n_added': 1}, tmp_path / 'declaration.json')
        rows[0]['seed'] = 2; registry.write_text(json.dumps({'status': 'NONSTUDY_OPERATIONAL_REPLAYS_ZERO_INDEPENDENT_N', 'rows': rows}))
        with pytest.raises(ValueError): probe.validate_declaration(d, tmp_path / 'declaration.json')
