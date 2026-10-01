"""Development marine adapter for the shared CRANE planner and realizer.

Zero model calls: static claim contracts, visible-packet computations, maximal
supported diagnosis, closed-template realization, atomic verification/local repair.
This is an additive candidate, not a relabeling of historical renderer outputs.
The whole packet is the provenance unit; numeric bindings additionally retain
JSON pointers or explicitly named certificate computations. No evaluator input
or caller-supplied certificates/facts/plans are accepted by ``explain``.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

from evidence_calibration_io import canonical_sha256, canonical_json_bytes
from maximal_supported_diagnosis import diagnose, FACT_SCHEMA
from realize_evidence_calibrated_explanation import realize, PLAN_SCHEMA, CANDIDATE_SCHEMA
from roboboat_temporal_certificate_v2 import certificate

CATALOG = Path(__file__).resolve().parents[1] / 'configs/roboboat_claim_contracts_v1_development.json'
KINEMATIC = ('position', 'heading', 'speed', 'yaw_rate', 'hull')


def build_inputs(packet, *, configuration_id, episode_id, condition_id):
    """Compute all facts from a validated v2 robot-visible packet only."""
    cert = certificate(packet)  # validates nested allowlists and computes temporal facts
    if packet['action']['status'] not in ('succeeded', 'aborted', 'canceled'):
        raise ValueError('unregistered action status; extend development contracts explicitly')
    for name, value in [('configuration_id', configuration_id), ('episode_id', episode_id),
                        ('condition_id', condition_id)]:
        if not isinstance(value, str) or not value:
            raise ValueError(name + ' must be a nonempty identifier')
    ontology = json.loads(CATALOG.read_text())
    ref = 'marine-packet-' + canonical_sha256(packet)
    method = {'evidence': {'marine_visible_packet': {'evidence_id': ref,
                                                   'packet': copy.deepcopy(packet)}}}
    entry = {'condition': {'configuration_id': configuration_id, 'episode_id': episode_id,
                          'condition_id': condition_id, 'available_evidence_ids': [ref],
                          'method_packet_sha256': canonical_sha256(method)}, 'method_packet': method}
    approved, values, bindings = set(), [], []

    def support(identifier, numeric=None):
        approved.add('req-' + identifier)
        for slot, (value, unit, source) in (numeric or {}).items():
            values.append({'claim_id': 'claim-' + identifier, 'slot_id': slot, 'value': value,
                           'unit': unit, 'support_reference': ref})
            bindings.append({'claim_id': 'claim-' + identifier, 'slot_id': slot,
                             'source': source, 'packet_sha256': canonical_sha256(packet)})

    support('evidence-scope')
    support('action-' + packet['action']['status'])
    support({'false': 'dwell-failed', 'true': 'dwell-sampled-success',
             'unknown': 'dwell-unknown'}[cert['sampled_task_support']])
    if cert['interval_s'][0] is not None:
        support('dwell-anchor', {slot: (value, 's', 'certificate.interval_s')
                for slot, value in zip(('interval_start', 'interval_end'), cert['interval_s'])})
    ret = cert['return_observation']
    if ret is not None:
        support('return-position', {
            'observation_time': (ret['time_s'], 's', '/return_observation/simSeconds'),
            'position_error': (ret['position_error_m'], 'm', 'measure(return_observation).position_error_m'),
            'position_margin': (ret['signed_margins']['position'], 'm', 'measure(return_observation).signed_margins.position'),
            'position_bound': (packet['task']['position_tolerance_m'], 'm', '/task/position_tolerance_m')})
        support('return-heading', {
            'heading_error': (ret['heading_error_rad'], 'rad', 'measure(return_observation).heading_error_rad'),
            'heading_bound': (packet['task']['heading_tolerance_rad'], 'rad', '/task/heading_tolerance_rad')})
        if ret['speed_mps'] is not None:
            support('return-speed', {
                'measured_speed': (ret['speed_mps'], 'm/s', 'measure(return_observation).speed_mps'),
                'speed_bound': (packet['task']['speed_tolerance_mps'], 'm/s', '/task/speed_tolerance_mps')})
    if cert['radial_error_growth_m'] is not None:
        support('radial-change', {'radial_error_change': (cert['radial_error_growth_m'], 'm', 'certificate.radial_error_growth_m')})
    keys = {'position': ('position_error_m', 'position_tolerance_m', 'm'),
            'heading': ('heading_error_rad', 'heading_tolerance_rad', 'rad'),
            'speed': ('speed_mps', 'speed_tolerance_mps', 'm/s'),
            'yaw_rate': (None, 'yaw_rate_tolerance_radps', 'rad/s'),
            'hull': (None, None, 'm')}
    for component in KINEMATIC:
        state = cert['component_support'][component]
        if state == 'false':
            witness = cert['witnesses'][component]
            metric, bound_key, unit = keys[component]
            bound = packet['task'][bound_key] if bound_key else 0
            margin = witness['signed_margins'][component]
            measured = witness[metric] if metric else (bound - margin if component == 'yaw_rate' else margin)
            source = 'certificate.witnesses.' + component
            support(component + '-violation', {
                'witness_time': (witness['time_s'], 's', source + '.time_s'),
                'measured_value': (measured, unit, source + ':source-qualified-measurement'),
                'requirement_bound': (bound, unit, '/task/' + bound_key if bound_key else 'public-hull-containment-zero-margin'),
                'signed_margin': (margin, unit, source + '.signed_margins.' + component)})
        elif state == 'true':
            support(component + '-compliance', {
                'sample_count': (cert['coverage']['sample_count'], 'samples', 'certificate.coverage.sample_count'),
                'maximum_gap': (cert['coverage']['max_gap_s'], 's', 'certificate.coverage.max_gap_s')})
        else:
            support(component + '-unknown')
    contact = cert['component_support']['contact']
    if contact == 'false':
        witness = cert['witnesses']['contact']
        support('contact-violation', {'witness_time': (witness['time_s'], 's', 'certificate.witnesses.contact.time_s'),
                                    'observed_events': (witness['count'], 'events', 'certificate.witnesses.contact.count')})
    else:
        support('contact-compliance' if contact == 'true' else 'contact-unknown')
    facts = {'schema': FACT_SCHEMA, 'condition_id': condition_id,
             'method_packet_sha256': canonical_sha256(method),
             'question_contract': {'question_id': 'roboboat-docking-diagnostic-v1',
                                   'failure_premise': False,
                                   'required_mechanism_families': ['action', 'docking']},
             'requirement_evaluations': [
                 {'requirement_id': row['requirement_id'],
                  'status': 'SATISFIED' if row['requirement_id'] in approved else 'ABSENT',
                  'support_references': [ref] if row['requirement_id'] in approved else [],
                  'detail': 'Computed from validated visible packet by marine adapter v1.'}
                 for row in ontology['evidence_requirements']], 'ambiguity_node_ids': []}
    return ontology, entry, facts, values, bindings


def explain(packet, *, configuration_id, episode_id, condition_id, candidate=None):
    ontology, entry, facts, values, bindings = build_inputs(
        packet, configuration_id=configuration_id, episode_id=episode_id, condition_id=condition_id)
    result = diagnose(ontology, entry, facts)
    plan = {'schema': PLAN_SCHEMA, 'plan_id': condition_id + '-full-crane-v1',
            'diagnostic_result_sha256': canonical_sha256(result),
            'required_claim_ids': list(result['approved_claim_ids']), 'optional_claim_ids': [],
            'required_non_entailment_ids': list(result['required_non_entailment_ids']),
            'approved_numeric_values': values}
    if candidate is None:
        clauses = []
        for identifier in plan['required_claim_ids']:
            numeric = [{key: value[key] for key in ('slot_id', 'value', 'unit')}
                       for value in values if value['claim_id'] == identifier]
            clauses.append({'clause_id': identifier, 'kind': 'CLAIM',
                            'contract_id': identifier, 'numeric_values': numeric})
        clauses += [{'clause_id': identifier, 'kind': 'NON_ENTAILMENT',
                     'contract_id': identifier, 'numeric_values': []}
                    for identifier in plan['required_non_entailment_ids']]
        candidate = {'schema': CANDIDATE_SCHEMA, 'response_id': condition_id + '-response',
                     'plan_sha256': canonical_sha256(plan), 'clauses': clauses}
    # The shared verifier uses numeric deltas; reject NaN before that comparison
    # (NaN > tolerance is false). Finite wrong values still receive local repair.
    for clause in candidate.get("clauses", []):
        for numeric in clause.get("numeric_values", []):
            value = numeric.get("value")
            if isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isfinite(value):
                raise ValueError("candidate numeric value must be finite")
    # Verification must retain generic repair behavior without trusting free text.
    realization = realize(ontology, result, plan, candidate)
    return {'schema': 'roboboat-full-crane/v1-development', 'development_only': True,
            'realization_mode': 'deterministic-zero-model-closed-template',
            'packet_sha256': canonical_sha256(packet), 'ontology_sha256': canonical_sha256(ontology),
            'condition_entry': entry, 'facts': facts, 'diagnostic_result': result,
            'plan': plan, 'numeric_source_bindings': bindings, 'candidate': candidate,
            'realization': realization}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    for field in ('configuration-id', 'episode-id', 'condition-id'):
        parser.add_argument('--' + field, required=True)
    args = parser.parse_args()
    result = explain(json.loads(args.packet.read_text()), configuration_id=args.configuration_id,
                     episode_id=args.episode_id, condition_id=args.condition_id)
    args.output.write_bytes(canonical_json_bytes(result) + b'\n')


if __name__ == '__main__':
    main()
