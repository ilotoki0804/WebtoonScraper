"""빌드를 자동화합니다."""
import os
import shutil
from pathlib import Path

import tomlkit
from WebtoonScraper import __version__

try:
    shutil.rmtree('dist')
except FileNotFoundError:
    os.mkdir('dist')

# update pyproject.toml version
pyproject_path = Path("pyproject.toml")
pyproject_data = tomlkit.parse(pyproject_path.read_text())
pyproject_data['tool']['poetry']['version'] = __version__  # type: ignore
pyproject_path.write_text(tomlkit.dumps(pyproject_data), encoding='utf-8')

os.system('poetry build')
os.system(f'poetry publish -u __token__ -p {Path("_token.txt").read_text("utf-8")}')
