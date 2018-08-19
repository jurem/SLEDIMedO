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
SOURCE = '24-UR'

base_url = 'https://www.24ur.com'
full_url = 'https://www.24ur.com/arhiv/novice?stran=' #kasneje dodas se stran

def getArticlesOn_n_pages(num_pages_to_check, driver):
    '''
        clanki se pojavijo na strani sele, ko se zloada javascript,
        zato se uporabi selenium knjiznjica
    '''
    articles = []
    for n in range(num_pages_to_check):
        driver.get(full_url + str(n+1))
        timeout = 8
        try:
            element_present = EC.presence_of_element_located((By.CSS_SELECTOR, 'div.timeline.timeline--blue'))
            WebDriverWait(driver, timeout).until(element_present)
        except TimeoutException:
            print ("Timed out waiting for page to load")
        soup = bs(driver.page_source, 'lxml')
        articles_on_page = soup.find('div', class_='timeline timeline--blue').findChildren('a', recursive=False)
        articles += articles_on_page
    driver.quit()
    return articles

def getTitle(soup):
    title = soup.select('h2 > span')
    if title:
        return title[0].text
    print('title not found, update select() method')
    return 'title not found'

def getDate(soup):
    date = soup.find('div', class_='timeline__date')
    if date:
        return date.text
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
        element_present = EC.presence_of_element_located((By.CSS_SELECTOR, 'div.article__summary'))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        print ("Timed out waiting for page to load")    

    soup = bs(driver.page_source, 'html.parser')
    content = soup.find('div', class_='article__body')
    if content:
        return ' '.join(content.text.split())
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
    num_pages_to_check = 1
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
        new_articles_tuples.append((str(datetime.date.today()), titles[i], content, formatDate(dates[i]), hashes[i], links[i], SOURCE))
        # time.sleep(2)

    driver.quit()

    dbExecutor.insertMany(new_articles_tuples)

    print(num_new_articles,'new articles found', num_pages_to_check, 'pages checked')


if __name__ == '__main__':
    main()