#!/usr/bin/env python3
"""Ordered full reserved release, contingent on already closed qualified pilot."""
import subprocess
from audit_release import ROOT
PYTHON=ROOT/'data/hexar_external/.venv/bin/python'
def step(script,*args):
 print('START',script,*args,flush=True);subprocess.run([str(PYTHON),str(ROOT/'analysis/hexar_external'/script),*args],cwd=ROOT,check=True);print('DONE',script,flush=True)
def main():
 step('freeze_v3.py')
 step('build_v3_reserved.py','--cohort','reserved')
 step('run_v3_reserved.py','--cohort','reserved')
 step('annotate_v3.py','--cohort','reserved','--stage','bank')
 print('ALL_324_RESERVED_RESPONSES_RETAINED_BLIND_INVENTORY_AND_SUPPORT_REQUIRED',flush=True)
if __name__=='__main__':main()
