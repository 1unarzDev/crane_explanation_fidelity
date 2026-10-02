"""Audit local static Python import closure for evaluator-only declarations."""
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def source_closure(seeds):
    pending=[Path(__file__), *map(Path,seeds)];seen=set()
    while pending:
        path=pending.pop().resolve()
        if path in seen:continue
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError('runtime source outside study checkout or missing')
        seen.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            names=([node.module.split('.')[0]] if isinstance(node,ast.ImportFrom) and node.module
                else [item.name.split('.')[0] for item in node.names] if isinstance(node,ast.Import) else [])
            for name in names:
                dependency=ROOT/'analysis'/(name+'.py')
                if dependency.is_file() and dependency.resolve() not in seen:pending.append(dependency)
    return sorted(seen)
