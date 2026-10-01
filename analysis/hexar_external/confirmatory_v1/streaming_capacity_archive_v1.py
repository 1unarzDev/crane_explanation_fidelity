"""Lossless retained synthetic payload archive; no provider/scientific activation."""
import gzip
import hashlib
import tarfile
from pathlib import Path

from .journal import exclusive_json, fingerprint
from .registered_attempt_executor_v2 import load_artifact
from .streaming_registry_shards_v1 import verify
from ..acquisition.raw_archive_v1 import digest

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'manifests/hexar_external/confirmatory_v1/development_streaming_capacity_v1'


def archive():
    report = load_artifact(BASE/'report.json')
    if (report['phase'] != 'synthetic_development_capacity_only' or report['provider_calls'] != 0
            or report['confirmatory_N'] != 0 or report['confirmation_authorized'] is not False):
        raise ValueError('terminal no-dispatch synthetic report required')
    folder = BASE/'payloads'
    index = verify(folder, report['canonical_index_sha256'])
    pins = {row['path']:dict(bytes=row['bytes'], sha256=row['sha256']) for row in index['shards']}
    for name in ('index.json', 'generation_claim.json'):
        path = folder/name
        pins[name] = dict(bytes=path.stat().st_size, sha256=digest(path))
    destination = BASE/'payloads.tar.gz'
    # Exclusive archive creation: retain partial bytes on failure; never repair
    # or remove the original payloads, declaration or capacity outcome.
    with destination.open('xb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.USTAR_FORMAT) as bundle:
                for name, pin in sorted(pins.items()):
                    path = folder/name
                    if path.stat().st_size != pin['bytes'] or digest(path) != pin['sha256']:
                        raise ValueError('original payload changed before archiving')
                    member = tarfile.TarInfo(name)
                    member.size = pin['bytes']; member.mode = 0o444; member.mtime = 0
                    with path.open('rb') as source:
                        bundle.addfile(member, source)
    reproduced = set()
    with tarfile.open(destination, mode='r|gz') as bundle:
        for member in bundle:
            if member.name not in pins or member.name in reproduced or not member.isreg():
                raise ValueError('unexpected archive entry')
            pin = pins[member.name]
            if member.size != pin['bytes']:
                raise ValueError('archive entry size differs')
            check = hashlib.sha256(); count = 0
            with bundle.extractfile(member) as source:
                while block := source.read(1048576):
                    check.update(block); count += len(block)
            if count != pin['bytes'] or check.hexdigest() != pin['sha256']:
                raise ValueError('lossless archive failed byte reproduction')
            reproduced.add(member.name)
    if reproduced != set(pins) or verify(folder, report['canonical_index_sha256']) != index:
        raise ValueError('incomplete archive or changed original bank')
    receipt = dict(schema='hexar-synthetic-streaming-payload-archive/v1',
        phase='synthetic_development_capacity_only', archive_path=destination.name,
        archive_sha256=digest(destination), archive_bytes=destination.stat().st_size,
        report_sha256=digest(BASE/'report.json'), canonical_index_sha256=fingerprint(index),
        original_bytes=sum(row['bytes'] for row in pins.values()), entries=pins,
        every_entry_losslessly_reproduced=True, originals_retained=True,
        producing_source_sha256=digest(Path(__file__)), provider_calls=0,
        confirmatory_N=0, confirmation_authorized=False)
    exclusive_json(BASE/'archive_receipt.json', receipt)
    print({k:v for k,v in receipt.items() if k != 'entries'}, flush=True)
    return receipt


if __name__ == '__main__':
    archive()
