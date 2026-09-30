"""Prospective local scorer: boolean accuracy and verbatim citation validity.

No required example-sentence match. Semantic citation validity still needs an
explicit full-source project review before qualification disposition.
"""
from run_evidence_calibration_agent_qualification import score_case as legacy_score


def score_case(case,returned):
    result=legacy_score(case,returned)
    response=case['form']['response_text']
    for category,value_key,prompt_key,result_key in (
        ('required_unit_coverage','communicated','unit_prompt','required_units'),
        ('limitation_preservation','preserved','limitation_prompt','limitations')):
        gold=case['expected'][category];actual=returned[category]
        expected_keys={g[prompt_key] for g in gold}
        if len(actual)!=len(expected_keys) or {a[prompt_key] for a in actual}!=expected_keys:raise ValueError('duplicate/missing field judgment')
        lookup={a[prompt_key]:a for a in actual};rows=[]
        for g in gold:
            a=lookup[g[prompt_key]];span=a['response_span']
            if type(a[value_key]) is not bool:raise ValueError('field must be explicit boolean')
            verbatim=isinstance(span,str) and bool(span) and span in response
            span_valid=verbatim if a[value_key] else span is None or verbatim
            rows.append({prompt_key:g[prompt_key],'correct':a[value_key]==g[value_key] and span_valid,
                         'boolean_matches_reference':a[value_key]==g[value_key],
                         'source_citation_valid':span_valid,'returned_span':span,
                         'semantic_citation_validity_established':False})
        result[result_key]=rows
    return result
