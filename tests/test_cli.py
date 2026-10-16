import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from hangeul_python import Catalog, compile_source, run_source
from hangeul_python.cli import Console
from hangeul_python.runtime import Runtime

ROOT = Path(__file__).resolve().parents[1]


def cli(*args, cwd=None):
    return subprocess.run([sys.executable, "-m", "hangeul_python", *map(str, args)],
                          cwd=cwd or ROOT, env={**os.environ, "PYTHONUTF8": "1"},
                          text=True, encoding="utf-8", capture_output=True)


@pytest.mark.parametrize("example", ["hello", "standard_library", "classes", "async", "module_import"])
def test_examples(example):
    result = cli("run", ROOT / f"examples/{example}.han")
    assert result.returncode == 0, result.stderr
    assert result.stdout


def test_cli_korean_commands_and_json_diagnostics(tmp_path):
    path = tmp_path / "한글.한"
    path.write_text("만약 참\n    통과\n", encoding="utf-8")
    result = cli("검사", path, "--json")
    assert result.returncode == 1
    error = json.loads(result.stdout)[0]
    assert error["line"] == 1 and error["column"] == 5
    assert "콜론" in error["message"]
    path.write_text("출력(3)\n", encoding="utf-8")
    result = cli("실행", path)
    assert result.returncode == 0 and result.stdout.strip() == "3"
    assert cli("사전", "--검증").returncode == 0


def test_cli_arguments_exit_code_main_identity(tmp_path):
    path = tmp_path / "main.han"
    path.write_text(
        '불러오기 시스템\n불러오기 __main__\n값 = 3\n'
        '출력(__main__.값)\n출력(시스템.인자들[1:])\n시스템.종료(7)\n',
        encoding="utf-8",
    )
    result = cli("run", path, "--my-flag", "한글")
    assert result.returncode == 7
    assert "3" in result.stdout and "--my-flag" in result.stdout and "한글" in result.stdout


def test_export_with_custom_profile_and_han_import(tmp_path):
    profile = tmp_path / "extra.json"
    profile.write_text(json.dumps({"schema_version": 1, "modules": {
        "math": {"alias": "계산도구", "members": {"sqrt": "뿌리"}}
    }}), encoding="utf-8")
    (tmp_path / "계산모듈.han").write_text("수 = 4\n", encoding="utf-8")
    source = tmp_path / "main.han"
    source.write_text("불러오기 계산도구\n불러오기 계산모듈\n"
                      "출력(계산도구.뿌리(계산모듈.수))\n", encoding="utf-8")
    output = tmp_path / "generated.py"
    result = cli("--profile", profile, "translate", source, "-o", output)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([sys.executable, str(output)], text=True, encoding="utf-8",
                            env={**os.environ, "PYTHONUTF8": "1"}, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "2.0"


def test_repl_waits_for_complete_multiline_block(capsys):
    console = Console(Runtime())
    assert console.push("함수 f():") is True
    assert console.push("    가 = 2") is True
    assert console.push("    반환 가 + 3") is True
    assert console.push("") is False
    assert console.push("출력(f())") is False
    assert capsys.readouterr().out.strip() == "5"


def test_fstring_named_unicode_escape_raw_and_debug_spec():
    ns = run_source('값 = f"\\N{SNOWMAN} {참}"\n'
                    '원시 = rf"\\N{참}"\n'
                    '디버그 = f"{참 = :>6}"\n')
    assert ns["값"] == "☃ True"
    assert ns["원시"] == "\\NTrue"
    assert ns["디버그"] == "참 =      1"


def test_compile_ast_and_top_level_await():
    tree = compile_source("결과 = 참", flags=ast.PyCF_ONLY_AST)
    assert isinstance(tree, ast.Module)
    code = compile_source("대기 작업()", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    assert code.co_flags & 0x80


@pytest.mark.skipif(sys.version_info < (3, 14), reason="t strings require Python 3.14")
def test_template_strings():
    ns = run_source('값 = t"진리: {참}"')
    assert ns["값"].strings == ("진리: ", "")
    assert ns["값"].interpolations[0].value is True


def test_builtin_module_aliases_and_no_eager_optional_imports():
    ns = run_source("불러오기 내장도구\n결과 = 내장도구.길이([1, 2])\n"
                    '값 = 내장도구.평가("참")')
    assert ns["결과"] == 2 and ns["값"] is True


def test_invalid_profile_is_rolled_back(tmp_path):
    catalog = Catalog()
    old = catalog.api
    path = tmp_path / "bad.json"
    path.write_text('{"schema_version":1,"modules":{"fake":{"alias":"수학"}}}', encoding="utf-8")
    with pytest.raises(ValueError):
        catalog.load_profile(path)
    assert catalog.api is old
    assert catalog.validate() == []


def test_all_repository_json_is_valid():
    for path in ROOT.rglob("*.json"):
        if ".git" in path.parts or "build" in path.parts:
            continue
        json.loads(path.read_text(encoding="utf-8"))
