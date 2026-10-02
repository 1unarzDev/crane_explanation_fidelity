#!/usr/bin/env python3
"""Concurrent development rendering candidate with process-owned FPS leases.

Fresh nonce class remains required. New workers share a reference-counted FPS
lease and a shared legacy gate; unchanged old collectors retain exclusive access.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import time
import uuid
from roboboat_render_fps_lease_v1 import FPSLease


def hypr(*args):
    result=subprocess.run(['hyprctl',*args],capture_output=True,text=True,check=True)
    value=result.stdout.strip()
    if args[0] in ('eval','output') and value!='ok':
        raise RuntimeError('Hyprland operation rejected: '+value)
    return value


def state(kind):return json.loads(hypr(kind,'-j'))


def process_records():
    records={}
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            text=path.read_text(); fields=text[text.rfind(')')+2:].split()
            records[int(path.parent.name)]={'state':fields[0],'ppid':int(fields[1]),
                'pgid':int(fields[2]),'sid':int(fields[3]),'start':int(fields[19])}
        except (OSError,ValueError,IndexError):pass
    return records


def group_owned_pid(pid,group,anchor,records):
    r=records.get(pid)
    return r is not None and r['pgid']==group and r['sid']==group and r['start']>=anchor and r['state']!='Z'


def cleanup_group(process,anchor,timeout_s=2):
    """Clean surviving original-session group even when immediate child exited.

    Escaped descendants are outside scope; group identity is checked before each
    signal using Linux process start times and session IDs.
    """
    pgid=process.pid
    if pgid==os.getpgrp():raise RuntimeError('refuse own process group cleanup')
    actions=[]
    for sig in (signal.SIGTERM,signal.SIGKILL):
        records=process_records()
        members=[pid for pid,r in records.items() if r['pgid']==pgid and r['state']!='Z']
        if not members:break
        if not all(group_owned_pid(pid,pgid,anchor,records) for pid in members):
            raise RuntimeError('process group identity changed; refuse signal')
        os.killpg(pgid,sig);actions.append({'signal':int(sig),'members':members})
        deadline=time.monotonic()+timeout_s
        while time.monotonic()<deadline:
            if not any(r['pgid']==pgid and r['state']!='Z' for r in process_records().values()):break
            time.sleep(.02)
    try:process.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:raise RuntimeError('child remains after group cleanup')
    if any(r['pgid']==pgid and r['state']!='Z' for r in process_records().values()):
        raise RuntimeError('live process group remains')
    return actions


def owned_window(clients,expected_class,workspace,monitor_id,group,anchor):
    matches=[c for c in clients if c.get('class')==expected_class]
    if len(matches)!=1:return False
    c=matches[0]
    return (c.get('mapped') is True and c.get('workspace',{}).get('name')==workspace
            and c.get('monitor')==monitor_id and type(c.get('pid')) is int
            and group_owned_pid(c['pid'],group,anchor,process_records()))


def run(command,*,expected_class=None,probe_only=False,timeout_s=20,audit_path=None,probe_hold_s=0):
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):raise ValueError('active Hyprland required')
    if os.environ.get('CRANE_NOGRAPHICS','0')=='1':raise ValueError('rendered mode required')
    # Never install a rule matching every CRANE instance. Caller must establish
    # a nonce class before mapping, which current Unity collector does not do.
    if not probe_only and (not command or not isinstance(expected_class,str) or
            re.fullmatch(r'CRANE-owned-[a-f0-9]{32}',expected_class) is None):
        raise ValueError('unqualified current player: exclusive nonce class required before launch')
    if not math.isfinite(timeout_s) or timeout_s<=0:raise ValueError('positive finite placement timeout required')
    if not math.isfinite(probe_hold_s) or probe_hold_s<0 or (probe_hold_s>0 and not probe_only):
        raise ValueError('nonnegative hold allowed only for empty-output engineering probes')
    if audit_path is not None:
        audit_path=Path(audit_path)
        with audit_path.open('x') as stream:stream.write('{"status":"INTENT"}\n')
    nonce=uuid.uuid4().hex
    name='CRANE-BOAT-v4-'+nonce;workspace=str(900000+os.getpid())
    ws_handle='_crane_ws_'+nonce;win_handle='_crane_win_'+nonce
    if any(m['name']==name for m in state('monitors all')) or any(w['name']==workspace for w in state('workspaces')):
        raise ValueError('owned namespace collision')
    if expected_class and any(c.get('class')==expected_class for c in state('clients')):
        raise ValueError('exclusive class already in use')
    def read_fps():return json.loads(hypr('getoption','misc:render_unfocused_fps','-j'))['int']
    def write_fps(value):hypr('eval','hl.config({misc={render_unfocused_fps='+str(value)+'}})')
    lease=FPSLease(read_fps,write_fps)
    report={'schema':'roboboat-hidden-render/v4-development','owned_output':name,'owned_workspace':workspace,
            'expected_class':expected_class,'original_fps':None,'cleanup_errors':[],
            'confirmation_n':0,'physics_equivalence_claimed':False,'full_state_preservation_claimed':False}
    created=False;ws_created=False;win_created=False;fps_leased=False;process=None;anchor=None
    primary_error=None;code=None
    def cleanup_stage(label,fn):
        try:report[label]=fn()
        except Exception as error:report['cleanup_errors'].append({'stage':label,'error':str(error)})
    try:
        report['fps_lease']=lease.acquire();fps_leased=True
        report['original_fps']=report['fps_lease']['original_fps']
        report['fps_readback']=report['fps_lease']['desired_fps']
        ws_created=True
        hypr('eval',ws_handle+'=hl.workspace_rule({workspace='+json.dumps(workspace)+',monitor='+json.dumps(name)+',["default"]=true}); assert('+ws_handle+' and '+ws_handle+':is_enabled())')
        created=True
        hypr('output','create','headless',name)
        monitors=state('monitors all');workspaces=state('workspaces')
        owned=[m for m in monitors if m['name']==name]
        ws=[w for w in workspaces if w['name']==workspace]
        if len(owned)!=1 or owned[0]['activeWorkspace']['name']!=workspace or len(ws)!=1 or ws[0]['monitor']!=name or ws[0]['windows']!=0:
            raise RuntimeError('owned active workspace readback failed')
        monitor_id=owned[0]['id']
        if not probe_only:
            rule_name='crane-render-v4-'+nonce
            win_created=True
            hypr('eval',win_handle+'=hl.window_rule({name='+json.dumps(rule_name)+',match={class='+json.dumps('^'+expected_class+'$')+'},workspace='+json.dumps(workspace+' silent')+',no_initial_focus=true,render_unfocused=true,suppress_event="activate activatefocus"}); assert('+win_handle+' and '+win_handle+':is_enabled())')
            process=subprocess.Popen(command,start_new_session=True)
            record=process_records().get(process.pid)
            if record is None or record['sid']!=process.pid:raise RuntimeError('launched session identity unavailable')
            anchor=record['start'];report['launched_session']={'pid':process.pid,'start':anchor}
            deadline=time.monotonic()+timeout_s
            while process.poll() is None:
                if owned_window(state('clients'),expected_class,workspace,monitor_id,process.pid,anchor):break
                if time.monotonic()>=deadline:raise RuntimeError('owned PID placement timed out')
                time.sleep(.05)
            else:raise RuntimeError('child exited before owned placement')
            report['placement_verified']=True
            code=process.wait();code=128-code if code<0 else code
        else:
            if probe_hold_s:time.sleep(probe_hold_s)
            if read_fps()!=60:raise RuntimeError('owned FPS changed during probe hold')
            report['probe_hold_s']=probe_hold_s
            code=0
    except BaseException as error:
        primary_error=error;report['primary_error']=repr(error)
    finally:
        if process is not None and anchor is None:
            report['cleanup_errors'].append({'stage':'process_group_cleanup','error':'session start identity unavailable; automatic signaling refused'})
        if process is not None and anchor is not None:
            cleanup_stage('process_group_cleanup',lambda:cleanup_group(process,anchor))
        if win_created:
            cleanup_stage('owned_window_rule_disabled',lambda:hypr('eval',win_handle+':set_enabled(false); assert('+win_handle+':is_enabled()==false); '+win_handle+'=nil'))
        if ws_created:
            cleanup_stage('owned_workspace_rule_disabled',lambda:hypr('eval',ws_handle+':set_enabled(false); assert('+ws_handle+':is_enabled()==false); '+ws_handle+'=nil'))
        if created:
            def remove():
                hypr('output','remove',name)
                if any(m['name']==name for m in state('monitors all')):raise RuntimeError('owned output remains')
                return True
            cleanup_stage('owned_output_removed',remove)
        if fps_leased:
            cleanup_stage('fps_lease_release',lease.release)
        report['return_code']=code
        report['status']='FAILED' if primary_error or report['cleanup_errors'] else 'COMPLETE_DEVELOPMENT_ONLY'
        if audit_path is not None:audit_path.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),flush=True)
    if primary_error is not None:raise primary_error
    if report['cleanup_errors']:raise RuntimeError('owned cleanup incomplete; inspect render audit')
    return code


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--probe-only',action='store_true');p.add_argument('--expected-class')
    p.add_argument('--probe-hold-seconds',type=float,default=0)
    p.add_argument('--audit-path',type=Path,required=True);p.add_argument('command',nargs=argparse.REMAINDER)
    a=p.parse_args()
    def interrupted(signum,frame):raise KeyboardInterrupt('render wrapper interrupted')
    signal.signal(signal.SIGTERM,interrupted)
    raise SystemExit(run(a.command,expected_class=a.expected_class,probe_only=a.probe_only,audit_path=a.audit_path,probe_hold_s=a.probe_hold_seconds))


if __name__=='__main__':main()
