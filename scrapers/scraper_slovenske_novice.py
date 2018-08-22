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
my_url = "https://www.slovenskenovice.si"

meseci = {'jan': '1.', 'feb': '2.', 'mar': '3.', 'apr': '4.', 'maj': '5.',
          'jun': '6.', 'jul': '7.', 'avg': '8.', 'sep': '9.',
          'okt': '10.', 'nov': '11.', 'dec': '12.'}

def makeHash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()
def initDriver():
    options = Options()
  #  options.set_headless(headless=True)
  #  options.add_argument("--window-size=1920x1080")
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
        piskotki = driver.find_element_by_xpath('//*[@id="t3-footer"]/div/div[6]/div/div/div/div[2]/span')
        if piskotki:
            piskotki.click()
            time.sleep(3)
    except:
        pass
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'article')))
        time.sleep(6)
        html = driver.execute_script("return document.documentElement.outerHTML")
        return html
    except:
        return NOT_FOUND
def getTitle(clanek):
    try:
        title = clanek.find('h2',class_='itemTitle').text
        title = title.strip()
        return title
    except:
        return NOT_FOUND
def mapMonth(mesec):
    for key in meseci.keys():
        if mesec.startswith(key):
            return meseci[key]
    return NOT_FOUND
def getDate(clanek):
    try:
        date = clanek.find('span', class_='itemDatePublished').text.strip()
        tmp = date.strip().split(" ")
        day = tmp[1]
        month = mapMonth(tmp[2])
        year = tmp[3]
        date = str(day)+str(month)+str(year)
        return uniformDateStr(date)
    except:
        return
def getContent(clanek):
    try:
        tmp = clanek.find("div", class_="itemFullText")
        for script in tmp(["script", "style"]):
            script.extract()
        text = tmp.get_text()
        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return str(text)
    except:
        return NOT_FOUND

def getClanek(driver, url):
    try:
        driver.get(url)
        try:
            WebDriverWait(driver, 6).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "itemFullText")))
        except:
            return NOT_FOUND
        html = driver.execute_script("return document.documentElement.outerHTML")
        openedClanek = soup(html, "html.parser")
        title = getTitle(openedClanek)
        date = getDate(openedClanek)
        content = getContent(openedClanek)
        source = str(url)
        hash = makeHash(title,date)
        if db.getByHash(hash):
            return NOT_FOUND
        novica = (str(datetime.date.today()),title,content,date,hash,my_url,source)
        return novica
    except:
        return NOT_FOUND
def getLinks(clanki):
    links = []
    for clanek in clanki:
        try:
            link = str(clanek.find("a")["href"])
            if link.startswith("http"):
                if  link not in links and link.startswith("https://www.slov"):
                    links.append(link)
            else:
                if link not in links:
                    links.append(my_url+str(link))
        except:
            pass
    return links


def main():
    driver = initDriver()
    html = fullyLoadPage(my_url, driver)
    i = 0
    while i < MAX_HTTP_RETRIES and html is NOT_FOUND:
        html = fullyLoadPage(my_url, driver)
        i += 1
    page_soup = soup(html, "html.parser")
    clanki = page_soup.findAll("div", class_="card_article")
    links = getLinks(clanki)
    NOVICE = []
    for link in links:
        novica = getClanek(driver,link)
        if novica is not NOT_FOUND:
            NOVICE.append(novica)
    db.insertMany(NOVICE)
    driver.close()
if __name__ == '__main__':
    main()