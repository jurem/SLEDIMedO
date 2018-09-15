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

#pridobi vse clanki na prvi strani in nato se iz arhiva

NOT_FOUND = "not found"
MAX_HTTP_RETRIES = 10
my_url = "http://www.arso.gov.si/"
arhiv_novic_url = "http://www.arso.gov.si/o%20agenciji/novice/arhiv.html"

meseci = {'jan': '1.', 'feb': '2.', 'mar': '3.', 'apr': '4.', 'maj': '5.',
          'jun': '6.', 'jul': '7.', 'avg': '8.', 'sep': '9.',
          'okt': '10.', 'nov': '11.', 'dec': '12.'}

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
def loadFirstPage(my_url, driver):
    driver.get(my_url)
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'vsebina')))
        time.sleep(3)
        html = driver.execute_script("return document.documentElement.outerHTML")
        return html
    except:
        return NOT_FOUND
def getTitle(clanek):
    try:
        title = clanek.find('h2').text
        title = title.strip()
        return title
    except:
        return NOT_FOUND
def getDate(clanek):
    try:
        date = clanek.find('p', class_="datum").text
        tmp = date.split(" ")
        day = tmp[0]
        month = mapMonth(tmp[1])
        year = tmp[2]
        date = str(day)+str(month)+str(year)
        return uniformDateStr(date)
    except:
        return NOT_FOUND

def mapMonth(mesec):
    for key in meseci.keys():
        if mesec.startswith(key):
            return meseci[key]
    print("Month not found in meseci")
def getContent(page_soup):
    try:
        content = cleanContent(page_soup.find('p', class_=None).text)
        return content
    except:
        return NOT_FOUND
def getNoviClanki(page_soup):
    try:
        noviClankiHtml = page_soup.findAll("div", class_="novica")
        date = ""
        title = ""
        content = ""
        source = ""
        hash = ""
        clanki = []
        for clanek in noviClankiHtml:
            date = getDate(clanek)
            try:
                title = str(clanek.find('h2').find('a').text).strip()
            except:
                title = NOT_FOUND
            try:
                content = getContent(clanek)
            except:
                content = NOT_FOUND

            hash = makeHash(title,date)
            if db.getByHash(hash):
                return NOT_FOUND

            try:
                source = my_url + str(clanek.find('h2').find('a')['href'])
            except:
                source = NOT_FOUND
            novica = (str(datetime.date.today()), title, content, date, hash, my_url, source)
            clanki.append(novica)
        if len(clanki) < 1:
            return NOT_FOUND
        else:
            return clanki
    except:
        return NOT_FOUND
def getStariClanki(driver):
    try:
        driver.get(arhiv_novic_url)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'vsebina')))
        time.sleep(3)
        html = driver.execute_script("return document.documentElement.outerHTML")
        page_soup = soup(html, "html.parser")
        clankihtml = page_soup.find_all('div', class_="novica")
        clanki = []
        for clanek in clankihtml:
            title = getTitle(clanek)
            date = getDate(clanek)
            hash = makeHash(title, date)
            if db.getByHash(hash):
                return NOT_FOUND
            content = getContent(clanek)
            source = arhiv_novic_url
            clanek = (str(datetime.date.today()), title, content, date, hash, my_url, source)
            clanki.append(clanek)
        if len(clanki) < 1:
            return NOT_FOUND
        else:
            return clanki
    except:
        return NOT_FOUND
def main():
    driver = initDriver()
    html = loadFirstPage(my_url, driver)
    i = 0
    while i < MAX_HTTP_RETRIES and html is NOT_FOUND:
        html = loadFirstPage(my_url, driver)
        i += 1
    page_soup = soup(html, "html.parser")
    noviClanki = getNoviClanki(page_soup)
    stariClanki = getStariClanki(driver)
    if noviClanki != NOT_FOUND and stariClanki != NOT_FOUND:
        vsiClanki = noviClanki + stariClanki
        db.insertMany(vsiClanki)
    else:
        print('Ni najdenih novih clankov')

    driver.close()
if __name__ == '__main__':
    main()