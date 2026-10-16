import ast
import builtins
import keyword
import textwrap
import traceback

import pytest

from hangeul_python import Catalog, compile_source, run_source, translate_source
from hangeul_python.diagnostics import format_exception


def run(source, namespace=None):
    return run_source(textwrap.dedent(source), namespace)


def test_complete_core_dictionary():
    catalog = Catalog()
    assert catalog.validate() == []
    assert set(keyword.kwlist) == set(catalog.core["keywords"])
    assert set(keyword.softkwlist) - {"_"} == set(catalog.core["soft_keywords"])
    for name in dir(builtins):
        if name.startswith("_") or name in keyword.kwlist:
            continue
        assert name in catalog.core["builtins"] or name in catalog.core["exceptions"]


def test_control_flow_and_comprehensions():
    ns = run("""
        함수 분류(수):
            만약 수 < 0:
                반환 "음수"
            아니고만약 수 == 0:
                반환 "영"
            아니면:
                반환 "양수"
        결과 = [분류(수) 반복 수 안에 [-1, 0, 1]]
        제곱들 = {수: 수 * 수 반복 수 안에 범위(5) 만약 수 % 2 == 0}
        모음 = {수 반복 수 안에 범위(3)}
        수 = 0
        동안 참:
            수 += 1
            만약 수 == 2:
                계속
            만약 수 == 4:
                중단
        단언 수 == 4 그리고 아님 거짓
        동일성 = 없음 동일 None
        대안 = 거짓 또는 참
    """)
    assert ns["결과"] == ["음수", "영", "양수"]
    assert ns["제곱들"] == {0: 0, 2: 4, 4: 16}
    assert ns["모음"] == {0, 1, 2}
    assert ns["동일성"] and ns["대안"]


def test_scope_generators_lambda_walrus_and_loop_else():
    ns = run("""
        값 = 1
        함수 바깥():
            지역 = 2
            함수 안쪽():
                비지역 지역
                전역 값
                지역 += 1
                값 += 2
                반환 지역
            반환 안쪽()
        결과 = 바깥()
        함수 생성():
            산출 1
            산출 에서 [2, 3]
        생성값 = 목록(생성())
        두배 = 익명함수 수: 수 * 2
        표현식 = (대입 := 두배(3))
        반복 수 안에 []:
            통과
        아니면:
            완료 = 참
        삭제 대입
    """)
    assert ns["값"] == 3 and ns["결과"] == 3
    assert ns["생성값"] == [1, 2, 3]
    assert ns["표현식"] == 6 and ns["완료"]
    assert "대입" not in ns


def test_exception_groups_and_finally():
    ns = run("""
        기록 = []
        시도:
            발생 예외묶음("묶음", [값오류("값"), 자료형오류("형")])
        예외* 값오류 별칭 오류:
            기록.추가("값")
        예외* 자료형오류:
            기록.추가("형")
        마지막:
            기록.추가("끝")
    """)
    assert ns["기록"] == ["값", "형", "끝"]


def test_match_type_alias_and_annotations():
    ns = run("""
        형별칭 숫자목록 = 목록[정수]
        함수 판별(값: 정수) -> 문자열:
            맞춤 값:
                경우 1 | 2:
                    반환 "작음"
                경우 _:
                    반환 "큼"
        결과 = 판별(2)
    """)
    assert ns["결과"] == "작음"
    assert ns["숫자목록"].__value__ == list[int]


def test_decorators_dunders_super_and_native_types():
    ns = run("""
        클래스 기반:
            함수 값(자신):
                반환 3
        클래스 자식(기반):
            함수 __초기화__(자신, 수):
                자신.수 = 수
            함수 값(자신):
                반환 상위().값() + 자신.수
            함수 __길이__(자신):
                반환 자신.수
            @정적메서드
            함수 더하기(가, 나):
                반환 가 + 나
        인스턴스 = 자식(4)
        결과 = 인스턴스.값()
        크기 = 길이(인스턴스)
        확인 = 자료형([]) 동일 목록
    """)
    assert ns["결과"] == 7 and ns["크기"] == 4 and ns["확인"]
    assert ns["자식"].더하기(2, 3) == 5


@pytest.mark.parametrize("source", [
    '반환 1', '중단', '계속', '불러오기 수학\n에서 __미래__ 불러오기 주석',
    '함수 f():\n    에서 수학 불러오기 *',
])
def test_python_context_errors_are_rejected(source):
    with pytest.raises(SyntaxError):
        compile_source(source)


def test_strings_comments_fstrings_and_debug_labels():
    ns = run("""
        # 만약, 함수, 참 are just comments.
        글 = "만약 함수 참"
        원시 = r"함수\\n참"
        여러줄 = '''만약
        함수'''
        값 = f"{{만약}} {참} {1 만약 참 아니면 0}"
        중첩 = f"{f'{참}'}"
        너비 = 5
        서식값 = f"{42:>{너비}}"
        디버그 = f"{참=}"
        비교 = f"{1 != 2}"
    """)
    assert ns["글"] == "만약 함수 참"
    assert ns["원시"] == r"함수\n참"
    assert "함수" in ns["여러줄"]
    assert ns["값"] == "{만약} True 1"
    assert ns["중첩"] == "True"
    assert ns["서식값"] == "   42"
    assert ns["디버그"] == "참=True"
    assert ns["비교"] == "True"


def test_pep701_same_quote_and_comments():
    ns = run('''
        값 = {"키": 3}
        결과 = f"{값["키"]} {(
            참 # 만약
        )}"
    ''')
    assert ns["결과"] == "3 True"


def test_reserved_helpers():
    with pytest.raises(SyntaxError, match="예약"):
        compile_source("__han_call__ = 1")


def test_source_locations_and_korean_diagnostic():
    source = "함수 확인():\n    반환 1 / 0\n확인()\n"
    with pytest.raises(ZeroDivisionError) as info:
        run_source(source, filename="<위치검사>")
    frames = traceback.extract_tb(info.value.__traceback__)
    assert frames[-1].lineno == 2
    assert frames[-1].line.strip() == "반환 1 / 0"
    assert "영나눗셈오류" in format_exception(info.value)
    with pytest.raises(SyntaxError) as info:
        compile_source("만약 참\n    통과\n", filename="<문법위치>")
    assert info.value.lineno == 1
    assert info.value.text.strip() == "만약 참"
    assert info.value.offset == 5


def test_exported_python_executes_and_future_stays_first():
    source = '에서 __미래__ 불러오기 주석\n값 = []\n값.추가(3)\n'
    output = translate_source(source)
    tree = ast.parse(output)
    assert tree.body[0].module == "__future__"
    ns = {}
    exec(compile(output, "<export>", "exec"), ns)
    assert ns["값"] == [3]
