#!/usr/bin/env python3
"""Check model availability without episode data before resuming frozen requests.

No method/endpoint/analysis changes. Failed study requests remain permanently
excluded by the existing runner; this avoids losing further candidates to a
known account-wide outage. Probe returns never enter the statistical sample.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from run_evidence_calibration_b2_pilot import ROOT,BoundedCodexCliCaller


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--freeze',required=True,type=Path)
    parser.add_argument('--look',choices=['FIRST','FINAL'],default='FIRST')
    parser.add_argument('--probe-only',action='store_true')
    args=parser.parse_args()
    freeze=json.loads(args.freeze.read_text())
    if freeze['status']!='FROZEN_BEFORE_FIRST_CONFIRMATORY_SEMANTIC_OUTPUT':raise RuntimeError('No frozen study')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    cache=ROOT/'model_outputs'/freeze['study_id']/'availability-probes'/stamp
    caller=BoundedCodexCliCaller(cache,'gpt-6-sol','high',freeze['b2_timeout_seconds'])
    schema=dict(type='object',properties=dict(ready=dict(type='boolean')),required=['ready'],additionalProperties=False)
    try:
        with tempfile.TemporaryDirectory(prefix='crane-no-study-availability-') as tmp:
            record=caller.call('TECHNICAL_AVAILABILITY_NO_STUDY_DATA','Return only the JSON object {"ready":true}. Do not use tools. This checks technical model availability; no robot episode or study answer is requested.',schema,
                working_directory=Path(tmp),workspace_identity=dict(probe_id=stamp,study_data_supplied=False,study_method_answer=False))
        if record['parsed_final']!={'ready':True}:raise RuntimeError('Unexpected technical probe response')
    except RuntimeError:
        print(json.dumps(dict(model_available=False,study_method_requests_launched=0,probe_cache=str(cache),frozen_design_changed=False)))
        return 75
    print(json.dumps(dict(model_available=True,probe_enters_statistical_sample=False)),flush=True)
    if args.probe_only:return 0
    return subprocess.run([sys.executable,str(ROOT/'analysis/run_handoff_confirmation_pairs.py'),'--freeze',str(args.freeze),'--look',args.look],cwd=ROOT).returncode


if __name__=='__main__':sys.exit(main())
