"""Retain every operational replay outcome and missingness; zero independent N."""
import argparse
from collections import Counter
import json
from pathlib import Path
from roboboat_owned_player_bundle_v1 import binding
from prepare_roboboat_baseline_interface_v1 import checked


def profile(declaration_path):
    declaration_path=Path(declaration_path).resolve();d=json.loads(declaration_path.read_text())
    if d['schema']!='roboboat-clock-repair-operational-declaration/v1' or any(d[k]!=0 for k in ('independent_n_added','confirmation_n','replication_n')):
        raise ValueError('zero-N operational declaration required')
    declared={r['path']:r['sha256'] for r in d['dependencies']}
    registry_path=Path(d['registry']);registry=json.loads(registry_path.read_text())
    if binding(registry_path)['sha256']!=declared[str(registry_path)]:raise ValueError('operational registry changed')
    expected={r['id']:r for r in registry['rows']};rows=[];dependencies=[binding(declaration_path),binding(registry_path),binding(__file__)]
    for identifier in d['rows']:
        folder=Path(d['output_root'])/identifier;terminal=folder/'capture-attempt.json'
        row={'id':identifier,'origin_id':d['origin_rows'][identifier],'status':'UNATTEMPTED'}
        if not terminal.exists():
            if (folder/'capture-intent.json').exists():row['status']='RUNNING'
            rows.append(row);continue
        capture=json.loads(terminal.read_text());dependencies.append(binding(terminal))
        if capture['row']!=expected[identifier] or capture['registry_sha256']!=binding(registry_path)['sha256'] or capture['prospective_declaration']!=binding(declaration_path):raise ValueError('replay identity mismatch')
        if capture['operational_replay']is not True or capture['independent_n_added']!=0:raise ValueError('replay mislabeled as independent evidence')
        row.update(status=capture['status'],navigation_status=capture.get('observed_navigation_status'),error=capture.get('error'),failed_checks=[k for k,v in capture.get('checks',{}).items() if not v])
        if row['status'] not in ('TECHNICAL_FAILURE','VALID_TRACE_QUALIFIED_DEVELOPMENT'):raise ValueError('nonterminal replay disposition')
        audit_path=folder/'action-timing-audit.json'
        if audit_path.exists():
            audit=json.loads(audit_path.read_text());dependencies.append(binding(audit_path));row.update(trace_integrity_pass=audit['trace_integrity_pass'],trace_issues=audit['issues'])
        if row['status']=='VALID_TRACE_QUALIFIED_DEVELOPMENT':
            export_path=folder/'capture-export-terminal-trace-v3.json';export=json.loads(export_path.read_text());dependencies.append(binding(export_path))
            if export['platform_version']!=d['platform_version'] or export['operational_replay']is not True or export['independent_n_added']!=0 or not all(capture['checks'].values()):raise ValueError('admitted replay lacks declared platform or complete checks')
            checked(export['original_capture_terminal'])
            for item in export['raw_sources']:checked(item);dependencies.append(item)
        rows.append(row)
    return {'schema':'roboboat-clock-repair-operational-profile/v1','phase':'NONSTUDY_ENGINEERING_RELIABILITY_ONLY','dependencies':dependencies,'rows':rows,'dispositions':dict(Counter(r['status'] for r in rows)),'fixed_attempts':len(d['rows']),'independent_n_added':0,'confirmation_n':0,'replication_n':0,'land_n_added':0,'interpretation':'Physical operational checks only. All scheduled failures and missingness retained. Repeats are not study N or causal rejection-rate/equivalence estimates. No method answers or scores read.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('declaration');p.add_argument('--output',required=True);a=p.parse_args();d=profile(a.declaration)
    with Path(a.output).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
    print(json.dumps(d['dispositions']))
