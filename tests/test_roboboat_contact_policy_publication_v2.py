import copy
from pathlib import Path
import pytest
from publish_roboboat_contact_policy_capsule_v2 import validate_result,safe_members


def result():return {'schema':'roboboat-contact-policy-support-results/v2','rows':[{}]*12,'missing_annotations':[],'new_independent_configuration_n':0,'confirmation_n':0,'replication_n':0,'alpha_consumed':0,'paired_cluster_effect_estimated':False}


def test_publication_requires_exact_reproduced_development_result():
    r=result();validate_result(r,copy.deepcopy(r))
    different=copy.deepcopy(r);different['missing_annotations']=['unavailable']
    with pytest.raises(ValueError):validate_result(r,different)


@pytest.mark.parametrize('field,value',[('rows',[{}]*11),('confirmation_n',1),('alpha_consumed',.01),('missing_annotations',['x']),('paired_cluster_effect_estimated',True)])
def test_partial_or_inferential_bank_cannot_publish_as_development(field,value):
    r=result();r[field]=value
    with pytest.raises(ValueError):validate_result(r,copy.deepcopy(r))


def test_members_deduplicate_paths_and_reject_external_or_symlink_files(tmp_path):
    p=tmp_path/'source.json';p.write_text('{}')
    assert safe_members([p,p],root=tmp_path)==[p]
    link=tmp_path/'pointer';link.symlink_to(p)
    with pytest.raises(ValueError):safe_members([link],root=tmp_path)
    with pytest.raises(ValueError):safe_members([Path('/etc/hosts')],root=tmp_path)
