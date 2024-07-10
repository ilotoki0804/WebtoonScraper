# Relese Note

## 3.4.0b2 (2024-06-22)

* 여러 버그를 수정했습니다.
* 문서를 보강했습니다.

## 3.4.0b1 (2024-06-22)

* `concat` command와 `image_concatenator` 모듈이 새로 생겼습니다.
* `merge` command의 `--target-parent-directory` 옵션이 `--target-webtoon-directory`으로 이름이 변경되었습니다.
* `merge` command의 작동이 변경되었습니다. 기존에는 웹툰 선택기로 갔지만 지금은 `--select` 옵션을 명시적으로 부과해야만 합니다.
* 여러 모듈이 `__all__`을 정의합니다. 따라서 pylance 등에서 보내는 일부 오류를 해결할 수 있습니다.
* `build.py` 대신 `simplebuild`를 이용해 빌드합니다.
* `INFORMATION_VARS`가 `get_information`을 대체합니다.
* `ensure_normal` 함수가 추가되었습니다. 웹툰 디렉토리가 기본 상태인지 점검합니다.
* 다양한 코드 및 문서 개선이 있었습니다.

## 3.3.0 (2024-04-30)

* 거대 코드 퀄리티 개선이 있었습니다. 문서들이 개선되거나 추가되고 isort도 적용되었습니다.
* IS_CONNECTION_STABLE이 제거되었습니다.
* 문서에 다양한 개선이 있었습니다.
* pyfilename 등 일부 패키지 버전의 업데이트가 있었습니다.
* build.py가 업데이트되었습니다.
* 다양한 comment 관련 예외들이 추가되었습니다.
* 특정 스크래퍼에 한해서 사용되는 의존성을 선택적으로 만들었습니다. 이제 WebtoonScraper를 완전히 이용하려면 `WebtoonScraper[full]`을 이용해 다운로드해야 합니다.
* `--version`에서 의존성 설치 상태를 확인할 수 있습니다.
* .gitignore의 규칙이 변경되어 이제 underscore로 시작하는 이름들도 git에 등록할 수 있게 되었습니다.
* 스크래퍼 모듈들의 이름을 완전히 재조정했습니다. 이제 스크래퍼 모듈들은 private 모듈입니다.
* kakaopage_query.py가 삭제되고 kakaopage에 흡수되었습니다.
* 로깅에서 이제 시간이 기본적으로 보이지 않도록 변경되었습니다.
* _check_webtoon_id_type가 추가되었습니다.
* VSCode의 새 기능 `MARK`를 활용해 scraper.py에서 이동하기에 간편하게 만들었습니다.
* 버프툰이 다시 작동합니다.

## 3.2.2 (2024-03-29)

* `-c`, `--comments` 옵션을 활용해 CLI로도 댓글을 다운로드할 수 있습니다.
* 문서에 `-c` 옵션과 관련된 내용이 추가되고 그 외 부분이 개선되었습니다.
* PyPI 릴리즈가 Actions로 자동화되었습니다.
* 여러 부분에서 rich를 사용하였습니다.

## 3.2.1 (2024-03-26)

* `webtoon.html`가 디자인, 코드 등이 개선되었습니다.
* 웹툰의 댓글과 작가의 말을 다운로드할 수 있습니다. 현재는 네이버 웹툰에서만 사용 가능합니다. `webtoon.html`에서 `show comments` 버튼을 눌러 다운로드한 댓글을 확인할 수 있습니다.
* 로깅을 루트 로거 대신 설정된 로거를 사용하도록 변경되었습니다.
* LEZHIN_BEARER를 환경 변수로 설정해 사용할 수 있습니다.
* CLI에서 여러 웹툰 ID를 입력할 수 있도록 변경되었습니다. 예를 들어 두 개의 웹툰을 다운로드받고 싶다면 `webtoon download webtoonid1 webtoonid2 -p naver_webtoon`과 같이 사용할 수 있습니다.
* `--show-detailed-error` 옵션이 삭제되고 같은 역할을 하는 `--verbose`가 추가되었습니다.
* `__license__`가 삭제되었습니다.

## 3.1.2 (2024-02-14)

* Scraper.from_url 추가 및 관련 문서 개선: webtoon_id 대신 raw URL에서 직접 사용할 수 있습니다.
* 각종 버그 수정 및 기능 개선, 문서 개선

## 3.1.1 (2024-02-12)

* 카카오 웹툰 지원 추가: 카카오 웹툰 지원을 추가했습니다.
* nest-asyncio 더 이상 사용하지 않음: 기존에 `download_webtoon`을 위해 사용되던 nest-asyncio를 더 이상 사용하지 않습니다. 자체적으로 설치해 사용하거나 `async_download_webtoon`을 사용하실 수 있습니다.
* directory_merger 관련 변화: `webtoon merge` 커맨드가 웹툰 포함 디렉토리에 대한 것으로 변경되었고, DirectoryMerger 클래스가 삭제되었습니다.
* logger 분리: 기존에 root logger에 로그를 남기던 것과 달리 별도의 로거를 만들었습니다.
* 의존성 변경: nest-asyncio가 의존성에서 빠지고 pycryptodomex가 의존성에 추가되었습니다.
* 기타 버그 수정 및 개선

## 3.0.1 (2024-01-19)

* pyinstaller 빌드 포함 및 Github Actions로 자동화: 이제 파이썬 설치 없이 pyinstaller로 만들어진 빌드 파일을 이용해 사용할 수 있습니다.
* 다운로드 시작 시 인자 표시 제거
* 문서 개선
* 웹툰 다운로드 시 container 상태 확인 추가

## 3.0.0 (2024-01-07)

* 문서 대폭 개선: 기존에 읽기 힘들었던 문서를 대폭 개선하였습니다.
* hxsoup 사용, resoup 의존성 제거: resoup와 requests 대신 httpx와 hxsoup를 이용하는 것으로 변경되었습니다. 이 변화로 더욱 빠르고 Pythonic한 코드를 짤 수 있게 되었습니다. 더욱이 파이썬 버전 제한이 사라졌습니다.
* nest-asyncio 사용: async를 이용한 코드를 짜면서 생기는 불편한 오류들을 없애기 위해 nest-asyncio를 사용합니다.
* 3.11.5 이상 파이썬 버전에 대한 경고 제거: 이제 드디어 파이썬 윗 버전에서도 불편함 없이 WebtoonScraper를 사용할 수 있게 되었습니다. 더 이상 WebtoonScraper는 3.11.5 이상의 버전에 대한 성능 저하가 일어나지 않습니다.
* 속도 개선: async 사용, httpx 사용, 더 빠른 다운로드 사용 등 다양한 이유로 속도가 더욱 개선되었습니다.
* webtoon.py 더이상 사용하지 않도록 권장: `WebtoonScraper.webtoon` 모듈은 초창기에 CLI가 없을 때 간단한 사용을 위해 만들어졌고 이제는 CLI로 대체되었습니다. 만약 파이썬 스크립트로 WebtoonScraper를 사용하고 싶다면 `WebtoonScraper.scrapers`를 사용하세요.
* webtoon viewer 추가: 다운로드받은 웹툰을 볼 수 있는 webtoon.html을 추가하는 add_webtoon_viewer(cli로는 --add-viewer)를 추가하였습니다.
* information.json 추가
* ExistingEpisodePolicy 추가: ExistingEpisodePolicy를 통해 다운로드 시 이미 다운로드된 에피소드 디렉토리를 봤을 때 어떻게 할 지를 설정할 수 있습니다.
* 버프툰 버그 수정
* 카카오페이지 버그 수정
* WebtoonsOriginals에서 WebtoonsDotcom으로 이름 변경
* Apache License 2.0 사용.
* 그 외 다양한 코드 개선 및 리팩토링, 버그 수정.

## 3.0.0 이전

2.3.6 (2024-01-01): 레진코믹스 소장한 무료 회차 1080p 관련 버그 수정(#3), typing_extensions 의존성 제거, 문서 및 코드 개선.

2.3.5 (2023-12-31): 레진코믹스 소장한 무료 회차 1080p 지원(#3) 및 코드 및 문서 개선.

2.3.4 (2023-12-30): fast_merge_webtoon이 기본값이 되고 기존 방식은 제거됨. setup이 fetch_all로 이름이 바뀜. 레진코믹스 구매한 회차 1080p 지원 및 모든 rating 지원(#3) 및 기본 timeout 늘림. 버그 개선 및 코드 개선, 문서 보강

2.3.3 (2023-12-27): directory_merger 관련 코드 개선 및 기타 코드 개선(#2)

2.3.2 (2023-12-10): CLI에 merge 명령 추가, restore_webtoon_directory_to_directory 추가, pyproject.toml에 프로젝트 메타데이터 추가, Hits 추가, 네이버 블로그 관련 버그 수정, callback 추가, EpisodeNoRange에서 slice와 iterable도 받도록 허용, webtoon CLI 추가

2.3.1 (2023-12-09): 네이버 포스트 & 네이버 블로그 버그 수정, resoup 사용, pyfilename 사용, best_challenge 관련 모듈 수정 및 seamless_redirect 추가, download_webtoons_getting_paid 관련 버그 수정, dm.select로 이름 변경 및 리팩토링, .gitignore 변경, 버전에 대한 경고 메시지

2.3.0 (2023-11-22): 티스토리 추가, 코드 개선 및 리팩토링

2.2.0 (2023-11-04): 네이버 블로그 추가, gitbook 추가, URL_REGEX 추가(현재는 사용처가 없지만 향후에 생길 예정), 리팩토링, 절대 경로 지원 제거

2.1.0 (2023-09-24): CLI 추가, 문서 개선

2.0.2 (2023-09-13): 의존성이 설치되지 않는 버그 수정

2.0.1 (2023-09-10): (의존성이 설치되지 않는 버그 있음: 의존성을 직접 설치하면 문제 없음.) scrapers 폴더 미포함 버그 수정, 필요없는 주석 제거, 빠뜨렸던 의존성 추가(typing_extensions)

2.0.0 (2023-09-10): (버그 있음 -- 사용하지 말 것을 권장함.) pyjsparser, async_lru 의존성 제거, 대규모 리팩토링(scraper 폴더 생성, directory_merger 리팩토링, exceptions 추가, py.typed 추가, 독스 추가, 그 외 버그 수정 등.), 레진 unshuffler 분리 및 unshuffler 버그 수정, Scraper 완전 변경, 만화경 지원 제거, async 로직에서 제거

1.3.0 (2023-08-27): 카카오페이지 추가, 의존성 증가(~~[requests-utils](https://github.com/ilotoki0804/resoup)~~(3.0.0 버전에서 의존성에서 제거됨))

1.2.0 (2023-07-27): 레진코믹스 추가, 의존성 증가(~~pyjsparser~~(2.0.0 버전에서 의존성에서 제거됨), Pillow)

1.1.1 (2023-07-22): 내부 모듈 이름 변경, merge option 추가, abstractmethod들의 일반 구현 추가

1.0.2 (2023-07-07): 대형 리팩토링, get_webtoon_platform 비동기 방식으로 속도 개선, 상대경로로 변경, 테스트 추가

1.0.1 (2023-06-30): 코드 개선 및 리팩토링, api를 통한 로직으로 변경 (버그가 많기에 사용을 권장하지 않음)

1.0.0 (2023-06-29): 네이버 게임 추가, FolderManager 리펙토링 및 개선, 정식 버전, docs 개선

0.1.1 (2023-06-21): 네이버 포스트 추가, readme 작성, pbar 표시 내용 변경, 버그 수정

0.1.0 (2023-06-19): 버프툰 추가, 빠진 부분 재추가

이 아래의 버전들은 더 이상 PyPI에서 확인할 수 없습니다.

~~0.0.19 (2023-06-18): merge 속성 추가, get_webtoon 함수로 변경, pbar에 표시되는 내용 변경, 내부적 개선~~

~~0.0.18 (2023-06-07): 만화경 지원, 리팩토링됨(Scraper Abstract Base Class 추가)~~

~~0.0.17 (2023-05-31): 웹툰즈 오리지널, 캔버스 지원~~

~~0.0.12 (2023-05-29): 네이버 웹툰, 베스트 도전 지원~~
