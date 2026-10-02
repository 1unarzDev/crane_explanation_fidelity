"""Outcome-blind retained V16 inventory; no simulator/provider dispatch."""
import json
from pathlib import Path
from ..acquisition.raw_archive_v1 import digest
from ..acquisition.navigation_usefulness_v2 import public_packet, reference
from ..confirmatory_v1.rich_blind_projection import project
from ..confirmatory_v1.journal import fingerprint

ROOT=Path(__file__).resolve().parents[3]
BANK=ROOT/'manifests/hexar_external/acquisition/development_reliability_v16'
FAMILIES=('charging','dynamic_env','localization','manual_joystick','obstacle','success')


def inventory():
    report=json.loads((BANK/'report.json').read_text())
    if report['method_or_judge_calls']!=0 or report['phase']!='development_only':
        raise ValueError('original acquisition bank identity changed')
    for name,sha in report['evidence_hashes'].items():
        if digest(BANK/name)!=sha:raise ValueError('retained review changed: '+name)
    interface=json.loads((BANK/'interface_review.json').read_text())
    native=json.loads((BANK/'native_inputs.json').read_text())
    raw={r['episode_id']:r for r in native['episodes']}
    technical={r['episode_id']:r for r in report['rows']}
    evidence={r['development_id']:r for r in interface['episodes']}
    packets={uid:[] for uid in raw}
    for p in interface['packets']:
        if fingerprint(p['method_packet'])!=p['closure']['packet_sha256']:raise ValueError('retained packet changed')
        packets[p['development_id']].append(p)
    rows=[]
    for uid in sorted(raw):
        run=raw[uid];reason=[]
        for item in run['raw_files']:
            path=ROOT/item['path']
            if not path.is_file() or path.stat().st_size!=item['size'] or digest(path)!=item['sha256']:
                reason.append('missing_or_changed_raw:'+item['path'])
        ep_path=next(ROOT/i['path'] for i in run['raw_files'] if i['path'].endswith('/episode.json'))
        ep=json.loads(ep_path.read_text())
        for name,sha in evidence[uid]['files'].items():
            path=ep_path.parent/name
            if not path.is_file() or digest(path)!=sha:reason.append('missing_or_changed_normalized:'+name)
        if not technical[uid]['technical_valid']:reason.append('original_technical_invalid')
        if len(packets[uid])!=9:reason.append('incomplete_retained_battery')
        for p in packets[uid]:
            try:
                packet=public_packet(p['method_packet']);refs=reference(packet)
                project(packet,refs,'Pre-generation neutral interface check.')
                if p['condition']!='diagnostic_removal':
                    snaps=[json.loads((ep_path.parent/n).read_text())['snapshot'] for n in ('controller_start.json','controller_end.json')]
                    if packet['source_context']['controller_runtime_observations']!=snaps:raise ValueError('runtime snapshots differ')
            except (ValueError,KeyError,TypeError) as exc:reason.append('packet_interface:'+str(exc))
        bags=[i for i in run['raw_files'] if i['path'].endswith('.db3')]
        rows.append(dict(episode_id=uid,family=technical[uid]['family'],seed=ep['seed_hidden'],
            container_id=run['container_id'],configuration=ep['sampling_hidden'],raw_root=str(ep_path.parent.relative_to(ROOT)),
            bag_files=bags,normalized_files=evidence[uid]['files'],technical_valid=technical[uid]['technical_valid'],
            eligible=not reason,ineligibility_reasons=reason,development_exposed=True,original_acquisition_semantic_calls=0,
            previous_comparable_output_count=0,previous_output_scope='Acquisition receipt has zero semantic calls; other semantic banks use distinct episode identities.',
            reference_version='hexar-navigation-development-reference/v2',retained_battery_cells=len(packets[uid])))
    for key in ('episode_id','seed','container_id'):
        if len({r[key] for r in rows})!=144:raise ValueError('independent identity collision: '+key)
    if len({b['sha256'] for r in rows for b in r['bag_files']})!=144:raise ValueError('bag content collision')
    return dict(schema='hexar-existing-v16-exploratory-inventory/v1',bank='V16',episodes=rows,
        counts_by_family={f:dict(collected=sum(r['family']==f for r in rows),eligible=sum(r['family']==f and r['eligible'] for r in rows),comparable_preexisting=0) for f in FAMILIES},
        acquired=144,eligible=sum(r['eligible'] for r in rows),model_or_judge_calls=0,robot_launches=0,
        source_hashes={str((BANK/n).relative_to(ROOT)):digest(BANK/n) for n in ('report.json','interface_review.json','native_inputs.json')},
        source_context_limit='Authenticated retained controller boundary snapshots and static source context; neither proves continuous wiring, physical arrival or unique cause.')
