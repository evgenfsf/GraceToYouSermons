import requests
from selenium import webdriver
from bs4 import BeautifulSoup
from loguru import logger
import sys
import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC

class GTYDriver(webdriver.Firefox):
    def __init__(self, debug=False):
        self.baseurl = "https://www.gty.org/sermons/archive?tab=scripture"
        self.previous_html = None
        self.previous_book = "Genesis"
        options = webdriver.FirefoxOptions()
        if debug == False:
            options.add_argument('--headless')
        super().__init__(options=options)
        logger.info("WebDriver started")
        self._load_base_page()

    def _load_base_page(self):
        logger.info(f"Navigating to {self.baseurl}")
        self.get(self.baseurl)
        logger.info("Waiting for sermon content to load...")
        self.wait_for_sermon_content_change(self.previous_book)
        logger.info("Initial sermon content loaded.")

    def wait_for_sermon_content_change(self, book, timeout=10):
        logger.debug("Waiting for sermon content to change...")
        if self.previous_book == book:
            self.previous_html = None
        def has_changed(d):
            try:
                current = d.find_element(By.CLASS_NAME, "media-card-noimg--info").get_attribute("innerHTML")
                
                if self.previous_html is None:
                    changed = current.strip() != ""
                    logger.debug(f"[Initial Load] Content loaded: {'Yes' if changed else 'No'}")
                else:
                    changed = current != self.previous_html
                    logger.debug(f"[Content Change] Changed: {'Yes' if changed else 'No'}")
                self.previous_html = current
                self.previous_book = book
                return changed
            except Exception as e:
                logger.error(f"Error while checking content change: {e}")
                return False

        try:
            WebDriverWait(self, timeout).until(has_changed)
            logger.success("✅ Sermon content successfully changed.")
        except Exception as e:
            logger.error(f"❌ Timeout waiting for content change: {e}")    

class GTYParser(BeautifulSoup):
    def __init__(self, source) -> None:
        super().__init__(source, features="html.parser")
        logger.info(f"Parser created")

class BookSelector():
    def __init__(self, element):
        self.element = element
        self.select = Select(element)

class SermonDownloader():
    def __init__(self, debug=False):
        self.driver = GTYDriver(debug)
        self.baseurl = self.driver.baseurl
        self.book_selector = BookSelector(self.driver.find_element(By.ID, "book-filter"))
        self.previous_html = None
        self.book_dict = self.return_book_dict()


    # def current_page(self):
    #     self.parser = self.GTYParser(self.driver.page_source)
    #     sermons = self.parser.findAll(class_="gty-asset store-library sermon")
    #     pagination_source = self.driver.find_element(By.CLASS_NAME, "col.s12.m7").find_element(By.CLASS_NAME, "pagination")
    #     pagination = self.GTYParser(pagination_source.get_attribute("outerHTML"))
    #     try:
    #         pg_n = pagination.find(class_="active").a.string
    #         last_chevron = pagination.find("i", class_="mdi-navigation-chevron-right").parent.parent
    #     except AttributeError:  #just one page
    #         pg_n = 1
    #         last_chevron = True
    #     return Page(sermons, int(pg_n), last_chevron)
    
    def return_book_dict(self):  
        options = self.book_selector.element.find_elements(By.TAG_NAME, "option")
        return {book.get_attribute("textContent"): i for i, book in enumerate(options)}
    
    def download_book(self, name):    
        bk_n = self.book_dict[name]
        logger.info(f"Creating folder: {bk_n:02}_{name}")
        os.makedirs(f"{bk_n:02}_{name}", exist_ok=True) #two digits always
        os.chdir(f"{bk_n:02}_{name}")

        self.book_selector.select.select_by_value(name)
        self.driver.wait_for_sermon_content_change(name)

        #Get the entire list of sermons for the book
        sermon_container__list = self.driver.find_element(By.CLASS_NAME, "blogs-archive--wrapper").find_elements(By.CLASS_NAME, "blogs-archive--item")
        book = Book(sermon_container__list, name, self.driver)
        book.download()

        #Remember to move back to the parent dir after book download is finished.
        os.chdir(os.pardir)
    
    
    def download_all_books(self):
        dirname = "GraceToYouSermons"  #for now
        os.makedirs(dirname, exist_ok=True)
        os.chdir(dirname)
        for book in self.book_dict.keys():
            self.download_book(book)
        os.chdir(os.pardir)
        
    
    def quit(self):
        self.driver.quit()
        logger.info("Driver Stopped")
        sys.exit()

class Book():
    def __init__(self, sermon_list, name, driver):
        self.driver = driver
        self.sermon_list = sermon_list
        self.name = name

    def download(self):
        with requests.Session() as session:     #a requests Session per Book, useful to safely dispose resources
            for sermon in self.sermon_list:
                html = sermon.get_attribute("outerHTML")  # capture it right away
                parser = GTYParser(html)
                with Sermon(parser, self.driver) as s:
                    s.download(session)  
        
class Sermon(): 
    def __init__(self, source, driver):
        self.driver = driver
        # SERMON NAME
        self.title = source.select_one("h2.media-card-noimg--title").text.strip()
        # DATE, PASSAGE, CODE
        info_items = source.select(".resources-bar--no-link")
        self.date = info_items[0].text.strip()
        self.scripture = info_items[1].text.strip()
        self.code = info_items[2].text.strip()
        # SERMON PAGE LINK (relative)
        link_rel = source.select_one("a.media-card-noimg--link")["href"]
        self.link_full = f"https://www.gty.org{link_rel}"
        self.download_link = self.extract_mp3_url(self.link_full)

        self.filename = self.filename_correct()
        logger.debug(f"Creating {self.filename}")

    ## __enter__ and __exit__ to use Sermon in a with statment
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def filename_correct(self):
        fn = f"{self.scripture}_{self.title}_{self.date}_{self.code}"
        fn = fn.translate({ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\\|`~-=_+\""})
        return f'{fn}.mp3'
    
    def extract_mp3_url(self, sermon_url):
        # 1. Save the original window
        original_window = self.driver.current_window_handle

        # 2. Open a new tab
        self.driver.execute_script("window.open('');")
        time.sleep(1)  # small delay for tab to register

        # 3. Switch to the new tab (last one)
        self.driver.switch_to.window(self.driver.window_handles[-1])

        # 4. Load the sermon page
        self.driver.get(sermon_url)

        # 5. Extract with BeautifulSoup
        soup = GTYParser(self.driver.page_source)
        # Find the <a> tag with both the MP3 label and a .mp3 link
        mp3_tag = soup.find("a", href=lambda x: x and ".mp3" in x)
        mp3_url = mp3_tag['href'] if mp3_tag else None

        # 6. Close the tab and switch back
        self.driver.close()
        self.driver.switch_to.window(original_window)

        return mp3_url

    def download(self, session):
        if os.path.exists(self.filename):
            logger.info(f"File already exists, skipping: {self.filename}")
            return

        logger.info(f"Downloading {self.download_link}")
        for _ in range(3):
            try:
                download = session.get(self.download_link)
                if download.status_code == 200:
                    logger.success(f"Download Succeeded: {self.download_link}")
                    with open(self.filename, 'wb') as f:            #open in binary mode to avoid errors
                        f.write(download.content)
                        logger.success(f"File Created: {self.filename}")
                    break
                else:   logger.error(f"Download Failed: {self.filename}")
                    
            except Exception as e:
                logger.warning(f"Retrying due to error: {e}")  
