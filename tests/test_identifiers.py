import inspect
import json
import subprocess
import sys

import pytest

from hangeul_python import Catalog, Runtime, run_source, translate_source


def make_catalog():
    catalog = Catalog()
    catalog.apply_profile({"schema_version": 1, "identifiers": {
        "self": "자신", "on_event": "사건수신", "Emitter": "사건발생기",
        "value": "받은값", "record": "기록내용", "emit": "사건전달",
        "callback": "처리함수", "events": "사건목록", "payload": "전달내용",
    }})
    return catalog


def test_native_callbacks_parameters_annotations_attributes_and_fstrings():
    catalog = make_catalog()
    ns = run_source('''
클래스 사건발생기:
    함수 __초기화__(자신):
        자신.사건목록 = []
    함수 사건전달(자신, 처리함수, *, 전달내용):
        자신.사건목록.추가(처리함수(받은값=전달내용))
함수 사건수신(받은값: 정수) -> 문자열:
    기록내용 = f"payload={받은값}"
    반환 기록내용
발생기 = 사건발생기()
발생기.사건전달(사건수신, 전달내용=3)
''', runtime=Runtime(catalog))
    callback = ns["on_event"]
    assert callback.__name__ == "on_event"
    assert list(inspect.signature(callback).parameters) == ["value"]
    assert callback(value=4) == "payload=4"
    assert ns["발생기"].events == ["payload=3"]
    assert ns["Emitter"].__init__.__name__ == "__init__"


def test_imports_literals_comments_reflection_and_english_can_mix():
    catalog = Catalog()
    catalog.apply_profile({"schema_version": 1, "identifiers": {
        "json": "자료교환도구", "dumps": "자료직렬화", "ensure_ascii": "영문탈출",
    }})
    ns = run_source('''
불러오기 자료교환도구
# json.dumps and ensure_ascii stay unchanged in this comment.
결과 = 자료교환도구.자료직렬화({"ensure_ascii": "한글"}, 영문탈출=거짓)
원문 = 자료교환도구.dumps({"x": 1})
반사 = 속성얻기(자료교환도구, "자료직렬화")({"x": 2})
''', runtime=Runtime(catalog))
    assert ns["결과"] == '{"ensure_ascii": "한글"}'
    assert ns["원문"] == '{"x": 1}' and ns["반사"] == '{"x": 2}'


@pytest.mark.parametrize("mapping", [
    {"first": "중복이름", "second": "중복이름"},
    {"first": "만약"}, {"first": "출력"}, {"first": "추가"},
    {"first": "__han_internal"}, {"bad.name": "안됨"},
    {"first": "두 단어"}, {"first": "ｘ"}, {"first": None},
    {"if": "조건문"}, {"first": "if"},
])
def test_invalid_identifier_profiles_roll_back(mapping):
    catalog = make_catalog()
    previous = dict(catalog.replacements)
    overrides = json.dumps(catalog.overrides)
    with pytest.raises(ValueError):
        catalog.apply_profile({"schema_version": 1, "identifiers": mapping})
    assert catalog.replacements == previous
    assert json.dumps(catalog.overrides) == overrides
    assert catalog.validate() == []


def test_malformed_identifier_section_rolls_back():
    catalog = make_catalog()
    previous = dict(catalog.replacements)
    with pytest.raises(ValueError):
        catalog.apply_profile({"schema_version": 1, "identifiers": []})
    assert catalog.replacements == previous


def test_matching_existing_api_aliases_and_later_conflicts():
    catalog = Catalog()
    catalog.apply_profile({"schema_version": 1, "identifiers": {
        "getLogger": "기록기얻기", "logging": "기록도구",
    }})
    ns = run_source('불러오기 기록도구\n결과 = 기록도구.기록기얻기("identifier-test")\n',
                    runtime=Runtime(catalog))
    assert ns["결과"].name == "identifier-test" and ns["logging"].__name__ == "logging"
    previous = dict(catalog.replacements)
    with pytest.raises(ValueError, match="충돌"):
        catalog.apply_profile({"schema_version": 1, "modules": {
            "othermodule": {"alias": "추가모듈", "members": {"other": "기록기얻기"}},
        }})
    assert catalog.replacements == previous
    assert "othermodule" not in catalog.api["modules"]


def test_export_and_cli_imported_modules_share_identifier_profile(tmp_path):
    catalog = make_catalog()
    profile = tmp_path / "names.json"
    profile.write_text(json.dumps(catalog.overrides), encoding="utf-8")
    module = tmp_path / "helper.han"
    module.write_text("함수 사건수신(받은값):\n    반환 받은값 + 1\n", encoding="utf-8")
    source = "에서 helper 불러오기 사건수신\n출력(사건수신(받은값=2))\n"
    path = tmp_path / "main.han"
    path.write_text(source, encoding="utf-8")
    exported = tmp_path / "generated.py"
    exported.write_text(translate_source(source, str(path), catalog=catalog), encoding="utf-8")
    for args in (
        ["-m", "hangeul_python", "--profile", str(profile), "run", str(path)],
        [str(exported)],
    ):
        result = subprocess.run([sys.executable, *args], cwd=tmp_path,
                                capture_output=True, text=True, encoding="utf-8")
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "3"
