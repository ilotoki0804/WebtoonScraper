from pathlib import Path
from setuptools import setup, find_packages

# this_directory = Path(__file__).parent
# long_description = (this_directory / "README.md").read_text()

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='WebtoonScraper',
    version='0.0.6',
    description='Scraping webtoons and some utils for it',
    author='ilotoki0804',
    author_email='ilotoki0804@gmail.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/ilotoki0804/WebtoonScraper',
    install_requires=['tqdm', 'bs4', 'requests'],
    packages=find_packages(exclude=[]),
    keywords=['Webtoon', 'Webtoon Scraper', 'Never Webtoon', 'Webtoon Downloader', 'Download Webtoon'],
    python_requires='>=3.6',
    package_data={},
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)