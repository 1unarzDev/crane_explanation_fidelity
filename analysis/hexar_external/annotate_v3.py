#!/usr/bin/env python3
"""Versioned unchanged support pipeline plus qualified form-applicability clarification."""
import json
from audit_release import ROOT,sha,write
from verify_v3 import V3,qualified
from qualify_v3 import effective_prompt
import annotate_v2

def main():
 qualified()
 binding={'schema':'hexar-annotation-interface-binding/v3','qualification_sha256':sha(V3/'qualification/qualification-result.json'),'base_amendment_sha256':sha(ROOT/'docs/hexar_external/v2/annotation_amendment.txt'),'sentinel_clarification_sha256':sha(ROOT/'docs/hexar_external/v3/sentinel_clarification.txt'),'executor_sha256':sha(ROOT/'analysis/hexar_external/annotate_v2.py'),'bridge_sha256':sha(ROOT/'analysis/hexar_external/annotate_v3.py'),'schema_and_validator':'unchanged current pinned main pipeline','inherited_status_name':'EXTERNAL_V2_AGENT_ASSESSED_QUALIFIED denotes inherited executor, not qualification identity; external_qualification_sha256 points to v3 and this binding pins its extra clarification.','physical_sample_increment':0,'failed_v2_jobs_retried':False,'endpoint_changed':False,'alpha_consumed':0}
 dest=V3/'annotation_binding.json'
 if dest.exists():assert json.loads(dest.read_text())==binding
 else:write(dest,binding)
 annotate_v2.V2=V3;annotate_v2.qualified=qualified;annotate_v2.effective_prompt=effective_prompt;annotate_v2.main()
if __name__=='__main__':main()
