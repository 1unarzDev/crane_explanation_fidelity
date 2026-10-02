#!/usr/bin/env python3
"""Hash scoped restorable assets without redistributing unresolved raw-data rights."""
from audit_release import ROOT,sha,write
from study_v2 import V2

def main():
 files=[]
 for p in sorted(V2.rglob('*')):
  if not p.is_file() or '/tmp/' in str(p) or p.name=='archive_manifest.json':continue
  files.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size,'local_only':('/calls/' in str(p) or '/model_cache/' in str(p) or p.name.startswith('events-'))})
 write(V2/'archive_manifest.json',{'schema':'hexar-scoped-restorable-manifest/v2','files':files,'redistribution':'Raw recordings/extracted events have unresolved dataset rights. Preserve local immutable archives; do not publish them on assumed package Apache-2.0 terms. Method outputs and evaluator artifacts require source attribution.','upstream_pin':'f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc','shared_storage_updates':False,'model_artifact':'hosted requested model configuration only; weights/immutability unavailable','cache_resume':'Use exact run declaration and cached call identity; no new answer on resume. Technical failures retained without retry.'})
 print('ARCHIVE_HASHED',len(files))
if __name__=='__main__':main()
