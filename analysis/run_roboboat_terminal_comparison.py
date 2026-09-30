#!/usr/bin/env python3
"""One-shot exploratory paired methods and current two-pass qualified annotations."""
import argparse,copy,hashlib,json,re,shutil,tempfile
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from roboboat_isolated_transport import call,isolated_run
from run_evidence_calibration_agent_annotation import run as annotate,StructuredCodexCliAgentCaller
from build_roboboat_terminal_batch import save
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/roboboat_terminal_evidence'
SCHEMA={'type':'object','properties':{'answer':{'type':'string'}},'required':['answer'],'additionalProperties':False}


def annotation_packet(packet,answer,reference,opaque):
    # Exact-span project inventory is method-blind and development-only; sentences retain
    # negation/modality and compound limitations. No claim can be omitted by method identity.
    spans=re.split(r'(?<=[.!?])\s+(?=[A-Z])',answer.strip())
    template=json.loads((ROOT/'research/explanation_fidelity/qualification/evidence-calibration-agent-exact-task-v4.json').read_text())['cases'][0]['form']
    units=['State the reported action outcome.',
           'State the physical task support at the declared temporal scope; missing evidence means unknown.',
           'Identify a decisive violation measurement and time when one is observed, or the relevant available observation/coverage limitation otherwise.',
           'Preserve the limitation that a physical motion cause is not identified.']
    forms=[]
    for slot in ('A','B'):
        form=copy.deepcopy(template);form.pop('response_text',None)
        form.update(form_id=f'{opaque}-{slot}',packet_id=opaque,annotator_slot=slot,
                    question_text=packet['question'],robot_visible_evidence=packet,sanitized_physical_facts=[],
                    atomic_statements=[{'item_id':f'claim-{i+1:02d}','statement':span,'response_span':span,
                    'asserted_abstraction_level':None,'label':None,'annotation_notes':None,'visible_support_references':[]} for i,span in enumerate(spans)],
                    required_unit_coverage=[{'unit_prompt':u,'communicated':None,'response_span':None} for u in units],
                    limitation_preservation=[{'limitation_prompt':'Do not identify waves/current/wind/actuation as a physical cause without evidence.','preserved':None,'response_span':None}],
                    highest_asserted_abstraction_level=None,false_premise_handling='NOT_APPLICABLE')
        forms.append(form)
    return {'schema':'crane-blinded-agent-atomic-annotation-packet-set/v1','response_text':answer,
            'forms':forms,'inventory_origin':'project-method-blind-exact-sentence-span-development',
            'independent_reference':reference}


def process(batch,level,out):
    packet=json.loads((batch/f'method_packets/L{level}.json').read_text())
    reference=json.loads((batch/f'evaluator/L{level}-reference.json').read_text())
    output=out/batch.name/f'L{level}';output.mkdir(parents=True,exist_ok=True)
    b2_path=output/'B2.json'
    if b2_path.exists():b2=json.loads(b2_path.read_text())
    else:
        with tempfile.TemporaryDirectory(prefix='boat-b2-packet-') as tmp:
            work=Path(tmp);save(work/'evidence.json',packet)
            shutil.copyfile(ROOT/'analysis/roboboat_temporal_certificate.py',work/'roboboat_temporal_certificate.py')
            prompt=(DOC/'marine_b2_prompt_v1.txt').read_text()
            result=call(out/'calls',f"{packet['packet_id']}-L{level}",work,prompt,'gpt-6-sol','high',SCHEMA,allow_tools=True)
        b2={'answer':result['parsed_final']['answer'],'cache_key':result['cache_key'],'latency_s':result['latency_s']}
        save(b2_path,b2)
    b4=json.loads((batch/f'contract_outputs/L{level}.json').read_text())
    save(output/'B4.json',{'answer':b4['answer'],'model_calls':0})
    # Method keys are separately retained, never present in blinded judge forms.
    for method,answer in [('B2',b2['answer']),('B4',b4['answer'])]:
        opaque=hashlib.sha256((packet['packet_id']+str(level)+answer).encode()).hexdigest()[:24]
        packet_path=out/'blind_packets'/f'{opaque}.json'
        save(packet_path,annotation_packet(packet,answer,reference,opaque))
        join={'opaque_response_id':opaque,'method':method,'batch':batch.name,'level':level}
        save(out/'evaluator_join'/f'{batch.name}-L{level}-{method}.json',join)
        target=out/'annotations'/opaque
        if (target/'development-summary.json').exists():continue
        annotate(packet_path,target,caller=StructuredCodexCliAgentCaller(target/'calls',model='gpt-6-astra',effort='high',runner=isolated_run))
    return batch.name,level


def main():
    p=argparse.ArgumentParser();p.add_argument('--batch-root',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True)
    p.add_argument('--declaration',type=Path,default=DOC/'method_comparison_declaration_v1.json')
    p.add_argument('--batch',action='append',help='Execute specified registered batches for queue overlap')
    p.add_argument('--available-only',action='store_true',help='Development overlap: report and defer unpublished batches');a=p.parse_args()
    qual=json.loads((ROOT/'artifacts/roboboat-terminal-v1/qualification-v2/qualification-result.json').read_text())
    if qual['status']!='QUALIFIED':raise RuntimeError('marine qualification gate closed')
    canary=json.loads((DOC/'tool_canary_v2.json').read_text())
    if '289' not in canary['answer']['answer'] or 'Neither' not in canary['answer']['answer']:raise RuntimeError('strong tool gate closed')
    declaration=json.loads(a.declaration.read_text())
    if declaration['transport_sha256']!=hashlib.sha256((ROOT/'analysis/roboboat_isolated_transport.py').read_bytes()).hexdigest():raise RuntimeError('transport binding changed')
    if declaration['prompt_sha256']!=hashlib.sha256((DOC/'marine_b2_prompt_v1.txt').read_bytes()).hexdigest():raise RuntimeError('prompt binding changed')
    if declaration['certificate_sha256']!=hashlib.sha256((ROOT/'analysis/roboboat_temporal_certificate.py').read_bytes()).hexdigest():raise RuntimeError('certificate binding changed')
    batches=[a.batch_root/name for name in declaration['batches']]
    if a.batch:
        if not set(a.batch).issubset(declaration['batches']):
            raise RuntimeError('unregistered batch requested')
        batches=[b for b in batches if b.name in a.batch]
    if a.available_only:
        if declaration['disposition']!='EXPLORATORY_DEVELOPMENT_ONLY':
            raise RuntimeError('partial overlap is development only')
        pending=[b.name for b in batches if not (b/'summary.json').exists()]
        print('pending unpublished batches',pending,flush=True)
        batches=[b for b in batches if (b/'summary.json').exists()]
    a.output_root.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs=[pool.submit(process,batch,level,a.output_root) for batch in batches for level in range(3)]
        for job in as_completed(jobs):print('complete',job.result(),flush=True)
if __name__=='__main__':main()
