"""Work in Progress"""

from __future__ import annotations
import logging
from pathlib import Path
import os
import re
import shutil
import multiprocessing

from PIL import Image


class LezhinUnshuffler:
    @staticmethod
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

    async def unshuffle_webtoon(self, titleid, base_webtoon_dir, alt_webtoon_dir, force_unshuffle: bool = False, process_number: int = 8):
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
        episode_id_ints = (await self.get_webtoon_data(titleid))['episode_id_ints']

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
            p.starmap(self.unshuffle_episode, unshuffle_parameters)

        logging.info('Unshuffling ended.')

    @staticmethod
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

    @staticmethod
    def get_image_order_from_random_number(random_numbers):
        image_order = list(range(25))
        for i in range(25):
            shuffle_index = random_numbers[i]
            image_order[i], image_order[shuffle_index] = image_order[shuffle_index], image_order[i]
        return image_order

    def unshuffle_image_and_save(self, base_image_path, alt_image_path, image_order, margin: int | None = None):
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
                index_y, index_x = divmod(image_index, 5)
                image_x, image_y = im.size
                image_y -= MARGIN
                return index_x * image_x, index_y * image_y

            assambled_image = Image.new("RGB", (image_x, image_y), (256, 0, 0))
            for i, cropped_image in enumerate(cropped_images):
                assambled_image.paste(cropped_image, tuple(
                    j // 5 for j in position_in_assambled_image(i)))
            assambled_image.save(alt_image_path)

    def unshuffle_episode(self, base_episode_dir: Path, alt_episode_dir: Path, episode_id_int: int):
        # print(f'{base_episode_dir = }, {alt_episode_dir = }, {episode_id_int = }')
        # return

        # self._set_pbar(f'{base_episode_dir}')
        logging.warning(base_episode_dir)
        # alt_episode_dir.mkdir()

        random_numbers = self.get_random_numbers_of_certain_seed(episode_id_int)
        image_order = self.get_image_order_from_random_number(random_numbers)
        for image_name in os.listdir(base_episode_dir):
            base_image_path = base_episode_dir / image_name
            alt_image_path = alt_episode_dir / image_name
            self.unshuffle_image_and_save(base_image_path, alt_image_path, image_order)
