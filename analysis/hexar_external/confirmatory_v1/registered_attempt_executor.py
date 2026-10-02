"""Registered single-attempt transport engine; no built-in provider or admission.

An independently qualified admission function must validate the real frozen
study/registry/provider before every operation. Synthetic/development admission
tests do not authorize confirmation or attest a provider's served version.
"""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path

from .journal import OneAttemptJournal, exclusive_json, fingerprint
from .strict_json import load
from .unique_request_plan import finite_json
from .request_binding import parse_answer
from .rich_evaluator_v4 import validate as validate_judge


def registry(binding_sha256, phase, jobs):
    if phase not in ('development_qualification', 'confirmation'):
        raise ValueError('explicit registered execution phase required')
    if not isinstance(binding_sha256, str) or len(binding_sha256) != 64:
        raise ValueError('exact study/development binding hash required')
    records = []
    seen = set()
    for job in jobs:
        if set(job) != {'job_id', 'request'} or job['job_id'] in seen:
            raise ValueError('unique closed registered job required')
        if type(job['job_id']) is not str or not job['job_id']:
            raise ValueError('nonempty opaque job identity required')
        seen.add(job['job_id'])
        request = job['request']
        finite_json(request)
        if request.get('role') not in ('method', 'judge', 'contract'):
            raise ValueError('known registered execution role required')
        if type(request.get('maximum_response_bytes')) is not int or request['maximum_response_bytes'] <= 0:
            raise ValueError('frozen response size limit required')
        records.append(dict(job_id=job['job_id'], request=copy.deepcopy(request),
                            request_sha256=fingerprint(request)))
    if not records:
        raise ValueError('nonempty sealed job registry required')
    return dict(schema='hexar-registered-attempt-registry/v1', phase=phase,
                binding_sha256=binding_sha256, jobs=sorted(records, key=lambda r: r['job_id']))


def raw_file(path, value):
    with path.open('xb') as stream:
        stream.write(value); stream.flush(); os.fsync(stream.fileno())
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


class RegisteredExecutor:
    def __init__(self, root, sealed_registry, admit):
        self.registry = copy.deepcopy(sealed_registry)
        self.root = Path(root)
        self.admit = admit
        self.binding = self.registry['binding_sha256']
        self.registry_sha256 = fingerprint(self.registry)
        self.jobs = {r['job_id']: r for r in self.registry['jobs']}
        if (len(self.jobs) != len(self.registry['jobs'])
                or registry(self.binding, self.registry['phase'],
                            [dict(job_id=r['job_id'], request=r['request']) for r in self.registry['jobs']]) != self.registry):
            raise ValueError('malformed or changed registered requests')
        self.authorize()
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / 'registered_jobs.json'
        if path.exists():
            if load(path.read_bytes()) != self.registry:
                raise ValueError('execution root already bound to another registry; no overwrite')
        else:
            exclusive_json(path, self.registry)
        self.journal = OneAttemptJournal(self.root / 'journal', self.binding)

    def authorize(self):
        result = self.admit(copy.deepcopy(self.registry))
        if (type(result) is not dict or result.get('authorized') is not True
                or result.get('registry_sha256') != self.registry_sha256
                or result.get('binding_sha256') != self.binding
                or result.get('phase') != self.registry['phase']):
            raise ValueError('independent frozen registry/provider admission failed')

    def execute(self, job_id, backend):
        if job_id not in self.jobs:
            raise ValueError('unscheduled job; no dispatch permitted')
        # A claimed job is indeterminate only after its live dispatcher exits.
        # A second caller must not close an attempt while its backend is active.
        lock_path = self.root / (fingerprint(dict(opaque_job=job_id)) + '.dispatch.lock')
        with lock_path.open('a+b') as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError('registered attempt is still active; no dispatch or crash disposition')
            try:
                return self._execute_locked(job_id, backend)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _execute_locked(self, job_id, backend):
        self.authorize()
        if fingerprint(load((self.root / 'registered_jobs.json').read_bytes())) != self.registry_sha256:
            raise ValueError('sealed on-disk registry changed')
        row = self.jobs[job_id]
        request = copy.deepcopy(row['request'])
        if fingerprint(request) != row['request_sha256']:
            raise ValueError('registered request changed')
        identity = dict(opaque_job=job_id)
        attempt_request = dict(registry_sha256=self.registry_sha256, request_sha256=row['request_sha256'])
        claim, outcome_path = self.journal.paths(identity)
        state = self.journal.state(identity)
        if state == 'CLOSED':
            retained = load(outcome_path.read_bytes())
            expected = dict(schema='hexar-one-attempt/v1', freeze_sha256=self.binding, job=identity,
                            request_sha256=fingerprint(attempt_request), attempt_count=1)
            if retained['attempt'] != expected:
                raise ValueError('retained attempt identity differs from registry')
            for name, expected_hash in retained['outcome'].get('raw_sha256', {}).items():
                if hashlib.sha256((self.root / fingerprint(identity) / name).read_bytes()).hexdigest() != expected_hash:
                    raise ValueError('retained raw response archive changed')
            return dict(outcome=retained['outcome'], dispatch_performed=False)
        if state == 'CLAIMED_NO_REISSUE':
            folder = self.root / fingerprint(identity)
            retained_raw = {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
                            for name in ('raw_response.json', 'stdout.bin', 'stderr.bin')
                            if (folder / name).exists()}
            outcome = dict(status='INDETERMINATE_AFTER_CRASH', parsed=None,
                           error='Prior durable claim has no closed outcome; never reissue.', raw_sha256=retained_raw)
            self.journal.finish(identity, attempt_request, outcome)
            return dict(outcome=outcome, dispatch_performed=False)
        self.journal.claim(identity, attempt_request)
        folder = self.root / fingerprint(identity)
        folder.mkdir(exist_ok=False)
        raw = {name: b'' for name in ('raw_response.json', 'stdout.bin', 'stderr.bin')}
        outcome = dict(status='TECHNICAL_FAILURE', parsed=None, error=None, raw_sha256={})
        try:
            response = backend(copy.deepcopy(request))
            for name, field in (('raw_response.json', 'raw_response'), ('stdout.bin', 'stdout'), ('stderr.bin', 'stderr')):
                if type(response.get(field)) is not bytes:
                    raise ValueError('exact raw transport bytes required')
                raw[name] = response[field]
            if (type(response.get('returncode')) is not int or response['returncode'] != 0
                    or response.get('transport_policy_passed') is not True):
                raise ValueError('transport/tool/provider policy failure')
            parsed = load(raw['raw_response.json'], request['maximum_response_bytes'])
            if request['role'] == 'judge':
                parsed = validate_judge(parsed, request['payload'])
            else:
                parse_answer(parsed)
            outcome.update(status='VALID', parsed=parsed)
        except Exception as exc:
            outcome['error'] = type(exc).__name__ + ': ' + str(exc)
        for name, data in raw.items():
            raw_file(folder / name, data)
            outcome['raw_sha256'][name] = hashlib.sha256(data).hexdigest()
        self.journal.finish(identity, attempt_request, outcome)
        return dict(outcome=outcome, dispatch_performed=True)
