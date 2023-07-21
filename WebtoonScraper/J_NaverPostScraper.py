'''Download Webtoons from Naver Post.'''
# TODO: subtitle_list에서 subtitles로 변경하기

from pathlib import Path
from itertools import count
import asyncio
# import logging

from async_lru import alru_cache
import demjson3
from bs4 import BeautifulSoup

if __name__ in ("__main__", "J_NaverPostScraper"):
    # logging.warning('Using ')
    from C_Scraper import Scraper
else:
    from .C_Scraper import Scraper


class NaverPostScraper(Scraper):
    '''Scrape webtoons from Naver Post.'''
    def __init__(self, pbar_independent=False):
        super().__init__(pbar_independent)
        self.IS_STABLE_CONNECTION = True
        self.BASE_URL = 'https://post.naver.com'

    @alru_cache(maxsize=4)
    async def get_webtoon_data(self, titleid: tuple[int, int]) -> dict[str, list]:
        # sourcery skip: for-append-to-extend, list-comprehension, move-assign-in-block
        series_no, member_no = titleid
        subtitle_list: list[str] = []
        episode_id_list: list[int] = []
        prev_data = None
        for i in count(1):
            # n번째 리스트 불러옴
            url = (f'https://post.naver.com/my/series/detail/more.nhn'
                   f'?memberNo={member_no}&seriesNo={series_no}&lastSortOrder=49'
                   f'&prevVolumeNo=&fromNo={i}&totalCount=68')
            # print(url)
            response_text: str = (await self.get_internet('requests', url)).text

            # 네이버는 기본적으로 json이 망가져 있기에 json이 망가져 있어도 parse를 해주는 demjson이 필요
            decoded_response_data: str = demjson3.decode(response_text)['html']
            soup = BeautifulSoup(decoded_response_data, 'html.parser')

            # subtitle data만듦.
            for tag in soup.select('ul > li > a > div > span.ell'):
                # subtitle_list.append({'subtitle': tag.text.strip()})
                subtitle_list.append(tag.text.strip())
            for tag in soup.select('ul > li > a > div > span.spot_post_like'):
                episode_id, _ = map(int, tag['data-cid'].split('_'))
                episode_id_list.append(episode_id)

            if prev_data == decoded_response_data:
                break

            prev_data = decoded_response_data

        # 1화부터로 변경
        return {'subtitles': subtitle_list[::-1], 'episode_ids': episode_id_list[::-1]}

    async def get_title(self, titleid: tuple[int, int]):
        series_no, member_no = titleid
        url = f'https://m.post.naver.com/my/series/detail.naver?seriesNo={series_no}&memberNo={member_no}'
        title: str = (await self.get_internet(get_type='soup_select_one', url=url,
                                              selector='h2.tit_series > span')).text
        return title.strip()

    async def save_webtoon_thumbnail(self, titleid: tuple[int, int], title, thumbnail_dir):
        series_no, member_no = titleid
        url = f'https://m.post.naver.com/my/series/detail.naver?seriesNo={series_no}&memberNo={member_no}'
        image_url_original = await self.get_internet(get_type='soup_select_one', url=url,
                                            selector='meta[property="og:image"]')
        if not image_url_original:
            raise ConnectionError('Naver Post changed their api specification. Contect developer to update save_webtoon_thumbnail.')
        image_url: str = image_url_original['content']
        image_extension = self.get_file_extension(image_url)
        image_raw: bytes = (await self.get_internet(get_type='requests', url=image_url)).content
        Path(f'{thumbnail_dir}/{title}.{image_extension}').write_bytes(image_raw)
        (thumbnail_dir / f'{title}.{image_extension}').write_bytes(image_raw)

    async def get_all_episode_no(self, titleid):
        """1부터 시작하니 주의!!"""
        return await super().get_all_episode_no(titleid)

    async def get_subtitle(self, titleid, episode_no):
        return await super().get_subtitle(titleid, episode_no)

    async def get_episode_images_url(self, titleid, episode_no, attempt=3):
        series_no, member_no = titleid
        episode_id = await self.episode_no_to_episode_id(titleid, episode_no)
        url = f'https://post.naver.com/viewer/postView.naver?volumeNo={episode_id}&memberNo={member_no}&navigationType=push'
        for _ in range(attempt):
            content = await self.get_internet(get_type='soup_select_one', url=url,
                                              selector='#__clipContent')
            if content is None:
                # '존재하지 않는 포스트입니다'하는 경고가 뜬 후 사이트가 받아지지 않는 오류
                # 아마 episode_id에 titleid가 잘못 들어가면 생기는 오류로 추정하지만
                # 정확한 이유는 불명, 가끔씩 생기는 문제.
                print(f'episode {episode_id} invalid. retrying...')
            else:
                break
        else:
            raise ConnectionError('Unknown error occurred. Please try again later.')
        content = content.text
        soup_content = BeautifulSoup(content, 'html.parser')

        # 문서 내에 있는 모든 이미지 링크를 불러옴
        selector = 'div.se_component_wrap.sect_dsc.__se_component_area > div > div > div > div > a > img'
        episode_images_url: list[str] = [tag['data-src'] for tag in soup_content.select(selector)]

        return [url for url in episode_images_url
                if not url.startswith('https://mail.naver.com/read/image/')]


if __name__ == '__main__':
    # logger = logging.getLogger()
    # logger.setLevel(logging.INFO)

    wt = NaverPostScraper()
    wt.download_one_webtoon((597061, 19803452))  # 겜덕겜소

    asyncio.run(wt.get_webtoon_data((577056, 19803452)))  # 겜덕툰

    # wt = NaverPostScraper()
    # wt.member_no = 19803452
    # print(asyncio.run(wt.get_episode_images_url(577056, 2)))
