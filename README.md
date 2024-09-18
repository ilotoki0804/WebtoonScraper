# WebtoonScraper

[![Sponsoring](https://img.shields.io/badge/Sponsoring-Patreon-blue?logo=patreon&logoColor=white)](https://www.patreon.com/ilotoki0804)
[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Filotoki0804%2FWebtoonScraper&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://github.com/ilotoki0804/WebtoonScraper)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/WebtoonScraper)](https://pypi.org/project/WebtoonScraper/)
[![image](https://img.shields.io/pypi/l/WebtoonScraper.svg)](https://github.com/ilotoki0804/WebtoonScraper/blob/main/LICENSE)
[![image](https://img.shields.io/pypi/pyversions/WebtoonScraper.svg)](https://pypi.org/project/WebtoonScraper/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/ilotoki0804/WebtoonScraper/blob/main/pyproject.toml)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/ilotoki0804/WebtoonScraper/blob/main/pyproject.toml)

**[English documentation is available](./docs/README-en.md).**

쉽고 빠르게 웹툰을 다운로드받을 있는 프로그램입니다.

저작권과 책임에 대한 내용을 더욱 자세히 알고 싶다면 [이 문서](./docs/copyright.md)를 참고해 주세요.

* [WebtoonScraper](#webtoonscraper)
    * [이용 방법](#이용-방법)
    * [추가 기능](#추가-기능)
        * [앱으로 이용하기 (베타)](#앱으로-이용하기-베타)
        * [실행 파일로 이용하기](#실행-파일로-이용하기)
            * [운영체제별 참고사항](#운영체제별-참고사항)
    * [릴리즈 노트](#릴리즈-노트)

## 이용 방법

앱이나 포터블 버전 이용 방법은 [여기](#앱으로-이용하기-베타)를 클릭하세요.

파이썬(3.10 이상, 최신 버전 권장)을 설치하고 터미널에서 다음과 같은 명령어를 실행합니다.

```console
pip install -U WebtoonScraper[full]
```

대부분의 웹툰은 다음과 같이 터미널에 `webtoon download`를 치고 큰따옴표로 감싼 URL을 뒤에 위치하면 작동합니다.

```console
webtoon download "https://comic.naver.com/webtoon/list?titleId=819217"
```

**일부 웹툰 플랫폼의 경우에는 추가적인 정보가 반드시 필요한 경우가 있습니다. 반드시 [플랫폼별 다운로드 가이드](./docs/platforms.md)를 참고해 주세요.**

일반 다운로드 외에도 WebtoonScraper에는 다양한 기능이 있습니다.

* 다운로드할 디렉토리 설정하기
* 범위를 설정해서 다운로드하기
* 파이썬 스크립트로 사용하기
* 그 외 다양한 기능들...

또한 일부 웹툰 플랫폼들은 추가적인 설정을 필요로 할 수 있습니다.

다른 기능들과 설정에 대해서는 **[사용 방법](./docs/how-to-use.md)** 문서를 참고해 주세요.

## 추가 기능

[![BECOME A PATREON](./images/patreon.png)](https://www.patreon.com/ilotoki0804)

WebtoonScraper 프로젝트는 후원으로 운영됩니다.

[Patreon](https://www.patreon.com/ilotoki0804)에서 후원하시면 개발자를 후원하실 수 있으며 다음과 같은 다양한 추가 기능을 사용할 수 있습니다.

* 네이버 웹툰과 레진코믹스와 더불어 카카오 웹툰, 카카오페이지, webtoons.com, 버프툰, 네이버 포스트, 네이버 게임, 네이버 블로그, 티스토리를 추가로 다운로드받을 수 있음
* WebtoonScraper 앱과 포터블 버전
* 웹툰 뷰어
* 에피소드 디렉토리 병합하기
* 이미지 연결하기

### 앱으로 이용하기 (베타)

[<img src="https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/main/images/gui.png" width="70%">](https://www.patreon.com/ilotoki0804)

WebtoonScraper는 파이썬이나 pip 설치 없이 바로 앱으로 사용할 수 있으며,
앱을 이용하면 CLI를 사용하는 방법을 알 필요 없이 더욱 간편하게 사용할 수 있습니다.

또한 실행 파일과 마찬가지로 네이버 웹툰과 레진코믹스와 더불어 카카오 웹툰, 카카오페이지, webtoons.com, 버프툰, 네이버 포스트, 네이버 게임, 네이버 블로그, 티스토리를 추가로 다운로드받을 수 있습니다.

현재는 베타 버전이며 윈도우에서만 사용할 수 있으나, 향후 맥이나 안드로이드에서도 사용할 수 있도록 준비하고 있습니다.

다음과 같은 방법을 통해 앱을 사용하실 수 있습니다.

1. [패트리온](https://www.patreon.com/ilotoki0804) 페이지로 가세요. 후원자의 경우에만 다운로드가 가능합니다.
1. `windows-app.zip` 파일을 클릭해 다운로드하세요.
1. zip파일을 풀고 사용하세요.
1. 이때 "Windows의 PC 보호" 창이 뜨면서 실행이 안 될 수 있습니다. 그런 경우에는 `추가 정보`(왼쪽 중간에 있습니다.)를 클릭하고 `실행`을 누르세요.

### 실행 파일로 이용하기

이 패키지는 윈도우, 맥, 리눅스에서 실행 파일 형태로 사용할 수 있습니다.
실행 파일로 사용하면 몇 가지 장점이 있습니다.

* 파이썬 설치나 pip를 다룰 필요 없이 다운로드한 뒤 바로 사용이 가능합니다.
* 네이버 웹툰과 레진코믹스와 더불어 카카오 웹툰, 카카오페이지, webtoons.com, 버프툰, 네이버 포스트, 네이버 게임, 네이버 블로그, 티스토리를 추가로 다운로드받을 수 있습니다.
* 실행 파일을 이용하면 여러 웹툰을 다운로드받을 때 훨씬 빠르게 다운로드가 가능합니다.

다음과 같은 방법을 통해 앱을 사용하실 수 있습니다.

1. [패트리온](https://www.patreon.com/ilotoki0804) 페이지로 가세요. 후원자의 경우에만 다운로드가 가능합니다.
1. 자신의 운영 체제와 일치하는 이름이 적힌 zip 파일을 클릭해 다운로드하세요.
1. zip파일을 풀고 사용하세요.

#### 운영체제별 참고사항

* 윈도우: "Windows의 PC 보호" 창이 뜨면서 실행이 안 될 수 있습니다. 그런 경우에는 `추가 정보`(왼쪽 중간에 있습니다.)를 클릭하고 `실행`을 누르세요.
* 맥OS와 리눅스: `bash: ./pyinstaller: Permission denied`라고 나오며 실행을 거부할 수 있습니다. `chmod +x ./pyinstaller`를 통해 실행 권한을 추가하세요.

## 릴리즈 노트

[릴리즈 노트 문서](./docs/releases.md)를 참고하세요.
