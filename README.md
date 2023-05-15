# WebtoonScraper
웹툰을 스크래핑하는 프로젝트입니다.

# 사용법
1. 우선 관련 종속성을 설치해 주세요. 해당 폴더로 가서 커맨드를 열고 `pip install -r requirements.txt`를 입력해 주세요.
2. 원하는 웹툰으로 가서 titleid를 복사하세요.
3. 다음의 코드를 같은 폴더 내에서 실행해 주세요.
```python
from WebtoonScraper import *

a = NaverWebtoonScraper()
a.get_webtoons(804862)
```
