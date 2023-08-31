import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import re
from loguru import logger

class SermonDownloader():
    def __init__(self) -> None:
        self.driver = self.GTYDriver()
        self.parser = self.GTYParser(self.driver.page_source)

    class GTYDriver(webdriver.Firefox):
        def __init__(self) -> None:
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

class Sermon():
    def __init__(self) -> None:
        pass
