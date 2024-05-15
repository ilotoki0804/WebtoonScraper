import logging
import multiprocessing
import os
import shutil
from itertools import count
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, UnidentifiedImageError
from tqdm import tqdm

from . import directory_merger, webtoon_viewer
from .miscs import logger


def concat_webtoon(
    source_webtoon_directory: Path,
    target_webtoon_directory: Path,
    batch_count: int,
    rebuild_webtoon_viewer: bool = True,
    process_number: int | None = None,
    use_tqdm: bool = True,
):
    """batch_count가 0이면 전체를 묶습니다. process_number가 1이라면 멀티프로세싱을 활용하지 않습니다."""
    directories, files = directory_merger._directories_and_files_of(source_webtoon_directory)

    target_webtoon_directory.mkdir(parents=True, exist_ok=True)

    # careless한 사용자들을 위한 편의 기능.
    # 한 웹툰 디렉토리는 한 함수만 접근 가능하게 만듦.
    # multiprocessing 사용 시 나오는 일부 오류를 해결함.
    working_indicator = target_webtoon_directory / "WORKING"
    if working_indicator.exists():
        logging.error(f"Concatenating canceled since working indicator(`{working_indicator.absolute()}`) exists.")
        return

    try:
        working_indicator.write_bytes(b"")
        logger.warning(
            "Unshuffling is started. It takes a while and it's very CPU-intensive task. "
            "So keep patient and wait until the process end."
        )

        if process_number == 1:
            if use_tqdm:
                directories = tqdm(directories, total=len(directories))

            for i, episode_directory in enumerate(directories, 1):
                episode_name = episode_directory.name
                target_directory = target_webtoon_directory / episode_name
                _concat_episode(episode_directory, target_directory, batch_count)

                if use_tqdm:
                    if TYPE_CHECKING:
                        assert isinstance(directories, tqdm)
                    directories.set_description(f"Episode {episode_name} concatenation ended")
                else:
                    logger.info(f"Episode {episode_name} concatenation ended ({i:02d}/{len(directories):02d})")

        else:
            parameters = [
                (episode_directory, target_webtoon_directory / episode_directory.name, batch_count)
                for episode_directory in directories
            ]

            with multiprocessing.Pool(process_number) as p:
                directory_names = p.imap_unordered(_concat_episode_packed, parameters)

                if use_tqdm:
                    progress_bar = tqdm(directory_names, total=len(parameters))
                    for episode_name in progress_bar:
                        progress_bar.set_description(f"Episode {episode_name} concatenation ended")
                else:
                    for i, episode_name in enumerate(directory_names, 1):
                        logger.info(f"Episode {episode_name} concatenation ended ({i:02d}/{len(parameters):02d})")

    finally:
        working_indicator.unlink(True)

    for file in files:
        shutil.copy(file, target_webtoon_directory / file.name)

    if rebuild_webtoon_viewer:
        webtoon_viewer.add_html_webtoon_viewer(target_webtoon_directory)


def _concat_episode_packed(args: tuple[Path, Path, int]):
    _concat_episode(*args)
    return args[1].name  # Directory name


def _concat_episode(
    source_episode_directory: Path,
    target_episode_directory: Path,
    batch_count: int,
):
    target_episode_directory.mkdir(exist_ok=True)

    image_names = sorted(os.listdir(source_episode_directory))
    images = _get_images(source_episode_directory, image_names)
    # next(images)
    images.send(None)

    for i in count(0):
        try:
            batched_images = images.send(batch_count)
        except StopIteration:
            break

        width = max(image.width for image in batched_images)
        height = sum(image.height for image in batched_images)

        y = 0
        composite = Image.new("RGB", (width, height))
        for image in batched_images:
            composite.paste(image, (0, y))
            y += image.height

        composite.save(target_episode_directory / f"{i:03d}.png")

        for image in batched_images:
            image.close()

def _get_images(directory: Path, image_names: list[str]):
    result: list[Image.Image] = []
    pointer = 0
    goal = 0
    while pointer < len(image_names):
        while goal and pointer < len(image_names) and pointer < goal:
            image_dir = directory / image_names[pointer]

            try:
                result.append(Image.open(image_dir))
            except UnidentifiedImageError:
                # 이미지가 아니어서 실패할 경우 오류를 내는 것이 아닌 해당 이미지를 무시하고
                # 다음 이미지를 불러오는 것을 시도함.
                continue

            pointer += 1

        batch_count = yield result
        batch_count = batch_count or len(image_names)
        goal = pointer + batch_count
        result.clear()
