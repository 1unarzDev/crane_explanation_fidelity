"""Static acquisition source inventory, never an assertion of full runtime binding.

Tracks host/package and captured source-bank Python imports, package initializers,
constant dynamic imports and every declared bank resource. External modules remain
explicitly unbound until their actual execution environments are qualified.
"""
import argparse
import ast
from pathlib import Path
import sys

from .raw_archive_v1 import digest,read,rooted
from ..confirmatory_v1.journal import exclusive_json


def discover(root,entrypoints,source_bank=None,bank_package=None,module_roots=(),allow_unresolved=False):
    root=Path(root).resolve()
    bank=rooted(root,source_bank) if source_bank else None
    extra_roots=[rooted(root,name) for name in module_roots]
    files={};external=set();edges={};pending=list(entrypoints);unresolved=[]
    def resolve(module,origin):
        rel=Path(*module.split('.'))
        searches=[root,*extra_roots]
        if bank is not None:searches=([bank,*searches] if origin.is_relative_to(bank) else [*searches,bank])
        for search in searches:
            for candidate in (search/rel.with_suffix('.py'),search/rel/'__init__.py'):
                if candidate.is_file():return candidate.resolve()
            if (search/rel).is_dir():return None  # namespace package: no initializer code
        if module.startswith(('analysis.','crane_explanation_fidelity.')):
            raise ValueError('missing internal imported module: '+module)
        external.add(module)
        return None
    while pending:
        path=rooted(root,pending.pop())
        relative=str(path.relative_to(root))
        if relative in files:continue
        files[relative]=digest(path);edges[relative]=[]
        if path.suffix!='.py':continue
        tree=ast.parse(path.read_text(),filename=relative)
        # Freeze any executable package initializers along the host import path.
        parent=path.parent
        while parent!=root and (bank is None or parent!=bank):
            init=parent/'__init__.py'
            if init.is_file() and init!=path:pending.append(str(init.relative_to(root)))
            parent=parent.parent
        for node in ast.walk(tree):
            modules=[]
            if isinstance(node,ast.Import):modules=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                if node.level:
                    if bank is not None and path.is_relative_to(bank):
                        package=(*((bank_package or '').split('.') if bank_package else ()),*path.parent.relative_to(bank).parts)
                    else:package=path.parent.relative_to(root).parts
                    if node.level>len(package):raise ValueError('relative import escapes declared package: '+relative)
                    prefix=package[:len(package)-node.level+1]
                    module='.'.join((*prefix,*(node.module.split('.') if node.module else [])))
                else:module=node.module or ''
                if module:modules.append(module)
                # from package import module can load submodules. Constants and
                # functions are left to the imported parent's own source closure.
                for alias in node.names:
                    if alias.name=='*':continue
                    name='.'.join(filter(None,(module,alias.name)))
                    relmod=Path(*name.split('.'))
                    if any((s/relmod.with_suffix('.py')).is_file() or (s/relmod/'__init__.py').is_file()
                           for s in ([root,bank] if bank else [root])):modules.append(name)
            elif isinstance(node,ast.Call):
                fn=node.func
                dynamic=(isinstance(fn,ast.Name) and fn.id=='__import__') or (
                    isinstance(fn,ast.Attribute) and fn.attr=='import_module')
                if dynamic:
                    if not node.args or not isinstance(node.args[0],ast.Constant) or not isinstance(node.args[0].value,str):
                        issue='unresolved dynamic import: '+relative+':'+str(node.lineno)
                        if not allow_unresolved:raise ValueError(issue)
                        unresolved.append(issue)
                    else:modules=[node.args[0].value]
                if isinstance(fn,ast.Name) and fn.id in ('exec','eval'):
                    issue='unresolved dynamic execution: '+relative+':'+str(node.lineno)
                    if not allow_unresolved:raise ValueError(issue)
                    unresolved.append(issue)
            for module in modules:
                target=resolve(module,path)
                if target is not None:
                    target_name=str(target.relative_to(root));pending.append(target_name)
                    edges[relative].append(target_name)
        edges[relative]=sorted(set(edges[relative]))
    return dict(files=dict(sorted(files.items())),import_edges=dict(sorted(edges.items())),
        unresolved_dynamic_sites=sorted(unresolved),
        stdlib_imports=sorted(m for m in external if m.split('.')[0] in sys.stdlib_module_names),
        external_imports=sorted(m for m in external if m.split('.')[0] not in sys.stdlib_module_names))


def candidate(root,config_path):
    from .raw_acquisition_admission_v1 import CRITICAL_FILES
    root=Path(root).resolve();config=read(rooted(root,config_path));bank=rooted(root,config['source_bank_path'])
    resources={}
    for name,expected in config['source_hashes'].items():
        path=rooted(bank,Path(name).relative_to('analysis/hexar_external/acquisition'))
        if digest(path)!=expected:raise ValueError('captured source bank changed: '+name)
        resources[str(path.relative_to(root))]=expected
    original_manifest='data/hexar_external/audit/source_data_manifest.json'
    original=read(root/original_manifest)
    replay_resources={original_manifest:digest(root/original_manifest)}
    for name in ('component_explain_navigation/component_explain_navigation/component_explainer_impl.py',
                 'skill_explain/skill_explain/skill_impl.py'):
        path=root/'data/hexar_external/upstream'/name
        expected=next(item['sha256'] for item in original['files'] if item['path']==name)
        if digest(path)!=expected:raise ValueError('pinned original callback source changed: '+name)
        replay_resources[str(path.relative_to(root))]=expected
    for name,expected in original['crane_core_hashes'].items():
        if digest(root/name)!=expected:raise ValueError('pinned CRANE core changed: '+name)
        replay_resources[name]=expected
    entries=sorted(set(CRITICAL_FILES)|{str(Path(__file__).relative_to(root))}|set(resources))
    module_roots=['analysis','analysis/hexar_external']
    value=discover(root,entries,config['source_bank_path'],'analysis.hexar_external.acquisition',module_roots,allow_unresolved=True)
    return dict(schema='hexar-acquisition-static-runtime-inventory/v1',
        status='LOCAL_SOURCE_CLOSURE_INVENTORIED_EXTERNAL_RUNTIME_UNBOUND',
        complete_transitive_closure=False,config_sha256=digest(rooted(root,config_path)),
        entrypoints=entries,source_bank_resources=resources,
        hash_checked_ast_replay_resources=replay_resources,
        dynamic_replay_scope='Pinned callback classes use capture-only offline objects. These resource pins do not remove the outstanding dynamic-execution qualification requirement.',
        additional_declared_host_module_roots=module_roots,
        bank_original_package_context='analysis.hexar_external.acquisition',
        bank_relative_import_scope='Conservative original package context; includes functions not executed by the standalone captured reader.',**value,
        limitation='Static source inventory only. Python/stdlib, Docker/OS, ROS/image and provider runtime bindings require qualification; this is not the final scientific runtime_dependencies.json.',
        robot_or_native_dispatches=0,method_or_judge_calls=0,confirmation_authorized=False)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();root=Path(__file__).resolve().parents[3];value=candidate(root,args.config)
    exclusive_json(args.output,value)
    print({k:value[k] for k in ('status','external_imports','unresolved_dynamic_sites','confirmation_authorized')})
