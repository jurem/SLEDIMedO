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
import datetime
from database.dbExecutor import dbExecutor

#TODO: dodaj opcijo za scrapanje vec strani na katerih so clanki

'''
    ta scraper potrebuje v isti mapi se file (linux):clear
        - chromedriver (za uporabo selenium knjiznjice) 

    idrija.si clanke loada skozi javascript, zato je potrebna knjiznjica selenium

    OPOZORILO!! nekateri clanki nimajo datuma zraven - so zgolj obvestila
'''

base_url = 'https://www.tolmin.si'

def getArticlesOn_n_pages(num_pages_to_check):
    '''
        clanki se pojavijo na strani sele, ko se zloada javascript,
        zato se uporabi selenium knjiznjica
    '''
    options = Options()
    options.set_headless(headless=True)
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(options=options) #ta vrstica klice napako, ce se v isti mapi ne nahaja file 'chromedriver'
    driver.get('https://www.tolmin.si/objave/')
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

def isArticleNew(hash):
    is_new = False
    try:
        f = open('article_list.txt', 'r+')
    except FileNotFoundError:
        f = open('article_list.txt', 'a+')

    if hash not in f.read().split():
        is_new = True
        f.write(hash + '\n')
        print('new article found')
    f.close()
    return is_new

def getLink(soup):
    link = soup.select('div > a')
    if link:
        return base_url + link[0]['href']

def getContent(link, session):
    print(link)

    r = session.get(link, timeout=10)
    soup = bs(r.text, 'lxml')
    content = soup.find('div', class_='opis obogatena_vsebina colored_links')
    if content:
        return ' '.join(content.text.split())
    print('content not found, update find() method')
    return 'content not found'

def formatDate(date):
    #format date for consistent database
    date = date.split('.')
    for i in range(2):
        if len(date[i]) == 1:
            date[i] = '0'+date[i]
    return '-'.join(reversed(date))
    

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
            
            if isArticleNew(hash_str):
                titles.append(title)
                dates.append(date)
                hashes.append(hash_str)
                links.append(getLink(x))
                num_new_articles += 1

        list_new = []
        for i in range(num_new_articles):
            content = getContent(links[i], session)
            tup = (str(datetime.date.today()), titles[i], content, formatDate(dates[i]), hashes[i], links[i], base_url)
            list_new.append(tup)

        dbExecutor.insertMany(list_new)



if __name__ == '__main__':
    main()