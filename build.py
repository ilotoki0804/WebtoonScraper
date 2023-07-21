import os
import shutil
import subprocess
from pathlib import Path

# os.mkdir('dist')
shutil.rmtree('dist')
os.system('python setup.py sdist bdist_wheel')
whl_file_name = os.listdir('dist')[0]
os.system(f'pip install --force-reinstall dist/{whl_file_name}')  # --user를 추가하면 오류가 덜 날 수도 있음
if input('Submit changes? (y or not)') in ('y', 'Y', 'ㅛ'):
    token = Path('token.txt').read_text(encoding='utf-8')
    subprocess.run(["twine", "upload", "-u", '__token__', "-p", token, "dist/*"])
os.system('pip show webtoonscraper')
