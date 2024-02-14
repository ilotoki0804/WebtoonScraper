import json
import os
import re
from contextlib import suppress
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Sequence, TypeVar

from .directory_merger import _iterdir_seperating_directories_and_files
from .miscs import __version__ as version

HTML_TEMPLATE = """\
<!-- With WebtoonScraper {version} at {created_time} -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{webtoon_title}</title>
    <link rel="icon" href={webtoon_thumbnail_name_repr} type="image/x-icon">
    <style>
        div.episode-selector {
            text-align: center;
            padding-bottom: 1em;
        }
        div#image-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            width: 100%;
        }
        @media (orientation: portrait) {
            div#image-container img {
                width: 100%;
            }
        }
        @media (orientation: landscape) {
            div#image-container img {
                width: 70%;
            }
        }
    </style>
</head>
<body>
    <div class="episode-selector">
        <span class="title-bar"></span>
        <br>
        <button class="prev-episode">이전 에피소드</button>
        <select class="episode-selector-dropdown"></select>
        <button id="delete-history">조회 기록 지우기</button>
        <button class="next-episode">다음 에피소드</button>
    </div>
    <div id="image-container"></div>
    <div class="episode-selector">
        <button class="next-episode" style="width: 70%; height: 200px; font-size: 3em; background-color: aliceblue;" type="button">다음 에피소드</button>
        <br>
        <button class="prev-episode">이전 에피소드</button>
        <select class="episode-selector-dropdown"></select>
        <br>
        <span class="title-bar"></span>
    </div>
    <script>
        const webtoonTitle = {webtoon_title_repr};
        const episodeDirectories = {episode_directories};
        const webtoonImagesOfDirectories = {images_of_episode_directories};
        const createdTime = {created_time};
        const localStorageName = `viewedEpisode(${webtoonTitle})`;
        const prevEpisodeButtons = Array.from(document.getElementsByClassName("prev-episode"));
        const nextEpisodeButtons = Array.from(document.getElementsByClassName("next-episode"));
        const titleBars = Array.from(document.getElementsByClassName("title-bar"));
        const episodeSelectors = Array.from(document.getElementsByClassName("episode-selector-dropdown"));
        const viewedEpisodesLocalStorageName = `viewedEpisodes@${webtoonTitle}(${createdTime})`;
        const lastViewedEpisodeLocalStorageName = `lastViewedEpisode@${webtoonTitle}(${createdTime})`;
        const episodeNoRaw = window.localStorage.getItem(lastViewedEpisodeLocalStorageName);
        const resetButton = document.getElementById("delete-history");
        let episodeNo = 0;
        if (episodeNoRaw !== null) {
            episodeNo = parseInt(episodeNoRaw);
        }
        let viewedEpisodes = [];

        loadViewedEpisodes();
        function loadViewedEpisodes() {
            let viewedEpisodesRaw = window.localStorage.getItem(viewedEpisodesLocalStorageName);
            if (viewedEpisodesRaw == null) {
                viewedEpisodes = [];
                episodeDirectories.forEach(() => viewedEpisodes.push(false));
                window.localStorage.setItem(viewedEpisodesLocalStorageName, JSON.stringify(viewedEpisodes));
            } else {
                viewedEpisodes = Array.from(JSON.parse(viewedEpisodesRaw));
            }
        }

        (function renderDropdown() {
            episodeSelectors.forEach((selector) => {
                episodeDirectories.forEach((episodeDirectory, index) => {
                    const option = document.createElement("option");
                    option.value = index;
                    option.innerHTML = episodeDirectory;
                    option.selected = index == episodeNo;
                    selector.appendChild(option);
                });
                selector.addEventListener("input", function(event) {
                    selector.childNodes.forEach((options, index) => {
                        if (options.selected) {
                            drawImage(index);
                        }
                    })
                });
            });
        })();

        drawImage(episodeNo);
        function drawImage(index) {
            episodeNo = index;
            window.localStorage.setItem(lastViewedEpisodeLocalStorageName, episodeNo);
            const imageContainer = document.getElementById('image-container');

            const directoryName = episodeDirectories[index];
            const imagesName = webtoonImagesOfDirectories[index];
            const webtoonImages = imagesName.map((imageName, index) => {
                return directoryName + "/" + imageName;
            });

            titleBars.forEach((titleBar) => {
                titleBar.innerHTML = `${webtoonTitle} | ${directoryName} | downloaded by WebtoonScraper`
            });

            while (imageContainer.firstChild) {
                imageContainer.removeChild(imageContainer.firstChild);
            }

            webtoonImages.forEach((webtoonImageSrc, index) => {
                const image = document.createElement("img");
                image.src = webtoonImageSrc;
                image.alt = imagesName[index];
                imageContainer.appendChild(image);
            });

            viewedEpisodes[index] = true;
            window.localStorage.setItem(viewedEpisodesLocalStorageName, JSON.stringify(viewedEpisodes));

            episodeSelectors.forEach((selector) => {
                selector.childNodes.forEach((option, optionIndex) => {
                    if (viewedEpisodes[optionIndex]) {
                        option.innerHTML = "☑ " + episodeDirectories[optionIndex];
                    } else {
                        option.innerHTML = "☐ " + episodeDirectories[optionIndex];
                    }
                    option.selected = optionIndex == episodeNo;
                })
            });

            window.scrollTo(0, 0);
            updateButton();
        }


        function updateButton() {
            if (episodeNo == 0) {
                prevEpisodeButtons.forEach((button) => {
                    button.innerHTML = "이전 회차가 없습니다.";
                    button.disabled = true;
                });
            } else {
                prevEpisodeButtons.forEach((button) => {
                    button.innerHTML = "이전 회차";
                    button.disabled = false;
                });
            }
            if (episodeDirectories.length - 1 <= episodeNo) {
                nextEpisodeButtons.forEach((button) => {
                    button.innerHTML = "다음 회차가 없습니다.";
                    button.disabled = true;
                });
            } else {
                nextEpisodeButtons.forEach((button) => {
                    button.innerHTML = "다음 회차";
                    button.disabled = false;
                });
            }
        }

        prevEpisodeButtons.forEach((button) => {
            button.addEventListener("click", function() {
                if (episodeNo > 0) {
                    drawImage(episodeNo - 1);
                }
            });
        });

        nextEpisodeButtons.forEach((button) => {
            button.addEventListener("click", function() {
                const originalepisodeNo = episodeNo
                try {
                    drawImage(episodeNo + 1);
                } catch {
                    episodeNo = originalepisodeNo;
                }
            });
        });

        resetButton.addEventListener("click", function() {
            console.log("reset");
            window.localStorage.removeItem(viewedEpisodesLocalStorageName);
            loadViewedEpisodes();
            drawImage(episodeNo);
        })
    </script>
</body>
</html>\
"""

T = TypeVar("T")


def _select_from_sequence(sequence_to_select: Sequence[T], message: str | None) -> T:
    if message is not None:
        print(message)
    if len(sequence_to_select) < 10:
        for i, item in enumerate(sequence_to_select, 1):
            print(f"{i}. {item}")
    else:
        for i, item in enumerate(sequence_to_select, 1):
            print(f"{i:02d}. {item}")

    user_answer = int(input("Enter number: "))
    return sequence_to_select[user_answer - 1]


def add_html_webtoon_viewer(
    webtoon_directory: Path,
    webtoon_title: str | None = None,
    thumbnail_name: str | None = None,
) -> None:
    """information.json의 데이터보다 인자로 주어진 데이터를 더 우선 순위로 잡습니다."""
    directories, files = _iterdir_seperating_directories_and_files(webtoon_directory)
    if webtoon_title is None or thumbnail_name is None:
        for file in files:
            if file.name == "information.json":
                with file.open("r", encoding="utf-8") as f:
                    information = json.load(f)
                if webtoon_title is None:
                    webtoon_title = information["title"]
                    assert isinstance(webtoon_title, str)
                if thumbnail_name is None:
                    thumbnail_name = information["thumbnail_name"]
                    assert isinstance(thumbnail_name, str)
                break
        else:
            webtoon_title, thumbnail_name = infer_webtoon_infomations(webtoon_directory, webtoon_title, thumbnail_name)

    episode_directories = json.dumps([directory.name for directory in directories], ensure_ascii=False)
    images_of_episode_directories = json.dumps(
        [os.listdir(episode_directory_name) for episode_directory_name in directories],
        ensure_ascii=False,
    )

    html = (
        HTML_TEMPLATE.replace(
            r"{webtoon_thumbnail_name_repr}",
            json.dumps(thumbnail_name, ensure_ascii=False),
        )
        .replace(r"{webtoon_title}", escape(webtoon_title))
        .replace(r"{webtoon_title_repr}", json.dumps(webtoon_title, ensure_ascii=False))
        .replace(r"{episode_directories}", episode_directories)
        .replace(r"{images_of_episode_directories}", images_of_episode_directories)
        .replace(r"{version}", version)
        .replace(r"{created_time}", json.dumps(datetime.now().isoformat()))
    )
    (webtoon_directory / "webtoon.html").write_text(html, encoding="utf-8")


def infer_webtoon_infomations(
    webtoon_directory: Path,
    webtoon_title: str | None = None,
    thumbnail_name: str | None = None,
) -> tuple[str, str]:
    """webtoon_title이나 thumbnail_name에 None이 아닌 것이 오면 그대로 패스합니다."""
    directories, files = _iterdir_seperating_directories_and_files(webtoon_directory)
    if thumbnail_name is None:
        with suppress(ValueError):
            files.remove(webtoon_directory / "webtoon.html")
        with suppress(ValueError):
            files.remove(webtoon_directory / "information.json")
        if len(files) == 1:
            thumbnail_path = files[0]
        else:
            for file in files:
                if file.name.startswith(webtoon_directory.name):
                    thumbnail_path = file
                    break
            else:
                thumbnail_path = _select_from_sequence(files, "Please select thumbnail in this list.")
        thumbnail_name = thumbnail_path.name

    if webtoon_title is None:
        webtoon_title_re = re.search("^.+(?=[.])", thumbnail_name)
        assert webtoon_title_re is not None
        webtoon_title = webtoon_title_re.group(0)

    return webtoon_title, thumbnail_name
