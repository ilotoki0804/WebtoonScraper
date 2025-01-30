>[!CAUTION]
> **이 문서는 업데이트되지 않으며 과거의 정보를 포함하고 있습니다. [새 문서](https://github.com/ilotoki0804/httpc)에서 업데이트된 내용을 확인하세요.**

# 플랫폼별 다운로드 가이드

WebtoonScraper 자체에 대한 자세한 설명은 **[사용 방법](how-to-use.md)** 문서를 참고하세요.

* [플랫폼별 다운로드 가이드](#플랫폼별-다운로드-가이드)
    * [네이버 웹툰](#네이버-웹툰)
    * [레진코믹스](#레진코믹스)
        * [bearer](#bearer)
        * [`LEZHIN_BEARER` 환경 변수](#lezhin_bearer-환경-변수)
        * [cookie](#cookie)
        * [다운로드](#다운로드)
        * [언셔플링](#언셔플링)
        * [기타 옵션들](#기타-옵션들)
    * [네이버 웹툰 글로벌 (webtoons.com)](#네이버-웹툰-글로벌-webtoonscom)
    * [버프툰](#버프툰)
        * [쿠키 얻기](#쿠키-얻기)
        * [다운로드](#다운로드-1)
    * [네이버 포스트](#네이버-포스트)
    * [네이버 게임](#네이버-게임)
    * [카카오페이지](#카카오페이지)
    * [네이버 블로그](#네이버-블로그)
    * [티스토리](#티스토리)
    * [카카오 웹툰](#카카오-웹툰)
    * [투믹스](#투믹스)
        * [쿠키 얻기](#쿠키-얻기-1)
        * [다운로드](#다운로드-2)

## 네이버 웹툰

다음과 같은 명령어로 다운로드가 가능합니다.

```console
webtoon download "https://comic.naver.com/webtoon/list?titleId=819217"
```

파이썬 스크립트로는 다음과 같습니다.

```python
from WebtoonScraper.scrapers import NaverWebtoonScraper

scraper = NaverWebtoonScraper.from_url("https://comic.naver.com/webtoon/list?titleId=819217")
scraper.download_webtoon()
```

## 레진코믹스

레진코믹스에서 웹툰을 다운로드하기 위해서는 bearer와 쿠키가 필요한데,
bearer는 필수로 요구되며, 성인 웹툰 다운로드 시에는 쿠키가 추가로 필요합니다.

### bearer

> [!WARNING]
> bearer는 쿠키와 달리 한 계정에 귀속되며 바뀌지 않습니다. 따라서 유출되지 않도록 특히나 주의해 주세요.

bearer를 얻는 방법은 다음과 같습니다.

1. [이 링크](https://htmlpreview.github.io/?https://github.com/ilotoki0804/WebtoonScraper/blob/main/docs/get-bearer.html)로 가세요(아직은 가지 마시고 설명을 좀 더 들으세요).
1. 해당 웹페이지에 링크가 하나 있을 텐데, 그 링크를 북마크바로 드래그하세요. 만약 북마크바가 보이지 않을 시 `ctrl+shift+B`를 이용해 보이게 하세요. 그러면 북마크에 `get bearer`라는 이름의 북마크가 하나 생성이 될 것입니다.
1. [이 링크](https://www.lezhin.com/ko/help#?faq=common&notice=serial)(메인 페이지에서는 사용할 수 없으니 꼭 이 링크로 가세요!)로 간 뒤 **로그인하세요**.
1. 해당 북마크를 클릭하세요.
1. 그러면 `here is the bearer string`이라는 안내 메시지와 함께 아래에 쿠키가 뜰 것입니다. 복사하세요.

### `LEZHIN_BEARER` 환경 변수

`LEZHIN_BEARER` 환경 변수를 설정할 경우 해당 환경 변수 값이 bearer 값으로 설정됩니다.
만약 다른 bearer값을 사용하고 싶은 경우에는 직접 bearer를 제공하면 됩니다.

### cookie

쿠키는 성인 웹툰을 다운로드받을 때만 경우에만 필요합니다.

[쿠키를 얻는 방법](how-to-use.md#cookie) 링크를 확인하세요.

### 다운로드

웹툰은 다음과 같은 방식으로 다운로드할 수 있습니다.

CLI의 경우:

```console
echo 웹툰 "https://www.lezhin.com/ko/comic/dr_hearthstone"을 다운로드받는 경우

echo 일반 웹툰의 경우 (쿠키가 필요하지 않음)
webtoon download "https://www.lezhin.com/ko/comic/dr_hearthstone" --options bearer="<얻은 bearer>"
echo 성인 웹툰의 경우 (쿠키도 필요함)
webtoon download "https://www.lezhin.com/ko/comic/dr_hearthstone" --options bearer="<얻은 bearer>" --cookie "<얻은 쿠키>"
```

*이전 버전(WebtoonScraper 3)과는 bearer를 제공하는 방식이 다르니 주의하세요.*

파이썬 스크립트의 경우:

```python
from WebtoonScraper.scrapers import LezhinComicsScraper

scraper = LezhinComicsScraper.from_url(
    "https://www.lezhin.com/ko/comic/dr_hearthstone",
    bearer="<얻은 bearer>",
    cookie="<얻은 쿠키(성인 웹툰 다운로드 시에만 필요)>",
)
scraper.download_webtoon()
```

### 언셔플링

레진코믹스의 일부 웹툰에는 셔플링이 적용되어 있습니다.
셔플된 이미지는 25개로 분할하여 무작위로 섞여 있습니다.
이때 섞인 이미지를 사람이 볼 수 있는 형태로 전환하는 데에 연셔플링이 활용됩니다.

언셔플링은 웹툰을 다운로드받은 동시에 **자동으로** 진행됩니다.
이 작업은 시간이 오래 걸리고 컴퓨팅 파워를 많이 사용합니다.
따라서 기기가 버벅일 수 있으며 끝날 때까지 조금 참을성 있게 기다려야 합니다.

언셔플링이 끝나면 `웹툰 이름(웹툰 id, shuffled)`로 되어 있는 웹툰 파일과 `웹툰 이름(웹툰 id)`로 되어 있는 웹툰 파일 두 개가 생성되는데, 그중에서 `shuffled`가 붙지 **않은** 쪽이 정상 웹툰 파일입니다.

### 기타 옵션들

다음의 옵션들은 `--options` 뒤에 추가해 레진코믹스 다운로더의 행동을 커스텀할 수 있습니다.

* `unshuffle=false`: 언셔플을 할지 안 할지 결정합니다. 기본적으로 하는 것으로 설정되어 있으며 `unshuffle=false` 옵션을 추가할 경우 언셔플 없이 웹툰 다운로드를 끝낼 수 있습니다.
* `delete-shuffled=true`: 웹툰 다운로드한 뒤 발생하는 `shuffled` 파일을 지우는 것을 설정할 수 있습니다. 기본값은 지우지 않고 유지하는 것입니다.
* `download-paid=true`: 구매한 에피소드를 추가로 다운로드합니다. 기본값은 구매가 필요하지 않은 무료 회차만 다운로드하는 것입니다.
* `bearer="Bearer ..."`: bearer를 설정합니다. 필수적으로 요구됩니다. 설명은 [여기](#bearer)를 참고하세요.
* `thread-number=<자연수>`: 언셔플시 사용될 프로세스 개수를 결정합니다. 기본값은 전체 스레드 개수의 반입니다. `1`이면 멀티프로세싱을 사용하지 않습니다.

## 네이버 웹툰 글로벌 (webtoons.com)

다음과 같은 명령어로 다운로드가 가능합니다.

```console
webtoon download "https://www.webtoons.com/en/fantasy/the-top-dungeon-farmer/list?title_no=5656"
```

## 버프툰

### 쿠키 얻기

쿠키가 없으면 다운로드를 진행할 수 없습니다.
[쿠키를 얻는 방법](how-to-use.md#cookie)을 참고하세요.

### 다운로드

다음과 같은 명령어로 다운로드가 가능합니다.

```console
webtoon download "https://bufftoon.plaync.com/series/1007888" --cookie "<YOUR COOKIE HERE 쿠키를 여기에 붙여넣으세요>"
```

## 네이버 포스트

다음과 같은 명령어로 다운로드가 가능합니다.

```console
webtoon download "https://m.post.naver.com/my/series/detail.naver?seriesNo=648552&memberNo=3395565"
```

## 네이버 게임

다음과 같은 명령어로 다운로드가 가능합니다.

```console
webtoon download "https://game.naver.com/original_series/5"
```

## 카카오페이지

다음과 같은 명령어로 다운로드가 가능합니다.

```console
webtoon download "https://page.kakao.com/content/53397318"
```

## 네이버 블로그

다음과 같은 명령어로 다운로드가 가능합니다.

```console
webtoon download "https://m.blog.naver.com/bkid4?categoryNo=55"
```

## 티스토리

다음과 같은 명령어로 다운로드가 가능합니다.

```console
webtoon download "https://doldistudio.tistory.com/category/진돌만화"
```

특정 티스토리 사이트는 다운로드가 되지 않을 수 있습니다. 만약 어떤 티스토리 사이트를 다운로드받는 데에 실패했다면 이슈를 열어주세요.

## 카카오 웹툰

다음과 같은 명령어로 다운로드가 가능합니다.

```console
webtoon download "https://webtoon.kakao.com/content/%EB%B6%80%EA%B8%B0%EC%98%81%ED%99%94/2343"
```

## 투믹스

### 쿠키 얻기

쿠키가 없으면 다운로드를 진행할 수 없습니다.
[쿠키를 얻는 방법](how-to-use.md#cookie)을 참고하세요.

### 다운로드

다음과 같은 명령어로 다운로드가 가능합니다.

```console
webtoon download "https://www.toomics.com/webtoon/episode/toon/1234" --cookie "<YOUR COOKIE HERE 쿠키를 여기에 붙여넣으세요>"
```
