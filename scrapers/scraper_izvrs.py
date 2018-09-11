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
my_url = "http://www.izvrs.si/novice/"

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
def cleanContent(text):
    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return str(text)
def getTitle(page_soup):
    try:
        title = page_soup.find('h3', class_='entry-title').find('a').text
        return str(title)
    except:
        return NOT_FOUND
def getDate(page_soup):
    try:
        date = page_soup.find('time', class_='entry-date updated')['datetime']
        date = date.split("T")
        return str(date[0])
    except:
        return NOT_FOUND
def getContent(page_soup):
    try:
        content = page_soup.find('p').text
        return cleanContent(content)
    except:
        return NOT_FOUND
def getSource(page_soup):
    try:
        source = page_soup.find('h3', class_='entry-title').find('a')['href']
        return str(source)
    except:
        return NOT_FOUND
def getClanek(clanekHtml):
    try:
        title = getTitle(clanekHtml)
        date = getDate(clanekHtml)
        hash = makeHash(title, date)
        if db.getByHash(hash):
            return NOT_FOUND
        content = getContent(clanekHtml)
        source = getSource(clanekHtml)
        clanek = (str(datetime.date.today()),title,content,date,hash,my_url,source)
        return clanek
    except:
        return NOT_FOUND
def loadNextPage(page_soup,driver):
    try:
        nextPageLink = page_soup.find('a',class_='nav-next')['href']
        driver.get(nextPageLink)
        WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'nav-next')))
        time.sleep(2)
        html = driver.execute_script("return document.documentElement.outerHTML")
        page_soup = soup(html, "html.parser")
        return page_soup
    except:
        return False
def getClanki(driver):
    try:
        driver.get(my_url)
        WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'nav-next')))
        time.sleep(2)
        piskotki = driver.find_element_by_xpath('//*[@id="cc-approve-button-thissite"]')
        if piskotki:
            piskotki.click()
        html = driver.execute_script("return document.documentElement.outerHTML")
        page_soup = soup(html, "html.parser")
        clanki = []
        stop = False
        while page_soup:
            if stop:
                break
            clankiHtml = page_soup.find_all('div', class_='blog-content wf-td')
            for clanekHtml in clankiHtml:
                clanek = getClanek(clanekHtml)
                if clanek is NOT_FOUND:
                    stop = True
                    break
                else:
                    clanki.append(clanek)
            page_soup = loadNextPage(page_soup,driver)
        if len(clanki) < 1:
            return NOT_FOUND
        else:
            return clanki
    except:
        return NOT_FOUND

def main():
    driver = initDriver()
    clanki = getClanki(driver)
    if clanki != NOT_FOUND:
        db.insertMany(clanki)
    else:
        print('Ni najdenih novih clankov')
    driver.close()

if __name__ == '__main__':
    main()