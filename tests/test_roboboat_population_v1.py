import copy
import json
from pathlib import Path
import pytest
import generate_roboboat_population_v1 as population
from run_roboboat_population_development_v1 import technical_checks


def test_sampling_reproducible_and_variants_share_physical_identity(tmp_path, monkeypatch):
    root = tmp_path / 'repo'
    doc = root / 'docs'
    doc.mkdir(parents=True)
    source = population.DOC / 'task_contract_v2.json'
    (doc / source.name).write_bytes(source.read_bytes())
    config = root / 'packages/crane_ml/Tools/Performance/roboboat_terminal_v1.yaml'
    config.parent.mkdir(parents=True)
    config.write_text('configuration')
    # Generator source identity is itself a declared file inside the isolated test repo.
    script = root / 'generate.py'; script.write_text('fixture source')
    monkeypatch.setattr(population, 'ROOT', root)
    monkeypatch.setattr(population, 'DOC', doc)
    monkeypatch.setattr(population, '__file__', str(script))
    a = population.generate(root/'population-a', 12, 42001)
    b = population.generate(root/'population-b', 12, 42001)
    assert len(a['clusters']) == 12
    assert len({r['cluster_id'] for r in a['rows']}) == 12
    assert len({r['id'] for r in a['rows']}) == 24
    assert {c['family'] for c in a['clusters']} == set(population.FAMILIES)
    for first, second in zip(a['rows'], b['rows']):
        assert first['goal'] == second['goal']
        assert first['geometry'] == second['geometry']
    for cluster in a['clusters']:
        rows = [r for r in a['rows'] if r['cluster_id'] == cluster['cluster_id']]
        assert {r['internal_xy_tolerance_m'] for r in rows} == {0.2, 0.4}
        assert rows[0]['goal'] == rows[1]['goal']
        assert rows[0]['task_contract'] == rows[1]['task_contract']
        contract = json.loads((root/rows[0]['task_contract']['path']).read_text())
        assert contract['berth_center'] == json.loads(source.read_text())['berth_center']
        assert contract['goal'] == rows[0]['goal']
        if 'path_file' in rows[0]:
            path = json.loads((root/rows[0]['path_file']['path']).read_text())
            assert path['poses'][-1] == contract['goal']
    with pytest.raises(FileExistsError): population.generate(root/'population-a', 12, 42001)
    with pytest.raises(ValueError): population.generate(root/'confirmation', 12, 50001, 'confirmation')


def clean_capture():
    timing = {'acceptedActions': 10, 'knownSourceActions': 10,
              'maximumSourceToApplicationTicks': 2, 'maximumReceiveToApplicationTicks': 1}
    worker = {'valid': True, 'actionTiming': timing, 'acceptedActions': 10,
              **{k: 0 for k in ('rejectedActions', 'staleActions', 'crossEpisodeActions', 'loggedErrors',
                                'loggedExceptions', 'invalidWaterSearches', 'staleObservations', 'failedObservations')}}
    summary = {'transport': {'duplicateNodeRegistrations': 0, 'endpointErrors': 0,
                            'maximumConcurrentUnityConnections': 1, 'activeConnectionsAtShutdown': 0}}
    return summary, worker, {'status': 'succeeded', 'trajectory': [{}]}


@pytest.mark.parametrize('status', ['succeeded', 'aborted', 'canceled', 'timeout'])
def test_valid_unexpected_navigation_outcomes_retained(status):
    summary, worker, fixture = clean_capture(); fixture['status'] = status
    assert all(technical_checks(summary, worker, fixture).values())


@pytest.mark.parametrize('field', ['staleObservations', 'failedObservations', 'rejectedActions', 'invalidWaterSearches'])
def test_sensor_transport_failure_cannot_be_hidden_by_success(field):
    summary, worker, fixture = clean_capture(); worker[field] = 1
    assert not all(technical_checks(summary, worker, fixture).values())


def test_unknown_lag_is_not_valid():
    summary, worker, fixture = clean_capture()
    del worker['actionTiming']['maximumReceiveToApplicationTicks']
    assert not all(technical_checks(summary, worker, fixture).values())
