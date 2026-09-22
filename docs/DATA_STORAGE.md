# Governed artifact storage

Git retains source, DVC pointer files, and content-free manifests. DVC retains the ignored episode
captures, evaluator-only records, model outputs, and model-call caches in a private Cloudflare R2
bucket through its S3-compatible endpoint.

## Tracked roots

- `data/robot_visible/{dev,final}`
- `data/evaluator_only/{dev,final}`
- `data/evaluator_only/annotation_keys`
- `model_outputs`
- `research/explanation_fidelity/model_cache`

The robot-visible and evaluator-only roots remain physically separate in both the workspace and
their DVC object identities. DVC does not make evaluator-only data model-visible; access control and
the experiment tooling must still preserve that boundary. `data/staging/`, build artifacts, and
temporary files are not synchronized.

The closed ecological pilot snapshot is under
`data/robot_visible/dev/ecological-pilot-v1/` and
`data/evaluator_only/dev/ecological-pilot-v1/`. It retains three qualified exports (warehouse
recovery, complete blockage, corrected S-turn), evaluator truth, QA summaries, and one evaluator-only
provenance manifest containing component/source hashes. Large Unity builds and full runtime
directories are deliberately omitted. A fresh checkout must run `scripts/dvc_r2_sync.sh pull`
before the pilot; model-facing tooling may read only the robot-visible root.

After a validated run or retained model batch, refresh the DVC pointers:

```bash
scripts/update_dvc_tracking.sh
git add data/robot_visible/*.dvc data/evaluator_only/*.dvc \
  model_outputs.dvc research/explanation_fidelity/model_cache.dvc
```

Commit pointer changes alongside or immediately after the corresponding run/model manifest. Raw
payloads remain ignored by Git.

## Install

The tested versions are pinned in `requirements-dvc.txt`. With `uv`:

```bash
uv tool install --python 3.13 dvc --with dvc-s3
```

## Create the R2 bucket and credentials

In the Cloudflare dashboard:

1. Create a private R2 bucket using **Standard** storage. The free tier does not apply to
   Infrequent Access storage.
2. Keep public `r2.dev` access disabled.
3. Create a bucket-scoped R2 S3 token with Object Read & Write permission. Record its Access Key ID
   and Secret Access Key when shown.
4. Create a separate Cloudflare API token with Account Analytics Read permission. The sync guard
   uses it to query account-wide R2 operations and storage; it is not an S3 credential.

Copy the credential template and fill `.env`, which is ignored by Git:

```bash
cp .env.example .env
# Edit .env without committing it.

scripts/configure_dvc_r2.sh
```

The scripts load root `.env` automatically. `CLOUDFLARE_API_TOKEN` must be a separate, active
Cloudflare API token scoped to this account with Account Analytics Read permission; it is not the
R2 S3 token, Access Key ID, or Secret Access Key.

The setup command writes the endpoint and S3 credentials only to ignored `.dvc/config.local`.
Never commit that file or place secrets in a data manifest.

## Sync

```bash
scripts/dvc_r2_sync.sh status
scripts/dvc_r2_sync.sh push
scripts/dvc_r2_sync.sh pull
```

### Publish a restorable snapshot

A DVC push uploads the objects named by the current `.dvc` pointer files. It does not discover
files created after those pointers were generated. Do not collect or modify governed data while
refreshing and pushing a snapshot.

A successful pull of some pointers does not prove every governed root is materialized. The sync
wrapper must name all seven pointers, and its regression test enforces that contract. Before
refreshing pointers, run `dvc status` and compare file counts against the prior pointer; an
unexpected decrease can publish a silently truncated snapshot.

```bash
# Refresh pointers after the validated run/model batch is complete.
scripts/update_dvc_tracking.sh

# Review the seven changed pointer files, then upload exactly that snapshot.
git diff -- data/robot_visible/*.dvc data/evaluator_only/*.dvc \
  model_outputs.dvc research/explanation_fidelity/model_cache.dvc
scripts/dvc_r2_sync.sh push

# Commit and publish the pointers only after the DVC push succeeds.
git add data/robot_visible/*.dvc data/evaluator_only/*.dvc \
  model_outputs.dvc research/explanation_fidelity/model_cache.dvc
git commit -m "data: update DVC snapshot pointers"
git push
```

The Git commit makes the snapshot discoverable; the R2 upload makes its referenced content
available. Both are required for restoration on another device. If data changes during a push,
let that push finish, refresh the pointers again, and perform another guarded push. Never assume a
push of an older pointer includes newly created episodes or model outputs.

### Restore on another device

After cloning the umbrella repository and initializing its package dependencies, install the
pinned DVC tooling, provision that device's local credentials, configure the remote, and pull:

```bash
git clone --recurse-submodules <umbrella-repository-url>
cd crane_explanation_fidelity
scripts/setup_workspace.sh

uv tool install --python 3.13 dvc --with dvc-s3
cp .env.example .env
# Fill .env with credentials issued for this device/person.
scripts/configure_dvc_r2.sh
scripts/dvc_r2_sync.sh status
scripts/dvc_r2_sync.sh pull
```

The pull restores only the seven governed roots listed above. It intentionally does not restore
`data/staging/`, `artifacts/`, ROS bags outside those roots, model weights, build products, or every
other file ignored by Git.

### Collaborator access and credential handling

Do not share the repository owner's existing `.env`. Create separate, revocable credentials for
each collaborator or device:

1. Issue an R2 S3 token restricted to this project's dedicated bucket. Use Object Read only for a
   download-only collaborator, or Object Read & Write when they must push as well as pull.
2. Issue a separate Cloudflare API token restricted to Account Analytics Read so the sync wrapper
   can perform its required account-wide budget check. Do not reuse a broad administrative token.
3. Give the collaborator only the project account ID, bucket, prefix, and those newly issued
   credentials through a password manager or another encrypted secret-sharing channel.
4. Revoke the collaborator's tokens when access ends. Rotate credentials immediately if an
   `.env` is committed, pasted into chat, emailed in plaintext, or otherwise exposed.

Bucket-scoped read/write access may allow a collaborator to overwrite or delete objects within
that bucket. Use a dedicated project bucket, keep public access disabled, and retain the Git-pinned
manifests and pointers needed to detect or recover from unintended changes.

The wrapper uses one DVC worker and refuses network access unless it can query account-wide R2
metrics for the rolling 31-day retention window. It then applies conservative projections at 90%
of the published free tier. Every remote action, including status, is pessimistically budgeted
against both operation classes:

| Resource | Published free tier | Local refusal threshold |
| --- | ---: | ---: |
| Standard storage | 10 GB-month/month | 9 GB projected account storage |
| Class A operations | 1,000,000/month | 900,000 projected month-to-date |
| Class B operations | 10,000,000/month | 9,000,000 projected month-to-date |

The initial local snapshot is under 100 MB and approximately 2,900 files, so it is comfortably
inside those guardrails.

## No-fee limitation

Cloudflare documents these values as a free tier, not hard quotas. R2 storage per bucket is
unlimited, and usage beyond the included amounts is billable. Cloudflare does not expose a
server-side R2 setting that stops requests or storage exactly at the free-tier boundary.

Therefore **this repository cannot guarantee zero fees**. The wrapper reduces risk by requiring
account-wide metrics, refusing unknown operation types, overestimating the pending transfer, using
one worker, and retaining 10% headroom. Metrics can lag, another client can bypass the wrapper, and
old DVC cache objects accumulate across revisions. Use only this wrapper, inspect the R2 Metrics tab
after transfers, enable any billing notifications available on the account, and revoke the S3 token
when synchronization is not needed. Notifications are alerts, not enforcement.

Collaborator-specific credentials do not change this limitation. Anyone with valid S3 credentials
can bypass the repository wrapper, and R2 does not provide a per-token or per-bucket hard free-tier
cap. The wrapper is a cooperative safety control, not a security boundary or spending guarantee.

Authoritative Cloudflare references:

- <https://developers.cloudflare.com/r2/pricing/>
- <https://developers.cloudflare.com/r2/platform/limits/>
- <https://developers.cloudflare.com/r2/platform/metrics-analytics/>
