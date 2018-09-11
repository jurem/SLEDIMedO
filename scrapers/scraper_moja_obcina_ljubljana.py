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

'''
    Scraper iterira cez linke in iz vsake clanka vzame podatke(naslov,datum,itd..),
    trenutno narejen tako, da ko vidi ze obstojecega, prekine ( ker si sledijo datumsko in nima smisla naprej)
'''
NOT_FOUND = "not found"
MAX_HTTP_RETRIES = 10
my_url = "https://www.mojaobcina.si/ljubljana/novice/"

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
def getLinks(numberOfPages):
    links = []
    for i in range(1,numberOfPages+1):
        url = 'https://www.mojaobcina.si/ljubljana/novice/iskalnik/?page=' + str(i) + '&not-use=ASC'
        links.append(url)
    return links
def getSourceLinks(links,driver):
    try:
        sourceLinks = []
        i = 3
        for link in links:
            if i <= 0:
                break
            driver.get(link)
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="positioner"]/div[3]/div[1]/div[2]')))
            time.sleep(2)
            html = driver.execute_script("return document.documentElement.outerHTML")
            page_soup = soup(html, "html.parser")
            newsContainers = page_soup.find_all('div', class_='fl newsTitleContent')
            for news in newsContainers:
                sourceLink = news.find('a', class_='newsContent')['href']
                sourceLink = 'https://www.mojaobcina.si/' + sourceLink
                sourceLinks.append(sourceLink)
            i-=1
        return sourceLinks
    except:
        return NOT_FOUND
def getTitle(page_soup):
    try:
        title = page_soup.find('h1', class_='single-art-title').text
        return str(title)
    except:
        return NOT_FOUND
def getDate(page_soup):
    try:
        date = page_soup.find('div', class_='single-art-date fl').text
        date = date[0:10]
        return uniformDateStr(str(date))
    except:
        return NOT_FOUND
def cleanContent(text):
    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return str(text)
def getContent(page_soup):
    try:
        content = ''
        pTags = page_soup.find('div', class_='single-art-text').find_all('p')
        for p in pTags:
            content+=p.text+"\n"
        return cleanContent(content)
    except:
        return NOT_FOUND

def getClanek(link,driver):
    try:
        driver.get(link)
        time.sleep(2)
        html = driver.execute_script("return document.documentElement.outerHTML")
        page_soup = soup(html, "html.parser")
        title = getTitle(page_soup)
        date = getDate(page_soup)
        hash = makeHash(title, date)
        if db.getByHash(hash):
            return NOT_FOUND
        content = getContent(page_soup)
        source = link
        clanek = (str(datetime.date.today()),title,content,date,hash,my_url,source)
        return clanek
    except:
        return NOT_FOUND

def getClanki(driver):
    try:
        '''
            pridobi stevilo vseh strani, za potrebe iteriranja cez njih
        '''
        driver.get(my_url)
        WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="positioner"]/div[3]/div[1]/div[2]')))
        time.sleep(3)
        html = driver.execute_script("return document.documentElement.outerHTML")
        page_soup = soup(html, "html.parser")
        pages = page_soup.find_all('a',class_='paginatorAll paginatorUnactive')
        numberOfPages = int(pages[-1].text)
        links = getLinks(numberOfPages)
        sourceLinks = getSourceLinks(links,driver)
        clanki = []
        for sourceLink in sourceLinks:
            clanek = getClanek(sourceLink,driver)
            if clanek is NOT_FOUND:
               break
            else:
                clanki.append(clanek)
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