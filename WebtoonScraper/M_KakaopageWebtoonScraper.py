'''Download Webtoons from Kakaopage.'''

from __future__ import annotations
from itertools import count

from async_lru import alru_cache
from requests_utils import requests

if __name__ in ("__main__", "M_KakaopageWebtoonScraper"):
    from C_Scraper import Scraper
else:
    from .C_Scraper import Scraper


class KakaopageWebtoonScraper(Scraper):
    '''Scrape webtoons from Kakaopage.'''
    def __init__(self, pbar_independent=False, cookie: str = ''):
        super().__init__(pbar_independent)
        self.BASE_URL = 'https://page.kakao.com'
        self.IS_STABLE_CONNECTION = False
        self.COOKIE = cookie
        self.HEADERS = {
            "Accept": "application/graphql+json, application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko,en-US;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Content-Length": "4371",
            "Content-Type": "application/json",
            "Cookie": self.COOKIE,
            "Dnt": "1",
            "Origin": "https://page.kakao.com",
            "Pragma": "no-cache",
            "Referer": "https://page.kakao.com/content/53397318/viewer/53486401",
            "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Microsoft Edge";v="115", "Chromium";v="115"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Gpc": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        }

    @alru_cache(maxsize=4)
    async def get_webtoon_data(self, titleid: int):
        res = requests.get("https://page.kakao.com/content/53397318")
        title = res.soup_select_one('meta[property="og:title"]', no_empty_result=True).get("content")
        thumnail_url = res.soup_select_one('meta[property="og:image"]', no_empty_result=True).get("content")

        query = "query contentHomeProductList($after: String, $before: String, $first: Int, $last: Int, $seriesId: Long!, $boughtOnly: Boolean, $sortType: String) {\n  contentHomeProductList(\n    seriesId: $seriesId\n    after: $after\n    before: $before\n    first: $first\n    last: $last\n    boughtOnly: $boughtOnly\n    sortType: $sortType\n  ) {\n    totalCount\n    pageInfo {\n      hasNextPage\n      endCursor\n      hasPreviousPage\n      startCursor\n      __typename\n    }\n    selectedSortOption {\n      id\n      name\n      param\n      __typename\n    }\n    sortOptionList {\n      id\n      name\n      param\n      __typename\n    }\n    edges {\n      cursor\n      node {\n        ...SingleListViewItem\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment SingleListViewItem on SingleListViewItem {\n  id\n  type\n  thumbnail\n  showPlayerIcon\n  isCheckMode\n  isChecked\n  scheme\n  row1 {\n    badgeList\n    title\n    __typename\n  }\n  row2\n  row3\n  single {\n    productId\n    ageGrade\n    id\n    isFree\n    thumbnail\n    title\n    slideType\n    operatorProperty {\n      isTextViewer\n      __typename\n    }\n    __typename\n  }\n  isViewed\n  purchaseInfoText\n  eventLog {\n    ...EventLogFragment\n    __typename\n  }\n}\n\nfragment EventLogFragment on EventLog {\n  fromGraphql\n  click {\n    layer1\n    layer2\n    setnum\n    ordnum\n    copy\n    imp_id\n    imp_provider\n    __typename\n  }\n  eventMeta {\n    id\n    name\n    subcategory\n    category\n    series\n    provider\n    series_id\n    type\n    __typename\n  }\n  viewimp_contents {\n    type\n    name\n    id\n    imp_area_ordnum\n    imp_id\n    imp_provider\n    imp_type\n    layer1\n    layer2\n    __typename\n  }\n  customProps {\n    landing_path\n    view_type\n    toros_imp_id\n    toros_file_hash_key\n    toros_event_meta_id\n    content_cnt\n    event_series_id\n    event_ticket_type\n    play_url\n    banner_uid\n    __typename\n  }\n}\n"

        curser = 0
        # episode_length: int = 0
        has_next_page: bool = True
        webtoon_episodes_data = []
        while has_next_page:
            post_data = {
                "operationName": "contentHomeProductList",
                "query": query,
                "variables": {"seriesId": titleid, "after": str(curser), "boughtOnly": False, "sortType": "asc"},
            }

            res = requests.post(
                "https://page.kakao.com/graphql",
                json=post_data,
                headers=self.HEADERS,
            )

            webtoon_raw_data = res.json()["data"]["contentHomeProductList"]

            # episode_length = webtoon_raw_data["totalCount"]
            has_next_page = webtoon_raw_data["pageInfo"]["hasNextPage"]
            curser = webtoon_raw_data["pageInfo"]["endCursor"]
            webtoon_episodes_data += webtoon_raw_data["edges"]

        # urls: list[str] = []
        episode_ids: list[int] = []
        is_free: list[bool] = []
        subtitles: list[str] = []
        for webtoon_episode_data in webtoon_episodes_data:
            # urls += "https://page.kakao.com/" + raw_url.removeprefix("kakaopage://open/")
            episode_ids.append(webtoon_episode_data["node"]["single"]["productId"])  # 에피소드 id
            is_free.append(webtoon_episode_data["node"]["single"]["isFree"])  # 무료인지 여부
            subtitles.append(webtoon_episode_data["node"]["single"]["title"])

        return {'subtitles': subtitles, 'episode_ids': episode_ids, 'title': title, 'webtoon_thumbnail': thumnail_url}

    async def download_single_image(self, episode_dir, url: str, image_no: int, default_file_extension: str | None = 'jpg') -> None:
        """Download image from url and returns to {episode_dir}/{file_name(translated to accactable name)}."""
        image_extension = self.get_file_extension(url)

        # for Bufftoon
        if image_extension is None:
            if default_file_extension is None:
                raise ValueError('File extension not detected.')
            image_extension = default_file_extension

        file_name = f'{image_no:03d}.{image_extension}'

        # self._set_pbar(f'{episode_dir}|{file_name}')
        # 'headers' is changed.
        image_raw: bytes = (await self.get_internet(get_type='requests', url=url, is_run_in_executor=True, headers={})).content

        file_dir = episode_dir / file_name
        file_dir.write_bytes(image_raw)

    async def save_webtoon_thumbnail(self, titleid, title: str, thumbnail_dir, default_file_extension: str | None = 'jpg') -> None:
        return await super().save_webtoon_thumbnail(titleid, title, thumbnail_dir, default_file_extension)

    async def get_episode_images_url(self, titleid, episode_no):
        episode_id = await self.episode_no_to_episode_id(titleid, episode_no)

        query = "query viewerInfo($seriesId: Long!, $productId: Long!) {\n  viewerInfo(seriesId: $seriesId, productId: $productId) {\n    item {\n      ...SingleFragment\n      __typename\n    }\n    seriesItem {\n      ...SeriesFragment\n      __typename\n    }\n    prevItem {\n      ...NearItemFragment\n      __typename\n    }\n    nextItem {\n      ...NearItemFragment\n      __typename\n    }\n    viewerData {\n      ...TextViewerData\n      ...TalkViewerData\n      ...ImageViewerData\n      ...VodViewerData\n      __typename\n    }\n    displayAd {\n      ...DisplayAd\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment SingleFragment on Single {\n  id\n  productId\n  seriesId\n  title\n  thumbnail\n  badge\n  isFree\n  ageGrade\n  state\n  slideType\n  lastReleasedDate\n  size\n  pageCount\n  isHidden\n  remainText\n  isWaitfreeBlocked\n  saleState\n  series {\n    ...SeriesFragment\n    __typename\n  }\n  serviceProperty {\n    ...ServicePropertyFragment\n    __typename\n  }\n  operatorProperty {\n    ...OperatorPropertyFragment\n    __typename\n  }\n  assetProperty {\n    ...AssetPropertyFragment\n    __typename\n  }\n}\n\nfragment SeriesFragment on Series {\n  id\n  seriesId\n  title\n  thumbnail\n  categoryUid\n  category\n  categoryType\n  subcategoryUid\n  subcategory\n  badge\n  isAllFree\n  isWaitfree\n  is3HoursWaitfree\n  ageGrade\n  state\n  onIssue\n  authors\n  pubPeriod\n  freeSlideCount\n  lastSlideAddedDate\n  waitfreeBlockCount\n  waitfreePeriodByMinute\n  bm\n  saleState\n  serviceProperty {\n    ...ServicePropertyFragment\n    __typename\n  }\n  operatorProperty {\n    ...OperatorPropertyFragment\n    __typename\n  }\n  assetProperty {\n    ...AssetPropertyFragment\n    __typename\n  }\n}\n\nfragment ServicePropertyFragment on ServiceProperty {\n  viewCount\n  readCount\n  ratingCount\n  ratingSum\n  commentCount\n  pageContinue {\n    ...ContinueInfoFragment\n    __typename\n  }\n  todayGift {\n    ...TodayGift\n    __typename\n  }\n  waitfreeTicket {\n    ...WaitfreeTicketFragment\n    __typename\n  }\n  isAlarmOn\n  isLikeOn\n  ticketCount\n  purchasedDate\n  lastViewInfo {\n    ...LastViewInfoFragment\n    __typename\n  }\n  purchaseInfo {\n    ...PurchaseInfoFragment\n    __typename\n  }\n}\n\nfragment ContinueInfoFragment on ContinueInfo {\n  title\n  isFree\n  productId\n  lastReadProductId\n  scheme\n  continueProductType\n  hasNewSingle\n  hasUnreadSingle\n}\n\nfragment TodayGift on TodayGift {\n  id\n  uid\n  ticketType\n  ticketKind\n  ticketCount\n  ticketExpireAt\n  ticketExpiredText\n  isReceived\n}\n\nfragment WaitfreeTicketFragment on WaitfreeTicket {\n  chargedPeriod\n  chargedCount\n  chargedAt\n}\n\nfragment LastViewInfoFragment on LastViewInfo {\n  isDone\n  lastViewDate\n  rate\n  spineIndex\n}\n\nfragment PurchaseInfoFragment on PurchaseInfo {\n  purchaseType\n  rentExpireDate\n  expired\n}\n\nfragment OperatorPropertyFragment on OperatorProperty {\n  thumbnail\n  copy\n  torosImpId\n  torosFileHashKey\n  isTextViewer\n}\n\nfragment AssetPropertyFragment on AssetProperty {\n  bannerImage\n  cardImage\n  cardTextImage\n  cleanImage\n  ipxVideo\n}\n\nfragment NearItemFragment on NearItem {\n  productId\n  slideType\n  ageGrade\n  isFree\n  title\n  thumbnail\n}\n\nfragment TextViewerData on TextViewerData {\n  type\n  atsServerUrl\n  metaSecureUrl\n  contentsList {\n    chapterId\n    contentId\n    secureUrl\n    __typename\n  }\n}\n\nfragment TalkViewerData on TalkViewerData {\n  type\n  talkDownloadData {\n    dec\n    host\n    path\n    talkViewerType\n    __typename\n  }\n}\n\nfragment ImageViewerData on ImageViewerData {\n  type\n  imageDownloadData {\n    ...ImageDownloadData\n    __typename\n  }\n}\n\nfragment ImageDownloadData on ImageDownloadData {\n  files {\n    ...ImageDownloadFile\n    __typename\n  }\n  totalCount\n  totalSize\n  viewDirection\n  gapBetweenImages\n  readType\n}\n\nfragment ImageDownloadFile on ImageDownloadFile {\n  no\n  size\n  secureUrl\n  width\n  height\n}\n\nfragment VodViewerData on VodViewerData {\n  type\n  vodDownloadData {\n    contentId\n    drmType\n    endpointUrl\n    width\n    height\n    duration\n    __typename\n  }\n}\n\nfragment DisplayAd on DisplayAd {\n  sectionUid\n  bannerUid\n  treviUid\n  momentUid\n}\n"

        post_data = {
            "operationName": "viewerInfo",
            "query": query,
            "variables": {"seriesId": titleid, "productId": episode_id},
        }

        res = requests.post(
            "https://page.kakao.com/graphql",
            json=post_data,
            headers=self.HEADERS,
        ).json()

        return [i['secureUrl']
                for i in res["data"]["viewerInfo"]["viewerData"]["imageDownloadData"]["files"]]

    async def check_if_legitimate_titleid(self, titleid: int) -> str | None:
        """If titleid is legitimate, return title. Otherwise, return None"""

        res = requests.get(f"https://page.kakao.com/content/{titleid}")
        if res.soup_select_one("title", no_empty_result=True).text == '콘텐츠홈 | 카카오페이지':
            return None

        title = res.soup_select_one('meta[property="og:title"]', no_empty_result=True).get("content")
        # sourcery skip
        if not isinstance(title, str):  # for typing purpose. Works fine even if remove this statement.
            return None
        return title.removesuffix(' | 카카오페이지')


if __name__ == '__main__':
    wt = KakaopageWebtoonScraper()
    wt.download_one_webtoon(53397318)  # 부기
