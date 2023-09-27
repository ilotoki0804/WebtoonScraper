# 버프툰 다운로드하기
로그인하지 않으면 cookie를 얻을 수 없는데, 이 경우 다운로드할 수는 있지만 약 3화 정도로 다운로드받을 수 있는 웹툰이 폭이 심하게 제한됩니다.

다운로드 방법은 [여기](https://github.com/ilotoki0804/WebtoonScraper#WebtoonScraper-CLI로-웹툰-다운로드하기)를 참고하세요.

## 로그인한 상태에서 웹툰 다운로드하기
이 과정은 PC를 기준으로 설명합니다. 만약 모바일이라면 Kiwi Browser 등을 통해 다음의 과정을 수행할 수 있습니다.

### ID 복사
웹툰 페이지에 들어가 주소창의 맨 마지막 수를 복사합니다. 이 예시에서는 1007888입니다.
    ![겜덕툰(버프툰) by 돈미니](../images/bufftoon1.png)

### cookie 찾기
**로그인을 후** f12를 누르고 네트워크 창을 연 뒤 웹툰 페이지에 들어갑니다.
    ![겜덕툰(버프툰) by 돈미니](../images/bufftoon2.png)
새로고침을 한 뒤 '이름'에 있는 favicon.ico 요청을 클릭하고 나온 창에 '헤더' 탭을 엽니다.
    ![img](../images/bufftoon3.png)
내려서 Cookie: 라고 되어 있는 모든 내용을 복사합니다.
    ![img](../images/bufftoon4.png)

### 다운로드
다음과 같이 다운로드할 수 있습니다.

자세한 내용은 [여기](https://github.com/ilotoki0804/WebtoonScraper#WebtoonScraper-CLI로-웹툰-다운로드하기)를 참고하세요.
```
WebtoonScraper 1007888 --cookie "...cookie here..."
```

혹은 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.
```python
from WebtoonScraper import Webtoon as wt

cookie = '두 번째로 복사했던 문자를 여기에다 붙여넣으세요.'
wt.get_webtoon(1007888, wt.BF, cookie=cookie)  # 첫 번째로 복사했던 수를 1007888의 위치에 붙여넣으세요.
```
로그인하면 볼 수 있는 모든 에피소드가 다운로드됩니다.

## 주의사항
* get_webtoon에서 cookie를 입력하면 자동으로 버프툰으로 인식합니다.
* favicon.ico가 요청에 뜨지 않는다면 ctrl+R을 해보고, 그래도 없다면 `필터`에서 `모두`로 설정되어 있는지 다시 확인하세요.

# 네이버 포스트 다운로드하기
웹툰이 있는 페이지로 가서 주소창에서 seriesNo와 memberNo를 복사하세요. 예시에서는 각각 597061과 19803452입니다.
![출처: 돈미니의 겜덕겜소(네이버 포스트) by 돈미니](../images/naver_post.png)

다음과 같이 다운로드할 수 있습니다.

자세한 내용은 [여기](https://github.com/ilotoki0804/WebtoonScraper#WebtoonScraper-CLI로-웹툰-다운로드하기)를 참고하세요.
```
WebtoonScraper 597061,19803452
```

혹은 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.
```python
from WebtoonScraper import Webtoon as wt

wt.get_webtoon((597061, 19803452), wt.P)  # 여기에 아까 복사한 seriesNo와 memberNo를 붙여넣으세요.
```
3. 만화 뷰어 앱을 통해 다운로드한 웹툰을 시청할 수 있습니다.

## 주의사항
* 가끔씩 이유 없는 오류가 발생할 수 있습니다. 그럴 때는 조금 시간이 지난 후에 다시 시도해 보세요.
* tuple를 입력하면 자동으로 포스트로 인식됩니다.

# 레진코믹스 다운로드하기
로그인하지 않으면 authkey를 얻을 수 없는데, 이 경우 다운로드할 수는 있지만 약 1~2화 정도로 다운로드받을 수 있는 웹툰이 폭이 심하게 제한됩니다.

이 과정은 PC를 기준으로 설명합니다. 만약 모바일이라면 Kiwi Browser 등을 통해 다음의 과정을 수행할 수 있습니다.

1. 우선 레진코믹스에 로그인합니다. **로그인하지 않으면 진행할 수 없습니다.**
1. 해당 웹툰의 페이지에 들어가 주소창의 맨 마지막 문자열을 복사합니다.
1. f12를 누르고 네트워크 창을 연 뒤 웹툰 페이지에 들어갑니다.
1. 새로고침을 한 뒤 좌측 상단에 있는 검색창에 'balance'라고 검색한 뒤 `balance` 혹은 `balance?lezhinObjectId...`이라고(둘 중 무엇을 골라도 상관은 없습니다.) 되어 있는 요청을 클릭하고 나온 창에 '헤더' 탭을 엽니다.
1. "request headers"(혹은 "요청 헤더") 부분까지 내려서  `Authorization:` 이라고 되어 있는 부분을 찾고 "Bearer ..."라고 되어 있는 부분을 **'Bearer'를 포함하여** 모든 내용을 복사합니다.
1. 다음과 같이 다운로드할 수 있습니다.

    자세한 내용은 [여기](https://github.com/ilotoki0804/WebtoonScraper#WebtoonScraper-CLI로-웹툰-다운로드하기)를 참고하세요.
    ```
    WebtoonScraper 1007888 --authkey "Bearer ..."
    ```

    혹은 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.
    ```python
    from WebtoonScraper import Webtoon as wt
    authkey = '두 번째로 복사했던 문자를 여기에다 붙여넣으세요.'  # Bearer ...
    wt.get_webtoon('dr_hearthstone', wt.L, authkey=authkey)  # 첫 번째로 복사했던 수를 dr_hearthstone의 위치에 붙여넣으세요.
    ```
1. 로그인하면 볼 수 있는 모든 에피소드가 다운로드됩니다.

## 유료 회차 다운로드받기

자신이 직접 구매한 유료 회차를 다운로드받을 때는 `get_paid_episode`를 True로 하세요.

```python
from WebtoonScraper.scrapers import LezhinComicsScraper

authkey = ''
scraper = LezhinComicsScraper('dr_hearthstone', authkey=authkey)
scraper.get_paid_episode = False
scraper.download_webtoon()
```

## 주의사항
* 다른 웹툰 플랫폼과는 다르게 titleid가 문자열입니다.
* 다른 웹툰 플랫폼들에 비해 다운로드 속도가 비교적 느린 편입니다.
* 일부 웹툰은 셔플링이 되어 있습니다. 따라서 웹툰을 다 다운로드받은 후 언셔플링을 하는 과정이 필요하며, 이 과정에 상당히 많은 시간과 컴퓨터 연산이 필요하다는 점 참고 바랍니다.
* get_paid_episode를 True로 했을 때는 다량의 경고 메시지가 뜰 수 있습니다. 정상 과정이므로 신경쓰지 않아도 됩니다.
