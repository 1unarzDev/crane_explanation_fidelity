"""One prospectively declared NON-STUDY synthetic tool capability call."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import roboboat_isolated_transport_v3 as transport
from roboboat_runtime_source_closure_v1 import source_closure

ROOT=Path(__file__).resolve().parents[1]
INPUT=b'RoboBoat synthetic capability input v1\nalpha: 17\n'
MARKER='ROBOBOAT_SYNTHETIC_CAPABILITY_V1='
CHALLENGE='''import hashlib,json,subprocess,sys,tempfile\nfrom pathlib import Path\nresult={"schema":"roboboat-synthetic-tool-result/v1","permission_errors":[]}\ndef operation(name,function):\n    try:result[name]=function()\n    except Exception as error:result["permission_errors"].append({"operation":name,"error_type":type(error).__name__});result[name]=None\noperation("input_sha256",lambda:hashlib.sha256(Path("synthetic_input.txt").read_bytes()).hexdigest())\ndef yaml_import():\n    import yaml\n    return yaml.safe_load("alpha: 17\\n")=={"alpha":17}\noperation("yaml_import",yaml_import)\noperation("subprocess_child",lambda:subprocess.run([sys.executable,"-c","print(6*7)"],capture_output=True,text=True,check=True).stdout.strip())\ndef scratch():\n    with tempfile.TemporaryDirectory(prefix="roboboat-synthetic-capability-",dir="/tmp") as directory:\n        path=Path(directory)/"scratch.txt";path.write_text("disposable-synthetic-marker");return path.read_text()\noperation("scratch_roundtrip",scratch)\nprint("ROBOBOAT_SYNTHETIC_CAPABILITY_V1="+json.dumps(result,sort_keys=True))\n'''
PROMPT='''This is a NON-STUDY synthetic capability probe, not a RoboBoat answer or scientific observation. Use an actual command execution tool exactly once to run: python3 synthetic_challenge.py . Read only the supplied synthetic_input.txt and synthetic_challenge.py. The script hashes immutable synthetic input, imports yaml, executes a Python subprocess child, and creates/reads/deletes disposable scratch in /tmp. Do not inspect environment variables, credentials, home, network, other files or research data. Do not change source inputs. Do not use tools to echo fabricated outputs. Do not retry any failure or seek elevated permission. Return the script JSON after its marker as probe_output, or null if execution was unavailable; report truthful permission_errors and executed. The retained command trace is the authority, not your self-report.'''
SCHEMA={'type':'object','additionalProperties':False,'required':['executed','probe_output','permission_errors'], 'properties':{'executed':{'type':'boolean'},'probe_output':{'anyOf':[{'type':'null'},{'type':'object','additionalProperties':False,'required':['schema','permission_errors','input_sha256','yaml_import','subprocess_child','scratch_roundtrip'],'properties':{'schema':{'type':'string'},'permission_errors':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['operation','error_type'],'properties':{'operation':{'type':'string'},'error_type':{'type':'string'}}}},'input_sha256':{'type':['string','null']},'yaml_import':{'type':['boolean','null']},'subprocess_child':{'type':['string','null']},'scratch_roundtrip':{'type':['string','null']}}}]},'permission_errors':{'type':'array','items':{'type':'string'}}}}

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def bind(path):return {'path':str(Path(path).resolve()),'sha256':digest(path)}
def save_new(path,value):
    with Path(path).open('x') as stream:stream.write(json.dumps(value,indent=2)+'\n')

def prepare(root):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=False);packet=root/'synthetic_packet';packet.mkdir()
    (packet/'synthetic_input.txt').write_bytes(INPUT);(packet/'synthetic_challenge.py').write_text(CHALLENGE)
    sources=source_closure([Path(__file__),Path(transport.__file__)])+[ROOT/'tests/test_probe_roboboat_isolated_baseline_capability_v1.py']
    declaration={'schema':'roboboat-non-study-baseline-capability-declaration/v1','disposition':'NON_STUDY_TOOLING_ONLY','model':'gpt-6-astra','effort':'high','timeout_s':600,'allow_tools':True,'maximum_real_calls':1,'quality_retries':0,'prompt':PROMPT,'return_schema':SCHEMA,'packet_root':str(packet),'sources':[bind(p) for p in sorted(set(sources))],'inputs':[bind(p) for p in sorted(packet.iterdir())],'source_workspace_writability_promised':False,'baseline_promotion':False,'source_audit_readiness':False,'confirmation_n':0,'replication_n':0,'alpha_consumed':0}
    save_new(root/'declaration.json',declaration);return declaration

def validate_receipt(receipt):
    commands=[event.get('item',{}) for event in receipt.get('events',[]) if event.get('item',{}).get('type')=='command_execution']
    matching=[item for item in commands if re.fullmatch(r'(?:/usr/bin/)?python3\s+(?:\./)?synthetic_challenge\.py',item.get('command','').strip())]
    output=[]
    for item in matching:
        for line in item.get('aggregated_output','').splitlines():
            if line.startswith(MARKER):
                try:output.append((item,json.loads(line[len(MARKER):])))
                except ValueError:pass
    expected={'schema':'roboboat-synthetic-tool-result/v1','permission_errors':[],'input_sha256':hashlib.sha256(INPUT).hexdigest(),'yaml_import':True,'subprocess_child':'42','scratch_roundtrip':'disposable-synthetic-marker'}
    final=receipt.get('parsed_final') or {}
    exact=bool(len(commands)==1 and len(matching)==1 and len(output)==1 and output[0][0].get('exit_code')==0 and output[0][1]==expected and final.get('executed') is True and final.get('probe_output')==expected and final.get('permission_errors')==[] and receipt.get('status')=='valid')
    return {'schema':'roboboat-non-study-baseline-capability-result/v1','status':'TRACE_VERIFIED_SYNTHETIC_CAPABILITY_PASS' if exact else 'CAPABILITY_UNVERIFIED_OR_FAILED','actual_command_execution_count':len(commands),'matching_challenge_commands':len(matching),'synthetic_expected_results_verified':exact,'permission_errors_retained':[body.get('permission_errors') for _,body in output],'baseline_promotion':False,'source_audit_readiness':False,'study_evidence':False,'confirmation_n':0,'replication_n':0,'alpha_consumed':0}

def execute(root):
    root=Path(root).resolve();declaration=root/'declaration.json';d=json.loads(declaration.read_text())
    for item in d['sources']+d['inputs']:
        if digest(item['path'])!=item['sha256']:raise ValueError('predeclared source/input changed')
    if (d['model'],d['effort'],d['timeout_s'],d['maximum_real_calls'],d['quality_retries'])!=('gpt-6-astra','high',600,1,0):raise ValueError('declared settings changed')
    save_new(root/'call-intent.json',{'declaration':bind(declaration),'maximum_real_calls':1,'no_retries':True})
    try:
        receipt=transport.call(root/'calls','non-study-synthetic-capability',Path(d['packet_root']),d['prompt'],d['model'],d['effort'],d['return_schema'],allow_tools=True,timeout=600)
        result=validate_receipt(receipt)
    except Exception:
        result={'schema':'roboboat-non-study-baseline-capability-result/v1','status':'CAPABILITY_TRANSPORT_FAILURE_RETAINED','study_evidence':False,'baseline_promotion':False,'source_audit_readiness':False,'confirmation_n':0,'replication_n':0,'alpha_consumed':0}
    result['declaration']=bind(declaration);result['retained_receipts']=[bind(p) for p in sorted((root/'calls').glob('*.json'))]
    save_new(root/'result.json',result);return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','execute']);parser.add_argument('--root',type=Path,required=True);args=parser.parse_args()
    result=prepare(args.root) if args.phase=='prepare' else execute(args.root)
    print(json.dumps({'phase':args.phase,'status':result.get('status',result.get('disposition')),'root':str(args.root.resolve())}))
if __name__=='__main__':main()
