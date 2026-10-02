"""Root engineering review for exploratory collection; no confirmation or equivalence."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from profile_roboboat_clock_repair_operational_v11 import profile
from roboboat_owned_player_bundle_v1 import binding, verify_build
from prepare_roboboat_baseline_interface_v1 import checked
from prepare_roboboat_baseline_interface_v3 import compiled_source_bindings


def review(declaration_path, build_manifest, source_audit, test_report):
    declaration_path,build_manifest,source_audit,test_report=map(lambda p:Path(p).resolve(),(declaration_path,build_manifest,source_audit,test_report))
    d=json.loads(declaration_path.read_text());p=profile(declaration_path)
    terminal_path=Path(d['output_root'])/'terminal.json'
    if not terminal_path.exists():raise ValueError('fixed operational batch has no terminal verdict yet')
    terminal=json.loads(terminal_path.read_text())
    if terminal['status']!='CLOCK_REPAIR_OPERATIONAL_BATCH_FINISHED' or terminal['physical_attempts']!=4 or terminal['declaration_sha256']!=binding(declaration_path)['sha256']:
        raise ValueError('operational batch/declaration mismatch')
    if p['dispositions']!={'VALID_TRACE_QUALIFIED_DEVELOPMENT':4} or any(r.get('trace_integrity_pass')is not True or r.get('trace_issues')!=[] for r in p['rows']):
        raise ValueError('retained operational outcomes require further engineering diagnosis')
    if len(terminal['results'])!=4 or [r['row']['id'] for r in terminal['results']]!=d['rows']:
        raise ValueError('terminal result identities differ from fixed schedule')
    bound={i['path']:i['sha256'] for i in d['dependencies']}
    if bound.get(str(build_manifest))!=binding(build_manifest)['sha256'] or bound.get(str(test_report))!=binding(test_report)['sha256']:
        raise ValueError('build and regression tests must predate the operational probe')
    manifest,_=verify_build(build_manifest)
    for item in manifest['source_bindings_current']:checked(item)
    sources=compiled_source_bindings(source_audit,build_manifest)
    xml=ET.parse(test_report).getroot()
    names={t.get('methodname') for t in xml.findall('.//test-case') if t.get('result')=='Passed'}
    required={'NavigationPublisherContinuesAfterBenchmarkClockResetWithoutBodyReset','RosClockDoesNotRetainWarmupDeadlineAfterBenchmarkClockReset','NavigationPublisherPreservesSameEpisodeDeadline','RosClockPreservesSameEpisodeDeadline','NavigationPublisherPreservesExplicitBeforePhysicsReset','RosClockPreservesExplicitBeforePhysicsReset'}
    if xml.get('failed')!='0' or not required<=names:raise ValueError('publisher repair regression tests incomplete')
    return {'schema':'roboboat-clock-repair-engineering-qualification/v1','status':'READY_FOR_CLOCK_REPAIRED_EXPLORATORY_COLLECTION','build_manifest':binding(build_manifest),'source_audit':binding(source_audit),'tests':binding(test_report),'review_source':binding(__file__),'operational_declaration':binding(declaration_path),'operational_terminal':binding(terminal_path),'operational_profile':p,'operational_checks_complete':True,'repaired_source_scope':'EpisodeId-bound scheduling of authoritative odometry and ROS clock; all tested same-episode and explicit-reset behaviors preserved','compiled_common_sources':len(sources),'reviewer':'root engineering/source review; not independent model judging or human annotation','interpretation':'Four predeclared operational replays across two previously failed geometries now pass all inherited gates, including full trace integrity. Supports exploratory use of explicitly revised platform only. Does not establish physics equivalence, population failure rate, causal rejection-rate reduction or B4-B2 superiority. Original failures unchanged.','independent_n_added':0,'confirmation_authorized':False,'confirmation_n':0,'replication_n':0,'land_n_added':0,'method_call_readiness':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('declaration','build-manifest','source-audit','test-report','output'):parser.add_argument('--'+name,required=True)
    a=parser.parse_args();value=review(a.declaration,a.build_manifest,a.source_audit,a.test_report)
    with Path(a.output).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(value['status'])
