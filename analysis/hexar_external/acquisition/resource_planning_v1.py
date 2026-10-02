"""Outcome-blind prospective resource planning; never selects scientific N."""
import argparse
import math
from pathlib import Path
import statistics

from .raw_archive_v1 import digest,read,rooted
from ..confirmatory_v1.journal import exclusive_json

ROOT=Path(__file__).resolve().parents[3]
RUN='manifests/hexar_external/acquisition/development_episode_plan_v16_qualification_run.json'
N_GRID=(72,114,768,1296,1920,3072)


def report(root=ROOT):
    root=Path(root);run=read(root/RUN)
    if len(run.get('episodes',[]))!=144 or run.get('phase')!='development_only':
        raise ValueError('complete 144-attempt development reliability capture required')
    rows=[];source_hashes={RUN:digest(root/RUN)}
    for receipt in run['episodes']:
        uid=receipt['episode_id'];path=root/'manifests/hexar_external/acquisition'/uid/'provenance.json'
        if read(path)!=receipt:raise ValueError('original reliability receipt differs')
        source_hashes[str(path.relative_to(root))]=digest(path)
        seconds=receipt['wall_seconds']
        if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0:
            raise ValueError('invalid retained capture time')
        raw_bytes=0
        for item in receipt['raw_files']:
            p=rooted(root,item['path'])
            if p.stat().st_size!=item['size'] or digest(p)!=item['sha256']:
                raise ValueError('retained reliability capture bytes changed')
            if '/raw/' in item['path']:raw_bytes+=item['size']
        rows.append(dict(episode_id=uid,family=receipt['family_hidden'],capture_wall_seconds=seconds,
            original_raw_bytes=raw_bytes))
    families=sorted({r['family'] for r in rows})
    if len(families)!=6 or any(sum(r['family']==f for r in rows)!=24 for f in families):
        raise ValueError('balanced original reliability cohort required')
    observed=dict(attempts=144,capture_wall_seconds_mean=statistics.mean(r['capture_wall_seconds'] for r in rows),
        capture_wall_seconds_maximum=max(r['capture_wall_seconds'] for r in rows),
        raw_bytes_mean=statistics.mean(r['original_raw_bytes'] for r in rows),
        raw_bytes_maximum=max(r['original_raw_bytes'] for r in rows),
        original_capture_bytes=sum(r['original_raw_bytes'] for r in rows))
    scenarios=[]
    for n in N_GRID:
        quota=n//6
        # Exact previously calculated reserve at N3072; smaller quota rows use
        # no implied scientific reserve decision and report valid attempts only.
        maximum_attempts=n+6*167 if n==3072 else None
        scenarios.append(dict(candidate_valid_n=n,balanced_valid_per_family=quota,
            capture_hours_at_observed_mean=n*observed['capture_wall_seconds_mean']/3600,
            raw_gib_at_observed_mean=n*observed['raw_bytes_mean']/2**30,
            raw_gib_at_observed_maximum=n*observed['raw_bytes_maximum']/2**30,
            prompt_model_calls=6*n,deterministic_contract_realizations=6*n,
            initial_agent_judgments=24*n,maximum_disagreement_only_judgments=12*n,
            model_calls_without_C=30*n,maximum_model_calls_with_C=42*n,
            conditional_20_percent_invalidity_reserve_maximum_attempts=maximum_attempts,
            reserve_capture_hours_at_observed_mean=(maximum_attempts*observed['capture_wall_seconds_mean']/3600 if maximum_attempts else None),
            reserve_raw_gib_at_observed_maximum=(maximum_attempts*observed['raw_bytes_maximum']/2**30 if maximum_attempts else None)))
    source_hashes[str(Path(__file__).relative_to(root))]=digest(Path(__file__))
    return dict(schema='hexar-outcome-blind-acquisition-resource-planning/v1',phase='development_planning',
        status='CONDITIONAL_RESOURCE_FORECAST_NO_N_DECISION',observed=observed,rows=rows,scenarios=scenarios,
        source_hashes=source_hashes,final_valid_n=None,confirmation_authorized=False,semantic_outputs_generated=0,
        alpha_consumed=0,cost_estimate=None,
        limits=['Mean/max capture forecasts are observations, not upper bounds or guarantees.',
          'Native review, admission/inventory, filesystem, sealing and provider durations are additional and not estimated here.',
          'Storage forecasts cover original raw files only; derived streams, transport archives and semantic artifacts require additional capacity.',
          'N3072 reserve is the existing conditional .20-invalidity/167-per-family example, not an adopted reserve decision.',
          'Call counts follow six unique requests per method, two initial independent judges per unique output, and at most one disagreement C per output.',
          'No assumption about semantic failure rates, gate success or power is inferred from acquisition resource observations.'])


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    value=report();exclusive_json(args.output,value);print(value['observed'])
