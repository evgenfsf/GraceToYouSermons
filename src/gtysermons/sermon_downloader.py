import requests
from selenium import webdriver
from bs4 import BeautifulSoup
from loguru import logger
import sys
import os
import time
from .constants import BIBLE_BOOKS_ORDER
from .file_helper import DateFileHelper, ScriptureFileHelper, TitleFileHelper
from abc import ABC, abstractmethod

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


class ContentNotFound(Exception):
    """Raised when sermon content element is missing and should skip section."""
    pass

class GTYDriver(webdriver.Firefox):
    def __init__(self, debug=False):
        options = webdriver.FirefoxOptions()
        if debug == False:
            options.add_argument('--headless')
        super().__init__(options=options)
        logger.info("WebDriver started")  

class GTYParser(BeautifulSoup):
    def __init__(self, source) -> None:
        super().__init__(source, features="html.parser")
        logger.info(f"Parser created")

class GroupSelector(ABC):
    def __init__(self, element):
        self.element = element
        self.option_dict = self.return_option_dict()
        self.select = Select(element)

    def return_option_dict(self):
        options = self.element.find_elements(By.TAG_NAME, "option")
        return {item.get_attribute("textContent"): item.get_attribute("value") for item in options}  
    
    def select_by_value(self, val):
        return self.select.select_by_value(val)

class BookSelector(GroupSelector):
    def __init__(self, driver):
        super().__init__(driver.find_element(By.ID, "book-filter"))
        self.option_dict = self.return_option_dict()

    def return_option_dict(self):  
        options = self.element.find_elements(By.TAG_NAME, "option")
        return {(book_name := book.get_attribute("textContent")): BIBLE_BOOKS_ORDER[book_name] for book in options}

class DateSelector(GroupSelector):
    def __init__(self, driver):
        super().__init__(driver.find_element(By.ID, "year-filter"))

class TitleSelector(GroupSelector):
    def __init__(self, driver):
        super().__init__(driver.find_element(By.ID, "alphabet-filter")) 

class SermonDownloaderFactory():
    def __init__(self, debug = False):
        self.debug = debug
        self.driver = GTYDriver(debug=debug)

    def get_downloader(self, type):
        if type == "date":
            init_item = "2024"
            url = "https://www.gty.org/sermons/archive?tab=date"
            self.driver.get(url)
            selector = DateSelector(self.driver)
            helper = DateFileHelper()
        if type == "book":
            init_item = "Genesis"
            url = "https://www.gty.org/sermons/archive?tab=scripture"
            self.driver.get(url)
            selector = BookSelector(self.driver)
            helper = ScriptureFileHelper()
        if type == "title":
            init_item = "A"
            url = "https://www.gty.org/sermons/archive?tab=title"
            self.driver.get(url)
            selector = TitleSelector(self.driver)
            helper = TitleFileHelper()
        
        return SermonDownloader(url=url, driver = self.driver, selector=selector, helper=helper, init_item=init_item, debug=self.debug)

class WaitUntilSermonContentChanges:
    def __init__(self, previous_html, item, updater):
        self.previous_html = previous_html
        self.previous_item = item
        self.updater = updater  # function to update the shared state

    def __call__(self, driver):
        try:
            element = driver.find_element(By.CLASS_NAME, "media-card-noimg--info")
            current = element.get_attribute("innerHTML")
            if self.previous_html is None:
                changed = current.strip() != ""
                logger.debug(f"[Initial Load] Content loaded: {'Yes' if changed else 'No'}")
            else:
                changed = current != self.previous_html
                logger.debug(f"[Content Change] Changed: {'Yes' if changed else 'No'}")
            #update shared state
            self.updater(current)
            return changed
        except NoSuchElementException:
            logger.warning(f"Item empty. Skipping {self.previous_item} due to missing content.")
            #raise a fatal exception to cancel the wait immediately
            raise ContentNotFound(f"No content for this section.")


class SermonDownloader():
    def __init__(self, url, driver, selector, helper, init_item, debug=False):
        self.driver = driver
        self.baseurl = url
        self.selector = selector
        self.fhelper = helper
        self.previous_html = None
        self.previous_item = init_item
        self._load_base_page()

    def _load_base_page(self):
        logger.info("Waiting for sermon content to load...")
        self.wait_for_sermon_content_change(self.previous_item)
        logger.info("Initial sermon content loaded.")

    def wait_for_sermon_content_change(self, item, timeout=15):
        logger.debug("Waiting for sermon content to change...")
        if self.previous_item == item:
            self.previous_html = None

        def update_shared(current_html):
            self.previous_html = current_html
            self.previous_item = item

        condition = WaitUntilSermonContentChanges(self.previous_html, item, update_shared)

        try:
            WebDriverWait(self.driver, timeout, ignored_exceptions=()).until(condition)
            logger.success("✅ Sermon content successfully changed.")
        except ContentNotFound:
            logger.debug("ContentNotFound triggered in wait_for_sermon_content_change")
            raise  # propagates up to download_section()
        except Exception as e:
            logger.error(f"❌ Timeout waiting for content change: {e}")
            raise


    
    def download_section(self, val): 
        self.fhelper.create_folder(val)   

        self.selector.select_by_value(val)
        try:
            self.wait_for_sermon_content_change(val)
        except ContentNotFound:
            logger.debug("Triggered ContentNotFound in download_section")
            return #warning logged in wait_for_sermon_content_change()
        #Get the entire list of sermons for the book
        sermon_container_list = self.driver.find_element(By.CLASS_NAME, "blogs-archive--wrapper").find_elements(By.CLASS_NAME, "blogs-archive--item")
        section = Section(sermon_container_list, val, self.driver, self.fhelper)
        section.download()

        #Remember to move back to the parent dir after book download is finished.
        os.chdir(os.pardir)
    
    def download_all(self):
        self.fhelper.create_root_folder()
        for section in self.selector.option_dict.keys():
            self.download_section(section)

        os.chdir(os.pardir)
    
    def quit(self):
        self.driver.quit()
        logger.info("Driver Stopped")
        sys.exit()


class Section():
    def __init__(self, sermon_list, name, driver, file_helper):
        self.driver = driver
        self.file_helper = file_helper
        self.sermon_list = sermon_list
        self.name = name

    def download(self):
        with requests.Session() as session:     #a requests Session per Book, useful to safely dispose resources
            for sermon in self.sermon_list:
                html = sermon.get_attribute("outerHTML")  # capture it right away
                parser = GTYParser(html)
                with Sermon(parser, self.driver, self.file_helper) as s:
                    s.download(session)  
        
class Sermon(): 
    def __init__(self, source, driver, file_helper):
        self.driver = driver
        self.file_helper = file_helper
        # SERMON NAME
        self.title = source.select_one("h2.media-card-noimg--title").text.strip()
        # DATE, PASSAGE, CODE
        info_items = source.select(".resources-bar--no-link")
        self.date = info_items[0].text.strip()
        self.scripture = info_items[1].text.strip()
        try:    
            self.code = info_items[2].text.strip()
        except IndexError:  #some audio files don't have a scripture reference (ex. interviews)
            self.scripture = ""
            self.code = info_items[1].text.strip()

        # SERMON PAGE LINK (relative)
        link_rel = source.select_one("a.media-card-noimg--link")["href"]
        self.link_full = f"https://www.gty.org{link_rel}"
        self.download_link = self.extract_mp3_url(self.link_full)

        self.filename = self.file_helper.filename_correct(self.scripture, self.title, self.date, self.code)
        logger.debug(f"Creating {self.filename}")

    ## __enter__ and __exit__ to use Sermon in a with statment
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def extract_mp3_url(self, sermon_url):
        #Save the original window
        original_window = self.driver.current_window_handle
        #Open a new tab
        self.driver.execute_script("window.open('');")
        time.sleep(1)  # small delay for tab to register
        self.driver.switch_to.window(self.driver.window_handles[-1])

        self.driver.get(sermon_url)
        soup = GTYParser(self.driver.page_source)
        #Find the <a> tag with a .mp3 link
        mp3_tag = soup.find("a", href=lambda x: x and ".mp3" in x)
        mp3_url = mp3_tag['href'] if mp3_tag else None

        #Close the tab and switch back
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


if __name__ == "__main__":
    factory = SermonDownloaderFactory(debug=True)
    sd = factory.get_downloader("title")
    sd.download_section("X")