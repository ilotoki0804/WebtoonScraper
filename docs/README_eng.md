# WebtoonScraper

[![GitHub Downloads (all assets, latest release)](https://img.shields.io/github/downloads/ilotoki0804/WebtoonScraper/latest/total?label=executable%20downloads)](https://github.com/ilotoki0804/WebtoonScraper/releases)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/WebtoonScraper)](https://pypi.org/project/WebtoonScraper/)
[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Filotoki0804%2FWebtoonScraper&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://github.com/ilotoki0804/WebtoonScraper)
[![Sponsoring](https://img.shields.io/badge/Sponsoring-Toss-blue?logo=GitHub%20Sponsors&logoColor=white)](https://toss.me/ilotoki)

The largest open source webtoon scraper.

It supports **Naver Webtoon (including Best Challenge, Challenge Comics), webtoons.com, Bufftoon, Naver Post, Naver Game, Lezhin Comics, KakaoPage, Naver Blog, Tistory, Kakao Webtoon**, and possibly more in future.

If you want to know more about copyright and responsibility, please refer to [this document(Korean)](copyright.md).

* I apologize that only the README is available in English. Most of our users, including myself, are Korean, so I can't pay much attention to English documentation. But the browser translation tool is pretty good! Give it a try.

## Using as an executable file

This package can be used as an executable file on Windows, macOS, and Linux.

1. Go to the [release page](https://github.com/ilotoki0804/WebtoonScraper/releases).
1. Go to the latest release, click on the zip file with the name matching your operating system to download.
1. Unzip the file and use it.

> [!WARNING]
> In the case of Windows, the "Windows protected your PC" window may pop up and prevent execution. In that case, click on `More Info` (located in the middle left) and press `Run`.

## Installation

1. Install Python (version 3.10 or higher, latest version is recommended). Ensure Python is included in the PATH during installation.
2. Run the following command in the terminal:

    ```console
    pip install -U WebtoonScraper[full]
    ```

To check if the program has been installed correctly, use the following command:

```console
webtoon --version
```

> If the `webtoon` command does not run properly, try using the following code:
>
> ```console
> python -m WebtoonScraper --version
> ```
>
> Depending on your environment, you may need to use `python3` or `py -3.12` instead of `python`.

If you get a message like or similar to the one below, you're good to go.

```console
WebtoonScraper 3.2.2 of Python 3.11.4 ... at ...
✅ All extra dependencies are installed!
```

> You might get a warning message like this.
>
> ```console
> WebtoonScraper 3.2.2 of Python 3.11.4 ... at ...
> ⚠️ Extra dependencies 'kakao_webtoon', 'lezhin_comics', 'naver_post' are not installed.
> You won't be able to download webtoons from following platforms: 'Kakao Webtoon', 'Lezhin Comics (partially)', 'Naver Post'.
> ```
>
> In this case, additional dependencies for the indicated platforms (in the case of this error message, Kakao Webtoon, Lezhin Comics (partially), and Naver Post) are not installed, so you won't be able to download webtoons from them.
>
> You can download webtoons on all platforms by writing the command as follows.
>
> ```console
> pip install -U WebtoonScraper[full]
> ```

## How to Use

Most webtoons can be downloaded by typing `webtoon download` in terminal followed by the URL enclosed in double quotes.

```console
webtoon download "https://www.webtoons.com/en/action/omniscient-reader/list?title_no=2154"
```

If you want to know more about the features of WebtoonScraper (set range of epidsodes to download, merge episode, set download directory, episode listing, use with Python, etc.) or if it does not work well with the method introduced above (Bufftoon and Lezhin Comics, additional steps are essential), please refer to the [`Usage Guide(Korean)`](how_to_use.md).

## Types of Webtoons/Episodes that This Library Can Download

Please refer to the [`Types of Webtoons/Episodes that This Library Can Download(Korean)`](download_availability.md) document.

## Build from Source

First, install git and python and clone the repository.

```console
git clone https://github.com/ilotoki0804/WebtoonScraper.git
```

Then create and activate a virtual environment.

```console
echo For Windows
py -3.12 -m venv .venv
.venv\Scripts\activate

echo For UNIX
python3.12 -m venv .venv
.venv/bin/activate
```

Install poetry and the dependencies.

```console
pip install poetry
poetry install --extras full --no-root
```

Run `build.py`.

```console
python build.py
```

Now, the built `whl` and `tar.gz` files will appear in `dist`.

## Release Note

Please refer to the [`Release Note(Korean)`](releases.md) document.
