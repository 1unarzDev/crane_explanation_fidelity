#!/usr/bin/env python3
"""One-shot bounded contact/coverage extension of the currently bound judge."""
import hashlib
import json
from pathlib import Path
from run_evidence_calibration_agent_qualification import run
from run_evidence_calibration_agent_annotation import StructuredCodexCliAgentCaller
from roboboat_isolated_transport import isolated_run

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/roboboat_terminal_evidence'
OUT=ROOT/'artifacts/roboboat-contact-policy-v2/qualification'


def main():
    freeze_path=DOC/'contact_policy_qualification_freeze_v2.json'
    freeze=json.loads(freeze_path.read_text())
    for item in freeze['dependencies']:
        if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('frozen qualification dependency changed: '+item['path'])
    binding=json.loads((ROOT/'manifests/study/evidence-calibration-agent-qualification-disposition-v1.json').read_text())['qualified_binding']
    if (binding['model'],binding['reasoning_effort'])!=(freeze['candidate']['model'],freeze['candidate']['reasoning_effort']):
        raise ValueError('current qualified binding differs')
    OUT.mkdir(parents=True,exist_ok=False)
    (OUT/'intent.json').write_text(json.dumps({'freeze_sha256':hashlib.sha256(freeze_path.read_bytes()).hexdigest(),'quality_retries':0,'timeout_s':300},indent=2)+'\n')
    try:
        result=run(DOC/'contact_policy_qualification_suite_v2.json',freeze_path,OUT,
            caller_factory=lambda cache:StructuredCodexCliAgentCaller(cache,model=binding['model'],effort=binding['reasoning_effort'],timeout_s=300,runner=isolated_run))
    except Exception as exc:
        (OUT/'retained-failure.json').write_text(json.dumps({'status':'RETAINED_FAILURE_NO_RETRY','type':type(exc).__name__,'detail':str(exc)},indent=2)+'\n')
        raise
    print(result['status'],flush=True)


if __name__=='__main__':main()
