"""한글 파이썬: Korean source, Python semantics."""

from .catalog import Catalog
from .compiler import compile_source, translate_source
from .importer import import_context
from .runtime import Runtime

__version__ = "0.1.0a1"
__all__ = ["Catalog", "Runtime", "compile_source", "translate_source", "run_source"]


def run_source(source: str, namespace: dict | None = None, *, filename="<한글>",
               runtime: Runtime | None = None) -> dict:
    runtime = runtime or Runtime()
    namespace = runtime.prepare({} if namespace is None else namespace)
    code = compile_source(source, filename, runtime=runtime)
    with import_context(runtime):
        exec(code, namespace)
    return namespace
