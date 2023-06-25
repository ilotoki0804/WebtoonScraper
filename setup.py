from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = '이 설명은 최신 버전이 아닐 수 있습니다. 만약 최신 버전을 확인하고 싶으시다면 [여기](https://github.com/ilotoki0804/WebtoonScraper)를 참고하세요.\n'
    long_description += f.read()
    long_description = long_description.replace('naver_webtoon.png', 'https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/master/naver_webtoon.png')
    long_description = long_description.replace('webtoons_original.png', 'https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/master/webtoons_original.png')
    long_description = long_description.replace('manhwakyung.png', 'https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/master/manhwakyung.png')
    long_description = long_description.replace('naver_post.png', 'https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/master/naver_post.png')

setup(
    name='WebtoonScraper',
    version='0.1.2',
    description='Scraping webtoons and some utils for it',
    author='ilotoki0804',
    author_email='ilotoki0804@gmail.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/ilotoki0804/WebtoonScraper',
    install_requires=['tqdm', 'bs4', 'requests', 'better_abc', 'async_lru', 'demjson3'],
    packages=find_packages(exclude=[]),
    keywords=['Webtoon', 'Webtoon Scraper', 'Naver Webtoon', 'Webtoon Downloader', 'Download Webtoon'],
    python_requires='>=3.10',
    package_data={},
    zip_safe=False,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)