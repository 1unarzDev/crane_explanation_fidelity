import ast
import copy
import json
from pathlib import Path
import subprocess

import pytest

BASE=Path(__file__).resolve().parents[2]/'analysis/hexar_external/acquisition'


class StripProvenance(ast.NodeTransformer):
    def visit_Expr(self,node):
        if isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
            return None
        if (isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute)
                and node.value.func.attr=='add_argument' and node.value.args
                and isinstance(node.value.args[0],ast.Constant)
                and node.value.args[0].value in ('--acquisition-phase','--acquisition-binding')):
            return None
        return self.generic_visit(node)

    def visit_If(self,node):
        if ('args.acquisition_binding' in ast.unparse(node.test)
                and len(node.body)==1 and isinstance(node.body[0],ast.Expr)
                and ast.unparse(node.body[0]).startswith("ap.error(")):
            return None
        return self.generic_visit(node)

    def visit_Dict(self,node):
        if (any(isinstance(k,ast.Constant) and k.value=='schema' for k in node.keys)
                and any(isinstance(v,ast.Constant) and v.value in
                        ('hexar-development-episode-runtime/v1','hexar-bound-episode-runtime/v2') for v in node.values)):
            pairs=[]
            for k,v in zip(node.keys,node.values):
                if k.value=='acquisition_binding_sha256':continue
                if k.value=='schema':v=ast.Constant(value='normalized-runtime-schema')
                if k.value=='phase':v=ast.Constant(value='normalized-runtime-phase')
                pairs.append((k,v))
            node.keys,node.values=[p[0] for p in pairs],[p[1] for p in pairs]
        return self.generic_visit(node)


def test_bound_driver_has_identical_physics_and_sampling_ast():
    old=StripProvenance().visit(ast.parse((BASE/'episode_driver.py').read_text()))
    new=StripProvenance().visit(ast.parse((BASE/'bound_episode_driver_v2.py').read_text()))
    assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)


def test_bound_shell_keeps_identical_runtime_recording_and_readiness():
    old=(BASE/'run_development_episode.sh').read_text().split('set +u\n',1)[1]
    new=(BASE/'run_bound_episode_v1.sh').read_text().split('set +u\n',1)[1]
    new=new.replace('/acquisition/bound_episode_driver_v2.py --acquisition-phase "$phase" --acquisition-binding "$binding" --family',
                    '/acquisition/episode_driver.py --family')
    assert old==new
    full=(BASE/'run_bound_episode_v1.sh').read_text()
    assert full.index('acquisition_intent.json')<full.index('ros2 launch')
    assert 'method_outputs_permitted=False' in full


@pytest.mark.parametrize('args',[
    ['success','1','hexar-tiago-dev-success-0040'],
    ['success','1','hexar-tiago-dev-success-0040','raw_confirmation','f'*64],
    ['success','1','hexar-tiago-confirm-'+'a'*16+'-success-0001','development_adapter_qualification','f'*64],
    ['success','1','hexar-tiago-dev-success-0040','development_adapter_qualification','bad-binding'],
])
def test_bound_shell_rejects_phase_id_or_binding_before_any_runtime(args):
    result=subprocess.run(['bash',str(BASE/'run_bound_episode_v1.sh'),*args],capture_output=True)
    assert result.returncode!=0
    assert b'/ws/install' not in result.stderr


def test_development_bound_qualifier_rejects_confirmation_or_previous_claim(tmp_path,monkeypatch):
    from analysis.hexar_external.acquisition import qualify_bound_runtime_v1 as q
    from analysis.hexar_external.acquisition.plan import make_plan
    monkeypatch.setattr(q,'OUT',tmp_path)
    monkeypatch.setattr(q.subprocess,'run',lambda *_a,**_k:pytest.fail('no runtime dispatch'))
    monkeypatch.setattr(q.subprocess,'check_output',lambda *_a,**_k:pytest.fail('no runtime inspection'))
    p=tmp_path/'plan.json';plan=make_plan('fixture',1,0,ordinal_start=40)
    p.write_text(json.dumps(dict(plan,phase='confirmation')))
    with pytest.raises(ValueError,match='never admits confirmation'):q.run(p,'unused')
    p.write_text(json.dumps(plan));claim=tmp_path/(plan['records'][0]['episode_id']+'.launch_claim.json')
    claim.write_text('preserved fixture claim')
    with pytest.raises(ValueError,match='prior development episode'):q.run(p,'unused')
    assert claim.read_text()=='preserved fixture claim'
