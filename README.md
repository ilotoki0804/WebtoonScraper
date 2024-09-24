# WebtoonScraper

[![Sponsoring](https://img.shields.io/badge/Sponsoring-Patreon-blue?logo=patreon&logoColor=white)](https://www.patreon.com/ilotoki0804)
[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Filotoki0804%2FWebtoonScraper&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://github.com/ilotoki0804/WebtoonScraper)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/WebtoonScraper)](https://pypi.org/project/WebtoonScraper/)
[![image](https://img.shields.io/pypi/l/WebtoonScraper.svg)](https://github.com/ilotoki0804/WebtoonScraper/blob/main/LICENSE)
[![image](https://img.shields.io/pypi/pyversions/WebtoonScraper.svg)](https://pypi.org/project/WebtoonScraper/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/ilotoki0804/WebtoonScraper/blob/main/pyproject.toml)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/ilotoki0804/WebtoonScraper/blob/main/pyproject.toml)

**[English documentation is available](./docs/README-en.md).**

쉽고 빠르게 많은 웹사이트에서 웹툰을 다운로드받을 있는 프로그램입니다.

저작권과 책임에 대한 내용을 더욱 자세히 알고 싶다면 [이 문서](./docs/copyright.md)를 참고해 주세요.

* [WebtoonScraper](#webtoonscraper)
    * [이용 방법](#이용-방법)
    * [후원하기](#후원하기)
    * [앱으로 이용하기](#앱으로-이용하기)
    * [실행 파일로 이용하기](#실행-파일로-이용하기)
    * [릴리즈 노트](#릴리즈-노트)

## 이용 방법

앱이나 포터블 버전 이용 방법은 [여기](#앱으로-이용하기)를 클릭하세요.

파이썬(3.10 이상, 최신 버전 권장)을 설치하고 터미널에서 다음과 같은 명령어를 실행합니다.

```console
pip install -U WebtoonScraper[full]
```

대부분의 웹툰은 다음과 같이 터미널에 `webtoon download`를 치고 큰따옴표로 감싼 URL을 뒤에 위치하면 작동합니다.

```console
webtoon download "https://comic.naver.com/webtoon/list?titleId=819217"
```

다른 기능들과 설정에 대해서는 **[사용 방법](./docs/how-to-use.md)** 문서를 참고해 주세요.

## 후원하기

[![BECOME A PATREON](./images/patreon.png)](https://www.patreon.com/ilotoki0804)

WebtoonScraper 프로젝트는 후원으로 운영됩니다.

[Patreon](https://www.patreon.com/ilotoki0804)으로 후원하시면 개발자를 후원하실 수 있으며 다음과 같은 다양한 추가 기능을 사용할 수 있습니다.

* **네이버 웹툰과 레진코믹스와 더불어 카카오 웹툰, 카카오페이지, webtoons.com, 버프툰, 네이버 포스트, 네이버 게임, 네이버 블로그, 티스토리, 투믹스를 추가로 다운로드받을 수 있습니다.**
* **WebtoonScraper 앱과 포터블 버전을 사용할 수 있습니다.**
* 에피소드 디렉토리 병합하기
* 이미지 연결하기
* 브라우저 PC 웹툰 뷰어 (webtoon.html)

## 앱으로 이용하기

[<img src="https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/main/images/gui.png" width="70%">](https://www.patreon.com/ilotoki0804)

WebtoonScraper는 파이썬이나 pip 설치 없이 바로 앱으로 사용할 수 있으며,
앱을 이용하면 CLI를 사용하는 방법을 알 필요 없이 더욱 간편하게 사용할 수 있습니다.

**다운로드와 사용 방법은 [앱 사용 가이드](./docs/app-guide.md)를 참고하세요.**

네이버 웹툰과 레진코믹스와 더불어 카카오 웹툰, 카카오페이지, webtoons.com, 버프툰, 네이버 포스트, 네이버 게임, 네이버 블로그, 티스토리, 투믹스를 추가로 다운로드받을 수 있습니다.

현재는 윈도우에서만 사용할 수 있으나, 향후 맥이나 안드로이드에서도 사용할 수 있도록 준비하고 있습니다.

## 실행 파일로 이용하기

이 패키지는 윈도우, 맥, 리눅스에서 실행 파일 형태로 사용할 수 있습니다.
실행 파일로 사용하면 몇 가지 장점이 있습니다.

* 파이썬 설치나 pip를 다룰 필요 없이 다운로드한 뒤 바로 사용이 가능합니다.
* 네이버 웹툰과 레진코믹스와 더불어 카카오 웹툰, 카카오페이지, webtoons.com, 버프툰, 네이버 포스트, 네이버 게임, 네이버 블로그, 티스토리, 투믹스를 추가로 다운로드받을 수 있습니다.
* 실행 파일을 이용하면 여러 웹툰을 다운로드받을 때 훨씬 빠르게 다운로드가 가능합니다.

**다운로드와 사용 방법은 [실행 파일 사용 가이드](./docs/executable-guide.md)를 참고하세요.**

## 릴리즈 노트

[릴리즈 노트 문서](./docs/releases.md)를 참고하세요.
