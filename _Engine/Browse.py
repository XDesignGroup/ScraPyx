import requests
import _Engine
from urllib.parse import unquote
from bs4 import BeautifulSoup as bs

def _url_parse(url: str, returnAsStr=True) -> str | list[str]:
    url = url.removeprefix("https://")
    url = url.removeprefix("http://")

    url = url.split("?", 1)[0]
    url = url.split("#", 1)[0]
    url = url.rstrip("/")

    url = unquote(url)
    if returnAsStr:
        return url
    else:
        return url.split("/")


class Browse:
    def __init__(self):
        self.cache = _Engine.Cache()

    def Get(self, url):
        # response.raise_for_status()

        ParsedUrl = _url_parse(url)

        if self.cache.exists(ParsedUrl):
            print("[CACHE]")
            self.content = self.cache.load(ParsedUrl)
        else:
            print("[REQUEST]")
            response = requests.get(url)
            response.raise_for_status()

            self.cache.save(ParsedUrl, response.text)
            self.content = response.text

        return self

    def content(self):
        Soup = bs(self.content, "html.parser")
        return Soup