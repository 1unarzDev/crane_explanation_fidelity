import hashlib,json
from pathlib import Path
import pytest
import probe_roboboat_isolated_baseline_capability_v3 as probe
import roboboat_writable_isolation_v2 as isolation

def receipt():
 body={'schema':'roboboat-synthetic-tool-result/v3','permission_errors':[],'input_sha256':hashlib.sha256(probe.INPUT).hexdigest(),'input_sha256_after':hashlib.sha256(probe.INPUT).hexdigest(),'yaml_import':True,'subprocess_child':'42','scratch_roundtrip':'disposable-synthetic-marker','public_write_refused':True}
 item={'id':'cmd1','type':'command_execution','command':'/usr/bin/bash -lc "python3 synthetic_challenge.py"','status':'completed','exit_code':0,'aggregated_output':probe.MARKER+json.dumps(body)}
 return {'status':'valid','parsed_final':{'executed':True,'probe_output':body,'permission_errors':[]},'events':[{'type':'item.started','item':{'id':'cmd1','type':'command_execution'}},{'type':'item.completed','item':item}]}

def test_lifecycle_and_completed_trace_are_required():
 r=receipt();assert probe.validate_receipt(r)['synthetic_expected_results_verified']
 for attack in ['no-completion','extra-command','writable-public','wrong-afterhash','self-report-only']:
  r=receipt()
  if attack=='no-completion':r['events']=r['events'][:1]
  elif attack=='extra-command':r['events'].append({'type':'item.started','item':{'id':'cmd2','type':'command_execution'}})
  elif attack=='self-report-only':r['events']=[]
  else:
   body=r['parsed_final']['probe_output'];body['public_write_refused' if attack=='writable-public' else 'input_sha256_after']=False
   r['events'][1]['item']['aggregated_output']=probe.MARKER+json.dumps(body)
  assert not probe.validate_receipt(r)['synthetic_expected_results_verified']

def test_one_shot_and_changed_input(tmp_path,monkeypatch):
 root=tmp_path/'probe';probe.prepare(root);calls=[]
 def call(*args,**kwargs):
  assert (root/'call-intent.json').is_file();calls.append(1);return receipt()
 monkeypatch.setattr(probe.transport,'call',call)
 assert probe.execute(root)['synthetic_expected_results_verified']
 with pytest.raises(FileExistsError):probe.execute(root)
 assert len(calls)==1
 root2=tmp_path/'changed';probe.prepare(root2);(root2/'synthetic_packet/synthetic_input.txt').write_text('changed')
 with pytest.raises(ValueError):probe.execute(root2)
 assert not (root2/'call-intent.json').exists()

def test_outer_mounts_config_and_no_shell_secret_inheritance(tmp_path,monkeypatch):
 host=tmp_path/'provider';host.mkdir();(host/'config.toml').write_text('model_provider="dummy"\n[model_providers.dummy]\nname="dummy"\nbase_url="https://example.invalid"\nenv_key="ROBOBOAT_MOCK_CREDENTIAL"\n')
 binary=tmp_path/'bin/codex';binary.parent.mkdir();binary.write_text('');(binary.parent/'codex-code-mode-host').write_text('');(binary.parent.parent/'codex-resources').mkdir()
 work=tmp_path/'work';work.mkdir();public=tmp_path/'public.txt';public.write_text('immutable')
 monkeypatch.setenv('CODEX_HOME',str(host));monkeypatch.setenv('ROBOBOAT_MOCK_CREDENTIAL','fake-nonsecret')
 monkeypatch.setattr(isolation.shutil,'which',lambda _:str(binary))
 def run(cmd,**kwargs):
  assert cmd[cmd.index('--remount-ro')+1]=='/tmp'
  for kind in ['daemon-staging','registry-staging']:
   stage=next(Path(x) for x in cmd if x.endswith('/'+kind));assert stage.stat().st_mode & 0o777 == 0o700
  assert f'/tmp/codex-daemon-{isolation.os.getuid()}' in cmd and f'/tmp/codex-bwrap-synthetic-mount-targets-{isolation.os.getuid()}' in cmd
  assert ['--ro-bind',str(public),'/workspace/public.txt'] == cmd[cmd.index(str(public))-1:cmd.index(str(public))+2]
  assert cmd[-2:]==['--cd','/workspace']
  cfg=Path(cmd[cmd.index('/provider-home')-1])/'config.toml';text=cfg.read_text()
  assert 'inherit = "none"' in text and 'network_access = false' in text and 'exclude_slash_tmp = true' in text
  return 42
 monkeypatch.setattr(isolation.subprocess,'run',run)
 assert isolation.isolated_run(['codex','exec','--cd',str(work)],public_files={public:'public.txt'})==42
