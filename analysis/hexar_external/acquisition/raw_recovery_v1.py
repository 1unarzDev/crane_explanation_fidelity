"""Conservative raw host-interruption disposition, without robot/native replay."""
import json
import os
from pathlib import Path
import re
import subprocess

from .raw_runtime_v1 import Runtime
from .raw_archive_v1 import create,digest,rooted,verify,read
from ..confirmatory_v1.journal import exclusive_json


class Recovery(Runtime):
    def export_invalid(self,record,attempt_folder):
        ctx=self.context(record,attempt_folder);config=ctx['config'];folder=Path(attempt_folder)
        destination=folder/'recovered_exported_attempt.json'
        if destination.exists():
            exported=read(destination)
            verify(self.root,exported['raw_archive_path'],exported['raw_archive_sha256'],ctx['freeze_sha256'],
                record,config['image_id'],ctx['excluded_hashes'],expected_phase=self.phase)
            if digest(rooted(self.root,exported['validity_receipt_path']))!=exported['validity_receipt_sha256']:
                raise ValueError('retained interrupted validity receipt changed')
            return exported
        # Only these CID files can authorize cleanup. Never stop a name that
        # might belong to another episode; never dispatch a reader or robot.
        for name in ('container_id.txt','native_reader_id.txt'):
            path=folder/name
            if path.exists():
                cid=path.read_text().strip()
                if re.fullmatch('[0-9a-f]{64}',cid):subprocess.run(['docker','kill',cid],capture_output=True)
        cap_root=rooted(self.root,config['capture_root']);capture=cap_root/record['episode_id']
        if capture.exists():
            subprocess.run(['docker','run','--rm','--network','none','-v',str(cap_root)+':/provenance',
                '--entrypoint','chown',config['image_id'],'-R',f'{os.getuid()}:{os.getgid()}',
                '/provenance/'+record['episode_id']],capture_output=True)
        capture.mkdir(parents=True,exist_ok=True);receipt=capture/'provenance.json'
        if not receipt.exists():
            exclusive_json(receipt,dict(schema='hexar-frozen-raw-interruption-capture/v1',
                episode_id=record['episode_id'],family_hidden=record['family'],seed_hidden=record['seed'],
                acquisition_phase=self.phase,acquisition_binding_sha256=ctx['freeze_sha256'],
                image_id=config['image_id'],fresh_container=False,exit_code=-1,
                method_outputs_generated=False,judge_labels_generated=False,
                source_hashes=config['source_hashes'],execution_source_bank_sha256=config['execution_source_bank_sha256'],
                error='Indeterminate host interruption; physical/reset completeness cannot be asserted'))
        pin=dict(path=str(receipt.relative_to(self.root)),sha256=digest(receipt))
        archive_path=folder/'interrupted_raw_archive.json'
        if archive_path.exists():
            verify(self.root,str(archive_path.relative_to(self.root)),digest(archive_path),ctx['freeze_sha256'],record,
                   config['image_id'],ctx['excluded_hashes'],expected_phase=self.phase)
        else:
            create(self.root,archive_path,capture,record,ctx['freeze_sha256'],pin,config['image_id'],
                   ctx['excluded_ids'],ctx['excluded_seeds'],ctx['excluded_hashes'],expected_phase=self.phase)
        validity=read(ctx['base']/'technical_validity.json');pred=validity['machine_predicate_sha256']
        closed=dict(schema='hexar-frozen-raw-validity/v1',acquisition_id=record['acquisition_id'],
            freeze_sha256=ctx['freeze_sha256'],raw_archive_sha256=digest(archive_path),
            validity_predicate_sha256=pred,technical_valid=False,
            reasons=['HOST_INTERRUPTION_AFTER_DURABLE_CLAIM'],method_outcomes_accessed=False,
            independent_reset_measured=False,navigation_success_used_as_exclusion=False,
            recovery_rule='Frozen conservative interruption disposition; prior native/export artifacts remain retained.')
        validity_path=folder/'interrupted_validity_receipt.json'
        if validity_path.exists():
            if read(validity_path)!=closed:raise ValueError('retained interrupted disposition differs')
        else:exclusive_json(validity_path,closed)
        exported=dict(record,raw_archive_path=str(archive_path.relative_to(self.root)),raw_archive_sha256=digest(archive_path),
            validity_receipt_path=str(validity_path.relative_to(self.root)),validity_receipt_sha256=digest(validity_path),
            validity_predicate_sha256=pred)
        exclusive_json(destination,exported)
        return exported
