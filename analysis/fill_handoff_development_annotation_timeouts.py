#!/usr/bin/env python3
"""Retain timed-out development annotations and fill only scoreless returns.

Never changes/retries a method answer. Never runs on confirmation observations.
"""
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'analysis/results/evidence-calibration-handoff-development'
spec=importlib.util.spec_from_file_location('measurement',HERE/'run_measurement.py')
measurement=importlib.util.module_from_spec(spec);spec.loader.exec_module(measurement)
source=ROOT/'model_outputs/evidence-calibration-final-v7-development-scoring-prompt-v5'
base=ROOT/'analysis/results/development/evidence-calibration-final-v7-development-prompt-v5'
records=[]
for slot in ['A','B']:
    cases=[];assets=None
    for p in sorted(source.glob(slot+'-batch-*.json')):
        if p.name.endswith('request.json'):continue
        r=json.loads(p.read_text())
        if r['status']=='STRUCTURALLY_VALID_SUPPORT_RETURN':continue
        if not r['timed_out'] or r['raw_final']:raise RuntimeError('Only scoreless technical timeouts eligible')
        request=json.loads(p.with_name(p.stem+'.request.json').read_text())
        cases+=request['cases'];assets=request['shared_exact_source_assets']
        records.append(dict(slot=slot,failed_source=str(p.relative_to(ROOT)),case_ids=[c['case_id'] for c in request['cases']]))
    (base/('scoreless-timeout-cases-'+slot+'.json')).write_text(json.dumps(dict(scope='DEVELOPMENT_ONLY',cases=cases,source_assets=assets),indent=2)+'\n')
    if cases:
        measurement.execute(cases,ROOT/'model_outputs/evidence-calibration-final-v7-development-scoring-prompt-v5-timeout-fill',slot,4,4,assets,HERE/'annotation-prompt-v5.md',True,'DEVELOPMENT_ONLY',900,'high')
(base/'scoreless-timeout-fill-manifest-v1.json').write_text(json.dumps(dict(development_only=True,method_answers_retried=0,failed_returns_retained=True,records=records),indent=2)+'\n')
