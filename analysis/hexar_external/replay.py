"""Execute pinned upstream callback bodies, never a hand-reimplemented state machine.

AST loading omits unavailable ROS service imports for offline mode only. Native mode
uses ROS Humble message classes and a real Lifecycle Node. Dispatch-clock tracing is
explicit instrumentation; not a historical wall-clock reproduction.
"""
import ast
import hashlib
import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace as NS

ROOT=Path(__file__).resolve().parents[2]
UPSTREAM=ROOT/'data/hexar_external/upstream'

class QuietLogger:
    def __getattr__(self,key): return lambda *a,**k:None
class Clock:
    def __init__(self): self.ns=0
    def now(self): return NS(to_msg=lambda:NS(sec=self.ns//10**9,nanosec=self.ns%10**9))
class OfflineNode:
    def __init__(self,*a,**k): self.clock=Clock();self.params={}
    def declare_parameter(self,k,v):self.params[k]=v
    def get_parameter(self,k):return NS(get_parameter_value=lambda:NS(string_value=self.params[k]))
    def get_logger(self):return QuietLogger()
    def get_clock(self):return self.clock
class CaptureClient:
    def __init__(self,**kwargs):self.requests=[];self.chat=NS(completions=NS(create=self.create))
    def create(self,**kwargs):
        self.requests.append(kwargs)
        return NS(choices=[NS(message=NS(content='CAPTURE_ONLY_NO_MODEL'))])

def classes(native=False):
    if native:
        from rclpy.lifecycle import Node
        from rcl_interfaces.msg import Log
        from geometry_msgs.msg import PoseWithCovarianceStamped
        from std_msgs.msg import Bool
    else:
        Node=OfflineNode;Log=NS(WARN=30);PoseWithCovarianceStamped=object;Bool=object
    scope={'Node':Node,'Log':Log,'PoseWithCovarianceStamped':PoseWithCovarianceStamped,
       'Bool':Bool,'OpenAI':CaptureClient,'DEFAULT_LLM_MODEL':'gpt-4.1-mini',
       'DEFAULT_LLM_HOST':'https://api.openai.com','json':json,
       'State':object,'TransitionCallbackReturn':object}
    for filename,names in [('component_explain_navigation/component_explain_navigation/component_explainer_impl.py',{'explainerImpl'}),
       ('skill_explain/skill_explain/skill_impl.py',{'TaskInfo','SkillInfo','GenerateExplanationSkillImpl'})]:
        manifest=json.loads((ROOT/'data/hexar_external/audit/source_data_manifest.json').read_text())
        expected=next(f['sha256'] for f in manifest['files'] if f['path']==filename)
        if hashlib.sha256((UPSTREAM/filename).read_bytes()).hexdigest()!=expected:
            raise ValueError('Pinned upstream file changed: '+filename)
        tree=ast.parse((UPSTREAM/filename).read_text())
        selected=[]
        for n in tree.body:
            if isinstance(n,ast.ClassDef) and n.name in names:
                # Prevent annotations from requiring action packages in capture-only execution.
                for sub in ast.walk(n):
                    if isinstance(sub,(ast.FunctionDef,ast.AsyncFunctionDef)):
                        sub.returns=None
                        for arg in sub.args.args:arg.annotation=None
                selected.append(n)
        exec(compile(ast.Module(body=selected,type_ignores=[]),str(UPSTREAM/filename),'exec'),scope)
    return scope

def objects(native=False):
    s=classes(native);nav=s['explainerImpl']()
    # Selector logic remains original; action/model routing is never run here.
    skill=s['GenerateExplanationSkillImpl'].__new__(s['GenerateExplanationSkillImpl'])
    skill.task_info_buffer={}
    skill.get_logger=lambda:QuietLogger()
    skill.get_clock=nav.get_clock
    return nav,skill

CALLBACKS={'/rosout':'rosout_callback','/amcl_pose':'amcl_pose_callback',
           '/joy_priority':'joy_priority_callback','/power/is_charging':'plugged_callback',
           '/task_info':'on_new_task_info'}

def message(e):
    v=e['value']
    if e['topic']=='/amcl_pose':return NS(pose=NS(covariance=v['covariance']))
    return NS(**v)

def dispatch(nav,skill,e,ns=None):
    nav.clock.ns=e['recorded_ns'] if ns is None else ns
    obj=skill if e['topic']=='/task_info' else nav
    getattr(obj,CALLBACKS[e['topic']])(message(e))

def request_window(skill):
    task=skill.fetch_latest_task_info(only_with_instructions=True)
    failed,idx=task.skill_failed()
    if failed:
        start=task.skill_sequence[idx-1].update_time if idx else task.creation_time
        end=task.skill_sequence[idx].update_time
    else:start,end=task.creation_time,task.update_time
    return task, f'{start.sec}.{start.nanosec}', f'{end.sec}.{end.nanosec}'

def snapshot(nav,skill,question):
    task,start,end=request_window(skill)
    with contextlib.redirect_stdout(io.StringIO()): nav.generate_explanation(question,start,end)
    return {'logs':nav.logs,'last_log_msg':nav.last_log_msg,
            'high_localization_variance_count':nav.high_localization_variance_count,
            'is_charging':nav.is_charging,'is_joystick_manual':nav.is_joystick_manual,
            'task':task.to_dict(),'task_window':[start,end],
            'llm_request':nav.llm_client.requests[-1]}

def replay(events,question):
    nav,skill=objects()
    for e in events:dispatch(nav,skill,e)
    return snapshot(nav,skill,question)
