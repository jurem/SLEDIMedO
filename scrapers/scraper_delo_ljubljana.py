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

'''
    Created by Robi
'''

'''
    potrebuje chromedriver.exe v isti mapi, ker se vsebina nalaga z JS

'''

NOT_FOUND = "not found"
MAX_HTTP_RETRIES = 10
NUMBER_OF_LOAD_MORE = 40
my_url = "https://www.delo.si/novice/ljubljana"

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
def fullyLoadPage(my_url,driver):
    driver.get(my_url)
    try:
        piskotki = driver.find_element_by_xpath('//*[@id="t3-footer"]/div/div[2]/div/div/div/div[2]/span')
        if piskotki:
            piskotki.click()
            time.sleep(3)
    except:
        pass
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="ocmContainer"]/div[9]/div/form/button')))
        loadMoreButton = driver.find_element_by_xpath('//*[@id="ocmContainer"]/div[9]/div/form/button')
        i = 0
        while loadMoreButton and NUMBER_OF_LOAD_MORE > i:
            loadMoreButton.click()
            i+=1
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="ocmContainer"]/div[9]/div/form/button')))
    except:
        print("loadMoreButton not found")
    try:
        html = driver.find_element_by_class_name("articleListWrapper").get_attribute('outerHTML')
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
    print("Month not found in meseci")
def getDate(clanek):
    try:
        date = clanek.find("div", class_="date").text
        tmp = date.split(" ")
        day = tmp[0]
        month = mapMonth(tmp[1])
        year = tmp[2]
        date = str(day)+str(month)+str(year)
        return uniformDateStr(date)
    except:
        return NOT_FOUND
def getContent(clanek):
    try:
        pTags = clanek.find("div", class_="itemFullText").findAll("p", class_=None)
        string = clanek.find("div", class_="itemFullText").text
        for p in pTags:
            string+=p.text+"\n"
        return string.strip()
    except:
        return NOT_FOUND
def getClanek(driver,clanek):
    try:
        link = clanek.find("a")["href"]
        url = my_url+str(link)
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
        hash = makeHash(title, date)
        if db.getByHash(hash):
            return NOT_FOUND
        source = str(url)
        novica = (str(datetime.date.today()),title,content,date,hash,my_url,source)
        return novica
    except:
        return NOT_FOUND



def main():
    driver = initDriver()
    html = fullyLoadPage(my_url,driver)
    page_soup = soup(html,"html.parser")
    clanki = page_soup.findAll("article")
    NOVICE = []
    for clanek in clanki:
        novica = getClanek(driver,clanek)
        if novica is not NOT_FOUND:
            NOVICE.append(novica)
    db.insertMany(NOVICE)
    driver.close()

if __name__ == '__main__':
    main()
