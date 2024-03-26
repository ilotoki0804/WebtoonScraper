"""Build a package that works on PyPI.

Replace relative links with GitHub links and add warning 

This program is not meant to be used as module.

Last modified at 2023-03-26; 7th edition.
"""
import os
import shutil
from pathlib import Path
import re

import tomlkit
from WebtoonScraper import __version__, __url__, __github_user_name__, __github_project_name__

LEAVE_README_BUILD_VERSION = False
PUBLISH = True

# LEAVE_README_BUILD_VERSION = True
# PUBLISH = False

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

long_description = f'Check lastest version [here]({github_project_url}).\n'
long_description += Path('README.md').read_text(encoding='utf-8')
long_description = re.sub(r'\[(?P<description>.*?)\]\((..\/)*(?P<path>(?P<directory_type>images|docs).*?)\)',
                          make_relative_link_work, long_description)

try:
    Path("README_build.md").write_text(long_description, encoding='utf-8')

    os.system('poetry build')
    if PUBLISH:
        if "PYPI_TOKEN" not in os.environ:
            raise ValueError("Environment variable `PYPI_TOKEN` is not defined. Please set it.")

        os.system(f'poetry publish -u __token__ -p {os.environ["PYPI_TOKEN"]}')
finally:
    if not LEAVE_README_BUILD_VERSION:
        os.remove("README_build.md")
