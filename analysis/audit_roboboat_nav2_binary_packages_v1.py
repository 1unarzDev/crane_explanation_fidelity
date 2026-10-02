"""Exact installed-file equality to matching ROS snapshot debs; qualified trust labels."""
import gzip
import io
import json
from pathlib import Path
import tarfile
import urllib.request
from audit_roboboat_nav2_source_v1 import digest, binding


def stanzas(raw):
    result=[]
    for stanza in raw.decode().split('\n\n'):
        fields={}
        for line in stanza.splitlines():
            if line and not line.startswith(' ') and ':' in line:
                key,value=line.split(':',1);fields[key]=value.strip()
        if fields:result.append(fields)
    return result


def deb_files(raw):
    if raw[:8]!=b'!<arch>\n':raise ValueError('not Debian ar archive')
    offset=8;data=None
    while offset<len(raw):
        header=raw[offset:offset+60]
        if len(header)!=60 or header[-2:]!=b'`\n':raise ValueError('invalid ar header')
        size=int(header[48:58]);name=header[:16].decode().strip().rstrip('/')
        member=raw[offset+60:offset+60+size]
        if name.startswith('data.tar'):data=member
        offset+=60+size+(size%2)
    if data is None:raise ValueError('missing Debian data archive')
    files={}
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:*') as tar:
        for item in tar:
            if not item.isfile():continue
            name=Path(item.name)
            if name.is_absolute() or '..' in name.parts:raise ValueError('unsafe deb payload path')
            files['/'+name.as_posix().removeprefix('./')]=tar.extractfile(item).read()
    return files


def audit(observation_path,root):
    observation_path,root=Path(observation_path).resolve(),Path(root).resolve()
    observation=json.loads(observation_path.read_text())
    index_raw=(root/'Packages.gz').read_bytes();index=stanzas(gzip.decompress(index_raw))
    base='http://snapshots.ros.org/jazzy/2026-06-18/ubuntu/'
    versions={line.split('\t')[0]:line.split('\t')[1] for line in observation['package_versions'].splitlines()}
    packages=[];payloads={}
    for name,version in versions.items():
        rows=[r for r in index if r.get('Package')==name and r.get('Version')==version and r.get('Architecture')=='amd64']
        if len(rows)!=1:raise ValueError('exact observed binary package missing from snapshot')
        row=rows[0];url=base+row['Filename'];target=root/Path(row['Filename']).name
        if not target.exists():target.write_bytes(urllib.request.urlopen(url,timeout=30).read())
        raw=target.read_bytes()
        if digest(raw)!=row['SHA256'] or len(raw)!=int(row['Size']):raise ValueError('published index/package checksum mismatch')
        files=deb_files(raw)
        for path,content in files.items():
            if path in payloads and payloads[path]!=content:raise ValueError('conflicting package payloads')
            payloads[path]=content
        packages.append({'package':name,'version':version,'url':url,'archive':binding(target),
                         'published_index_record':row,'payload_file_count':len(files)})
    comparisons=[]
    for item in observation['installed_files']:
        raw=Path(item['snapshot']).read_bytes()
        if digest(raw)!=item['sha256']:raise ValueError('observed installed bytes changed')
        candidate=payloads.get(item['container_path'])
        comparisons.append({'container_path':item['container_path'],'installed_sha256':item['sha256'],
                            'binary_package_payload_sha256':digest(candidate) if candidate is not None else None,
                            'status':'BYTE_IDENTICAL' if candidate is not None and digest(candidate)==item['sha256']
                                     else 'MISMATCH' if candidate is not None else 'NOT_IN_PAYLOAD'})
    result={'schema':'roboboat-nav2-binary-package-audit/v1-development',
        'observation':binding(observation_path),'episode_image_id':observation['image_id'],
        'index':binding(root/'Packages.gz'),'inrelease':binding(root/'InRelease'),
        'packages':packages,'comparisons':comparisons,
        'byte_identical_count':sum(r['status']=='BYTE_IDENTICAL' for r in comparisons),
        'mismatch_count':sum(r['status']=='MISMATCH' for r in comparisons),
        'missing_payload_count':sum(r['status']=='NOT_IN_PAYLOAD' for r in comparisons),
        'trust':{'transport':'HTTP_INDEX_AND_ARCHIVES; package hash agrees with retained index',
                 'apt_signature':'NOT_AUTHENTICATED; InRelease signer4B63CF8FDE49746E98FA01DDAD19BAB3CBF125EA not in fetched current ROS key',
                 'binary_equality':'BYTE_COMPARISON_TO_EXACT_OBSERVED_INSTALLED_FILES',
                 'source_build_equivalence':'NOT_ESTABLISHED'},
        'preparation_source':binding(__file__),'confirmation_n':0,'replication_n':0,'alpha_consumed':0}
    target=root/'binary-package-audit.json'
    with target.open('x') as stream:json.dump(result,stream,indent=2)
    return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--observation',type=Path,required=True);p.add_argument('--root',type=Path,required=True)
    a=p.parse_args();r=audit(a.observation,a.root);print(json.dumps({k:r[k] for k in ('byte_identical_count','mismatch_count','missing_payload_count')}))
