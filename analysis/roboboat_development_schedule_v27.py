"""Outcome-blind development scheduling, with geometry-level exclusion/identity."""
import copy
import random


def schedule(population, operational_origin_rows, seed=43227):
    by_id={r['id']:r for r in population['rows']}
    if len(by_id)!=len(population['rows']):raise ValueError('duplicate population row')
    if not set(operational_origin_rows)<=set(by_id):raise ValueError('unknown inspected origin')
    excluded={by_id[i]['cluster_id'] for i in operational_origin_rows}
    clusters=[copy.deepcopy(c) for c in population['clusters'] if c['cluster_id'] not in excluded]
    if len({c['cluster_id'] for c in clusters})!=len(clusters):raise ValueError('duplicate independent geometry')
    random.Random(seed).shuffle(clusters)
    rows=[];lanes=[[],[]]
    for index,c in enumerate(clusters):
        pair=[copy.deepcopy(by_id[i]) for i in c['rows']]
        if len(pair)!=2 or {r['variant'] for r in pair}!={1,2} or any(r['cluster_id']!=c['cluster_id'] for r in pair):
            raise ValueError('complete original physical pair required')
        if any(r['disposition']!='DEVELOPMENT_EXPLORATORY' for r in pair):raise ValueError('development origins required')
        rows.extend(pair);lanes[index%2].extend(r['id'] for r in pair)
    return rows,clusters,lanes,sorted(excluded)
