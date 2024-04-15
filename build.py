"""
Replace relative path links with GitHub links and add warning in front of the long description.

Last modified at 2023-04-12; 9th edition.
"""

import os
import re
import shutil
from pathlib import Path

import tomlkit

from WebtoonScraper import __url__ as url
from WebtoonScraper import __version__ as version

LEAVE_README_BUILD_VERSION = False
PUBLISH = True

# LEAVE_README_BUILD_VERSION = True
# PUBLISH = False


def match_url(url: str) -> tuple[str, str]:
    result = re.match(
        r"(https?:\/\/)?github[.]com\/(?P<user>\w+)\/(?P<project>\w+)", url
    )
    if result is None:
        raise ValueError("URL is invalid or not a github URL.")
    return result["user"], result["project"]


username, project_name = match_url(url)
github_project_url = f"https://github.com/{username}/{project_name}"


def make_relative_link_work(match: re.Match) -> str:
    if match.group("directory_type") == "images":
        return (
            f'[{match.group("description")}]'
            f'(https://raw.githubusercontent.com/{username}'
            f'/{project_name}/master/'
            f'{match.group("path")})'
        )

    return (
        f'[{match.group("description")}]'
        f'({github_project_url}/blob/master/{match.group("path")})'
    )


def main():
    try:
        shutil.rmtree("dist")
    except FileNotFoundError:
        os.mkdir("dist")

    # update pyproject.toml version
    pyproject_path = Path("pyproject.toml")
    pyproject_data = tomlkit.parse(pyproject_path.read_text())
    pyproject_data["tool"]["poetry"]["version"] = version  # type: ignore
    pyproject_path.write_text(tomlkit.dumps(pyproject_data), encoding="utf-8")

    long_description = f"**Check lastest version [here]({github_project_url}).**\n"
    long_description += Path("README.md").read_text(encoding="utf-8")
    long_description = re.sub(
        r"\[(?P<description>.*?)\]\((..\/)*(?P<path>(?P<directory_type>images|docs).*?)\)",
        make_relative_link_work,
        long_description,
    )

    try:
        Path("README_build.md").write_text(long_description, encoding="utf-8")

        os.system("poetry build")
        if PUBLISH:
            if "PYPI_TOKEN" not in os.environ:
                raise ValueError("Environment variable `PYPI_TOKEN` is not set.")

            os.system(f'poetry publish -u __token__ -p {os.environ["PYPI_TOKEN"]}')
    finally:
        if not LEAVE_README_BUILD_VERSION:
            os.remove("README_build.md")


if __name__ == "__main__":
    main()
