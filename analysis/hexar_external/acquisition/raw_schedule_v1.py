"""Prospective raw episode schedule and durable outcome-blind attempt control.

No simulator or provider is called by this module itself. Production admission,
capture and independently qualified technical review are separate prerequisites.
Synthetic admission can qualify scheduling only, never activate confirmation.
"""
import copy
import fcntl
import hashlib
from pathlib import Path
import re

from .plan import FAMILIES
from ..confirmatory_v1.journal import canonical, exclusive_json, fingerprint
from ..confirmatory_v1.strict_json import load

MAX_BYTES = 32 * 1024 * 1024


def make_plan(master_seed, valid_per_family, reserve_per_family, excluded_ids=(), excluded_seeds=(), phase="confirmation"):
    if not isinstance(master_seed, str) or not re.fullmatch('[0-9a-f]{64}', master_seed):
        raise ValueError('independently drawn 256-bit hexadecimal master seed required')
    if (type(valid_per_family) is not int or valid_per_family < 1
            or type(reserve_per_family) is not int or reserve_per_family < 0):
        raise ValueError('positive valid quota and nonnegative finite reserve required')
    if phase not in ('confirmation','development'):
        raise ValueError('explicit development or confirmation schedule required')
    records = []
    token = hashlib.sha256(master_seed.encode()).hexdigest()[:16]
    for order in range(1, valid_per_family + reserve_per_family + 1):
        for family in FAMILIES:
            prefix='confirm' if phase=='confirmation' else 'dev-integrated'
            identity = f'hexar-tiago-{prefix}-{token}-{family}-{order:04d}'
            payload=['hexar-fresh-raw-schedule/v1', master_seed, family, order]
            if phase=='development':payload.append('permanently-excluded-development')
            seed = int.from_bytes(hashlib.sha256(canonical(payload)).digest()[:4], 'big')
            if identity in excluded_ids or seed in excluded_seeds:
                raise ValueError('development identity/seed collision; reject plan before acquisition')
            records.append(dict(acquisition_id=identity, episode_id=identity, family=family,
                                seed=seed, attempt_order=order))
    if len({r['seed'] for r in records}) != len(records):
        raise ValueError('seed collision; reject master seed before acquisition')
    plan = dict(schema='hexar-fresh-raw-schedule/v1', phase=phase,
        status='CANDIDATE_NOT_ADMITTED', master_seed=master_seed,
        cohort_type='adapted simulated HEXAR external-validation benchmark',
        independent_unit='independently generated simulated robot episode',
        valid_per_family=valid_per_family, maximum_attempts_per_family=valid_per_family+reserve_per_family,
        family_order=list(FAMILIES), records=records,
        stopping_rule='Within-family ordered prefix until valid quota or finite cap; no semantic access.',
        confirmation_authorized=False)
    if len(canonical(plan)) + 1 > MAX_BYTES:
        raise ValueError('schedule exceeds candidate persisted-artifact limit')
    return plan


def validate_plan(plan):
    try:
        expected = make_plan(plan['master_seed'], plan['valid_per_family'],
                             plan['maximum_attempts_per_family']-plan['valid_per_family'],phase=plan['phase'])
        if plan != expected:
            raise ValueError('noncanonical candidate raw schedule; no implicit allocation changes')
    except (KeyError, TypeError) as exc:
        raise ValueError('incomplete raw acquisition schedule') from exc
    return True


def read(path):
    return load(Path(path).read_bytes(), MAX_BYTES)


class RawSchedule:
    """One admitted root; each allocated episode receives at most one launch."""
    def __init__(self, root, plan, binding_sha256, admit):
        validate_plan(plan)
        if not isinstance(binding_sha256, str) or not re.fullmatch('[0-9a-f]{64}', binding_sha256):
            raise ValueError('exact acquisition/development binding required')
        self.root, self.plan = Path(root), copy.deepcopy(plan)
        self.binding, self.admit = binding_sha256, admit
        self.plan_hash = fingerprint(plan)
        self.identity = dict(schema='hexar-raw-schedule-execution/v1', binding_sha256=self.binding,
                             plan_sha256=self.plan_hash, execution_root=str(self.root.resolve()))
        self.authorize()
        self.root.mkdir(parents=True, exist_ok=True)
        for name, value in (('schedule.json', self.plan), ('binding.json', self.identity)):
            path = self.root/name
            if path.exists():
                if read(path) != value:
                    raise ValueError('raw acquisition root already bound to another schedule/binding')
            else:
                exclusive_json(path, value)
        (self.root/'attempts').mkdir(exist_ok=True)

    def authorize(self):
        request = dict(self.identity, plan=copy.deepcopy(self.plan))
        value = self.admit(request)
        if type(value) is not dict or value != dict(authorized=True, **self.identity):
            raise ValueError('independent raw acquisition admission failed')

    def folder(self, record):
        return self.root/'attempts'/record['acquisition_id']

    def claim(self, record):
        return dict(schema='hexar-raw-episode-attempt/v1', binding_sha256=self.binding,
                    plan_sha256=self.plan_hash, planned=record, launch_limit=1,
                    method_or_judge_calls_permitted=False)

    def state(self):
        """Verify all closed prefixes before making any further allocation."""
        attempts, valid = [], {family: 0 for family in FAMILIES}
        next_order = {family: 1 for family in FAMILIES}
        pending = None
        names = set()
        unattempted_gap = False
        for record in self.plan['records']:
            folder = self.folder(record)
            if not folder.exists():
                if valid[record['family']] < self.plan['valid_per_family']:
                    unattempted_gap = True
                continue
            if unattempted_gap:
                raise ValueError('raw attempts violate frozen interleaved order')
            if (folder/'contamination.json').exists():
                raise ValueError('retained semantic contamination; raw acquisition cannot continue')
            names.add(folder.name)
            if record['attempt_order'] != next_order[record['family']]:
                raise ValueError('attempts are not consecutive within-family prefixes')
            if valid[record['family']] >= self.plan['valid_per_family']:
                raise ValueError('attempt beyond completed valid family quota')
            if read(folder/'claim.json') != self.claim(record):
                raise ValueError('durable raw attempt claim changed')
            closed = folder/'outcome.json'
            if not closed.exists():
                if pending is not None:
                    raise ValueError('multiple pending raw attempts; acquisition ordering invalid')
                pending = record
                continue
            if pending is not None:
                raise ValueError('later attempt closed ahead of pending raw attempt')
            value = read(closed)
            if (set(value) != {'claim', 'disposition', 'technical_valid', 'reasons',
                              'method_outcomes_accessed', 'retained_artifacts'}
                    or value['claim'] != self.claim(record)
                    or type(value['technical_valid']) is not bool
                    or value['method_outcomes_accessed'] is not False
                    or type(value['reasons']) is not list
                    or value['disposition'] not in ('TECHNICAL_VALID', 'TECHNICAL_INVALID', 'INDETERMINATE_NO_REISSUE')
                    or value['technical_valid'] != (value['disposition']=='TECHNICAL_VALID')
                    or (value['technical_valid'] and value['reasons'])):
                raise ValueError('closed raw technical disposition changed/malformed')
            expected_names = {'runtime.json', 'review.json'} if value['disposition']!='INDETERMINATE_NO_REISSUE' else set(value['retained_artifacts'])
            if set(value['retained_artifacts']) != expected_names:
                raise ValueError('required raw runtime/review disposition archives missing')
            for name, digest in value['retained_artifacts'].items():
                if name not in ('runtime.json','review.json') or hashlib.sha256((folder/name).read_bytes()).hexdigest()!=digest:
                    raise ValueError('retained raw attempt archive changed')
            attempts.append(value)
            next_order[record['family']] += 1
            valid[record['family']] += int(value['technical_valid'])
        actual = {p.name for p in (self.root/'attempts').iterdir()}
        if actual != names:
            raise ValueError('unallocated raw attempt directory')
        return attempts, valid, next_order, pending

    def advance(self, capture, technical_review, recover=None):
        """Run one outcome-blind attempt, or close a crashed claim without launch."""
        with (self.root/'acquisition.lock').open('a+b') as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError('raw acquisition dispatcher still active; no crash disposition') from exc
            try:
                return self._advance(capture, technical_review, recover)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _advance(self, capture, technical_review, recover=None):
        self.authorize()
        if read(self.root/'schedule.json')!=self.plan or read(self.root/'binding.json')!=self.identity:
            raise ValueError('raw execution schedule/binding changed')
        attempts, valid, orders, pending = self.state()
        if pending is not None:
            record = pending
            folder = self.folder(record)
            # Recovery must share the dispatch lock: another live dispatcher
            # may still own the robot/native reader for this pending claim.
            if recover is not None:
                recover(copy.deepcopy(record), folder)
            # A deterministic recovery-review adapter may later be qualified.
            # V1 retains every byte and conservatively closes an interrupted
            # attempt as indeterminate without rerunning physics or review.
            retained = {name:hashlib.sha256((folder/name).read_bytes()).hexdigest()
                        for name in ('runtime.json','review.json') if (folder/name).exists()}
            outcome = dict(claim=self.claim(record), disposition='INDETERMINATE_NO_REISSUE',
                technical_valid=False, reasons=['HOST_INTERRUPTION_AFTER_DURABLE_CLAIM'],
                method_outcomes_accessed=False, retained_artifacts=retained)
            exclusive_json(folder/'outcome.json', outcome)
            return dict(status='ATTEMPT_CLOSED', outcome=outcome, launch_performed=False)
        if all(count == self.plan['valid_per_family'] for count in valid.values()):
            return dict(status='VALID_QUOTAS_COMPLETE_NOT_SEALED', valid_by_family=valid,
                        attempted_episodes=len(attempts), launch_performed=False)
        # The frozen interleaving is deterministic; filled families are skipped.
        record = next((r for r in self.plan['records']
                       if valid[r['family']] < self.plan['valid_per_family']
                       and r['attempt_order']==orders[r['family']]), None)
        if record is None:
            return dict(status='FINITE_RESERVE_EXHAUSTED_NO_COHORT', valid_by_family=valid,
                        attempted_episodes=len(attempts), launch_performed=False)
        # If any family exhausted its cap, the declared balanced cohort cannot
        # complete. Retain all attempts; do not expand the reserve or keep going.
        if any(valid[f] < self.plan['valid_per_family'] and orders[f] > self.plan['maximum_attempts_per_family'] for f in FAMILIES):
            return dict(status='FINITE_RESERVE_EXHAUSTED_NO_COHORT', valid_by_family=valid,
                        attempted_episodes=len(attempts), launch_performed=False)
        folder = self.folder(record)
        folder.mkdir(exist_ok=False)
        exclusive_json(folder/'claim.json', self.claim(record))
        try:
            runtime = capture(copy.deepcopy(record), folder)
        except Exception as exc:
            runtime = dict(technical_capture_error=type(exc).__name__+': '+str(exc),
                           method_outputs_generated=False, judge_labels_generated=False)
        if (type(runtime) is not dict or runtime.get('method_outputs_generated') is not False
                or runtime.get('judge_labels_generated') is not False):
            # Scientific exposure is not an invalidity that can be replaced.
            # Leave the claim retained and raise; independent admission must
            # revoke this contaminated acquisition, rather than reissue it.
            exclusive_json(folder/'contamination.json', dict(reason='RAW_CAPTURE_SEMANTIC_EXPOSURE_OR_UNKNOWN',
                binding_sha256=self.binding, plan_sha256=self.plan_hash))
            raise ValueError('raw capture semantic exposure/unknown; acquisition permanently closed')
        exclusive_json(folder/'runtime.json', runtime)
        verdict = technical_review(copy.deepcopy(record), copy.deepcopy(runtime), folder)
        if type(verdict) is dict and verdict.get('method_outcomes_accessed') is not False:
            exclusive_json(folder/'contamination.json', dict(reason='TECHNICAL_REVIEW_SEMANTIC_EXPOSURE_OR_UNKNOWN',
                binding_sha256=self.binding, plan_sha256=self.plan_hash))
            raise ValueError('technical review semantic exposure/unknown; acquisition permanently closed')
        if (type(verdict) is not dict or set(verdict) != {'technical_valid','reasons','method_outcomes_accessed'}
                or type(verdict.get('technical_valid')) is not bool
                or verdict.get('method_outcomes_accessed') is not False
                or type(verdict.get('reasons')) is not list
                or (verdict['technical_valid'] and verdict['reasons'])):
            raise ValueError('qualified outcome-blind technical review required')
        exclusive_json(folder/'review.json', verdict)
        retained = {name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in ('runtime.json','review.json')}
        outcome = dict(claim=self.claim(record), disposition='TECHNICAL_VALID' if verdict['technical_valid'] else 'TECHNICAL_INVALID',
            technical_valid=verdict['technical_valid'], reasons=verdict['reasons'],
            method_outcomes_accessed=False, retained_artifacts=retained)
        exclusive_json(folder/'outcome.json', outcome)
        return dict(status='ATTEMPT_CLOSED', outcome=outcome, launch_performed=True)
