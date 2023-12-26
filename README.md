# WebtoonScraper
<!-- [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) -->
[![PyPI - Downloads](https://img.shields.io/pypi/dm/WebtoonScraper)](https://pypi.org/project/WebtoonScraper/)
[![Gitbook Link](https://img.shields.io/badge/Gitbook-Link-blue?link=https%3A%2F%2Filotoki0804.gitbook.io%2Fwebtoonscraper%2F)](https://ilotoki0804.gitbook.io/webtoonscraper/)
[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Filotoki0804%2FWebtoonScraper&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://github.com/ilotoki0804/WebtoonScraper)

최대 규모 오픈 소스 웹툰 스크래퍼입니다.

**네이버 웹툰, 베스트 도전만화, 웹툰 오리지널, 웹툰 캔버스, 버프툰, 네이버 포스트, 네이버 게임, 레진 코믹스, 카카오페이지, 네이버 블로그, 티스토리**를 지원하고, 계속해서 지원 목록을 확대할 계획입니다.

카카오 웹툰을 다운로드받고 싶다면 카카오페이지 웹툰 스크래퍼를 이용해 주세요. 카카오웹툰에 있는 모든 웹툰은 카카오페이지에도 있습니다.

저작권과 책임에 대한 내용을 더욱 자세히 알고 싶다면 [이 문서](docs/copyright.md)를 참고해 주세요.

## 사용 가능한 파이썬 버전

3.10 이상 3.11.4 이하에서 지원됩니다.

**3.11.5 이상에서도 작동하기는 하지만 OpenSSL 관련 변화로 인해 속도가 느려지고 CPU 점유율이 비정상적으로 높아지는 문제가 있습니다. 사용을 권장하지 않습니다.**

3.9 및 그 이하 버전은 호환되지 않습니다.

## 시작하기

1. 파이썬을 설치합니다(추천 버전: 3.11.4).
1. 터미널에서 다음과 같은 명령어를 실행합니다.

    ```console
    pip install -U WebtoonScraper
    ```

1. 자신의 환경에서 잘 설치되었는지 확인해 보세요.

    ```python
    from WebtoonScraper import webtoon as wt
    ```

    위의 코드가 정상적으로 실행된다면 잘 설치된 겁니다.

## 네이버 웹툰, 베스트 도전만화, 웹툰 오리지널, 웹툰 캔버스, 네이버 게임, 카카오페이지 다운로드하기

버프툰과 네이버 포스트, 레진코믹스, 네이버 블로그는 [이 문서](docs/specific_platform_download.md)를 참고하세요.

### 웹툰 ID 복사

원하는 웹툰으로 가서 웹툰 ID를 복사하세요.

[**네이버 웹툰/베스트 도전** 예시: 위아더좀비(이명재)](https://comic.naver.com):
![위아더좀비(네이버 웹툰) by 이명재](images/naver_webtoon.png)

[**웹툰 오리지널/캔버스** 예시: Wetermelon(Rorita)](https://webtoons.com):
![Wetermelon(WEBTOON) by Rorita](images/webtoons_original.png)

[**네이버 게임 오리지널 시리즈** 예시: 도리도리의 게임추억(도리도리)](https://game.naver.com/original_series):
![출처: 도리도리의 게임추억(네이버 게임 오리지널 시리즈) by 도리도리](images/naver_game.png)

버프툰과 네이버 포스트는 아래의 '버프툰 다운로드하기'섹션과 '네이버 포스트 다운로드하기' 섹션을 참고해 주세요.

### WebtoonScraper CLI로 웹툰 다운로드하기

CLI는 Command Line Interface의 약자로, Win+R 키를 누르고 `cmd`를 입력하면 나오는 까만(혹은 하얗거나 파란) 창으로 상호작용하는 것을 일컫습니다.

다음의 설명을 따르면 CLI로 간편히 웹툰을 다운로드 받을 수 있습니다.

#### 시작하기 전에

우선 `시작하기` 부분에 있었던 파이썬과 모듈 설치는 제대로 했는지 확인하세요.

#### CLI 사용

WebtoonScraper를 다운로드하면 `webtoon` 명령어를 사용할 수 있습니다.

```console
c:\Users>webtoon -h
usage: Download or merge webtoons in CLI

Download webtoons with ease!

options:
  -h, --help        show this help message and exit
  --mock            No actual download.
  --version         show program's version number and exit

Commands:
  {download,merge}  Choose command you want. Currently download is only valid option.
    download        Download webtoons.
    merge           Merge/Restore webtoon directory.
```

만약 해당 명령어가 작동하지 않을 경우 `python -m WebtoonScraper` 명령어를 사용하세요.

```python
python -m WebtoonScraper -h
```

이 뒤부터는 `webtoon` 명령어를 사용합니다. 만약 `'webtoon'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램, 또는 배치 파일이 아닙니다.`라는 오류가 출력(윈도우 기준)된다면 모든 `webtoon`를 `python -m WebtoonScraper`로 바꿔서 진행하세요.

##### download 커맨드

'download' command를 이용하면 명령어를 웹툰을 다운로드할 수 있습니다.

```console
webtoon download 766648
```

네이버 포스트의 경우 두 개의 인자를 입력해야 하는데, `webtoon download "<seriesNo>,<memberNo>"` 형식으로 입력하시면 됩니다.

따옴표 없이 사용해도 되지만, 따옴표 없이 사용한다면 `,` 사이에 스페이스를 넣으면 안 된다는 점을 주의하세요.

```console
webtoon download "614921,19803452"   # 가능
webtoon download "614921, 19803452"  # 가능
webtoon download 614921,19803452     # 가능
webtoon download 614921, 19803452    # XXX 불가능
```

웹툰으로 다운로드받을 플랫폼을 직접 설정할 수도 있습니다. 설정하지 않아도 정상적으로 작동되지만 플랫폼을 설정하면 더 빠르고 추가적인 상호작용 없이 다운로드받을 수 있습니다. 이는 `-p` 또는 `--platform`을 사용하시면 됩니다.

```console
webtoon download 766648 -p naver_webtoon
```

`-r`, `--range`를 이용하면 몇 번부터 몇 번까지 웹툰을 다운로드 받을지 결정할 수 있습니다. 이때 주의할 것은 웹툰 제목에 있는 `...화`라고 되어 있는 것과는 다르다는 점입니다. 우선 `--list-episodes`를 이용해 어디부터 어디까지 다운로드받을지 결정하세요.

```console
webtoon download 766648 -p naver_webtoon -r 6,20  # 6번부터 20번까지
## 앞과 뒤에 있는 숫자는 생략 가능합니다
webtoon download 766648 -p naver_webtoon -r ,3  # 처음부터 3번 회차까지
webtoon download 766648 -p naver_webtoon -r 15,  # 15번부터 끝까지
```

기타 옵션들:

```console
-h, --help: 도움말을 출력합니다.
-m, --merge: 만약에 merge를 사용한다면, merge할 양을 정합니다. (['여러 회차 하나로 묶기' 참고](https://github.com/ilotoki0804/WebtoonScraper#여러-회차-하나로-묶기))
--list-episodes: 전체 에피소드들을 에피소드 번호와 함께 표로 출력합니다. 이 기능을 사용한다면 webtoon_id, cookie, authkey를 제외한 나머지 인수들은 사용되지 않습니다.
-d, --download-directory: 웹툰을 다운로드할 디렉토리를 설정합니다. 기본은 'webtoon'이고 만약 현재 폴더에 바로 다운로드받고 싶다면 '.'을 입력하세요.
--authkey: (레진코믹스 전용): authkey를 설정합니다. 앞뒤에 큰따옴표(")를 붙이세요.
--cookie: (버프툰 전용): cookie를 설정합니다. 앞뒤에 큰따옴표(")를 붙이세요.
```

예를 들어 다음과 같이 사용할 수 있습니다.

```console
webtoon download -h  # 다운로드 관련 도움말 보기
webtoon download 766648  # 766648 웹툰 다운로드
webtoon download 766648 -p naver_webtoon  # 766648번 네이버 웹툰 다운로드
webtoon download 766648 --platform naver_webtoon  # 위와 같음
webtoon download 614921,19803452 -p naver_post  # 네이버 포스트 다운로드
webtoon download "614921,19803452" -p naver_post  # 위와 같음
webtoon download 766648 -r 4,16  # 4화부터 16화까지 다운로드
webtoon download 766648 -r 13,  # 13화부터 끝까지 다운로드
webtoon download 766648 -m 5  # 5화씩 묶기
webtoon download 766648 --list-episodes  # 모든 에피소드 정보 보기
webtoon download 766648 -p naver_webtoon -r 4, -m 5 -d .  # 여러 옵션 섞기
```

##### merge 커맨드

웹툰을 합치거나 되돌리고 싶을 때 merge 커맨드를 사용할 수 있습니다.
예를 들어 다음과 같이 커맨드를 작성하면

```console
webtoon merge "킬더킹(670145)" 
```

"webtoon/킬더킹(670145)"에 있는 만화가 만약 이미 합쳐진 웹툰이라면 복구되고, 기본 상태 웹툰이라면 합쳐집니다.

만약 webtoon이 아닌 다른 부모 디렉토리에 있다면(예: 웹툰이 `./hello/world/킬더킹(670145)`에 있다면) 다음과 같은 명령어를 사용할 수 있습니다.

```console
webtoon merge "킬더킹(670145)" -r hello/world
```

만약 웹툰 디렉토리가 현재 디렉토리에 있다면(예: 웹툰이 `./킬더킹(670145)`에 있다면) 다음과 같은 명령어를 사용할 수 있습니다.

```console
webtoon merge "킬더킹(670145)" -r .
```

전체 설명:

```console
usage: Download or merge webtoons in CLI merge [-h] [--all]
                                               [-a [a]uto|[m]erge|[r]estore]
                                               [-m merge_amount]
                                               [-s source_parent_directory]
                                               [-t target_parent_directory] [--list]    
                                               [webtoon_directory_name]

positional arguments:

options:
  -h, --help            show this help message and exit
  --all                 Merge/Restore all webtoons in root directory. If state of
                        webtoons not equal, you cannot use auto action.
  -a [a]uto|[m]erge|[r]estore, --action [a]uto|[m]erge|[r]estore
                        Merge/Restore. If this is auto, it'll flip state(merge >
                        restore, restore > merge).
  -m merge_amount, --merge-amount merge_amount
                        Merge amount when merge.
  -s source_parent_directory, --source-directory source_parent_directory, --source-parent-directory source_parent_directory     
                        The directory that the folders of webtoons are located.
  -t target_parent_directory, --target-directory target_parent_directory, --target-parent-directory target_parent_directory     
                        The directory that the result of merge/restore will be
                        located. Defaults to soure directory itself.
  --list                List all directories and states.
```

### `WebtoonScraper.webtoon` 모듈로 웹툰 다운로드하기

이 파트의 전체 내용은 [이 문서](docs/python_script.md)를 참고하세요.

다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.

이때 전에 복사해 두었던 웹툰 ID를 함수의 첫 번째 파라미터에 위치시키면 됩니다.

```python
# 이 라인은 꼭 포함하세요.
# 대소문자에 주의하세요! 맞추지 않으면 작동하지 않습니다.
# webtoon으로 사용해도 상관없지만 wt으로 줄여서 사용하는 것을 권장합니다.
from WebtoonScraper import webtoon as wt

# 이 아래부터는 자신이 원하는 플랫폼 하나를 골라서 사용하면 됩니다.

# 네이버 웹툰
wt.download_webtoon(766648, wt.N)

# 베스트 도전만화
wt.download_webtoon(763952, wt.BC)

# 웹툰 오리지널
wt.download_webtoon(1435, wt.O)

# 웹툰 캔버스
wt.download_webtoon(304446, wt.C)

# 네이버 게임 오리지널 시리즈
wt.download_webtoon(5, wt.G)

# 버프툰
cookie = 'cookie here'  # cookie를 여기에다 붙여넣으세요. 자세한 설명은 아래의 '버프툰 다운로드하기'를 참고하세요.
wt.download_webtoon(1007888, wt.BF, cookie=cookie)

# 네이버 포스트
wt.download_webtoon((597061, 19803452), wt.P)  # seriesNo와 memberNo를 각각 붙여넣으세요. 자세한 설명은 아래의 '네이버 포스트 다운받기'를 참고하세요.

# 레진코믹스
authkey = 'authkey here'  # authkey을 여기에다 붙여넣으세요. 자세한 설명은 아래의 '레진코믹스 다운로드하기'를 참고하세요.
wt.download_webtoon('dr_hearthstone', wt.L, authkey=authkey)

# 카카오페이지
wt.download_webtoon(53397318, wt.KP)
```

위에서 적합한 코드를 입력하면 웹툰이 webtoons 폴더에 다운로드됩니다.

cf) 웹툰 태그를 생략하면 해당 웹툰이 어떤 사이트의 웹툰 id인지 자동으로 알아냅니다. 만약 몇몇 태그가 겹친다면 태그에 맞는 수를  입력하는 창에 알맞은 수를 입력하면 됩니다.

> [!WARNING]
> 웹툰을 나타내는 상수에는 문자열 값(예: 'naver_webtoon'), 전체 이름 상수 변수(예: 변수 NAVER_WEBTOON) 그리고 이를 축약한 1\~2 글자 상수 변수(예: 변수 N)가 있습니다.
> 문자열 값은 디버깅의 어려움 때문에 사용을 권하지 않으며, 1~2글자 상수 변수는 바뀔 염려가 있고 가독성 문제가 있어 웹툰을 일회성으로 다운로드 받고 싶은 경우에만 사용을 권합니다. 따라서 WebtoonScraper로 프로그램을 만들 때에는 NAVER_WEBTOON 같은 전체 이름 상수 변수를 사용하는 것을 강력히 권장합니다.

episode_no_range 파라미터를 이용하면 특정한 에피소드만 다운로드받을 수 있습니다.

```python
wt.download_webtoon(5, wt.G, episode_no_range=(1, 20))  # 1화부터 20화까지
```

이때 None을 이용하면 해당 부분의 끝부분까지 다운로드받을 것을 의미합니다.

```python
wt.download_webtoon(5, wt.G, episode_no_range=(None, 35))  # 처음부터 35화까지; (1, 35)와 같음.
wt.download_webtoon(5, wt.G, episode_no_range=(21, None))  # 21화부터 끝까지 쭉
```

merge_amount 파라미터를 이용하면 webtoon 폴더 내에 있는 모든 웹툰을 원하는 개수 만큼 묶을 수 있습니다.

```python
wt.download_webtoon(5, wt.G, merge_amount=5)  # 1~5화, 6~10화 이런 식으로 회차를 한 폴더 내로 묶어 정주행하기 편하게 함.
```

### 다운로드 주의사항

* 중간에 웹툰 다운로드가 멈춘 듯이 보여도 정상입니다. 그대로 가만히 있으면 다운로드가 다시 진행됩니다.
* 만약 작동하지 않는다면 윈도우에서 Python 3.11를 설치하고 앞의 과정을 반복해 보세요.
* 웹툰 다운로드에 실패했더라도 걱정하실 것 없습니다. 같은 코드를 다시 실행하면 처음부터 다시 받는 것이 아니라 중간부터 다시 시작합니다.

## 버프툰 다운로드하기

버프툰 다운로드 방법은 [이 문서](docs/specific_platform_download.md#버프툰-다운로드하기)를 참고하세요.

## 네이버 포스트 다운로드하기

네이버 포스트 다운로드 방법은 [이 문서](docs/specific_platform_download.md#네이버-포스트-다운로드하기)를 참고하세요.

## 레진코믹스 다운로드하기

레진코믹스 다운로드 방법은 [이 문서](docs/specific_platform_download.md#레진코믹스-다운로드하기)를 참고하세요.

## 네이버 블로그 다운로드하기

네이버 블로그 다운로드 방법은 [이 문서](docs/specific_platform_download.md#네이버-블로그-다운로드하기)를 참고하세요.

## 티스토리 다운로드하기

티스토리 다운로드 방법은 [이 문서](docs/specific_platform_download.md#티스토리-다운로드하기)를 참고하세요.

## 이 라이브러리가 다운로드 가능한 그리고 불가능한 웹툰 회차/웹툰의 종류

요약: 유료 회차를 무료로 보고 싶은 마음으로 이 라이브러리를 찾으셨다면, 애석하게도 이 라이브러리는 그런 용도가 아니라는 사실을 알려드립니다.

이 라이브러리는 많은 종류의 웹툰 다운로드를 지원하지만 어느 정도의 한계가 있습니다.

1. **비로그인 사용자에게까지 완전히 공개된 회차**: 다운로드 **가능**

1. **무료이지만 로그인이 필요한 회차**: 추가적인 절차를 거치면 **가능**

    버프툰, 레진 코믹스의 경우에는 사실상 로그인이 필수입니다. 이런 경우 별도의 절차가 필요하며, 절차를 거치면 다운로드가 가능합니다. 절차는 각각 메뉴얼을 제공하고 있습니다. 필수가 아니지만 로그인을 할 수는 있는 웹툰 플랫폼들도 있을 수 있습니다.

1. **자신이 구매한 유료 회차**: 로그인 시 기술적으로 가능하지만, 현재는 **불가능**하거나 테스트되지 않음.

    기술적으로는 가능합니다만, 현재로서는 지원할 계획이 없습니다. 필요한 경우 이슈를 생성하거나 Pull Request를 보내 주세요.

    이 라이브러리는 자신이 구매한 유료 회차가 다운로드가 가능한지에 관해 테스트해 본 적이 없습니다. 로그인을 지원하는 Scraper(버프툰, 레진코믹스 등)들에 한해 다운로드가 가능할 가능성이 있습니다.

1. **구매하지 않은 유료 회차**: 다운로드 **불가능**

    유료로 파는 자료를 (이벤트성 무료화나 3다무 등 공식적으로 허용된 방식이 아닌 경우) 무료로 열람하는 것은 거의 모든 경우에서 불법이고 불가능합니다.
    이 라이브러리는 본인이 구매하지 않은 유료 회차의 다운로드를 현재 지원하지 않고, 향후에도 지원할 계획이 없습니다.

1. **3다무, 매일+등 시간 제한이 있는 회차**: 자신이 앱으로 볼 수 있는 회차는 기술적으로 가능하지만 현재는 **불가능**, 앱으로 볼 수 없는 회차는 **불가능**

    '시간 제한이 있는 회차'는 '유료 회차'와 사실상 일치합니다. 따라서 자신이 현재 앱으로 볼 수 있는 회차는 기술적으로 가능하지만, 자신이 볼 수 없는 회차는 아예 불가능합니다. 이도 현재로서는 지원할 계획이 없습니다.

1. **성인 웹툰**: 성인 인증이 된 계정으로 로그인 시 기술적으로 가능하지만, 현재는 **불가능**하거나 테스트되지 않음.

    성인 웹툰도 별도의 절차가 필요하다는 점에서 '시간 제한이 있는 회차'의 제한과 비슷합니다. 자신이 성인이고 성인 계정으로 로그인했다면 작동할 가능성이 있지만 테스트되지 않았습니다.

## 여러 회차 하나로 묶기

1. 웹툰을 상기한 대로 다운로드받습니다.
1. 다음과 같이 코드를 짭니다.

    ```python
    from WebtoonScraper import DirectoryMerger

    fm = DirectoryMerger()
    fm.select_webtoon_and_merge_or_restore(5)
    ```

1. 다음과 같은 질문창이 나타나면 합칠 웹툰을 선택합니다. 합칠 웹툰 이름 앞에 있는 번호를 입력하면 되고, 이때 0은 따라와도 상관없습니다.(예: 1 = 01 = 001)

    ```console
    Select webtoon to merge or restore.
    1. (웹툰 이름 1)
    2. (웹툰 이름 2)
    3. (웹툰 이름 3)
    Enter number:
    ```

1. 다른 질문이 나오면 그냥 엔터를 누릅니다. 이때 오류가 난다면 제대로 된 웹툰 폴더를 선택했는지, shuffled 웹툰을 선택한 것은 아닌지 다시 한 번 확인하세요.
1. 선택한 웹툰 폴더가 'webtoon_merge' 폴더에 5화씩 묶여져 다운로드됩니다.

### 주의사항

* Merging 중 폴더가 사라지고 이미지가 폴더 밖으로 나오는데, 이는 정상 과정입니다.

## 묶인 회차 다시 원래대로 되돌리기

1. 윗글의 기능으로 묶인 회차를 준비합니다.
1. 다음과 같이 코드를 짭니다.

    ```python
    from WebtoonScraper import DirectoryMerger

    fm = DirectoryMerger()
    fm.select_webtoon_and_merge_or_restore(5)
   ```

1. 다음과 같은 질문창이 나타나면 합칠 웹툰을 선택합니다. 합칠 웹툰 이름 앞에 있는 번호를 입력하면 되고, 이때 0은 따라와도 상관없습니다.(예: '1' = '01' = '001')

    ```console
    Select webtoon to merge or restore.
    1. (웹툰 이름 1)
    2. (웹툰 이름 2)
    3. (웹툰 이름 3)
    Enter number:
    ```

1. 'webtoon' 폴더에 있던 모든 웹툰이 웹툰을 처음 다운로드했던 상태로 되돌아갑니다.

## Relese Note

2.3.2 (Dec 10, 2023): CLI에 merge 명령 추가, restore_webtoon_directory_to_directory 추가, pyproject.toml에 프로젝트 메타데이터 추가, Hits 추가, 네이버 블로그 관련 버그 수정, callback 추가, EpisodeNoRange에서 slice와 iterable도 받도록 허용, webtoon CLI 추가

2.3.1 (Dec 09, 2023): 네이버 포스트 & 네이버 블로그 버그 수정, resoup 사용, pyfilename 사용, best_challenge 관련 모듈 수정 및 seamless_redirect 추가, download_webtoons_getting_paid 관련 버그 수정, dm.select로 이름 변경 및 리팩토링, .gitignore 변경, 버전에 대한 경고 메시지

2.3.0 (Nov 22, 2023): 티스토리 추가, 코드 개선 및 리팩토링

2.2.0 (Nov 4, 2023): 네이버 블로그 추가, gitbook 추가, URL_REGEX 추가(현재는 사용처가 없지만 향후에 생길 예정), 리팩토링, 절대 경로 지원 제거

2.1.0 (Sep 24, 2023): CLI 추가, 문서 개선

2.0.2 (Sep 13, 2023): 의존성이 설치되지 않는 버그 수정

2.0.1 (Sep 10, 2023): (의존성이 설치되지 않는 버그 있음: 의존성을 직접 설치하면 문제 없음.) scrapers 폴더 미포함 버그 수정, 필요없는 주석 제거, 빠뜨렸던 의존성 추가(typing_extensions)

2.0.0 (Sep 10, 2023): (버그 있음 -- 사용하지 말 것을 권장함.) pyjsparser, async_lru 의존성 제거, 대규모 리팩토링(scraper 폴더 생성, directory_merger 리팩토링, exceptions 추가, py.typed 추가, 독스 추가, 그 외 버그 수정 등.), 레진 unshuffler 분리 및 unshuffler 버그 수정, Scraper 완전 변경, 만화경 지원 제거, async 로직에서 제거

1.3.0 (Aug 27, 2023): 카카오페이지 추가, 의존성 증가([requests-utils](https://github.com/ilotoki0804/resoup))

1.2.0 (Jul 27, 2023): 레진코믹스 추가, 의존성 증가(~~pyjsparser~~(2.0.0 버전에서 의존성에서 제거됨), Pillow)

1.1.1 (Jul 22, 2023): 내부 모듈 이름 변경, merge option 추가, abstractmethod들의 일반 구현 추가

1.0.2 (Jul 7, 2023): 대형 리팩토링, get_webtoon_platform 비동기 방식으로 속도 개선, 상대경로로 변경, 테스트 추가

1.0.1 (Jun 30, 2023): 코드 개선 및 리팩토링, api를 통한 로직으로 변경 (버그가 많기에 사용을 권장하지 않음)

1.0.0 (Jun 29, 2023): 네이버 게임 추가, FolderManager 리펙토링 및 개선, 정식 버전, docs 개선

0.1.1 (Jun 21, 2023): 네이버 포스트 추가, readme 작성, pbar 표시 내용 변경, 버그 수정

0.1.0 (Jun 19, 2023): 버프툰 추가, 빠진 부분 재추가

0.0.19.3 (Jun 18, 2023): merge 속성 추가, get_webtoon 함수로 변경

0.0.19.1: pbar에 표시되는 내용 변경, 내부적 개선

0.0.18 (Jun 7, 2023): 만화경 지원, 리팩토링됨(Scraper Abstract Base Class 추가)

0.0.17 (May 31, 2023): 웹툰즈 오리지널, 캔버스 지원

0.0.12 (May 29, 2023): 네이버 웹툰, 베스트 도전 지원
