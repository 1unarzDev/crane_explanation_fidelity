"""Publish fresh prospectively admitted trace-qualified development only."""
import json
from pathlib import Path
from generate_roboboat_population_v1 import digest
from build_roboboat_terminal_batch import save
from roboboat_temporal_certificate_v2 import audit_ladder
from roboboat_trace_qualified_validity_v1 import assess


def publish_terminal(row, registry_path, capture, config, declaration_path):
    declaration=json.loads(declaration_path.read_text());original=capture/'capture-attempt.json'
    old=json.loads(original.read_text())
    if row['id'] not in declaration['rows'] or old['row']!=row or old['registry_sha256']!=digest(registry_path):
        raise ValueError('prospective fresh capture identity mismatch')
    if old['status']!='VALID_TRACE_QUALIFIED_DEVELOPMENT' or old['development_recording_admitted'] is not True:
        raise ValueError('cannot salvage an old or failed recording')
    if old['prospective_declaration']!={'path':str(declaration_path),'sha256':digest(declaration_path)}:
        raise ValueError('prospective declaration mismatch')
    summary=json.loads((capture/'navigation-reset-summary.json').read_text());worker=json.loads((capture/'worker-0/result.json').read_text());fixture=json.loads((capture/'fixture-summary.json').read_text())
    records=[json.loads(x) for x in (capture/'action-timing.jsonl').read_text().splitlines() if x.strip()]
    if not assess(summary,worker,fixture,records,(capture/'worker-0/player.log').read_text())['candidate_qualified']:
        raise ValueError('fresh recording fails trace-qualified predicates')
    if old['return_code'] not in (0,1) or (old['return_code']==1 and fixture['status']==summary['expectedNavigationStatus']):
        raise ValueError('non-outcome launcher failure')
    if not all(old['checks'].values()):raise ValueError('incomplete runtime or rendering qualification')
    output=capture/'exports-v2';packets=[json.loads((output/'method_packets'/f'L{i}.json').read_text()) for i in range(3)]
    audit_ladder(packets)
    value={'schema':'roboboat-trace-qualified-export/v1-development','status':'VALID_TRACE_QUALIFIED_DEVELOPMENT',
        'row':row,'registry_sha256':digest(registry_path),'export_directory':'exports-v2',
        'level_outcomes':old['level_outcomes'],'recording_technical_valid':True,
        'worker_valid_original':worker['valid'],'stale_actions_observed':worker['staleActions'],
        'prospective_declaration':old['prospective_declaration'],
        'original_capture_terminal':{'path':str(original),'sha256':digest(original)},
        'exporter':{'path':str(Path(__file__).resolve()),'sha256':digest(Path(__file__))},
        'raw_sources':[{'path':str(capture/n),'sha256':digest(capture/n)} for n in ('fixture-summary.json','runtime-parameters.json','navigation-reset-summary.json','worker-0/result.json','action-timing.jsonl','worker-0/player.log')],
        'platform_version':'isolated instrumented v9; .02 physics step, .04 catch-up cap; physical equivalence unasserted',
        'prior_dispositions_changed':False,'new_physical_runs_by_export':0,'confirmation_n':0,'replication_n':0}
    save(capture/'capture-export-terminal-trace-v1.json',value)
    return value
