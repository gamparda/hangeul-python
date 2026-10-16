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
