# WebtoonScraper

웹툰을 다운로드하는 프로젝트입니다. 그 외에도 웹툰 모아서 보기 등 몇 가지 편의 기능을 지원합니다.

# 시작하기

1. 파이썬을 PATH를 추가한 뒤 설치합니다.
2. cmd 창을 열어 다음과 같은 명령어를 칩니다.

   ```
   pip install WebtoonScraper
   ```

   또는
   ```
   pip3 install WebtoonScraper
   ```

# 웹툰 다운로드하기

1. 원하는 웹툰으로 가서 titleid를 복사하세요.
   ![img](example1.png)
2. 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.

   ```python
   from WebtoonScraper import *

   a = NaverWebtoonScraper()
   a.get_webtoons(76648) # titleid를 여기에다 붙여넣으세요
   ```

   이제 웹툰이 webtoons 폴더에 다운로드됩니다.

   만약 여러 웹툰을 한 번에 다운로드 받고 싶다면 다음과 같이 코드를 짤 수 있습니다.

   ```python
   from WebtoonScraper import *

   webtoon = NaverWebtoonScraper()
   webtoon.get_webtoons(748105, 81482, 728128) # titleid를 여기에다 붙여넣으세요. 길이에 제한은 없습니다.
   ```
3. 만화 뷰어 앱을 통해 다운로드한 웹툰을 시청할 수 있습니다.

## 주의사항

* 중간에 웹툰 다운로드가 멈춘 듯이 보여도 정상입니다. 그대로 가만히 있으면 다운로드가 다시 진행됩니다.
* 만약 작동하지 않는다면 윈도우에서 Python 3.11.3을 설치하고 앞의 과정을 반복해 보세요.

# 여러 회차 하나로 묶기

1. 웹툰을 상기한 대로 다운로드받습니다.
2. 다음과 같이 코드를 짭니다.
   ```python
   from WebtoonScraper import *

   folder = WebtoonFolderManagement('webtoon_merge')
   folder.divide_all_webtoons(5)
   ```
3. webtoons 폴더에 있는 **모든** 웹툰이 'webtoons_merge' 폴더에 5화씩 묶여져 다운로드됩니다.

## 주의사항

* 시작 시 꼭 디렉토리를 선택해 주세요. 아니면 오류가 납니다.
* 작업 중간에 폴더가 사라지고 이미지가 폴더 밖으로 나오는데, 이는 정상 과정입니다.
* 기기 사양에 따라 파이썬이 '응답 없음'을 내보낼 수 있습니다.
* 너무 큰 숫자를 입력하면 웹툰 뷰어가 제대로 작동하지 않을 수 있음을 유의하세요.

# 묶인 회차 다시 원래대로 되돌리기

1. 윗글의 기능으로 묶인 회차를 준비합니다.
2. 다음과 같이 코드를 짭니다.
   ```python
   from WebtoonScraper import *

   folder = WebtoonFolderManagement('webtoon_merge')
   folder.revert_to_original_state('webtoon/1초(725586)')
   ```
3. 'webtoon/1초(725586)' 폴더에 있던 모든 웹툰이 웹툰을 처음 다운로드했던 상태로 되돌아갑니다.
