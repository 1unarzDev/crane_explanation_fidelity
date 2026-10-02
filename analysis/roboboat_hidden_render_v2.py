#!/usr/bin/env python3
"""Single owned named display/workspace with verified Lua render settings.

Additive infrastructure version; no Unity sensing/physics/controller changes.
"""
import argparse
import json
import os
import signal
import subprocess
import time


def hypr(*args):
    r=subprocess.run(['hyprctl',*args],capture_output=True,text=True,check=True)
    value=r.stdout.strip()
    if value.startswith(('error','Error','keyword can')):raise RuntimeError('Hyprland command rejected')
    return value


def state(kind):return json.loads(hypr(kind,'-j'))


def active_workspace_empty(monitors,workspaces,name,workspace):
    matches=[m for m in monitors if m['name']==name]
    if len(matches)!=1 or matches[0]['activeWorkspace']['name']!=workspace:return False
    matches=[w for w in workspaces if w['name']==workspace]
    return len(matches)==1 and matches[0]['monitor']==name and matches[0]['windows']==0


def owned_window(clients,name,workspace,monitor_id):
    # Only the single CRANE window is governed, without inspecting user titles.
    windows=[w for w in clients if w.get('class')=='CRANE.x86_64' and w.get('title')=='ASV']
    return len(windows)==1 and windows[0]['workspace']['name']==workspace and windows[0]['monitor']==monitor_id and windows[0]['mapped'] is True


def run(command,*,probe_only=False,timeout_s=20):
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):raise ValueError('active Hyprland required')
    if os.environ.get('CRANE_NOGRAPHICS','0')=='1':raise ValueError('rendered mode required')
    fps=int(os.environ.get('CRANE_RENDER_UNFOCUSED_FPS','60'))
    if fps<=0:raise ValueError('positive render FPS required')
    name='CRANE-BOAT-'+str(os.getpid());workspace=str(900000+os.getpid())
    before=state('monitors all');before_workspace=state('workspaces')
    if any(m['name']==name for m in before) or any(w['name']==workspace for w in before_workspace):
        raise ValueError('owned namespace already exists')
    original_fps=json.loads(hypr('getoption','misc:render_unfocused_fps','-j'))['int']
    process=None;created=False
    try:
        hypr('eval','hl.workspace_rule({workspace='+json.dumps(workspace)+',monitor='+json.dumps(name)+',["default"]=true})')
        hypr('output','create','headless',name);created=True
        monitors=state('monitors all')
        if not active_workspace_empty(monitors,state('workspaces'),name,workspace):
            raise RuntimeError('dedicated active render workspace not empty')
        monitor_id=next(m['id'] for m in monitors if m['name']==name)
        hypr('eval','hl.config({misc={render_unfocused_fps='+str(fps)+'}})')
        if json.loads(hypr('getoption','misc:render_unfocused_fps','-j'))['int']!=fps:
            raise RuntimeError('render FPS readback mismatch')
        hypr('eval','hl.window_rule({name="crane-headless-render-v2",match={class="^CRANE[.]x86_64$"},workspace='+json.dumps(workspace+' silent')+',no_initial_focus=true,render_unfocused=true,suppress_event="activate activatefocus"})')
        print(json.dumps({'schema':'roboboat-hidden-render/v2','owned_output':name,'owned_workspace':workspace,
            'readback_render_unfocused_fps':fps,'original_render_unfocused_fps':original_fps,
            'active_workspace_empty_before_launch':True,'unrelated_inactive_windows_not_rejected':True}),flush=True)
        if probe_only:return 0
        process=subprocess.Popen(command,start_new_session=True)
        deadline=time.monotonic()+timeout_s
        while process.poll() is None:
            if owned_window(state('clients'),name,workspace,monitor_id):break
            if time.monotonic()>=deadline:raise RuntimeError('render placement timed out')
            time.sleep(.05)
        else:raise RuntimeError('command exited before render placement verification')
        print('Owned RoboBoat window placement verified.',flush=True)
        code=process.wait()
        return 128-code if code<0 else code
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=20)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
        if created:
            try:hypr('output','remove',name)
            except (RuntimeError,subprocess.CalledProcessError):pass
        # Matches established wrapper cleanup, then restores actual prior FPS.
        hypr('reload','config-only')
        hypr('eval','hl.config({misc={render_unfocused_fps='+str(original_fps)+'}})')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--probe-only',action='store_true');p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
    if not a.command and not a.probe_only:p.error('command required')
    def interrupted(signum,frame):raise KeyboardInterrupt('owned render wrapper interrupted')
    signal.signal(signal.SIGTERM,interrupted)
    raise SystemExit(run(a.command,probe_only=a.probe_only))

if __name__=='__main__':main()
