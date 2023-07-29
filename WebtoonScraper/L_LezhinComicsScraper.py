'''Download Webtoons from Lezhin Comics.'''
# from itertools import count
import logging
from pathlib import Path
import os
import re
import json
import shutil
import multiprocessing

from tqdm import tqdm
from async_lru import alru_cache
import pyjsparser
from PIL import Image

if __name__ in ("__main__", "L_LezhinComicsScraper"):
    from C_Scraper import Scraper
else:
    # from Scraper import Scraper
    from .C_Scraper import Scraper


class LezhinComicsScraper(Scraper):
    '''Scrape webtoons from Lezhin Comics.'''
    def __init__(self, pbar_independent=False):
        super().__init__(pbar_independent)
        self.BASE_URL = 'https://www.lezhin.com/ko/comic'
        self.IS_STABLE_CONNECTION = True
        self.EPISODE_IMAGES_URL_SELECTOR = '#sectionContWide > img'  # for best challenge
        self.COOKIE: str = ''
        self.AUTHORIZATION: str = ''

        self.UNSHUFFLE = True
        self.DELETE_SHUFFLED_FILE = False

    async def get_webtoon_dir_name(self, titleid, title: str) -> str:
        is_shuffled = (await self.get_webtoon_data(titleid))['is_shuffled']
        return f'{title}({titleid}, shuffled)' if is_shuffled else f'{title}({titleid})'

    async def lezhin_unshuffle_process(self, titleid, base_webtoon_dir: Path):
        """For lezhin's shuffle process. This function changes webtoon_dir to unshuffled webtoon's directory."""
        is_shuffled = (await self.get_webtoon_data(titleid))['is_shuffled']
        if not is_shuffled:
            return base_webtoon_dir
        alt_webtoon_dir = Path(str(base_webtoon_dir).removesuffix(', shuffled)') + ')')
        alt_webtoon_dir.mkdir(exist_ok=True)
        if is_shuffled and self.UNSHUFFLE:
            await self.unshuffle_webtoon(titleid, base_webtoon_dir, alt_webtoon_dir)

        if self.DELETE_SHUFFLED_FILE:
            shutil.rmtree(base_webtoon_dir)
            logging.info('Shuffle file is deleted.')

        return alt_webtoon_dir

    @alru_cache(maxsize=4)
    async def get_webtoon_data(self, titleid: str):
        """Default titleid is titleid_str, and default episode_id is episode_id_str, which is displayed to users."""
        soup = await self.get_internet('soup', f'{self.BASE_URL}/{titleid}', )
        if soup.select_one('meta[property="og:title"]') == "404 - 레진코믹스":
            raise ValueError(f'Invalid {titleid = }')

        title = soup.select_one("h2.comicInfo__title").text
        thumbnail_url = soup.select_one('meta[property="og:image"]')["content"]

        parsed = pyjsparser.parse(soup.select("script")[5].text.removeprefix("<script>").removesuffix("</script>"))

        # title = parsed["body"][1]["expression"]["right"]["properties"][1]["value"]["properties"][1]["value"]["properties"][0]["value"]["value"]
        titleid_int = int(parsed["body"][1]["expression"]["right"]["properties"][1]["value"]["properties"][0]["value"]["raw"])  # ~ contentId
        logging.debug(f'length of body > 1 > 1: {parsed["body"][1]["expression"]["right"]["properties"][1]["value"]["properties"]}')
        episodes_data = parsed["body"][1]["expression"]["right"]["properties"][1]["value"]["properties"][-1]["value"]["elements"]
        # is_shuffled: bool = parsed["body"][1]["expression"]["right"]["properties"][1]["value"]["properties"][19]["value"]["properties"][0]["value"]["value"]  # imageShuffle

        def determine_is_shuffled(parsed):
            for property_index in range(20):
                for possibily_shuffled in parsed["body"][1]["expression"]["right"]["properties"][1]["value"]["properties"]:
                    try:
                        attribute = possibily_shuffled["value"]["properties"][property_index]["key"]["value"]
                    except (KeyError, IndexError):
                        continue
                    else:
                        if attribute == "imageShuffle":
                            return possibily_shuffled["value"]["properties"][property_index]["value"]["value"]
            return False
        is_shuffled = determine_is_shuffled(parsed)

        episode_id_strings = []
        subtitles = []
        episode_id_integers = []
        infomation_chars = []
        for episode in episodes_data:
            episode_id_str: str = episode["properties"][1]["value"]["value"]
            subtitle = episode["properties"][2]["value"]["properties"][0]["value"]["value"]
            episode_id_int: int = int(episode["properties"][0]["value"]["raw"])  # in other words, 'episodeId'

            # n, e, g 등. episode_id_str의 x(특별편)은 e로 바뀌는 듯함.
            infomation_char = episode["properties"][2]["value"]["properties"][1]["value"]['value']
            expired = episode["properties"][3]["value"]["properties"][0]["value"]['value']
            not_for_sale = episode["properties"][3]["value"]["properties"][1]["value"]['value']

            if infomation_char != 'g':
                logging.debug(f'Unique {infomation_char = } of {subtitle}')
            if not_for_sale:
                logging.warning(f'This episode is not for sale: {subtitle}')
            if expired:
                logging.warning(f'This episode is expired: {subtitle}')
            if infomation_char != 'g' and not episode_id_str.startswith(infomation_char):
                logging.warning(f'{infomation_char = } is not matched with {episode_id_str = }')

            # print(f'{episode_id_str = }, {subtitle = }, {expired = }, {not_for_sale = }, {episode_id_int = }, {infomation_char = }')
            episode_id_strings.append(episode_id_str)
            subtitles.append(subtitle)
            episode_id_integers.append(episode_id_int)
            infomation_chars.append(infomation_char)

        # 현재 titleid_str(titleid와 동일)과 infomation_chars는 사용되는 곳이 없음
        return {'title': title, 'webtoon_thumbnail': thumbnail_url,
                'episode_ids': episode_id_strings[::-1], 'subtitles': subtitles[::-1],
                'episode_id_integers': episode_id_integers[::-1], 'infomation_chars': infomation_chars[::-1],
                'titleid_str': titleid, 'titleid_int': titleid_int, 'is_shuffled': is_shuffled, }

    async def get_title(self, titleid):
        return await super().get_title(titleid)

    async def save_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        return await super().save_webtoon_thumbnail(titleid, title, thumbnail_dir, default_file_extension='jpg')

    async def get_all_episode_no(self, titleid):
        return await super().get_all_episode_no(titleid)

    async def get_subtitle(self, titleid, episode_no):
        return await super().get_subtitle(titleid, episode_no)

    async def get_episode_images_url(self, titleid, episode_no, _attempt: int = 1):
        # sourcery skip: simplify-fstring-formatting
        HEADERS = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko,en-US;q=0.9,en;q=0.8",
            "Authorization": self.AUTHORIZATION,
            "Cache-Control": "no-cache",
            "Cookie": self.COOKIE,
            "Dnt": "1",
            "Referer": "https://www.lezhin.com/ko/comic/revatoon/x1",
            "Sec-Ch-Ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Gpc": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82",
            "X-Lz-Adult": "0",
            "X-Lz-Allowadult": "false",
            "X-Lz-Country": "kr",
            "X-Lz-Locale": "ko-KR",
        }
        episode_id_str = (await self.get_webtoon_data(titleid))['episode_ids'][episode_no]
        episode_id_int = (await self.get_webtoon_data(titleid))['episode_id_integers'][episode_no]
        titleid_int = (await self.get_webtoon_data(titleid))['titleid_int']

        keygen_url = (f"https://www.lezhin.com/lz-api/v2/cloudfront/signed-url/generate?"
                      f"contentId={titleid_int}&episodeId={episode_id_int}&purchased={'false'}&q={30}&firstCheckType={'P'}")

        keys_res = await self.get_internet('requests', keygen_url, headers=HEADERS)
        if keys_res.status_code == 403:
            logging.warning(f"can't retrieve data from {episode_id_int = }. "
                            "It's probably because Episode is not available or not for free episode.")
            return

        res_json = keys_res.json()["data"]
        lz_policy = res_json["Policy"]
        lz_signature = res_json["Signature"]
        lz_key_pair_id = res_json["Key-Pair-Id"]

        images_retrieve_url = ("https://www.lezhin.com/lz-api/v2/inventory_groups/comic_viewer_k?"
                               f"platform=web&store=web&alias={titleid}&name={episode_id_str}&preload=false"
                               "&type=comic_episode")
        try:
            images_data = (await self.get_internet('requests', images_retrieve_url, headers=HEADERS)).json()
            # return images_data # for debugg purpose
        except json.JSONDecodeError:
            if _attempt >= 3:
                raise
            logging.warning('Retrying json decode...')
            return await self.get_episode_images_url(titleid, episode_no, _attempt=_attempt + 1)
        # print(images_data)

        # created_at = images_data["data"]["createdAt"]
        image_urls = []
        for image_url_data in images_data["data"]["extra"]["episode"]["scrollsInfo"]:
            image_url = (f'https://rcdn.lezhin.com/v2{image_url_data["path"]}'
                         f'.webp?purchased={"false"}&q={30}&updated={1587628135437}'
                         f'&Policy={lz_policy}&Signature={lz_signature}&Key-Pair-Id={lz_key_pair_id}')
            image_urls.append(image_url)

        return image_urls

    async def unshuffle_webtoon(self, titleid, base_webtoon_dir, alt_webtoon_dir, force_unshuffle: bool = False, process_number: int = 8):
        def get_episode_dir_no(episode_dir_name: str):
            # print(episode_dir_name)
            try:
                return int(episode_dir_name.split('.')[0])
            except ValueError as e:
                if episode_dir_name.endswith(('jpg', 'png', 'webp', 'gif', 'bmp')):
                    return
                if re.search(r'^(\d+)~(\d+)', episode_dir_name):
                    raise ValueError(
                        'Episode name is not valid. It\'s because you tried merging already merged webtoon folder. '
                        '`unshuffle_webtoon` does not support merged webtoon.'
                    )
                raise ValueError('`episode_dir_name` is invalid. Maybe you tried to unshuffle merged webtoon directory. '
                                 '`unshuffle_webtoon` does not support merged webtoon.') from e

        # 웹툰을 다운로드 받을 때 유료 웹툰이거나 하는 이유로 일부 에피소드는 다운로드되지 않을 수 있음
        # 하지만 episode_id는 0부터 쭉 존재함.
        # 따라서 다운로드되지 않은 웹툰을 걸러 작업을 하지 않도록 거르는 작업이 필요함.
        # `unshuffle_episode`에서 직접 episode_id를 고르면 복잡한 로직이 필요없지만 그때마다 get_webtoon_data를 불러야 하기에
        # 성능 하락의 우려가 아주 살짝 있음. 하지만 크진 않기에 unshuffle_episode에서 직접 episode_id를 가지는 것도 고려해볼만 함.

        is_shuffled = (await self.get_webtoon_data(titleid))['is_shuffled']
        if not is_shuffled and force_unshuffle:
            if input('trying to unshuffle webtoon that seems to be not shuffled. Proceed anyway? (y to proceed)') != 'y':
                raise ValueError('Trying to unshuffle webtoon that is not shuffled at first place.')

        episode_dir_names_indexed = {get_episode_dir_no(episode_dir_name): episode_dir_name
                                     for episode_dir_name in os.listdir(base_webtoon_dir)
                                     if get_episode_dir_no(episode_dir_name) is not None}
        episode_id_ints = (await self.get_webtoon_data(titleid))['episode_id_integers']

        # self.pbar = tqdm([(episode_dir_names_indexed.get(i + 1), episode_id) for i, episode_id in enumerate(episode_id_ints)])
        episodes_with_episode_id = [(episode_id, episode_dir_names_indexed.get(i + 1)) for i, episode_id in enumerate(episode_id_ints)]
        unshuffle_parameters = []
        for episode_id, episode_dir_name in episodes_with_episode_id:
            if episode_dir_name is None:
                continue
            base_episode_dir = base_webtoon_dir / episode_dir_name
            alt_episode_dir = alt_webtoon_dir / episode_dir_name
            try:
                alt_episode_dir.mkdir()
            except FileExistsError:
                if len(os.listdir(alt_episode_dir)) == len(os.listdir(base_episode_dir)):
                    logging.warning(f'passing {episode_dir_name}')
                    continue
                logging.warning(f'{episode_dir_name} is not valid. Delete items and continue.')
                shutil.rmtree(alt_episode_dir)
                alt_episode_dir.mkdir()
            # self.unshuffle_episode(base_episode_dir, alt_episode_dir, episode_id)
            unshuffle_parameters.append((base_episode_dir, alt_episode_dir, episode_id))

        # self.pbar = tqdm(unshuffle_parameters)
        logging.warning('Unshuffling is started. It takes a while and very CPU-intensive task. '
                        'So keep patient and wait until process end.')
        with multiprocessing.Pool(process_number) as p:
            p.starmap(LezhinComicsScraper.unshuffle_episode, unshuffle_parameters)

        logging.info('Unshuffling ended.')

    @staticmethod
    def unshuffle_episode(base_episode_dir: Path, alt_episode_dir: Path, episode_id_int: int):
        # print(f'{base_episode_dir = }, {alt_episode_dir = }, {episode_id_int = }')
        # return

        def get_random_numbers_of_certain_seed(seed):
            """Mutating Lezhin's random number generator. `random_numbers` are always same if given seed is same."""
            results = []
            state = seed
            for _ in range(25):
                state ^= state >> 12
                state ^= (state << 25) & 18446744073709551615
                state ^= state >> 27
                result = (state >> 32) % 25
                results.append(result)
            return results

        def get_image_order_from_random_number(random_numbers):
            image_order = list(range(25))
            for i in range(25):
                shuffle_index = random_numbers[i]
                image_order[i], image_order[shuffle_index] = image_order[shuffle_index], image_order[i]
            return image_order

        def unshuffle_image_and_save(base_image_path, alt_image_path, image_order, margin: int | None = None):
            with Image.open(base_image_path) as im:
                image_x, image_y = im.size
                # MARGIN = image_y % 5 * 5
                MARGIN = image_y % 5 if margin is None else margin
                # im = im.resize((image_x * 5, image_y * 5), Image.Resampling.NEAREST)
                image_x, image_y = im.size
                image_y -= MARGIN  # margin
                # print((image_x, image_y))
                cropped_images: list[Image.Image] = [None] * 25
                for index_x, left, right in ((i, i * image_x // 5, (i + 1) * image_x // 5) for i in range(5)):
                    for index_y, upper, lower in ((i, i * image_y // 5, (i + 1) * image_y // 5) for i in range(5)):
                        cropped_image: Image.Image = im.crop(
                            (left, upper, right, lower))
                        # draw = ImageDraw.Draw(cropped_image)
                        image_index = index_x + index_y * 5
                        cropped_images[image_order.index(image_index)] = cropped_image

                def position_in_assambled_image(image_index) -> tuple[int, int]:
                    index_x, index_y = divmod(image_index, 5)
                    image_x, image_y = im.size
                    image_y -= MARGIN
                    return index_y * image_x, index_x * image_y

                assambled_image = Image.new("RGB", (image_x, image_y), (256, 0, 0))
                for i, cropped_image in enumerate(cropped_images):
                    assambled_image.paste(cropped_image, tuple(
                        j // 5 for j in position_in_assambled_image(i)))
                assambled_image.save(alt_image_path)

        # self._set_pbar(f'{base_episode_dir}')
        logging.warning(base_episode_dir)
        # alt_episode_dir.mkdir()

        random_numbers = get_random_numbers_of_certain_seed(episode_id_int)
        image_order = get_image_order_from_random_number(random_numbers)
        for image_name in os.listdir(base_episode_dir):
            base_image_path = base_episode_dir / image_name
            alt_image_path = alt_episode_dir / image_name
            unshuffle_image_and_save(base_image_path, alt_image_path, image_order)


if __name__ == '__main__':
    wt = LezhinComicsScraper()
    wt.download_one_webtoon('revatoon')  # unshuffled
    wt.download_one_webtoon('cartoon_hero')  # shuffled
