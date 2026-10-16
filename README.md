# 한글 파이썬 · Hangeul Python

[![CI](https://github.com/gamparda/hangeul-python/actions/workflows/ci.yml/badge.svg)](https://github.com/gamparda/hangeul-python/actions/workflows/ci.yml)

`만약`, `함수`, `반환`, `출력`으로 작성하고 기존 파이썬 실행기에서 실행하는 언어입니다.
목표는 문법·내장 함수·메서드·라이브러리·오류·개발 도구까지 한국어로 제공하는 것입니다.

**현재 버전: 0.1.0a1 · 초기 개발판 · Python 3.13 / 3.14**

```text
함수 합격자구하기(점수들):
    합격자 = []
    반복 점수 안에 점수들:
        만약 점수 >= 60:
            합격자.추가(점수)
    반환 합격자

결과 = 합격자구하기([45, 80, 95])
출력("합격 인원:", 길이(결과))
출력("점수:", 결과, 구분=" ", 끝="\n")
```

## 시작하기

Python 3.13 또는 3.14 환경에서 설치합니다. 아직 PyPI에는 게시하지 않았습니다.

```console
git clone https://github.com/gamparda/hangeul-python.git
cd hangeul-python
python -m pip install -e .
hangeul run examples/hello.han
```

```text
안녕하세요, 세계!
합격 인원: 2
점수: [80, 95]
```

한국어 명령도 사용할 수 있습니다.

```console
한글파이썬 실행 examples/hello.han
한글파이썬 검사 examples/classes.han
한글파이썬 변환 examples/hello.han --출력 hello.py
한글파이썬 사전 --검증
한글파이썬 대화
```

실행 파일이 PATH에 없으면 `python -m hangeul_python run examples/hello.han`을 사용합니다.
소스 확장자는 `.han`과 `.한`입니다. 들여쓰기·괄호·콜론·연산 기호는 파이썬과 같습니다.

## 라이브러리와 메서드

```text
불러오기 수학
에서 경로도구 불러오기 경로
불러오기 제이슨

출력(수학.제곱근(81))
출력(경로.현재경로().이름)
출력(제이슨.인코딩({"언어": "한글"}, 아스키만=거짓))

값들 = [1, 3, 2]
값들.정렬(역순=참)
출력(값들)
```

목록 리터럴은 실제 `list`이고, 배열은 실제 NumPy 배열입니다.
사용자가 정의한 한글 멤버·인자는 우선하며, 등록된 API에만 번역을 적용합니다.
영문 파이썬 문법·API도 함께 사용할 수 있습니다.

데이터 분석 예제를 실행하려면 다음을 사용합니다.

```console
python -m pip install -e ".[data]"
hangeul run examples/data.han
```

## 현재 지원 범위

| 영역 | 상태 |
|---|---|
| Python 3.13·3.14의 기본 예약어 35개 | 전체 번역 등록, CPython 문법·실행기 활용 |
| 문맥 키워드 match·case·type | 번역 등록 |
| 공개 내장 이름·예외 | 전체 이름 번역 등록, 플랫폼별 이름은 존재할 때 제공 |
| 클래스·상속·생성기·비동기·예외 묶음 | 실행 및 비교 시험 포함 |
| f 문자열·3.14 t 문자열 | 표현식 변환, 원래 문자열 내용 보존 |
| 내장 자료형 메서드·함수 인자·특수 이름 | 사전에 등록된 항목 지원 |
| 표준 라이브러리 | 공개 최상위 모듈 이름의 한글 별칭, 일부 API 번역 |
| NumPy·pandas | 일부 API 어댑터와 통합 시험 |
| 한글 모듈·패키지 | 상대 불러오기, .py 파일과 함께 사용 |
| 동적 코드 | 평가·실행·컴파일, 호출한 코드의 이름공간 활용 |
| 오류 | 한글 분류·주요 설명·원본 위치·원문 정보 |
| VS Code | 문법 강조·사전 자동완성·저장 시 문법 검사·실행 명령 |

**모든 라이브러리 API와 모든 오류 문구의 번역이 완료된 버전은 아닙니다.**
모듈 별칭만 있는 항목은 API 전체 번역으로 계산하지 않습니다.
현재 범위는 [번역 사전](docs/translation-reference.md)과
[지원 현황](docs/coverage.md), 향후 작업은 [개발 계획](docs/roadmap.md)에 기록합니다.

## 문서

- [언어 명세 v0.1](docs/specification.md)
- [자동 생성 번역 사전](docs/translation-reference.md)
- [실행 구조와 설계 결정](docs/architecture.md)
- [지원 현황·호환성 한계](docs/coverage.md)
- [전체 개발 계획과 완료 기준](docs/roadmap.md)
- [라이브러리 번역 사전 추가](docs/profiles.md)
- [VS Code 확장](editors/vscode/README.md)
- [기여 방법](CONTRIBUTING.md)
- [검증 기록](docs/verification.md)

## 개발 및 검증

```console
python -m pip install -e ".[dev,data]"
python -m pytest
python -m ruff check .
python tools/generate_reference.py --check
python -m build
```

일반 파이썬과 대응하는 한글 프로그램의 결과를 비교하고,
이름 충돌·원본 위치·모듈 불러오기·배포 패키지·외부 라이브러리를 검증합니다.
GitHub Actions에서 Windows / Ubuntu × Python 3.13 / 3.14를 검사합니다.

## 선행 사례

[Translatable Python](https://github.com/9th-Floor-Developers/Translatable-Python),
[약속](https://github.com/yaksok/yaksok),
[누리](https://github.com/suhdonghwi/nuri),
[HanPy 연구](https://doi.org/10.20972/kjee.36.2.202506.191)를 조사했습니다.
이 저장소의 실행기는 별도로 작성했으며, 다른 프로젝트 코드를 가져오지 않았습니다.

MIT License.
