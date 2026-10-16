"""Korean lexical translation, Python validation, and API-aware AST lowering."""

from __future__ import annotations

import ast
import linecache

from .catalog import Catalog
from .lexer import Lexer, SourceMap


def helper(name, arguments, location, keywords=None):
    node = ast.Call(func=ast.Name(id=f"__han_{name}__", ctx=ast.Load()),
                    args=arguments, keywords=keywords or [])
    return ast.copy_location(node, location)


class Imports(ast.NodeTransformer):
    def __init__(self, catalog):
        self.catalog = catalog

    def visit_Import(self, node):
        result = []
        for item in node.names:
            canonical = self.catalog.canonical_module(item.name)
            if item.asname:
                alias = item.asname
            elif "." not in canonical:
                alias = item.name if canonical != item.name else None
            else:
                alias = None
            result.append(ast.copy_location(
                ast.Import(names=[ast.alias(name=canonical, asname=alias)]), node))
            if not item.asname and "." in canonical and canonical != item.name:
                result.append(ast.copy_location(ast.Assign(
                    targets=[ast.Name(id=item.name.split(".")[0], ctx=ast.Store())],
                    value=helper("bind_module", [ast.Constant(canonical.split(".")[0])], node),
                ), node))
            if canonical in self.catalog.api["modules"]:
                result.append(ast.copy_location(ast.Expr(value=helper(
                    "bind_module", [ast.Constant(canonical)], node)), node))
        return result

    def visit_ImportFrom(self, node):
        if node.level or node.module is None:
            return node
        canonical = self.catalog.canonical_module(node.module)
        profile = self.catalog.api["modules"].get(canonical, {})
        reverse = {value: key for key, value in profile.get("members", {}).items()}
        names = []
        star = False
        for item in node.names:
            original = reverse.get(item.name, item.name)
            names.append(ast.alias(name=original,
                                   asname=item.asname or (item.name if original != item.name else None)))
            star |= item.name == "*"
        node.module, node.names = canonical, names
        if canonical == "__future__":
            return node
        result = [node]
        if canonical in self.catalog.api["modules"]:
            result.append(ast.copy_location(ast.Expr(value=helper(
                "bind_module", [ast.Constant(canonical)], node)), node))
            if star:
                result.append(ast.copy_location(ast.Expr(value=helper(
                    "import_star", [ast.Constant(canonical),
                                    helper("globals", [], node)], node)), node))
        return result


class APIs(ast.NodeTransformer):
    def __init__(self, catalog):
        self.catalog = catalog
        self.class_depth = 0

    def visit_ClassDef(self, node):
        self.class_depth += 1
        node = self.generic_visit(node)
        self.class_depth -= 1
        return node

    def visit_FunctionDef(self, node):
        if self.class_depth and any(isinstance(child, ast.Name) and child.id == "상위"
                                    for child in ast.walk(node)):
            # CPython's compiler recognizes the English spelling of zero-argument super.
            # A dead reference creates the same __class__ closure for the Korean alias.
            reference = ast.If(test=ast.Constant(False), body=[ast.Expr(
                value=ast.Name(id="__class__", ctx=ast.Load()))], orelse=[])
            ast.copy_location(reference, node)
            insert = 1 if node.body and isinstance(node.body[0], ast.Expr) and isinstance(
                node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str) else 0
            node.body.insert(insert, reference)
        return self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Attribute(self, node):
        self.generic_visit(node)
        if node.attr not in self.catalog.attribute_aliases:
            return node
        if isinstance(node.ctx, ast.Load):
            return helper("getattr", [node.value, ast.Constant(node.attr)], node)
        slot = helper("target", [node.value, ast.Constant(node.attr)], node)
        return ast.copy_location(ast.Attribute(value=slot, attr="value", ctx=node.ctx), node)

    def visit_Call(self, node):
        self.generic_visit(node)
        if any(key.arg is None or key.arg in self.catalog.keyword_aliases for key in node.keywords):
            return helper("call", [node.func, *node.args], node, node.keywords)
        return node


def front_end(source: str, filename: str = "<한글>", mode: str = "exec", *, catalog=None,
              flags=0, optimize=-1):
    catalog = catalog or Catalog()
    source = source.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    mapping = Lexer(source, catalog.replacements, filename).run()
    linecache.cache[filename] = (len(source), None, source.splitlines(keepends=True), filename)
    try:
        # CPython can read filename from disk when constructing SyntaxError, which
        # would combine translated byte offsets with the original Korean line.
        # Parse/validate with a virtual filename, then map to the real source.
        virtual_filename = "<hangeul-python:parse>"
        tree = compile(mapping.translated, virtual_filename, mode, flags=flags | ast.PyCF_ONLY_AST,
                       dont_inherit=True, optimize=optimize)
        tree = Imports(catalog).visit(tree)
        ast.fix_missing_locations(tree)
        # Validate statements that ast.parse accepts, e.g. return outside a function.
        if not flags & ast.PyCF_ONLY_AST:
            compile(tree, virtual_filename, mode, flags=flags, dont_inherit=True, optimize=optimize)
    except SyntaxError as error:
        raise mapping.syntax_error(error, filename) from None
    return tree, mapping


def lower(source: str, filename: str = "<한글>", mode="exec", *, catalog=None,
          flags=0, optimize=-1):
    catalog = catalog or Catalog()
    tree, mapping = front_end(source, filename, mode, catalog=catalog,
                              flags=flags, optimize=optimize)
    tree = APIs(catalog).visit(tree)
    ast.fix_missing_locations(tree)
    remap_locations(tree, mapping)
    return tree


def remap_locations(tree, mapping: SourceMap):
    for node in ast.walk(tree):
        if hasattr(node, "lineno"):
            start = mapping.position(node.lineno, node.col_offset)
            end = mapping.position(node.end_lineno or node.lineno,
                                   node.end_col_offset if node.end_col_offset is not None
                                   else node.col_offset)
            node.lineno, node.col_offset = start
            node.end_lineno, node.end_col_offset = max(start, end)


def compile_source(source: str, filename: str = "<한글>", mode: str = "exec", *, runtime=None,
                   catalog=None, flags: int = 0, optimize: int = -1):
    catalog = runtime.catalog if runtime else catalog or Catalog()
    tree = lower(source, filename, mode, catalog=catalog, flags=flags, optimize=optimize)
    return compile(tree, filename, mode, flags=flags, dont_inherit=True, optimize=optimize)


def translate_source(source: str, filename="<한글>", *, catalog=None) -> str:
    """Export executable Python. The installed hangeul_python runtime is required."""
    catalog = catalog or Catalog()
    tree = lower(source, filename, catalog=catalog)
    bootstrap = ast.parse(
        "from hangeul_python.runtime import export_namespace as __han_export__\n"
        f"globals().update(__han_export__({catalog.overrides!r}))\n"
    ).body
    index = 0
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(
        tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
        index = 1
    while index < len(tree.body) and isinstance(tree.body[index], ast.ImportFrom) and (
        tree.body[index].module == "__future__"
    ):
        index += 1
    remaining = tree.body[index:]
    context = ast.With(items=[ast.withitem(
        context_expr=ast.Call(func=ast.Name(id="__han_import_context__", ctx=ast.Load()),
                              args=[], keywords=[]))], body=remaining or [ast.Pass()])
    tree.body[index:] = [*bootstrap, context]
    ast.fix_missing_locations(tree)
    return "# Generated by hangeul-python; requires hangeul-python.\n" + ast.unparse(tree) + "\n"
