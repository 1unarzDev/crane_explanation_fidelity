import pytest
from analysis.hexar_external.confirmatory_v1.strict_json import load


def test_valid_provider_JSON_is_preserved_without_repairs():
    assert load(b'{"answer":"Scope: odometry, not physical arrival.","count":1.25}')=={'answer':'Scope: odometry, not physical arrival.','count':1.25}


@pytest.mark.parametrize('raw',[b'{"unsupported_material":true,"unsupported_material":false}',b'{"nested":{"flag":0,"flag":1}}',b'{"v":NaN}',b'{"v":Infinity}',b'{"v":1e400}',b'{} trailing',b'\xff',b'\xef\xbb\xbf{}'])
def test_ambiguous_nonfinite_or_malformed_documents_fail_closed(raw):
    with pytest.raises((ValueError,UnicodeError)):load(raw)


def test_resource_limit_is_explicit_and_enforced():
    with pytest.raises(ValueError,match='size bound'):load(b'{"answer":"long"}',maximum_bytes=4)
