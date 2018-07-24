from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
import requests
import hashlib

'''
    ta scraper potrebuje v isti mapi se file (linux):
        - chromedriver (za uporabo selenium knjiznjice) 
'''

base_url = 'https://www.idrija.si'

def getSoup():
    '''
        clanki se pojavijo na strani sele, ko se zloada javascript,
        zato se uporabi selenium knjiznjica
    '''
    options = Options()
    options.set_headless(headless=True)
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.idrija.si/objave/8')
    timeout = 5
    try:
        element_present = EC.presence_of_element_located((By.CSS_SELECTOR, 'div.postsgroup'))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        print ("Timed out waiting for page to load")

    soup = bs(driver.page_source, 'html.parser')
    driver.quit()
    return soup

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
    r = session.get(link, timeout=10)
    soup = bs(r.text, 'html.parser')
    content = soup.find('div', class_='opis obogatena_vsebina colored_links')
    if content:
        return content.text
    print('content not found, update find() method')
    return 'content not found'


def main():

    num_new_articles = 0

    with requests.Session() as session:
        soup = getSoup()
        articles = soup.find_all('div', class_='ListType1')

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

        for i in range(num_new_articles):
            print(getContent(links[i], session))

    print(num_new_articles,'new articles found')


if __name__ == '__main__':
    main()