"""Pure outcome-blind selection of frozen raw archives, including missing bags.

A production wrapper must verify the committed acquisition freeze, fresh plan,
qualified native validity and exact runtime before invoking or writing a seal.
This candidate never authorizes confirmation or writes a seal itself.
"""
from pathlib import Path

from ..acquisition.raw_archive_v1 import digest, read, rooted, verify
from .seal_cohort import verify_attempt_schedule


def select(root, plan, attempts, quota, maximum_per_family, families,
           freeze_sha256, validity_predicate_sha256, expected_image,
           excluded_ids=(),excluded_seeds=(),excluded_raw_hashes=()):
    if type(quota) is not int or quota<1:raise ValueError('positive frozen valid family quota required')
    if any(not isinstance(v,str) or len(v)!=64 for v in (freeze_sha256,validity_predicate_sha256)):
        raise ValueError('exact frozen acquisition and native predicate hashes required')
    verify_attempt_schedule(plan,attempts,families,maximum_per_family)
    allocated={r['acquisition_id']:r for r in plan['records']}
    groups={family:[] for family in families}
    seen_ids,seen_seeds,seen_archives,seen_bags=set(),set(),set(),set()
    for attempt in attempts:
        uid=attempt['acquisition_id'];record=allocated[uid]
        if uid in seen_ids or attempt['seed'] in seen_seeds:raise ValueError('duplicate attempted identity/seed')
        if uid in excluded_ids or attempt['seed'] in excluded_seeds:raise ValueError('development identity/seed reused')
        seen_ids.add(uid);seen_seeds.add(attempt['seed'])
        sha=attempt['raw_archive_sha256']
        if sha in seen_archives:raise ValueError('duplicate raw attempt archive')
        seen_archives.add(sha)
        archive=verify(root,attempt['raw_archive_path'],sha,freeze_sha256,record,expected_image,excluded_raw_hashes)
        for bag in archive['bag_sha256s']:
            if bag in seen_bags:raise ValueError('recording bytes duplicated between attempts')
            seen_bags.add(bag)
        receipt_path=rooted(root,attempt['validity_receipt_path'])
        if digest(receipt_path)!=attempt['validity_receipt_sha256']:raise ValueError('native validity receipt changed')
        receipt=read(receipt_path)
        if (receipt.get('schema')!='hexar-frozen-raw-validity/v1' or receipt.get('acquisition_id')!=uid
                or receipt.get('freeze_sha256')!=freeze_sha256
                or receipt.get('raw_archive_sha256')!=sha
                or receipt.get('validity_predicate_sha256')!=validity_predicate_sha256
                or attempt.get('validity_predicate_sha256')!=validity_predicate_sha256
                or receipt.get('method_outcomes_accessed') is not False
                or type(receipt.get('technical_valid')) is not bool or type(receipt.get('reasons')) is not list):
            raise ValueError('frozen outcome-blind native validity binding required')
        if receipt['technical_valid']:
            if (archive['bag_missing'] or archive['fresh_container'] is not True or receipt.get('independent_reset_measured') is not True
                    or receipt['reasons']):
                raise ValueError('valid recording must have actual bag and measured independent reset')
            names={Path(f['path']).relative_to(archive['folder']).as_posix() for f in archive['artifacts']}
            required={'acquisition_intent.json','episode.json','controller_start.json','controller_end.json','raw/metadata.yaml'}
            if not required<=names:raise ValueError('valid recording lacks required original capture artifacts')
        elif not receipt['reasons']:
            raise ValueError('invalid attempt requires explicit technical reasons')
        groups[attempt['family']].append((attempt,receipt['technical_valid']))
    selected,dispositions=[],[]
    for family in families:
        rows=sorted(groups[family],key=lambda item:item[0]['attempt_order'])
        valid=0
        for attempt,passed in rows:
            if valid==quota:raise ValueError('attempt acquired after family quota completed')
            if passed:
                valid+=1;selected.append(dict(attempt,technical_valid=True,semantic_outputs_inspected=False))
            dispositions.append(dict(acquisition_id=attempt['acquisition_id'],family=family,
                                     disposition='SELECTED' if passed else 'TECHNICAL_INVALID'))
        if valid!=quota:raise ValueError('finite reserve exhausted: no balanced confirmatory cohort')
    return selected,dispositions
