"""Korean presentation of exceptions, without changing their type or arguments."""

from __future__ import annotations

import linecache
import re
import traceback

from .catalog import Catalog

SYNTAX_MESSAGES = {
    "invalid syntax": "문법이 올바르지 않습니다",
    "expected ':'": "콜론(:)이 필요합니다",
    "unexpected indent": "예상하지 않은 들여쓰기입니다",
    "unindent does not match any outer indentation level": "들여쓰기 깊이가 맞지 않습니다",
    "expected an indented block": "들여쓴 코드 블록이 필요합니다",
    "'return' outside function": "함수 밖에서는 반환할 수 없습니다",
    "'break' outside loop": "반복문 밖에서는 중단할 수 없습니다",
    "'continue' not properly in loop": "반복문 밖에서는 계속할 수 없습니다",
    "unterminated string literal": "문자열의 닫는 따옴표가 없습니다",
    "unterminated triple-quoted string literal": "여러 줄 문자열을 닫아야 합니다",
}


def explanation(error: BaseException) -> str:
    if isinstance(error, SyntaxError):
        for english, korean in SYNTAX_MESSAGES.items():
            if error.msg.startswith(english):
                return korean
        return "문법을 확인해 주세요"
    if isinstance(error, NameError):
        return f"이름 '{error.name}'이 정의되지 않았습니다"
    if isinstance(error, AttributeError):
        return f"객체에 속성 '{error.name}'이 없습니다" if error.name else "속성을 찾지 못했습니다"
    if isinstance(error, ZeroDivisionError):
        return "0으로 나눌 수 없습니다"
    if isinstance(error, IndexError):
        return "색인이 범위를 벗어났습니다"
    if isinstance(error, KeyError):
        return f"키 {error.args[0]!r}가 없습니다" if error.args else "키가 없습니다"
    if isinstance(error, FileNotFoundError):
        return f"파일을 찾을 수 없습니다: {error.filename}"
    if isinstance(error, ModuleNotFoundError):
        return f"모듈 '{error.name}'을 찾을 수 없습니다"
    if isinstance(error, TypeError):
        if match := re.search(r"unexpected keyword argument '([^']+)'", str(error)):
            return f"지원하지 않는 인자 '{match[1]}'가 전달되었습니다"
        return "자료형 또는 함수 인자를 확인해 주세요"
    return str(error)


def format_exception(error: BaseException, *, original: bool = True) -> str:
    catalog = Catalog()
    name = catalog.core["exceptions"].get(type(error).__name__, type(error).__name__)
    result = [f"{name}: {explanation(error)}"]
    if isinstance(error, SyntaxError):
        result.append(f"  {error.filename}:{error.lineno}:{error.offset or 1}")
        text = (error.text or "").rstrip()
        if text:
            result.extend([f"    {text}", "    " + " " * max(0, (error.offset or 1) - 1) + "^"])
    else:
        frames = traceback.extract_tb(error.__traceback__)
        for frame in frames:
            if "/hangeul_python/" in frame.filename.replace("\\", "/"):
                continue
            result.append(f"  {frame.filename}:{frame.lineno} ({frame.name})")
            if text := linecache.getline(frame.filename, frame.lineno).strip():
                result.append(f"    {text}")
    if error.__cause__:
        result.append("원인: " + format_exception(error.__cause__, original=original))
    elif error.__context__ and not error.__suppress_context__:
        result.append("이전 예외: " + format_exception(error.__context__, original=original))
    if isinstance(error, BaseExceptionGroup):
        for index, nested in enumerate(error.exceptions, 1):
            result.append(f"  [{index}] " + format_exception(nested, original=original))
    message = error.msg if isinstance(error, SyntaxError) else str(error)
    if original and message and message != explanation(error):
        result.append(f"  원문: {message}")
    return "\n".join(result)
