"""
░██╗░░░░░░░██╗███████╗██████╗░████████╗░█████╗░░█████╗░███╗░░██╗░██████╗░█████╗░██████╗░░█████╗░██████╗░███████╗██████╗░
░██║░░██╗░░██║██╔════╝██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗████╗░██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
░╚██╗████╗██╔╝█████╗░░██████╦╝░░░██║░░░██║░░██║██║░░██║██╔██╗██║╚█████╗░██║░░╚═╝██████╔╝███████║██████╔╝█████╗░░██████╔╝
░░████╔═████║░██╔══╝░░██╔══██╗░░░██║░░░██║░░██║██║░░██║██║╚████║░╚═══██╗██║░░██╗██╔══██╗██╔══██║██╔═══╝░██╔══╝░░██╔══██╗
░░╚██╔╝░╚██╔╝░███████╗██████╦╝░░░██║░░░╚█████╔╝╚█████╔╝██║░╚███║██████╔╝╚█████╔╝██║░░██║██║░░██║██║░░░░░███████╗██║░░██║
░░░╚═╝░░░╚═╝░░╚══════╝╚═════╝░░░░╚═╝░░░░╚════╝░░╚════╝░╚═╝░░╚══╝╚═════╝░░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░░░░╚══════╝╚═╝░░╚═╝

Scrape webtoons with ease.
"""  # noqa

from .directory_merger import DirectoryMerger

__title__ = "WebtoonScraper"
__description__ = "Scraping webtoons with ease."
__url__ = "https://github.com/ilotoki0804/WebtoonScraper"
__raw_source_url__ = "https://raw.githubusercontent.com/ilotoki0804/WebtoonScraper/master"
__version_info__ = (2, 2, 0)
__version__ = str.join('.', map(str, __version_info__))
__author__ = "ilotoki0804"
__author_email__ = "ilotoki0804@gmail.com"
__license__ = "MIT License"

import sys as _sys
if _sys.version_info < (3, 10):
    import logging
    logging.warning(f'Python version ({_sys.version}) is too low. Program may be run but not tested. '
                    'Upgrade Python if program not works well.')
if _sys.version_info[:3] == (3, 12, 0):
    import logging
    logging.warning('This program works on Python 3.12.0, but it hurts performance. '
                    'Use python 3.11(3.11.4 is recommended.) or 3.10.')
