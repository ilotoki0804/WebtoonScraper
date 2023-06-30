'''Download Webtoons from Naver Post.
'''
from pathlib import Path
from itertools import count
import asyncio
from async_lru import alru_cache
import demjson3
from bs4 import BeautifulSoup
# from WebtoonScraper.Scraper import Scraper
from WebtoonScraper.Scraper import Scraper

class NaverPostScraper(Scraper):
    '''Scrape webtoons from Naver Post.'''
    def __init__(self, pbar_independent=False, short_connection=False):
        super().__init__(pbar_independent, short_connection)
        self.BASE_URL = 'https://post.naver.com'
        if not short_connection:
            self.IS_STABLE_CONNECTION = True

    def download_one_webtoon(self, titleid: int, member_no: int,  value_range: tuple|int|None=None) -> None:
        """async를 사용하지 않는 일반 상태일 경우 사용하는 함수이다. 사용법은 download_one_webtoon_async와 동일하다."""
        asyncio.run(self.download_one_webtoon_async(titleid, member_no,  value_range))
        # self.loop.run_until_complete(self.download_one_webtoon_async(titleid, value_range))

    async def download_one_webtoon_async(self, titleid, member_no: int, episode_no_range: tuple|int|None=None) -> None:
        """포스트는 member_no도 받아야 하기 때문에 불가피하게 수정이 필요."""
        self.member_no = member_no
        await super().download_one_webtoon_async(titleid, episode_no_range)

    @alru_cache(maxsize=4)
    async def _get_webtoon_infomation(self, titleid: int) -> list:
        subtitle_list = []
        for i in count(1):
            subtitle_sublist = []
            # n번째 리스트 불러옴
            url = f'https://post.naver.com/my/series/detail/more.nhn?memberNo={self.member_no}&seriesNo={titleid}&lastSortOrder=49&prevVolumeNo=&fromNo={i}&totalCount=68'
            # print(url)
            response = await self.get_internet('requests', url)

            # 네이버는 기본적으로 json이 망가져 있기에 json이 망가져 있어도 parse를 해주는 demjson이 필요
            demres = demjson3.decode(response.text)['html']
            soup = BeautifulSoup(demres, 'html.parser')
            
            # subtitle data만듦.
            for tag in soup.select('ul > li > a > div > span.ell'):
                subtitle_sublist.append({'subtitle' : tag.text.strip()})
            for j, tag in enumerate(soup.select('ul > li > a > div > span.spot_post_like')):
                # 버려지는 값은 member_no/그냥 member_no라고 해도 되지만 혹시 모를 corruption을 막기 위한 조치
                episode_id, _ = map(int, tag['data-cid'].split('_'))
                subtitle_sublist[j].update({'episode_id': episode_id, 'member_no': self.member_no})
            
            # 지금 받아온 데이터가 이전 데이터와 같은지 확인
            if subtitle_sublist == subtitle_list[-len(subtitle_sublist):]:
                break
            else:
                subtitle_list += subtitle_sublist
        # 1화부터로 변경
        return subtitle_list[::-1]

    async def get_title(self, titleid, file_acceptable=True):
        url = f'https://m.post.naver.com/my/series/detail.naver?seriesNo={titleid}&memberNo={self.member_no}'
        title = await self.get_internet(get_type='soup_select_one', url=url,
                                        selector='h2.tit_series > span')
        title = title.text.strip()
        if file_acceptable:
            title = self.get_acceptable_file_name(title)
        return title

    async def save_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        url = f'https://m.post.naver.com/my/series/detail.naver?seriesNo={titleid}&memberNo={self.member_no}'
        image_url = await self.get_internet(get_type='soup_select_one', url=url,
                                            selector='meta[property="og:image"]')
        image_url = image_url['content']
        image_extension = self.get_file_extension(image_url)
        image_raw = await self.get_internet(get_type='requests', url=image_url)
        image_raw = image_raw.content
        Path(f'{thumbnail_dir}/{title}.{image_extension}').write_bytes(image_raw)

    async def get_all_episode_no(self, titleid):
        """1부터 시작하니 주의!!"""
        subtitle_list = await self._get_webtoon_infomation(titleid)
        return (i + 1 for i in range(len(subtitle_list)))

    async def get_subtitle(self, titleid, episode_no, file_acceptable):
        # if sleep:
        #     time.sleep(1)
        subtitle_list = await self._get_webtoon_infomation(titleid)
        subtitle_info = subtitle_list[episode_no - 1]
        subtitle = subtitle_info['subtitle']
        if file_acceptable:
            subtitle = self.get_acceptable_file_name(subtitle)
        return subtitle

    async def get_episode_images_url(self, titleid, episode_no, attempt=3):
        subtitle_list = await self._get_webtoon_infomation(titleid)
        episode_id = subtitle_list[episode_no - 1]['episode_id']
        url = f'https://post.naver.com/viewer/postView.naver?volumeNo={episode_id}&memberNo={self.member_no}&navigationType=push'
        for _ in range(attempt):
            content = await self.get_internet(get_type='soup_select_one', url=url,
                                                    selector='#__clipContent')
            if content is None:
                # '존재하지 않는 포스트입니다'하는 경고가 뜬 후 사이트가 받아지지 않는 오류
                # 아마 episode_id에 titleid가 잘못 들어가면 생기는 오류로 추정하지만
                # 정확한 이유는 불명, 가끔씩 생기는 문제.
                print(f'episode {titleid} invalid. retrying...')
            else:
                break
        else:
            raise ConnectionError('Unknown error occurred. Please try again later.')
        content = content.text
        soup_content = BeautifulSoup(content, 'html.parser')
        
        # 문서 내에 있는 모든 이미지 링크를 불러옴
        selector = 'div.se_component_wrap.sect_dsc.__se_component_area > div > div > div > div > a > img'
        episode_images_url = [tag['data-src'] for tag in soup_content.select(selector)]
        
        return [url for url in episode_images_url 
                if not url.startswith('https://mail.naver.com/read/image/')]
    
if __name__ == '__main__':
    # np = NaverPost()
    # np.download_one_webtoon(625402, 19803452)

    # wt = NaverPost()
    # asyncio.run(wt.get_data(625402, 19803452))

    # wt = NaverPost()
    # wt.member_no = 19803452
    # print(asyncio.run(wt.get_episode_images_url(577056, 2)))

    # from NaverPost import NaverPostScraper
    wt = NaverPostScraper()
    # wt.download_one_webtoon(614921, 19803452)
    wt.download_one_webtoon(577056, 19803452)
    wt.download_one_webtoon(625402, 19803452)