# WebtoonScraper

[![PyPI - Downloads](https://img.shields.io/pypi/dm/WebtoonScraper)](https://pypi.org/project/WebtoonScraper/)
[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Filotoki0804%2FWebtoonScraper&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://github.com/ilotoki0804/WebtoonScraper)
[![Sponsoring](https://img.shields.io/badge/Sponsoring-Patreon-blue?logo=patreon&logoColor=white)](https://www.patreon.com/ilotoki0804)

This is a program that allows you to quickly and easily download webtoons from many websites.

For more information about copyright and liability, see [this document](./copyright.md).

* [WebtoonScraper](#webtoonscraper)
    * [How to use](#how-to-use)
    * [featuresAdditional](#featuresadditional)
    * [Use as an app](#use-as-an-app)
    * [Get it as an executable](#get-it-as-an-executable)
    * [Release notes](#release-notes)

## How to use

To use the app or portable version, click [here](#Use-as-an-app).

Install Python (3.10 or later, newer versions recommended) and run the following command in the terminal

```console
pip install -U WebtoonScraper[full]
```

Most webtoons will work by typing `webtoon download` in the terminal, followed by the URL in double quotes, like so

```console
webtoon download "https://comic.naver.com/webtoon/list?titleId=819217"
```

For other features and settings, please refer to the **[How to use](./how-to-use.md)** documentation.

## Donating

[![BECOME A PATREON](../images/patreon.png)](https://www.patreon.com/ilotoki0804)

The WebtoonScraper project is supported by donations.

By donating on [Patreon](https://www.patreon.com/ilotoki0804), you can support the developer and get a variety of additional features, including:

* In addition to Naver Webtoon and Lezhin Comics, you can download additional webtoons from Kakao Webtoon, Kakaopage, webtoons.com, Bufftoon, Naver Post, Naver Games, Naver Blog, and Tistory.
* WebtoonScraper app and its portable version
* Webtoon Viewer
* Merge episode directories
* Concatenating images

## Use as an app

[<img src="https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/main/images/gui.png" width="70%">](https://www.patreon.com/ilotoki0804)

WebtoonScraper is available as an app out of the box, with no python or pip installation required,
You don't need to know how to use the CLI to use the app.

**Please refer to the [App User Guide](./app-guide.md) for more information on how to download and use WebtoonScraper.**

In addition to Naver Webtoon and Lezhin Comics, you can download Kakao Webtoon, Kakaopage, webtoons.com, Bufftoon, Naver Post, Naver Games, Naver Blog, and Tistory.

Currently, it is only available for Windows, but I'm preparing to make it available for Mac and Android in the future.

## Get it as an executable

This package can be used as an executable file on Windows, Mac, and Linux.
There are several advantages to using it as an executable.

* You don't have to install Python or deal with pip, just download it and start using it.
* In addition to Naver Webtoon and Lezhin Comics, you can download Kakao Webtoon, Kakao Page, webtoons.com, Bufftoon, Naver Post, Naver Games, Naver Blog, and Tistory.
* The executable file allows you to download multiple webtoons much faster.

**Please refer to the [Executable File User Guide](./executable-guide.md) to learn how to download and use it.**

## Release notes

Please refer to the [Release Notes documentation](./releases.md).
