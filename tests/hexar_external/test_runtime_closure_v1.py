from pathlib import Path

import pytest

from analysis.hexar_external.acquisition.runtime_closure_v1 import discover
from analysis.hexar_external.acquisition.raw_archive_v1 import digest


def write(root,name,text):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)


def test_relative_package_import_cycle_and_initializer_are_pinned(tmp_path):
    write(tmp_path,'analysis/p/__init__.py','from . import b\n')
    write(tmp_path,'analysis/p/a.py','from .b import value\nimport json\n')
    write(tmp_path,'analysis/p/b.py','from . import a\nvalue=1\n')
    value=discover(tmp_path,['analysis/p/a.py'])
    assert set(value['files'])=={'analysis/p/a.py','analysis/p/b.py','analysis/p/__init__.py'}
    assert value['files']['analysis/p/b.py']==digest(tmp_path/'analysis/p/b.py')
    assert value['stdlib_imports']==['json'] and not value['external_imports']


def test_bank_resolution_precedes_host_for_captured_bank_code(tmp_path):
    write(tmp_path,'bank/a.py','import helper\nimport rclpy\n')
    write(tmp_path,'bank/helper.py','import yaml\n')
    write(tmp_path,'helper.py','raise RuntimeError("wrong host helper")\n')
    value=discover(tmp_path,['bank/a.py'],'bank')
    assert set(value['files'])=={'bank/a.py','bank/helper.py'}
    assert value['external_imports']==['rclpy','yaml']


def test_missing_internal_dependency_fails_closed(tmp_path):
    write(tmp_path,'a.py','import analysis.missing\n')
    with pytest.raises(ValueError,match='missing internal'):discover(tmp_path,['a.py'])


@pytest.mark.parametrize('text',['__import__(name)','import importlib\nimportlib.import_module(name)','exec(code)','eval(code)'])
def test_unknown_dynamic_code_fails_closed(tmp_path,text):
    write(tmp_path,'a.py',text)
    with pytest.raises(ValueError,match='unresolved dynamic'):discover(tmp_path,['a.py'])


def test_constant_dynamic_import_and_nonpython_resource(tmp_path):
    write(tmp_path,'a.py','import importlib\nimportlib.import_module("helper")\n')
    write(tmp_path,'helper.py','pass\n');write(tmp_path,'config.xml','resource bytes')
    value=discover(tmp_path,['a.py','config.xml'])
    assert set(value['files'])=={'a.py','helper.py','config.xml'}


def test_declared_script_search_roots_capture_legacy_local_imports(tmp_path):
    write(tmp_path,'entry.py','import helper\n')
    write(tmp_path,'analysis/helper.py','import json\n')
    value=discover(tmp_path,['entry.py'],module_roots=['analysis'])
    assert set(value['files'])=={'entry.py','analysis/helper.py'}
    assert 'helper' not in value['external_imports']


def test_inventory_mode_preserves_unresolved_site_without_executing_it(tmp_path):
    write(tmp_path,'a.py','exec(code)\n')
    value=discover(tmp_path,['a.py'],allow_unresolved=True)
    assert value['unresolved_dynamic_sites']==['unresolved dynamic execution: a.py:1']


def test_declared_bank_package_relative_import_closes_host_source(tmp_path):
    write(tmp_path,'bank/tool.py','from .helper import value\n')
    write(tmp_path,'analysis/acquisition/helper.py','value=1\n')
    value=discover(tmp_path,['bank/tool.py'],'bank','analysis.acquisition')
    assert set(value['files'])=={'bank/tool.py','analysis/acquisition/helper.py'}


def test_search_root_cannot_escape_project(tmp_path):
    write(tmp_path,'a.py','pass\n')
    with pytest.raises(ValueError):discover(tmp_path,['a.py'],module_roots=['..'])
