from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor
import sys

'''
    firstRunBool used - working (traja lahko tudi do 30 min)

    created by markzakelj
'''

SOURCE = 'MDDSZ'
firstRunBool = False

base_url = 'http://www.mddsz.gov.si'
full_url = 'http://www.mddsz.gov.si/si/medijsko_sredisce/sporocila_za_medije/page/' #kasneje dodas se cifro strani
headers = {
    'user-agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 '
        'Safari/537.36'}

def makeHash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()

def find_last_page(soup):
    num = soup.find('ul', class_='f3-widget-paginator').find_all('li')[-2].text
    return int(num)

def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    print('new article found')
    return True

def getLink(soup):
    link = soup.select('h4 > a')
    if link:
        return link[0]['href']
    print('link not found, update find() method')
    return 'link not found'


def getDate(soup):
    date = soup.find('time')
    if date:
        return ''.join(date.text.split())
    print('date not found, update find() method')
    return 'date not found'


def getTitle(soup):
    title = soup.select('h4 > a')
    if title:
        return ' '.join(title[0].text.split())
    print('title not found, update find() method')
    return 'title not found'


def getContent(url, session):
    r = session.get(url, timeout=5)
    soup = BeautifulSoup(r.text, 'lxml')

    #znebi se script texta na strani, da ne bo del content-a
    for script in soup(['script']):
        script.decompose()

    content = soup.find('div', class_='news news-single-item')
    if content:
        return ' '.join(content.text.split())
    print('content not found, update select() method', url)
    return 'content not found'


def formatDate(date):
    #format date for consistent database
    return '-'.join(reversed(date.split('.')))


def getArticlesOnPage(num_pages_to_check, session):
    articles = []

    for n in range(num_pages_to_check):
        r = session.get(full_url + str(n+1), timeout=10)
        soup = BeautifulSoup(r.text, 'lxml')
        articles_on_page = soup.find('div', class_='news').find_all('table')
        articles = articles + articles_on_page
    return articles


def main():
    num_pages_to_check = 3
    num_new_articles = 0
    articles_checked = 0

    with requests.Session() as session:
        session.headers.update(headers)
        if firstRunBool:
            num_pages_to_check = find_last_page(BeautifulSoup(requests.get(full_url).text, 'html.parser'))
            print('last page is', num_pages_to_check)

        articles = getArticlesOnPage(num_pages_to_check, session)

        article_tuples = []
        for x in articles:
            title = getTitle(x)
            date = getDate(x)
            hash_str = makeHash(title, date)
            articles_checked += 1

            if is_article_new(hash_str):
                link = getLink(x)
                print(link + '\n')
                content = getContent(link, session)
                tup = (str(datetime.date.today()), title, content, formatDate(date), hash_str, link, SOURCE)
                article_tuples.append(tup)
                num_new_articles += 1

        dbExecutor.insertMany(article_tuples)

    print(num_new_articles, 'new articles found', articles_checked, 'articles checked')



if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()