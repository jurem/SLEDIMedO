from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
import requests
import datetime
import hashlib
import time
from database.dbExecutor import dbExecutor
import sys
from tqdm import tqdm
import re

#TODO: dodaj opcijo za scrapanje vec strani na katerih so clanki

'''
    ta scraper potrebuje v isti mapi se file (linux):clear
        - chromedriver (za uporabo selenium knjiznjice) 

    dodaj se opcijo za letnico(zdaj jemlje samo 2018 clanke)

    created by markzakelj
'''
SOURCE = 'SAZU'
firstRunBool = False
num_errors = 0
base_url = 'http://www.sazu.si'
full_url = 'http://www.sazu.si/objave/?page=' #kasneje dodas se cifro strani

meseci = {'jan.': '1.', 'feb.': '2.', 'mar.': '3.', 'apr.': '4.', 'maj': '5.',
          'jun.': '6.', 'jul.': '7.', 'avg.': '8.', 'sep.': '9.',
          'okt.': '10.', 'nov.': '11.', 'dec.': '12.'}

def getArticlesOn_n_pages(num_pages_to_check, driver):
    '''
        clanki se pojavijo na strani sele, ko se zloada javascript,
        zato se uporabi selenium knjiznjica
    '''
    articles = []
    print('\tgathering articles ...')
    for year in range(2016, 2019):
        print('year:' + str(year))
        if firstRunBool:
            num_pages_to_check = find_last_page(driver, year)
        for n in tqdm(range(num_pages_to_check)):
            driver.get(full_url + str(n+1) + '&year=' +str(year))
            timeout = 8
            try:
                element_present = EC.presence_of_element_located((By.CSS_SELECTOR, 'div.list-group'))
                WebDriverWait(driver, timeout).until(element_present)
            except TimeoutException:
                log_error ("Timed out waiting for page to load")

            time.sleep(4) #pocakaj, da se stran zares zloada
            soup = bs(driver.page_source, 'html.parser')
            
            articles += soup.find_all('a', class_='list-group-item ng-scope')
        
    driver.quit()
    return articles

def find_last_page(driver, year):
    driver.get('http://www.sazu.si/objave/?year=' + str(year))
    time.sleep(4)
    driver.find_element_by_css_selector('body > section > section > section > section > div.containerw > div > ul > li.pagination-last.ng-scope > a').click()
     #pocakaj, da se stran zares zloada
    time.sleep(4)
    url = driver.current_url
    num = re.search(r'\d', url).group(0)
    return int(num)


def log_error(text):
    global num_errors
    num_errors += 1
    log_file = open('error_log_zakelj.log', 'a+')
    log_file.write(str(datetime.datetime.today()) + '\n')
    log_file.write('scraper_sazu.py' + '\n')
    log_file.write(text + '\n\n')
    log_file.close()

def getTitle(soup):
    title = soup.select('h4')
    if title:
        return title[0].text
    log_error('title not found, update select() method')
    return 'title not found'

def getDate(soup):
    date = soup.select('span > span')
    if date:
        date = date[0].text.split()
        date[1] = meseci[date[1]]
        return ''.join(date)
    log_error('date not found, update select() method')
    return '1.1.1111'

def makeHash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()

def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True

def getLink(soup):
    link = soup.get('href')
    if link:
        return base_url + link
    log_error('link not found')

def getContent(link, driver):
    driver.get(link)
    timeout = 8
    try:
        element_present = EC.presence_of_element_located((By.CSS_SELECTOR, 'p.docContent.ng-binding'))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        log_error ("Timed out waiting for page to load")

    soup = bs(driver.page_source, 'html.parser')
    content = soup.find('p', class_='docContent ng-binding')
    if content:
        return content.text
    log_error('content not found, update find() method')
    return 'content not found'

def initDriver():
    options = Options()
    options.set_headless(headless=True)
    options.add_argument("--window-size=1920x1080")
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--allow-insecure-localhost')
    driver = webdriver.Chrome(options=options) #v isti mapi se mora nahajati file "chromedriver"
    return driver

def formatDate(raw_date):
    #format date for consistent database
    try:
        date = raw_date.split('.')
        for i in range(2):
            if len(date[i]) == 1:
                date[i] = '0'+date[i]
        return '-'.join(reversed(date))
    except IndexError:
        log_error('cant format date:'+ str(raw_date))
    

def main():
    print('=========================')
    print(sys.argv[0])
    print('=========================')

    num_new_articles = 0
    num_pages_to_check = 3
    driver = initDriver()

    articles = getArticlesOn_n_pages(num_pages_to_check, driver)
    driver.quit()

    titles = []
    dates = []
    links = []
    hashes = []

    print('\tgathering article info ...')
    for x in tqdm(articles):
        title = getTitle(x)
        date = getDate(x)
        hash_str = makeHash(title, date)
        
        if is_article_new(hash_str):
            titles.append(title)
            dates.append(date)
            hashes.append(hash_str)
            links.append(getLink(x))
            num_new_articles += 1
    
    new_articles_tuples = []

    driver = initDriver()
    print('\tgathering article content ...')
    for i in tqdm(range(num_new_articles)):
        content = getContent(links[i], driver)
        new_articles_tuples.append((str(datetime.date.today()), titles[i], content, formatDate(dates[i]), hashes[i], links[i], SOURCE))
        # time.sleep(2)

    driver.quit()

    dbExecutor.insertMany(new_articles_tuples)

    print(num_new_articles,'new articles found,', len(articles), 'articles checked,', num_errors,'errors found\n')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()