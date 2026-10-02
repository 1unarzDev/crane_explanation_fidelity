import pytest
from analysis.hexar_external.acquisition.offline_domain_qualification import domain_checks


def test_domain_reuse_only_qualifies_offline_isolated_configuration():
    receipt=dict(requested_network_mode='none',observed_network_mode='none',requested_ros_domain_id=70,observed_ros_domain_id='70')
    assert all(domain_checks(receipt).values())
    for key,bad in (('requested_network_mode','host'),('observed_network_mode','bridge'),
                    ('requested_ros_domain_id',True),('requested_ros_domain_id',70.0),('observed_ros_domain_id','71')):
        assert not all(domain_checks(dict(receipt,**{key:bad})).values())
    assert not all(domain_checks({}).values())
