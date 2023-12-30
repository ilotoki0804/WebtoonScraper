"""Automate build.

v.2023-12-30(3)
"""
import os
import shutil
from pathlib import Path
import re

import tomlkit
from WebtoonScraper import __version__, __url__, __github_user_name__, __github_project_name__

LEAVE_README_BUILD_VERSION = False
PUBLISH = True

github_project_url = f"https://github.com/{__github_user_name__}/{__github_project_name__}"


def make_relative_link_work(match: re.Match) -> str:
    if match.group('directory_type') == 'images':
        return (
            f'[{match.group("description")}]'
            f'(https://raw.githubusercontent.com/{__github_user_name__}'
            f'/{__github_project_name__}/master/'
            f'{match.group("path")})'
        )

    return (
        f'[{match.group("description")}]'
        f'({github_project_url}/blob/master/{match.group("path")})'
    )


try:
    shutil.rmtree('dist')
except FileNotFoundError:
    os.mkdir('dist')

# update pyproject.toml version
pyproject_path = Path("pyproject.toml")
pyproject_data = tomlkit.parse(pyproject_path.read_text())
pyproject_data['tool']['poetry']['version'] = __version__  # type: ignore
pyproject_path.write_text(tomlkit.dumps(pyproject_data), encoding='utf-8')

long_description = f'이 설명은 최신 버전이 아닐 수 있습니다. 만약 최신 버전을 확인하고 싶으시다면 [이 깃허브 링크]({github_project_url})를 참고하세요.\n'
long_description += Path('README.md').read_text(encoding='utf-8')
long_description = re.sub(r'[[](?P<description>.*?)[]][(](..\/)*(?P<path>(?P<directory_type>images|docs).*?)[)]',
                          make_relative_link_work, long_description)

try:
    Path("README_build.md").write_text(long_description, encoding='utf-8')

    os.system('poetry build')
    if PUBLISH:
        os.system(f'poetry publish -u __token__ -p {Path("_token.txt").read_text("utf-8")}')
finally:
    if not LEAVE_README_BUILD_VERSION:
        os.remove("README_build.md")
