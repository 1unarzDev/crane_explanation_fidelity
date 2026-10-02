"""Supplemental audit of held-out returns; never changes frozen scores/gates.

Bool judgments and verbatim source containment are separate from whether a
reference's example sentence is selected. Neither is semantic validity alone.
"""


def audit_fields(case, returned):
    text=case['form']['response_text']; rows=[]
    for category,prompt_key,value_key in (
        ('required_unit_coverage','unit_prompt','communicated'),
        ('limitation_preservation','limitation_prompt','preserved')):
        expected=case['expected'][category]
        actual=returned[category]
        keys=[r[prompt_key] for r in actual]
        if len(keys)!=len(set(keys)) or set(keys)!={r[prompt_key] for r in expected}:
            raise ValueError('field identity/coverage mismatch')
        lookup={r[prompt_key]:r for r in actual}
        for gold in expected:
            value=lookup[gold[prompt_key]];span=value['response_span']
            if type(value[value_key]) is not bool:
                raise ValueError('explicit boolean judgment required')
            source_span_valid=(isinstance(span,str) and bool(span) and span in text) if value[value_key] else span is None or (isinstance(span,str) and bool(span) and span in text)
            example_match=(isinstance(span,str) and gold['response_span'].lower() in span.lower()) if gold[value_key] else True
            rows.append({'category':category,'prompt':gold[prompt_key],
                         'boolean_matches_reference':value[value_key]==gold[value_key],
                         'verbatim_source_span_valid':source_span_valid,
                         'reference_example_span_match':example_match,
                         'returned_span':span,
                         'semantic_citation_validity_established_by_arithmetic':False})
    return {'fields':rows,'frozen_score_replaced':False,'qualification_promoted':False,
            'all_boolean_and_source_span_checks_pass':all(r['boolean_matches_reference'] and r['verbatim_source_span_valid'] for r in rows)}
