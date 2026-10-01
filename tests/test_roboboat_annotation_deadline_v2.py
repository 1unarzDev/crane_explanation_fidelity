import json
from types import SimpleNamespace
import pytest
import roboboat_annotation_deadline_v2 as deadline
import run_roboboat_full_population_inventory_v3 as inventory
import run_roboboat_full_population_support_v3 as support
from test_roboboat_full_population_inventory_v2 import population


def test_fresh_inventory_declares_deadline_and_binds_adapter(tmp_path):
    declaration, root, _ = population(tmp_path)
    result = inventory.prepare(declaration,root,tmp_path/'bank',tmp_path/'inventory.json')
    assert result['timeout_s'] == 600 and result['quality_retries'] == 0
    assert result['schema'].endswith('/v3')
    assert '600-second' in result['execution_contract']['scientific_settings']
    assert any(x['path'].endswith('roboboat_annotation_deadline_v2.py') for x in result['dependencies'])
    assert support.inventory is inventory


def test_extractor_changes_only_deadline_and_preserves_model_tools_no_retry(monkeypatch,tmp_path):
    calls=[]
    freeze=json.loads((deadline.safe.atomizer.DOC/'marine_atomization_freeze_v5.json').read_text())
    def call(cache,role,work,prompt,model,effort,schema,**kwargs):
        calls.append(role)
        assert kwargs == {'allow_tools':False,'timeout':600}
        assert model == freeze['candidate']['model'] and effort == freeze['candidate']['reasoning_effort']
        assert 'private-gold' not in prompt
        entry=json.loads((work/'response.json').read_text())
        return {'cache_key':'fake','parsed_final':{
            'schema':'crane-evidence-calibration-atomization-return/v1',
            'opaque_response_id':entry['opaque_response_id'],'claims':[{
                'response_span':'Outcome unknown.','claim_text':'Outcome unknown.','asserted_abstraction_level':'task_outcome'}],
            'unresolved_spans':[],'attestation':'METHOD_BLIND_EXHAUSTIVE_EXTRACTION_ATTEMPT'}}
    monkeypatch.setattr(deadline.extraction_transport,'call',call)
    case={'case_id':'opaque','response_text':'Outcome unknown.','expected':'private-gold'}
    first=deadline.safe_execute(case,'A',freeze,tmp_path)
    assert deadline.safe_execute(case,'A',freeze,tmp_path) == first and len(calls) == 1


def test_support_rejects_undeclared_deadline(monkeypatch):
    with pytest.raises(ValueError,match='declaration'):
        deadline.safe_annotate('packet','output',caller=SimpleNamespace(timeout_s=300))
    monkeypatch.setattr(deadline.safe,'qualified_annotate',lambda *a,**k: 'same-qualified-logic')
    assert deadline.safe_annotate('packet','output',caller=SimpleNamespace(timeout_s=600)) == 'same-qualified-logic'


def test_support_and_release_accept_fresh_600s_inventory(monkeypatch,tmp_path):
    import test_roboboat_full_population_support_v2 as support_fixture
    import test_summarize_roboboat_full_population_support_v2 as release_fixture
    import summarize_roboboat_full_population_support_v3 as release
    monkeypatch.setattr(support_fixture,'inventory',inventory)
    monkeypatch.setattr(support_fixture,'support',support)
    monkeypatch.setattr(release_fixture,'support',support)
    monkeypatch.setattr(release_fixture,'release',release)
    result=release_fixture.prepared_support(tmp_path)
    # Reuse constructed, explicitly non-scientific fixture through new real bridge.
    assert result is not None
    declarations=list(tmp_path.glob('support.json'))
    assert len(declarations)==1
    d=json.loads(declarations[0].read_text())
    assert d['timeout_s']==600 and d['schema'].endswith('/v3')
    assert any(x['path'].endswith('roboboat_annotation_deadline_v2.py') for x in d['dependencies'])


def test_decoded_escaped_credential_excluded_before_qualified_persistence(monkeypatch,tmp_path):
    import subprocess
    output=tmp_path/'answer.json'
    output.write_text('{"annotation_notes":"sec\\u0072et-value"}')
    monkeypatch.setattr(deadline.safe.transport,'provider_secret_values',lambda: ('secret-value',))
    monkeypatch.setattr(deadline.safe.transport,'isolated_run',lambda *a,**k: subprocess.CompletedProcess([],0,'',''))
    result=deadline.transport.safe_isolated_run(['codex','--output-last-message',str(output)])
    assert result.returncode==125
    assert 'secret-value' not in json.dumps(json.loads(output.read_text()))


def test_600s_support_uses_decoded_safe_runner(monkeypatch):
    caller=SimpleNamespace(timeout_s=600,runner='old')
    def annotate(*args,**kwargs):
        assert kwargs['caller'].runner is deadline.transport.safe_isolated_run
        return 'valid'
    monkeypatch.setattr(deadline.safe,'qualified_annotate',annotate)
    assert deadline.safe_annotate('packet','output',caller=caller)=='valid'


def test_escaped_credentials_in_decoded_trace_are_redacted(monkeypatch,tmp_path):
    import subprocess
    output=tmp_path/'answer.json';output.write_text('{"safe":true}')
    stdout='{"type":"sec\\u0072et-value","item":{"text":"sec\\u0072et-value"}}'
    monkeypatch.setattr(deadline.safe.transport,'provider_secret_values',lambda: ('secret-value',))
    monkeypatch.setattr(deadline.safe.transport,'isolated_run',lambda *a,**k: subprocess.CompletedProcess([],0,stdout,''))
    result=deadline.transport.safe_isolated_run(['codex','--output-last-message',str(output)])
    assert result.returncode==0
    assert 'secret-value' not in json.dumps(json.loads(result.stdout))
    events=deadline.extraction_transport.safe_events(stdout,('secret-value',))
    assert 'secret-value' not in json.dumps(events)


def test_timeout_decoded_trace_excluded(monkeypatch):
    import subprocess
    monkeypatch.setattr(deadline.safe.transport,'provider_secret_values',lambda: ('secret-value',))
    def fail(*a,**k):
        raise subprocess.TimeoutExpired(['secret-value'],600,output=b'{"type":"sec\\u0072et-value"}')
    monkeypatch.setattr(deadline.safe.transport,'isolated_run',fail)
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        deadline.transport.safe_isolated_run(['codex'],timeout=600)
    assert 'secret-value' not in json.dumps(json.loads(caught.value.output))
    assert 'secret-value' not in str(caught.value)


def test_static_runtime_closure_binds_transitive_annotation_and_release_dependencies():
    from roboboat_runtime_source_closure_v1 import source_closure
    import summarize_roboboat_full_population_support_v3 as release
    paths=source_closure([inventory.__file__, support.__file__, release.__file__])
    names={p.name for p in paths}
    assert {'validate_evidence_calibration_atomization.py','build_roboboat_terminal_batch.py',
        'summarize_roboboat_population_support_v1.py','roboboat_isolated_transport_v3.py',
        'roboboat_safe_annotation_transport_v2.py','roboboat_runtime_source_closure_v1.py'} <= names
    assert len(paths)==len(set(paths))
