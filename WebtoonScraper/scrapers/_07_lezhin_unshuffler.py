"""Unshuffles Lezhin Comics Webtoon."""

from __future__ import annotations

import json
import multiprocessing
import os
import re
import shutil
from contextlib import suppress
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

from tqdm import tqdm

from ..directory_merger import (
    NORMAL_EPISODE_DIRECTORY,
    NORMAL_WEBTOON_DIRECTORY,
    _iterdir_seperating_directories_and_files,
    check_container_state,
    check_filename_state,
    webtoon_regexes,
)
from ..exceptions import DirectoryStateUnmatchedError, MissingOptionalDependencyError
from ..miscs import logger

if TYPE_CHECKING:
    from PIL import Image
else:
    Image = None


def get_image() -> ModuleType:
    global Image
    if Image:
        return Image
    with MissingOptionalDependencyError.importing("Pillow", "lezhin_comics"):
        from PIL import Image
    return Image


def unshuffle_typical_webtoon(
    source_webtoon_directory: Path,
    episode_int_ids: list[int] | None = None,
) -> Path:
    str_source_webtoon_directory = str(source_webtoon_directory)
    if str_source_webtoon_directory.endswith(", shuffled)"):
        str_target_webtoon_directory = str_source_webtoon_directory.removesuffix(", shuffled)") + ")"
    elif str_source_webtoon_directory.endswith(", shuffled, HD)"):
        str_target_webtoon_directory = str_source_webtoon_directory.removesuffix(", shuffled, HD)") + ", HD)"
    else:
        raise ValueError(f"webtoon directory {source_webtoon_directory} is not typical. Use `unshuffle`.")
    target_webtoon_directory = Path(str_target_webtoon_directory)

    unshuffle(source_webtoon_directory, target_webtoon_directory, episode_int_ids)
    return target_webtoon_directory


def unshuffle(
    source_webtoon_directory,
    target_webtoon_directory,
    episode_int_ids: list[int] | None,
    process_number: int | None = None,
    check_directory_state: bool = True,
) -> None:
    if episode_int_ids is None:
        episode_int_ids = find_episode_int_ids(source_webtoon_directory)

    target_webtoon_directory.mkdir(exist_ok=True)

    directories, files = _iterdir_seperating_directories_and_files(source_webtoon_directory)
    for file in files:
        shutil.copy(file, target_webtoon_directory / file.name)

    if check_directory_state:
        directory_state = check_container_state(source_webtoon_directory)
        if directory_state != NORMAL_WEBTOON_DIRECTORY:
            raise DirectoryStateUnmatchedError(f"Directory state is {directory_state}, which is not supported.")

    unshuffle_parameters = []
    for episode_directory_name in sorted(os.listdir(source_webtoon_directory)):
        source_episode_directory = source_webtoon_directory / episode_directory_name
        target_episode_directory = target_webtoon_directory / episode_directory_name

        processed_directory_name = webtoon_regexes[NORMAL_EPISODE_DIRECTORY].match(episode_directory_name)
        if processed_directory_name is None:
            logger.debug(f"{episode_directory_name} is passed and it assumed to be thumbnail, so just ignored.")
            continue

        episode_no = int(processed_directory_name.group("episode_no"))
        episode_id = episode_int_ids[episode_no - 1]

        unshuffle_parameters.append((source_episode_directory, target_episode_directory, episode_id))

    logger.warning(
        "Unshuffling is started. It takes a while and it's very CPU-intensive task. "
        "So keep patient and wait until the process end."
    )
    with multiprocessing.Pool(process_number) as p:
        unshuffled_episode_ids = p.imap_unordered(unshuffle_episode_packed, unshuffle_parameters)
        progress_bar = tqdm(unshuffled_episode_ids, total=len(unshuffle_parameters))
        for episode_name in progress_bar:
            progress_bar.set_description(f"Episode {episode_name} unshuffle ended")

    logger.info("Unshuffling ended successfully.")


def find_episode_int_ids(source_webtoon_directory: Path) -> list[int]:
    # sourcery skip: extract-method
    information_file = source_webtoon_directory / "information.json"
    if information_file.exists():
        with suppress(json.JSONDecodeError):
            information = json.loads(information_file.read_text("utf-8"))
        with suppress(KeyError):
            return information["episode_int_ids"]

    raise ValueError(
        "There's no information.json(or lack of information about episode_id_ints on it) "
        "and episode_id_ints is not provided."
    )


def unshuffle_episode_packed(args) -> str | None:
    """
    Equevalent to `lambda x: unshuffle_episode(*x)`,
    but it doesn't work well with multiprocessing.Pool,
    so this is defined separately.
    """
    return unshuffle_episode(*args)


def unshuffle_episode(
    source_episode_directory: Path,
    target_episode_directory: Path,
    episode_id_int: int,
) -> str | None:
    shutil.rmtree(target_episode_directory, ignore_errors=True)
    target_episode_directory.mkdir()

    random_numbers = calculate_random_numbers(episode_id_int)
    image_order = calculate_image_order(random_numbers)
    for image_name in os.listdir(source_episode_directory):
        source_image_path = source_episode_directory / image_name
        target_image_path = target_episode_directory / image_name
        unshuffle_image_and_save(source_image_path, target_image_path, image_order)

    return source_episode_directory.name


def calculate_random_numbers(seed: int) -> list[int]:
    """Mutating Lezhin's random number generator. `random_numbers` are always same if given seed is same."""
    results: list[int] = []
    state = seed
    for _ in range(25):
        state ^= state >> 12
        state ^= (state << 25) & 0xFFFFFFFFFFFFFFFF
        state ^= state >> 27
        result = (state >> 32) % 25
        results.append(result)
    return results


def calculate_image_order(random_numbers: list[int]) -> list[int]:
    image_order = list(range(25))
    for i in range(25):
        shuffle_index = random_numbers[i]
        image_order[i], image_order[shuffle_index] = (
            image_order[shuffle_index],
            image_order[i],
        )
    return image_order


def unshuffle_image_and_save(base_image_path: Path, alt_image_path: Path, image_order: list[int]) -> None:
    get_image()
    with Image.open(base_image_path) as image:
        image_x, image_y = image.size
        margin = image_y % 5
        image_y -= margin
        cropped_images: list[Image.Image] = [None] * 25  # type: ignore # 이 None은 후에 image로 덮어씌워진다.
        for index_x, left, right in ((i, i * image_x // 5, (i + 1) * image_x // 5) for i in range(5)):
            for index_y, upper, lower in ((i, i * image_y // 5, (i + 1) * image_y // 5) for i in range(5)):
                cropped_image: Image.Image = image.crop((left, upper, right, lower))
                image_index = index_x + index_y * 5
                cropped_images[image_order.index(image_index)] = cropped_image

        assambled_image = image
        for image_index, cropped_image in enumerate(cropped_images):
            index_y, index_x = divmod(image_index, 5)
            assambled_image.paste(cropped_image, (index_x * image_x // 5, index_y * image_y // 5))
        assambled_image.save(alt_image_path)
