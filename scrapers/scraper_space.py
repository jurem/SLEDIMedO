from bs4 import BeautifulSoup as soup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from database.dbExecutor import dbExecutor as db
import time
import datetime
import hashlib

NOT_FOUND = "not found"
MAX_HTTP_RETRIES = 10
my_url = "http://www.space.si/novice/"

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
        title = page_soup.find('h2').find('a').text
        return str(title).strip()
    except:
        return NOT_FOUND
def getDate(page_soup):
    try:
        date = page_soup.find('time')['datetime']
        date = date.split("T")
        return str(date[0])
    except:
        return NOT_FOUND
def getContent(page_soup):
    try:
        pTags = page_soup.find_all('p', class_=None)
        content = ""
        for p in pTags:
            content += p.text + "\n"
        return cleanContent(content)
    except:
        return NOT_FOUND
def getSource(page_soup):
    try:
        source = page_soup.find('h2').find('a')['href']
        return str(source)
    except:
        return  NOT_FOUND
def loadPage(driver):
    driver.get(my_url)
    try:
        time.sleep(5)
        html = driver.execute_script("return document.documentElement.outerHTML")
        return html
    except:
        return NOT_FOUND
def getClanki(page_soup):
    try:
        clanki = page_soup.find_all('article', {"data-tpl":"content"})
        novice = []
        for clanek in clanki:
            title = getTitle(clanek)
            date = getDate(clanek)
            hash = makeHash(title,date)
            if db.getByHash(hash):
                break
            content = getContent(clanek)
            source = getSource(clanek)
            novica = (str(datetime.date.today()), title, content, date, hash, my_url, source)
            novice.append(novica)
        if len(novice) < 1:
            return NOT_FOUND
        else:
            return novice
    except:
        return NOT_FOUND
def main():
    driver = initDriver()
    html = loadPage(driver)
    i = 0
    while i < MAX_HTTP_RETRIES and html is NOT_FOUND:
        html = loadPage(driver)
        i += 1
    page_soup = soup(html, "html.parser")
    clanki = getClanki(page_soup)
    if clanki != NOT_FOUND:
        db.insertMany(clanki)
    else:
        print('Ni najdenih novih clankov')
    driver.close()

if __name__ == '__main__':
    main()