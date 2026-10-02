#!/usr/bin/env python3
"""Fresh development routes with tangent-consistent yaw and terminal diversity.

Physical initial state and fixed berth unchanged. Feasibility is unasserted.
"""
import argparse
import copy
import json
import math
import random
from pathlib import Path
from generate_roboboat_population_v1 import ROOT, DOC, digest, write

FAMILIES = ('aligned-long', 'aligned-short', 'curved-stem', 'terminal-s-bend', 'terminal-dogleg', 'direct-goal')
START = (-2.2768, -5.2)  # Approximate route anchor, not a physical pose setter.
SPACING_M = .20


def hermite(p0, p1, t0, t1):
    chord = math.dist(p0,p1)
    n = max(2, math.ceil(2*chord/SPACING_M))
    result=[]
    for i in range(n+1):
        u=i/n
        result.append(tuple((2*u**3-3*u*u+1)*p0[k]+(u**3-2*u*u+u)*t0[k]
            +(-2*u**3+3*u*u)*p1[k]+(u**3-u*u)*t1[k] for k in range(2)))
    return result


def route(lane, bottom, goal, length, offset, amplitude, family):
    # Smooth stem to existing south-turn corridor.
    points=hermite(START,(lane,bottom),(0,bottom-START[1]),(0,bottom-START[1]))
    if family == 'curved-stem':
        points=[(x+amplitude*math.sin(2*math.pi*i/(len(points)-1))*math.sin(math.pi*i/(len(points)-1)),y)
                for i,(x,y) in enumerate(points)]
    angle=math.pi/2+offset
    staging=(goal['x']-length*math.cos(angle),goal['y']-length*math.sin(angle))
    right=staging[0]; radius=(right-lane)/2; center=(right+lane)/2
    if radius <= .5 or staging[1] <= bottom+.2:
        raise ValueError('declared route geometry is degenerate')
    n=max(16,math.ceil(math.pi*radius/SPACING_M))
    points += [(center+radius*math.cos(math.pi+math.pi*i/n),
                bottom+radius*math.sin(math.pi+math.pi*i/n)) for i in range(1,n+1)]
    points += hermite((right,bottom),staging,(0,staging[1]-bottom),
                      (math.cos(angle)*(staging[1]-bottom),math.sin(angle)*(staging[1]-bottom)))[1:]
    terminal=hermite(staging,(goal['x'],goal['y']),
        (length*math.cos(angle),length*math.sin(angle)),(0,length))
    if family in ('terminal-s-bend','terminal-dogleg'):
        for i,(x,y) in enumerate(terminal):
            u=i/(len(terminal)-1)
            shape=math.sin(2*math.pi*u)*math.sin(math.pi*u) if family=='terminal-s-bend' else math.sin(math.pi*u)**2
            terminal[i]=(x+amplitude*shape,y)
    points += terminal[1:]
    # Subdivide actual chords after perturbation; no waypoint gap exceeds bound.
    dense=[points[0]]
    for a,b in zip(points,points[1:]):
        n=max(1,math.ceil(math.dist(a,b)/SPACING_M))
        dense += [(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n) for i in range(1,n+1)]
    poses=[]
    for i,(x,y) in enumerate(dense):
        a=dense[max(0,i-1)]; b=dense[min(len(dense)-1,i+1)]
        poses.append({'x':x,'y':y,'yaw':math.atan2(b[1]-a[1],b[0]-a[0])})
    poses[-1]=dict(goal)  # Requested final heading, deliberately distinct from route tangent.
    return {'schema':'crane-nav2-path-v1','frameId':'odom',
        'description':'Development v2 tangent-consistent route; fixed physical start/berth; clearance/feasibility unasserted.',
        'poses':poses}


def descriptors(path):
    poses=path['poses']; gaps=[math.dist((a['x'],a['y']),(b['x'],b['y'])) for a,b in zip(poses,poses[1:])]
    turns=[abs(math.atan2(math.sin(b['yaw']-a['yaw']),math.cos(b['yaw']-a['yaw']))) for a,b in zip(poses,poses[1:-1])]
    return {'length_m':sum(gaps),'maximum_waypoint_gap_m':max(gaps),
        'maximum_interior_heading_change_rad':max(turns,default=0),
        'initial_path_heading_rad':poses[0]['yaw'],'terminal_path_heading_rad':poses[-2]['yaw'],
        'x_extent_m':[min(p['x'] for p in poses),max(p['x'] for p in poses)],
        'y_extent_m':[min(p['y'] for p in poses),max(p['y'] for p in poses)],
        'clearance_validated':False,'physical_initial_pose_varied':False}


def generate(output,count,seed,phase='development'):
    output=Path(output).resolve()
    if count < 1 or phase != 'development':raise ValueError('positive development count required')
    if output.exists():raise FileExistsError('immutable population namespace exists')
    runtime=ROOT/'packages/crane_ml/Tools/Performance/generated_populations'/output.name
    if runtime.exists():raise FileExistsError('runtime namespace exists')
    rng=random.Random(seed);output.mkdir(parents=True)
    task=json.loads((DOC/'task_contract_v2.json').read_text())
    config=ROOT/'packages/crane_ml/Tools/Performance/roboboat_terminal_v1.yaml'
    rows=[];clusters=[]
    for index in range(count):
        family=FAMILIES[index%len(FAMILIES)];cluster=f'boat-geom-{seed}-{index+1:05d}'
        goal={'x':rng.uniform(.7141434,1.0141434),'y':rng.uniform(-27.736906,-27.436906),'yaw':math.pi/2+rng.uniform(-.10,.10)}
        lane=rng.uniform(-3.4,-2.1);bottom=rng.uniform(-35,-32)
        length=rng.uniform(1,2.5) if family=='aligned-short' else rng.uniform(3,5)
        offset=0.0 if family.startswith('aligned') else rng.uniform(-.10,.25)
        amplitude=rng.uniform(-.25,.25)
        # Input-only construction constraint: reserve a northbound connector.
        bottom=min(bottom,goal['y']-length*math.cos(offset)-1.0)
        contract=copy.deepcopy(task);contract['id']=cluster+'-task-v2';contract['goal']=goal
        contract_path=output/'contracts'/(cluster+'.json');write(contract_path,contract)
        path_file=runtime/(cluster+'.json')
        design={'lane_x':lane,'turn_y':bottom,'terminal_length_m':length,'terminal_offset_rad':offset,'curvature_amplitude_m':amplitude,
                'physical_start':'unchanged scene default; route anchor is approximate','feasibility_validated':False}
        if family!='direct-goal':
            path=route(lane,bottom,goal,length,offset,amplitude,family);write(path_file,path);design.update(descriptors(path))
        ids=[]
        for variant,tolerance in enumerate((.2,.4) if index%2==0 else (.4,.2),1):
            row={'id':cluster+f'-v{variant}','cluster_id':cluster,'family':family,'variant':variant,
                'internal_xy_tolerance_m':tolerance,'action_mode':'navigate-to-pose' if family=='direct-goal' else 'follow-path',
                'goal':goal,'task_contract':{'path':str(contract_path.relative_to(ROOT)),'sha256':digest(contract_path)},
                'sampling_seed':seed,'geometry_draw_index':index,'seed':seed*1000+index,'retry_budget':0,
                'disposition':'DEVELOPMENT_EXPLORATORY','geometry':design}
            if family!='direct-goal':row['path_file']={'path':str(path_file.relative_to(ROOT)),'sha256':digest(path_file)}
            rows.append(row);ids.append(row['id'])
        clusters.append({'cluster_id':cluster,'family':family,'rows':ids})
    result={'schema':'roboboat-generated-development-population/v2','status':'DEVELOPMENT_EXPLORATORY_NOT_CONFIRMATION',
        'seed':seed,'independent_geometry_draws':count,'physical_variants':len(rows),'rows':rows,'clusters':clusters,
        'nav2_configuration':{'path':str(config.relative_to(ROOT)),'sha256':digest(config)},
        'generator':{'path':str(Path(__file__).resolve().relative_to(ROOT)),'sha256':digest(Path(__file__))},
        'dependencies':[{'path':str((ROOT/'analysis/generate_roboboat_population_v1.py').relative_to(ROOT)),
                         'sha256':digest(ROOT/'analysis/generate_roboboat_population_v1.py')}],
        'sampling':'Balanced six predeclared route families, independent continuous draws, AB/BA tolerance order; unique launch seeds across namespaces.',
        'independence':'One geometry draw is one cluster; tolerance variants, evidence levels, masks, seeds and repeats add zero N.',
        'platform_change':'Input-design revision only: tangent-derived path yaw, terminal geometry, unique launch seed mapping. Physical start, berth, controller/sensing/physics unchanged.',
        'validity':'Strict technical collection gates independent of navigation and method outcomes; geometric clearance/feasibility not asserted.',
        'confirmation_n':0,'replication_n':0,'land_n_added':0,'population_ceiling':None}
    write(output/'registry.json',result);return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--clusters',required=True,type=int);p.add_argument('--seed',required=True,type=int);a=p.parse_args()
    d=generate(a.output,a.clusters,a.seed);print(json.dumps({'clusters':d['independent_geometry_draws'],'rows':len(d['rows'])}))

if __name__=='__main__':main()
