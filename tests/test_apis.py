import sys
import textwrap

import pytest

from hangeul_python import Runtime, run_source


def run(source, namespace=None):
    return run_source(textwrap.dedent(source), namespace)


def test_builtin_keywords_and_shadowing(capsys):
    ns = run("""
        출력(1, 2, 구분="|", 끝="!")
        결과 = 정렬([1, 3, 2], 역순=참)
        함수 출력(값, 끝):
            반환 값 + 끝
        사용자 = 출력(1, 끝=2)
    """)
    assert capsys.readouterr().out == "1|2!"
    assert ns["결과"] == [3, 2, 1] and ns["사용자"] == 3


def test_keyword_expansion_and_duplicate_translation():
    ns = run("""
        옵션 = {"역순": 참}
        결과 = 정렬([1, 3, 2], **옵션)
    """)
    assert ns["결과"] == [3, 2, 1]
    with pytest.raises(TypeError, match="두 번"):
        run('결과 = 정렬([1], reverse=참, 역순=참)')


def test_methods_static_methods_and_literals():
    ns = run("""
        값 = [3, 1, 2]
        값.정렬(역순=참)
        값.추가(4)
        문자값 = " 가 나 ".공백제거().나누기(구분=" ")
        결합 = "-".이어붙이기(문자값)
        사전값 = 사전.키로만들기(["가", "나"], 3)
        숫자 = (15).비트길이()
        변환 = 정수.바이트에서(b"\\x01", 바이트순서="big")
        고정 = 고정집합({1, 2}).합집합({3})
    """)
    assert ns["값"] == [3, 2, 1, 4]
    assert ns["문자값"] == ["가", "나"] and ns["결합"] == "가-나"
    assert ns["사전값"] == {"가": 3, "나": 3}
    assert ns["숫자"] == 4 and ns["변환"] == 1
    assert ns["고정"] == {1, 2, 3}


def test_user_attributes_and_keyword_names_win():
    ns = run("""
        클래스 사용자:
            함수 추가(자신, 값, 끝=0):
                반환 값 + 끝
        클래스 사용자목록(목록):
            함수 추가(자신, 값):
                자신.append(값 * 2)
        결과 = 사용자().추가(1, 끝=2)
        값 = 사용자목록()
        값.추가(3)
    """)
    assert ns["결과"] == 3 and ns["값"] == [6]


def test_attribute_assignment_augassign_delete_and_single_evaluation():
    ns = run("""
        호출들 = []
        클래스 사용자:
            값 = 1
        대상 = 사용자()
        함수 가져오기():
            호출들.추가(1)
            반환 대상
        가져오기().값 += 2
        대상.이름 = "한글"
        복사 = 대상.이름
        삭제 대상.이름
    """)
    assert ns["대상"].값 == 3 and ns["호출들"] == [1]
    assert ns["복사"] == "한글" and not hasattr(ns["대상"], "이름")


def test_descriptor_attribute_error_is_not_swallowed():
    with pytest.raises(AttributeError, match="사용자속성오류"):
        run("""
            클래스 사용자(목록):
                @속성
                함수 추가(자신):
                    발생 속성오류("사용자속성오류")
            사용자().추가
        """)


def test_imports_modules_submodules_and_star():
    ns = run("""
        불러오기 수학
        에서 수학 불러오기 제곱근 별칭 뿌리
        에서 수학 불러오기 *
        불러오기 운영체제.경로
        불러오기 제이슨 별칭 자료형식
        결과 = 수학.제곱근(81) + 뿌리(16) + 정수제곱근(9)
        경로값 = 운영체제.경로.합치기("가", "나")
        글 = 자료형식.인코딩({"한": 1}, 아스키만=거짓)
    """)
    assert ns["결과"] == 16
    assert "가" in ns["경로값"] and "한" in ns["글"]


def test_pathlib_file_io_and_context_manager(tmp_path):
    ns = run("""
        에서 경로도구 불러오기 경로
        파일 = 경로(위치) / "한글.txt"
        파일.문자열쓰기("안녕하세요", 인코딩="utf-8")
        읽은값 = 파일.문자열읽기(인코딩="utf-8")
        함께 열기(파일, 인코딩="utf-8") 별칭 입력파일:
            다시읽기 = 입력파일.읽기()
        파일명 = 파일.이름
    """, {"위치": str(tmp_path)})
    assert ns["읽은값"] == ns["다시읽기"] == "안녕하세요"
    assert ns["파일명"] == "한글.txt"


def test_datetime_collections_and_dataclass():
    ns = run("""
        에서 날짜시간 불러오기 날짜, 시간차
        에서 자료모음 불러오기 계수기
        에서 자료클래스 불러오기 자료형정의
        @자료형정의(동결=참)
        클래스 점:
            가로: 정수
            세로: 정수
        결과 = 날짜(2026, 10, 16).연도
        초 = 시간차(일수=1).전체초()
        빈도 = 계수기("가가나").빈도순(1)
        위치 = 점(1, 2)
    """)
    assert ns["결과"] == 2026 and ns["초"] == 86400
    assert ns["빈도"] == [("가", 2)]
    assert ns["위치"].가로 == 1


def test_dynamic_code_and_caller_scope():
    ns = run("""
        함수 계산():
            수 = 5
            평가값 = 평가("수 + 2")
            지역값 = 지역변수()
            확장지역값 = 지역변수(**{})
            반환 평가값, 지역값["수"], 확장지역값["수"]
        결과 = 계산()
        공간 = {}
        실행("값 = []\\n값.추가(3)", 전역공간=공간)
        코드 = 컴파일("반환값 = 참", "<동적>", "exec")
        실행(코드, 공간)
    """)
    assert ns["결과"] == (7, 5, 5)
    assert ns["공간"]["값"] == [3] and ns["공간"]["반환값"] is True


def test_reflection_uses_korean_member_and_special_names():
    ns = run("""
        값 = []
        속성얻기(값, "추가")(3)
        있나 = 속성있음(값, "추가")
        이름들 = 속성목록(값)
        길이함수 = 속성얻기(값, "__길이__")
        결과 = 길이함수()
    """)
    assert ns["값"] == [3] and ns["있나"] and ns["결과"] == 1
    assert "추가" in ns["이름들"]


def test_async_await_async_generator_and_context():
    ns = run("""
        불러오기 비동기도구
        비동기 함수 생성():
            산출 1
            산출 2
        비동기 함수 시작():
            대기 비동기도구.잠시대기(0)
            반환 [수 비동기 반복 수 안에 생성()]
        결과 = 비동기도구.실행(시작())
    """)
    assert ns["결과"] == [1, 2]


def test_numpy_pandas_adapters_keep_native_objects():
    np = pytest.importorskip("numpy")
    pd = pytest.importorskip("pandas")
    ns = run("""
        불러오기 넘파이
        불러오기 판다스
        배열값 = 넘파이.배열([1, 2, 3], 자료형=넘파이.정수64)
        평균값 = 배열값.평균()
        표 = 판다스.자료표(자료={"점수": [80, 95]})
        첫점수 = 표.값정렬(기준="점수", 오름차순=거짓).앞부분(개수=1)
        열 = 표["점수"]
        합 = 열.합계()
    """)
    assert isinstance(ns["배열값"], np.ndarray)
    assert isinstance(ns["표"], pd.DataFrame)
    assert ns["평균값"] == 2 and ns["합"] == 175
    assert ns["첫점수"]["점수"].iloc[0] == 95


def test_custom_callable_equality_is_never_invoked():
    class Callable:
        def __eq__(self, other):
            raise AssertionError("call dispatch must not use equality")

        def __call__(self, **kwargs):
            return kwargs

    ns = run('결과 = 호출(끝=3)', {"호출": Callable()})
    assert ns["결과"] == {"끝": 3}


def test_no_builtin_monkeypatch():
    import builtins
    before = set(vars(builtins))
    run("값 = []\n값.추가(1)")
    assert set(vars(builtins)) == before
    assert not hasattr(list, "추가")


def test_profile_extension(tmp_path):
    profile = tmp_path / "extra.json"
    profile.write_text('{"schema_version":1,"modules":{"math":{"alias":"계산도구",'
                       '"members":{"sqrt":"뿌리"}}}}', encoding="utf-8")
    runtime = Runtime()
    runtime.catalog.load_profile(profile)
    ns = run_source("불러오기 계산도구\n결과 = 계산도구.뿌리(16)", runtime=runtime)
    assert ns["결과"] == 4


def test_han_package_relative_import_and_py_precedence(tmp_path, monkeypatch):
    package = tmp_path / "한글시험패키지"
    package.mkdir()
    (package / "__init__.han").write_text("에서 .도구 불러오기 두배\n", encoding="utf-8")
    (package / "도구.한").write_text("함수 두배(수):\n    반환 수 * 2\n", encoding="utf-8")
    (tmp_path / "우선순위.py").write_text("값 = 1\n", encoding="utf-8")
    (tmp_path / "우선순위.han").write_text("값 = 2\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        ns = run("불러오기 한글시험패키지\n불러오기 우선순위\n결과 = 한글시험패키지.두배(4)")
        assert ns["결과"] == 8 and ns["우선순위"].값 == 1
    finally:
        for name in ["한글시험패키지", "한글시험패키지.도구", "우선순위"]:
            sys.modules.pop(name, None)
