"""Maintain explicit Korean aliases for public stdlib module names. No imports of targets."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "src/hangeul_python/data/api.json"

ALIASES = """
abc 추상기반
annotationlib 주석해석
antigravity 반중력
argparse 인자해석
array 배열도구
ast 구문트리
atexit 종료처리
base64 육십사진법
bdb 기본디버거
binascii 이진아스키
builtins 내장도구
bz2 비지압축
cProfile 시프로파일
calendar 달력
cmath 복소수학
cmd 명령셸
code 대화코드
codecs 인코딩도구
codeop 코드완성판정
colorsys 색상변환
compileall 전체컴파일
compression 압축도구
compression.zstd 압축도구.제트표준
concurrent 동시실행
concurrent.futures 동시실행.미래결과
configparser 설정해석
contextlib 문맥도구
contextvars 문맥변수
copyreg 복사등록
ctypes 시자료형
curses 터미널화면
dbm 단순데이터베이스
difflib 차이비교
dis 바이트코드해석
doctest 문서시험
email 전자우편
encodings 인코딩모음
ensurepip 패키지도구설치
errno 오류번호
faulthandler 장애처리
fcntl 파일제어
filecmp 파일비교
fileinput 파일입력
fnmatch 파일명일치
ftplib 파일전송
gc 메모리수거
genericpath 공통경로
getopt 옵션얻기
getpass 암호입력
gettext 다국어문구
glob 경로패턴
graphlib 그래프도구
grp 그룹정보
gzip 지집압축
hashlib 해시도구
hmac 메시지인증
html 하이퍼문서
http 웹통신
http.client 웹통신.클라이언트
http.server 웹통신.서버
idlelib 아이들편집기
imaplib 우편접근
importlib 모듈적재
inspect 코드조사
ipaddress 인터넷주소
keyword 예약어도구
linecache 줄캐시
locale 지역설정
logging 기록도구
lzma 엘지엠에이압축
mailbox 우편함
marshal 내부직렬화
mimetypes 매체유형
mmap 메모리매핑
modulefinder 모듈찾기
msvcrt 윈도우시실행기
multiprocessing 다중프로세스
netrc 네트워크인증정보
nt 윈도우내부
ntpath 윈도우경로도구
nturl2path 윈도우주소경로
numbers 수치기반
opcode 명령코드
optparse 구형옵션해석
pdb 파이썬디버거
pickle 객체직렬화
pickletools 직렬화조사
pkgutil 패키지도구
platform 실행환경
plistlib 속성목록파일
poplib 우편받기
posix 포직스내부
posixpath 포직스경로도구
pprint 보기좋은출력
profile 성능분석
pstats 성능통계
pty 가상터미널
pwd 사용자정보
py_compile 파일컴파일
pyclbr 클래스찾기
pydoc 파이썬문서
pydoc_data 파이썬문서자료
pyexpat 엑스엠엘내부해석
queue 대기열도구
quopri 인용인코딩
readline 입력줄편집
reprlib 축약표현
resource 자원관리
rlcompleter 입력자동완성
runpy 모듈실행
sched 예약실행
secrets 보안난수
select 입출력선택
selectors 입출력선택도구
shelve 객체저장소
shlex 셸문법해석
shutil 파일작업
signal 신호처리
site 설치환경
smtplib 우편보내기
socket 소켓
socketserver 소켓서버
sqlite3 경량데이터베이스
sre_compile 구형정규식컴파일
sre_constants 구형정규식상수
sre_parse 구형정규식해석
ssl 보안통신
stat 파일상태
string 문자열도구
stringprep 문자열준비
struct 이진구조
subprocess 하위프로세스
symtable 기호표
sysconfig 파이썬설정
syslog 시스템기록
tabnanny 들여쓰기검사
tarfile 타르파일
tempfile 임시파일
termios 터미널입출력
textwrap 글줄정리
this 파이썬철학
threading 스레드
timeit 시간측정
tkinter 티케이화면
token 토큰
tokenize 토큰분석
tomllib 톰엘
trace 실행추적
traceback 오류추적
tracemalloc 메모리추적
tty 터미널모드
turtle 거북이
turtledemo 거북이예제
types 형도구
unicodedata 유니코드자료
unittest 단위시험
urllib 주소도구
urllib.request 주소도구.요청
urllib.parse 주소도구.해석
urllib.error 주소도구.오류
uuid 고유식별자
venv 가상환경
warnings 경고도구
wave 음성파일
weakref 약한참조
webbrowser 웹브라우저
winreg 윈도우레지스트리
winsound 윈도우소리
wsgiref 웹서버규약
xml 엑스엠엘
xml.etree.ElementTree 엑스엠엘.원소트리
xmlrpc 엑스엠엘원격호출
zipapp 압축앱
zipfile 집파일
zipimport 압축불러오기
zlib 제트압축
zoneinfo 시간대정보
"""

# Only maintained API translations are marked implemented. Module aliases alone
# intentionally do not imply that a whole module's public API has been translated.
MEMBERS = {
    "contextlib": {"contextmanager": "문맥관리자", "asynccontextmanager": "비동기문맥관리자",
                   "suppress": "억제", "nullcontext": "빈문맥", "closing": "닫기보장",
                   "redirect_stdout": "표준출력전환", "ExitStack": "종료스택"},
    "argparse": {"ArgumentParser": "인자해석기", "Namespace": "이름공간"},
    "logging": {"debug": "디버그", "info": "정보", "warning": "경고", "error": "오류",
                "exception": "예외기록", "critical": "치명적", "getLogger": "기록기얻기",
                "basicConfig": "기본설정", "DEBUG": "디버그수준", "INFO": "정보수준"},
    "tempfile": {"TemporaryDirectory": "임시디렉터리", "NamedTemporaryFile": "이름있는임시파일",
                 "TemporaryFile": "임시파일", "gettempdir": "임시경로"},
    "shutil": {"copy": "복사", "copy2": "정보포함복사", "copytree": "디렉터리복사",
               "move": "이동", "rmtree": "디렉터리삭제", "which": "실행파일찾기",
               "make_archive": "압축만들기", "unpack_archive": "압축풀기"},
    "pickle": {"dump": "쓰기", "dumps": "직렬화", "load": "읽기", "loads": "역직렬화"},
    "hashlib": {"sha256": "샤256", "sha512": "샤512", "md5": "엠디5", "new": "만들기"},
    "secrets": {"choice": "고르기", "randbelow": "미만난수", "token_hex": "십육진토큰",
                "token_urlsafe": "주소안전토큰", "compare_digest": "상수시간비교"},
    "socket": {"socket": "소켓", "create_connection": "연결만들기",
               "gethostname": "호스트명", "AF_INET": "인터넷주소형", "SOCK_STREAM": "흐름형"},
    "subprocess": {"run": "실행", "Popen": "프로세스열기", "PIPE": "파이프",
                   "DEVNULL": "버리기", "CalledProcessError": "프로세스실패오류"},
    "urllib.request": {"urlopen": "주소열기", "Request": "요청", "urlretrieve": "내려받기"},
    "urllib.parse": {"urlparse": "주소해석", "urlencode": "질의인코딩",
                     "quote": "인코딩", "unquote": "해독", "urljoin": "주소합치기"},
    "tomllib": {"load": "읽기", "loads": "해독", "TOMLDecodeError": "해독오류"},
    "uuid": {"uuid4": "무작위식별자", "UUID": "식별자"},
    "zoneinfo": {"ZoneInfo": "시간대", "available_timezones": "시간대목록"},
    "threading": {"Thread": "스레드", "Lock": "잠금", "Event": "이벤트",
                  "current_thread": "현재스레드"},
    "queue": {"Queue": "대기열", "PriorityQueue": "우선대기열", "Empty": "비어있음오류"},
    "concurrent.futures": {"ThreadPoolExecutor": "스레드풀", "ProcessPoolExecutor": "프로세스풀",
                           "as_completed": "완료순", "wait": "대기"},
    "sqlite3": {"connect": "연결", "Connection": "연결형", "Row": "행"},
    "zipfile": {"ZipFile": "집파일", "is_zipfile": "집파일여부"},
    "tarfile": {"open": "열기", "is_tarfile": "타르파일여부"},
    "gzip": {"open": "열기", "compress": "압축", "decompress": "압축풀기"},
    "base64": {"b64encode": "육십사진인코딩", "b64decode": "육십사진해독"},
    "html": {"escape": "이스케이프", "unescape": "이스케이프해제"},
    "textwrap": {"dedent": "공통들여쓰기제거", "indent": "들여쓰기", "wrap": "줄나누기",
                 "fill": "줄맞춤", "shorten": "줄이기"},
    "unicodedata": {"normalize": "정규화", "name": "이름", "category": "범주"},
    "inspect": {"signature": "인자명세", "getsource": "소스얻기", "isfunction": "함수여부"},
    "importlib": {"import_module": "모듈불러오기", "reload": "다시불러오기"},
    "platform": {"system": "시스템", "machine": "기계", "python_version": "파이썬버전"},
}

if __name__ == "__main__":
    data = json.loads(PATH.read_text(encoding="utf-8"))
    for line in ALIASES.strip().splitlines():
        module, alias = line.split()
        data["modules"].setdefault(module, {"alias": alias})
    for module, members in MEMBERS.items():
        data["modules"][module].setdefault("members", {}).update(members)
    core = json.loads((ROOT / "src/hangeul_python/data/core.json").read_text(encoding="utf-8"))
    data["modules"]["builtins"]["members"] = {**core["builtins"], **core["exceptions"]}
    data["modules"]["builtins"]["keywords"] = data["builtin_keywords"].copy()
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
