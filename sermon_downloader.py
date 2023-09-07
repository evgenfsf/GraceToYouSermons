import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import re
from loguru import logger

class SermonDownloader():
    def __init__(self):
        self.driver = self.GTYDriver()
        self.parser = self.GTYParser(self.driver.page_source)

    class GTYDriver(webdriver.Firefox):
        def __init__(self):
            defaultlink = "https://www.gty.org/library/resources/sermons-library"
            options = webdriver.FirefoxOptions()
            options.add_argument('--headless')
            super().__init__(options=options)
            logger.info(f"WebDriver started")
            self.get(defaultlink)
    
    class GTYParser(BeautifulSoup):
        def __init__(self, source) -> None:
            super().__init__(source, features="html.parser")
            logger.info(f"Parser started")
        
        def parse_sermon(self):
            return Sermon("")

    class Book():
        def __init__(self):
            pass

        def go(self):
            pass

    class Chapter():
        def __init__(self):
            pass

    class Sermon():     #result of BeautifulSoup.find or .findall
        def __init__(self):
            pass

        def download(self):
            pass

        def name(self):
            pass