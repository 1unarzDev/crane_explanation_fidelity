"""Replay already exposed labels through the reusable blinded workflow.

No new judgments, method outputs, confirmation relabeling or significance test.
The reconstructed registry demonstrates mechanics, not historical preregistration.
"""
import hashlib
import json
from pathlib import Path
import secrets

from .blinded_scoring_workflow import reference_registry, prepare, select_C, finalize
from .development_unique_scoring_v2 import job as prior_job
from .journal import exclusive_json
from ..acquisition.navigation_usefulness_v2 import public_packet, reference

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'manifests/hexar_external/confirmatory_v1'


def report(destination):
    method_path = BASE / 'development_unique_methods_v2/report.json'
    plan_path = BASE / 'development_unique_methods_v2/unique_request_plan.json'
    score_path = BASE / 'development_unique_scoring_v2/report.json'
    packet_path = ROOT / 'manifests/hexar_external/acquisition/controller_boundary_qualification_v13.json'
    methods, plan, score, packets = (json.loads(p.read_text()) for p in
                                    (method_path, plan_path, score_path, packet_path))
    if any(v.get('phase') != 'development_only' for v in (methods, score, packets)):
        raise ValueError('completed retained development artifacts required')
    entries = []
    for row in packets['packets']:
        packet = public_packet(row['method_packet'])
        entries.append(dict(episode_id=row['development_id'], job_id=row['question_id']+'-'+row['condition'],
                            packet=packet, reference=reference(packet)))
    registry = reference_registry(entries)
    public, private = prepare(plan, methods['answers'], registry, secrets.token_bytes(32), 2026100111)
    attempts = {}
    prior = {r['opaque_job']: r for r in score['attempts']}
    for mapping in private['entries']:
        for slot in ('A', 'B'):
            uid = prior_job(dict(unique_request_id=mapping['unique_request_id'], payload=None), slot)['opaque_job']
            attempt = prior[uid]
            folder = BASE / 'development_unique_scoring_v2' / uid
            for label, filename in (('stdout', 'stdout.jsonl'), ('stderr', 'stderr.txt'), ('final', 'raw_final.json')):
                if hashlib.sha256((folder / filename).read_bytes()).hexdigest() != attempt['raw_sha256'][label]:
                    raise ValueError('retained development judge bytes changed')
            attempts[mapping['opaque_slots'][slot]] = attempt
    if select_C(public, attempts):
        raise ValueError('retained v2 workflow unexpectedly requires new C; no new call permitted')
    result = finalize(plan, methods['answers'], registry, public, private, attempts, {})
    if result['paired_counts'] != score['conservative_mapped_development_cells']:
        raise ValueError('reusable workflow changes retained development endpoints')
    sources = [Path(__file__), Path(__file__).with_name('blinded_scoring_workflow.py'),
               Path(__file__).with_name('rich_adjudication.py'), method_path, plan_path, score_path, packet_path,
               ROOT / 'analysis/hexar_external/acquisition/navigation_usefulness_v2.py']
    destination.mkdir(exist_ok=False)
    exclusive_json(destination / 'reconstructed_reference_registry.json', registry)
    exclusive_json(destination / 'public_scoring_plan.json', public)
    exclusive_json(destination / 'sealed_method_linkage.json', private)
    exclusive_json(destination / 'closed_dispositions.json', result)
    value = dict(schema='hexar-development-reusable-workflow-replay/v1', phase='development_only',
        status='RETAINED_WORKFLOW_REPRODUCED_NOT_FINAL_ADAPTER_QUALIFICATION',
        historical_raw_judge_attempts_verified=144, unique_outcomes=72, battery_cells=108,
        independent_development_episodes=6, paired_counts=result['paired_counts'],
        new_provider_calls=0, confirmatory_N=0, alpha_consumed=0, significance_test_performed=False,
        agent_assessed=True, human_validated=False,
        chronology='Registry reconstructed from exposed packets to test mechanics; not a prospective registry for these historical outputs.',
        source_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    exclusive_json(destination / 'report.json', value)
    print(value['status'], result['paired_counts'])


if __name__ == '__main__':
    report(BASE / 'development_workflow_replay_v1')
