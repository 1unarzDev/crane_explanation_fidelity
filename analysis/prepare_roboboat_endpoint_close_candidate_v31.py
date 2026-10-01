"""Isolated narrowly conditioned close-race candidate; no live source modifications."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/roboboat-live-endpoint-source-audit-v30-001/tcp_sender.py'
OLD='''                except Exception as e:
                    self.tcp_server.logerr("Exception {}".format(e))
                    break
'''
NEW='''                except OSError as e:
                    if e.errno == errno.EBADF and halt_event.is_set():
                        self.tcp_server.loginfo("Socket closed after reader halt: {}".format(e))
                    else:
                        self.tcp_server.logerr("Exception {}".format(e))
                    break
                except Exception as e:
                    self.tcp_server.logerr("Exception {}".format(e))
                    break
'''


def binding(path):
    p=Path(path).resolve();return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}


def prepare(root):
    root=Path(root).resolve()
    if root.exists():raise FileExistsError('immutable fresh close-race candidate required')
    original=BASE.read_text()
    if original.count(OLD)!=1 or original.count('import socket\n')!=1:raise ValueError('exact reviewed sender-loop seam required')
    candidate=original.replace('import socket\n','import socket\nimport errno\n').replace(OLD,NEW)
    def methods(source):return {n.name:ast.dump(n) for c in ast.parse(source).body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef)}
    before,after=methods(original),methods(candidate)
    changed=[n for n in before if before[n]!=after[n]]
    if changed!=['sender_loop'] or before.keys()!=after.keys():raise ValueError('unexpected source change')
    root.mkdir();target=root/'tcp_sender_candidate_v31.py';target.write_text(candidate)
    review={'schema':'roboboat-endpoint-close-race-candidate/v31','status':'PREPARED_UNLAUNCHED_UNQUALIFIED',
        'original':binding(BASE),'candidate':binding(target),'builder':binding(__file__),
        'only_changed_method':'sender_loop','new_condition':'OSError errno.EBADF AND existing shared reader halt event already set',
        'unexpected_ebadf_without_prior_halt_stays_error':True,'other_os_errors_stay_errors':True,
        'existing_broken_pipe_reset_behavior_unchanged':True,'queue_halt_cleanup_unchanged':True,
        'live_endpoint_or_shared_land_source_modified':False,'old_failure_relabelled':False,
        'historical_failed_container_or_cause_authenticated':False,'operationally_qualified':False,
        'confirmation_n':0,'replication_n':0,'independent_n_added':0,
        'future_requirements':'Separate boat-only endpoint runtime, exact deployed-source authentication and prospective full transport/trace/runtime qualification. Current v27 and queued v29 declarations retain original endpoint code and zero-error gates. Source-level reproducer is not a historical-episode diagnosis.'}
    (root/'candidate.json').write_text(json.dumps(review,indent=2)+'\n');return review


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);a=p.parse_args();r=prepare(a.root)
    print(json.dumps({'status':r['status'],'live_source_modified':False}))
