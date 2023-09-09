import os
import shutil
import subprocess
from pathlib import Path

PYTHON_PATH = Path('python_path.txt').read_text(encoding='utf-8')

shutil.rmtree('dist')
os.system(f'{PYTHON_PATH}python.exe setup.py sdist bdist_wheel')
whl_file_name = os.listdir('dist')[0]
os.system(f'{PYTHON_PATH}python.exe -m pip install --force-reinstall dist/{whl_file_name}')
if input('Submit changes? (y or not)') in ('y', 'Y', 'ㅛ'):
    token = Path('token.txt').read_text(encoding='utf-8')
    subprocess.run(["twine", "upload", "-u", '__token__', "-p", token, "dist/*"])
    os.system(f'{PYTHON_PATH}python.exe -m pip show webtoonscraper')
