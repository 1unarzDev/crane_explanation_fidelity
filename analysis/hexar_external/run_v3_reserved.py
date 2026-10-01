#!/usr/bin/env python3
"""Execute the complete frozen three-method reserved comparison, same executor."""
import json,sys
from audit_release import ROOT,sha,write
from verify_v3 import V3,qualified,study
import run_v2

def main():
 study()
 if sys.argv[1:]!=['--cohort','reserved']:raise ValueError('Reserved bridge requires the full reserved cohort.')
 release=json.loads((V3/'reserved/reference_release.json').read_text());assert release['method_answers_inspected'] is False
 assert release['packets_sha256']==sha(V3/'reserved/packets.json') and release['references_sha256']==sha(V3/'reserved/references.json')
 value={'schema':'hexar-reserved-executor-binding/v3','freeze_sha256':sha(V3/'study_freeze.json'),'qualification_sha256':sha(V3/'qualification/qualification-result.json'),'executor_sha256':sha(ROOT/'analysis/hexar_external/run_v2.py'),'bridge_sha256':sha(ROOT/'analysis/hexar_external/run_v3_reserved.py'),'reference_release_sha256':sha(V3/'reserved/reference_release.json'),'scope':'all twelve reserved physical recordings, three original questions, three fixed masks, three methods; inherited v2 schema names with declared v3 identity','alpha_consumed':0}
 dest=V3/'reserved/v3_binding.json'
 if dest.exists():assert json.loads(dest.read_text())==value
 else:write(dest,value)
 run_v2.V2=V3;run_v2.qualified=qualified;run_v2.study=study;run_v2.main()
if __name__=='__main__':main()
