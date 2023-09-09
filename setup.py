from setuptools import setup, find_packages
import re
from pathlib import Path
import WebtoonScraper

long_description = '이 설명은 최신 버전이 아닐 수 있습니다. 만약 최신 버전을 확인하고 싶으시다면 [여기](https://github.com/ilotoki0804/WebtoonScraper)를 참고하세요.\n'
long_description += Path('README.md').read_text(encoding='utf-8')
# 사진 대체
repl = r'[\g<description>](https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/master/\g<path>)'
long_description = re.sub(r'[[](?P<description>.*?)[]][(](..\/)*(?P<path>(?:images|docs).*?)[)]',
                          repl, long_description)

version = WebtoonScraper.__version__

general_requirements = [line for line in Path('requirements.txt').read_text(encoding='utf-8').split()
                        if line[0] == '#']

if __name__ == '__main__':
    setup(
        name='WebtoonScraper',
        version=version,
        description='Scraping webtoons and some utils for it',
        author='ilotoki0804',
        author_email='ilotoki0804@gmail.com',
        long_description=long_description,
        long_description_content_type='text/markdown',
        license='MIT',
        url='https://github.com/ilotoki0804/WebtoonScraper',
        install_requires=general_requirements,
        packages=find_packages(exclude=[]),
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
