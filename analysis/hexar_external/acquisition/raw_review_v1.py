"""Frozen raw/native validity and archive export; no method/evaluator calls."""
import json
from pathlib import Path
import subprocess

from .raw_runtime_v1 import Runtime
from .raw_archive_v1 import create,digest,rooted,verify
from .operational_validity_candidate import evaluate
from .project_raw_episode_v1 import review as project
from ..confirmatory_v1.journal import exclusive_json
from ..confirmatory_v1.registered_attempt_executor_v2 import raw_file
from ..confirmatory_v1.strict_json import load


class Review(Runtime):
    def __call__(self,record,runtime,attempt_folder):
        ctx=self.context(record,attempt_folder);config=ctx['config'];attempt_folder=Path(attempt_folder)
        root=self.root;folder=rooted(root,config['capture_root'])/record['episode_id']
        original=folder/'provenance.json'
        if not original.exists():
            # A launch-side infrastructure failure with no receipt is retained
            # as an explicit empty/partial capture, never a fabricated episode.
            folder.mkdir(parents=True,exist_ok=True)
            runtime=dict(schema='hexar-frozen-raw-capture-failure/v1',episode_id=record['episode_id'],
                seed_hidden=record['seed'],family_hidden=record['family'],fresh_container=False,
                acquisition_phase='raw_confirmation',acquisition_binding_sha256=ctx['freeze_sha256'],
                image_id=config['image_id'],method_outputs_generated=False,judge_labels_generated=False,
                exit_code=-1,error='Capture failed before durable raw receipt',source_hashes=config['source_hashes'],
                execution_source_bank_sha256=config['execution_source_bank_sha256'],raw_files=[])
            exclusive_json(original,runtime)
        receipt=load(original.read_bytes(),32*1024*1024)
        if runtime.get('episode_id') is not None and runtime!=receipt:raise ValueError('capture/runtime receipt differs')
        pin=dict(path=str(original.relative_to(root)),sha256=digest(original))
        archive_path=attempt_folder/'raw_archive.json'
        archive=create(root,archive_path,folder,record,ctx['freeze_sha256'],pin,config['image_id'],
            ctx['excluded_ids'],ctx['excluded_seeds'],ctx['excluded_hashes'])
        reasons=[];native={};projected={};independent_reset=False
        if receipt.get('exit_code')!=0 or receipt.get('fresh_container') is not True:
            reasons.append('CAPTURE_TECHNICAL_FAILURE')
        if receipt.get('observed_image_id')!=config['image_id']:reasons.append('OBSERVED_IMAGE_BINDING_INVALID')
        if archive['bag_missing']:reasons.append('NO_RAW_RECORDING')
        if not reasons:
            reader=rooted(root,config['native_reader']['path']);bank=rooted(root,config['source_bank_path'])
            cid=attempt_folder/'native_reader_id.txt'
            command=['docker','run','--rm','--cidfile',str(cid),'--network','none','--memory',config['memory'],
                '-v',str(folder)+':/capture:ro','-v',str(bank)+':/bank:ro',
                '-v',str(original)+':/receipt.json:ro','-v',str(reader)+':/review.py:ro',
                '--entrypoint','bash',config['image_id'],'-lc',
                'source /ws/install/setup.bash; python3 /review.py --folder /capture --bank /bank --receipt /receipt.json --phase raw_confirmation --binding "$1"',
                'native-review',ctx['freeze_sha256']]
            exclusive_json(attempt_folder/'native_dispatch_claim.json',dict(command=command,launch_limit=1,
                freeze_sha256=ctx['freeze_sha256'],method_or_judge_calls_permitted=False))
            stdout,stderr=b'',b''
            try:
                result=subprocess.run(command,capture_output=True,timeout=config['native_wall_timeout_seconds'])
                stdout,stderr=result.stdout,result.stderr
                if result.returncode!=0:raise ValueError('native reader return code '+str(result.returncode))
                value=load(stdout,32*1024*1024)
                if (value.get('schema')!='hexar-phase-aware-native-review/v1' or value.get('episode_id')!=record['episode_id']
                        or value.get('phase')!='raw_confirmation' or value.get('acquisition_binding_sha256')!=ctx['freeze_sha256']
                        or value.get('method_or_judge_calls')!=0 or value.get('original_capture_mutated') is not False):
                    raise ValueError('native reader phase/binding/scope differs')
                native=value['native_review']
                projected=project(folder,record['episode_id'],value['events'],value['motion'])
                episode=load((folder/'episode.json').read_bytes(),32*1024*1024)
                verdict=evaluate(receipt,episode,record,projected['episode'],native)
                reasons.extend(verdict['reasons']);independent_reset=not verdict['reasons']
                exclusive_json(attempt_folder/'derived_native_review.json',value)
                exclusive_json(attempt_folder/'derived_interface_review.json',projected)
            except subprocess.TimeoutExpired as exc:
                stdout,stderr=exc.stdout or b'',exc.stderr or b''
                reasons.append('NATIVE_REVIEW_UNRESOLVED: TimeoutExpired: '+str(exc))
            except Exception as exc:
                reasons.append('NATIVE_REVIEW_UNRESOLVED: '+type(exc).__name__+': '+str(exc))
            finally:
                raw_file(attempt_folder/'native_stdout.bin',stdout);raw_file(attempt_folder/'native_stderr.bin',stderr)
                # Timeout/crash reader cleanup touches only the CID belonging to
                # this immutable reader claim, never a robot or prior container.
                if cid.exists():
                    import re
                    identity=cid.read_text().strip()
                    if re.fullmatch('[0-9a-f]{64}',identity):
                        subprocess.run(['docker','kill',identity],capture_output=True)
        verify(root,str(archive_path.relative_to(root)),digest(archive_path),ctx['freeze_sha256'],record,
               config['image_id'],ctx['excluded_hashes'])
        validity=load((ctx['base']/'technical_validity.json').read_bytes(),32*1024*1024)
        if validity.get('machine_predicate_implementation')!='analysis/hexar_external/acquisition/raw_review_v1.py' or validity.get('machine_predicate_sha256')!=digest(Path(__file__)):
            raise ValueError('final native predicate implementation not frozen to this review adapter')
        closed=dict(schema='hexar-frozen-raw-validity/v1',acquisition_id=record['acquisition_id'],
            freeze_sha256=ctx['freeze_sha256'],raw_archive_sha256=digest(archive_path),
            validity_predicate_sha256=validity['machine_predicate_sha256'],technical_valid=not reasons,
            reasons=reasons,method_outcomes_accessed=False,independent_reset_measured=independent_reset,
            navigation_success_used_as_exclusion=False)
        receipt_path=attempt_folder/'validity_receipt.json';exclusive_json(receipt_path,closed)
        exported=dict(record,raw_archive_path=str(archive_path.relative_to(root)),raw_archive_sha256=digest(archive_path),
            validity_receipt_path=str(receipt_path.relative_to(root)),validity_receipt_sha256=digest(receipt_path),
            validity_predicate_sha256=validity['machine_predicate_sha256'])
        exclusive_json(attempt_folder/'exported_attempt.json',exported)
        return dict(technical_valid=closed['technical_valid'],reasons=reasons,method_outcomes_accessed=False)
