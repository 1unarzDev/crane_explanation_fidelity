from pathlib import Path
import pytest
from analysis.hexar_external.acquisition.bound_cli_guard_v1 import compatible,probe,verify_allocations
from analysis.hexar_external.acquisition.raw_schedule_v1 import make_plan

SHELL=Path(__file__).resolve().parents[2]/'analysis/hexar_external/acquisition/run_bound_episode_v1.sh'


@pytest.mark.parametrize('phase,mode',[('development','development_adapter_qualification'),('confirmation','raw_confirmation')])
def test_every_allocated_id_passes_exact_qualified_shell_prefix(phase,mode):
    plan=make_plan('a'*64,1,1,phase=phase)
    result=probe(SHELL,plan['records'],mode,'f'*64)
    assert result['passed'] and len(result['rows'])==12 and result['robot_or_native_launches']==0


def test_retained_v19_identity_is_rejected_before_any_runtime():
    record=dict(episode_id='hexar-tiago-dev-integrated-e13d4646a581efb8-charging-0001',family='charging',seed=1)
    assert not compatible(record,'development_adapter_qualification','f'*64)
    with pytest.raises(ValueError,match='violates qualified shell guard'):
        verify_allocations(SHELL,[record],'development_adapter_qualification','f'*64)


def test_changed_prefix_cannot_execute_arbitrary_shell(tmp_path):
    path=tmp_path/'guard.sh';path.write_text('touch /tmp/should-never-run\noutput_dir=anything\n')
    with pytest.raises(ValueError,match='guard changed'):probe(path,make_plan('a'*64,1,1)['records'],'raw_confirmation','f'*64)
