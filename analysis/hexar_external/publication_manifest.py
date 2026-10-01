#!/usr/bin/env python3
"""Scoped immutable archive handoff; no DVC/Git/shared-component mutation."""
from pathlib import Path
from audit_release import ROOT,sha,write

def main():
    local=[]
    for pattern in ('data/hexar_external/development/model_cache/*.json',
        'data/hexar_external/qualification/pass-*/calls/*.json',
        'data/hexar_external/extracted/*.json',
        'data/hexar_external/replay/native-parity.json',
        'data/hexar_external/replay/native-dispatch-trace.json'):
        for p in sorted(ROOT.glob(pattern)):
            local.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size,
                'role':'immutable_local_model_record' if '/calls/' in str(p) or '/model_cache/' in str(p) else 'local_replay_input_or_trace'})
    write(ROOT/'data/hexar_external/publication_manifest.json',{'schema':'hexar-publication-handoff/v1',
        'shared_storage_updates_made':False,'local_archive_files':local,
        'source_data_hash_manifest':'data/hexar_external/audit/source_data_manifest.json',
        'source_data_redistribution_permission':'not established independently; do not upload raw recordings under an assumed package license',
        'evaluator_only_assets':['data/hexar_external/annotation/join_key.evaluator-only.json','data/hexar_external/development/independent_references.json'],
        'status':'executed development tranche; qualified endpoint blocked; no external alpha allocated',
        'publication_owner_next_step':'Review scoped artifacts and local immutable archive. Resolve qualification and all-family scientific gates before reserved semantic generation. Coordinate budget through actual shared ledger; do not infer an alpha allocation from this manifest.'})
    print(f'Scoped archive records: {len(local)}')
if __name__=='__main__':main()
