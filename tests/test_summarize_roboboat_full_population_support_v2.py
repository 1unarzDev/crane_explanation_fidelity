"""Construction labels validate gates/mapping only; no semantic study scoring."""
import json
from pathlib import Path
import pytest
import summarize_roboboat_full_population_support_v2 as release
import run_roboboat_full_population_support_v2 as support
from test_roboboat_full_population_support_v2 import reviewed_inventory
from adjudicate_evidence_calibration_annotations import compare, finalize, _values
from evidence_calibration_io import canonical_sha256


def prepared_support(tmp_path, *, fail=False):
    response_path,response_root,d,bank=reviewed_inventory(tmp_path,fail=fail)
    out=tmp_path/'support';decl=tmp_path/'support.json'
    sd=support.prepare(bank,response_path,response_root,out,decl)
    for bound in sd['packets']:
        packet_path=support.checked(bound);packet=json.loads(packet_path.read_text());key=packet_path.stem
        folder=out/'annotations'/key;folder.mkdir(parents=True)
        returns={}
        for form in packet['forms']:
            slot=form['annotator_slot']
            returned={'schema':'crane-blinded-atomic-annotation-return/v1',
                'packet_set_sha256':canonical_sha256(packet),'form_id':form['form_id'],
                'packet_id':key,'annotator_slot':slot,'annotator_id':'construction-'+slot,
                'atomic_labels':[{'item_id':a['item_id'],'label':'SUPPORTED_BY_VISIBLE_EVIDENCE','annotation_notes':None}
                                 for a in form['atomic_statements']],
                'required_unit_coverage':[{'unit_prompt':u['unit_prompt'],'communicated':True,
                                          'response_span':packet['response_text']} for u in form['required_unit_coverage']],
                'highest_asserted_abstraction_level':'task_outcome',
                'limitation_preservation':[{'limitation_prompt':l['limitation_prompt'],'preserved':True,
                                           'response_span':packet['response_text']} for l in form['limitation_preservation']],
                'false_premise_handling':'NOT_APPLICABLE','annotator_attestation':'INDEPENDENT_BLINDED_COMPLETE'}
            returns[slot]=returned;(folder/f'annotation-{slot}.json').write_text(json.dumps(returned))
        report=compare(packet,returns['A'],returns['B'])
        final=finalize(report,{'schema':'crane-blinded-atomic-annotation-adjudication/v1',
            'agreement_report_sha256':canonical_sha256(report),'adjudicator_id':'construction-C',
            'decisions':[],'attestation':'DISAGREEMENT_ONLY_BLINDED_COMPLETE'})
        (folder/'agreement.json').write_text(json.dumps(report));(folder/'final.json').write_text(json.dumps(final))
        terminal=out/'terminals'/f'{key}.json';terminal.parent.mkdir(exist_ok=True)
        terminal.write_text(json.dumps({'status':'SUPPORT_COMPLETE_CITATION_REVIEW_PENDING',
            'source_identity':{'packet':bound,'declaration_sha256':support.digest(decl)}}))
        review={'schema':'roboboat-population-citation-review/v1','packet_id':key,'status':'PASS',
            'complete_source_review':True,'project_agent_review_not_human_validation':True,
            'issues':[],'unresolved_decision_keys':[],'packet':release.binding(packet_path),
            'inputs':[release.binding(p) for p in folder.glob('*.json')]}
        reviews=out/'citation_reviews';reviews.mkdir(exist_ok=True)
        (reviews/f'{key}.json').write_text(json.dumps(review))
    return decl,out,sd


def test_real_support_release_pipeline_retains_full_labels_and_partial_geometry_only(tmp_path):
    decl,out,sd=prepared_support(tmp_path)
    result=release.summarize(decl,out)
    assert len(result['rows'])==6
    assert result['method_totals']['B2']['reviewed_answers']==3
    assert result['complete_geometry_descriptive_summary']['complete_independent_geometry_count']==0
    assert result['partial_geometry_clusters']
    assert all('all_final_decisions' in r['whole_answer_and_supporting_labels'] for r in result['rows'])
    assert result['confirmation_n']==result['replication_n']==result['independent_n_added']==0
    assert result['p_value'] is None


def test_missing_b2_call_is_full_snapshot_sensitivity_and_never_selective_release(tmp_path):
    decl,out,sd=prepared_support(tmp_path,fail=True)
    result=release.summarize(decl,out)
    totals=result['method_totals']['B2']
    assert totals['snapshot_answer_slots']==3 and totals['missing_or_failed_answers']==3
    assert totals['success_total_adverse']==0 and totals['success_total_favorable']==3
    assert all(p['difference_bounds']==[0,1] for p in result['paired_questions'])
    assert result['complete_geometry_descriptive_summary']['complete_independent_geometry_count']==0


@pytest.mark.parametrize('attack',['missing-review','unresolved-review','failed-support','unresolved-primary','missing-primary'])
def test_actual_release_gates_refuse_every_unfinished_declared_packet(tmp_path,attack):
    decl,out,sd=prepared_support(tmp_path);packet=support.checked(sd['packets'][0]);key=packet.stem
    review=out/'citation_reviews'/f'{key}.json';folder=out/'annotations'/key
    if attack=='missing-review':review.unlink()
    elif attack=='unresolved-review':
        v=json.loads(review.read_text());v['unresolved_decision_keys']=['unit:any'];review.write_text(json.dumps(v))
    elif attack=='failed-support':
        terminal=out/'terminals'/f'{key}.json';v=json.loads(terminal.read_text());v['status']='TECHNICAL_SUPPORT_FAILURE';terminal.write_text(json.dumps(v))
    else:
        final=folder/'final.json';v=json.loads(final.read_text())
        decision=next(k for k in v['final_decisions'] if k.startswith('unit:'))
        if attack=='unresolved-primary':v['final_decisions'][decision]=None
        else:del v['final_decisions'][decision]
        final.write_text(json.dumps(v));r=json.loads(review.read_text())
        r['inputs']=[release.binding(p) for p in folder.glob('*.json')];review.write_text(json.dumps(r))
    with pytest.raises(ValueError):release.summarize(decl,out)


def test_cluster_descriptives_require_all_two_variants_times_three_levels_and_methods():
    registry={'rows':[{'id':'geom-v1','cluster_id':'geom','variant':1},
                      {'id':'geom-v2','cluster_id':'geom','variant':2}]}
    entries=[{'id':row['id']+f'-L{level}'} for row in registry['rows'] for level in range(3)]
    rows=[{'response_id':e['id'],'method':m,'answer_status':'SOURCE_REVIEWED',
           'primary_bounds':[1,1] if m=='B4' else [0,0]} for e in entries for m in ('B2','B4')]
    complete,partial,summary=release.describe_clusters(registry,entries,rows)
    assert summary['complete_independent_geometry_count']==1
    assert complete[0]['difference']==1 and complete[0]['B4_only_success_questions']==6
    assert summary['cluster_difference_sign_counts']=={'positive':1,'negative':0,'tie':0}
    assert not partial
    rows[0]['answer_status']='MISSING_OR_FAILED_RESPONSE_RETAINED'
    complete,partial,summary=release.describe_clusters(registry,entries,rows)
    assert not complete and summary['complete_independent_geometry_count']==0
    assert partial[0]['independent_n_added']==0
