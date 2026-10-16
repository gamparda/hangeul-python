# 라이브러리 번역 사전 추가

실행 코드가 없는 JSON으로 모듈·멤버·인자를 등록한다.
같은 모듈 또는 타입 항목을 다시 등록하면 해당 항목을 교체한다.
일부 필드만 덧붙이는 방식이 아니므로 유지할 멤버도 함께 적는다.

```json
{
  "schema_version": 1,
  "modules": {
    "math": {
      "alias": "계산도구",
      "members": {"sqrt": "뿌리"},
      "keywords": {}
    }
  },
  "types": {},
  "builtin_keywords": {}
}
```

```console
hangeul --profile extra.json run example.han
hangeul --profile extra.json translate example.han -o example.py
```

```text
불러오기 계산도구
출력(계산도구.뿌리(16))
```

types의 키는 공개 모듈 경로와 클래스명이다.
members와 keywords는 원문 이름 → 한글 이름으로 작성한다.
keywords 안의 키는 원래 함수·메서드 이름이다.

```json
{
  "schema_version": 1,
  "types": {
    "somepackage.Record": {
      "members": {"save": "저장"},
      "keywords": {"save": {"overwrite": "덮어쓰기"}}
    }
  }
}
```

패키지는 별도로 설치해야 한다. 등록만으로 패키지를 설치하지 않는다.
비공개 구현 클래스 이름보다 공개된 클래스 경로를 사용한다.
번역 사전은 라이브러리의 버전 차이를 자동 해결하지 않으므로 통합 시험을 추가한다.

파이썬 코드에서는 Catalog에 사전을 먼저 적용한 뒤 Runtime을 만든다.

```python
from hangeul_python import Catalog, Runtime, run_source

catalog = Catalog()
catalog.load_profile("extra.json")
runtime = Runtime(catalog)
run_source("불러오기 계산도구\n출력(계산도구.뿌리(16))", runtime=runtime)
```

## 프로젝트의 변수·함수·API 이름

0.1.0a2부터 선택 항목인 identifiers에 원문 식별자 → 한글 이름을 등록할 수 있다.
이 기능은 해당 사전을 적용한 모든 파일에서 이름 토큰을 컴파일 전에 복원한다.
변수, 함수·클래스 선언, import 경로, 속성, 키워드 인자, f 문자열의 표현식에 적용된다.
라이브러리에 넘기는 콜백의 이름·매개변수·형 주석은 원래 Python 이름으로 유지된다.

```json
{
  "schema_version": 1,
  "identifiers": {
    "self": "자신",
    "on_event": "사건수신",
    "payload": "전달자료"
  }
}
```

identifiers는 객체별 API 사전과 달리 파일 전체에 적용한다.
프로젝트에서 서로 다른 Python 이름에 같은 번역어를 줄 수 없으며,
일반 한글 변수에도 등록된 번역어를 다른 뜻으로 사용하지 않는다.
기존 문법·내장 이름과 충돌하거나 기존 API 사전의 다른 뜻과 겹치는 번역어는 거부한다.
동일한 원문을 뜻하는 기존 API 번역어는 함께 사용할 수 있다.
주석·문자열·JSON 키·환경변수·문자열 형 주석은 고치지 않으며,
동적 코드 문자열을 실행하는 경우에는 이 경계를 고려해야 한다.
반사 API의 속성얻기·속성설정 등에는 사전의 번역어를 사용할 수 있다.

--profile 옵션을 run·check·translate·repl 앞에 지정한다.
같은 실행 문맥에서 불러온 .han 모듈과 내보낸 Python 코드에도 사전이 전달된다.
이 기능은 등록한 이름만 번역하며 외부 라이브러리 전체의 번역을 보장하지 않는다.
