from setuptools import setup, find_packages
import re
from pathlib import Path
from WebtoonScraper import __version__, __description__, __url__, __author__, __raw_source_url__, __author_email__, __title__

long_description = f'이 설명은 최신 버전이 아닐 수 있습니다. 만약 최신 버전을 확인하고 싶으시다면 [이 깃허브 링크]({__url__})를 참고하세요.\n'
long_description += Path('README.md').read_text(encoding='utf-8')


def repl_script(match: re.Match) -> str:
    if match.group('directory_type') == 'images':
        return rf'[{match.group("description")}]({__raw_source_url__}/{match.group("path")})'

    return rf'[{match.group("description")}]({__raw_source_url__}/{match.group("path")})'


long_description = re.sub(r'[[](?P<description>.*?)[]][(](..\/)*(?P<path>(?P<directory_type>images|docs).*?)[)]',
                          repl_script, long_description)


requirements = [line for line in Path('requirements.txt').read_text(encoding='utf-8').splitlines()
                if line and line[0] != '#']

if __name__ == '__main__':
    setup(
        name=__title__,
        version=__version__,
        description=__description__,
        author=__author__,
        author_email=__author_email__,
        long_description=long_description,
        long_description_content_type='text/markdown',
        license='MIT',
        url=__url__,
        install_requires=requirements,
        packages=['WebtoonScraper', 'WebtoonScraper.scrapers'],
        keywords=['Webtoon', 'Webtoon Scraper', 'Naver Webtoon', 'Webtoon Downloader', 'Download Webtoon'],
        python_requires='>=3.10',
        package_data={"WebtoonScraper": ["py.typed"]},
        zip_safe=False,
        classifiers=[
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
        ],
    )
