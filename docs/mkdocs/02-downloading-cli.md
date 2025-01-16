# PyPI 패키지와 포터블에서의 웹툰 다운로드

앱을 통해 다운로드하는 방법이 궁금하다면 [앱으로 웹툰 다운로드](./3-downloading-app.md)를 참고하세요.

## 다운로드

PyPI 패키지와 포터블에서는 기본적으로 다음과 같은 명령어를 통해 다운로드를 할 수 있습니다.

```console
webtoon download "https://<다운로드받을 URL>"
```
![downloading_portable](image/downloading/downloading_portable.png)

이렇게 하면 명령어가 실행된 디렉토리에서 `웹툰이름(웹툰ID)` 형식의 웹툰 디렉토리가 나타납니다.

![webtoon_directory](image/downloading/webtoon_directory.png)

웹툰 디렉토리 내에는 웹툰의 썸네일인 *thumbnail.jpg*, 웹툰에 관련한 정보를 담는 *information.json*,
웹브라우저에서 웹툰을 볼 수 있는 [*webtoon.html*](./viewer.md)(포터블 버전에서만 포함됨), 그리고 가장 중요한 웹툰 이미지 파일들을 담은 여러 폴더(에피소드 디렉토리라고 부르겠습니다.)들이 있습니다.

## 추가 인자 설정

다운로드 시에 URL만 제공해도 충분한 경우가 있지만, 다운로드 시 부가적인 정보가 필요하거나 옵션을 통해 다운로드를 커스텀할 수도 있습니다.
이 값들을 추가하는 것이 인자입니다.

인자는 1개 혹은 2개의 하이픈(-)으로 시작하는 인자 이름과 인자의 값으로 이루어져 있습니다.

```
webtoon download --추가-인자1 "추가 인자1 값" --값-없는-추가-인자 --추가-인자2 "추가 인자2 값" --추가-인자3 "추가 인자3 값" "<URL>"
```

예를 들어 아래는 다양한 추가 인자들을 삽입해 웹툰을 다운로드하는 예시입니다.

```
webtoon download --cookie "..." --option download-comments="true" --option download-audio="false" -r "~3" "https://..."
```

위의 명령어는 다음과 같이 해석할 수 있습니다.

* `webtoon download`: WebtoonScraper를 통해 웹툰을 다운로드
* `--cookie "..."`: [쿠키 값](#쿠키)을 `...`으로 설정
* `--option download-comments="true"`: `download-comments`라는 옵션의 값을 `true`로 설정합니다.
* `--option download-audio="false"`: `download-audio`라는 옵션의 값을 `false`로 설정합니다.
* `-r "~3"`: [다운로드 범위](90-download-range.md#적용)를 적용시켜  3화까지만 다운로드하도록 설정합니다.
* `"https://..."`: 다운로드할 웹툰의 URL입니다.

## 쿠키

쿠키는 일종의 인증서로서, 로그인이 요구되거나 성인 인증이 필요한 경우 필요합니다.
쿠키에 대한 자세한 설명은 [별도의 문서](04-cookie.md)를 참고하세요.

## `--option` 인자

각 웹툰 사이트들에는 해당 사이트에 특화한 기능에 대한 옵션이 필요하기도 합니다.
그런 기능들은 `--option` 인자를 통해 설정할 수 있습니다.

예를 들어, 특정 웹툰 사이트에서 bearer를 사용해야 하는 경우 다음과 같이 사용할 수 있습니다:

```console
webtoon download --option bearer="Bearer ..." "<URL>"
```

사용 가능한 옵션들은 각 웹툰 사이트마다 다를 수 있으며, 자세한 내용은 [해당 사이트의 문서](10-platforms.md)를 참고하세요.

`--option` 인자를 여러 개 사용하고 싶은 경우에는 사용할 `--option` 인자들을 그냥 나열하면 됩니다.

### 논리값을 가지는 `--option` 인자

설정할 수 있는 `--option` 중에서 일부는 참이나 거짓의 값으로 설정할 필요가 있을 수 있습니다.

이럴 경우 **1 yes true on**는 대소문자 구분 없이 참으로 평가되고, **0 no false off**는 대소문자 구분 없이 거짓으로 평가됩니다.

즉, 논리값을 가지는 옵션 `--option my-option=true`와 `--option my-option=1`은 동일하며,
`--option my-option=no`와 `--option my-option=off`도 동일합니다.

## 여러 웹툰 한번에 다운로드하기

같은 설정으로 여러 웹툰을 한번에 다운로드하고 싶은 경우 URL을 여러 번 입력하면 됩니다.

```console
webtoon download "https://<다운로드받을 웹툰 URL 1>" "https://<다운로드받을 웹툰 URL 2>" "https://<다운로드받을 웹툰 URL 3>"
```

## 다시 다운로드하기

웹툰을 다운로드한 뒤 시간이 지나 에피소드를 업데이트하고 싶을 수 있습니다.
그럴 때는 웹툰 디렉토리를 그대로 둔 상태로 같은 URL에 대해 다운로드를 시도하세요.

그렇게 하면 기존에 다운로드한 디렉토리를 그대로 둔 상태로 새롭게 나타난 웹툰들만 다운로드할 수 있습니다.

이 동작은 `download`와 URL 사이에 `--existing-episode` 플래그를 위치시킴으로써 변형할 수 있습니다.

```console
webtoon download --existing-episode skip "https://..."
```

* `--existing-episode skip`(기본값): 웹툰 디렉토리가 발견되면 다운로드하지 않고 넘어갑니다.
* `--existing-episode raise`: 웹툰 디렉토리가 발견되면 오류를 내고 다운로드를 중단시킵니다.
* `--existing-episode download_again`: 웹툰 디렉토리가 발견되면 기존 디렉토리를 지우고 처음부터 다시 다운로드합니다.
* `--existing-episode hard_check`: 웹툰 디렉토리가 발견되면 디렉토리 내부에 있는 이미지 개수를 확인하고 실제 가져야 하는 웹툰 이미지 개수를 비교하고 일치하지 않는다면 기존 디렉토리를 지우고 처음부터 다시 다운로드합니다.

WebtoonScraper는 작동 중 오류가 나거나 예기치 않게 정지하는 상황에서도 에피소드 디렉토리의 무결성을 보장합니다.
따라서 기본값인 `skip`을 사용하는 것이 대부분의 경우 가장 좋은 선택입니다.

`hard_check`의 경우 결국 웹툰 플랫폼 서버를 거쳐야 하기 때문에 `skip`에 비해 현저하게 느리고 무결성이 보장되지도 않지만 모든 이미지를 다시 다운로드하는 `download_again`에 비하면 네트워크를 덜 사용합니다.
