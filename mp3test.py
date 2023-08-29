import requests
from selenium import webdriver
from bs4 import BeautifulSoup

options = webdriver.FirefoxOptions()
options.add_argument('--headless')
driver = webdriver.Firefox(options=options)
driver.get("https://www.gty.org/library/resources/sermons-library")
soup = BeautifulSoup(driver.page_source, features="html.parser")
driver.quit()

download_server = "https://cdn.gty.org/sermons/High/"

sermon_box = soup.find(class_='gty-asset store-library sermon')
title = sermon_box.find(class_="title").span.string
scripture = sermon_box.find(class_="scripture").span.string
code = sermon_box.find(class_="code").span.string

filename = f'{scripture}'
link = f'{download_server}{code}.mp3'

sermon = requests.get(link)

with open(f'{code}.mp3', 'wb') as f:
        f.write(sermon.content)

pass

#TODO requests.Session()
#TODO stream=True