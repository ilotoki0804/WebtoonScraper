# WebtoonScraper

[![PyPI - Downloads](https://img.shields.io/pypi/dm/WebtoonScraper)](https://pypi.org/project/WebtoonScraper/)
[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Filotoki0804%2FWebtoonScraper&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://github.com/ilotoki0804/WebtoonScraper)
[![Sponsoring](https://img.shields.io/badge/Sponsoring-Patreon-blue?logo=patreon&logoColor=white)](https://www.patreon.com/ilotoki0804)

Download webtoons with ease.

If you want to know more about copyright and responsibility, please refer to [this document(Korean)](copyright.md).

* [WebtoonScraper](#webtoonscraper)
    * [How to use](#how-to-use)
    * [Installation](#installation)
        * [Use as an executable](#use-as-an-executable)
            * [Operating system-specific notes](#operating-system-specific-notes)
        * [Install via pip](#install-via-pip)
    * [Donate](#donate)
    * [Release Note](#release-note)

## How to use

Most webtoons work by typing `webtoon download` in the terminal followed by the URL enclosed in double quotes, like below.

```console
webtoon download "https://comic.naver.com/webtoon/list?titleId=819217"
```

**For some webtoon platforms, additional information may be required. Please refer to the [platform-specific download guide(Korean)](platforms.md) for more information.**


In addition to regular downloads, WebtoonScraper has many other features.

* Set the directory to download
* Webtoon viewer
* Set a range to download
* Merge episode directories
* Concatenating images
* Use it as a Python script
* And more...

Also, some webtoon platforms may require additional configuration.

Please refer to the **[How to use(Korean)](how-to-use.md)** documentation for additional features and settings.

## Installation

### Use as an executable

This package can be used as an executable on Windows, macOS, and Linux.

1. go to the [Patreon page](https://www.patreon.com/ilotoki0804).
1. Under Latest Releases, click the zip file with the name that matches your operating system to download it.
1. Unzip the file and use it.

#### Operating system-specific notes

* Windows: The "Windows Protected your PC" window may pop up and prevent you from running, in which case click "More Info" (in the middle left corner) and hit "Run".
* MacOS and Linux: It might tell you `bash: ./pyinstaller: Permission denied` and refuse to run. Add execute permission via `chmod +x ./pyinstaller`.

### Install via pip

Install Python (3.10 or later, newer versions are recommended) and run the following command in the terminal

```console
pip install -U WebtoonScraper[full]
```

You can use the same code for updates.

To make sure it installed well, test it with the command

```console
webtoon --version
```

## Donate

The WebtoonScraper project is funded by donations.

You can support the developers by donating on [Patreon](https://www.patreon.com/ilotoki0804),
and you can download a portable version.

We also plan to create a GUI application in the future.

## Release Note

See the [Release Note](releases.md).
