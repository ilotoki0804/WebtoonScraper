"""Work in Progress"""
# folder 용어 제거
from __future__ import annotations
import logging
from pathlib import Path
import os
import re
import shutil
import multiprocessing

from PIL import Image

if __name__ in {"__main__", "J_lezhin_unshuffler"}:
    logging.warning(f'파일이 아닌 WebtoonScraper 모듈에서 실행되고 있습니다. {__name__ = }')
    from WebtoonScraper.directory_merger import fast_check_directory_state, check_filename_state, DEFAULT_STATE, webtoon_regexes, move_thumbnail_only
    from WebtoonScraper.exceptions import DirectoryStateUnmatched
else:
    from ..directory_merger import fast_check_directory_state, check_filename_state, DEFAULT_STATE, webtoon_regexes, move_thumbnail_only
    from ..exceptions import DirectoryStateUnmatched


def unshuffle_typical_webtoon_directory(source_webtoon_directory: Path, episode_id_ints: list[int]):
    target_webtoon_directory = Path(str(source_webtoon_directory).removesuffix(', shuffled)') + ')')
    unshuffle_webtoon_directory_to_directory(source_webtoon_directory, target_webtoon_directory, episode_id_ints)
    return target_webtoon_directory


def unshuffle_webtoon_directory_to_directory(
    source_webtoon_directory,
    target_webtoon_directory,
    episode_id_ints: list[int],
    process_number: int = 8,
    proceed_without_checking_directory_state: bool = False,
):
    # 웹툰을 다운로드 받을 때 유료 웹툰이거나 하는 이유로 일부 에피소드는 다운로드되지 않을 수 있음
    # 하지만 episode_id는 0부터 쭉 존재함.
    # 따라서 다운로드되지 않은 웹툰을 걸러 작업을 하지 않도록 거르는 작업이 필요함.
    # `unshuffle_episode`에서 직접 episode_id를 고르면 복잡한 로직이 필요없지만 그때마다 get_webtoon_data를 불러야 하기에
    # 성능 하락의 우려가 아주 살짝 있음. 하지만 크진 않기에 unshuffle_episode에서 직접 episode_id를 가지는 것도 고려해볼만 함.

    target_webtoon_directory.mkdir(exist_ok=True)
    move_thumbnail_only(source_webtoon_directory, target_webtoon_directory, copy=True)

    if not proceed_without_checking_directory_state:
        directory_state = fast_check_directory_state(source_webtoon_directory)
        if directory_state != DEFAULT_STATE:
            raise DirectoryStateUnmatched(f'Directory state is {directory_state}, which is not supported.')

    unshuffle_parameters = []
    for episode_directory_name in sorted(os.listdir(source_webtoon_directory)):
        source_episode_directory = source_webtoon_directory / episode_directory_name
        target_episode_directory = target_webtoon_directory / episode_directory_name

        processed_directory_name = webtoon_regexes.default_episode_name_directory.match(episode_directory_name)
        if processed_directory_name is None:
            logging.debug(f"{episode_directory_name} is passed and it assumed to be thumbnail, so just ignored.")
            continue

        episode_no = int(processed_directory_name.group('no'))
        episode_id = episode_id_ints[episode_no - 1]

        unshuffle_parameters.append((source_episode_directory, target_episode_directory, episode_id))

    print("Unshuffling is started. It takes a while and it's very CPU-intensive task. "
          'So keep patient and wait until the process end.')
    with multiprocessing.Pool(process_number) as p:
        p.starmap(unshuffle_episode, unshuffle_parameters)

    logging.info('Unshuffling ended.')


def unshuffle_episode(source_episode_directory: Path, target_episode_directory: Path, episode_id_int: int):
    try:
        target_episode_directory.mkdir()
    except FileExistsError:
        if check_filename_state(target_episode_directory.name) != DEFAULT_STATE:
            logging.warning(f'Damaged file or directory detected. Skip and continue. Name: {target_episode_directory.name}')
            return
        if len(os.listdir(target_episode_directory)) == len(os.listdir(source_episode_directory)):
            logging.warning(f"Skipping {target_episode_directory.name}, because there are items in the directory and the number of contents in each directory is the same.")
            return
        if len(os.listdir(target_episode_directory)) != 0:
            logging.warning(f'{target_episode_directory.name} is not valid. Delete items and continue.')
            shutil.rmtree(target_episode_directory)
            target_episode_directory.mkdir()

    random_numbers = get_random_numbers_of_certain_seed(episode_id_int)
    image_order = get_image_order_from_random_number(random_numbers)
    for image_name in os.listdir(source_episode_directory):
        source_image_path = source_episode_directory / image_name
        target_image_path = target_episode_directory / image_name
        unshuffle_image_and_save(source_image_path, target_image_path, image_order)


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


def get_episode_dir_no(episode_directory_name: str):
    try:
        return int(episode_directory_name.split('.')[0])
    except ValueError as e:
        if episode_directory_name.endswith(('jpg', 'png', 'webp', 'gif', 'bmp')):
            return None
        if re.search(r'^(\d+)~(\d+)', episode_directory_name):
            raise ValueError(
                'Episode name is not valid. It\'s because you tried merging already merged webtoon folder. '
                '`unshuffle_webtoon` does not support merged webtoon.'
            )
        raise ValueError('`episode_dir_name` is invalid. Maybe you tried to unshuffle merged webtoon directory. '
                         '`unshuffle_webtoon` does not support merged webtoon.') from e


def unshuffle_image_and_save(base_image_path, alt_image_path, image_order):
    with Image.open(base_image_path) as im:
        image_x, image_y = im.size
        margin = image_y % 5
        image_y -= margin
        cropped_images: list[Image.Image] = [None] * 25
        for index_x, left, right in ((i, i * image_x // 5, (i + 1) * image_x // 5) for i in range(5)):
            for index_y, upper, lower in ((i, i * image_y // 5, (i + 1) * image_y // 5) for i in range(5)):
                cropped_image: Image.Image = im.crop((left, upper, right, lower))
                image_index = index_x + index_y * 5
                cropped_images[image_order.index(image_index)] = cropped_image

        def position_in_assambled_image(image_index) -> tuple[int, int]:
            index_y, index_x = divmod(image_index, 5)
            image_x, image_y = im.size
            image_y -= margin
            return index_x * image_x, index_y * image_y

        assambled_image = Image.new("RGB", im.size, (256, 0, 0))
        for i, cropped_image in enumerate(cropped_images):
            assambled_image.paste(cropped_image, tuple(
                j // 5 for j in position_in_assambled_image(i)))
        assambled_image.paste(im.crop((0, image_y, *im.size)), (0, image_y))
        assambled_image.save(alt_image_path)
