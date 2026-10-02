"""Durable one-attempt primitive. Caller must separately pass frozen admission.

A crash after claiming a job leaves a retained indeterminate technical attempt.
It NEVER causes an automatic reissue. This module cannot call any provider.
"""
import hashlib
import json
import os
from pathlib import Path


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def exclusive_json(path,value):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(canonical(value)+b'\n'); stream.flush(); os.fsync(stream.fileno())
        directory=os.open(Path(path).parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
    except BaseException:
        # Even a partial claim is retained: loss of certainty is a technical
        # failure, never a reason to reissue a semantic call.
        raise


class OneAttemptJournal:
    def __init__(self,root,freeze_sha256):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.freeze_sha256=freeze_sha256

    def paths(self,job):
        handle=fingerprint(dict(freeze_sha256=self.freeze_sha256,job=job))
        return self.root/(handle+'.claim.json'),self.root/(handle+'.outcome.json')

    def claim(self,job,request_identity):
        claim,outcome=self.paths(job)
        record=dict(schema='hexar-one-attempt/v1',freeze_sha256=self.freeze_sha256,
                    job=job,request_sha256=fingerprint(request_identity),attempt_count=1)
        exclusive_json(claim,record)
        return record

    def finish(self,job,request_identity,outcome):
        claim,dest=self.paths(job)
        expected=dict(schema='hexar-one-attempt/v1',freeze_sha256=self.freeze_sha256,
                      job=job,request_sha256=fingerprint(request_identity),attempt_count=1)
        if json.loads(claim.read_text())!=expected:
            raise ValueError('attempt identity changed')
        if outcome.get('status') not in ('VALID','TECHNICAL_FAILURE','INDETERMINATE_AFTER_CRASH'):
            raise ValueError('closed outcome disposition required')
        exclusive_json(dest,dict(attempt=expected,outcome=outcome))
        return dest

    def state(self,job):
        claim,outcome=self.paths(job)
        if outcome.exists():return 'CLOSED'
        if claim.exists():return 'CLAIMED_NO_REISSUE'
        return 'UNCLAIMED'
