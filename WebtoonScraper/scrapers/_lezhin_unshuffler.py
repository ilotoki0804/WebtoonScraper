from __future__ import annotations

import json
import os
import shutil
from contextlib import suppress
from multiprocessing.pool import ThreadPool
from pathlib import Path

from PIL import Image
from rich import progress

from ..base import get_default_thread_number, logger
from ..directory_state import (
    DirectoryState,
    _directories_and_files_of,
    check_container_state,
)
from ..exceptions import DirectoryStateError


def unshuffle_typical_webtoon(
    source_webtoon_directory: Path,
    episode_int_ids: list[int] | None = None,
    progress: progress.Progress | None = None,
    thread_number: int | None = None,
) -> Path:
    str_source_webtoon_directory = str(source_webtoon_directory)
    if str_source_webtoon_directory.endswith(", shuffled)"):
        str_target_webtoon_directory = str_source_webtoon_directory.removesuffix(", shuffled)") + ")"
    elif str_source_webtoon_directory.endswith(", shuffled, HD)"):
        str_target_webtoon_directory = str_source_webtoon_directory.removesuffix(", shuffled, HD)") + ", HD)"
    else:
        raise ValueError(f"webtoon directory {source_webtoon_directory} is not typical. Use `unshuffle` instead.")
    target_webtoon_directory = Path(str_target_webtoon_directory)

    unshuffle(
        source_webtoon_directory,
        target_webtoon_directory,
        episode_int_ids,
        progress=progress,
        thread_number=thread_number,
    )
    return target_webtoon_directory


def unshuffle(
    source_webtoon_directory: Path,
    target_webtoon_directory: Path,
    episode_int_ids: list[int] | None,
    thread_number: int | None = None,
    check_directory_state: bool = True,
    progress: progress.Progress | None = None,
) -> None:
    if episode_int_ids is None:
        episode_int_ids = _search_episode_int_ids(source_webtoon_directory)

    target_webtoon_directory.mkdir(exist_ok=True)

    _, files = _directories_and_files_of(source_webtoon_directory)
    for file in files:
        shutil.copy(file, target_webtoon_directory / file.name)

    if check_directory_state:
        directory_state = check_container_state(source_webtoon_directory)
        if directory_state != DirectoryState.WebtoonDirectory(is_merged=False):
            raise DirectoryStateError.from_state(directory_state, source_webtoon_directory)

    unshuffle_parameters = []
    for episode_directory_name in sorted(os.listdir(source_webtoon_directory)):
        source_episode_directory = source_webtoon_directory / episode_directory_name
        target_episode_directory = target_webtoon_directory / episode_directory_name

        processed_directory_name = DirectoryState.EpisodeDirectory(is_merged=False).pattern().match(episode_directory_name)
        if processed_directory_name is None:
            logger.debug(f"{episode_directory_name} is passed and it assumed to be thumbnail, so just ignored.")
            continue

        episode_no = int(processed_directory_name.group("episode_no"))
        episode_id = episode_int_ids[episode_no - 1]

        unshuffle_parameters.append((source_episode_directory, target_episode_directory, episode_id))

    logger.info(
        "The webtoon is being unshuffled. It takes a while and it's very CPU-intensive task. "
        "So keep patient and wait until the process end."
    )
    with ThreadPool(thread_number or get_default_thread_number()) as p:
        unshuffled_episode_ids = p.imap_unordered(lambda args: unshuffle_episode(*args), unshuffle_parameters)
        if progress is None:
            for i, episode_name in enumerate(unshuffled_episode_ids, 1):
                logger.info(f"[{i:02d}/{len(unshuffle_parameters):02d}] Episode {episode_name} unshuffle ended")
        else:
            task = progress.add_task("Unshuffle webtoon...", total=len(unshuffle_parameters))
            for episode_name in unshuffled_episode_ids:
                progress.update(task, description=f"Episode {episode_name} unshuffle ended")

    logger.info("The webtoon unshuffled successfully.")


def _search_episode_int_ids(source_webtoon_directory: Path) -> list[int]:
    information_file = source_webtoon_directory / "information.json"
    if information_file.exists():
        with suppress(json.JSONDecodeError):
            information = json.loads(information_file.read_text("utf-8"))
            with suppress(KeyError):
                return information["episode_int_ids"]

    raise ValueError("No information.json, or no information about episode_int_ids.")


def unshuffle_episode(
    source_episode_directory: Path,
    target_episode_directory: Path,
    episode_id_int: int,
) -> str | None:
    shutil.rmtree(target_episode_directory, ignore_errors=True)
    target_episode_directory.mkdir()

    random_numbers = generate_random(episode_id_int)
    image_order = calculate_image_order(random_numbers)
    for image_name in os.listdir(source_episode_directory):
        source_image_path = source_episode_directory / image_name
        target_image_path = target_episode_directory / image_name
        unshuffle_image_and_save(source_image_path, target_image_path, image_order)

    return source_episode_directory.name


def generate_random(seed: int) -> list[int]:
    """Imitate Lezhin's pseudorandom generator. The result is always same if given seed is same."""
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
    # gif일 경우 unshuffle이 일어나지 않음.
    if base_image_path.suffix == ".gif":
        shutil.copy(base_image_path, alt_image_path)
        return

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

        assembled_image = image
        for image_index, cropped_image in enumerate(cropped_images):
            index_y, index_x = divmod(image_index, 5)
            assembled_image.paste(cropped_image, (index_x * image_x // 5, index_y * image_y // 5))
        if base_image_path.suffix in (".jpg", ".jpeg"):
            assembled_image.save(alt_image_path, optimize=True, quality=95)
        else:
            assembled_image.save(alt_image_path)
