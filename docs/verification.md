# 0.1.0a1 검증 기록

검증일: 2026-10-16 (Asia/Seoul).

## 로컬

Windows에서 다음을 확인했다.

| 환경 | 결과 |
|---|---|
| CPython 3.13.14 | 62 통과, 1 제외 |
| CPython 3.14.5 | 63 통과 |
| 정적 검사 | ruff 통과 |
| 번역 사전 | 중복·충돌·내장 이름 누락 검사 통과 |
| 자동 생성 문서 | 원본 사전과 일치 |
| 예제 | 기본·클래스·표준 라이브러리·비동기·한글 패키지 실행 |
| NumPy 2.5.4 / pandas 3.0.6 | 통합 시험 통과 |
| Python 배포 | wheel / sdist 생성, 별도 가상환경에 wheel 설치 후 실행 |
| VS Code 확장 | JavaScript 문법 검사, vsce로 VSIX 패키징 |

3.13에서 제외한 항목은 Python 3.14부터 제공하는 t 문자열 시험이다.
VS Code 확장의 실제 GUI·debugpy 전체 통합을 검증했다는 뜻은 아니다.

## 자동 검증

[GitHub Actions](https://github.com/gamparda/hangeul-python/actions/workflows/ci.yml)에서
Windows / Ubuntu와 Python 3.13 / 3.14 조합을 검사한다.
원격 검증 결과는 각 실행의 상태를 기준으로 확인한다.

## 재현

설치된 의존성의 버전은 최신 환경에 따라 달라질 수 있다.

```console
python -m pip install -e ".[dev,data]"
python -m pytest
python -m ruff check .
python tools/generate_reference.py --check
python -m hangeul_python dictionary --validate
python -m build
node --check editors/vscode/extension.js
```

실행 결과 비교 시험 외에도 사용자 한글 속성, descriptor 오류,
함수 인자 충돌, 호출자 스코프, 한글 파일의 실제 오류 위치, 생성된 Python 소스,
한글 패키지와 원래 .py 파일의 우선순위를 확인한다.
