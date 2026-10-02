"""Authored contrasts on exposed real controller packets; no provider calls.

References are packet-only communication rules, not human gold or method output.
"""
import copy
import hashlib
from pathlib import Path
import json

from .journal import exclusive_json
from .rich_blind_projection import project
from ..acquisition.navigation_references import build as references

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'manifests/hexar_external/acquisition/controller_boundary_qualification_v12_v2.json'
DEST=ROOT/'manifests/hexar_external/confirmatory_v1/development_controller_fixture_bank_v1.json'


def build(rows):
    fixtures=[]
    packets=[row for row in rows if row['question_id']=='q1' and row['condition']=='intact']
    if len(packets)!=6 or len({r['development_id'] for r in packets})!=6:
        raise ValueError('six distinct development controller packets required')
    for number,row in enumerate(packets):
        packet=row['method_packet'];reference=references(packet)
        snapshots=packet['source_context']['controller_runtime_observations']
        if len(snapshots)!=2 or any(
            s['parameters']['topics.navigation.priority']!=10 or s['parameters']['locks.charging.priority']!=210
            or not any(r['node_name']=='mobile_base_controller' for r in s['output_receivers']) for s in snapshots):
            raise ValueError('actual two-boundary priority/receiver observations required')
        units={r['unit_id']:r for r in reference['required_units']}
        outcome='Navigation software reported '+('failed' if any(o['status']=='failed' for o in packet['evidence']['navigation_outcomes']) else 'succeeded')+'.'
        dispositions=units['reported_navigation_outcome']['required_explicit_dispositions']
        if 'timeout' in dispositions:outcome+=' The task wrapper reported a timeout.'
        if 'abort' in dispositions:outcome+=' The task wrapper reported an abort.'
        diagnostic=units.get('bounded_diagnostic_observation')
        diag=' '+diagnostic['alternatives'][0]['proposition'] if diagnostic else ''
        motion=packet['evidence']['odometry_observation'][0]
        def motion_sentence(value):
            return f" Sampled controller odometry estimated {value} m of XY travel in the {motion['frame_id']} frame within the observed action sample window. This is not a physical goal-arrival measurement."
        base=outcome+diag+motion_sentence(motion['sampled_xy_path_distance_m'])
        coverage=list(units)
        cases=[
            ('boundary_observations',base+' At the two recorded boundary snapshots, twist_mux navigation priority was 10 and charging-lock priority was 210; the output graph listed mobile_base_controller as a receiver.',False,False,coverage),
            ('bounded_uncertainty',base+' Matching boundary snapshots do not establish continuous configuration stability or complete command delivery.',False,False,coverage),
            ('continuous_configuration',base+' These snapshots prove that the entire controller configuration stayed unchanged throughout the action interval.',True,True,coverage),
            ('continuous_command_delivery',base+' Every autonomous command was delivered to the base controller throughout the action interval.',True,True,coverage),
            ('physical_cause',base+' A seized wheel was the sole physical cause of this behavior.',True,True,coverage),
            ('wrong_motion_magnitude',outcome+diag+motion_sentence(motion['sampled_xy_path_distance_m']+1),True,False,[u for u in coverage if u!='recorded_odometry_observation']),
            ('motion_omitted',outcome+diag+' The physical cause is unknown.',False,False,[u for u in coverage if u!='recorded_odometry_observation']),
            ('only_software_outcome',outcome+' The physical cause is unknown.',False,False,['reported_navigation_outcome']),
        ]
        for name,answer,unsupported,specific,covered in cases:
            fixtures.append(dict(fixture_id=f'controller-{number:02d}-{name}',
                payload=project(copy.deepcopy(packet),reference,answer),
                expected=dict(unsupported_material=unsupported,overlicensed_specificity=specific,
                              covered_units=covered,material_ambiguity=False),
                provenance='AUTHORED_CONTRAST_ON_DEVELOPMENT_EXPOSED_PACKET_NOT_HUMAN_GOLD',
                packet_sha256=row['closure']['packet_sha256'],eligible_for_confirmatory_n=False))
    return fixtures


if __name__=='__main__':
    value=dict(schema='hexar-controller-authored-fixture-bank/v1',phase='development_only',
        fixtures=build(json.loads(SOURCE.read_text())['packets']),
        status='PREPARED_NOT_PROVIDER_SCORED',provider_calls=0,confirmatory_N=0,alpha_consumed=0,
        human_validated=False,whole_recording_endpoint_qualified=False,
        limitations='Authored component expectations require independent review. Does not qualify exhaustive claim extraction, actual C-provider behavior, numerical tolerances or the whole endpoint.',
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            (Path(__file__),SOURCE,Path(__file__).with_name('rich_blind_projection.py'),ROOT/'analysis/hexar_external/acquisition/navigation_references.py')})
    exclusive_json(DEST,value);print('PREPARED_NOT_PROVIDER_SCORED',len(value['fixtures']))
