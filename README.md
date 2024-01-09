# WebtoonScraper
<!-- [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) -->
[![PyPI - Downloads](https://img.shields.io/pypi/dm/WebtoonScraper)](https://pypi.org/project/WebtoonScraper/)
[![Gitbook Link](https://img.shields.io/badge/Gitbook-Link-blue?link=https%3A%2F%2Filotoki0804.gitbook.io%2Fwebtoonscraper%2F)](https://ilotoki0804.gitbook.io/webtoonscraper/)
[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Filotoki0804%2FWebtoonScraper&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://github.com/ilotoki0804/WebtoonScraper)

최대 규모 오픈 소스 웹툰 스크래퍼입니다.

**네이버 웹툰(베스트 도전, 도전만화 포함), webtoons.com, 버프툰, 네이버 포스트, 네이버 게임, 레진 코믹스, 카카오페이지, 네이버 블로그, 티스토리**를 지원하고, 계속해서 지원 목록을 확대할 계획입니다.

> [!TIP]
> 카카오 웹툰에 있는 웹툰들은 카카오페이지에도 있으니 카카오 웹툰을 다운로드받고 싶다면 카카오페이지 웹툰 스크래퍼를 이용해 주세요.

저작권과 책임에 대한 내용을 더욱 자세히 알고 싶다면 [이 문서](docs/copyright.md)를 참고해 주세요.

## Installation

1. 파이썬(3.10 이상)을 설치합니다. 설치 방법은 인터넷에 잘 나와 있습니다. 꼭 Path에 파이썬이 포함되도록 설치하세요.
1. 터미널에서 다음과 같은 명령어를 실행합니다.

    ```console
    pip install -U WebtoonScraper
    ```

    대체적으로, 자신이 사용하는 운영 체제가 POSIX 기반(Mac이나 Linux)라면 다음의 명령어를 사용해야 할 수도 있습니다.

    ```console
    pip3 install -U WebtoonScraper
    ```

1. 자신의 환경에서 잘 설치되었는지 확인해 보세요.

    CLI가 잘 설치되었는지를 확인하려면 다음의 명령어를 사용해 보세요.

    ```console
    webtoon --version
    ```

    >[!NOTE]
    > 만약 `webtoon` 명령어가 잘 실행되지 않는다면 다음의 코드를 사용해 보세요.
    >
    > ```console
    > python -m WebtoonScraper --version
    > ```
    >
    > 자신의 환경에 따라 `python` 대신 `python3`나 `py -3.12`과 같은 코드를 적절히 사용해야 할 수 있습니다.

    자신의 파이썬 환경에 잘 설치되었는지를 확인하려면 다음의 코드를 실행해 보세요.

    ```python
    from WebtoonScraper import webtoon as wt
    ```

## How to use

사용 방법은 [`사용 방법` 문서](docs/how_to_use.md)를 참고해 주세요.

## 이 라이브러리가 다운로드 가능한 웹툰/에피소드의 종류

[이 라이브러리가 다운로드 가능한 웹툰/에피소드의 종류 문서](docs/download_availability.md)를 참고하세요.

## Relese Note

[Relese Note 문서](docs/releases.md)를 참고하세요.
