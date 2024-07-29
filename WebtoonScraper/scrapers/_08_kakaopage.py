"""Download Webtoons from Kakaopage."""

from __future__ import annotations

import re
from typing import Final

from ..exceptions import InvalidWebtoonIdError
from ._01_scraper import Scraper, reload_manager

WEBTOON_DATA_QUERY: Final[str] = "\n    query contentHomeProductList($after: String, $before: String, $first: Int, $last: Int, $seriesId: Long!, $boughtOnly: Boolean, $sortType: String) {\n  contentHomeProductList(\n    seriesId: $seriesId\n    after: $after\n    before: $before\n    first: $first\n    last: $last\n    boughtOnly: $boughtOnly\n    sortType: $sortType\n  ) {\n    totalCount\n    pageInfo {\n      hasNextPage\n      endCursor\n      hasPreviousPage\n      startCursor\n    }\n    selectedSortOption {\n      id\n      name\n      param\n    }\n    sortOptionList {\n      id\n      name\n      param\n    }\n    edges {\n      cursor\n      node {\n        ...SingleListViewItem\n      }\n    }\n  }\n}\n    \n    fragment SingleListViewItem on SingleListViewItem {\n  id\n  type\n  thumbnail\n  showPlayerIcon\n  isCheckMode\n  isChecked\n  scheme\n  row1\n  row2\n  row3 {\n    badgeList\n    text\n  }\n  single {\n    productId\n    ageGrade\n    id\n    isFree\n    thumbnail\n    title\n    slideType\n    operatorProperty {\n      isTextViewer\n    }\n  }\n  isViewed\n  eventLog {\n    ...EventLogFragment\n  }\n}\n    \n\n    fragment EventLogFragment on EventLog {\n  fromGraphql\n  click {\n    layer1\n    layer2\n    setnum\n    ordnum\n    copy\n    imp_id\n    imp_provider\n  }\n  eventMeta {\n    id\n    name\n    subcategory\n    category\n    series\n    provider\n    series_id\n    type\n  }\n  viewimp_contents {\n    type\n    name\n    id\n    imp_area_ordnum\n    imp_id\n    imp_provider\n    imp_type\n    layer1\n    layer2\n  }\n  customProps {\n    landing_path\n    view_type\n    helix_id\n    helix_yn\n    helix_seed\n    content_cnt\n    event_series_id\n    event_ticket_type\n    play_url\n    banner_uid\n  }\n}\n    "  # noqa # fmt: skip
EPISODE_IMAGES_QUERY: Final[str] = "query viewerInfo($seriesId: Long!, $productId: Long!) {\n  viewerInfo(seriesId: $seriesId, productId: $productId) {\n    item {\n      ...SingleFragment\n      __typename\n    }\n    seriesItem {\n      ...SeriesFragment\n      __typename\n    }\n    prevItem {\n      ...NearItemFragment\n      __typename\n    }\n    nextItem {\n      ...NearItemFragment\n      __typename\n    }\n    viewerData {\n      ...TextViewerData\n      ...TalkViewerData\n      ...ImageViewerData\n      ...VodViewerData\n      __typename\n    }\n    displayAd {\n      ...DisplayAd\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment SingleFragment on Single {\n  id\n  productId\n  seriesId\n  title\n  thumbnail\n  badge\n  isFree\n  ageGrade\n  state\n  slideType\n  lastReleasedDate\n  size\n  pageCount\n  isHidden\n  remainText\n  isWaitfreeBlocked\n  saleState\n  series {\n    ...SeriesFragment\n    __typename\n  }\n  serviceProperty {\n    ...ServicePropertyFragment\n    __typename\n  }\n  operatorProperty {\n    ...OperatorPropertyFragment\n    __typename\n  }\n  assetProperty {\n    ...AssetPropertyFragment\n    __typename\n  }\n}\n\nfragment SeriesFragment on Series {\n  id\n  seriesId\n  title\n  thumbnail\n  categoryUid\n  category\n  categoryType\n  subcategoryUid\n  subcategory\n  badge\n  isAllFree\n  isWaitfree\n  ageGrade\n  state\n  onIssue\n  authors\n  description\n  pubPeriod\n  freeSlideCount\n  lastSlideAddedDate\n  waitfreeBlockCount\n  waitfreePeriodByMinute\n  bm\n  saleState\n  startSaleDt\n  serviceProperty {\n    ...ServicePropertyFragment\n    __typename\n  }\n  operatorProperty {\n    ...OperatorPropertyFragment\n    __typename\n  }\n  assetProperty {\n    ...AssetPropertyFragment\n    __typename\n  }\n}\n\nfragment ServicePropertyFragment on ServiceProperty {\n  viewCount\n  readCount\n  ratingCount\n  ratingSum\n  commentCount\n  pageContinue {\n    ...ContinueInfoFragment\n    __typename\n  }\n  todayGift {\n    ...TodayGift\n    __typename\n  }\n  preview {\n    ...PreviewFragment\n    ...PreviewFragment\n    ...PreviewFragment\n    __typename\n  }\n  waitfreeTicket {\n    ...WaitfreeTicketFragment\n    __typename\n  }\n  isAlarmOn\n  isLikeOn\n  ticketCount\n  purchasedDate\n  lastViewInfo {\n    ...LastViewInfoFragment\n    __typename\n  }\n  purchaseInfo {\n    ...PurchaseInfoFragment\n    __typename\n  }\n  preview {\n    ...PreviewFragment\n    __typename\n  }\n}\n\nfragment ContinueInfoFragment on ContinueInfo {\n  title\n  isFree\n  productId\n  lastReadProductId\n  scheme\n  continueProductType\n  hasNewSingle\n  hasUnreadSingle\n}\n\nfragment TodayGift on TodayGift {\n  id\n  uid\n  ticketType\n  ticketKind\n  ticketCount\n  ticketExpireAt\n  ticketExpiredText\n  isReceived\n}\n\nfragment PreviewFragment on Preview {\n  item {\n    ...PreviewSingleFragment\n    __typename\n  }\n  nextItem {\n    ...PreviewSingleFragment\n    __typename\n  }\n  usingScroll\n}\n\nfragment PreviewSingleFragment on Single {\n  id\n  productId\n  seriesId\n  title\n  thumbnail\n  badge\n  isFree\n  ageGrade\n  state\n  slideType\n  lastReleasedDate\n  size\n  pageCount\n  isHidden\n  remainText\n  isWaitfreeBlocked\n  saleState\n  operatorProperty {\n    ...OperatorPropertyFragment\n    __typename\n  }\n  assetProperty {\n    ...AssetPropertyFragment\n    __typename\n  }\n}\n\nfragment OperatorPropertyFragment on OperatorProperty {\n  thumbnail\n  copy\n  helixImpId\n  isTextViewer\n  selfCensorship\n}\n\nfragment AssetPropertyFragment on AssetProperty {\n  bannerImage\n  cardImage\n  cardTextImage\n  cleanImage\n  ipxVideo\n}\n\nfragment WaitfreeTicketFragment on WaitfreeTicket {\n  chargedPeriod\n  chargedCount\n  chargedAt\n}\n\nfragment LastViewInfoFragment on LastViewInfo {\n  isDone\n  lastViewDate\n  rate\n  spineIndex\n}\n\nfragment PurchaseInfoFragment on PurchaseInfo {\n  purchaseType\n  rentExpireDate\n  expired\n}\n\nfragment NearItemFragment on NearItem {\n  productId\n  slideType\n  ageGrade\n  isFree\n  title\n  thumbnail\n}\n\nfragment TextViewerData on TextViewerData {\n  type\n  atsServerUrl\n  metaSecureUrl\n  contentsList {\n    chapterId\n    contentId\n    secureUrl\n    __typename\n  }\n}\n\nfragment TalkViewerData on TalkViewerData {\n  type\n  talkDownloadData {\n    dec\n    host\n    path\n    talkViewerType\n    __typename\n  }\n}\n\nfragment ImageViewerData on ImageViewerData {\n  type\n  imageDownloadData {\n    ...ImageDownloadData\n    __typename\n  }\n}\n\nfragment ImageDownloadData on ImageDownloadData {\n  files {\n    ...ImageDownloadFile\n    __typename\n  }\n  totalCount\n  totalSize\n  viewDirection\n  gapBetweenImages\n  readType\n}\n\nfragment ImageDownloadFile on ImageDownloadFile {\n  no\n  size\n  secureUrl\n  width\n  height\n}\n\nfragment VodViewerData on VodViewerData {\n  type\n  vodDownloadData {\n    contentId\n    drmType\n    endpointUrl\n    width\n    height\n    duration\n    __typename\n  }\n}\n\nfragment DisplayAd on DisplayAd {\n  sectionUid\n  bannerUid\n  treviUid\n  momentUid\n}\n"  # noqa # fmt: skip


class KakaopageScraper(Scraper[int]):
    """Scrape webtoons from Kakaopage."""

    BASE_URL = "https://page.kakao.com"
    TEST_WEBTOON_ID = 53397318  # 부기영화
    URL_REGEX = re.compile(r"(?:https?:\/\/)?page[.]kakao[.]com\/content\/(?P<webtoon_id>\d+)")
    DEFAULT_IMAGE_FILE_EXTENSION = "jpg"
    DOWNLOAD_INTERVAL = 0.5
    PLATFORM = "kakaopage"
    INFORMATION_VARS = Scraper.INFORMATION_VARS | dict(
        episodes_free_status=None,
    )

    def __init__(self, webtoon_id: int):
        super().__init__(webtoon_id)
        self.headers = {}
        self.graphql_headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko,en-US;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            # "Cookie": self.cookie,
            "Dnt": "1",
            "Origin": "https://page.kakao.com",
            "Pragma": "no-cache",
            "Referer": "https://page.kakao.com/content/53397318",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Gpc": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        res = self.hxoptions.get(f"https://page.kakao.com/content/{self.webtoon_id}")

        title = res.soup_select_one('meta[property="og:title"]', no_empty_result=True).get("content")
        if title == "카카오페이지" or not isinstance(title, str):
            raise InvalidWebtoonIdError.from_webtoon_id(self.webtoon_id, type(self), rating_notice=True)

        thumbnail_url = res.soup_select_one('meta[property="og:image"]', no_empty_result=True).get("content")
        assert isinstance(thumbnail_url, str)

        self.title = title
        self.webtoon_thumbnail_url = thumbnail_url

    @reload_manager
    def fetch_episode_information(self, *, reload: bool = False) -> None:
        curser = "0"
        # episode_length: int = 0
        has_next_page: bool = True
        webtoon_episodes_data = []
        while has_next_page:
            post_data = {
                "query": WEBTOON_DATA_QUERY,
                "variables": {
                    "boughtOnly": False,
                    "after": curser,
                    "seriesId": self.webtoon_id,
                    "sortType": "asc",
                },
            }

            res = self.hxoptions.post(
                "https://page.kakao.com/graphql",
                json=post_data,
                headers=self.graphql_headers,
            )

            webtoon_raw_data = res.json()["data"]["contentHomeProductList"]

            # episode_length = webtoon_raw_data["totalCount"]
            has_next_page = webtoon_raw_data["pageInfo"]["hasNextPage"]
            curser = webtoon_raw_data["pageInfo"]["endCursor"]
            webtoon_episodes_data += webtoon_raw_data["edges"]

        # urls: list[str] = []
        episode_ids: list[int] = []
        episodes_free_status: list[bool] = []
        subtitles: list[str] = []
        for webtoon_episode_data in webtoon_episodes_data:
            # urls += "https://page.kakao.com/" + raw_url.removeprefix("kakaopage://open/")
            episode_ids.append(webtoon_episode_data["node"]["single"]["productId"])  # 에피소드 id
            episodes_free_status.append(webtoon_episode_data["node"]["single"]["isFree"])  # 무료인지 여부
            subtitles.append(webtoon_episode_data["node"]["single"]["title"])

        self.episode_titles = subtitles
        self.episode_ids = episode_ids
        self.episodes_free_status = episodes_free_status

    def get_episode_image_urls(self, episode_no) -> list[str]:
        episode_id = self.episode_ids[episode_no]

        post_data = {
            "operationName": "viewerInfo",
            "query": EPISODE_IMAGES_QUERY,
            "variables": {"seriesId": self.webtoon_id, "productId": episode_id},
        }

        res = self.hxoptions.post(
            "https://page.kakao.com/graphql",
            json=post_data,
            headers=self.graphql_headers,
        ).json()["data"]

        return [i["secureUrl"] for i in res["viewerInfo"]["viewerData"]["imageDownloadData"]["files"]]
