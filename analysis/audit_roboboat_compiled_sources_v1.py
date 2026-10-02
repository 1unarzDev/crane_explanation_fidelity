"""Read-only compiled document checksum audit; no deployment or study admission."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from roboboat_owned_player_bundle_v1 import binding, verify_build
from prepare_roboboat_baseline_interface_v1 import ROBOT_FILES

ALGORITHMS = {'8829d00f-11b8-4213-878b-770e8597ac16': 'sha256',
              'ff1816ec-aa5e-4d10-87f7-6f4963833460': 'sha1'}


def compare_document(document, project):
    project = Path(project).resolve()
    name = Path(document['name'])
    path = (name if name.is_absolute() else project/name).resolve()
    # No suffix guessing or reads of arbitrary external compiler paths.
    if not path.is_relative_to(project):
        return {'document': document, 'status': 'OUTSIDE_DECLARED_PROJECT_NOT_READ'}
    result = {'document': document, 'relative': path.relative_to(project).as_posix()}
    algorithm = ALGORITHMS.get(document['algorithm'])
    if not algorithm:
        return dict(result, status='UNKNOWN_CHECKSUM_ALGORITHM')
    if not path.is_file():
        return dict(result, status='SOURCE_UNAVAILABLE')
    data = path.read_bytes()
    actual = hashlib.new(algorithm, data).hexdigest()
    return dict(result, source=binding(path), actual_document_checksum=actual,
                status='MATCH' if actual == document['checksum'] else 'MISMATCH')


def audit(manifest_path, project, utility):
    manifest, build = verify_build(manifest_path)
    project = Path(project).resolve()
    utility = Path(utility).resolve()
    records = []
    # Audit all project documents represented in every bound managed PDB, not
    # only the sources whose hashes happen to match the desired candidates.
    for pdb in sorted((build/'CRANE_Data/Managed').glob('*.pdb')):
        assembly = pdb.with_suffix('.dll')
        if not assembly.is_file():
            records.append({'pdb': binding(pdb), 'status': 'NO_ASSEMBLY'})
            continue
        call = subprocess.run(['dotnet', str(utility), str(assembly), str(pdb)],
                              capture_output=True, text=True, timeout=60)
        try:
            metadata = json.loads(call.stdout)
        except ValueError:
            records.append({'pdb': binding(pdb), 'assembly': binding(assembly),
                            'status': 'UNREADABLE_METADATA', 'returncode': call.returncode,
                            'stderr': call.stderr[-2000:]})
            continue
        if metadata['assembly_sha256'] != binding(assembly)['sha256'] or metadata['pdb_sha256'] != binding(pdb)['sha256']:
            raise ValueError('metadata input identity changed')
        qualified = (call.returncode == 0 and metadata['assembly_pdb_identity_match']
                     and metadata['pe_pdb_checksum_match'] is True)
        records.append({'metadata': metadata, 'status': 'MATCHED_METADATA' if qualified else 'UNQUALIFIED_METADATA',
                        'source_documents': [compare_document(d, project) for d in metadata['documents']]})
    # Reverify the entire build after audit to detect concurrent mutation.
    verify_build(manifest_path)
    public = []
    for candidate in ROBOT_FILES:
        relative = candidate.removeprefix('packages/crane_ml/')
        hits = [(r['status'], d) for r in records for d in r.get('source_documents', []) if d.get('relative') == relative]
        status = ('MISSING_COMPILED_DOCUMENT' if not hits else
                  'MATCH' if all(s == 'MATCHED_METADATA' and d['status'] == 'MATCH' for s, d in hits)
                  else 'UNQUALIFIED_OR_MISMATCHED')
        public.append({'candidate': candidate, 'status': status, 'occurrences': len(hits)})
    return {'schema': 'roboboat-compiled-document-source-audit/v1-development',
            'build_manifest': binding(manifest_path), 'project': str(project), 'utility': binding(utility),
            'records': records, 'public_source_candidates': public,
            'deployment_wiring_proven': False, 'transitive_semantics_proven': False,
            'study_call_readiness': False, 'confirmation_n': 0, 'replication_n': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--project', required=True)
    parser.add_argument('--utility', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists(): raise FileExistsError('fresh audit namespace required')
    result = audit(args.manifest, args.project, args.utility)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream: json.dump(result, stream, indent=2)
