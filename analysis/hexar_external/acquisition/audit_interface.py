"""Development-only bag/replay/removal compatibility audit, zero semantic calls."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'analysis/hexar_external'))
from extract_events import extract
from study_v2 import build_packet
from evidence_calibration_io import canonical_sha256


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--qualification',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    args.qualification=args.qualification.resolve()
    declaration=json.loads(args.qualification.read_text())
    if declaration['phase']!='development_only':raise ValueError('development data only')
    battery=json.loads((ROOT/'manifests/hexar_external/confirmatory_v1/battery.json').read_text())
    audits=[];packets=[]
    for episode in declaration['episodes']:
        name=episode['episode_id'];family=episode['family_hidden']
        folder=args.qualification.parent/name/'raw'
        record=dict(episode_id=name,family_evaluator_only=family,compatible=False,topics={},error=None)
        try:
            for file in folder.glob('*.db3'):
                db=sqlite3.connect('file:'+str(file.resolve())+'?mode=ro&immutable=1',uri=True)
                for topic,count in db.execute('SELECT t.name,count(*) FROM messages m JOIN topics t ON t.id=m.topic_id GROUP BY t.name'):
                    record['topics'][topic]=record['topics'].get(topic,0)+count
                db.close()
            events=extract(folder)
            if not events:raise ValueError('no navigation evidence extracted')
            task_values=[json.loads(e['value']['data']) for e in events if e['topic']=='/task_info']
            statuses=[t['task_status'] for t in task_values]
            if not statuses or statuses[0]!='running' or statuses[-1] not in ('failed','succeeded'):
                raise ValueError('initial/terminal task recording missing')
            record.update(initial_and_terminal_tasks_present=True,extracted_events=len(events),
                          terminal_task_status=statuses[-1],source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.db3')})
            for query in battery['questions_by_family'][family]:
                trio=[]
                for condition in battery['evidence_conditions']:
                    packet,snapshot,closure=build_packet(events,query['wording'],condition)
                    if not packet['evidence']['navigation_outcomes']:raise ValueError('outcome disappeared in replay')
                    job=f'{name}-{query["question_id"]}-{condition}'
                    trio.append(packet)
                    packets.append(dict(job_id=job,recording_id=name,question_id=query['question_id'],condition=condition,
                                        method_packet=packet,packet_sha256=canonical_sha256(packet),closure=closure))
                if trio[0]!=trio[1]:raise ValueError('irrelevant removal changed legitimate evidence')
                if trio[0]['evidence']['navigation_outcomes']!=trio[2]['evidence']['navigation_outcomes']:
                    raise ValueError('diagnostic removal changed required outcome')
            record['compatible']=True
        except Exception as exc:
            record['error']=f'{type(exc).__name__}: {exc}'
        audits.append(record)
    report=dict(schema='hexar-simulated-interface-development-audit/v1',phase='development_only',
                qualification_sha256=hashlib.sha256(args.qualification.read_bytes()).hexdigest(),
                status='INTERFACE_COMPATIBLE_NOT_FULL_ACQUISITION_QUALIFICATION' if len(audits)==6 and all(r['compatible'] for r in audits) else 'INTERFACE_FAILED_RETAINED',
                recording_n=len(audits),packets=len(packets),semantic_outputs_generated=False,confirmatory_N=0,
                audits=audits,packet_records=packets,
                limitation='same receipt-clock instrumented upstream callbacks; simulated robot, no native full-stack HEXAR parity claim')
    with args.output.open('x') as stream:stream.write(json.dumps(report,indent=2)+'\n')
    print(report['status'],len(packets))

if __name__=='__main__':main()
