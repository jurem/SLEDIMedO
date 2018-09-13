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

NOT_FOUND = "not found"
MAX_HTTP_RETRIES = 10
my_url = "http://www.gis.si/sl/novice#older"

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
def fullyLoadPage(my_url,driver):
    driver.get(my_url)
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME,"default-link_wrap")))
        time.sleep(5)
        html = driver.execute_script("return document.documentElement.outerHTML")
        return html
    except:
        return NOT_FOUND
def getTitle(clanek):
    try:
        title = clanek.find("h2", class_="art-postheader").text
        return title.strip()
    except:
        return NOT_FOUND
def getLinks(page_soup):
    try:
        linksHtml = page_soup.findAll("a", class_="link_older")
        links = []
        for link in linksHtml:
            links.append(str(link['href']))
        return links
    except:
        return NOT_FOUND
def loadOldPage(url,driver):
    driver.get(url)
    try:
        time.sleep(2)
        html = driver.execute_script("return document.documentElement.outerHTML")
        return html
    except:
        return NOT_FOUND
def getVsebina(clanek):
    try:
        vsebina = clanek.find("div", class_="art-postcontent").text
        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in vsebina.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        vsebina = '\n'.join(chunk for chunk in chunks if chunk)
        return vsebina
    except:
        return NOT_FOUND
def getClanki(page_soup,driver):
    noviClankiHtml = page_soup.findAll("div", class_="art-post-inner art-article")
    clanki = []
    #pridobi nove clanke
    for clanek in noviClankiHtml:
        title = getTitle(clanek)
        date = getDate(clanek)
        content = getVsebina(clanek)
        source = my_url
        hash = makeHash(title, date)
        #ce je ze v bazi, se ustavi
        if db.getByHash(hash):
            return clanki
        else:
            clanki.append((str(datetime.date.today()),title,content,date,hash,my_url,source))
    #pridobi stare clanke
    oldClankiLinks = getLinks(page_soup)
    if oldClankiLinks is NOT_FOUND:
        pass
    else:
        for link in oldClankiLinks:
            html = loadOldPage(link,driver)
            clanek = soup(html, "html.parser")
            title = getTitle(clanek)
            content = getVsebina(clanek)
            source = link
            hash = makeHash(title, date)
            if db.getByHash(hash):
                return clanki
            else:
                clanki.append((str(datetime.date.today()), title, content, date, hash, my_url, source))
    return clanki
def getDate(clanek):
    try:
        date = clanek.find('span', class_ = 'h_date').text.strip()
        return uniformDateStr(date)
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
    db.insertMany(clanki)
    driver.close()
if __name__ == '__main__':
    main()