import pytest
import roboboat_isolated_transport_v5 as transport
import test_roboboat_isolated_transport_v2 as prior

@pytest.mark.parametrize('name',[n for n in vars(prior) if n.startswith('test_')])
def test_inherited_safe_transport(name,tmp_path,monkeypatch):
 monkeypatch.setattr(prior,'transport',transport)
 getattr(prior,name)(tmp_path,monkeypatch)

def test_decoded_json_secret_redacted():
 assert transport.safe_events('{"message":"\\u0073ecret"}',('secret',)) == [{'message':'[PROVIDER_CREDENTIAL_REDACTED]'}]
