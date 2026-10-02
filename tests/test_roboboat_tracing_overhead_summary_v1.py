import json
import pytest
from summarize_roboboat_tracing_overhead_v1 import summarize, binding


def test_failure_and_missing_measurements_remain_in_fixed_denominator(tmp_path):
    root=tmp_path/'captures';root.mkdir();d={'output_root':str(root),'schedule':[{'operational_run_id':f'boat-reliability-{i}','trace_enabled':toggle} for i,toggle in enumerate((True,False,False,True))]}
    path=tmp_path/'declaration.json';path.write_text(json.dumps(d));results=[]
    for u in d['schedule']:
        record={'row':{'id':u['operational_run_id']},'trace_enabled':u['trace_enabled'],'new_independent_n':0,'status':'TECHNICAL_FAILURE','error':'retained missing worker'}
        results.append(record);out=root/u['operational_run_id'];out.mkdir();(out/'capture-attempt.json').write_text(json.dumps(record))
    terminal={'status':'RELIABILITY_ASSAY_FINISHED','declaration_sha256':binding(path)['sha256'],'results':results}
    (root/'terminal.json').write_text(json.dumps(terminal))
    result=summarize(path)
    assert len(result['runs'])==4 and all(r['measurements']=={} for r in result['runs'])
    assert result['all_declared_runs_retained'] and not result['performance_equivalence_established']
    terminal['results'].pop();(root/'terminal.json').write_text(json.dumps(terminal))
    with pytest.raises(ValueError,match='all declared runs'):summarize(path)
