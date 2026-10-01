"""Reconstruct the bound launcher's final strict-summary exit; no broad exit waiver."""


def assess(summary, worker, fixture, controller_log, endpoint_log, return_code):
    endpoint_lines=endpoint_log.splitlines();active=0;maximum=0;connections=0;disconnects=0
    for line in endpoint_lines:
        if 'Connection from ' in line:connections+=1;active+=1;maximum=max(maximum,active)
        elif 'Disconnected from ' in line:disconnects+=1;active=max(0,active-1)
    transport={'connections':connections,'disconnects':disconnects,'maximumConcurrentUnityConnections':maximum,
        'activeConnectionsAtShutdown':active,'duplicateNodeRegistrations':sum('already registered for node name' in x for x in endpoint_lines),
        'endpointErrors':sum('[ERROR]' in x for x in endpoint_lines)}
    expected=summary.get('expectedNavigationStatus')
    observed={'succeeded':any('Goal succeeded' in x or 'Reached the goal!' in x for x in controller_log.splitlines()),
        'timeout':any('Client requested to cancel the goal' in x for x in controller_log.splitlines()),
        'canceled':any('Goal canceled' in x for x in controller_log.splitlines()),
        'aborted':any('Goal failed' in x for x in controller_log.splitlines())}.get(expected)
    timing=worker.get('actionTiming',{});limit=summary.get('actions',{}).get('maximumLagTicks')
    predicates={'expected_navigation_status':fixture.get('status')==expected,'expected_outcome_observed':observed is True,
        'worker_valid':worker.get('valid') is True,'rejected_actions_zero':worker.get('rejectedActions')==0,
        'stale_actions_zero':worker.get('staleActions')==0,'cross_episode_zero':worker.get('crossEpisodeActions')==0,
        'errors_zero':worker.get('loggedErrors')==0,'exceptions_zero':worker.get('loggedExceptions')==0,
        'water_searches_zero':worker.get('invalidWaterSearches')==0,'duplicate_registration_zero':transport['duplicateNodeRegistrations']==0,
        'endpoint_errors_zero':transport['endpointErrors']==0,'single_connection':maximum<=1,'connection_closed':active==0,
        'accepted_count':timing.get('acceptedActions')==worker.get('acceptedActions'),
        'known_count':timing.get('knownSourceActions')==worker.get('acceptedActions'),
        'source_lag':type(limit)is int and type(timing.get('maximumSourceToApplicationTicks'))is int and timing['maximumSourceToApplicationTicks']<=limit,
        'receive_lag':type(limit)is int and type(timing.get('maximumReceiveToApplicationTicks'))is int and timing['maximumReceiveToApplicationTicks']<=limit,
        'reset_requirement':not summary.get('resetRequired') or worker.get('resetProbe',{}).get('executed')is True,
        'occupied_costmap_requirement':not summary.get('occupiedCostmapRequired') or (fixture.get('costmapObservations',0)>0 and fixture.get('maximumOccupiedCostmapCells',0)>0)}
    expected_valid=all(predicates.values())
    allowed={'expected_navigation_status','expected_outcome_observed','worker_valid','rejected_actions_zero','stale_actions_zero'}
    failures=[k for k,v in predicates.items() if not v]
    checks={'transport_summary_reconstructed':all(summary.get('transport',{}).get(k)==v for k,v in transport.items()),
        'expected_outcome_observer_reconstructed':type(observed)is bool and summary.get('expectedOutcomeObserved')is observed,
        'strict_summary_validity_reconstructed':type(summary.get('valid'))is bool and summary['valid']==expected_valid,
        'exact_final_summary_exit':type(return_code)is int and return_code==(0 if expected_valid else 1),
        'only_prospectively_excepted_summary_failures':set(failures)<=allowed,
        'fixed_common_summary_contract':expected=='succeeded' and limit==10 and summary.get('actions',{}).get('commandTimeoutTicks')==25 and summary.get('resetRequired')is False and summary.get('occupiedCostmapRequired')is False}
    return {'schema':'roboboat-launcher-terminal-audit/v1-development','checks':checks,
        'terminal_classification_pass':all(checks.values()),'strict_summary_failed_predicates':failures,
        'strict_summary_expected_valid':expected_valid,'strict_summary_expected_exit':0 if expected_valid else 1,
        'scientific_admission_authorized':False,
        'limitations':['Requires separately bound final-summary and launcher sources, a fresh output namespace, and complete owned rendering cleanup.',
            'Only classifies the inherited final-summary exit; independent trace/sensor/runtime qualification remains required.']}
