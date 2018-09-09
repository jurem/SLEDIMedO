from bs4 import BeautifulSoup as soup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from scrapers.database.dbExecutor import dbExecutor as db
import time
import datetime
import hashlib

NOT_FOUND = "not found"
MAX_HTTP_RETRIES = 10
my_url = "http://www.uirs.si/Novice"

meseci = {'jan': '1.', 'feb': '2.', 'mar': '3.', 'apr': '4.', 'maj': '5.',
          'jun': '6.', 'jul': '7.', 'avg': '8.', 'sep': '9.',
          'okt': '10.', 'nov': '11.', 'dec': '12.'}

def mapMonth(mesec):
    for key in meseci.keys():
        if mesec.startswith(key):
            return meseci[key]
    print("Month not found in meseci")
def makeHash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()
def initDriver():
    options = Options()
    options.set_headless(headless=True)
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(options=options)
    return driver

# creates a uniform date string out of the input @dateStr and date format @inputDateFromat
# input format defaulted to: "%d.%m.%Y"
# output format: "%Y-%m-%d" - default database entry format
def uniformDateStr(dateStr, inputDateFromat=""):
    if inputDateFromat == "":
        inputDateFromat = "%d.%m.%Y"
    return datetime.datetime.strptime(dateStr, inputDateFromat).strftime("%Y-%m-%d")
def loadPage(my_url, driver):
    driver.get(my_url)
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, 'dnn_contentPane8')))
        time.sleep(3)
        html = driver.execute_script("return document.documentElement.outerHTML")
        return html
    except:
        return NOT_FOUND
def getTitle(clanek):
    try:
        title = clanek.find('header', class_='edn_articleTitle edsAccordion_title').find('h2').text
        title = title.strip()
        return title
    except:
        return NOT_FOUND

def getDate(clanek):
    try:
        date = clanek.find("time").text
        tmp = date.split(" ")
        day = tmp[0]
        month = mapMonth(tmp[1])
        year = tmp[2]
        date = str(day) + str(month) + str(year)
        return uniformDateStr(date)
    except:
        return NOT_FOUND
def getContent(clanek):
    try:
        content = clanek.find_all('p')
        string = ''
        for p in content:
            string += p.text + "\n"
        return string.strip()
    except:
        return NOT_FOUND
def getLinks(page_soup):
    try:
        aTags = page_soup.find_all('a', class_='page')
        links = []
        for a in aTags:
            links.append(str(a['href']))
        return links
    except:
        return NOT_FOUND

def getClanki(page_soup, driver):
    try:
        clanki = []
        links = getLinks(page_soup)
        links.append(str(my_url))
        stop = False
        for link in links:
            if stop:
                break
            html = loadPage(link,driver)
            i = 0
            while i < MAX_HTTP_RETRIES and html is NOT_FOUND:
                html = loadPage(my_url, driver)
                i += 1
            page_soup = soup(html, "html.parser")
            articles = page_soup.find_all('article')
            for article in articles:
                title = getTitle(article)
                date = getDate(article)
                hash = makeHash(title, date)
                if db.getByHash(hash):
                    stop = True
                    continue
                content = getContent(article)
                source = link
                clanek = (str(datetime.date.today()),title,content,date,hash,my_url,source)
                clanki.append(clanek)
        return clanki
    except:
        return NOT_FOUND
def main():
    driver = initDriver()
    html = loadPage(my_url, driver)
    i = 0
    while i < MAX_HTTP_RETRIES and html is NOT_FOUND:
        html = loadPage(my_url, driver)
        i += 1
    page_soup = soup(html, "html.parser")
    clanki = getClanki(page_soup, driver)
    if clanki is not NOT_FOUND:
        db.insertMany(clanki)
    driver.close()

if __name__ == '__main__':
    main()