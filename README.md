# WebtoonScraper
웹툰을 스크래핑하는 프로젝트입니다.

# 사용법(NaverWebtoonScraper)
1. 우선 관련 종속성을 설치해 주세요. 해당 폴더로 가서 커맨드를 열고 `pip install -r requirements.txt`를 입력해 주세요.
2. 원하는 웹툰으로 가서 titleid를 복사하세요.
   ![img](example1.png)
3. 다음의 코드를 같은 폴더 내에서 실행해 주세요.
```python
from WebtoonScraper import *

a = NaverWebtoonScraper()
a.get_webtoons(<titleid>) # titleid를 여기에다 붙여넣으세요
```
이제 웹툰이 webtoons 폴더에 다운로드됩니다.

만약 여러 웹툰을 한 번에 다운로드 받고 싶다면 다음과 같이 코드를 짤 수 있습니다.
```python
from WebtoonScraper import *

a = NaverWebtoonScraper()
a.get_webtoons(<titleid1>, <titleid2>, ...) # titleid를 원하는 만큼 쉼표를 붙여 여기에다 붙여넣으세요
```
# 사용법(WebtoonFolderManagement)
1. 웹툰을 상기한 대로 다운로드받습니다.
2. 다음과 같이 코드를 짭니다.
```python
from WebtoonScraper import *

a = WebtoonFolderManagement('webtoon_merge')
a.divide_all_webtoons(5)
```
3. webtoons 폴더에 있는 웹툰이 모두 webtoons_merge 폴더에 5화씩 묶여져 다운로드됩니다.