# 개발자 가이드

이 문서는 WebtoonScraper의 구조를 알고 싶거나 기여하고 싶은 개발자들을 대상으로 이 프로젝트에 대한 상세한 설명을 제공합니다.

## 구조

WebtoonScraper 프로젝트의 전체 구조는 다음과 같이 구성되어 있습니다.

```path
WebtoonScraper/
├── scarapers/
│   ├── __init__.py
│   └── (scrapers and the others)
├── __init__.py
├── __main__.py
├── directory_merger.py
├── exceptions.py
├── miscs.py
├── py.typed
├── webtoon_viewer.py
└── webtoon.py
.gitignore
build.py
LICENSE
poetry.lock
pyinstaller.py
pyproject.toml
README.md
```

### 루트 디렉토리

중요한 파일 위주로 설명하겠습니다.

* `LICENSE`: WebtoonScraper의 라이선스가 명시되어 있습니다. 이 프로젝트는 Apache 2.0으로 공유됩니다.
* `pyinstaller.py`: PyInstaller로 컴파일될 때 CLI 환경을 결정합니다.
* `pyproject.toml`: 프로젝트의 여러가지 설정과 속성이 정의되어 있습니다.
* `README.md`: WebtoonScraper에 대한 설명이 적혀 있습니다. 참고로 빌드에 직접적으로 사용되지 않습니다.
* `build.py`: 여러가지 빌드에 필요한 것들을 정리하고 README를 해석해 README_build로 만들어 해당 파일을 PyPI 릴리즈에 적용합니다.

### `WebtoonScraper` 디렉토리

`WebtoonScraper` 디렉토리는 WebtoonScraper의 본격적인 코드가 모여 있는 디렉토리입니다.

* `scrapers`: 웹툰을 다운로드하는 스크래퍼들이 모여 있는 디렉토리입니다.
* `__init__`: WebtoonScraper를 import했을 때 자동으로 초기화되는 코드를 관리하고 사용자가 편하게 코드를 접근할 수 있도록 합니다.
* `__main__`: CLI와 관련된 코드가 있습니다.
* `directory_merger`: 디렉토리 관리와 관련된 사항들과 모아서 보기 관련 기능들이 존재합니다.
* `exceptions`: WebtoonScraper에서 사용되는 모든 커스텀 예외들이 정의되어 있습니다.
* `misc`(miscellaneous): 여러 프로젝트에서 사용되어 한 모듈에 놓고 import하기 곤란한 것이나 잡다한 것들이 있습니다.
* `py.typed`: 정적 타입 체커들에게 이 패키지가 타입 힌트를 지원한다는 것을 선언한 것입니다. 특별한 내용물은 없습니다.
* `webtoon`: CLI에서 사용되는 코드 중 웹툰과 관련된 실재적인 코드가 모여 있습니다.

### 스크래퍼 파일들의 앞 수의 의미

스크래퍼들의 파일 앞에는 수가 있습니다. 이는 스크래퍼가 구현된 순서를 의미합니다.

## hxsoup

httpx는 requests와 많은 부분 호환되지만 async 지원 등 더욱 발전된 기능을 가지고 있는 패키지입니다. `hxsoup`는 이러한 `httpx`와 `BeatifulSoup`를 간편하게 사용할 수 있도록 통합해서 사용할 수 있도록 만든 자작 패키지로 사용 방법은 httpx와 호환되기에 매우 간단합니다. 전체 문서는 [여기](https://github.com/ilotoki0804/hxsoup)에서 확인할 수 있습니다.

## 스크래퍼의 구조

모든 웹툰 스크래퍼는 `WebtoonScraper.scrapers.Scraper`을 상속합니다. 해당 클래스에는 기본적인 기능들이 마련되어 있으며, 만약 새로운 웹툰 스크래퍼를 만들고 싶다면 필수적으로 3가지의 메소드를 구현해야 하고, 선택적으로 서너 개를 더 override할 수 있습니다.

* `fetch_webtoon_information`: 필수적으로 구현되어야 합니다. 이 함수의 결과로는 최소한 self.webtoon_thumbnail_url(썸네일 URL)과 self.title(웹툰 제목)이 생성되어야 합니다. `reload_manager` 데코레이터로 반드시 감싸야 합니다.
* `fetch_episode_information`: 필수적으로 구현되어야 합니다. 이 함수는 최소한 self.episode_titles(각 에피소드의 이름, 리스트), self.episode_ids(각 에피소드의 ID)가 생성되어야 합니다. `reload_manager` 데코레이터로 반드시 감싸야 합니다.
* `get_episode_image_urls`: 필수적으로 구현되어야 합니다. 이 함수는 episode_no를 인자로 받아 이미지 URL들을 반환합니다.

위 세 개를 구현하면 기본적으로 작동하게 되어 있습니다. 만약 마음에 들지 않는 동작이 있거나 더 간편하게 사용하기 위해서는 다음과 같은 기능을 추가적으로 구현할 수 있습니다.

* `get_episode_comments`: 댓글 다운로드를 지원하고 싶을 경우 구현하세요.
* `__init__`: 만약 웹툰 플랫폼이 추가적인 인증을 요구한다면 사용하세요. 예시: LezhinComicsScraper
* `get_webtoon_directory_name`: 웹툰 디렉토리의 이름을 만듭니다. 만약 웹툰 ID가 단순한 수나 문자열이 아닐 때 사용하면 좋습니다.
* `callback`: 추가적인 콜백이 있다면 사용하세요.
* `get_information`: information.json에 더 추가할 내용이 있다면 추가하세요. 예시: LezhinComicsScraper

## 용어 모음

여러 플랫폼은 저마다의 언어로 웹툰 서비스를 구현했습니다. 예를 들어 웹툰의 ID을 네이버 웹툰은 titleid, 버프툰은 series, 레진코믹스는 alias라고 하는 등 다양한 명명이 사용됩니다. 그러나 이러한 표현을 각자의 플랫폼에 맞추어 용어를 다르게 사용한다면 통일적인 개발이 불가능해질 것입니다. 이 섹션에서는 WebtoonScraper에서 사용되는 다양한 용어를 정의합니다.

* platform(aka 플랫폼, 웹툰 플랫폼): 웹툰을 제공하는 웹서비스를 의미합니다. 예를 들어 네이버 웹툰, 카카오 웹툰, 레진코믹스 등이 있습니다. 플랫폼에는 네이버 웹툰이나 카카오 웹툰처럼 정식으로 웹툰을 연재하는 곳도 있지만 네이버 블로그나 티스토리처럼 웹툰을 올리는 것만이 목적이 아닌 경우도 있습니다. 그런 플랫폼의 경우 일반적으로 텍스트 등의 다양한 서식을 사용할 수도 있는데, 그런 경우 이미지만 다운로드됩니다.
* webtoon ID(aka webtoon_id, 웹툰 ID): 웹툰의 식별자를 의미합니다. 한 웹툰 ID는 해당 플랫폼에서 유일하게 하나의 값을 가지며 여러 에피소드를 가지고 있습니다. 단, 한 웹툰 ID는 다른 플랫폼에서 겹쳐 나타날 수 있습니다.
* scraper(aka 스크래퍼): 스크래퍼는 해당 플랫폼의 웹툰을 다운로드하거나 여러 정보를 불러오기 위해 사용할 수 있습니다.
* CLI: WebtoonScraper를 사용할 수 있는 공간 중 하나입니다. 모바일에서는 확인하기 어렵지만, 컴퓨터에서는 주로 명령어 창의 형태로 나타나며, WebtoonScraper를 사용하는 가장 간단한 방법이 될 수 있습니다.
* 실행 파일: CLI와 마찬가지로 WebtoonScraper를 사용할 수 있는 공간 중 하나입니다. CLI와는 다르게 사용 시 설치를 필요로 하지 않습니다.
