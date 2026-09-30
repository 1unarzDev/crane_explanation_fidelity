#!/usr/bin/env python3
"""Ordered two-worker candidate qualification/fresh pilot, no old job retry."""
import json,subprocess,time
from audit_release import ROOT
from verify_v3 import V3
PYTHON=ROOT/'data/hexar_external/.venv/bin/python'
def main():
 marker=ROOT/'data/hexar_external/v2/development/annotation/annotation_summary.json'
 while True:
  p=subprocess.run(['ps','-p','1137324','-o','args='],capture_output=True,text=True)
  if 'analysis/hexar_external/annotate_v2.py --cohort development --stage annotate' not in p.stdout:break
  time.sleep(15)
 if not marker.exists():raise RuntimeError('Verified v2 process ended without a batch summary; investigate before next release.')
 print('V2_CLOSED_RETAINED',json.loads(marker.read_text()),flush=True)
 subprocess.run([str(PYTHON),str(ROOT/'analysis/hexar_external/qualify_v3.py')],cwd=ROOT,check=True)
 status=json.loads((V3/'qualification/qualification-result.json').read_text())['status'];print('FRESH_QUALIFICATION',status,flush=True)
 if status!='QUALIFIED':return
 subprocess.run([str(PYTHON),str(ROOT/'analysis/hexar_external/run_v3_pilot.py'),'--cohort','development'],cwd=ROOT,check=True)
 print('FRESH_V3_PILOT_RESPONSES_READY_INVENTORY_AND_SUPPORT_STILL_REQUIRED',flush=True)
if __name__=='__main__':main()
