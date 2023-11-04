# 개발자 가이드

이 문서는 이 라이브러리가 어떻게 구성되어 있는지에 대한 가이드를 제공합니다.

## 구조

WebtoonScraper 라이브러리는 다음과 같이 구성되어 있습니다.

```path
scrapers/
└── (scrapers)
__main__.py
directory_merger.py
exceptions.py
miscs.py
py.typed
webtoon.py
```

**scrapers**에는 실제로 웹툰을 다운로드받는 역할을 하는 클래스들이 나옵니다. 뒤쪽에서 더욱 자세히 설명합니다.

**`__main__`**에는 CLI와 관련된 코드가 있습니다.

**directory_merger**는 디렉토리 관리와 관련된 사항들과 merger가 존재합니다.

**exceptions**에는 WebtoonScraper에서 사용된 예외들이 모여 있습니다.

**miscs**에는 여러 프로젝트에서 사용되어 한 모듈에 놓고 import하기 곤란한 것이나 잡다한 것들이 있습니다.

**py.typed**는 정적 타입 체커들에게 이 라이브러리가 타입 힌트를 지원한다는 것을 선언한 것입니다. 특별한 내용물은 없습니다.

**webtoon.py**는 간단하게 WebtoonScraper를 사용할 수 있도록 하는 파일이며 CLI의 근간이 됩니다.

## requests-utils

`requests-utils`는 `requests`와 `BeatifulSoup`를 간단하게 통합해서 사용할 수 있도록 만든 자작 라이브러리로 사용 방법은 매우 간단합니다. 전체 문서는 [여기](https://github.com/ilotoki0804/requests-utils)에서 확인할 수 있지만 중요한 부분만 추려서 여기에서 설명합니다.

### CustomDefaults

이 클래스는 이름 그대로 기본값들을 사용자 입맛대로 설정할 수 있도록 도와주는 클래스입니다.

예를 들어 다음과 같이 사용할 수 있습니다.

```python
from requests_utils import CustomDefaults

requests = CustomDefaults(timeout=10)
requests.get('https://www.python.org')  # timeout이 10으로 적용됨
requests.get('https://www.python.org', timeout=30)  # '기본값' 10 대신 30이 적용됨.
```

이는 header 등 한 클래스 내에서 공유되는 기본값을 불필요한 코드 없이 사용할 수 있어서 유용합니다.

하지만 이 성질 때문에 연결 관련 속성이 변경되었을 때 새로고침이 필요합니다. `self.update_requests()`로 이 작업을 수행할 수 있습니다.

```python
from WebtoonScraper.scrapers import NaverWebtoonScraper as Scraper

scraper = Scraper()
scraper.timeout = 100  # timeout이 수동으로 재설정됨.
scraper.update_requests()  # 새로고침 필요
```

### `.soup_select()`, `.soup_select_one()`

스크래핑을 하다 보면 반복되는 코드가 있습니다. 바로 다음과 같은 코드입니다.

```python
import requests
from bs4 import BeatifulSoup

response = requests.get('https://www.python.org')
soup = BeatifulSoup(response.text, 'html.parser')
selected = soup.select_one('strong')

...
```

복잡한 코드는 아니더라도 확실히 귀찮습니다. 이런 반복되는 코드를 줄일 수 있지는 않을까요?

`requests-utils` 라이브러리를 사용하면 이런 코드를 한 줄로 줄일 수 있습니다.

```python
from requests_utils import requests

selected = requests.get('https://www.python.org').soup_select_one('strong')
```

기존에 `soup.select_one`이었던 코드는 `response.soup_select_one`으로 변경되고, `soup.select`는 `response.soup_select`로 변경됩니다.

import까지 포함하면 5줄이었던 코드가 2줄로 줄었습니다. 또한 기억할 만한 것들도 줄어들었습니다.

### SoupTools

SoupTools는 그냥 'request-utils 스타일 BeatifulSoup'으로 생각하면 좋습니다.

이미 requests_utils를 import했다면 굳이 다시 BeatifulSoup를 import할 필요는 없으니 사용하는 라이브러리라고 생각해도 무리는 없습니다. 하지만 BeatifulSoup보다 조금 더 편하게 프로그래밍할 수 있는 몇 가지 편한 기능을 제공합니다.

아래에서 각각 윗줄과 아랫줄은 같은 의미의 코드입니다.

```python
from requests_utils import requests, SoupTools
from bs4 import BeautifulSoup

res = requests.get('https://www.python.org')
ready = SoupTools.from_response(res)

# BeautifulSoup
BeautifulSoup(res.text, 'html.parser').select('strong')
# souptools
ready.soup_select('strong')

# BeautifulSoup
BeautifulSoup(res.text, 'html.parser').select_one('strong')
# souptools
ready.soup_select_one('strong')

# BeautifulSoup
result = BeautifulSoup(res.text, 'html.parser').select_one('strong')
assert result is not None
# souptools
ready.soup_select_one('strong', no_empty_result=True)  # 특히 method chaining 시 편합니다.
```

string으로 된 html을 분석해야 할 때 유용합니다.
