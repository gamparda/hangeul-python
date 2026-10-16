"""Import .han and .한 modules and packages alongside ordinary .py modules."""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path

from .compiler import compile_source


class HanLoader(importlib.abc.Loader):
    def __init__(self, path: Path, runtime):
        self.path, self.runtime = path, runtime

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        module.__file__ = str(self.path)
        self.runtime.prepare(module.__dict__)
        source = self.path.read_text(encoding="utf-8-sig")
        code = compile_source(source, str(self.path), runtime=self.runtime)
        exec(code, module.__dict__)


class HanFinder(importlib.abc.MetaPathFinder):
    def __init__(self, runtime):
        self.runtime = runtime

    def find_spec(self, fullname, path=None, target=None):
        # An ordinary Python module/package always keeps Python's normal precedence.
        ordinary = importlib.machinery.PathFinder.find_spec(fullname, path)
        if ordinary is not None and ordinary.loader is not None:
            return None
        name = fullname.rsplit(".", 1)[-1]
        for entry in path if path is not None else sys.path:
            root = Path(entry or ".")
            for extension in (".han", ".한"):
                package = root / name / ("__init__" + extension)
                if package.is_file():
                    return importlib.util.spec_from_file_location(
                        fullname, package, loader=HanLoader(package, self.runtime),
                        submodule_search_locations=[str(package.parent)],
                    )
                module = root / (name + extension)
                if module.is_file():
                    return importlib.util.spec_from_file_location(
                        fullname, module, loader=HanLoader(module, self.runtime),
                    )
        return None


@contextmanager
def import_context(runtime, directory=None):
    finder = HanFinder(runtime)
    index = next((i for i, item in enumerate(sys.meta_path)
                  if item is importlib.machinery.PathFinder), len(sys.meta_path))
    sys.meta_path.insert(index, finder)
    path_entry = str(Path(directory).resolve()) if directory else None
    if path_entry:
        sys.path.insert(0, path_entry)
    try:
        yield
    finally:
        sys.meta_path.remove(finder)
        if path_entry:
            sys.path.remove(path_entry)
