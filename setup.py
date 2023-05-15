from setuptools import setup, find_packages

setup(
    name='WebtoonScraper',
    version='0.0.1',
    description='Scraping webtoons and some utils',
    author='ilotoki0804',
    author_email='ilotoki0804@gmail.com',
    url='https://github.com/ilotoki0804/WebtoonScraper',
    install_requires=['tqdm', 'bs4', 'requests', 'selenium'],
    packages=find_packages(exclude=[]),
    keywords=['webtoon', 'webtoon scraper', 'python datasets', 'python tutorial', 'pypi'],
    python_requires='>=3.6',
    package_data={},
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)