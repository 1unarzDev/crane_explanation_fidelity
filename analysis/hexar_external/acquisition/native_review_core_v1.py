"""Phase-aware raw/native review in the pinned TIAGo image; no providers.

Original capture is read-only. Compatibility files needed by the previously
qualified checker are created in temporary scratch, never in original capture.
"""
import argparse
import json
from pathlib import Path
import sys
import tempfile


def execute(folder,bank,receipt,expected_phase,expected_binding):
    folder,bank=Path(folder).resolve(),Path(bank).resolve()
    if expected_phase not in ('raw_confirmation','development_adapter_qualification'):
        raise ValueError('explicit acquisition phase required')
    if (receipt.get('acquisition_phase')!=expected_phase
            or receipt.get('acquisition_binding_sha256')!=expected_binding
            or receipt.get('method_outputs_generated') is not False
            or receipt.get('judge_labels_generated') is not False):
        raise ValueError('receipt phase/binding/semantic scope differs')
    episode=json.loads((folder/'episode.json').read_text())
    intent=json.loads((folder/'acquisition_intent.json').read_text())
    if any(v.get('phase')!=expected_phase or v.get('acquisition_binding_sha256')!=expected_binding for v in (episode,intent)):
        raise ValueError('original runtime and prelaunch intent differ from bound receipt')
    sys.path.insert(0,str(bank))
    import extract_events
    import extract_motion_v2
    import sampling_clock_qualification
    import clock_envelope_review
    events=extract_events.extract(folder/'raw')
    motion,extraction=extract_motion_v2.extract(folder/'raw')
    uid=receipt['episode_id']
    if not isinstance(uid,str) or Path(uid).name!=uid or uid in ('.','..'):
        raise ValueError('safe single episode identity required')
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);compat=root/uid;compat.mkdir()
        # Native checker reads original physics/reset/seed/raw bytes through
        # read-only links; only normalized compatibility streams are authored.
        (compat/'raw').symlink_to(folder/'raw',target_is_directory=True)
        (compat/'episode.json').symlink_to(folder/'episode.json')
        (compat/'events_development.json').write_text(json.dumps(events))
        (compat/'motion_events_v3.json').write_text(json.dumps(motion))
        run=root/'closed_native_input.json'
        run.write_text(json.dumps(dict(phase=expected_phase,episodes=[receipt])))
        native=sampling_clock_qualification.native(root,bank,run)[0]
    envelope=clock_envelope_review.native(folder)
    full_stream=native['checks'].pop('odometry_within_observed_simulated_clock_range')
    native['checks'].update(action_boundaries_within_clock_envelope=envelope['action_boundaries_within_clock_envelope'],
        task_window_odometry_within_clock_envelope=envelope['task_window_odometry_outside_envelope_n']==0)
    native.update(full_stream_clock_envelope_passed=full_stream,clock_envelope_diagnostic=envelope,
                  passed=all(native['checks'].values()))
    return dict(schema='hexar-phase-aware-native-review/v1',episode_id=uid,phase=expected_phase,
        acquisition_binding_sha256=expected_binding,native_review=native,events=events,motion=motion,
        motion_extraction=extraction,original_capture_mutated=False,method_or_judge_calls=0)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--folder',type=Path,required=True)
    ap.add_argument('--bank',type=Path,required=True);ap.add_argument('--receipt',type=Path,required=True)
    ap.add_argument('--phase',required=True);ap.add_argument('--binding',required=True)
    args=ap.parse_args()
    print(json.dumps(execute(args.folder,args.bank,json.loads(args.receipt.read_text()),args.phase,args.binding)))
