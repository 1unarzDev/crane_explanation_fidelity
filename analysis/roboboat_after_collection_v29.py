"""Wait on one exact collection identity; never restart or infer completion from silence."""
import json
from pathlib import Path
import time
from roboboat_render_fps_lease_v1 import process_identity
from generate_roboboat_population_v1 import digest


def predecessor_ready(record, *, identity=process_identity):
    declaration=Path(record['declaration']['path'])
    if digest(declaration)!=record['declaration']['sha256']:raise ValueError('predecessor declaration changed')
    d=json.loads(declaration.read_text());terminal=Path(d['output_root'])/'terminal.json'
    if terminal.exists():
        t=json.loads(terminal.read_text())
        if t['status']!='TRACE_QUALIFIED_DEVELOPMENT_BATCH_FINISHED' or t['declaration_sha256']!=record['declaration']['sha256']:
            raise ValueError('predecessor terminal/declaration mismatch')
        ids=[r['row']['id'] for r in t['results']]
        if len(ids)!=len(set(ids)) or set(ids)!=set(d['rows']) or t['physical_attempts']!=len(d['rows']):
            raise ValueError('predecessor schedule incomplete')
        if any(r['status'] not in ('TECHNICAL_FAILURE','VALID_TRACE_QUALIFIED_DEVELOPMENT') for r in t['results']):
            raise ValueError('unresolved predecessor disposition')
        return True
    actual=identity(record['process']['pid'])
    if actual!=record['process']:raise RuntimeError('exact predecessor is no longer live without a complete terminal; no restart or successor launch')
    return False


def wait(record):
    announced=False
    while not predecessor_ready(record):
        if not announced:
            print(json.dumps({'status':'WAITING_ON_EXACT_LIVE_PREDECESSOR','process':record['process'],'no_restart':True}),flush=True)
            announced=True
        time.sleep(5)
