import copy
import run_roboboat_population_development_v7 as parent
import run_roboboat_population_development_v8 as successor


def test_strict_gates_remain_identical_including_retained_stale_rejections():
    summary={'transport':{'duplicateNodeRegistrations':0,'endpointErrors':0,
                        'maximumConcurrentUnityConnections':1,'activeConnectionsAtShutdown':0}}
    worker={'valid':True,'acceptedActions':4,'rejectedActions':0,'staleActions':0,
            'crossEpisodeActions':0,'loggedErrors':0,'loggedExceptions':0,
            'invalidWaterSearches':0,'staleObservations':0,'failedObservations':0,
            'actionTiming':{'acceptedActions':4,'knownSourceActions':4,
                            'maximumSourceToApplicationTicks':10,'maximumReceiveToApplicationTicks':1}}
    fixture={'status':'timeout','trajectory':[{'measurement':'construction'}]}
    assert successor.technical_checks(summary,worker,fixture)==parent.technical_checks(summary,worker,fixture)
    assert all(successor.technical_checks(summary,worker,fixture).values())
    for field in ['rejectedActions','staleActions','staleObservations','loggedErrors']:
        bad=copy.deepcopy(worker);bad[field]=1
        actual=successor.technical_checks(summary,bad,fixture)
        assert actual==parent.technical_checks(summary,bad,fixture)
        assert not all(actual.values())


def test_baseline_explanation_quality_is_not_an_admission_input():
    import inspect
    signature=inspect.signature(successor.technical_checks)
    assert list(signature.parameters)==['summary','worker','fixture']
    assert successor.PROBE_VERSION.endswith('development')
    assert successor.BUILD_IDENTITY.name=='full-build-root-v1.json'
