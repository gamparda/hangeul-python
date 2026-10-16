# 기여 방법

Python 3.13 또는 3.14에서 저장소를 복제하고 개발 의존성을 설치합니다.

```console
python -m pip install -e ".[dev,data]"
python -m pytest
python -m ruff check .
python tools/generate_reference.py --check
python -m build
```

번역어를 바꿀 때 src/hangeul_python/data/core.json 또는 api.json을 수정하고
tools/generate_reference.py를 실행합니다. 생성된 문서와 자동완성 데이터도 커밋합니다.
tools/expand_catalog.py는 초기 모듈 별칭·API를 관리하는 보조 스크립트입니다.
api.json을 직접 변경했다면 expand_catalog.py가 해당 항목을 덮어쓰지 않는지 확인합니다.

문법·동작을 바꾸면 docs/specification.md와 docs/coverage.md를 갱신합니다.
새 API는 단순한 이름 매핑 확인을 넘어, 실제 객체 정체성·사용자 이름 충돌·인자 전달·
예외 동작 중 변경과 관련된 부분을 검증합니다. 원래 Python 프로그램과의 비교 시험을 권장합니다.

한글 번역 기준:

- 같은 기능은 같은 용어를 우선합니다.
- 함수·메서드는 동작이 드러나는 짧은 표현을 사용합니다.
- 서로 다른 의미를 무리하게 같은 단어에 합치지 않습니다.
- 원문 이름과 원문 문서로 이동할 수 있게 합니다.
- 검토하지 않은 자동 번역 후보를 구현 완료로 표시하지 않습니다.

코드·문서 기여는 MIT 라이선스로 제공합니다.
