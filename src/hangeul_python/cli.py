from __future__ import annotations

import argparse
import code
import codeop
import json
import sys
import types
from pathlib import Path

from . import __version__, compile_source, translate_source
from .diagnostics import format_exception
from .importer import import_context
from .runtime import Runtime
from .lexer import Lexer
from .catalog import Catalog


class Console(code.InteractiveConsole):
    def __init__(self, runtime):
        super().__init__(locals=runtime.prepare({}))
        self.runtime = runtime

    def runsource(self, source, filename="<대화>", symbol="single"):
        try:
            translated = Lexer(source, self.runtime.catalog.replacements, filename).run().translated
            try:
                if codeop.compile_command(translated, filename, symbol) is None:
                    return True
            except SyntaxError:
                pass  # The compiler supplies mapped diagnostics and translated imports.
            compiled = compile_source(source, filename, mode=symbol, runtime=self.runtime)
        except (SyntaxError, OverflowError, ValueError) as error:
            self.write(format_exception(error) + "\n")
            return False
        self.runcode(compiled)
        return False

    def showtraceback(self):
        self.write(format_exception(sys.exception()) + "\n")


def parser():
    result = argparse.ArgumentParser(description="한글로 작성하고 파이썬으로 실행합니다")
    result.add_argument("--version", "--버전", action="version", version=__version__)
    result.add_argument("--profile", "--사전", action="append", default=[],
                        help="추가 API 번역 사전 JSON 파일")
    sub = result.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", aliases=["실행"], help="한글 소스 실행")
    run.add_argument("file", help=".han 또는 .한 소스 파일")
    run.add_argument("args", nargs=argparse.REMAINDER, help="프로그램에 전달할 인자")
    check = sub.add_parser("check", aliases=["검사"], help="실행 없이 문법 검사")
    check.add_argument("files", nargs="+")
    check.add_argument("--json", action="store_true", help="편집기용 JSON 진단")
    translate = sub.add_parser("translate", aliases=["변환"], help="실행 가능한 파이썬으로 변환")
    translate.add_argument("file")
    translate.add_argument("-o", "--output", "--출력", help="생략하면 화면에 출력")
    sub.add_parser("repl", aliases=["대화"], help="대화형 실행")
    dictionary = sub.add_parser("dictionary", aliases=["사전"], help="번역 사전 보기·검증")
    dictionary.add_argument("--validate", "--검증", action="store_true")
    dictionary.add_argument("--json", action="store_true")
    return result


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        catalog = Catalog()
        for profile in args.profile:
            catalog.load_profile(profile)
        runtime = Runtime(catalog)
        command = args.command
        if command in {"dictionary", "사전"}:
            if args.validate:
                problems = runtime.catalog.validate()
                if problems:
                    print("\n".join(problems), file=sys.stderr)
                    return 1
                print("번역 사전 검증 통과")
            elif args.json:
                print(json.dumps({"core": runtime.catalog.core, "api": runtime.catalog.api,
                                  "identifiers": runtime.catalog.identifiers},
                                 ensure_ascii=False, indent=2))
            else:
                for section in ("keywords", "soft_keywords", "builtins", "exceptions", "special_names"):
                    for english, korean in runtime.catalog.core[section].items():
                        print(f"{english:32} {korean}")
                for english, korean in runtime.catalog.identifiers.items():
                    print(f"{english:32} {korean}")
            return 0
        if command in {"repl", "대화"}:
            with import_context(runtime):
                Console(runtime).interact(banner=f"한글 파이썬 {__version__}", exitmsg="종료합니다")
            return 0
        if command in {"check", "검사"}:
            diagnostics = []
            for name in args.files:
                path = Path(name).resolve()
                try:
                    compile_source(path.read_text(encoding="utf-8-sig"), str(path), runtime=runtime)
                except SyntaxError as error:
                    if not args.json:
                        raise
                    diagnostics.append({"file": str(path), "line": error.lineno or 1,
                                        "column": error.offset or 1,
                                        "end_line": error.end_lineno or error.lineno or 1,
                                        "end_column": error.end_offset or error.offset or 1,
                                        "message": format_exception(error)})
                if not args.json:
                    print(f"문법 검사 통과: {name}")
            if args.json:
                print(json.dumps(diagnostics, ensure_ascii=False))
            if diagnostics:
                return 1
            return 0
        path = Path(args.file).resolve()
        source = path.read_text(encoding="utf-8-sig")
        if command in {"translate", "변환"}:
            output = translate_source(source, str(path), catalog=runtime.catalog)
            if args.output:
                Path(args.output).write_text(output, encoding="utf-8")
            else:
                print(output, end="")
            return 0
        module = types.ModuleType("__main__")
        namespace = runtime.prepare(module.__dict__)
        namespace.update({"__file__": str(path), "__package__": None, "__spec__": None})
        old_argv = sys.argv
        old_main = sys.modules.get("__main__")
        sys.modules["__main__"] = module
        sys.argv = [str(path), *args.args]
        try:
            compiled = compile_source(source, str(path), runtime=runtime)
            with import_context(runtime, path.parent):
                exec(compiled, namespace)
        finally:
            sys.argv = old_argv
            if old_main is None:
                sys.modules.pop("__main__", None)
            else:
                sys.modules["__main__"] = old_main
        return 0
    except KeyboardInterrupt:
        print("키보드중단: 실행을 중단했습니다", file=sys.stderr)
        return 130
    except SystemExit:
        raise
    except Exception as error:
        print(format_exception(error), file=sys.stderr)
        return 1
