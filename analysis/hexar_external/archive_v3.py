#!/usr/bin/env python3
"""Retain both failed and qualified measurement versions without public upload."""
from audit_release import ROOT,sha,write

def main():
 base=ROOT/'data/hexar_external';rows=[]
 for version in ('v2','v3'):
  for p in sorted((base/version).rglob('*')):
   if not p.is_file() or '/tmp/' in str(p) or p.name=='archive_manifest.json':continue
   rows.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size,'local_only':('/calls/' in str(p) or '/model_cache/' in str(p) or p.name.startswith('events-'))})
 write(base/'v3/archive_manifest.json',{'schema':'hexar-restorable-all-version-manifest/v3','files':rows,'upstream_pin':'f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc','core_pin':'9a81db860f9eec66557240b2297cd122fba9ca06','data_redistribution_rights':'not established independently of package Apache-2.0; do not publish raw recordings/extractions/call payloads on that assumption','model_provenance':'same requested hosted configuration; immutable weights unavailable; no historical phi4 identity claim','failed_versions_retained':True,'shared_storage_or_pins_modified':False,'alpha_consumed':0})
 print('ALL_VERSION_LOCAL_ARCHIVE_HASHED',len(rows))
if __name__=='__main__':main()
