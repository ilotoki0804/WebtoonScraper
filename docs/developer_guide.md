# 개발자 가이드

이 문서는 이 라이브러리가 어떻게 구성되어 있는지에 대한 가이드를 제공합니다.

## 구조

WebtoonScraper 라이브러리는 다음과 같이 구성되어 있습니다.

```path
scrapers/
├── __init__.py
└── (scrapers and the others)
__main__.py
directory_merger.py
exceptions.py
miscs.py
py.typed
webtoon.py
```

* `scrapers`에는 실제로 웹툰을 다운로드받는 역할을 하는 클래스들이 나옵니다. `J_lezhin_unshuffler`나 `K_kakaopage_queries`와 같이 스크래퍼는 아니지만 특정 스크래퍼와 관련이 있는 모듈들도 이 파일 안에 있을 수 있습니다. 뒤쪽에서 더욱 자세히 설명합니다.

* `__main__`에는 CLI와 관련된 코드가 있습니다.

* `directory_merger`는 디렉토리 관리와 관련된 사항들과 merger가 존재합니다.

* `exceptions`에는 WebtoonScraper에서 사용된 예외들이 모여 있습니다.

* `miscs`에는 여러 프로젝트에서 사용되어 한 모듈에 놓고 import하기 곤란한 것이나 잡다한 것들이 있습니다.

* `py.typed`는 정적 타입 체커들에게 이 라이브러리가 타입 힌트를 지원한다는 것을 선언한 것입니다. 특별한 내용물은 없습니다.

* `webtoon.py`는 간단하게 WebtoonScraper를 사용할 수 있도록 하는 파일이며 CLI의 근간이 됩니다.

## hxsoup

httpx는 requests와 많은 부분 호환되지만 async 지원 등 더욱 발전된 기능을 가지고 있는 라이브러리입니다. `hxsoup`는 이러한 `httpx`와 `BeatifulSoup`를 간편하게 사용할 수 있도록 통합해서 사용할 수 있도록 만든 자작 라이브러리로 사용 방법은 httpx와 호환되기에 매우 간단합니다. 전체 문서는 [여기](https://github.com/ilotoki0804/hxsoup)에서 확인할 수 있습니다.

## 스크래퍼의 구조

모든 웹툰 스크래퍼는 `WebtoonScraper.scrapers.Scraper`을 상속합니다. 해당 클래스에는 기본적인 기능들이 마련되어 있으며, 만약 새로운 웹툰 스크래퍼를 만들고 싶다면 필수적으로 3가지의 메소드를 override해야 하고, 선택적으로 서너 개를 더 override할 수 있습니다.

* fetch_webtoon_information: 필수적으로 override되어야 합니다. 이 함수의 결과로는 최소한 self.webtoon_thumbnail_url(썸내일 URL)과 self.title(웹툰 제목)이 생성되어야 합니다. `reload_manager` 데코레이터로 반드시 감싸야 합니다.
* fetch_episode_informations: 필수적으로 override되어야 합니다. 이 함수는 최소한 self.episode_titles(각 에피소드의 이름, 리스트), self.episode_ids(각 에피소드의 ID)가 생성되어야 합니다. `reload_manager` 데코레이터로 반드시 감싸야 합니다.
* get_episode_image_urls: 필수적으로 override되어야 합니다. 이 함수는 episode_no를 인자로 받아 이미지 URL들을 반환합니다.

위 세 개를 구현하면 기본적으로 작동하게 되어 있습니다. 만약 마음에 들지 않는 동작이 있거나 더 간편하게 사용하기 위해서는 다음과 같은 기능을 추가적으로 구현할 수 있습니다.

* \_\_init__: 만약 웹툰 플랫폼이 추가적인 인증을 요구한다면 사용하세요.
* get_webtoon_directory_name: 웹툰 디렉토리의 이름을 만듭니다. 만약 웹툰 ID가 단순한 수나 문자열이 아닐 때 사용하면 좋습니다.
* callback: 추가적인 콜백이 있다면 사용하세요.
* get_informations: information.json에 더 추가할 내용이 있다면 추가하세요.

### 앞 알파벳의 의미

스크래퍼들의 파일 앞에는 알파벳이 있습니다. 이는 스크래퍼가 구현된 순서를 의미하며, 그 이상의 의미는 없습니다.
