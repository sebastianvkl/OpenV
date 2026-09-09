"""Static publication includes only the same files the public artifact API served."""
import importlib.util
import json
from pathlib import Path
import tarfile

import pytest

spec=importlib.util.spec_from_file_location('static_export',Path(__file__).parents[1]/'deploy/export-static-demo.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_public_export_preserves_evidence_and_excludes_private_files(tmp_path):
    source=tmp_path/'artifacts';run=source/'run-test';run.mkdir(parents=True)
    record=b'{"id":"run-test","gate":"UNKNOWN"}'
    (run/'run.json').write_bytes(record)
    (run/'geometry.step').write_bytes(b'original STEP bytes')
    (run/'execution.log').write_text('private execution log')
    (run/'.env').write_text('API_KEY=private')
    auth=tmp_path/'auth';auth.mkdir();(auth/'tokens.json').write_text('private token')
    index=tmp_path/'index.json';index.write_text(json.dumps([{'id':'run-test'}]))
    output=tmp_path/'export.tar.gz';first=module.export(source,index,output)
    with tarfile.open(output) as tar:
        names=tar.getnames()
        assert not any('auth' in n or n.endswith(('.env','.log')) for n in names)
        assert tar.extractfile('recorded/runs/run-test.json').read()==record
        assert tar.extractfile('artifacts/run-test/geometry.step').read()==b'original STEP bytes'
        config=json.load(tar.extractfile('recorded/config.json'))
        assert config['read_only'] and config['static_demo'] and not config['astra_ready']
    second=module.export(source,index,output)
    assert first==second


def test_export_rejects_symlink_to_credentials(tmp_path):
    source=tmp_path/'artifacts';run=source/'run-test';run.mkdir(parents=True)
    (run/'run.json').write_text('{"id":"run-test"}')
    secret=tmp_path/'secret.json';secret.write_text('private')
    (run/'leak.json').symlink_to(secret)
    index=tmp_path/'index.json';index.write_text('[{"id":"run-test"}]')
    with pytest.raises(ValueError,match='Symlink'):module.export(source,index,tmp_path/'export.tar.gz')


def test_export_rejects_run_path_traversal(tmp_path):
    index=tmp_path/'index.json';index.write_text('[{"id":"../auth"}]')
    with pytest.raises(ValueError,match='Invalid run ID'):module.export(tmp_path,index,tmp_path/'export.tar.gz')
