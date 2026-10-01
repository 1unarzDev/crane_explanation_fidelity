#!/usr/bin/env python3
"""Single ordered descriptive release after annotation, safe to resume each stage."""
import json,subprocess,time
from audit_release import ROOT,write
from study_v2 import V2
PYTHON=ROOT/'data/hexar_external/.venv/bin/python'
def step(script,*args):
 print('START',script,*args,flush=True)
 subprocess.run([str(PYTHON),str(ROOT/'analysis/hexar_external'/script),*args],cwd=ROOT,check=True)
 print('DONE',script,flush=True)
def main():
 marker=V2/'development/annotation/annotation_summary.json'
 while not marker.exists():time.sleep(15)
 summary=json.loads(marker.read_text());print('ANNOTATION_BATCH_CLOSED',summary,flush=True)
 step('report_v2.py','--cohort','development')
 step('freeze_v2.py')
 step('build_v2_packets.py','--cohort','reserved')
 step('build_references_v2.py','--cohort','reserved')
 # Per-packet references must exist before any reserved model-backed realization.
 assert (V2/'reserved/references.json').exists()
 step('run_v2.py','--cohort','reserved')
 step('annotate_v2.py','--cohort','reserved','--stage','bank')
 step('archive_v2.py')
 print('RESERVED_BANK_READY_FOR_INDEPENDENT_INVENTORY',flush=True)
if __name__=='__main__':main()
