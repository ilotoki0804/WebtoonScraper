# WebtoonScraper

웹툰을 다운로드하는 프로젝트입니다.

네이버 웹툰, 베스트 도전만화, 웹툰 오리지널, 웹툰 캔버스, 만화경, 버프툰, 네이버 포스트, 네이버 게임을 지원합니다.

# 시작하기

1. 파이썬을 설치합니다.
2. cmd 창을 열어 pip 명령어를 실행합니다.
   ```
   pip install -U WebtoonScraper
   ```

# 네이버 웹툰, 베스트 도전만화, 웹툰 오리지널, 웹툰 캔버스, 만화경, 네이버 게임 다운로드하기

버프툰과 네이버 포스트는 아래로 가서 확인하세요.

1. 원하는 웹툰으로 가서 titleid 또는 title_no를 복사하세요.
   ![img](images/naver_webtoon.png)
   네이버 웹툰과 베스트 도전의 경우 여기에서,
   ![img](images/webtoons_original.png)
   웹툰 오리지널과 캔버스의 경우는 여기에서,
   ![img](images/manhwakyung.png)
   만화경의 경우는 여기에서,
   ![img](images/naver_game.png)
   네이버 게임 오리지널 시리즈의 경우는 여기에서 확인할 수 있습니다.
2. 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요. 웹툰은 정식 연재와 베스트 도전, Webtoons 오리지널과 캔버스, 만화경, 네이버 게임 모두 가능합니다.

   ```python
   from WebtoonScraper import Webtoon as wt

   # 네이버 웹툰
   wt.get_webtoon(76648, wt.N) # titleid를 여기에다 붙여넣으세요.
   # 베스트 도전만화
   wt.get_webtoon(763952, wt.B) # titleid를 여기에다 붙여넣으세요.
   # 웹툰 오리지널
   wt.get_webtoon(1435, wt.O) # titleid를 여기에다 붙여넣으세요.
   # 웹툰 캔버스
   wt.get_webtoon(304446, wt.C) # titleid를 여기에다 붙여넣으세요.
   # 만화경
   wt.get_webtoon(146, wt.M) # titleid를 여기에다 붙여넣으세요. Webtoon.T 태그도 사용 가능합니다.
   # 네이버 게임 오리지널 시리즈
   wt.get_webtoon(146, wt.G) # titleid를 여기에다 붙여넣으세요.
   ```

   이제 웹툰이 webtoons 폴더에 다운로드됩니다.

   cf. 웹툰 태그를 생략하면 해당 웹툰이 어떤 사이트의 웹툰 id인지 자동으로 알아냅니다. 만약 몇몇 태그가 겹친다면 태그에 맞는 수를 입력하는 창에 알맞은 수를 입력하면 됩니다.

   또 merge 태그를 이용하면 webtoon 폴더 내에 있는 모든 웹툰을 자동으로 5화씩 묶습니다.
3. 만화 뷰어 앱을 통해 다운로드한 웹툰을 시청할 수 있습니다.

## 주의사항

* 중간에 웹툰 다운로드가 멈춘 듯이 보여도 정상입니다. 그대로 가만히 있으면 다운로드가 다시 진행됩니다.
* 만약 작동하지 않는다면 윈도우에서 Python 3.11.4을 설치하고 앞의 과정을 반복해 보세요.

# 버프툰 다운로드하기

## 로그인하지 않은 상태에서 웹툰 다운로드하기

로그인하지 않은 상태에서도 웹툰을 다운로드받을 수 있으나, 받을 수 있는 웹툰 수가 매우 적기에 추천하지 않습니다.

1. 웹툰 페이지에 들어가 주소창의 맨 마지막 수를 복사합니다.
2. 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.
   ```python
   from WebtoonScraper import Webtoon as wt

   wt.get_webtoon(1007888, wt.BF) # 복사했던 수를 여기에다 붙여넣으세요.
   ```
3. 'Enter cookie of 1007888(시리즈 id) (Enter nothing to preceed without cookie)'라는 문구와 함께 입력란이 나오면 그냥 enter를 눌러줍니다.
4. 로그인하지 않고 볼 수 있는 모든 에피소드가 다운로드됩니다.

## 로그인한 상태에서 웹툰 다운로드하기

이 과정은 PC를 기준으로 설명합니다. 만약 모바일이라면 Kiwi Browser 등을 통해 다음의 과정을 수행할 수 있습니다.

1. 웹툰 페이지에 들어가 주소창의 맨 마지막 수를 복사합니다. 이 예시에서는 1007888입니다.
   ![img](images/bufftoon1.png)
2. 로그인을 하고 f12를 누르고 네트워크 창을 연 뒤 웹툰 페이지에 들어갑니다.
   ![img](images/bufftoon2.png)
3. 새로고침을 한 뒤 '이름'에 있는 favicon.ico 요청을 클릭하고 나온 창에 '헤더' 탭을 엽니다.
   ![img](images/bufftoon3.png)
4. 내려서 Cookie: 라고 되어 있는 모든 내용을 복사합니다.
   ![img](images/bufftoon4.png)
5. 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.

   ```python
   from WebtoonScraper import Webtoon as wt

   wt.get_webtoon(1007888, wt.BF) # 첫 번째로 복사했던 수를 여기에다 붙여넣으세요.
   ```

   혹은 다음과 같이 cookie를 코드 내에 포함할 수도 있습니다.

   ```python
   from WebtoonScraper import Webtoon as wt
   cookie = '두 번째로 복사했던 문자를 여기에다 붙여넣으세요.'
   wt.get_webtoon(1007888, wt.BF, cookie=cookie) # 첫 번째로 복사했던 수를 여기에다 붙여넣으세요.
   ```

   1. 'Enter cookie of 1007888(시리즈 id) (Enter nothing to proceed without cookie)'라는 문구와 함께 입력란이 나오면 두 번째로 복사했던 일련의 문자열을 붙여넣기합니다.
6. 로그인하면 볼 수 있는 모든 에피소드가 다운로드됩니다.

## 주의사항

* get_webtoon에서 cookie를 입력하면 자동으로 버프툰으로 인식합니다.

# 네이버 포스트 다운로드하기

1. 웹툰이 있는 페이지로 가서 seriesNo와 memberNo를 복사하세요. 예시에서는 각각 597061과 19803452입니다.
   ![img](images/naver_post.png)
2. 다음의 파이썬 코드를 웹툰이 다운로드되길 원하는 폴더 내에서 실행해 주세요.

   ```python
   from WebtoonScraper import Webtoon as wt

   wt.get_webtoon(597061, wt.M) # 우선 seriesNo만 여기에 입력해주세요.
   ```

   혹은 memberNo를 코드 내에 포함할 수 있습니다.

   ```python
   from WebtoonScraper import Webtoon as wt

   wt.get_webtoon(597061, wt.M, member_no=19803452)
   ```
3. 'Enter memberNo of 597061(해당 웹툰의 seriesNo)'라는 말과 함께 입력란이 나오면 거기에 아까 복사해 놓은 memberNo를 붙여넣습니다.
   만약 앞에서 이미 member_no를 사용했다면 이 단계는 건너뛰어집니다.

   ```
   Enter memberNo  of 597061: 19803452
   ...진행됨...
   ```
4. 만화 뷰어 앱을 통해 다운로드한 웹툰을 시청할 수 있습니다.

## 주의사항

* 가끔씩 이유 없는 오류가 발생할 수 있습니다. 그럴 때는 조금 시간이 지난 후에 다시 시도해 보세요.
* 네이버 포스트는 titleid를 get_webtoon_platform으로 알아낼 수 없습니다.
* member_no를 입력하면 자동으로 포스트로 인식됩니다.

# 여러 회차 하나로 묶기

1. 웹툰을 상기한 대로 다운로드받습니다.
2. 다음과 같이 코드를 짭니다.
   ```python
   from WebtoonScraper import FolderManager

   fm = FolderManager()
   fm.divide_all_webtoons(5)
   ```
3. webtoons 폴더에 있는 **모든** 웹툰이 'webtoon_merge' 폴더에 5화씩 묶여져 다운로드됩니다.

## 주의사항

* 시작 시 꼭 디렉토리를 선택해 주세요. 아니면 오류가 납니다.
* 작업 중간에 폴더가 사라지고 이미지가 폴더 밖으로 나오는데, 이는 정상 과정입니다.
* 너무 큰 수를 입력하면 웹툰 뷰어가 제대로 작동하지 않을 수 있음을 유의하세요.

# 묶인 회차 다시 원래대로 되돌리기

1. 윗글의 기능으로 묶인 회차를 준비합니다.
2. 다음과 같이 코드를 짭니다.
   ```python
   from WebtoonScraper import FolderManager

   fm= FolderManager()
   fm.restore_webtoons_in_directory()
   ```
3. 'webtoon' 폴더에 있던 모든 웹툰이 웹툰을 처음 다운로드했던 상태로 되돌아갑니다.

# QNA

## 회차 번호 관련

### 문제와 이유

회차가 띄엄띄엄 있거나 설정된 회차 번호가 작가가 설정한 회차 번호와 다르거나 회차 묶기를 사용했는데 묶인 회차 수가 설정한 수보다 더 적은 이유는 다음과 같습니다.
이 프로젝트에서 웹툰의 회차 번호는 ID를 기준으로 합니다. 이는 작가가 정한 회차와는 다를 수 있습니다. 작가가 프롤로그부터 시작하는 경우(프로젝트의 회차 번호가 하나 빠름), 작가가 리메이크를 해서 전에 있던 작품을 제거해 ID가 연속적으로 있지 않는 경우(주로 베도에서 일어남/회차 번호가 띄엄띄엄하게 있음), 논란이나 작가 실수 등으로 회차가 삭제된 경우(한 회차를 건너띔) 등에서 ID가 불연속적이거나 작품과 일치하기 않는 경우가 생기게 됩니다.

### ID를 회차 번호로 그대로 사용하는 이유

우선 작가가 설정한 회차 번호에 맞추는 것은 힘듭니다. 우선 번호가 어디에 있을지 알기 어렵고, 프롤로그가 있을지 없을지 알 수 없으며, 여러 화에 걸쳐 같은 에피소드를 진행하는 경우도 있고, 외전으로 본편의 회차에서 분리된 화를 운영하는 경우가 있어 화에 맞추어서 번호를 정하는 것을 어렵습니다.
1부터 시작해서 끝까지 일정한 번호를 유지하는 것도 고려해볼 만하나 만약 그렇게 된다면 무결성 체크를 사용하기 어렵게 됩니다.
따라서 작가가 설정한 회차를 그대로 사용하는 것도 어렵고, 만약 가능하다 할 지라도 무결성 체크를 포기하기 어렵기 때문에 현재는 ID를 회차 번호로 사용하고 있습니다.

# Relese Note

1.0.2: 대형 리팩토링, get_webtoon_platform 비동기 방식으로 속도 개선, 상대경로로 변경, 테스트 추가

1.0.1: 코드 개선 및 리팩토링, api를 통한 로직으로 변경 (버그가 많기에 사용을 권장하지 않음)

1.0.0: 네이버 게임 추가, FolderManager 리펙토링 및 개선, 정식 버전, docs 개선

0.1.1: 네이버 포스트 추가, readme 작성, pbar 표시 내용 변경, 버그 수정

0.1.0: 버프툰 추가, 빠진 부분 재추가

0.0.19.3: merge 속성 추가, get_webtoon 함수로 변경

0.0.19.1: pbar에 표시되는 내용 변경, 내부적 개선

0.0.18: 만화경 지원, 리팩토링됨(Scraper Abstract Base Class 추가)

0.0.17: 웹툰즈 오리지널, 캔버스 지원

0.0.12: 네이버 웹툰, 베스트 도전 지원
