# VS Code 확장

문법 강조, 번역 사전 자동완성, 함수·조건문 스니펫, 저장 시 문법 검사, 실행 명령을 제공합니다.
이 확장은 아직 Visual Studio Marketplace에 게시하지 않았습니다.

## 설치

[개발판 릴리스](https://github.com/gamparda/hangeul-python/releases/tag/v0.1.0a1)의
VSIX 파일을 받으면 VS Code의 Extensions: Install from VSIX 명령으로 설치할 수 있습니다.

1. 사용하는 Python 3.13 / 3.14에 hangeul-python을 설치합니다.
2. 이 저장소의 editors/vscode 폴더를 VS Code 확장 개발 프로젝트로 엽니다.
3. .vscode/launch.json의 Extension Development Host 구성을 실행합니다.
4. 새 창에서 .han 파일을 열고 사용합니다.

VSIX 패키징 도구가 설치되어 있다면 해당 폴더에서 다음 명령으로 패키징할 수 있습니다.

```console
npx @vscode/vsce package
```

설정 hangeulPython.pythonPath에 패키지를 설치한 Python 실행 파일 경로를 지정합니다.
검사 도구는 그 Python의 hangeul_python 모듈을 사용합니다.
저장하지 않은 파일은 검사하지 않습니다. 자동완성은 자료형을 추론하지 않는 사전 기반입니다.

## 디버깅

별도 Python Debugger 확장이 있는 경우 프로젝트에서 아래 구성을 사용할 수 있습니다.
원본 위치를 제공하지만 모든 debugpy 기능에 대한 호환성 검증은 아직 진행 중입니다.

```json
{
  "name": "한글 파이썬 실행",
  "type": "debugpy",
  "request": "launch",
  "module": "hangeul_python",
  "args": ["run", "${file}"],
  "console": "integratedTerminal",
  "justMyCode": false,
  "env": {"PYTHONUTF8": "1"}
}
```
