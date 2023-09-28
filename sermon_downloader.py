import requests
from selenium import webdriver
from bs4 import BeautifulSoup
from bs4.element import Tag
from loguru import logger
import sys
import os

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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
        pagination_source = self.driver.find_element(By.CLASS_NAME, "col.s12.m7").find_element(By.CLASS_NAME, "pagination")
        pagination = self.GTYParser(pagination_source.get_attribute("outerHTML"))
        try:
            pg_n = pagination.find(class_="active").a.string
            last_chevron = pagination.find("i", class_="mdi-navigation-chevron-right").parent.parent
        except AttributeError:  #just one page
            pg_n = 1
            last_chevron = True
        return Page(sermons, int(pg_n), last_chevron)
    
    def return_book_dict(self):
        selector = self.driver.find_element(By.CLASS_NAME, "col.s8.l5").find_element(By.TAG_NAME, "select")
        options = selector.find_elements(By.TAG_NAME, "option")
        return {book.get_attribute("textContent"):book.get_attribute("value") for book in options}
    
    def download_book(self, name, pg=1):    
        # "https://www.gty.org/library/resources/sermons-library/scripture/1?book=1&chapter=0"
        bk_n = self.book_dict[name]
        ch_n = 0 #0 means all chapters
        pg_n = pg
        logger.info(f"Creating folder: {bk_n}_{name}")
        os.mkdir(f"{bk_n}_{name}")
        os.chdir(f"{bk_n}_{name}")
        while True:
            logger.info(f"Page {pg_n}")
            full_url=f"{self.baseurl}/{pg_n}?book={bk_n}&chapter={ch_n}"
            logger.info(f"Driver get: {full_url}")
            while True:
                try:
                    self.driver.get(full_url)
                    condition = WebDriverWait(self.driver, 10).until(EC.url_to_be(full_url))
                    if condition:
                        break
                except TimeoutException:
                    logger.info("Timeout, retrying...")
                    continue
                    
            current = self.current_page()
            current.download()
            if current.is_last():
                logger.info("Reached last page.")
                break
            pg_n += 1
        os.chdir(os.pardir)
    
    
    def download_all_books(self):
        dirname = "GraceToYouSermons"  #for now
        os.mkdir(dirname)
        os.chdir(dirname)
        for book in self.book_dict.keys():
            self.download_book(book)
        os.chdir(os.pardir)
        self.quit()
        
    
    def quit(self):
        self.driver.quit()
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
        if type(self.ch) == Tag:
            return True if self.ch["class"][0] == "disabled" else False
        else: 
            return self.ch


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
        fn = fn.translate({ord(c): "-" for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+\""})
        return f'{fn}.mp3'
    
    def download(self, session):
        link = f"{self.download_server}{self.code}.mp3"
        logger.info(f"Downloading {link}")
        download = session.get(link)
        if download.status_code == 200:
            logger.success(f"Download Succeeded: {link}")
            with open(self.filename, 'wb') as f:            #open in binary mode to avoid errors
                    f.write(download.content)
            logger.success(f"File Created: {self.filename}")
        else:   logger.error(f"Download Failed: {self.filename}")

    def name(self):
        pass
    