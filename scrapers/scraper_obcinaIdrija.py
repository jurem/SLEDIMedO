from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
import requests
import hashlib
import time
from database.dbExecutor import dbExecutor
import sys

'''
    ta scraper potrebuje v isti mapi se file (linux):clear
        - chromedriver (za uporabo selenium knjiznjice) 

    idrija.si clanke loada skozi javascript, zato je potrebna knjiznjica selenium

    OPOZORILO!! nekateri clanki nimajo datuma zraven - so zgolj obvestila

    created by markzakelj
'''

SOURCE = 'OBCINA-IDRIJA'
firstRunBool = False

base_url = 'https://www.idrija.si'

def getArticlesOn_n_pages(num_pages_to_check):
    '''
        clanki se pojavijo na strani sele, ko se zloada javascript,
        zato se uporabi selenium knjiznjica
    '''
    options = Options()
    options.set_headless(headless=True)
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(options=options) #ta vrstica klice napako, ce se v isti mapi ne nahaja file 'chromedriver'
    driver.get('https://www.idrija.si/objave/8')
    timeout = 8
    try:
        element_present = EC.presence_of_element_located((By.CSS_SELECTOR, 'div.postsgroup'))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        print ("Timed out waiting for page to load")


    articles = []

    for i in range(1, num_pages_to_check+1):
        driver.find_element_by_link_text(str(i)).click()
        time.sleep(3)    #pocakaj 3 sekunde, da se zloada stran
        soup = bs(driver.page_source, 'lxml')
        articles_on_page = soup.find_all('div', class_='ListType1')
        articles += articles_on_page

    driver.quit()
    return articles

def getTitle(soup):
    title = soup.select('div > a')
    if title:
        return title[0].text
    print('title not found, update select() method')
    return 'title not found'

def getDate(soup):
    date = soup.select('div.date')
    if date:
        return date[0].text.strip()
    print('date not found, update select() method')
    return 'date not found'

def makeHash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()

def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    print('new article found')
    return True

def getLink(soup):
    link = soup.select('div > a')
    if link:
        return base_url + link[0]['href']

def getContent(link, session):
    r = session.get(link, timeout=10)
    soup = bs(r.text, 'lxml')
    content = soup.find('div', class_='opis obogatena_vsebina colored_links')
    if content:
        return ' '.join(content.text.split())
    print('content not found, update find() method')
    return 'content not found'
    

def main():

    num_new_articles = 0
    num_pages_to_check = 2

    with requests.Session() as session:
        
        articles = getArticlesOn_n_pages(num_pages_to_check)

        titles = []
        dates = []
        links = []
        hashes = []
        
        for x in articles:
            title = getTitle(x)
            date = getDate(x)
            hash_str = makeHash(title, date)
            
            if is_article_new(hash_str):
                titles.append(title)
                dates.append(date)
                hashes.append(hash_str)
                links.append(getLink(x))
                num_new_articles += 1

        for i in range(num_new_articles):
            content = getContent(links[i], session)
            print(titles[i])
            print(dates[i])
            print(content)

    print(num_new_articles,'new articles found', num_pages_to_check, 'pages checked')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()