# 파이썬으로 사용하기

## `WebtoonScraper.webtoon` 모듈 사용

`webtoon`모듈은 스크래퍼를 더욱 간단하게 사용할 수 있도록 만든 사용자를 위한 모듈이며, 이를 이용하면 스크래퍼에 쉽게 접근할 수 있습니다.

웬만한 필요한 기능은 전부 지원하지만 고급 설정이 필요하다면(커스텀 timeout이나 tqdm 사용하지 않기 등.) 스크래퍼를 직접 사용해야 합니다.

이 모듈을 import할 때는 `wt`으로 줄여서 import하는 것을 권장합니다.

```python
from WebtoonScraper import webtoon as wt
import WebtoonScraper.webtoon as wt  # matplotlib.pyplot처럼 묶어서 import하더라도 문제는 없습니다.
```

`webtoon`이나 `WebtoonScraper.webtoon`으로 import한다면 플랫폼명을 사용해야 할 때 너무 길어질 수 있기 때문입니다. 예를 들어 플랫폼 이름을 사용할 때 길어질 수 있기 때문입니다. `wt.N` 대신 `WebtoonScraper.webtoon.NAVER_WEBTOON`을 사용한다면 조금 보기 어렵겠죠?

하지만 한두 번 사용되는 코드가 아닌 다른 코드에 결합하여 사용되는 경우 `webtoon` 이름 자체로 사용해도 문제는 없습니다.

웹툰을 다운로드할 때는 다음과 같은 코드를 사용할 수 있습니다.

```python
from WebtoonScraper import webtoon as wt

wt.download_webtoon(766648, wt.N)  # 네이버 웹툰에서 다운로드. 웹툰 ID를 처음으로 입력하세요.
wt.download_webtoon(766648, wt.NAVER_WEBTOON)  # 풀네임으로 사용하는 것이 편하다면 사용하세요.
wt.download_webtoon(766648)  # 플랫폼을 입력하지 않으면 자동으로 플랫폼을 유추합니다.
# (오류) wt.download_webtoon('766648')  # 잘못된 타입을 입력하지 마세요. 다운로드에 실패할 수 있습니다.

# 네이버 포스트를 비롯한 몇몇 플랫폼들에서는 정수가 아닌 특이한 타입을 사용할 수 있습니다.
# 자세한 내용은 문서를 참고하세요.
wt.download_webtoon((597061, 19803452), wt.NAVER_POST)  # 네이버 포스트
# 레진코믹스. 레진코믹스는 authkey를 포함해야 합니다. 자세한 사항은 문서를 확인하세요.
wt.download_webtoon('dr_hearthstone', wt.L, authkey='...')
wt.download_webtoon(('dpk58172', 24), wt.B)  # 네이버 블로그

# 이런 특이한 타입들도 맨 처음에 설명한 바와 같이 플랫폼을 생략할 수 있습니다.
wt.download_webtoon((597061, 19803452))  # 네이버 포스트. 괄호(튜플)를 입력해야 한다는 점을 절대 잊지 마세요!
wt.download_webtoon('dr_hearthstone', authkey='...')  # 레진코믹스
wt.download_webtoon(('dpk58172', 24))  # 네이버 블로그. 괄호(튜플)를 입력해야 한다는 점을 절대 잊지 마세요!

# 다음과 같은 기능들도 존재합니다.

# 웹툰을 모두 다운로드한 뒤 설정한 회차만큼 묶어 한 회차에 보관합니다.
# 웹툰을 몰아볼 때 유용합니다.
wt.download_webtoon(766648, wt.N, merge_amount=5)

# 어느 디렉토리에 다운로드받을지 결정합니다. 
wt.download_webtoon(766648, download_directory='webtoon')

# 에피소드를 나열합니다.
wt.download_webtoon(766648, is_list_episodes=True)
# 어디부터 어디까지 다운로드 받을 지 결정합니다. 이 경우에는 2번부터 끝까지 다운로드받습니다.
wt.download_webtoon(766648, episode_no_range=(2, None))

# 레진코믹스는 자신이 구매한 유료 회차에 한해 다운로드 받을 수 있는 기능이 존재합니다.
wt.download_webtoon('dr_hearthstone', wt.L, authkey='...', get_paid_episode=True)

# 기능을 중첩해서 사용할 수도 있습니다.
wt.download_webtoon('dr_hearthstone', wt.L, merge_amount=5, authkey='...', episode_no_range=(2, None), get_paid_episode=True)
# 하지만 is_list_episodes는 예외입니다.
# is_list_episodes는 merge_amount, episode_no_range, download_directory, get_paid_episode와 같이 사용할 수 없거나 무시됩니다.
wt.download_webtoon('dr_hearthstone', wt.L, is_list_episodes=True)
```

## 플랫폼과 플랫폼 선택기

이 라이브러리는 다양한 웹툰 플랫폼을 지원하고 있습니다.

각각의 플랫폼에는 해당 플랫폼을 위한 스크래퍼가 존재하고, 이는 `scrapers` 모듈 안에 있습니다.

### 플랫폼 이름

각각의 웹툰 플랫폼에는 `webtoon` 모듈에서 사용할 수 있는 이름들이 있습니다.

각각의 이름은 다음과 같습니다.

<table>
<thead>
  <tr>
    <th>플랫폼명</th>
    <th>약칭 변수</th>
    <th>풀네임 변수</th>
    <th>저장된 값</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>네이버 웹툰</td>
    <td>N</td>
    <td>NAVER_WEBTOON</td>
    <td>'naver_webtoon'</td>
  </tr>
  <tr>
    <td>베스트 도전</td>
    <td>B</td>
    <td>BEST_CHALLENGE</td>
    <td>'best_challenge'</td>
  </tr>
  <tr>
    <td>Webtoons 오리지널</td>
    <td>OR</td>
    <td>ORIGINALS</td>
    <td>'originals'</td>
  </tr>
  <tr>
    <td>Webtoons 캔버스</td>
    <td>C</td>
    <td>CANVAS</td>
    <td>'canvas'</td>
  </tr>
  <tr>
    <td>버프툰</td>
    <td>BF</td>
    <td>BUFFTOON</td>
    <td>'bufftoon'</td>
  </tr>
  <tr>
    <td>네이버 포스트(사진)</td>
    <td>P</td>
    <td>NAVER_POST</td>
    <td>'naver_post'</td>
  </tr>
  <tr>
    <td>네이버 게임 오리지널 시리즈(사진)</td>
    <td>G</td>
    <td>NAVER_GAME</td>
    <td>'naver_game'</td>
  </tr>
  <tr>
    <td>레진코믹스</td>
    <td>L</td>
    <td>LEZHIN</td>
    <td>'lezhin'</td>
  </tr>
  <tr>
    <td>카카오 페이지 웹툰</td>
    <td>KP</td>
    <td>KAKAOPAGE</td>
    <td>'kakaopage'</td>
  </tr>
  <tr>
    <td>네이버 블로그(사진)</td>
    <td>NB</td>
    <td>NAVER_BLOG</td>
    <td>'naver_blog'</td>
  </tr>
</tbody>
</table>
* (사진)이라고 괄호 표시 되어 있는 것은 글과 사진이 혼합된 플랫폼일 경우 사진 다운로드만을 지원한다는 의미입니다.

\* 순서가 사전순이 아닌 이유가 궁금하실 수도 있는데요, 각 순서는 WebtoonScraper에서 지원을 시작한 순서입니다.

이 값들은 모두 같은 값을 의미하며, 다음과 같은 쓸모가 있습니다.

#### 약칭 변수

CLI 등에서 한 번만 사용하고 말 코드를 짤 때 간단하게 사용할 수 있도록 만든 변수입니다.

**다른 프로그램 내에서 쓰는 등 코드가 여러 번 쓰이는 환경에서는 사용하지 마세요.**

예시는 다음과 같습니다.

```console
~ $ # CLI에서의 사용
~ $ python
Python 3.11.6 ...
Type "help", "copyright", "credits" or "license" for more information.
>>> from WebtoonScraper import webtoon as wt
>>> wt.download_webtoon(
...     809590,  # 웹툰 ID
...     wt.N  # 웹툰 약칭 변수는 이런 식으로 사용됩니다. (* wt.N: 네이버 웹툰의 약칭 변수)
... )
(다운로드 진행됨...)
```

> [!WARNING]
> 이러한 약칭 변수는 WebtoonScraper에 CLI가 없을 때 만들어졌습니다. 하지만 최신 버전에서는 CLI가 존재하니 만약 CLI에서 사용할 때는 약칭 변수 대신 CLI를 사용하는 것을 권합니다.
