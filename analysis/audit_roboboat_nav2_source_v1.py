#!/usr/bin/env python3
"""Bind installed Nav2 observations to HTTPS release sources; no build-equivalence claim."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

PACKAGES=('nav2_controller','nav2_core','nav2_regulated_pure_pursuit_controller','nav2_bt_navigator')
REPOSITORY='ros2-gbp/navigation2-release'


def digest(raw): return hashlib.sha256(raw).hexdigest()

def binding(path): return {'path':str(Path(path).resolve()),'sha256':digest(Path(path).read_bytes())}

def fetch(url):
    with urllib.request.urlopen(url,timeout=30) as response: return response.read()


def archive_files(raw):
    files={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
        for member in archive.getmembers():
            if not member.isfile():continue
            relative=Path(member.name)
            if relative.is_absolute() or '..' in relative.parts:raise ValueError('unsafe archive path')
            name=Path(*relative.parts[1:]).as_posix()
            if name in files:raise ValueError('duplicate source archive path')
            files[name]=archive.extractfile(member).read()
    return files


def resolve_installed(container_path):
    relative=container_path.removeprefix('/opt/ros/jazzy/')
    if relative.startswith('include/'):
        package,tail=relative.removeprefix('include/').split('/',1)
        return package,'include/'+package+'/'+tail
    if relative.startswith('share/'):
        package,tail=relative.removeprefix('share/').split('/',1)
        return package,tail
    return None


def audit(observation_path,output_root, *, getter=fetch):
    observation_path,output_root=Path(observation_path).resolve(),Path(output_root).resolve()
    if output_root.exists():raise FileExistsError('immutable Nav2 source audit already exists')
    observation=json.loads(observation_path.read_text())
    if observation['schema']!='roboboat-deployed-nav2-observation/v1':raise ValueError('deployed observation required')
    versions={}
    for line in observation['package_versions'].splitlines():
        fields=line.split('\t')
        if len(fields)!=4 or fields[0]!=fields[2] or fields[1]!=fields[3]:raise ValueError('ambiguous installed package identity')
        versions[fields[0]]=fields[1]
    for package in PACKAGES:
        name='ros-jazzy-'+package.replace('_','-')
        if not versions.get(name,'').startswith('1.3.12-1noble.20260615.'):
            raise ValueError('audit release does not match observed package version')
    for item in observation['installed_files']:
        raw=Path(item['snapshot']).read_bytes()
        if digest(raw)!=item['sha256'] or len(raw)!=item['bytes']:raise ValueError('installed snapshot changed')
    receipt=observation['container_id_receipt']
    if digest(Path(receipt['path']).read_bytes())!=receipt['sha256']:raise ValueError('episode container receipt changed')
    output_root.mkdir(parents=True,exist_ok=False)
    releases=[];source_files={};retrieval=[]
    for package in PACKAGES:
        # ROS release package commit and generated Debian branch commit are
        # separate immutable references. Their presence is not proof that an
        # installed binary was reproducibly compiled from them.
        for kind,tag in [('release',f'release/jazzy/{package}/1.3.12-1'),
                         ('debian',f'debian/ros-jazzy-{package.replace("_","-")}_1.3.12-1_noble')]:
            url=f'https://api.github.com/repos/{REPOSITORY}/git/ref/tags/'+tag
            raw=getter(url);target=output_root/'metadata'/(package+'-'+kind+'-ref.json')
            target.parent.mkdir(exist_ok=True);target.write_bytes(raw)
            reference=json.loads(raw)
            if reference['ref']!='refs/tags/'+tag or reference['object']['type']!='commit':raise ValueError('unexpected release reference')
            commit=reference['object']['sha']
            url_archive=f'https://codeload.github.com/{REPOSITORY}/tar.gz/{commit}'
            archive=getter(url_archive);archive_path=output_root/'archives'/(package+'-'+kind+'-'+commit+'.tar.gz')
            archive_path.parent.mkdir(exist_ok=True);archive_path.write_bytes(archive)
            files=archive_files(archive)
            for relative,content in files.items():
                destination=output_root/'sources'/kind/package/relative
                destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(content)
            if kind=='release':source_files[package]=files
            releases.append({'package':package,'kind':kind,'tag':tag,'commit':commit,
                             'reference':binding(target),'archive':binding(archive_path),
                             'file_count':len(files)})
            retrieval.extend([{'url':url,'saved':binding(target),'transport':'HTTPS_CERTIFICATE_VERIFIED'},
                              {'url':url_archive,'saved':binding(archive_path),'transport':'HTTPS_CERTIFICATE_VERIFIED'}])
    comparisons=[]
    for item in observation['installed_files']:
        resolved=resolve_installed(item['container_path'])
        if resolved is None:continue
        package,relative=resolved
        if package not in source_files:continue
        raw=source_files[package].get(relative)
        comparisons.append({'container_path':item['container_path'],'installed_sha256':item['sha256'],
            'package':package,'release_source_relative_path':relative,
            'release_source_sha256':digest(raw) if raw is not None else None,
            'status':'BYTE_IDENTICAL' if raw is not None and digest(raw)==item['sha256'] else
                     'BYTE_DIFFERENT' if raw is not None else 'NOT_PRESENT_IN_PACKAGE_RELEASE'})
    original_files=[binding(p) for p in sorted((output_root/'sources').rglob('*')) if p.is_file()]
    result={'schema':'roboboat-nav2-release-source-audit/v1-development',
        'status':'MATCHING_PUBLIC_RELEASE_SOURCE_WITH_DEPLOYED_BYTE_COMPARISONS',
        'observation':binding(observation_path),'actual_episode_image_id':observation['image_id'],
        'actual_episode_container_id':observation['container_id'],'episode_receipt':receipt,
        'installed_package_versions':versions,'releases':releases,'retrievals':retrieval,
        'source_files':original_files,'installed_comparisons':comparisons,
        'byte_identical_count':sum(r['status']=='BYTE_IDENTICAL' for r in comparisons),
        'byte_different_count':sum(r['status']=='BYTE_DIFFERENT' for r in comparisons),
        'unmapped_source_count':sum(r['status']=='NOT_PRESENT_IN_PACKAGE_RELEASE' for r in comparisons),
        'installed_binary_bindings':[{'container_path':r['container_path'],**binding(r['snapshot'])}
                                    for r in observation['installed_files'] if '/lib/' in r['container_path']],
        'authentication':{'installed_episode_snapshots':'OBSERVED_SOURCE_BOUND_BYTES',
            'release_source':'HTTPS_COMMIT_BOUND_MATCHING_RELEASE_VERSION',
            'exact_debian_source_package':'NOT_RETRIEVED_OR_SIGNATURE_AUTHENTICATED',
            'binary_package_archive':'NOT_RETRIEVED_OR_APT_SIGNATURE_AUTHENTICATED',
            'installed_binary_source_build_equivalence':'NOT_ESTABLISHED'},
        'limitations':['Release/debian Git refs and matching headers do not establish exact Debian source archive provenance.',
            'Build flags, dependencies, ROS build-farm timestamp and compiler provenance are not reconstructed.',
            'No deterministic rebuild or installed binary equivalence is claimed.',
            'No historical episode image identity is inferred; active episode receipt alone anchors this observation.'],
        'preparation_source':binding(__file__),'preparation_tests':binding(Path(__file__).resolve().parents[1]/'tests/test_audit_roboboat_nav2_source_v1.py'),
        'call_readiness':False,'provider_calls':0,'study_answers_read':False,
        'confirmation_n':0,'replication_n':0,'alpha_consumed':0}
    target=output_root/'source-audit.json';target.write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--observation',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True)
    a=p.parse_args();result=audit(a.observation,a.output_root)
    print(json.dumps({k:result[k] for k in ('status','byte_identical_count','byte_different_count','unmapped_source_count','call_readiness')}))


if __name__=='__main__':main()
