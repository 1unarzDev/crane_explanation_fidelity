from analysis.hexar_external.confirmatory_v1.development_unique_scoring import prepare,job,summarize


def test_missing_method_output_has_no_judge_payload_or_alias_repair():
    entries,plan,*_=prepare()
    assert len(entries)==72 and sum(e['method_status']=='VALID' for e in entries)==71
    missing=[e for e in entries if e['method_status']!='VALID']
    assert len(missing)==1 and missing[0]['method']=='HX-PROMPT' and missing[0]['payload'] is None
    assert sum(a['unique_request_id']==missing[0]['unique_request_id'] for a in plan['aliases'])>=1
    attempts={}
    for entry in entries:
        if entry['method_status']!='VALID':continue
        parsed=dict(unsupported_material=False,overlicensed_specificity=False,covered_units=[u['unit_id'] for u in entry['payload']['required_units']],rationale='Fake component fixture.',unsupported_spans=[],overlicensed_spans=[],ambiguous_spans=[])
        for slot in ('A','B'):attempts[job(entry,slot)['opaque_job']]=dict(status='VALID',parsed=parsed)
    labels,components,cells,episodes,counts=summarize(entries,plan,attempts)
    assert len(labels)==72 and len(cells)==108 and len(episodes)==6
    assert labels[missing[0]['unique_request_id']]['status']=='UNRESOLVED'
    assert all(value is None for value in components[missing[0]['unique_request_id']].values())
    assert counts==[0,0,6,0] # Conservative prompt missingness cannot create a contract win.
