import json
import sys
import tarfile
from pathlib import Path
import publish_roboboat_terminal_capsule as module


def test_relative_artifact_root_publishes_atomic_capsule_and_coordinator_intake(tmp_path,monkeypatch):
    root=tmp_path/'workspace';root.mkdir();doc=root/'docs/roboboat_terminal_evidence';doc.mkdir(parents=True)
    artifacts=root/'artifacts/boat';artifacts.mkdir(parents=True)
    (artifacts/'comparison-results.json').write_text(json.dumps({'missing_annotations':[],'rows':[{} for _ in range(18)]}))
    (doc/'fixture.md').write_text('Isolated development fixture.')
    monkeypatch.setattr(module,'ROOT',root);monkeypatch.setattr(module,'DOC',doc)
    monkeypatch.chdir(root);monkeypatch.setattr(sys,'argv',['publish','--artifact-root','artifacts/boat'])
    module.main()
    capsule=artifacts/'publication/development-capsule-v1.tar.gz'
    assert capsule.is_file() and not capsule.with_suffix('.tmp').exists()
    with tarfile.open(capsule,'r:gz') as tar:
        assert 'artifacts/boat/comparison-results.json' in tar.getnames()
        assert 'docs/roboboat_terminal_evidence/fixture.md' in tar.getnames()
        assert all(not name.startswith('/') for name in tar.getnames())
    ledger=json.loads((doc/'publication_intake_ledger_v1.json').read_text())
    assert ledger['jobs']['boat-terminal-capsule-intake']['state']=='COMPLETED'
    assert ledger['releases']==[]
