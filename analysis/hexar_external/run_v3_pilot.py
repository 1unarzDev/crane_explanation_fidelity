#!/usr/bin/env python3
"""Fresh bounded interface pilot using the unchanged v2 production executor."""
import json
from audit_release import ROOT,sha,write
from verify_v3 import V3,qualified
import run_v2

def main():
 qualified()
 binding={'schema':'hexar-fresh-interface-pilot-binding/v3','qualification_sha256':sha(V3/'qualification/qualification-result.json'),'executor_sha256':sha(ROOT/'analysis/hexar_external/run_v2.py'),'bridge_sha256':sha(ROOT/'analysis/hexar_external/run_v3_pilot.py'),'adapter_sha256':sha(ROOT/'analysis/hexar_external/study_v2.py'),'slice_sha256':sha(V3/'development/slice_declaration.json'),'inherited_v2_schema_names':'Only file-root and qualified-binding injections differ; method/evidence/model behavior remains the unchanged v2 executor. This is not a new physical cohort or a v2 answer rescore.','alpha_consumed':0}
 dest=V3/'development/v3_binding.json'
 if dest.exists():assert json.loads(dest.read_text())==binding
 else:write(dest,binding)
 run_v2.V2=V3;run_v2.qualified=qualified;run_v2.main()
if __name__=='__main__':main()
