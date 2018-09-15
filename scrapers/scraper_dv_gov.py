from bs4 import BeautifulSoup as soup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from database.dbExecutor import dbExecutor as db
import time
import datetime
import hashlib

#pridobi vse clanke/novice, ce vidi ze obstojecega v bazi, prekine, saj si datumsko sledijo

NOT_FOUND = "not found"
MAX_HTTP_RETRIES = 10
my_url = "http://www.dv.gov.si/si/medijsko_sredisce/sporocila_za_javnost/"

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
        title = page_soup.find('h4').find('a').text
        return str(title).strip()
    except:
        return NOT_FOUND
def getDate(page_soup):
    try:
        date = page_soup.find('time')['datetime']
        date = str(date).replace(" ","")
        return uniformDateStr(date)
    except:
        return NOT_FOUND
def getContent(page_soup):
    try:
        content = page_soup.find('div', {"itemprop":"description"}).text
        return cleanContent(content)
    except:
        return NOT_FOUND
def getSource(page_soup):
    try:
        source = page_soup.find('h4').find('a')['href']
        return str(source)
    except:
        return  NOT_FOUND
def getClanek(clanekHtml):
    try:
        title = getTitle(clanekHtml)
        date = getDate(clanekHtml)
        hash = makeHash(title,date)
        if db.getByHash(hash):
            return NOT_FOUND
        content = getContent(clanekHtml)
        source = getSource(clanekHtml)
        print(title)
        print(date)
        print('---------------------')
        clanek = (str(datetime.date.today()),title,content,date,hash,my_url,source)
        return clanek
    except:
        return NOT_FOUND
def loadNextPage(page_soup,driver):
    try:
        nextPageLink = page_soup.find('li',class_='last next').find('a')['href']
        driver.get(nextPageLink)
        WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.CLASS_NAME, 'news')))
        time.sleep(2)
        html = driver.execute_script("return document.documentElement.outerHTML")
        page_soup = soup(html, "html.parser")
        return page_soup
    except:
        return False
def getClanki(driver):
    try:
        driver.get(my_url)
        WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.CLASS_NAME, 'news')))
        time.sleep(2)
        html = driver.execute_script("return document.documentElement.outerHTML")
        page_soup = soup(html, "html.parser")
        clanki = []
        stop = False
        while page_soup:
            if stop:
                break
            clankiHtml = page_soup.find_all('td', class_='news-list-text')
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
