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

* `scrapers`에는 실제로 웹툰을 다운로드받는 역할을 하는 클래스들이 나옵니다. `J_lezhin_unshuffler`나 `K_kakaopage_queries`와 같이 스크래퍼는 아니지만 스크래퍼와 관련이 있는 모듈들도 이 파일 안에 있을 수 있습니다. 뒤쪽에서 더욱 자세히 설명합니다.

* `__main__`에는 CLI와 관련된 코드가 있습니다.

* `directory_merger`는 디렉토리 관리와 관련된 사항들과 merger가 존재합니다.

* `exceptions`에는 WebtoonScraper에서 사용된 예외들이 모여 있습니다.

* `miscs`에는 여러 프로젝트에서 사용되어 한 모듈에 놓고 import하기 곤란한 것이나 잡다한 것들이 있습니다.

* `py.typed`는 정적 타입 체커들에게 이 라이브러리가 타입 힌트를 지원한다는 것을 선언한 것입니다. 특별한 내용물은 없습니다.

* `webtoon.py`는 간단하게 WebtoonScraper를 사용할 수 있도록 하는 파일이며 CLI의 근간이 됩니다.

## resoup

`resoup`는 `requests`와 `BeatifulSoup`를 간단하게 통합해서 사용할 수 있도록 만든 자작 라이브러리로 사용 방법은 requests와 호환되기에 매우 간단합니다. 전체 문서는 [여기](https://github.com/ilotoki0804/resoup)에서 확인할 수 있습니다.
