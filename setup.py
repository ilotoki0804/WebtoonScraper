from setuptools import setup, find_packages

# this_directory = Path(__file__).parent
# long_description = (this_directory / "README.md").read_text()

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='WebtoonScraper',
    version='0.0.18',
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
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)