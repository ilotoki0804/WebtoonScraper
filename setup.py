from setuptools import setup, find_packages
import re
from pathlib import Path
from WebtoonScraper import __version__, __description__, __url__, __author__, __raw_source_url__, __author_email__, __title__


PACKAGES = [__title__, f'{__title__}.scrapers']
KEYWORDS = ['Webtoon', 'Webtoon Scraper', 'Naver Webtoon', 'Webtoon Downloader', 'Download Webtoon']
PYTHON_VERSION_MINIMUM = (3, 10)
CLASSIFIERS = [
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    # 'Programming Language :: Python :: 3.12',
]
EXTRA_REQUIREMENTS = {}
HAS_CLI = True
HAS_READTHEDOCS = False  # 지원하기
HAS_GITBOOK = True
LICENSE = 'MIT'


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
test_requirements = [line for line in Path('requirements_dev.txt').read_text(encoding='utf-8').splitlines()
                     if line and line[0] != '#']


def main() -> None:
    setup(
        name=__title__,
        version=__version__,
        description=__description__,
        author=__author__,
        author_email=__author_email__,
        url=__url__,
        project_urls={
            "Documentation": f'https://ilotoki0804.gitbook.io/{__title__}/' if HAS_GITBOOK
                             else f"https://{__title__}.readthedocs.io" if HAS_READTHEDOCS
                             else None,
            "Source": __url__,
        },

        long_description=long_description,
        long_description_content_type='text/markdown',

        license=LICENSE,
        packages=PACKAGES,
        keywords=KEYWORDS,
        classifiers=CLASSIFIERS,
        python_requires=F'>={".".join(map(str, PYTHON_VERSION_MINIMUM))}',

        install_requires=requirements,
        extras_require=EXTRA_REQUIREMENTS or None,  # or None이 필요하지 않을 수도 있음.

        package_data={__title__: ["py.typed"]},
        zip_safe=False,
        entry_points={
            'console_scripts': [
                f'{__title__} = {__title__}:__main__.main',
            ],
        } if HAS_CLI else None,
    )


if __name__ == '__main__':
    main()
