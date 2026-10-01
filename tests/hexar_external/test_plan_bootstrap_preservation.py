"""Unfrozen scientific amendments must survive bootstrap and concurrent writes."""
import json
import pytest
from analysis.hexar_external.confirmatory_v1 import build_plan


@pytest.mark.parametrize('status', ['CANDIDATE', 'FROZEN', 'PROSPECTIVE_FIXED_SEQUENCE_UNBOUND'])
def test_bootstrap_refuses_existing_artifact_before_any_mutation(tmp_path,monkeypatch,status):
    monkeypatch.setattr(build_plan,'OUT',tmp_path)
    original=json.dumps(dict(status=status,scientific_amendment='preserve'))
    path=tmp_path/'endpoint.json';path.write_text(original)
    with pytest.raises(ValueError,match='amended explicitly'):
        build_plan.main()
    assert path.read_text()==original
    assert list(tmp_path.iterdir())==[path]


def test_each_bootstrap_write_is_exclusive(tmp_path,monkeypatch):
    monkeypatch.setattr(build_plan,'OUT',tmp_path)
    build_plan.write('new.json',{'status':'CANDIDATE'})
    original=(tmp_path/'new.json').read_bytes()
    with pytest.raises(FileExistsError):
        build_plan.write('new.json',{'status':'different'})
    assert (tmp_path/'new.json').read_bytes()==original
