"""Unshuffles Lezhin Comics Webtoon."""
from __future__ import annotations
import logging
from pathlib import Path
import os
import re
import shutil
import multiprocessing

from tqdm import tqdm
from PIL import Image

if __name__ in {"__main__", "J_lezhin_unshuffler"}:
    logging.warning(f'파일이 아닌 WebtoonScraper 모듈에서 실행되고 있습니다. {__name__ = }')
    from WebtoonScraper.directory_merger import fast_check_container_state, check_filename_state, NORMAL_WEBTOON_DIRECTORY, webtoon_regexes, move_thumbnail_only, NORMAL_EPISODE_DIRECTORY
    from WebtoonScraper.exceptions import DirectoryStateUnmatched
else:
    from ..directory_merger import fast_check_container_state, check_filename_state, NORMAL_WEBTOON_DIRECTORY, webtoon_regexes, move_thumbnail_only, NORMAL_EPISODE_DIRECTORY
    from ..exceptions import DirectoryStateUnmatched


def unshuffle_typical_webtoon_directory_and_return_target_directory(source_webtoon_directory: Path, episode_int_ids: list[int] | None = None) -> Path:
    target_webtoon_directory = Path(str(source_webtoon_directory).removesuffix(', shuffled)') + ')')
    unshuffle_webtoon_directory_to_directory(source_webtoon_directory, target_webtoon_directory, episode_int_ids)
    return target_webtoon_directory


def unshuffle_webtoon_directory_to_directory(
    source_webtoon_directory,
    target_webtoon_directory,
    episode_int_ids: list[int] | None,
    process_number: int | None = None,
    proceed_without_checking_directory_state: bool = False,
) -> None:
    ids_file_search_result = search_episode_int_ids_exclude_if_from_directory(source_webtoon_directory)
    if episode_int_ids is None:
        if not ids_file_search_result:
            raise ValueError('episode_id_ints is not provided. Provide it or download episode_id_ints.')

        episode_int_ids, _, _ = ids_file_search_result

    try:
        target_webtoon_directory.mkdir(exist_ok=True)
        move_thumbnail_only(source_webtoon_directory, target_webtoon_directory, copy=True)

        if not proceed_without_checking_directory_state:
            directory_state = fast_check_container_state(source_webtoon_directory)
            if directory_state != NORMAL_WEBTOON_DIRECTORY:
                raise DirectoryStateUnmatched(f'Directory state is {directory_state}, which is not supported.')

        unshuffle_parameters = []
        for episode_directory_name in sorted(os.listdir(source_webtoon_directory)):
            source_episode_directory = source_webtoon_directory / episode_directory_name
            target_episode_directory = target_webtoon_directory / episode_directory_name

            processed_directory_name = webtoon_regexes[NORMAL_EPISODE_DIRECTORY].match(episode_directory_name)
            if processed_directory_name is None:
                logging.debug(f"{episode_directory_name} is passed and it assumed to be thumbnail, so just ignored.")
                continue

            episode_no = int(processed_directory_name.group('episode_no'))
            episode_id = episode_int_ids[episode_no - 1]

            unshuffle_parameters.append((source_episode_directory, target_episode_directory, episode_id))

        print("Unshuffling is started. It takes a while and it's very CPU-intensive task. "
              'So keep patient and wait until the process end.')
        with multiprocessing.Pool(process_number) as p:
            unshuffled_episode_ids = p.imap(unshuffle_episode_unpacking, unshuffle_parameters)
            progress_bar = tqdm(unshuffled_episode_ids, total=len(unshuffle_parameters))
            for episode_name in progress_bar:
                progress_bar.set_description(f'Episode {episode_name} unshuffle ended')
    finally:
        if ids_file_search_result is not None:
            _, id_text_file_target_path, id_text_file_source_path = ids_file_search_result
            os.rename(id_text_file_target_path, id_text_file_source_path)

    logging.info('Unshuffling ended successfully.')


def search_episode_int_ids_exclude_if_from_directory(source_webtoon_directory: Path) -> tuple[list[int], Path, Path] | None:
    for episode_int_ids_or_not in os.listdir(source_webtoon_directory):
        if episode_int_ids_or_not.endswith('_ids.txt'):  # f'{webtoon_id}_ids.txt'도 고려할 만 함.
            text_file_name = episode_int_ids_or_not
            id_text_file_source_path = source_webtoon_directory / text_file_name
            id_text_file_target_path = source_webtoon_directory.parent / text_file_name

            episode_int_ids_raw = id_text_file_source_path.read_text(encoding='utf-8')
            episode_int_ids = [int(line) for line in episode_int_ids_raw.splitlines()]

            os.rename(id_text_file_source_path, id_text_file_target_path)

            return episode_int_ids, id_text_file_target_path, id_text_file_source_path

    return None


def unshuffle_episode_unpacking(args) -> str | None:
    """
    Equevalent to `lambda x: unshuffle_episode(*x)`,
    but it doesn't work well with multiprocessing.Pool,
    so this is defined separately.
    """
    return unshuffle_episode(*args)


def unshuffle_episode(source_episode_directory: Path, target_episode_directory: Path, episode_id_int: int) -> str | None:
    try:
        target_episode_directory.mkdir()
    except FileExistsError:
        # stdout이 원본 interpreter와는 다른지 logging이 출력되지는 않음. logging이 출력되게 하거나 제거할 것.

        if check_filename_state(target_episode_directory.name) != NORMAL_WEBTOON_DIRECTORY:
            logging.warning(f'{target_episode_directory.name} is not valid container state. Delete items and continue.')
        elif len(os.listdir(target_episode_directory)) == len(os.listdir(source_episode_directory)):
            logging.warning(f"Skipping {target_episode_directory.name}, because there are items in the directory and the number of contents in each directory is the same.")
            return None
        elif len(os.listdir(target_episode_directory)) != 0:
            logging.warning(f'{target_episode_directory.name} has the invalid number of images. Delete items and continue.')

        shutil.rmtree(target_episode_directory)
        target_episode_directory.mkdir()

    random_numbers = get_random_numbers_of_certain_seed(episode_id_int)
    image_order = get_image_order_from_random_numbers(random_numbers)
    for image_name in os.listdir(source_episode_directory):
        source_image_path = source_episode_directory / image_name
        target_image_path = target_episode_directory / image_name
        unshuffle_image_and_save(source_image_path, target_image_path, image_order)

    return source_episode_directory.name


def get_random_numbers_of_certain_seed(seed: int) -> list[int]:
    """Mutating Lezhin's random number generator. `random_numbers` are always same if given seed is same."""
    results: list[int] = []
    state = seed
    for _ in range(25):
        state ^= state >> 12
        state ^= (state << 25) & 18446744073709551615
        state ^= state >> 27
        result = (state >> 32) % 25
        results.append(result)
    return results


def get_image_order_from_random_numbers(random_numbers) -> list[int]:
    image_order = list(range(25))
    for i in range(25):
        shuffle_index = random_numbers[i]
        image_order[i], image_order[shuffle_index] = image_order[shuffle_index], image_order[i]
    return image_order


def get_episode_directory_no(episode_directory_name: str) -> int | None:
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
        raise ValueError('`episode_directory_name` is invalid. Maybe you tried to unshuffle merged webtoon directory. '
                         '`unshuffle_webtoon` does not support merged webtoon.') from e


def unshuffle_image_and_save(base_image_path, alt_image_path, image_order) -> None:
    with Image.open(base_image_path) as im:
        image_x, image_y = im.size
        margin = image_y % 5
        image_y -= margin
        cropped_images: list[Image.Image] = [None] * 25  # type: ignore 이 None은 후에 image로 덮어씌워진다.
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

        # assambled_image = im  # 덮어씌우든 새로 만들든 속도차는 크게 없다 (26.71(새로 만듦) > 26.54(덮어씀), 오차 있음.)
        assambled_image = Image.new("RGB", im.size, (256, 0, 0))
        for i, cropped_image in enumerate(cropped_images):
            assambled_image.paste(
                cropped_image,
                tuple(j // 5 for j in position_in_assambled_image(i))  # type: ignore
            )
        assambled_image.paste(im.crop((0, image_y, *im.size)), (0, image_y))
        assambled_image.save(alt_image_path)
