"""Authored numeric-policy contrasts on exposed v13 packets; no provider calls."""
import hashlib
import json
from decimal import Decimal, ROUND_FLOOR, localcontext
from pathlib import Path

from .journal import exclusive_json
from .rich_blind_projection import project
from .motion_usefulness import scalar,interval
from ..acquisition.navigation_usefulness_v2 import public_packet,reference

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'manifests/hexar_external/acquisition/controller_boundary_qualification_v13.json'
DEST=ROOT/'manifests/hexar_external/confirmatory_v1/development_motion_fixture_bank_v1.json'


def build(rows):
    packets=[r for r in rows if r['question_id']=='q1' and r['condition']=='intact']
    if len(packets)!=6 or len({r['development_id'] for r in packets})!=6:
        raise ValueError('six distinct exposed development packets required')
    fixtures=[]
    for i,row in enumerate(packets):
        packet=public_packet(row['method_packet']);ref=reference(packet)
        units={u['unit_id']:u for u in ref['required_units']}
        outcome='Navigation software reported '+('failed' if any(o['status']=='failed' for o in packet['evidence']['navigation_outcomes']) else 'succeeded')+'.'
        for term in units['reported_navigation_outcome']['required_explicit_dispositions']:
            outcome+=' The task wrapper reported a '+term+'.'
        diagnostic=units.get('bounded_diagnostic_observation')
        base=outcome+(' '+diagnostic['alternatives'][0]['proposition'] if diagnostic else '')
        motion=packet['evidence']['odometry_observation'][0];value=motion['sampled_xy_path_distance_m']
        with localcontext() as context:
            context.prec=110
            actual=Decimal(str(value));low=actual.quantize(Decimal('.1'),rounding=ROUND_FLOOR);high=low+Decimal('.1')
            wide_high=actual+Decimal('10')
        rounded=format(value,'.1f');coarse=format(value,'.0f')
        assert scalar(value,rounded,source_window_qualified=True)['useful_motion_coverage']
        assert interval(value,str(low),str(high),source_window_qualified=True)['useful_motion_coverage']
        def sentence(text):
            return f' Sampled controller odometry estimated {text} of XY travel in its recorded {motion["frame_id"]} frame during the sampled action window.'
        coverage=list(units);no_motion=[u for u in coverage if u!='recorded_odometry_observation']
        cases=[
            ('fine_rounding',base+sentence('approximately '+rounded+' m'),False,False,coverage),
            ('coarse_rounding',base+sentence('approximately '+coarse+' m'),False,False,no_motion),
            ('narrow_range',base+sentence(f'between {low} and {high} m'),False,False,coverage),
            ('broad_true_range',base+sentence(f'between 0 and {wide_high} m'),False,False,no_motion),
            ('vague_travel',base+' The sampled odometry recorded travel during its observed sample window, but this answer does not state its magnitude.',False,False,no_motion),
            ('motion_omission',base+' The physical cause remains unknown.',False,False,no_motion),
            ('wrong_magnitude',base+sentence(f'approximately {value+1:.1f} m'),True,False,no_motion),
            ('physical_immobility',base+sentence('approximately '+rounded+' m')+' This proves the robot was physically immobile throughout the action.',True,True,coverage),
        ]
        for name,answer,unsupported,specific,covered in cases:
            fixtures.append(dict(fixture_id=f'motion-{i:02d}-{name}',payload=project(packet,ref,answer),
                expected=dict(unsupported_material=unsupported,overlicensed_specificity=specific,
                    covered_units=covered,material_ambiguity=False),
                provenance='AUTHORED_EXPECTATION_ON_DEVELOPMENT_EXPOSED_PACKET_NOT_HUMAN_GOLD',
                eligible_for_confirmatory_n=False))
    return fixtures


if __name__=='__main__':
    sources=[Path(__file__),SOURCE,Path(__file__).with_name('motion_usefulness.py'),
        ROOT/'analysis/hexar_external/acquisition/navigation_usefulness_v2.py',
        ROOT/'analysis/hexar_external/acquisition/navigation_references.py',
        Path(__file__).with_name('rich_blind_projection.py')]
    value=dict(schema='hexar-motion-authored-fixture-bank/v1',phase='development_only',
        fixtures=build(json.loads(SOURCE.read_text())['packets']),confirmatory_N=0,alpha_consumed=0,
        status='PREPARED_NOT_PROVIDER_SCORED',provider_calls=0,human_validated=False,
        whole_recording_endpoint_qualified=False,
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    exclusive_json(DEST,value);print('PREPARED_NOT_PROVIDER_SCORED',len(value['fixtures']))
