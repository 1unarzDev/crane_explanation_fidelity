#!/usr/bin/env python3
"""Same-source/contract development responses, with judgments kept separate."""
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from build_roboboat_terminal_batch import ROOT,DOC,save,digest
from roboboat_isolated_transport import call
from run_roboboat_terminal_comparison import SCHEMA

OUT=ROOT/'artifacts/roboboat-contact-policy-comparison-v2'
DECLARATION=DOC/'contact_policy_response_declaration_v2.json'


def execute(entry,declaration):
    output=OUT/'responses'/entry['id'];terminal=output/'response-terminal.json'
    identity={'declaration_sha256':digest(DECLARATION),'packet_sha256':entry['packet']['sha256'],'candidate_sha256':entry['candidate']['sha256']}
    if terminal.exists():
        if json.loads(terminal.read_text())['source_identity']!=identity:
            raise ValueError('terminal identity differs')
        return
    intent=OUT/'intents'/f"{entry['id']}.json";intent.parent.mkdir(parents=True,exist_ok=True)
    with intent.open('x') as f:json.dump(identity,f)
    packet=json.loads((ROOT/entry['packet']['path']).read_text())
    with tempfile.TemporaryDirectory(prefix='boat-contact-v2-response-') as tmp:
        work=Path(tmp);save(work/'evidence.json',packet)
        for source in declaration['method_sources']:
            p=ROOT/source['path'];shutil.copyfile(p,work/p.name)
        shutil.copyfile(ROOT/entry['effective_configuration']['path'],work/'effective-configuration.yaml')
        save(work/'configuration-basis.json',{'goal_checker_values':'pre-action-node-plugin-specific-ROS-readback','remaining_configuration':'declared-launch-profile','serialization':'config_sha256 identifies this derived effective YAML, not the raw launch file','internal-consumption-of-odometry-proven':False})
        result=call(OUT/'calls',entry['id'],work,(DOC/'marine_b2_contact_policy_prompt_v2.txt').read_text(),
                    declaration['B2']['model'],declaration['B2']['effort'],SCHEMA,allow_tools=True,timeout=300)
    save(output/'B2.json',{'answer':result['parsed_final']['answer'],'cache_key':result['cache_key'],'latency_s':result['latency_s'],'model_calls':1})
    save(output/'B4.json',{'answer':json.loads((ROOT/entry['candidate']['path']).read_text())['answer'],'model_calls':0})
    save(terminal,{'source_identity':identity,'status':'COMPLETE_RESPONSE_SUPPORT_UNJUDGED','new_configuration_cluster_n':0,'confirmation_n':0,'alpha_consumed':0})
    print('responses retained',entry['id'],flush=True)


def main():
    d=json.loads(DECLARATION.read_text())
    if d['disposition']!='INSPECTED_DEVELOPMENT_RESPONSE_REPLAY_ONLY':
        raise ValueError('development gate closed')
    for b in d['dependencies']+d['method_sources']:
        if digest(ROOT/b['path'])!=b['sha256']:raise ValueError('frozen input changed: '+b['path'])
    for entry in d['entries']:
        execute(entry,d)


if __name__=='__main__':main()
