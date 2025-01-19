# WebtoonScraper

**[English documentation is available](./README-en.md).**

쉽고 빠르게 많은 웹사이트에서 웹툰을 다운로드받을 있는 프로그램입니다.

저작권과 책임에 대한 내용을 더욱 자세히 알고 싶다면 [이 문서](./mkdocs/94-copyright.md)를 참고해 주세요.

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

다른 기능들과 설정에 대해서는 **[사용 방법](./mkdocs/02-downloading-cli.md)** 문서를 참고해 주세요.

## 후원하기

[![BECOME A PATREON](https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/refs/heads/main/images/patreon.png)](https://www.patreon.com/ilotoki0804)

WebtoonScraper 프로젝트는 후원으로 운영됩니다.

[Patreon](https://www.patreon.com/ilotoki0804)으로 후원하시면 개발자를 후원하실 수 있으며 다음과 같은 다양한 추가 기능을 사용할 수 있습니다.

* **네이버 웹툰과 레진코믹스와 더불어 카카오 웹툰, 카카오페이지, 리디, webtoons.com, 버프툰, 네이버 포스트, 네이버 게임, 네이버 블로그, 티스토리, 투믹스, 이만배를 추가로 다운로드받을 수 있습니다.**
* **WebtoonScraper 앱과 포터블 버전을 사용할 수 있습니다.**
* 에피소드 디렉토리 병합하기
* 이미지 연결하기
* 브라우저 PC 웹툰 뷰어 (webtoon.html)

## 앱으로 이용하기

[<img src="https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/main/images/gui.png" width="70%">](https://www.patreon.com/ilotoki0804)

WebtoonScraper는 파이썬이나 pip 설치 없이 바로 앱으로 사용할 수 있으며,
앱을 이용하면 CLI를 사용하는 방법을 알 필요 없이 더욱 간편하게 사용할 수 있습니다.

**다운로드와 사용 방법은 [앱 사용 가이드](./mkdocs/03-downloading-app.md)를 참고하세요.**

네이버 웹툰과 레진코믹스와 더불어 카카오 웹툰, 카카오페이지, webtoons.com, 버프툰, 네이버 포스트, 네이버 게임, 네이버 블로그, 티스토리, 투믹스를 추가로 다운로드받을 수 있습니다.

현재는 윈도우에서만 사용할 수 있으나, 향후 맥이나 안드로이드에서도 사용할 수 있도록 준비하고 있습니다.

## 실행 파일로 이용하기

이 패키지는 윈도우, 맥, 리눅스에서 실행 파일 형태로 사용할 수 있습니다.
실행 파일로 사용하면 몇 가지 장점이 있습니다.

* 파이썬 설치나 pip를 다룰 필요 없이 다운로드한 뒤 바로 사용이 가능합니다.
* 네이버 웹툰과 레진코믹스와 더불어 카카오 웹툰, 카카오페이지, webtoons.com, 버프툰, 네이버 포스트, 네이버 게임, 네이버 블로그, 티스토리, 투믹스를 추가로 다운로드받을 수 있습니다.
* 실행 파일을 이용하면 여러 웹툰을 다운로드받을 때 훨씬 빠르게 다운로드가 가능합니다.

**다운로드와 사용 방법은 [실행 파일 사용 가이드](./mkdocs/02-downloading-cli.md)를 참고하세요.**

## 릴리즈 노트

[릴리즈 노트 문서](./mkdocs/95-releases.md)를 참고하세요.

## 이용 방법

WebtoonScraper는 크게 세 가지 종류로 나뉘어집니다.

* PyPI 패키지
* 포터블 버전
* 앱

**PyPI 패키지**는 가장 기본이 되는 버전이며 자유롭게 다운로드해 사용할 수 있지만 파이썬을 설치해야 하고 *네이버 웹툰과 레진코믹스만 지원*합니다.

**포터블 버전**은 [후원](https://www.patreon.com/ilotoki0804)을 하면 이용할 수 있고 네이버 웹툰과 레진코믹스를 *포함*해 *카카오 웹툰, 카카오페이지, webtoons.com, 버프툰, 네이버 포  스트, 네이버 게임, 네이버 블로그, 티스토리, 투믹스*에서도 웹툰 다운로드를 지원하며, 특별한 설치 없이도 사용 가능합니다.

**앱 버전**은 포터블 버전과 마찬가지로 [후원](https://www.patreon.com/ilotoki0804)하면 이용할 수 있으며 직접 명령어를 입력할 필요 없이 사용할 수 있습니다.

## 오류를 발견했어요!

모든 프로그램이 그렇듯 WebtoonScraper를 사용하다 보면 오류를 발견할 수도 있습니다.
그럴 경우 [깃허브 이슈](https://github.com/ilotoki0804/WebtoonScraper/issues/)를 만들거나 [패트리온 DM](https://www.patreon.com/ilotoki0804)으로 연락 주시면 됩니다.
보통은 하루 이내에 답장을 받으실 수 있을 겁니다.

오류를 설명할 때는 다음과 같은 사항들을 알려주시면 더 빠르게 수정될 수 있습니다.

* `webtoon --version`을 실행했을 때 출력되는 문자열. 최신이 아닐 경우 제보 전 최신 버전으로 업데이트한 후 해결되는지 확인하세요!
* 사용한 프로그램(PyPI 패키지, 포터블, 앱)
* 다운로드하려고 시도했던 웹툰의 URL
* 운영체제 (윈도우/맥/리눅스)
* (포터블/패키지의 경우)`-v` 플래그 추가해 다운로드 시도한 뒤 출력되는 문자열(예: `webtoon -v download "<url>"`)
