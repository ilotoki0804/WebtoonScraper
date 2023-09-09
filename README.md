# WebtoonScraper
[![PyPI - Downloads](https://img.shields.io/pypi/dm/WebtoonScraper)](https://pypi.org/project/WebtoonScraper/)
<!-- [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) -->

최대 규모 오픈 소스 웹툰 스크래퍼입니다.

네이버 웹툰, 베스트 도전만화, 웹툰 오리지널, 웹툰 캔버스, 만화경, 버프툰, 네이버 포스트, 네이버 게임, 레진 코믹스, 카카오페이지를 지원하고,
이외에도 더 많은 웹툰을 추후에 지원할 예정입니다.

저작권과 책임에 대한 내용을 더욱 자세히 알고 싶다면 [이 문서](docs/copyright.md)를 참고해 주세요.

## 이 라이브러리가 다운로드 가능한 그리고 불가능한 웹툰의 종류
요약: 유료 회차를 무료로 보고 싶은 마음으로 이 라이브러리를 찾으셨다면, 애석하게도 이 라이브러리는 그런 용도가 아니라는 사실을 알려드립니다.

이 라이브러리는 많은 종류의 웹툰 다운로드를 지원하지만 어느 정도의 한계가 있습니다.

1. **비로그인 사용자에게까지 완전히 공개된 회차**: 다운로드 **가능**

1. **무료이지만 로그인이 필요한 회차**: 추가적인 절차를 거치면 **가능**

    버프툰, 레진 코믹스의 경우에는 사실상 로그인이 필수입니다. 이런 경우 별도의 절차가 필요하며, 절차를 거치면 다운로드가 가능합니다. 절차는 각각 메뉴얼을 제공하고 있습니다. 필수가 아니지만 로그인을 할 수는 있는 웹툰 플랫폼들도 있습니다.

1. **자신이 구매한 유료 회차**: 로그인 시 기술적으로 가능하지만, 현재는 **불가능**하거나 테스트되지 않음.

    기술적으로는 가능합니다만, 현재로서는 지원할 계획이 없습니다. 필요한 경우 이슈를 생성하거나 Pull Request를 보내 주세요.

    이 라이브러리는 자신이 구매한 유료 회차가 다운로드가 가능한지에 관해 테스트해 본 적이 없습니다. 로그인을 지원하는 Scraper(버프툰, 레진코믹스 등)들에 한해 다운로드가 가능할 가능성이 있습니다.

1. **구매하지 않은 유료 회차**: 다운로드 **불가능**

    유료로 파는 자료를 (이벤트성 무료화나 3다무 등 공식적으로 허용된 방식이 아닌 경우) 무료로 열람하는 것은 거의 모든 경우에서 불법이고 불가능합니다.
    이 라이브러리는 본인이 구매하지 않은 유료 회차의 다운로드를 현재 지원하지 않고, 향후에도 지원할 계획이 없습니다.

1. **3다무, 매일+등 시간 제한이 있는 회차**: 자신이 앱으로 볼 수 있는 회차는 기술적으로 가능하지만 현재는 **불가능**, 앱으로 볼 수 없는 회차는 **불가능**

    '시간 제한이 있는 회차'는 '유료 회차'와 사실상 일치합니다. 따라서 자신이 현재 앱으로 볼 수 있는 회차는 기술적으로 가능하지만, 자신이 볼 수 없는 회차는 아예 불가능합니다. 이도 현재로서는 지원할 계획이 없습니다.

1. **성인 웹툰**: 성인 인증이 된 계정으로 로그인 시 기술적으로 가능하지만, 현재는 **불가능**하거나 테스트되지 않음.

    성인 웹툰도 별도의 절차가 필요하다는 점에서 '시간 제한이 있는 회차'의 제한과 비슷합니다. 자신이 성인이고 성인 계정으로 접속했다면 작동할 가능성이 있지만 테스트되지 않았습니다.

# 시작하기
1. 파이썬을 설치합니다.
1. 터미널에서 다음과 같은 명령어를 실행합니다.
   ```
   pip install -U WebtoonScraper
   ```

# 네이버 웹툰, 베스트 도전만화, 웹툰 오리지널, 웹툰 캔버스, 만화경, 네이버 게임, 카카오페이지 다운로드하기
버프툰과 네이버 포스트는 아래로 가서 확인하세요.

## titleid 복사
원하는 웹툰으로 가서 titleid 또는 title_no를 복사하세요.

[**네이버 웹툰/베스트 도전** <small>예시: 위아더좀비(이명재)</small>](https://comic.naver.com):
![위아더좀비(네이버 웹툰) by 이명재](images/naver_webtoon.png)
[**웹툰 오리지널/캔버스** <small>예시: Wetermelon(Rorita)</small>](https://webtoons.com):
![Wetermelon(WEBTOON) by Rorita](images/webtoons_original.png)
[**만화경** <small>예시: 나의 여름방학(지수, 곰방)</small>](https://manhwakyung.com)
![출처: 나의 여름방학(만화경) by 지수, 곰방](images/manhwakyung.png)
[**네이버 게임 오리지널 시리즈** <small>예시: 도리도리의 게임추억(도리도리)</small>](https://game.naver.com/original_series):
![출처: 도리도리의 게임추억(네이버 게임 오리지널 시리즈) by 도리도리](images/naver_game.png)

버프툰과 네이버 포스트는 아래의 '버프툰 다운로드하기'섹션과 '네이버 포스트 다운로드하기' 섹션을 참고해 주세요.

레진코믹스와 카카오페이지 웹툰은 따로 준비된 스크린샷은 없습니다만 방법은 다른 웹툰들과 같습니다.
레진코믹스는 titleid가 문자열이라는 점에 참고하세요.

## 코드 실행
다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.

```python
# 이 라인은 꼭 포함하세요.
from WebtoonScraper import webtoon as wt

# 이 아래부터는 자신이 원하는 플랫폼 하나를 골라서 사용하면 됩니다.

# 네이버 웹툰
wt.download_webtoon(76648, wt.N)  # titleid를 여기에다 붙여넣으세요.
# 베스트 도전만화
wt.download_webtoon(763952, wt.B)  # titleid를 여기에다 붙여넣으세요.  # ! 수정
# 웹툰 오리지널
wt.download_webtoon(1435, wt.O)  # title_no를 여기에다 붙여넣으세요.
# 웹툰 캔버스
wt.download_webtoon(304446, wt.C)  # title_no를 여기에다 붙여넣으세요.
# 만화경
wt.download_webtoon(146, wt.M)  # titleid를 여기에다 붙여넣으세요. Webtoon.T 태그도 사용 가능합니다.
# 네이버 게임 오리지널 시리즈
wt.download_webtoon(5, wt.G)  # titleid를 여기에다 붙여넣으세요.
# 버프툰
cookie = 'cookie here'  # cookie를 여기에다 붙여넣으세요. 자세한 설명은 아래의 '버프툰 다운로드하기'를 참고하세요.
wt.download_webtoon(1007888, wt.BF, cookie=cookie)  # titleid를 여기에다 붙여넣으세요.
# 네이버 포스트
wt.download_webtoon((597061, 19803452), wt.P)  # seriesNo와 memberNo를 각각 붙여넣으세요. 자세한 설명은 아래의 '네이버 포스트 다운받기'를 참고하세요.
# 레진코믹스
authorization = 'authorization here'  # authorization을 여기에다 붙여넣으세요. 자세한 설명은 아래의 '레진코믹스 다운로드하기'를 참고하세요.
wt.get_webtoon('dr_hearthstone', wt.L, authorization=authorization)  # titleid를 여기에다 붙여넣으세요.
# 카카오페이지
wt.get_webtoon(53397318, wt.KP)
```

이제 웹툰이 webtoons 폴더에 다운로드됩니다.

> cf. 웹툰 태그를 생략하면 해당 웹툰이 어떤 사이트의 웹툰 id인지 자동으로 알아냅니다. 만약 몇몇 태그가 겹친다면 태그에 맞는 수를  입력하는 창에 알맞은 수를 입력하면 됩니다.

episode_no_range 파라미터를 이용하면 특정한 에피소드만 다운로드받을 수 있습니다. 
```python
wt.get_webtoon(5, wt.G, episode_no_range=(1, 20))  # 1화부터 20화까지
```
이때 None을 이용하면 해당 파라미터부터 끝까지 다운로드받을 것을 의미합니다.
```python
wt.get_webtoon(5, wt.G, episode_no_range=(None, 35))  # 처음부터 35화까지; (1, 35)와 같음.
wt.get_webtoon(5, wt.G, episode_no_range=(21, None))  # 21화부터 끝까지 쭉
```

merge 파라미터를 이용하면 webtoon 폴더 내에 있는 모든 웹툰을 원하는 개수 만큼 묶을 수 있습니다.
```python
wt.get_webtoon(5, wt.G, merge=5)  # 1~5화, 6~10화 이런 식으로 회차를 한 폴더 내로 정주행하기 편하게 함.
```

## 주의사항
* 중간에 웹툰 다운로드가 멈춘 듯이 보여도 정상입니다. 그대로 가만히 있으면 다운로드가 다시 진행됩니다.
* 만약 작동하지 않는다면 윈도우에서 Python 3.11.4을 설치하고 앞의 과정을 반복해 보세요.
* 웹툰 다운로드에 실패했더라도 걱정하실 것 없습니다. 같은 코드를 다시 실행하면 처음부터 다시 받는 것이 아니라 중간부터 다시 시작합니다.

# 버프툰 다운로드하기

## 로그인하지 않은 상태에서 웹툰 다운로드하기
로그인하지 않은 상태에서도 웹툰을 다운로드받을 수 있으나, 받을 수 있는 웹툰 수가 매우 적기에 추천하지 않습니다.

1. 웹툰 페이지에 들어가 주소창의 맨 마지막 수를 복사합니다.
2. 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.
    ```python
    from WebtoonScraper import Webtoon as wt

    wt.get_webtoon(1007888, wt.BF)  # 복사했던 수를 여기에다 붙여넣으세요.
    ```
3. 'Enter cookie of 1007888(시리즈 id) (Enter nothing to preceed without cookie)'라는 문구와 함께 입력란이 나오면 그냥 enter를 눌러줍니다.
4. 로그인하지 않고 볼 수 있는 모든 에피소드가 다운로드됩니다.

## 로그인한 상태에서 웹툰 다운로드하기
이 과정은 PC를 기준으로 설명합니다. 만약 모바일이라면 Kiwi Browser 등을 통해 다음의 과정을 수행할 수 있습니다.

1. 웹툰 페이지에 들어가 주소창의 맨 마지막 수를 복사합니다. 이 예시에서는 1007888입니다.
    ![출처: 겜덕툰(버프툰) by 돈미니](images/bufftoon1.png)
2. 로그인을 하고 f12를 누르고 네트워크 창을 연 뒤 웹툰 페이지에 들어갑니다.
    ![출처: 겜덕툰(버프툰) by 돈미니](images/bufftoon2.png)
3. 새로고침을 한 뒤 '이름'에 있는 favicon.ico 요청을 클릭하고 나온 창에 '헤더' 탭을 엽니다.
    ![img](images/bufftoon3.png)
4. 내려서 Cookie: 라고 되어 있는 모든 내용을 복사합니다.
    ![img](images/bufftoon4.png)
5. 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.
    ```python
    from WebtoonScraper import Webtoon as wt
    cookie = '두 번째로 복사했던 문자를 여기에다 붙여넣으세요.'
    wt.get_webtoon(1007888, wt.BF, cookie=cookie)  # 첫 번째로 복사했던 수를 여기에다 붙여넣으세요.
    ```
6. 로그인하면 볼 수 있는 모든 에피소드가 다운로드됩니다.

## 주의사항
* get_webtoon에서 cookie를 입력하면 자동으로 버프툰으로 인식합니다.
* favicon.ico가 요청에 뜨지 않는다면 ctrl+R을 해보고, 그래도 없다면 `필터`에서 `모두`로 설정되어 있는지 다시 확인하세요.

# 네이버 포스트 다운로드하기
1. 웹툰이 있는 페이지로 가서 주소창에서 seriesNo와 memberNo를 복사하세요. 예시에서는 각각 597061과 19803452입니다.
    ![출처: 돈미니의 겜덕겜소(네이버 포스트) by 돈미니](images/naver_post.png)
2. 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.
    ```python
    from WebtoonScraper import Webtoon as wt

    wt.get_webtoon((597061, 19803452), wt.P)  # 여기에 아까 복사한 seriesNo와 memberNo를 붙여넣으세요.
    ```
3. 만화 뷰어 앱을 통해 다운로드한 웹툰을 시청할 수 있습니다.

## 주의사항
* 가끔씩 이유 없는 오류가 발생할 수 있습니다. 그럴 때는 조금 시간이 지난 후에 다시 시도해 보세요.
* tuple를 입력하면 자동으로 포스트로 인식됩니다.

# 레진코믹스 다운로드하기
로그인하지 않은 상태에서도 웹툰을 다운로드받을 수 있으나, 받을 수 있는 에피소드의 개수가 제한된다는 점을 유의해 주십세요.
로그인하지 않은 상태이더라도 웹툰을 다운로드받을 수는 있습니다.

1. 웹툰 페이지에 들어가 주소창의 맨 마지막 문자열을 복사합니다.
2. 로그인을 하고 f12를 누르고 네트워크 창을 연 뒤 웹툰 페이지에 들어갑니다.
3. 새로고침을 한 뒤 '이름'에 있는 `balance?lezhinObjectId=...&lezhinObjectType=comic`(찾기 조금 어려울 수 있습니다.) 요청을 클릭하고 나온 창에 '헤더' 탭을 엽니다.
4. 내려서 Authorization: 이라고 되어 있는 모든 내용을 복사합니다.
5. 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.
    ```python
    from WebtoonScraper import Webtoon as wt
    authorization = '두 번째로 복사했던 문자를 여기에다 붙여넣으세요.'
    wt.get_webtoon(1007888, wt.L, authorization=authorization)  # 첫 번째로 복사했던 수를 여기에다 붙여넣으세요.
    ```
6. 로그인하면 볼 수 있는 모든 에피소드가 다운로드됩니다.

## 주의사항
* 다른 웹툰 플렛폼과는 다르게 titleid가 문자열입니다.
* 다른 웹툰 플랫폼들에 비해 다운로드 속도가 비교적 느린 편입니다.
* 일부 웹툰은 셔플링이 되어 있습니다. 따라서 웹툰을 다 다운로드받은 후 언셔플링을 하는 과정이 필요하며, 이 과정에 다소 시간이 소요된다는 점 참고 바랍니다.

# 여러 회차 하나로 묶기
1. 웹툰을 상기한 대로 다운로드받습니다.
2. 다음과 같이 코드를 짭니다.
    ```python
    from WebtoonScraper import FolderMerger

    fm = FolderMerger()
    fm.divide_all_webtoons(5)
    ```
3. webtoons 폴더에 있는 **모든** 웹툰이 'webtoon_merge' 폴더에 5화씩 묶여져 다운로드됩니다.

## 주의사항
* 시작 시 꼭 디렉토리를 선택해 주세요. 아니면 오류가 납니다.
* 작업 중간에 폴더가 사라지고 이미지가 폴더 밖으로 나오는데, 이는 정상 과정입니다.
* 너무 큰 수를 입력하면 웹툰 뷰어가 제대로 작동하지 않을 수 있음을 유의하세요.

# 묶인 회차 다시 원래대로 되돌리기
1. 윗글의 기능으로 묶인 회차를 준비합니다.
2. 다음과 같이 코드를 짭니다.
    ```python
    from WebtoonScraper import FolderMerger

    fm= FolderMerger()
    fm.restore_webtoons_in_directory()
   ```
3. 'webtoon' 폴더에 있던 모든 웹툰이 웹툰을 처음 다운로드했던 상태로 되돌아갑니다.

# Relese Note

2.0.0 (): pyjsparser 의존성 제거, 대규모 리팩토링(scraper 폴더 생성, directory_merger 리팩토링, exceptions 추가, py.typed 추가, 독스 추가, 그 외 버그 수정 등.), 레진 unshuffler 분리 및 unshuffler 버그 수정, Scraper 완전 변경, 만화경 지원 제거

1.3.0 (Aug 27, 2023): 카카오페이지 추가, 의존성 증가([requests-utils](https://github.com/ilotoki0804/requests-utils))

1.2.0 (Jul 27, 2023): 레진코믹스 추가, 의존성 증가(~~pyjsparser~~ 2.0.0 버전에서 의존성에서 제거됨, Pillow)

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
