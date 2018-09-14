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
import sys
from tqdm import tqdm

'''

    firstRunBool used - working

    ta scraper potrebuje v isti mapi se file (linux):clear
        - chromedriver (za uporabo selenium knjiznjice) 

    idrija.si clanke loada skozi javascript, zato je potrebna knjiznjica selenium

    OPOZORILO!! nekateri clanki nimajo datuma zraven - so zgolj obvestila

    created by markzakelj
'''

SOURCE = 'OBCINA-IDRIJA'
firstRunBool = False
num_pages_to_check = 2
num_errors = 0
base_url = 'https://www.idrija.si'
full_url = 'https://www.idrija.si/objave/8'


def log_error(text):
    global num_errors
    num_errors += 1
    log_file = open('error_log_zakelj.log', 'a+')
    log_file.write(str(datetime.datetime.today()) + '\n')
    log_file.write('scraper_obcinaIdrija.py' + '\n')
    log_file.write(text + '\n\n')
    log_file.close()


def getArticlesOn_n_pages(num_pages_to_check):
    '''
        clanki se pojavijo na strani sele, ko se zloada javascript,
        zato se uporabi selenium knjiznjica
    '''
    options = Options()
    options.set_headless(headless=True)
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(options=options) #ta vrstica klice napako, ce se v isti mapi ne nahaja file 'chromedriver'
    driver.get(full_url)
    timeout = 8
    try:
        element_present = EC.presence_of_element_located((By.CSS_SELECTOR, 'div.postsgroup'))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
       log_error("Timed out waiting for page to load")


    articles = []
    print('\tgathering articles ...')
    i = 0
    n = 0
    while i < num_pages_to_check:
        driver.find_element_by_link_text(str(n+1)).click()
        time.sleep(3)    #pocakaj 3 sekunde, da se zloada stran
        soup = bs(driver.page_source, 'lxml')
        if firstRunBool:
            n += 1
            if soup.find('div', class_='stevilcenje').find_all('a')[-1].text != 'Zadnja':
                break
        else:
            i += 1
            n += 1
        articles += soup.find_all('div', class_='ListType1')
    driver.quit()
    return articles

def getTitle(soup):
    title = soup.select('div > a')
    if title:
        return title[0].text
    log_error('title not found, update select() method')
    return 'title not found'

def getDate(soup):
    date = soup.select('div.date')
    if date:
        return date[0].text.strip()
    log_error('date not found for article' + getTitle(soup))
    return '1.1.1111'

def makeHash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()

def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True

def getLink(soup):
    link = soup.select('div > a')
    if link:
        return base_url + link[0]['href']
    return base_url

def getContent(link, session):
    r = session.get(link, timeout=10)
    soup = bs(r.text, 'lxml')
    content = soup.find('div', class_='opis obogatena_vsebina colored_links')
    if content:
        return ' '.join(content.text.split())
    log_error('content not found, update find() method')
    return 'content not found'
    

def main():
    print('=========================')
    print(sys.argv[0])
    print('=========================')

    num_new_articles = 0
    

    with requests.Session() as session:
        
        articles = getArticlesOn_n_pages(num_pages_to_check)

        print('\tgathering article info')
        for x in tqdm(articles):
            title = getTitle(x)
            date = getDate(x)
            hash_str = makeHash(title, date)
            
            if is_article_new(hash_str):
                link = getLink(x)
                content = getContent(link, session)
                tup = (str(datetime.date.today()), title, content, date, hash_str, link, SOURCE)
                dbExecutor.insertOne(tup)
                num_new_articles += 1

        print(num_new_articles,'new articles found', len(articles), 'articles checked,', num_errors, 'errors found')

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()