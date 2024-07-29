"""HTML로 된 웹툰을 볼 수 있는 뷰어를 제공합니다."""

from __future__ import annotations

import json
import os
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Sequence, TypeVar

from ..base import __version__ as version
from .directory_merger import _directories_and_files_of

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
        body {
            background-color: rgb(249, 249, 249);
        }
        .episode-selector {
            text-align: center;
            padding-bottom: 1rem;
        }
        .margin {
            margin-top: 1rem;
        }
        div#image-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            width: 100%;
        }
        #big-button {
            height: 12rem;
            font-size: 3rem;
            background-color: rgb(200, 239, 137);
            border: 3rem darkblue darkblue;
            border-color: rgb(200, 239, 137);
            margin-bottom: 1rem;
            border-radius: 1rem;
        }
        @media (orientation: portrait) {
            div#image-container img, #big-button, .comment-box, .author-comment-box {
                width: 100%;
            }
        }
        @media (orientation: landscape) {
            div#image-container img, #big-button, .comment-box, .author-comment-box {
                width: 40rem;
            }
        }

        #comments {
            text-align: justify;
            display: flex;
            flex-direction: column;
            align-content: center;
            align-items: center;
            margin-bottom: 3rem;
            display: none;
        }

        .comment-box {
            border: solid #000;
            background-color: white;

            padding: 1rem;
            box-sizing: border-box;
            margin-top: 1rem;

            text-align: justify;
        }

        .comment-box > div + div {
            margin-top: 1rem;
        }

        .username > small, .buttons > small {
            float: right;
        }

        .show-reply {
            display: inline;
        }

        .author-comment-box {
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <header class="episode-selector">
        <div id="platform-warning"></div>
        <span class="title-bar"></span>
        <br>
        <button class="prev-episode">이전 에피소드</button>
        <select class="episode-selector-dropdown"></select>
        <button id="delete-history">조회 기록 지우기</button>
        <button class="next-episode">다음 에피소드</button>
    </header>
    <div id="image-container"></div>
    <div class="episode-selector margin">
        <button class="next-episode" id="big-button" type="button">다음 에피소드</button>
        <br>
        <button class="prev-episode">이전 에피소드</button>
        <select class="episode-selector-dropdown"></select>
        <button id="show-comments" type="button">Show comments</button>
        <br>
        <div id="comments"></div>
        <span class="title-bar"></span>
    </div>
    <script>
        const webtoonTitle = {webtoon_title_repr};
        const episodeDirectories = {episode_directories};
        const webtoonImagesOfDirectories = {images_of_episode_directories};
        const createdTime = {created_time};
        const commentsData = {comments_data};
        const authorName = {author_name};
        const mergeNumber = {merge_number};

        const localStorageName = `viewedEpisode(${webtoonTitle})`;
        const prevEpisodeButtons = Array.from(document.getElementsByClassName("prev-episode"));
        const nextEpisodeButtons = Array.from(document.getElementsByClassName("next-episode"));
        const titleBars = Array.from(document.getElementsByClassName("title-bar"));
        const episodeSelectors = Array.from(document.getElementsByClassName("episode-selector-dropdown"));
        const viewedEpisodesLocalStorageName = `viewedEpisodes@${webtoonTitle}(${createdTime})`;
        const resetButton = document.getElementById("delete-history");
        const commentsBox = document.getElementById("comments");
        const showComments = document.getElementById("show-comments");
        let commentsShowed = false;
        let viewedEpisodes = [];
        let episodeNo;
        episodeNo = getEpisodeNo();

        function getEpisodeNo() {
            const urlParams = new URLSearchParams(window.location.search);
            let episodeNo = urlParams.get("episode_no");
            if (episodeNo == null) {
                applyEpisodeNoAndRender(0);
                return 0;
            } else {
                return episodeNo - 1;
            }
        }

        function applyEpisodeNoAndRender(value) {
            if (value < 0 || value >= episodeDirectories.length) {
                console.error("Cannot apply episodeNo; incorrect value: " + value)
                return;
            }
            const urlParams = new URLSearchParams(window.location.search);
            urlParams.set("episode_no", value + 1);
            window.history.pushState(null, null, `?${urlParams.toString()}`);
            episodeNo = value;
            refresh();
        }

        function refresh() {
            let index = episodeNo;
            const imageContainer = document.getElementById('image-container');

            const directoryName = episodeDirectories[index];
            const imagesName = webtoonImagesOfDirectories[index];
            const webtoonImages = imagesName.map((imageName, index) => {
                return directoryName + "/" + imageName;
            });

            titleBars.forEach((titleBar) => {
                titleBar.innerText = `${webtoonTitle} by ${authorName} | ${directoryName} | downloaded via WebtoonScraper`
            });

            while (imageContainer.lastChild) {
                imageContainer.removeChild(imageContainer.lastChild);
            }

            webtoonImages.forEach((webtoonImageSrc, index) => {
                const image = document.createElement("img");
                image.src = webtoonImageSrc;
                image.alt = imagesName[index];
                image.onerror = () => {
                    if (/Android|iPad|iPhone|iPod/.test(navigator.userAgent)) {
                        document.getElementById("platform-warning").innerText = "This may not work well in mobile platforms."
                    } else {
                        document.getElementById("platform-warning").innerText = "Check whether your files are intact or not."
                    }
                };
                imageContainer.appendChild(image);
            });

            viewedEpisodes[index] = true;
            window.localStorage.setItem(viewedEpisodesLocalStorageName, JSON.stringify(viewedEpisodes));

            episodeSelectors.forEach((selector) => {
                selector.childNodes.forEach((option, optionIndex) => {
                    if (viewedEpisodes[optionIndex]) {
                        option.innerText = "☑ " + episodeDirectories[optionIndex];
                    } else {
                        option.innerText = "☐ " + episodeDirectories[optionIndex];
                    }
                    option.selected = optionIndex == episodeNo;
                })
            });

            window.scrollTo(0, 0);
            updateButtons();
            updateComments();
        }

        function updateButtons() {
            if (episodeNo == 0) {
                prevEpisodeButtons.forEach((button) => {
                    button.innerText = "이전 회차가 없습니다.";
                    button.disabled = true;
                });
            } else {
                prevEpisodeButtons.forEach((button) => {
                    button.innerText = "이전 회차";
                    button.disabled = false;
                });
            }
            if (episodeDirectories.length - 1 <= episodeNo) {
                nextEpisodeButtons.forEach((button) => {
                    button.innerText = "다음 회차가 없습니다.";
                    button.disabled = true;
                });
            } else {
                nextEpisodeButtons.forEach((button) => {
                    button.innerText = "다음 회차";
                    button.disabled = false;
                });
            }
        }

        function escapeHTML(unsafeText) {
            let div = document.createElement('div');
            div.innerText = unsafeText;
            return div.innerHTML;
        }

        function updateComments() {
            refreshCommentsButton();

            let episode_comments = commentsData[episodeNo]["comments"];
            if (!episode_comments) {
                console.log("There's no comments to show.");
                commentsBox.style.display = "none";
                showComments.style.display = "none";
                return;
            }

            function createCommentBox(information) {
                comment = document.createElement("div");
                comment.classList.add("comment-box");
                let createdTime = (new Date(information.created)).toLocaleString();
                comment.innerHTML = `
                    <div class="username"><strong>${escapeHTML(information.username)}</strong> <small>${createdTime}</small></div>
                    <div class="comment-body">${escapeHTML(information.comment)}</div>
                    <div class="created-date"></div>
                    <div class="buttons">
                        <button class="show-reply">${information.reply_count} ${information.reply_count <= 1? "reply": "replies"}</button>
                        <small>👍${information.likes} 👎${information.dislikes}</small>
                    </div>
                    <div class="replies"></div>
                `.replace(/  +/g, '');
                return comment;
            }

            while (commentsBox.lastChild) {
                commentsBox.removeChild(commentsBox.lastChild);
            }

            let authorComment = commentsData[episodeNo]["author_comment"];
            if (authorComment && authorComment != ".") {
                let authorCommentDiv = document.createElement("div");
                authorCommentDiv.classList.add("author-comment-box");
                authorCommentDiv.innerHTML = `<strong>${authorName}</strong>: ${authorComment}`;
                commentsBox.appendChild(authorCommentDiv);
            } else {
                console.log("There's no author comment to present, or the author comment was `.`.");
            }

            episode_comments.forEach((comment) => commentsBox.appendChild(createCommentBox(comment)));
        }

        function refreshCommentsButton() {
            let episodeCommentCount = commentsData[episodeNo]["comment_count"];
            if (episodeCommentCount) {
                if (!commentsShowed) {
                    commentsBox.style.display = "none";
                    showComments.innerText = `Show ${episodeCommentCount} comment(s)`;
                } else {
                    commentsBox.style.display = "flex";
                    showComments.innerText = `Hide ${episodeCommentCount} comment(s)`;
                }
            } else {
                if (!commentsShowed) {
                    commentsBox.style.display = "none";
                    showComments.innerText = "Show comments";
                } else {
                    commentsBox.style.display = "flex";
                    showComments.innerText = "Hide comments";
                }
            }
        }

        let viewedEpisodesRaw = window.localStorage.getItem(viewedEpisodesLocalStorageName);
        if (viewedEpisodesRaw == null) {
            viewedEpisodes = [];
            episodeDirectories.forEach(() => viewedEpisodes.push(false));
            window.localStorage.setItem(viewedEpisodesLocalStorageName, JSON.stringify(viewedEpisodes));
        } else {
            viewedEpisodes = Array.from(JSON.parse(viewedEpisodesRaw));
        }

        episodeSelectors.forEach((selector) => {
            episodeDirectories.forEach((episodeDirectory, index) => {
                const option = document.createElement("option");
                option.value = index;
                option.innerHTML = episodeDirectory;
                option.selected = index == episodeNo;
                selector.appendChild(option);
            });
            selector.addEventListener("input", (event) => {
                selector.childNodes.forEach((options, index) => {
                    if (options.selected) {
                        applyEpisodeNoAndRender(index);
                    }
                })
            });
        });

        prevEpisodeButtons.forEach((button) => {
            button.addEventListener("click", () => {
                applyEpisodeNoAndRender(episodeNo - 1);
            });
        });
        nextEpisodeButtons.forEach((button) => {
            button.addEventListener("click", () => {
                applyEpisodeNoAndRender(episodeNo + 1);
            });
        });
        resetButton.addEventListener("click", () => {
            window.localStorage.removeItem(viewedEpisodesLocalStorageName);
            viewedEpisodes = [];
            applyEpisodeNoAndRender(episodeNo);
        });
        showComments.addEventListener("click", () => {
            commentsShowed ^= true;
            updateComments();
        });

        applyEpisodeNoAndRender(episodeNo);
    </script>
</body>
</html>\
"""

T = TypeVar("T")


def _select_from_sequence(choices: Sequence[T], message: str | None) -> T:
    """사용자에게 여러 개의 선택지를 보여주고 결정할 수 있도록 하는 CLI용 선택 시 사용할 수 있는 툴입니다.

    Arguments:
        choices: 사용자가 고를 수 있는 선택지입니다. Sequence여야 제대로 동작합니다.
        message: 선택지들을 보여주기 전 사용자에게 어떤 선택지를 골라야 하는지 설명합니다.

    Returns:
        choices 중 사용자가 고른 선택지의 값을 반환합니다.

    Raises:
        TypeError: choices가 Sequence가 아닌 경우 발생합니다.
        ValueError: 사용자의 입력이 올바르지 않은 경우 발생합니다.
        IndexError: 사용자가 범위를 벗어나는 선택을 했을 때 발생합니다.

    Example:
        ```python
        >>> user_choice = _select_from_sequence(["첫번째", "두번째", "세번째"], "웹툰을 선택하세요.")
        웹툰을 선택하세요.
        1. 첫번째
        2. 두번째
        3. 세번째
        Enter number: 2
        >>> print(user_choice)
        두번째
        ```
    """
    if message is not None:
        print(message)
    if len(choices) < 10:
        for i, item in enumerate(choices, 1):
            print(f"{i}. {item}")
    else:
        for i, item in enumerate(choices, 1):
            print(f"{i:02d}. {item}")

    user_answer = int(input("Enter number: "))
    return choices[user_answer - 1]


def add_html_webtoon_viewer(webtoon_directory: Path) -> None:
    """웹툰 디렉토리에 사용할 수 있는 `webtoon.html`이라는 웹툰 뷰어를 추가합니다.

    Arguments:
        webtoon_directory: 일반적인 웹툰 디렉토리입니다. 이때 이 디렉토리에는 웹툰이 있어야 하며 \
            손상되지 않은 information.json 파일이 존재하여야 합니다.

    Raises:
        ValueError: 웹툰 디렉토리에 information.json이 없을 경우 발생합니다.

    Example:
        ```python
        >>> from pathlib import Path
        >>> from WebtoonScraper.webtoon_viewer import add_html_webtoon_viewer
        >>> add_html_webtoon_viewer(Path("./webtoon/웹툰 이름(1234567)"))
        ```
    """

    # 웹툰 정보 불러옴. 이때 선택적 정보가 없는 경우 빈 값으로 설정함.
    directories, files = _directories_and_files_of(webtoon_directory)
    for file in files:
        if file.name == "information.json":
            with file.open("r", encoding="utf-8") as f:
                information: dict[str, Any] = json.load(f)
            webtoon_title = information["title"]
            thumbnail_name = information["thumbnail_name"]
            comments_data = information.get("comments_data", {})
            author_name = information.get("author", "author")
            merge_number = information["merge_number"]
            break
    else:
        raise ValueError("There's no information.json, thus cannot create webtoon viewer.")

    # 에피소드 디렉토리 이름 및 이미지 이름 추출.
    # 후에 webtoon.html에서 드롭다운 메뉴에 에피소드 이름을 표시하고 이미지를 출력하는 데에 사용됨.
    episode_directories = json.dumps([directory.name for directory in directories], ensure_ascii=False)
    images_of_episode_directories = json.dumps(
        [sorted(os.listdir(episode_directory_name)) for episode_directory_name in directories],
        ensure_ascii=False,
    )

    # HTML 제작 및 파일에 작성.
    html = (
        HTML_TEMPLATE.replace(
            r"{webtoon_thumbnail_name_repr}",
            json.dumps(thumbnail_name, ensure_ascii=False),
        )
        .replace(r"{webtoon_title}", escape(webtoon_title))  # type: ignore
        .replace(r"{webtoon_title_repr}", json.dumps(webtoon_title, ensure_ascii=False))
        .replace(r"{episode_directories}", episode_directories)
        .replace(r"{images_of_episode_directories}", images_of_episode_directories)
        .replace(r"{version}", version)
        .replace(r"{created_time}", json.dumps(datetime.now().isoformat()))
        .replace(r"{comments_data}", json.dumps(comments_data, ensure_ascii=False))
        .replace(r"{author_name}", json.dumps(author_name, ensure_ascii=False))
        .replace(r"{merge_number}", "null" if merge_number is None else str(merge_number))
    )
    (webtoon_directory / "webtoon.html").write_text(html, encoding="utf-8")
