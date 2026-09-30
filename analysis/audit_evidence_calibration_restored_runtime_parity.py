#!/usr/bin/env python3
"""Deterministic local runtime parity probes; no model caller migration or semantic scoring."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess

import build_evidence_calibration_five_method_packet_candidate as candidate
from build_evidence_calibration_method_packets import build
from evidence_calibration_io import canonical_sha256
from evidence_calibration_local_tool_sandbox_v2 import command, Limits
from inspect_evidence_calibration_packet import summarize
from stage_evidence_calibration_workspace import staged_workspace, verify

ROOT=Path(__file__).resolve().parents[1]
RESTORATION=ROOT/'output/infrastructure/runtime-restoration-fsetid-development-v1'
LIMITS=Limits(wall_seconds=5,cpu_seconds_per_process=2,address_space_bytes_per_process=256*1024**2,combined_output_bytes=1024**2)
PRIMITIVE="""import bz2,ctypes,csv,decimal,gzip,hashlib,io,json,lzma,math,random,sqlite3,ssl,statistics,sys,xml.etree.ElementTree as ET
payload=b'full visible samples'
rows={
 'python':sys.version.split()[0], 'hypot':math.hypot(3,4),
 'mean':statistics.mean([0.1,0.2,0.3]), 'decimal':str(decimal.Decimal('0.1')+decimal.Decimal('0.2')),
 'gzip_roundtrip':gzip.decompress(gzip.compress(payload))==payload,
 'bz2_roundtrip':bz2.decompress(bz2.compress(payload))==payload,
 'lzma_roundtrip':lzma.decompress(lzma.compress(payload))==payload,
 'sha256':hashlib.sha256(payload).hexdigest(), 'xml_tag':ET.fromstring('<visible/>').tag,
 'csv_rows':list(csv.reader(io.StringIO('time,speed\\n1,0.25\\n'))),
 'sqlite':sqlite3.connect(':memory:').execute('select 3+4').fetchone()[0],
 'ssl':ssl.OPENSSL_VERSION, 'ctypes_double_bytes':ctypes.sizeof(ctypes.c_double),
 'random_seeded':random.Random(17).random()}
print(json.dumps(rows,sort_keys=True))
"""


def probe(workspace: Path, identity: dict, args: list[str], runtime: Path | None):
    argv=command(workspace,identity,args,LIMITS)
    if runtime is not None:
        matches=[i for i in range(len(argv)-2) if argv[i:i+3]==['--ro-bind','/usr','/usr']]
        if len(matches)!=1 or runtime.is_symlink() or not runtime.is_dir():
            raise ValueError('exact registered runtime bind seam unavailable')
        argv[matches[0]+1]=str(runtime.resolve())
    try:
        # This fixed-output, project-authored probe is not the model-facing tool execution path.
        done=subprocess.run(argv,env={},close_fds=True,capture_output=True,text=True,check=False,timeout=5)
        if done.returncode or len(done.stdout.encode())+len(done.stderr.encode())>LIMITS.combined_output_bytes:
            raise ValueError('runtime probe failed; retain technical status without host fallback')
        return done
    finally:verify(workspace,identity)


def audit():
    terminal=json.loads((RESTORATION/'terminal.json').read_text())
    if terminal['status']!='RESTORED_RUNTIME_IDENTITY_VERIFIED_EXECUTION_AND_ADOPTION_OPEN' or not terminal['container_removed_or_absent']:
        raise ValueError('complete successful restoration required before execution probes')
    runtime=RESTORATION/'root/usr'
    source=candidate.build();catalog=json.loads((ROOT/candidate.CATALOG).read_text())
    rows=[];primitives=None
    for episode in source['episodes']:
        diagnostic=json.loads((ROOT/f"data/robot_visible/dev/{episode['source_run_id']}/command-motion-diagnostic-v3.json").read_text())
        for entry in candidate.materialize(diagnostic,episode['configuration_id'],episode['family'],catalog):
            packets=build(entry,candidate.execution_contract(entry,diagnostic))
            packet=next(p for p in packets['method_packets'] if p['method_id']=='B2')
            with staged_workspace(entry,packet) as (workspace,identity):
                args=['tools/inspect_evidence_calibration_packet.py','robot_visible/evidence.json']
                host=probe(workspace,identity,args,None);restored=probe(workspace,identity,args,runtime)
                if (host.stdout,host.stderr)!=(restored.stdout,restored.stderr) or json.loads(restored.stdout)!=summarize(entry['method_packet']):
                    raise ValueError('original inventory tool differs across runtime candidates')
                if primitives is None:
                    a=probe(workspace,identity,['-c',PRIMITIVE],None);b=probe(workspace,identity,['-c',PRIMITIVE],runtime)
                    if (a.stdout,a.stderr)!=(b.stdout,b.stderr):raise ValueError('registered stdlib primitive results differ')
                    primitives={'stdout_sha256':hashlib.sha256(b.stdout.encode()).hexdigest(),
                                'stdout_bytes':len(b.stdout.encode()),'result':json.loads(b.stdout)}
                rows.append({'condition_id':entry['condition']['condition_id'],
                    'workspace_sha256':identity['workspace_sha256'],
                    'stdout_sha256':hashlib.sha256(restored.stdout.encode()).hexdigest(),
                    'stderr_bytes':len(restored.stderr.encode()),'byte_exact_match':True})
    if len(rows)!=60:raise ValueError('full retained condition scope changed')
    return {'schema':'crane-restored-runtime-parity-audit/v1-development',
        'status':'SIXTY_ORIGINAL_TOOL_RESULTS_AND_STDLIB_PROBES_MATCH',
        'restoration_terminal_raw_sha256':hashlib.sha256((RESTORATION/'terminal.json').read_bytes()).hexdigest(),
        'runtime_inventory_sha256':terminal['result']['inventory_sha256'],
        'condition_count':len(rows),'conditions':rows,'stdlib_primitive_probe':primitives,
        'primitive_code_sha256':hashlib.sha256(PRIMITIVE.encode()).hexdigest(),
        'method_runtime_adopted':False,'general_execution_equivalence_proven':False,
        'complete_model_facing_harness_verified':False,'model_call_attempted':False,
        'semantic_method_outputs_generated':0,'endpoint_scoring_authorized':False,
        'p11_authorized':False,'confirmation_independent_n':0,'replication_independent_n':0}


if __name__=='__main__':
    print(json.dumps(audit(),indent=2,sort_keys=True))
