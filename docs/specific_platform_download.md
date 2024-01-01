# 특정 플랫폼 다운로드하기

## 버프툰 다운로드하기

로그인하지 않으면 cookie를 얻을 수 없는데, 이 경우 다운로드할 수는 있지만 약 3화 정도로 다운로드받을 수 있는 웹툰이 폭이 심하게 제한됩니다. 그럼에도 쿠키 없이 다운로드하고 싶다면 아래 튜토리얼에서 쿠키와 관련된 부분을 무시하고 쿠키 인자는 넘기지 마세요.

### 로그인한 상태에서 웹툰 다운로드하기

이 과정은 PC를 기준으로 설명합니다. 만약 모바일이라면 Kiwi Browser 등을 통해 다음의 과정을 수행할 수 있습니다.

#### ID 복사

웹툰 페이지에 들어가 주소창의 맨 마지막 수를 복사합니다. 이 예시에서는 1007888입니다.

![겜덕툰(버프툰) by 돈미니](../images/bufftoon1.png)

#### cookie 찾기

**로그인을 한 후** f12를 누르고 네트워크 창을 연 뒤 웹툰 페이지에 들어갑니다.

![겜덕툰(버프툰) by 돈미니](../images/bufftoon2.png)

새로고침을 한 뒤 '이름'에 있는 favicon.ico 요청을 클릭하고 나온 창에 '헤더' 탭을 엽니다.

![img](../images/bufftoon3.png)

내려서 Cookie: 라고 되어 있는 모든 내용을 복사합니다.

![img](../images/bufftoon4.png)

#### 다운로드

다음과 같이 다운로드할 수 있습니다.

자세한 내용은 [여기](https://github.com/ilotoki0804/WebtoonScraper#WebtoonScraper-CLI로-웹툰-다운로드하기)를 참고하세요.

```console
WebtoonScraper 1007888 --cookie "...cookie here..."
```

혹은 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.

```python
from WebtoonScraper import Webtoon as wt

cookie = '두 번째로 복사했던 문자를 여기에다 붙여넣으세요.'
wt.download_webtoon(1007888, wt.BF, cookie=cookie)  # 첫 번째로 복사했던 수를 1007888의 위치에 붙여넣으세요.
```

로그인하면 볼 수 있는 모든 에피소드가 다운로드됩니다.

### 버프툰 다운로드 시 주의사항

* download_webtoon에서 cookie를 입력하면 자동으로 버프툰으로 인식합니다.
* favicon.ico가 요청에 뜨지 않는다면 ctrl+R을 해보고, 그래도 없다면 `필터`에서 `모두`로 설정되어 있는지 다시 확인하세요.

## 네이버 포스트 다운로드하기

웹툰이 있는 페이지로 가서 주소창에서 seriesNo와 memberNo를 복사하세요. 예시에서는 각각 597061과 19803452입니다.

![돈미니의 겜덕겜소(네이버 포스트) by 돈미니](../images/naver_post.png)

다음과 같이 다운로드할 수 있습니다.

자세한 내용은 [여기](https://github.com/ilotoki0804/WebtoonScraper#WebtoonScraper-CLI로-웹툰-다운로드하기)를 참고하세요.

```console
webtoon 597061,19803452 -p naver_post
```

혹은 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.

```python
from WebtoonScraper import Webtoon as wt

wt.download_webtoon((597061, 19803452), wt.P)  # 여기에 아까 복사한 seriesNo와 memberNo를 붙여넣으세요.
```

이제 만화 뷰어 앱을 통해 다운로드한 웹툰을 시청할 수 있습니다.

### 네이버 포스트 다운로드 시 주의사항

* 네이버 포스트에는 글과 그림이 같이 있을 수 있지만 이 라이브러리는 사진만들 다운로드받습니다.
* 가끔씩 이유 없는 오류가 발생할 수 있습니다. 그럴 때는 조금 시간이 지난 후에 다시 시도해 보세요.

## 레진코믹스 다운로드하기

로그인하지 않으면 bearer를 얻을 수 없는데, 이 경우 다운로드할 수는 있지만 약 1~2화 정도로 다운로드받을 수 있는 웹툰이 폭이 심하게 제한됩니다.

이 과정은 PC를 기준으로 설명합니다. 만약 모바일이라면 Kiwi Browser 등을 통해 다음의 과정을 수행할 수 있습니다.

1. 우선 레진코믹스에 로그인합니다. **로그인하지 않으면 진행할 수 없습니다.**
1. 해당 웹툰의 페이지에 들어가 주소창의 맨 마지막 문자열을 복사합니다.
1. f12를 누르고 네트워크 창을 연 뒤 웹툰 페이지에 들어갑니다.
1. 새로고침을 한 뒤 좌측 상단에 있는 검색창에 'balance'라고 검색한 뒤 `balance` 혹은 `balance?lezhinObjectId...`이라고(둘 중 무엇을 골라도 상관은 없습니다.) 되어 있는 요청을 클릭하고 나온 창에 '헤더' 탭을 엽니다.
1. "request headers"(혹은 "요청 헤더") 부분까지 내려서  `Authorization:` 이라고 되어 있는 부분을 찾고 "Bearer ..."라고 되어 있는 부분을 **'Bearer'를 포함하여** 모든 내용을 복사합니다.
1. 다음과 같이 다운로드할 수 있습니다.

    자세한 내용은 [여기](https://github.com/ilotoki0804/WebtoonScraper#WebtoonScraper-CLI로-웹툰-다운로드하기)를 참고하세요.

    ```console
    WebtoonScraper 1007888 --bearer "Bearer ..."
    ```

    혹은 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.

    ```python
    from WebtoonScraper import Webtoon as wt
    
    if __name__ == "__main__":
        bearer = '두 번째로 복사했던 문자를 여기에다 붙여넣으세요.'  # Bearer ...
        wt.download_webtoon('dr_hearthstone', wt.L, bearer=bearer)  # 첫 번째로 복사했던 수를 dr_hearthstone의 위치에 붙여넣으세요.
    ```

1. 로그인하면 볼 수 있는 모든 에피소드가 다운로드됩니다.

### 유료 회차 다운로드받기

자신이 직접 구매한 유료 회차는 다운로드 가능합니다. `get_paid_episode`를 True로 하세요.

```python
from WebtoonScraper.scrapers import LezhinComicsScraper

if __name__ == "__main__":
    bearer = 'Bearer ...'
    scraper = LezhinComicsScraper('gahu_r', bearer=bearer)  # 자신이 구매한 유료 회차가 있는 웹툰을 gahu_r의 위치에 붙여넣으세요.
    scraper.get_paid_episode = True
    scraper.download_webtoon()
```

### 성인 웹툰 다운로드하기

모든 종류의 웹툰을 다운로드받으려면 자신의 성인이어야 합니다. 만약 아닐 경우에는 어떤 방식으로든 다운로드가 지원되지 않습니다.
아래의 방식은 자신이 성인이고 이미 레진코믹스 웹/앱에서 성인 웹툰을 열람할 수 있다는 전제가 성립되어야 다운로드가 가능합니다.

쿠키를 찾는 방법은 다음과 같습니다.

1. 웹툰 페이지로 갑니다.
1. 우선 f12를 누르고 `네트워크` 탭으로 갑니다.
1. f5를 누릅니다.
1. 스크롤을 맨 위로 올려서 첫 번째 request를 클릭합니다.
1. 아래로 내려서 `요청 헤더`로 갑니다(주의: '응답 헤더'가 아닙니다!)
1. 요청 헤더에서 아래로 스크롤하다 보면 `Cookie:`라고 되어 있는 란이 뜹니다.
1. 쿠키를 복사합니다.
1. 다음과 같이 코드를 짭니다.

```python
from WebtoonScraper.scrapers import LezhinComicsScraper

if __name__ == "__main__":
    bearer = "Bearer ..."  # 얻어온 bearer를 여기에 붙여넣으세요.
    cookie = "COOKIE HERE"  # 얻어온 cookie를 여기에 붙여넣으세요.

    scraper = LezhinComicsScraper("webtoon_id", bearer=bearer, cookie=cookie)  # 자신이 구매한 유료 회차가 있는 웹툰을 webtoon_id의 위치에 붙여넣으세요.
    scraper.download_webtoon()
```

### 소장한 에피소드 고화질로 다운로드받기

이 라이브러리는 소장한 유료 에피소드에 대해서는 기본적으로 고화질 다운로드를 지원합니다. `유료 회차 다운로드받기` 파트를 참고하세요.

소장한 에피소드가 하나라도 있다면 웹툰 디렉토리 이름 뒤에 `HD`가 붙게 되는데, 만약 이것이 싫다면 `self.is_fhd_downloaded`을 `None`으로 설정하세요.

```python
from WebtoonScraper.scrapers import LezhinComicsScraper

if __name__ == "__main__":
    bearer = 'Bearer ...'
    scraper = LezhinComicsScraper('gahu_r', bearer=bearer)  # 자신이 구매한 유료 회차가 있는 웹툰을 gahu_r의 위치에 붙여넣으세요.
    scraper.get_paid_episode = True
    scraper.is_fhd_downloaded = None
    scraper.download_webtoon()
```

소장한 "무료" 에피소드를 고화질로 다운로드받으려면 다운로드 전 추가적으로 `scraper.fetch_user_infos()`를 실행해야 합니다.

```python
from WebtoonScraper.scrapers import LezhinComicsScraper

if __name__ == "__main__":
    bearer = 'Bearer ...'
    scraper = LezhinComicsScraper('gahu_r', bearer=bearer)  # 소장한 무료 에피소드가 있는 웹툰을 gahu_r의 위치에 붙여넣으세요.
    scraper.get_paid_episode = True
    scraper.fetch_user_informations()
    scraper.download_webtoon()
```

추후 버전에서는 무료 에피소드도 자동으로 고화질로 다운로드받을 수 있도록 변경될 예정입니다.

### 레진코믹스 다운로드 시 주의사항

* 다른 웹툰 플랫폼과는 다르게 titleid가 문자열입니다.
* 다른 웹툰 플랫폼들에 비해 다운로드 속도가 비교적 느린 편입니다.
* 일부 웹툰은 셔플링이 되어 있습니다. 따라서 웹툰을 다 다운로드받은 후 언셔플링을 하는 과정이 필요하며, 이 과정에 상당히 많은 시간과 컴퓨터 연산이 필요하다는 점 참고 바랍니다.
* get_paid_episode를 True로 했을 때는 다량의 경고 메시지가 뜰 수 있습니다. 정상 과정이므로 신경쓰지 않아도 됩니다.

## 네이버 블로그 다운로드하기

네이버 블로그에서 한 카테고리를 특정지으려면 blogId(영어+숫자 혼합 문자열)와 categoryNo(수)가 필요합니다.

각각의 번호는 블로그에서 확인할 수 있습니다.

이 스크래퍼는 한 카테고리 전체를 다 다운로드 받는 방식으로 작동합니다.

![이 무슨 대자연인가-고래마켓(네이버 블로그) by 상덕이](../images/naver_blog.png)

blogId와 categoryNo을 복사했다면 각각을 `(blogId, categoryNo)` 순서대로 나열한 뒤 webtoon_id 자리에 사용합니다.

```python
from WebtoonScraper import webtoon as wt

wt.download_webtoon(('bkid4', 55), wt.NB)  # 괄호로 감싸는 걸 잊지 마세요!
```

CLI로도 사용할 수 있습니다. 이때는 괄호는 선택이고 스페이스는 포함하지 말아주세요.

```console
# 기본적으로는 이렇게 사용하는 것을 추천합니다.
webtoon download bkid4,55 -p naver_blog

# 괄호는 넣어도 되고 안 넣어도 됩니다.
webtoon download (bkid4,55) -p naver_blog

# 만약 정 스페이스를 포함하고 싶다면 따옴표로 감싸주세요.
webtoon download "(bkid4, 55)" -p naver_blog

# blogId에 알파벳이 섞여있다면 상관없지만 만약 모두 숫자라면 네이버 포스트와 구분해야 하기에 따옴표나 쌍따옴표로 감싸주세요.
webtoon download '2394',55

# 하지만 플랫폼을 명시했다면 괜찮습니다.
webtoon download 2394,55 -p naver_blog
```

## 티스토리 다운로드하기

주의: 특정 티스토리 사이트는 다운로드가 되지 않을 수 있습니다. 만약 어떤 티스토리 사이트를 다운로드받는 데에 실패했다면 이슈를 열거나 이메일로 알려주세요.

우선 url에서 블로그 ID와 카테고리를 찾아냅니다.

```url
https://<블로그 ID>.tistory.com/category/<카테고리>
```

예를 들어 다음과 같은 URL에서 블로그 ID와 카테고리는 다음과 같습니다.

그런 다음 CLI에서 다음과 같이 입력하세요.

```
https://doldistudio.tistory.com/category/돌디툰
        ^^^^^^^^^^^                      ^^^^^
         블로그 ID                       카테고리
```

그런 다음 console에 다음과 같이 입력합니다. 이때 스페이스를 중간에 넣지 않도록 주의하세요. 오류가 날 수 있습니다.

```console
webtoon download doldistudio,돌디툰 -p naver_blog
```
