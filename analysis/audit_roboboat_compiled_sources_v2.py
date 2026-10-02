"""Explicit, hash-bound imported compiler-cache source mapping; no runtime wiring claim."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from audit_roboboat_compiled_sources_v1 import ALGORITHMS
from prepare_roboboat_baseline_interface_v1 import checked
from roboboat_owned_player_bundle_v1 import binding, verify_build


def map_document(document, project, parent, parent_bindings, current_bindings):
    project,parent=Path(project).resolve(),Path(parent).resolve()
    name=Path(document['name'])
    if not name.is_absolute() or not name.is_relative_to(parent):
        return None
    relative=name.relative_to(parent).as_posix();current=project/relative
    original=parent_bindings.get(str(name));actual=current_bindings.get(str(current))
    if original is None or actual is None:
        return {'document':document,'status':'IMPORTED_CACHE_SOURCE_NOT_BOUND','relative':relative}
    # Both roots are explicit, both source records predate this audit, and the
    # compiler's own checksum must agree with both. No basename/suffix search.
    checked(original);checked(actual)
    if original['sha256']!=actual['sha256']:
        return {'document':document,'status':'IMPORTED_CACHE_SOURCE_DIFFERS','relative':relative}
    algorithm=ALGORITHMS.get(document['algorithm'])
    if algorithm is None or hashlib.new(algorithm,current.read_bytes()).hexdigest()!=document['checksum']:
        return {'document':document,'status':'IMPORTED_CACHE_DOCUMENT_MISMATCH','relative':relative}
    return {'document':document,'relative':relative,'source':binding(current),
            'compiler_source':original,'mapping':'explicit parent compiler root, identical independently bound current bytes',
            'actual_document_checksum':document['checksum'],'status':'MATCH'}


def audit(original_audit, manifest_path, parent_manifest):
    original_audit,manifest_path,parent_manifest=map(lambda p:Path(p).resolve(),(original_audit,manifest_path,parent_manifest))
    original=json.loads(original_audit.read_text());checked(original['build_manifest'])
    if Path(original['build_manifest']['path'])!=manifest_path:raise ValueError('original audit binds different build')
    current,build=verify_build(manifest_path);parent,oldbuild=verify_build(parent_manifest)
    project=Path(original['project']).resolve();parent_project=oldbuild.parent.parent
    if build!=project/'Builds/CRANE-Worker':raise ValueError('current build/project mismatch')
    parents={i['path']:i for i in parent['source_bindings_current']};currents={i['path']:i for i in current['source_bindings_current']}
    records=copy.deepcopy(original['records'])
    for record in records:
        for index,document in enumerate(record.get('source_documents',[])):
            if document['status']=='OUTSIDE_DECLARED_PROJECT_NOT_READ':
                mapped=map_document(document['document'],project,parent_project,parents,currents)
                if mapped is not None:
                    mapped['original_document_resolution']=document['status']
                    record['source_documents'][index]=mapped
    verify_build(manifest_path);verify_build(parent_manifest)
    return dict(original,schema='roboboat-compiled-document-source-audit/v2-development',records=records,
                original_audit=binding(original_audit),mapping_audit_source=binding(__file__),
                explicit_imported_compiler_root=str(parent_project),parent_build_manifest=binding(parent_manifest),
                public_source_candidates_original=original['public_source_candidates'],
                public_source_candidates=None,
                mapping_scope='Exact explicit imported root plus two independently bound equal source hashes plus compiler document checksum. No suffix inference; vendor/generated unresolved records retained.',
                deployment_wiring_proven=False,study_call_readiness=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--original-audit',required=True);p.add_argument('--manifest',required=True);p.add_argument('--parent-manifest',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    value=audit(a.original_audit,a.manifest,a.parent_manifest)
    with Path(a.output).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
