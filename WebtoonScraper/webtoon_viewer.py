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
        const comments = {comments};
        const commentCounts = {comment_counts};
        const authorComments = {author_comments};
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
        let episodeNo = getEpisodeNo();
        let viewedEpisodes = [];

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
                        document.getElementById("platform-warning").innerText = "Check whether your files are intect or not."
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

            let episode_comments = comments[episodeNo];
            if (!episode_comments) {
                console.log("There's no comments to show.");
                commentsBox.style.display = "none";
                showComments.style.display = "none";
                return;
            }

            function createCommentBox(information) {
                comment = document.createElement("div");
                comment.classList.add("comment-box");
                comment.innerHTML = `
                    <div class="username"><strong>${escapeHTML(information.username)}</strong> <small>${information.created}</small></div>
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

            let authorComment = authorComments[episodeNo];
            if (authorComment) {
                let authorCommentDiv = document.createElement("div");
                authorCommentDiv.classList.add("author-comment-box");
                authorCommentDiv.innerHTML = `<strong>${authorName}</strong>: ${authorComment}`;
                commentsBox.appendChild(authorCommentDiv);
            } else {
                console.log("There's no author comment to present.");
            }

            episode_comments.forEach((comment) => commentsBox.appendChild(createCommentBox(comment)));
            // commentsBox.appendChild(createCommentBox({
            //     "comments_id": "1234",
            //     "reply_count": 50,
            //     "comment": "진돌진돌진돌 세끼진돌진돌 번식진돌진돌 가족진돌진돌 진돌진돌진돌",
            //     "username": "진돌",
            //     "likes": 1000,
            //     "dislikes": 23,
            //     "last_modified": "2023-01-10",
            //     "created": "2023-01-10",
            //     "replies": [],
            // }));
        }

        function refreshCommentsButton() {
            let episodeCommentCount = commentCounts[episodeNo];
            if (episodeCommentCount) {
                if (commentsShowed) {
                    commentsBox.style.display = "none";
                    showComments.innerText = `Show ${episodeCommentCount} comment(s)`;
                } else {
                    commentsBox.style.display = "flex";
                    showComments.innerText = `Hide ${episodeCommentCount} comment(s)`;
                }
            } else {
                if (commentsShowed) {
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


def add_html_webtoon_viewer(webtoon_directory: Path) -> None:
    """information.json의 데이터보다 인자로 주어진 데이터를 더 우선 순위로 잡습니다."""
    directories, files = _iterdir_seperating_directories_and_files(webtoon_directory)
    for file in files:
        if file.name == "information.json":
            with file.open("r", encoding="utf-8") as f:
                information = json.load(f)
            webtoon_title = information["title"]
            thumbnail_name = information["thumbnail_name"]
            comments = information.get("comments", {})
            comment_counts = information.get("comment_counts", {})
            author_comments = information.get("author_comments", {})
            author_name = information.get("author_name", "author")
            merge_number = information["merge_number"]
            break
    else:
        raise ValueError("There's no information.json, thus cannot create webtoon viewer.")

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
        .replace(r"{webtoon_title}", escape(webtoon_title))  # type: ignore
        .replace(r"{webtoon_title_repr}", json.dumps(webtoon_title, ensure_ascii=False))
        .replace(r"{episode_directories}", episode_directories)
        .replace(r"{images_of_episode_directories}", images_of_episode_directories)
        .replace(r"{version}", version)
        .replace(r"{created_time}", json.dumps(datetime.now().isoformat()))
        .replace(r"{comments}", json.dumps(comments, ensure_ascii=False))
        .replace(r"{comment_counts}", json.dumps(comment_counts))
        .replace(r"{author_comments}", json.dumps(author_comments))
        .replace(r"{author_name}", json.dumps(author_name))
        .replace(r"{merge_number}", "null" if merge_number is None else str(merge_number))
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
