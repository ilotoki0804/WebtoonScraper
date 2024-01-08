from contextlib import suppress
import json
import os
from pathlib import Path
import re

from .directory_merger import _iterdir_seperating_directories_and_files, _select_from_sequence
from .miscs import __version__ as version

HTML_TEMPLATE = """\
<!-- WITH VERSION {version} -->
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
        <!-- <input type="number" class="episode-redirect" name="name" min="1" /> -->
        <button class="next-episode">다음 에피소드</button>
    </div>
    <div id="image-container"></div>
    <div class="episode-selector">
        <button class="next-episode" style="width: 70%; height: 200px; font-size: 3em; background-color: aliceblue;" type="button">다음 에피소드</button>
        <br>
        <button class="prev-episode">이전 에피소드</button>
        <select class="episode-selector-dropdown"></select>
        <!-- <input type="number" class="episode-redirect" name="name" min="1" /> -->
        <br>
        <span class="title-bar"></span>
    </div>
    <script>
        let episodeNo = 0;
        const webtoonTitle = {webtoon_title_repr};
        const episodeDirectories = {episode_directories};
        const webtoonImagesOfDirectories = {images_of_episode_directories};
        const prevEpisodeButtons = Array.from(document.getElementsByClassName("prev-episode"));
        const nextEpisodeButtons = Array.from(document.getElementsByClassName("next-episode"));
        // const episodeNumberInput = Array.from(document.getElementsByClassName('episode-redirect'));
        const titleBars = Array.from(document.getElementsByClassName("title-bar"));
        const episodeSelectors = Array.from(document.getElementsByClassName("episode-selector-dropdown"));

        (function renderDropdown() {
            episodeSelectors.forEach((selector) => {
                episodeDirectories.forEach((episodeDirectory, index) => {
                    const option = document.createElement("option")
                    option.value = index
                    option.innerHTML = episodeDirectory
                    option.selected = index == episodeNo
                    selector.appendChild(option)
                });
                selector.addEventListener("input", function(event) {
                    selector.childNodes.forEach((options, index) => {
                        if (options.selected) {
                            drawImage(index)
                        }
                    })
                });
            });
        })();


        drawImage(episodeNo)
        function drawImage(index) {
            episodeNo = index
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
            episodeSelectors.forEach((selector) => {
                selector.childNodes.forEach((option, optionIndex) => {
                    option.selected = optionIndex == episodeNo
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

        // episodeNumberInput.forEach((input) => {
        //     input.addEventListener('keydown', function(event) {
        //         if (event.key === 'Enter') {
        //             const value = parseInt(event.target.value) - 1
        //             drawImage(value)
        //         }
        //     });
        // });
    </script>
</body>
</html>
"""


def add_html_webtoon_viewer(webtoon_directory: Path) -> None:
    directories, files = _iterdir_seperating_directories_and_files(webtoon_directory)
    with suppress(ValueError):
        files.remove(webtoon_directory / "webtoon.html")
    if len(files) == 1:
        thumbnail_name = files[0]
    else:
        for file in files:
            if file.name.startswith(webtoon_directory.name):
                thumbnail_name = file
                break
        else:
            thumbnail_name = _select_from_sequence(files, "Please select thumbnail in this list.")

    webtoon_title = re.search("^.+(?=[.])", thumbnail_name.name)
    assert webtoon_title is not None
    webtoon_title = webtoon_title.group(0)

    episode_directories = json.dumps([directory.name for directory in directories], ensure_ascii=False)
    images_of_episode_directories = json.dumps([
        os.listdir(episode_directory_name)
        for episode_directory_name in directories
    ], ensure_ascii=False)

    html = (
        HTML_TEMPLATE
        .replace(r"{webtoon_thumbnail_name_repr}", json.dumps(thumbnail_name.name, ensure_ascii=False))
        .replace(r"{webtoon_title}", webtoon_title)
        .replace(r"{webtoon_title_repr}", json.dumps(webtoon_title, ensure_ascii=False))
        .replace(r"{episode_directories}", episode_directories)
        .replace(r"{images_of_episode_directories}", images_of_episode_directories)
        .replace(r"{version}", version)
    )
    (webtoon_directory / "webtoon.html").write_text(html, encoding='utf-8')
