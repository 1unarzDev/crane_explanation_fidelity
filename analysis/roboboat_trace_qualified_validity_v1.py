"""Prospective development validity candidate; never salvages an old recording.

Correct stale rejection can be an execution observation. This candidate reproduces
all other benchmark-validity conditions and requires complete, source-specific trace
qualification. Selection uses no explanation output or navigation success.
"""
import re
from audit_roboboat_action_trace_v1 import audit as audit_trace
from audit_roboboat_trace_semantics_v1 import audit as audit_semantics
from run_roboboat_population_development_v8 import technical_checks as strict_checks

SCHEMA='roboboat-trace-qualified-validity/v1-development-candidate'
BENCHMARK_ZERO_FIELDS=('loggedErrors','loggedExceptions','failedObservations','staleObservations',
                      'staleActions','crossEpisodeActions','depthBufferValidationMismatches','invalidWaterSearches')


def assess(summary, worker, fixture, records, player_log):
    checks=strict_checks(summary,worker,fixture)
    inherited_failures=[k for k,v in checks.items() if not v]
    # Match the source expression exactly instead of broadly ignoring worker.valid.
    expected_valid=all(type(worker.get(k)) is int and worker[k]==0 for k in BENCHMARK_ZERO_FIELDS)
    checks.pop('worker_valid');checks.pop('stale_actions_zero');checks.pop('rejected_actions_zero')
    checks['benchmark_validity_source_reconstructed']=(type(worker.get('valid')) is bool and worker['valid']==expected_valid)
    for field in BENCHMARK_ZERO_FIELDS:
        if field!='staleActions':checks['retained_benchmark_'+field]=type(worker.get(field)) is int and worker[field]==0
    for field in ('duplicateActions','unknownSourceActions'):
        checks[field+'_zero']=type(worker.get(field)) is int and worker[field]==0
    stale=worker.get('staleActions');rejected=worker.get('rejectedActions')
    checks['only_stale_rejections']=(type(stale)is int and type(rejected)is int and stale>=0 and rejected==stale)
    trace=audit_trace(records,worker=worker);semantics=audit_semantics(records)
    checks['whole_command_trace_integrity']=trace['trace_integrity_pass']
    checks['clock_and_ros_payload_semantics']=semantics['checks_pass']
    checks['no_pending_receipt_at_shutdown']=trace['pending_receipts']==0
    snapshot=next((e for e in records if e.get('kind')=='counter_snapshot' and e.get('episode')==worker.get('episodeId')),None)
    decisions=[e for e in records if e.get('kind')=='gate_decision']
    checks['exact_common_ros_gate_contract']=bool(decisions) and all(e['source']=='ros:/crane/cmd_vel_stamped' and e['policy']=='BoundedLag' and e['maximumLagTicks']==10 and e['sourceTick']>=0 for e in decisions)
    check_decisions=[e for e in decisions if snapshot and e['ordinal']<snapshot['ordinal'] and e['decisionEpisode']==worker['episodeId']]
    accepted_ticks={e['applicationTick'] for e in check_decisions if e['reason']=='None'}
    # Warning logs establish aggregate timeout observation and last accepted tick,
    # never the exact transition tick or motor response.
    warnings=re.findall(r'CRANE_ROS_COMMAND_TIMEOUT topic=/crane/cmd_vel_stamped lastApplicationTick=(\d+)',player_log)
    count=worker.get('actionTiming',{}).get('commandTimeouts')
    checks['timeout_warning_aggregate_reconciled']=type(count)is int and count>=0 and len(warnings)==count and all(int(t) in accepted_ticks for t in warnings)
    ready=re.findall(r'CRANE_ROS_COMMAND_READY topic=/crane/cmd_vel_stamped[^\n]*linearScale=([^ ]+) yawScale=([^ ]+)',player_log)
    checks['declared_velocity_scales_observed']=ready==[('1','1')]
    checks['clamped_payload_within_unit_scales']=all(abs(r[k])<=1 for r in semantics['desired_velocity_component_ranges'] for k in ('minimum','maximum'))
    return {'schema':SCHEMA,'candidate_qualified':all(checks.values()),'checks':checks,
            'inherited_strict_failures':inherited_failures,'stale_rejections_observed':stale,
            'worker_valid_original':worker.get('valid'),'benchmark_validity_expected':expected_valid,
            'trace':trace,'semantics':semantics,'timeout_warnings_observed':len(warnings),
            'scientific_admission_authorized':False,'prior_dispositions_changed':False,
            'confirmation_n':0,'replication_n':0,'new_independent_n':0,
            'limitations':['Candidate only: prospective capture declaration, bound-source review and instrumentation qualification are separate prerequisites.',
                'Stamped source age is forwarded latest-odometry provenance, not proof of Nav2 observation consumption or a network-delay cause.',
                'Accepted callbacks set desired velocity; timeout warnings describe aggregate controller events without proving physical stopping.',
                'No equality of raw Twist values and clamped desired velocity or cross-process clock mapping is established.']}
