from bs4 import BeautifulSoup as soup

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from database.dbExecutor import dbExecutor as db
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
NOT_FOUND = "not found"
MAX_HTTP_RETRIES = 10
NUMBER_OF_PAGES = 20
my_url = "https://www.dnevnik.si/lokalno/ljubljana"


def initDriver():
    options = Options()
    options.set_headless(headless=True)
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(options=options)
    return driver
def filterAds(clanki):
    for clanek in clanki:
        ad = clanek.find("div", class_="tl-ad")
        if ad:
            clanki.remove(clanek)
    return clanki

def getDate(clanek):
    try:
        date = clanek.find("span", class_="date").text
        if date:
            result =date[6:]+"-"+date[3:5]+"-"+date[0:2]
            return result
    except:
        return NOT_FOUND
def getTitle(clanek):
    try:
        title = clanek.find("h2").text
        if title:
            return title
    except:
        return NOT_FOUND
def getContent(clanek):
    try:
        Allcontent = clanek.find('div',{'class':['tl-article-text', 'tl-text']})
        content = Allcontent.find("article")
        if content is None :
            content = Allcontent.find("p")
        else:
            content = content.find("p")
        if content:
            return content.text
    except:
        return NOT_FOUND
def makeHash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()
def fullyLoadPage(my_url,driver):
    driver.get(my_url)
    #sprejmi piskotke ce so
    try:
        WebDriverWait(driver,6).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR,"button.button-load-more.wide.loading-hidden")))
    except TimeoutException as e:
        print("button for load more not found: exception->" + str(e))
    try:
        piskotki = driver.find_element_by_css_selector(".close-button");
        if piskotki:
            piskotki.click()
            time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    except:
        pass
    try:
        WebDriverWait(driver,6).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR,"button.button-load-more.wide.loading-hidden")))
    except TimeoutException as e:
        print("button for load more not found: exception->"+str(e))


    loadMoreButton = driver.find_element_by_css_selector("button.button-load-more.wide.loading-hidden")
    i = 0
    while loadMoreButton and NUMBER_OF_PAGES>= i:
        #scrollaj dol
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(6)
        #ce se vedno button prikazan, ga klikni da nalozi vec
        loadMoreButton = driver.find_element_by_css_selector("button.button-load-more.wide.loading-hidden")
        if loadMoreButton:
            try:
                loadMoreButton.click()
            except WebDriverException:
                print("loadMoreButton not clickable (possible unexpected ad), restarting job...")
                return NOT_FOUND

        try:
            WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.button-load-more.wide.loading-hidden")))
        except TimeoutException as e:
            print("button for load more not found: exception->" + str(e))
        i+=1
    time.sleep(5)
    html = driver.execute_script("return document.documentElement.outerHTML")
    return html

def getSource(clanek):
    try:
        viewMore = clanek.find("a", class_="view-more")
        if viewMore and viewMore.has_attr('href'):
            return "www.dnevnik.si"+str(viewMore["href"])
        else:
            link = clanek.find("span", {"tooltip" : "Kopiraj povezavo"})
            if link:
                return str(link["data-clipboard-text"])
            else:
                return my_url
    except:
        return NOT_FOUND
def main():
    driver = initDriver()
    html = fullyLoadPage(my_url,driver)
    i = 0
    while html is NOT_FOUND and MAX_HTTP_RETRIES >= i:
        html = fullyLoadPage(my_url,driver)
        i+=1

    page_soup = soup(html, "html.parser")
    #vzame vsak clanek
    try:
        clanki = page_soup.findAll("div", class_="tl-entry-flex")
        clanki = filterAds(clanki)
        novice = []
        count = 0
        for clanek in clanki:
            date = getDate(clanek)
            title = getTitle(clanek)
            hash = makeHash(title,date)
            if db.getByHash(hash):
                break
            content = getContent(clanek)
            source = getSource(clanek)
            count+=1
            data = (str(datetime.date.today()),title,content,date,hash,my_url,source)
            novice.append(data)
        if len(novice) > 0:
            db.insertMany(novice)
            print("Najdenih "+str(count)+" novih clankov")
        else:
            print('Ni najdenih novih clankov')
        driver.close()
    except:
        print("Error pri obdelavi clankov")
if __name__ == '__main__':
    main()
