# Relese Note

3.0.0 (2024-01-07): 문서 대폭 개선. hxsoup 및 nest-asyncio 사용(의존성 증가), resoup 의존성 제거. 3.11.5 이상 파이썬 버전에 대한 경고 제거. 속도 개선. 버프툰 버그 수정 및 다양한 버그 수정. webtoon.py 더이상 사용하지 않도록 권장. Apache License 2.0 사용. 그 외 다양한 코드 개선 및 리팩토링.

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

1.3.0 (2023-08-27): 카카오페이지 추가, 의존성 증가([requests-utils](https://github.com/ilotoki0804/resoup))

1.2.0 (2023-07-27): 레진코믹스 추가, 의존성 증가(~~pyjsparser~~(2.0.0 버전에서 의존성에서 제거됨), Pillow)

1.1.1 (2023-07-22): 내부 모듈 이름 변경, merge option 추가, abstractmethod들의 일반 구현 추가

1.0.2 (2023-07-07): 대형 리팩토링, get_webtoon_platform 비동기 방식으로 속도 개선, 상대경로로 변경, 테스트 추가

1.0.1 (2023-06-30): 코드 개선 및 리팩토링, api를 통한 로직으로 변경 (버그가 많기에 사용을 권장하지 않음)

1.0.0 (2023-06-29): 네이버 게임 추가, FolderManager 리펙토링 및 개선, 정식 버전, docs 개선

0.1.1 (2023-06-21): 네이버 포스트 추가, readme 작성, pbar 표시 내용 변경, 버그 수정

0.1.0 (2023-06-19): 버프툰 추가, 빠진 부분 재추가

0.0.19 (2023-06-18): merge 속성 추가, get_webtoon 함수로 변경, pbar에 표시되는 내용 변경, 내부적 개선

0.0.18 (2023-06-07): 만화경 지원, 리팩토링됨(Scraper Abstract Base Class 추가)

0.0.17 (2023-05-31): 웹툰즈 오리지널, 캔버스 지원

0.0.12 (2023-05-29): 네이버 웹툰, 베스트 도전 지원
