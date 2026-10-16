"""Compare Python and Korean programs independently of individual lowering rules."""

import io
import textwrap
import tokenize

import pytest

from hangeul_python import Catalog, run_source

CASES = [
    """
    result = []
    for i in range(6):
        if i == 1:
            continue
        elif i == 4:
            break
        else:
            result.append(i)
    """,
    """
    result = 0
    i = 0
    while i < 3:
        result += i
        i += 1
    else:
        result += 10
    assert result == 13
    """,
    """
    def f(a, /, b=2, *args, c=3, **kwargs):
        return a + b + sum(args) + c + kwargs['d']
    result = f(1, 2, 3, 4, c=5, **{'d': 6})
    """,
    """
    x = 1
    def outer():
        x = 3
        def inner():
            nonlocal x
            x += 1
            return x
        return inner()
    def change():
        global x
        x += 1
    change()
    result = (outer(), x)
    """,
    """
    def generate():
        yield 1
        yield from range(2, 5)
    result = list(generate())
    """,
    """
    result = []
    try:
        raise ValueError('original user message')
    except ValueError as error:
        result.append(str(error))
    finally:
        result.append('finally')
    """,
    """
    result = []
    try:
        pass
    except Exception:
        result.append(1)
    else:
        result.append(2)
    finally:
        result.append(3)
    """,
    """
    from contextlib import contextmanager
    result = []
    @contextmanager
    def manager():
        result.append('enter')
        try:
            yield 3
        finally:
            result.append('exit')
    with manager() as value:
        result.append(value)
    """,
    """
    result = ([i * i for i in range(5) if i % 2],
              {i for i in range(3)}, {i: i + 1 for i in range(2)},
              tuple(i for i in range(2)))
    """,
    """
    fn = lambda x: x * 2
    values = [0, 1, 2, 3]
    result = (fn(3), values[1:3], (n := 4), True and not False,
              None is None, 2 in values, 8 not in values)
    del values[1]
    """,
    """
    class Value:
        def __init__(self, n):
            self.n = n
        def __add__(self, other):
            return Value(self.n + other.n)
        def __len__(self):
            return self.n
    result = len(Value(3) + Value(4))
    """,
    """
    match {'name': '한글', 'value': 3}:
        case {'name': name, 'value': value} if value > 0:
            result = (name, value)
        case _:
            result = None
    """,
    """
    import asyncio
    class Manager:
        async def __aenter__(self):
            return 4
        async def __aexit__(self, *args):
            pass
    async def generate():
        for n in [1, 2]:
            yield n
    async def main():
        async with Manager() as n:
            values = [i async for i in generate()]
            await asyncio.sleep(0)
            return (n, values)
    result = asyncio.run(main())
    """,
    """
    first, *middle, last = range(5)
    result = (first, middle, last, {'a': 1} | {'b': 2}, 3 if True else 4)
    """,
    """
    import math as m
    from collections import Counter as C
    result = (m.isqrt(17), C('aaba').most_common(1))
    """,
]


def koreanize(python):
    catalog = Catalog()
    mapping = {**catalog.core["keywords"], **catalog.core["soft_keywords"],
               **catalog.core["special_names"]}
    # Here tokenize is intentionally used only on valid, original Python.
    return tokenize.untokenize([
        token._replace(string=mapping.get(token.string, token.string))
        if token.type == tokenize.NAME else token
        for token in tokenize.generate_tokens(io.StringIO(python).readline)
    ])


@pytest.mark.parametrize("python", CASES)
def test_python_equivalence(python):
    source = textwrap.dedent(python)
    expected = {}
    exec(compile(source, "<python>", "exec"), expected)
    actual = run_source(koreanize(source))
    assert actual["result"] == expected["result"]
