"""Candidate whole-episode technical admission before semantic generation.

The caller must supply independently hash-verified raw/interface reviews. This
pure predicate reads no method output, judge label or navigation success value.
Batch identity/freshness/source/image checks are required separately.
"""
import math
from .family_delivery import checks as family_checks
from .offline_domain_qualification import domain_checks


def evaluate(receipt,episode,planned,raw_interface_review):
    reasons=[]
    try:
        if receipt.get('episode_id')!=planned.get('episode_id'):
            reasons.append('ACQUISITION_ID_MISMATCH')
        if receipt.get('seed_hidden')!=planned.get('seed') or episode.get('seed_hidden')!=planned.get('seed'):
            reasons.append('APPLIED_SEED_REPORT_MISMATCH')
        if receipt.get('exit_code')!=0 or type(receipt.get('exit_code')) is not int:
            reasons.append('ACQUISITION_EXECUTION_FAILURE')
        if receipt.get('method_outputs_generated') is not False or receipt.get('judge_labels_generated') is not False:
            reasons.append('SEMANTIC_EXPOSURE_OR_UNKNOWN')
        if not all(domain_checks(receipt).values()):
            reasons.append('OFFLINE_DOMAIN_BINDING_NOT_ESTABLISHED')
        if episode.get('accepted') is not True:
            reasons.append('NAVIGATION_GOAL_NOT_ACCEPTED')
        if raw_interface_review.get('candidate_integrity') is not True:
            reasons.append('RAW_OR_QUERY_MASK_INTERFACE_INVALID')
        bag=raw_interface_review.get('bag_integrity',{})
        if bag.get('bag_integrity_passed') is not True or bag.get('seed_applied_matches_plan') is not True:
            reasons.append('RAW_INTEGRITY_OR_ACTUAL_SEED_UNVERIFIED')
        setup=family_checks(episode,planned['family'])
        reasons.extend('SETUP_'+key.upper() for key,value in setup.items() if value is not True)
        window=raw_interface_review.get('observed_action_window')
        if type(window) is not dict or type(window.get('start_stamp_ns')) is not int or type(window.get('end_stamp_ns')) is not int or window['end_stamp_ns']<=window['start_stamp_ns']:
            reasons.append('OBSERVED_ACTION_BOUNDARIES_INVALID')
        else:
            for row in episode.get('intervention_observations_hidden',[]):
                if type(row.get('observed_sim_stamp_ns')) is not int or row['observed_sim_stamp_ns']>=window['start_stamp_ns']:
                    reasons.append('FAMILY_SETUP_NOT_OBSERVED_BEFORE_GOAL')
                    break
        sampling=episode.get('sampling_hidden',{})
        if (sampling.get('profile')!='home_top_room_clearance_v4_development'
                or sampling.get('required_clearance_m')!=.6 or sampling.get('sampling_bounds_xy')!=[-6,1.2,-.5,2.0]):
            reasons.append('SAMPLING_PROFILE_MISMATCH')
        distance=sampling.get('distance_m')
        if type(distance) not in (int,float) or not math.isfinite(distance) or not 3<=distance<=5.5:
            reasons.append('START_GOAL_DISTANCE_INVALID')
    except (KeyError,TypeError,ValueError,AttributeError):
        reasons.append('MISSING_OR_MALFORMED_TECHNICAL_INPUT')
    return dict(schema='hexar-episode-technical-predicate-candidate/v1',valid=not reasons,reasons=reasons,
        navigation_success_used_as_exclusion=False,method_semantic_outcomes_used=False,
        qualification_scope='Candidate per-episode checks only; batch freshness/source/image/adapter qualification remains separate.')
