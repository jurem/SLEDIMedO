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
# parameter stDni=-356 nastavi datum od , na eno leto nazaj
my_url = "https://www.stat.si/StatWeb/ReleaseCal?StDni=-356"

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
def fullyLoadPage(my_url, driver):
    driver.get(my_url)
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="myForm"]/div[3]/div[1]/div/input')))
        driver.find_element_by_id('myForm').submit()
        time.sleep(3)
        piskotki = driver.find_element_by_xpath('/html/body/div[3]/div[2]/button')
        if piskotki:
            piskotki.click()
        html = driver.execute_script("return document.documentElement.outerHTML")
        return html
    except:
        return NOT_FOUND
def getLinks(page_soup):
    try:
        htmlLinks = page_soup.findAll("a", class_="search-item-link ng-binding ng-scope")
        links = []
        for link in htmlLinks:
            if str(link['href']).startswith('http'):
                pass
            else:
                links.append('https://www.stat.si/statweb/'+str(link['href']))
        return links
    except:
        return NOT_FOUND
def getDate(clanek):
    try:
        date = clanek.find('ul',class_='news-info-ul').find("li",recursive=False).text
        date = date.strip()
        return uniformDateStr(date)
    except:
        return NOT_FOUND
def getTitle(clanek):
    try:
        title = clanek.find('h1', class_='news-h1').text
        title = title.strip()
        return title
    except:
        return NOT_FOUND
def getHtmlSoup(driver):
    try:
        html = driver.execute_script("return document.documentElement.outerHTML")
        page_soup = soup(html, "html.parser")
        return page_soup
    except:
        pass
def getContent(clanek):
    try:
        content = clanek.find("p", class_="news-summary").text
        return str(content.strip())
    except:
        return NOT_FOUND
def getClanek(driver,link):
    try:
        driver.get(link)
        time.sleep(3)
        html = driver.execute_script("return document.documentElement.outerHTML")
        openedClanek = soup(html, "html.parser")
        date = getDate(openedClanek)
        title = getTitle(openedClanek)
        content = getContent(openedClanek)
        source = str(link)
        hash = makeHash(title, date)
        if db.getByHash(hash):
            return NOT_FOUND
        clanek = (str(datetime.date.today()),title,content,date,hash,my_url,source)
        return clanek
    except:
        return NOT_FOUND



def getClanki(page_soup,driver):
    try:
        htmlSoup = page_soup
        clanki = []
        ListOfLinks = []
        numberOfPages = driver.find_element_by_xpath('//a[@ng-click="selectPage(states.NumberOfPages)"]')
        currentPages = driver.find_elements_by_xpath('//a[@ng-click="selectPage(page)"]')
        for nxtPage in currentPages:
            links = getLinks(htmlSoup)
            if links is NOT_FOUND:
                return NOT_FOUND
            else:
                ListOfLinks.append(links)
            nxtPage.click()
            time.sleep(2)
            htmlSoup = getHtmlSoup(driver)
        nextPage = driver.find_elements_by_xpath('//a[@ng-click="selectPage(page)"]')
        nextPage =nextPage[-1]

        oldPage = nextPage
        while nextPage:
            nextPage.click()
            time.sleep(2)
            htmlSoup = getHtmlSoup(driver)
            links = getLinks(htmlSoup)
            if links is NOT_FOUND:
                return NOT_FOUND
            else:
                ListOfLinks.append(links)
            if nextPage is numberOfPages:
                break
            nextPage = driver.find_elements_by_xpath('//a[@ng-click="selectPage(page)"]')
            nextPage = nextPage[-1]
            if nextPage.text == oldPage.text:
                nextPage = numberOfPages
                continue
            oldPage = nextPage

        for links in ListOfLinks:
            for link in links:
                clanek = getClanek(driver,link)
                if clanek is not NOT_FOUND:
                    clanki.append(clanek)
                else:
                    return clanki
        return clanki
    except:
        return NOT_FOUND


def main():
    driver = initDriver()
    html = fullyLoadPage(my_url, driver)
    i = 0
    while i < MAX_HTTP_RETRIES and html is NOT_FOUND:
        html = fullyLoadPage(my_url, driver)
        i += 1
    page_soup = soup(html, "html.parser")
    clanki = getClanki(page_soup,driver)
    if clanki is not NOT_FOUND:
        db.insertMany(clanki)
    driver.close()
if __name__ == '__main__':
    main()