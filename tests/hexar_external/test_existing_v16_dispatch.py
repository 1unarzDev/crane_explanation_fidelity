import json
from pathlib import Path

import pytest
from analysis.hexar_external.existing_v16_exploratory_v1.dispatch import dispatch
from analysis.hexar_external.acquisition.raw_archive_v1 import digest


def jobs(count=6):
    return [dict(job_id=f'opaque-{i}', request=dict(role='method', maximum_response_bytes=1024)) for i in range(count)]


def backend_factory(calls, before=None):
    def factory(reg):
        def backend(request):
            if before:before()
            calls.append(request)
            return dict(raw_response=b'{"answer":"test"}', stdout=b'exact', stderr=b'', returncode=0, transport_policy_passed=True)
        return backend
    return factory


def prior(tmp_path):
    path=tmp_path/'prior.json';path.write_text('{}');return {path:digest(path)}


def test_stage_receipts_precede_backend_and_shards_cover_all_jobs(tmp_path):
    calls=[];pins=prior(tmp_path);root=tmp_path/'stage'
    def inspect():
        assert (root/'pre_dispatch_receipt.json').exists()
        assert not (root/'completion_receipt.json').exists()
    results, receipt=dispatch(root,'a'*64,'methods',jobs(),pins,lambda:None,backend_factory(calls,inspect))
    assert len(calls)==6 and receipt['valid']==6 and set(results)=={r['job_id'] for r in jobs()}
    index=json.loads((root/'payloads/index.json').read_text());assert len(index['shards'])==2
    assert receipt['confirmation_authorized'] is False and receipt['confirmatory_N']==0
    with pytest.raises(FileExistsError):dispatch(root,'a'*64,'methods',jobs(),pins,lambda:None,backend_factory(calls))
    assert len(calls)==6


def test_empty_adjudication_has_explicit_closed_zero_call_stage(tmp_path):
    calls=[]
    results, receipt=dispatch(tmp_path/'stage','a'*64,'adjudication_judges',[],prior(tmp_path),lambda:None,backend_factory(calls))
    assert results=={} and receipt['attempts']==0 and calls==[]


def test_denied_source_or_changed_prerequisite_never_creates_root(tmp_path):
    pins=prior(tmp_path);calls=[]
    def deny():raise ValueError('source denied')
    with pytest.raises(ValueError,match='source denied'):
        dispatch(tmp_path/'stage','a'*64,'methods',jobs(),pins,deny,backend_factory(calls))
    assert not (tmp_path/'stage').exists()
    next(iter(pins)).write_text('{"changed":true}')
    with pytest.raises(ValueError,match='prerequisite changed'):
        dispatch(tmp_path/'stage','a'*64,'methods',jobs(),pins,lambda:None,backend_factory(calls))
    assert not (tmp_path/'stage').exists() and calls==[]


def test_changed_pre_dispatch_receipt_revokes_calls(tmp_path):
    pins=prior(tmp_path);root=tmp_path/'stage';calls=[];counter=0
    def guard():
        nonlocal counter
        counter+=1
        if (root/'pre_dispatch_receipt.json').exists():
            (root/'pre_dispatch_receipt.json').write_text('{}')
    with pytest.raises(ValueError,match='membership/chronology'):
        dispatch(root,'a'*64,'methods',jobs(),pins,guard,backend_factory(calls))
    assert calls==[] and not (root/'completion_receipt.json').exists()


def test_duplicates_and_cohort_sized_stages_are_rejected_before_mutation(tmp_path):
    pins=prior(tmp_path);calls=[]
    for bad in (jobs(25),jobs(1)*2):
        with pytest.raises(ValueError):dispatch(tmp_path/'stage','a'*64,'methods',bad,pins,lambda:None,backend_factory(calls))
    assert not (tmp_path/'stage').exists() and calls==[]


def test_transport_failure_stays_closed_without_retry(tmp_path):
    count=0
    def factory(_):
        def fail(_):
            nonlocal count
            count+=1
            raise RuntimeError('retained fixture transport failure')
        return fail
    results,receipt=dispatch(tmp_path/'stage','a'*64,'methods',jobs(1),prior(tmp_path),lambda:None,factory)
    assert count==1 and results['opaque-0']['status']=='TECHNICAL_FAILURE' and receipt['valid']==0
