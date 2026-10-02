"""Thin marine score adapter around the existing bounded e-process primitives.

This module supplies scoring and simulation QA. It does not authorize any look,
allocate alpha, alter the land monitor or read study responses automatically.
"""
from sequential_diagnostic_monitor import lower_confidence_bound,upper_confidence_bound

QUESTIONS=tuple(f'{variant}:L{level}' for variant in ('a','b') for level in range(3))


def score_cluster(cluster):
    if cluster['recording_valid'] != {'a':True,'b':True}:
        raise ValueError('both prospectively paired recordings must be valid')
    rows=cluster['questions']
    if len(rows)!=6 or {r['question_id'] for r in rows}!=set(QUESTIONS):
        raise ValueError('six unique fixed questions required; ladders add no N')
    for row in rows:
        if any(row[m] is not None and type(row[m]) is not bool for m in ('B2','B4')):
            raise ValueError('success must be Boolean or unresolved None')
    low=sum((0 if r['B4'] is None else int(r['B4']))-
            (1 if r['B2'] is None else int(r['B2'])) for r in rows)/6
    high=sum((1 if r['B4'] is None else int(r['B4']))-
             (0 if r['B2'] is None else int(r['B2'])) for r in rows)/6
    complete=all(r[m] is not None for r in rows for m in ('B2','B4'))
    return {'cluster_id':cluster['cluster_id'],'question_n':6,'independent_n':1,
            'difference':low if complete else None,
            'adverse_difference':low,'favorable_difference':high}


def simulation_bounds(clusters,alpha,betting_fractions):
    if any(c.get('origin')!='SIMULATED' for c in clusters):
        raise ValueError('real-study inference requires coordinator-approved activation')
    if len({c['cluster_id'] for c in clusters})!=len(clusters):
        raise ValueError('duplicate cluster cannot increase N')
    scores=[score_cluster(c) for c in clusters]
    return {'purpose':'SIMULATION_QA_NOT_STUDY_INFERENCE','cluster_n':len(scores),
            'adverse_lower':lower_confidence_bound(
                [s['adverse_difference'] for s in scores],alpha,betting_fractions),
            'favorable_upper':upper_confidence_bound(
                [s['favorable_difference'] for s in scores],alpha,betting_fractions),
            'alpha_allocated_or_consumed':0}
