from bs4 import BeautifulSoup as soup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from scrapers.database.dbExecutor import dbExecutor as db
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
STEVILO_VSEH_STRANI = None
my_url = "https://www.mladina.si"

def initDriver():
    options = Options()
    options.set_headless(headless=True)
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(options=options)
    return driver
def loadPage(my_url,driver,pageNumber):
    url = str(my_url)+"?p="+str(pageNumber)
    driver.get(str(url))
    #sprejmi piskotke ce so
    try:
        piskotki = driver.find_element_by_xpath("/html/body/div[6]/div/form/p[2]/input[3]")
        if piskotki:
            piskotki.click()
            time.sleep(3)
    except:
        pass
    try:
        WebDriverWait(driver,8).until(
            EC.presence_of_element_located((By.CLASS_NAME,"articles")))
        time.sleep(4)
    except TimeoutException as e:
        print("Articles not loaded")
        return NOT_FOUND
    html = driver.execute_script("return document.documentElement.outerHTML")
    return html

def getTitle(clanek):
    title = clanek.find("p", class_="h2")
    if title:
        return title.text
    return NOT_FOUND
def getContent(clanek):
    content = clanek.find("p", class_=None, recursive=False)
    if content:
        return content.text
    return NOT_FOUND
def getDate(clanek):
    try:
        date = clanek.find("div", class_="info-box").findAll("p")[1]
        date = date.text.replace(" ","")
        return uniformDateStr(date[0:9])
    except:
        return NOT_FOUND
# creates a uniform date string out of the input @dateStr and date format @inputDateFromat
# input format defaulted to: "%d.%m.%Y"
# output format: "%Y-%m-%d" - default database entry format
def uniformDateStr(dateStr, inputDateFromat=""):
    if inputDateFromat == "":
        inputDateFromat = "%d.%m.%Y"
    return datetime.datetime.strptime(dateStr, inputDateFromat).strftime("%Y-%m-%d")
def getSteviloVsehStrani(my_url,driver):
    driver.get(my_url)
    try:
        WebDriverWait(driver,8).until(
            EC.visibility_of_element_located((By.CLASS_NAME,"articles")))
        html = driver.execute_script("return document.documentElement.outerHTML")
        page_soup = soup(html,"html.parser")
        strani = page_soup.find("ul", class_="pages").findAll("li")
        STEVILO_VSEH_STRANI = strani[len(strani)-1].find("a").text
        return int(STEVILO_VSEH_STRANI)
    except TimeoutException as e:
        print("Number of all pages not found")
        return NOT_FOUND
def getSource(clanek):
    try:
        link = clanek.find("a", class_="more")["href"]
        source = my_url+str(link)
        return source
    except:
        return NOT_FOUND
def makeHash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()
def main():
    with requests.Session() as s:
        driver = initDriver()
        html = loadPage(my_url,driver,1)
        i = 0
        #ce se clanki niso uspesno nalozili, probaj max 10krat
        while i < MAX_HTTP_RETRIES and html is NOT_FOUND:
            html = loadPage(my_url,driver,1)
            i+=1

        NOVICE = []
        STEVILO_VSEH_STRANI = getSteviloVsehStrani(my_url,driver)
        '''
            Trenutno gre skozi vse članke, če pride do že obstoječega, se ustavi
            
            Za testiranje najboljše, da zamenjaš STEVILO_VSEH_STRANI z neko malo cifro,
            da ne naloada vseh clankov, ker jih je ogromno
        '''
        for x in range(1,3):
            i = 0
            html = loadPage(my_url, driver, x)
            while i < MAX_HTTP_RETRIES and html is NOT_FOUND:
                html = loadPage(my_url,driver,x)
                i+=1
            page_soup = soup(html, "html.parser")
            clanki = page_soup.find("ul", class_="articles").findAll("li", class_="item bigger")
            count = 0
            # print("PAGE "+str(x)+"**************************")
            done = False
            for clanek in clanki:
                title = getTitle(clanek)
                content = getContent(clanek)
                date = getDate(clanek)
                source = getSource(clanek)
                hash = makeHash(title, date)
                if content is NOT_FOUND and title is NOT_FOUND:
                    continue
                if db.getByHash(hash):
                    done = True
                    break
                else:
                    data = (str(datetime.date.today()), title, content, date, hash, my_url, source)
                    NOVICE.append(data)
                    # print("Datum: "+str(date))
                    # print("Naslov: "+str(title))
                    # print("Vsebina: "+str(content))
                    # print("Source: "+str(source))
                    # print("Hash: "+str(hash))
                    # print("-------------------------------------------------------")
                    count += 1
            if done:
                break
        db.insertMany(NOVICE)
        # print(count)
        # print("STEVILO_VSEH_STRANI: "+str(STEVILO_VSEH_STRANI))
        driver.close()
if __name__ == '__main__':
    main()