import requests
from bs4 import BeautifulSoup as bs

USER_AGENT = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.68'}

def get_soup_from_requests(url, select: str|None=None, user_agent: dict|bool=True) -> bs|list:
    if user_agent:
        if user_agent == True:
            request = requests.get(url, headers=USER_AGENT)
        else:
            request = requests.get(url, headers=user_agent)
    else:
        request = requests.get(url)

    soup = bs(request.text, "html.parser")
    if select:
        return soup.select(select)
    else:
        return soup