import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import re
from loguru import logger
import sys

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
            
    def current_page(self):
        return Page(self.parser.findAll(class_='gty-asset store-library sermon'))
    
    def quit(self):
        self.GTYDriver.quit()
        logger.info("Driver Stopped")
        sys.exit()

class Book():
    def __init__(self):
        pass

    def go(self):
        pass

class Chapter():
    def __init__(self):
        pass
        
class Page():
    def __init__(self, content):
        self.content = content
        
    def download(self):
        with requests.Session() as session:
            for sermon in self.content:
                with Sermon(sermon) as s:
                    s.download(session)


class Sermon(): 
    def __init__(self, source):
        """_summary_

        Args:
            source (bs4.element.Tag): result of BeautifulSoup.find or .findAll
        """
        self.title = source.find(class_="title").span.string
        self.scripture = source.find(class_="scripture").span.string
        self.code = source.find(class_="code").span.string
        self.filename = self.filename_correct()
        self.download_server = "https://cdn.gty.org/sermons/High/"
    
    def __enter__(self):
        return self
    
    def __exit__(self, ex_type, ex_val, ex_trace):
        del self
        
    def filename_correct(self):
        fn = f"{self.scripture}_{self.title}_{self.code}.mp3"
        return fn.translate ({ord(c): "-" for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})
    
    def download(self, session):
        logger.info(f"Downloading {self.filename}")
        download = session.get(f"{self.download_server}{self.code}.mp3")
        if download.status_code == 200:
            logger.success(f"Download Succeeded: {self.filename}")
            with open(self.filename, 'wb') as f:            #open in binary mode to avoid errors
                    f.write(download.content)
            logger.success(f"File Created: {self.filename}")
        else:   logger.error(f"Download Failed: {self.filename}")

    def name(self):
        pass
    

        
        

#download all sermons from default page