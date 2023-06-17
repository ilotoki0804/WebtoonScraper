from setuptools import setup, find_packages

# this_directory = Path(__file__).parent
# long_description = (this_directory / "README.md").read_text()

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = '이 설명은 최신 버전이 아닐 수 있습니다. 만약 최신 버전을 확인하고 싶으시다면 [여기](https://github.com/ilotoki0804/WebtoonScraper)를 참고하세요.\n'
    long_description += f.read()
    long_description = long_description.replace('titleid_from_nw.png', 'https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/master/titleid_from_nw.png')
    long_description = long_description.replace('title_no_from_webtoons.com.png', 'https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/master/title_no_from_webtoons.com.png')
    long_description = long_description.replace('number_from_manhwakyung.png', 'https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/master/number_from_manhwakyung.png')

setup(
    name='WebtoonScraper',
    version='0.0.19.2',
    description='Scraping webtoons and some utils for it',
    author='ilotoki0804',
    author_email='ilotoki0804@gmail.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/ilotoki0804/WebtoonScraper',
    install_requires=['tqdm', 'bs4', 'requests', 'better_abc'],
    packages=find_packages(exclude=[]),
    keywords=['Webtoon', 'Webtoon Scraper', 'Never Webtoon', 'Webtoon Downloader', 'Download Webtoon'],
    python_requires='>=3.8',
    package_data={},
    zip_safe=False,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)