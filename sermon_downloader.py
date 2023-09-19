import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import re
from loguru import logger
import sys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SermonDownloader():
    def __init__(self, debug=False):
        self.driver = self.GTYDriver(debug)
        self.baseurl = self.driver.baseurl
        self.parser = self.GTYParser(self.driver.page_source)
        self.book_dict = self.return_book_dict()

    class GTYDriver(webdriver.Firefox):
        def __init__(self, debug=False):
            self.baseurl = "https://www.gty.org/library/resources/sermons-library/scripture"
            options = webdriver.FirefoxOptions()
            if debug == False:
                options.add_argument('--headless')
            super().__init__(options=options)
            logger.info("WebDriver started")
            self.implicitly_wait(10)
            logger.info("Waiting implicitly for driver to load all elements")
            self.get(self.baseurl)
            logger.info("Finished waiting")
    
    class GTYParser(BeautifulSoup):
        def __init__(self, source) -> None:
            super().__init__(source, features="html.parser")
            logger.info(f"Parser created")
            
    def current_page(self):
        self.parser = self.GTYParser(self.driver.page_source)
        sermons = self.parser.findAll(class_="gty-asset store-library sermon")
        pagination = self.parser.find("ul", class_="pagination")
        pg_n = pagination.find(class_="active").a.string
        last_chevron = pagination.find("i", class_="mdi-navigation-chevron-right").parent.parent
        return Page(sermons, pg_n, last_chevron)
    
    def return_book_dict(self):
        selector = self.driver.find_element(By.CLASS_NAME, "col.s8.l5").find_element(By.TAG_NAME, "select")
        options = selector.find_elements(By.TAG_NAME, "option")
        return {book.get_attribute("textContent"):book.get_attribute("value") for book in options}
    
    def download_book(self, name, pg=0):    
        # "https://www.gty.org/library/resources/sermons-library/scripture/1?book=1&chapter=0"
        bk_n = self.book_dict[name]
        ch_n = 0 #0 means all chapters
        pg_n = pg
        while True:
            self.driver.get(f"{self.baseurl}/{pg_n}?book={bk_n}&chapter={ch_n}")
            current = self.current_page()
            if current.is_last():
                break
    
    
    def download_all_books(self):
        pass
    
    def quit(self):
        self.GTYDriver.quit()
        logger.info("Driver Stopped")
        sys.exit()

class Book():
    def __init__(self, name):
        self.name = name

    def download(self):
        pass        

class Chapter():
    def __init__(self):
        pass
        
class Page():
    def __init__(self, content, page_num, chevron):
        self.content = content
        self.pn = page_num
        self.ch = chevron
        
    def download(self):
        with requests.Session() as session:     #a requests Session per page, useful to safely dispose resources
            for sermon in self.content:
                with Sermon(sermon) as s:
                    s.download(session)
    
    def is_last(self):
        return True if self.ch["class"][0] == "disabled" else False


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
        fn = f"{self.scripture}_{self.title}_{self.code}"
        fn = fn.translate({ord(c): "-" for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})
        return f'{fn}.mp3'
    
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