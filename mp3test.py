import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import re
from loguru import logger

options = webdriver.FirefoxOptions()
options.add_argument('--headless')
driver = webdriver.Firefox(options=options)
driver.get("https://www.gty.org/library/resources/sermons-library")
soup = BeautifulSoup(driver.page_source, features="html.parser")
driver.quit()           #avoids resource waisting

download_server = "https://cdn.gty.org/sermons/High/"

sermon_box = soup.find(class_='gty-asset store-library sermon')
title = sermon_box.find(class_="title").span.string
scripture = sermon_box.find(class_="scripture").span.string
code = sermon_box.find(class_="code").span.string

filename = f'{scripture}'
link = f'{download_server}{code}.mp3'

session = requests.Session()
sermon = session.get(link)

if sermon.status_code == 200:                           #only save file if file properly received
        logger.success(f"Download Succeeded: {filename}")
        with open(f'{code}.mp3', 'wb') as f:            #open in binary mode to avoid errors
                f.write(sermon.content)
else:   logger.error(f"Download Failed: {filename}")


#TODO stream=True ?