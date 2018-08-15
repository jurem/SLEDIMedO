from bs4 import BeautifulSoup as soup
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from scrapers.database.dbExecutor import dbExecutor as db
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import time
import datetime
import hashlib

'''
    Created by Robi
'''

'''
    potrebuje chromedriver.exe v isti mapi, ker se vsebina nalaga z JS
'''

MAX_HTTP_RETRIES = 10
#TODO: ker je infinity scroll, zaenkrat limit 10, da ne crasha chrome, moramo predebatirat
NUMBER_OF_PAGES = 10

my_url = "https://www.dnevnik.si/lokalno/ljubljana"

def filterAds(clanki):
    for clanek in clanki:
        ad = clanek.find("div", class_="tl-ad")
        if ad:
            clanki.remove(clanek)
    return clanki

def getDate(clanek):
    date = clanek.find("span", class_="date").text
    if date:
        result =date[6:]+"-"+date[3:5]+"-"+date[0:2]
        return result
    print("date not found")
    return "date not found"
def getTitle(clanek):
    title = clanek.find("h2").text
    if title:
        return title
    print("title not found")
    return "title not found"
def getContent(clanek):
    Allcontent = clanek.find('div',{'class':['tl-article-text', 'tl-text']})
    content = Allcontent.find("article")
    if content is None :
        content = Allcontent.find("p")
    else:
        content = content.find("p")
    if content:
        return content.text
    print("content not found")
    return "content not found"
def makeHash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()
def fullyLoadPage(my_url):
    options = Options()
    options.set_headless(headless=True)
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(options=options)
    driver.get(my_url)
    #sprejmi piskotke ce so
    try:
        WebDriverWait(driver,8).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR,"button.button-load-more.wide.loading-hidden")))
    except TimeoutException as e:
        print("button for load more not found: exception->" + str(e))
 #   wait = WebDriverWait(driver, 10)
 #   element = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="test"]')))
 #   element.click()
    piskotki = driver.find_element_by_css_selector(".close-button");
    if piskotki:
        piskotki.click()
        time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    try:
        WebDriverWait(driver,10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR,"button.button-load-more.wide.loading-hidden")))
    except TimeoutException as e:
        print("button for load more not found: exception->"+str(e))


    loadMoreButton = driver.find_element_by_css_selector("button.button-load-more.wide.loading-hidden")
    i = 0
    while loadMoreButton and NUMBER_OF_PAGES>= i:
        #scrollaj dol
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(8)
        #ce se vedno button prikazan, ga klikni da nalozi vec
        loadMoreButton = driver.find_element_by_css_selector("button.button-load-more.wide.loading-hidden")
        if loadMoreButton:
            try:
                loadMoreButton.click()
            except WebDriverException:
                print("loadMoreButton not clickable (possible unexpected ad), restarting job...")
                return "RESTART"

        try:
            WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.button-load-more.wide.loading-hidden")))
        except TimeoutException as e:
            print("button for load more not found: exception->" + str(e))
        i+=1
    time.sleep(8)
    html = driver.execute_script("return document.documentElement.outerHTML")
    driver.close()
    return html

def getSource(clanek):
    viewMore = clanek.find("a", class_="view-more")
    if viewMore and viewMore.has_attr('href'):
        return "www.dnevnik.si"+str(viewMore["href"])
    else:
        link = clanek.find("span", {"tooltip" : "Kopiraj povezavo"})
        if link:
            return str(link["data-clipboard-text"])
        else:
            return my_url
def main():
    with requests.Session() as s:
        html = fullyLoadPage(my_url)
        while html is "RESTART":
            html = fullyLoadPage(my_url)

        page_soup = soup(html, "html.parser")
        #vzame vsak clanek
        clanki = page_soup.findAll("div", class_="tl-entry-flex")
        clanki = filterAds(clanki)

        titles = []
        dates = []
        links = []
        hashes = []
        count = 0
        for clanek in clanki:
            date = getDate(clanek)
            title = getTitle(clanek)
            content = getContent(clanek)
            hash = makeHash(title,date)
            source = getSource(clanek)
            # print(date)
            # print(title)
            # print("Vsebina:"+str(content))
            # print("Hash:"+str(hash))
            # print("Source"+str(source))
            # print("------------------")
            count+=1
            # ce clanek ze v bazi, ga preskoci
            if db.getByHash(hash):
                continue
            else:
                data = (str(datetime.date.today()),title,content,date,hash,my_url,source)
                db.insertOne(data)
     #   print(count)
if __name__ == '__main__':
    main()
