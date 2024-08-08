# WebtoonScraper

[![GitHub Downloads (all assets, latest release)](https://img.shields.io/github/downloads/ilotoki0804/WebtoonScraper/latest/total?label=executable%20downloads)](https://github.com/ilotoki0804/WebtoonScraper/releases)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/WebtoonScraper)](https://pypi.org/project/WebtoonScraper/)
[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Filotoki0804%2FWebtoonScraper&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://github.com/ilotoki0804/WebtoonScraper)
[![Sponsoring](https://img.shields.io/badge/Sponsoring-Toss-blue?logo=GitHub%20Sponsors&logoColor=white)](https://toss.me/ilotoki)

1. [WebtoonScraper](#webtoonscraper)
    1. [How to use](#how-to-use)
    2. [Installation](#installation)
        1. [Use as an executable](#use-as-an-executable)
            1. [운영체제별 참고사항](#운영체제별-참고사항)
        2. [Install through pip](#install-through-pip)
        3. [Build from source](#build-from-source)
    3. [Release Note](#release-note)


**English documentation is available [here](./docs/README_eng.md).**

최대 규모 오픈 소스 웹툰 스크래퍼입니다.

**네이버 웹툰, webtoons.com, 버프툰, 네이버 포스트, 네이버 게임, 레진 코믹스, 카카오페이지, 네이버 블로그, 티스토리, 카카오 웹툰**을 지원하고, 계속해서 지원 목록을 확대할 계획입니다.

저작권과 책임에 대한 내용을 더욱 자세히 알고 싶다면 [이 문서](./docs/copyright.md)를 참고해 주세요.

## How to use

대부분의 웹툰은 다음과 같이 터미널에 `webtoon download`를 치고 큰따옴표로 감싼 URL을 뒤에 위치하면 작동합니다.

```console
webtoon download "https://comic.naver.com/webtoon/list?titleId=819217"
```

**일부 웹툰 플랫폼의 경우에는 추가적인 정보가 반드시 필요한 경우가 있습니다. 반드시 [플랫폼별 다운로드 가이드](docs/platforms.md)를 참고해 주세요.**

일반 다운로드 외에도 WebtoonScraper에는 다양한 기능이 있습니다.

* 다운로드할 디렉토리 설정하기
* 웹툰 뷰어
* 범위를 설정해서 다운로드하기
* 에피소드 디렉토리 병합하기
* 이미지 연결하기
* 파이썬 스크립트로 사용하기
* 그 외 다양한 기능들...

또한 일부 웹툰 플랫폼들은 추가적인 설정을 필요로 할 수 있습니다.

추가 기능들과 설정에 대해서는 **[사용 방법](./docs/how_to_use.md)** 문서를 참고해 주세요.

## Installation

### Use as an executable

이 패키지는 Windows, macOS, Linux에서 실행 파일 형태로 사용할 수 있습니다.

1. [릴리즈 페이지](https://github.com/ilotoki0804/WebtoonScraper/releases)로 가세요.
1. 최신 릴리즈 아래에서 자신의 운영 체제와 일치하는 이름이 적힌 zip 파일을 클릭해 다운로드하세요.
1. zip파일을 풀고 사용하세요.

#### 운영체제별 참고사항

* 윈도우: "Windows의 PC 보호" 창이 뜨면서 실행이 안 될 수 있습니다. 그런 경우에는 `추가 정보`(왼쪽 중간에 있습니다.)를 클릭하고 `실행`을 누르세요.
* 맥OS와 리눅스: `bash: ./pyinstaller: Permission denied`라고 나오며 실행을 거부할 수 있습니다. `chmod +x ./pyinstaller`를 통해 실행 권한을 추가하세요.

### Install through pip

파이썬(3.10 이상, 최신 버전 권장)을 설치하고 터미널에서 다음과 같은 명령어를 실행합니다.

```console
pip install -U WebtoonScraper[full]
```

업데이트시에도 똑같은 코드를 이용할 수 있습니다.

잘 설치되었는지를 확인하려면 다음의 명령어로 테스트해 보세요.

```console
webtoon --version
```

### Build from source

우선 git과 python을 설치하고 레포지토리를 클론하고 해당 디렉토리로 이동하세요.

```console
git clone https://github.com/ilotoki0804/WebtoonScraper.git
cd WebtoonScraper
```

그런 다음 가상 환경을 생성하고 활성화하세요.

```console
echo 윈도우의 경우
py -3.12 -m venv .venv
.venv\Scripts\activate

echo UNIX인 경우
python3.12 -m venv .venv
.venv/bin/activate
```

poetry를 설치하고 의존성을 설치하세요.

```console
pip install poetry
poetry install --extras full --no-root
```

`simplebuilder`를 실행하세요.

```console
python -m simplebuilder
```

이제 `dist`에 빌드된 `whl` 파일과 `tar.gz` 파일이 나타납니다.

## Release Note

[Release Note 문서](./docs/releases.md)를 참고하세요.
