#!/usr/bin/env python3
"""One-shot, inspected development replay: new identities, no new recording N."""
import hashlib
import json
from pathlib import Path
from roboboat_temporal_certificate_v2 import upgrade_development_packet, audit_ladder, certificate, render
from reference_roboboat_temporal_v2 import calculate

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/roboboat-contact-policy-v2/replay'
TASK=ROOT/'docs/roboboat_terminal_evidence/task_contract_v2.json'


def main():
    OUT.mkdir(parents=True,exist_ok=False)
    task=json.loads(TASK.read_text());bindings=[];records=[]
    for episode in ('boat-terminal-settling-001','boat-terminal-settling-002'):
        levels=[]
        for level in ('L0','L1','L2'):
            source=ROOT/'artifacts/roboboat-terminal-settling-v1/batches'/episode/'method_packets'/f'{level}.json'
            old=json.loads(source.read_text())
            packet=upgrade_development_packet(old,episode+'-contact-policy-v2',task)
            cert=certificate(packet);reference=calculate(packet)
            assert cert['sampled_task_support']==reference['sampled_task_support']=='unknown'
            assert cert['component_support']['contact']==reference['contact_support']=='unknown'
            target=OUT/episode;target.mkdir(exist_ok=True)
            (target/f'{level}-packet.json').write_text(json.dumps(packet,indent=2)+'\n')
            (target/f'{level}-development.json').write_text(json.dumps({'certificate':cert,'independent_reference':reference,'answer':render(packet,cert)},indent=2)+'\n')
            levels.append(packet)
            bindings.append({'path':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
            records.append({'episode':episode,'level':level,'support':cert['sampled_task_support'],'contact_support':cert['component_support']['contact']})
        audit_ladder(levels)
    dependencies=[TASK,Path(__file__).resolve(),ROOT/'analysis/roboboat_temporal_certificate_v2.py',ROOT/'analysis/reference_roboboat_temporal_v2.py',ROOT/'analysis/roboboat_temporal_certificate.py',ROOT/'analysis/reference_roboboat_temporal.py',*[ROOT/f'analysis/roboboat_temporal_renderer_v{i}.py' for i in (2,3,4)]]
    bindings += [{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in dependencies]
    (OUT/'development-audit.json').write_text(json.dumps({'status':'PASS','disposition':'INSPECTED_DEVELOPMENT_REPLAY_ONLY','records':records,'source_bindings':bindings,'new_recordings':0,'new_independent_configuration_clusters':0,'synthetic_contact_observations_exported':False,'annotation_qualification_established_by_this_replay':False,'alpha_consumed':0},indent=2)+'\n')
    print('six successor packets independently checked; two removal-only ladders pass')


if __name__=='__main__':main()
