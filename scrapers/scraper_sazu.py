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

#TODO: dodaj opcijo za scrapanje vec strani na katerih so clanki

'''
    ta scraper potrebuje v isti mapi se file (linux):clear
        - chromedriver (za uporabo selenium knjiznjice) 

    
'''
SOURCE = 'SAZU'

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
    for n in range(num_pages_to_check):
        driver.get(full_url + str(n+1) + '&year=2018')
        timeout = 8
        try:
            element_present = EC.presence_of_element_located((By.CSS_SELECTOR, 'div.list-group'))
            WebDriverWait(driver, timeout).until(element_present)
        except TimeoutException:
            print ("Timed out waiting for page to load")

        time.sleep(4) #pocakaj, da se stran zares zloada
        soup = bs(driver.page_source, 'html.parser')
        articles += soup.find_all('a', class_='list-group-item ng-scope')
        
    driver.quit()
    return articles

def getTitle(soup):
    title = soup.select('h4')
    if title:
        return title[0].text
    print('title not found, update select() method')
    return 'title not found'

def getDate(soup):
    date = soup.select('span > span')
    if date:
        date = date[0].text.split()
        date[1] = meseci[date[1]]
        return ''.join(date)
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
    link = soup.get('href')
    if link:
        return base_url + link
    print('link not found')

def getContent(link, driver):
    print(link)
    driver.get(link)

    timeout = 8
    try:
        element_present = EC.presence_of_element_located((By.CSS_SELECTOR, 'p.docContent.ng-binding'))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        print ("Timed out waiting for page to load")

    soup = bs(driver.page_source, 'html.parser')
    content = soup.find('p', class_='docContent ng-binding')
    if content:
        return content.text
    print('content not found, update find() method')
    return 'content not found'

def initDriver():
    options = Options()
    options.set_headless(headless=True)
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(options=options) #v isti mapi se mora nahajati file "chromedriver"
    return driver

def formatDate(date):
    #format date for consistent database
    return '-'.join(reversed(date.split('.')))
    

def main():

    num_new_articles = 0
    num_pages_to_check = 3
    driver = initDriver()

    articles = getArticlesOn_n_pages(num_pages_to_check, driver)
    driver.quit()

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
    
    new_articles_tuples = []

    driver = initDriver()
    for i in range(num_new_articles):
        content = getContent(links[i], driver)
        new_articles_tuples.append((str(datetime.date.today()), titles[i], content, formatDate(dates[i]), hashes[i], links[i], base_url))
        # time.sleep(2)

    driver.quit()

    dbExecutor.insertMany(new_articles_tuples)

    print(num_new_articles,'new articles found', num_pages_to_check, 'pages checked')


if __name__ == '__main__':
    main()